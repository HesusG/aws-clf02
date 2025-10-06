#!/usr/bin/env python3
"""
Script 5: Phoenix Evaluations
Evalúa calidad de preguntas generadas usando Arize Phoenix
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("❌ Error: OPENAI_API_KEY no encontrada")
    sys.exit(1)

import phoenix as px
from phoenix.evals import (
    HallucinationEvaluator,
    QAEvaluator,
    llm_classify,
    OpenAIModel
)
from tqdm import tqdm

# Directorios
DATA_DIR = PROJECT_ROOT / "data"
PHOENIX_DIR = DATA_DIR / "phoenix_logs"
PHOENIX_DIR.mkdir(parents=True, exist_ok=True)

# Configuración
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class QuestionEvaluator:
    def __init__(self, model_name: str = MODEL):
        self.model = OpenAIModel(model=model_name)
        self.hallucination_eval = None
        self.qa_eval = None

    def setup_evaluators(self):
        """Configura los evaluators de Phoenix"""
        print("🔧 Configurando Phoenix Evaluators...")

        # Hallucination Evaluator
        self.hallucination_eval = HallucinationEvaluator(self.model)

        # QA Evaluator
        self.qa_eval = QAEvaluator(self.model)

        print("   ✅ Evaluators configurados")

    def evaluate_hallucination(self, question_data: dict) -> dict:
        """Evalúa si la pregunta contiene hallucinations"""

        # Input: pregunta + opciones
        input_text = f"{question_data['question']}\n\n"
        for letter, text in question_data['options'].items():
            input_text += f"{letter}) {text}\n"

        # Output: explicación
        output_text = question_data['explanation']

        # Context: documentación AWS recuperada
        context_text = question_data.get('retrieved_context', '')

        try:
            result = self.hallucination_eval.evaluate(
                input=input_text,
                output=output_text,
                context=context_text
            )

            return {
                "score": result.score,
                "label": result.label,
                "explanation": result.explanation
            }
        except Exception as e:
            print(f"⚠️  Error en hallucination eval: {str(e)}")
            return {"score": 0.5, "label": "unknown", "explanation": str(e)}

    def evaluate_qa_correctness(self, question_data: dict) -> dict:
        """Evalúa si la pregunta tiene sentido y la respuesta es correcta"""

        # Input: pregunta
        input_text = question_data['question']

        # Output: respuesta correcta
        correct_letter = question_data['correct_answer']
        output_text = f"{correct_letter}) {question_data['options'][correct_letter]}"

        # Reference: explicación
        reference_text = question_data['explanation']

        try:
            result = self.qa_eval.evaluate(
                input=input_text,
                output=output_text,
                reference=reference_text
            )

            return {
                "score": result.score,
                "label": result.label,
                "explanation": result.explanation
            }
        except Exception as e:
            print(f"⚠️  Error en QA eval: {str(e)}")
            return {"score": 0.5, "label": "unknown", "explanation": str(e)}

    def evaluate_clf_compliance(self, question_data: dict) -> dict:
        """Evalúa compliance con formato CLF-C02"""

        checks = {
            "has_4_options": len(question_data.get('options', {})) == 4,
            "has_correct_answer": question_data.get('correct_answer') in ['A', 'B', 'C', 'D'],
            "has_domain": question_data.get('domain', '').startswith('Domain'),
            "has_explanation": len(question_data.get('explanation', '')) > 100,
            "answer_in_options": question_data.get('correct_answer') in question_data.get('options', {}),
            "question_not_empty": len(question_data.get('question', '')) > 20
        }

        score = sum(checks.values()) / len(checks)
        passed = score >= 0.9  # 90% de checks deben pasar

        failed_checks = [k for k, v in checks.items() if not v]

        return {
            "score": score,
            "label": "compliant" if passed else "non_compliant",
            "explanation": f"Passed {sum(checks.values())}/{len(checks)} checks. Failed: {failed_checks}"
        }

    def evaluate_question(self, question_data: dict, index: int) -> dict:
        """Evalúa una pregunta con todos los evaluators"""

        # Eval 1: Hallucination
        hall_result = self.evaluate_hallucination(question_data)

        # Eval 2: QA Correctness
        qa_result = self.evaluate_qa_correctness(question_data)

        # Eval 3: CLF-C02 Compliance
        compliance_result = self.evaluate_clf_compliance(question_data)

        # Combinar resultados
        eval_results = {
            "id": index,
            "hallucination": hall_result,
            "qa_correctness": qa_result,
            "clf_compliance": compliance_result
        }

        # Determinar si pasa todos los criterios
        passed = (
            hall_result["score"] < 0.3 and  # Bajo score de hallucination es bueno
            qa_result["score"] > 0.7 and    # Alto score de QA es bueno
            compliance_result["score"] >= 0.9  # Compliance estricto
        )

        eval_results["overall_pass"] = passed

        return eval_results

    def evaluate_batch(self, questions: List[dict]) -> tuple:
        """Evalúa un batch de preguntas"""

        print(f"\n🔍 Evaluando {len(questions)} preguntas con Phoenix...")
        print("="*70)

        approved_questions = []
        rejected_questions = []
        all_eval_results = []

        for i, question in enumerate(tqdm(questions, desc="Evaluando"), 1):
            eval_results = self.evaluate_question(question, i)
            all_eval_results.append(eval_results)

            # Agregar eval results a question data
            question_with_eval = {**question, "phoenix_evals": eval_results}

            if eval_results["overall_pass"]:
                approved_questions.append(question_with_eval)
            else:
                # Agregar razón de rechazo
                reasons = []
                if eval_results["hallucination"]["score"] >= 0.3:
                    reasons.append(f"Hallucination: {eval_results['hallucination']['score']:.2f}")
                if eval_results["qa_correctness"]["score"] <= 0.7:
                    reasons.append(f"QA: {eval_results['qa_correctness']['score']:.2f}")
                if eval_results["clf_compliance"]["score"] < 0.9:
                    reasons.append(f"Compliance: {eval_results['clf_compliance']['score']:.2f}")

                question_with_eval["rejection_reasons"] = reasons
                rejected_questions.append(question_with_eval)

        return approved_questions, rejected_questions, all_eval_results

    def generate_report(self, eval_results: List[dict], approved: int, rejected: int):
        """Genera reporte de evaluaciones"""

        print("\n" + "="*70)
        print("📊 REPORTE DE EVALUACIONES")
        print("="*70)

        # Estadísticas generales
        total = approved + rejected
        approval_rate = (approved / total * 100) if total > 0 else 0

        print(f"\nTotal evaluadas: {total}")
        print(f"✅ Aprobadas: {approved} ({approval_rate:.1f}%)")
        print(f"❌ Rechazadas: {rejected} ({100-approval_rate:.1f}%)")

        # Promedios de scores
        avg_hallucination = sum(r["hallucination"]["score"] for r in eval_results) / len(eval_results)
        avg_qa = sum(r["qa_correctness"]["score"] for r in eval_results) / len(eval_results)
        avg_compliance = sum(r["clf_compliance"]["score"] for r in eval_results) / len(eval_results)

        print(f"\n📊 Scores Promedio:")
        print(f"   Hallucination: {avg_hallucination:.3f} (menor es mejor, límite: 0.3)")
        print(f"   QA Correctness: {avg_qa:.3f} (mayor es mejor, límite: 0.7)")
        print(f"   CLF Compliance: {avg_compliance:.3f} (mayor es mejor, límite: 0.9)")

        # Distribución de rechazos
        if rejected > 0:
            print(f"\n❌ Razones de Rechazo:")
            hall_fails = sum(1 for r in eval_results if r["hallucination"]["score"] >= 0.3)
            qa_fails = sum(1 for r in eval_results if r["qa_correctness"]["score"] <= 0.7)
            comp_fails = sum(1 for r in eval_results if r["clf_compliance"]["score"] < 0.9)

            print(f"   Hallucination: {hall_fails}")
            print(f"   QA Correctness: {qa_fails}")
            print(f"   CLF Compliance: {comp_fails}")


def main():
    parser = argparse.ArgumentParser(description="Evalúa preguntas con Phoenix")
    parser.add_argument("--input", type=str, default="questions_raw.json", help="Archivo de entrada")
    parser.add_argument("--output", type=str, default="questions_evaluated.json", help="Archivo aprobadas")
    parser.add_argument("--rejected", type=str, default="questions_rejected.json", help="Archivo rechazadas")
    args = parser.parse_args()

    # Cargar preguntas
    input_path = DATA_DIR / args.input
    if not input_path.exists():
        print(f"❌ Error: {input_path} no encontrado")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    print(f"\n📖 Cargadas {len(questions)} preguntas desde {input_path}")

    # Inicializar Phoenix
    print("\n🚀 Iniciando Arize Phoenix...")
    session = px.launch_app()
    print(f"   📊 Dashboard: http://localhost:6006")

    # Evaluar
    evaluator = QuestionEvaluator()
    evaluator.setup_evaluators()

    approved, rejected, eval_results = evaluator.evaluate_batch(questions)

    # Guardar resultados
    output_path = DATA_DIR / args.output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(approved, f, indent=2, ensure_ascii=False)

    rejected_path = DATA_DIR / args.rejected
    with open(rejected_path, 'w', encoding='utf-8') as f:
        json.dump(rejected, f, indent=2, ensure_ascii=False)

    # Generar reporte
    evaluator.generate_report(eval_results, len(approved), len(rejected))

    print(f"\n✅ Preguntas aprobadas guardadas en: {output_path}")
    print(f"❌ Preguntas rechazadas guardadas en: {rejected_path}")

    print("\n📊 Phoenix Dashboard sigue corriendo en: http://localhost:6006")
    print("   Presiona Ctrl+C para cerrar")

    # Mantener Phoenix corriendo
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Cerrando Phoenix...")


if __name__ == "__main__":
    main()
