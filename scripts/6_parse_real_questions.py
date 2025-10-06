#!/usr/bin/env python3
"""
Script 6: Parse Real Questions from TXT
Extrae y enriquece las preguntas reales del archivo EXAMEN REAL MAESTRO AWS.txt
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

# Verificar API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ Error: OPENAI_API_KEY no encontrada en .env")
    sys.exit(1)

from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from tqdm import tqdm

# Configuración
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_db"
INPUT_FILE = PROJECT_ROOT / "document" / "EXAMEN REAL  MAESTRO AWS.txt"
OUTPUT_DIR = PROJECT_ROOT / "data"

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Mapeo de dominios CLF-C02
TOPIC_TO_DOMAIN = {
    # Seguridad
    "shield": "Domain 2: Security and Compliance",
    "guardduty": "Domain 2: Security and Compliance",
    "waf": "Domain 2: Security and Compliance",
    "iam": "Domain 2: Security and Compliance",
    "inspector": "Domain 2: Security and Compliance",
    "responsabilidad": "Domain 2: Security and Compliance",
    "seguridad": "Domain 2: Security and Compliance",

    # Contenedores
    "ecs": "Domain 3: Cloud Technology and Services",
    "eks": "Domain 3: Cloud Technology and Services",
    "ecr": "Domain 3: Cloud Technology and Services",
    "fargate": "Domain 3: Cloud Technology and Services",
    "contenedor": "Domain 3: Cloud Technology and Services",

    # Cómputo
    "ec2": "Domain 3: Cloud Technology and Services",
    "spot": "Domain 3: Cloud Technology and Services",
    "reserved": "Domain 3: Cloud Technology and Services",
    "compute optimizer": "Domain 3: Cloud Technology and Services",

    # Almacenamiento
    "s3": "Domain 3: Cloud Technology and Services",
    "glacier": "Domain 3: Cloud Technology and Services",
    "ebs": "Domain 3: Cloud Technology and Services",
    "efs": "Domain 3: Cloud Technology and Services",

    # Bases de datos
    "rds": "Domain 3: Cloud Technology and Services",
    "dynamodb": "Domain 3: Cloud Technology and Services",
    "aurora": "Domain 3: Cloud Technology and Services",
    "redshift": "Domain 3: Cloud Technology and Services",

    # Red
    "vpc": "Domain 3: Cloud Technology and Services",
    "cloudfront": "Domain 3: Cloud Technology and Services",
    "route 53": "Domain 3: Cloud Technology and Services",
    "elastic load": "Domain 3: Cloud Technology and Services",

    # Serverless
    "lambda": "Domain 3: Cloud Technology and Services",

    # Facturación
    "pricing": "Domain 4: Billing, Pricing, and Support",
    "billing": "Domain 4: Billing, Pricing, and Support",
    "cost": "Domain 4: Billing, Pricing, and Support",
    "support": "Domain 4: Billing, Pricing, and Support",
    "trusted advisor": "Domain 4: Billing, Pricing, and Support",

    # Cloud Concepts
    "escalabilidad": "Domain 1: Cloud Concepts",
    "elasticidad": "Domain 1: Cloud Concepts",
    "alta disponibilidad": "Domain 1: Cloud Concepts",
    "well-architected": "Domain 1: Cloud Concepts",
    "caf": "Domain 1: Cloud Concepts",
}


class RealQuestionParser:
    def __init__(self):
        self.client = OpenAI()
        self.vectorstore = None
        self.questions = []

    def load_rag_system(self):
        """Carga el sistema RAG"""
        print("🔮 Cargando RAG system...")

        if not CHROMA_DIR.exists():
            print("❌ Error: ChromaDB no encontrado")
            print("   Ejecuta: python scripts/2_build_rag.py")
            sys.exit(1)

        embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        self.vectorstore = Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=embeddings,
            collection_name="aws_docs"
        )
        print("   ✅ RAG system cargado")

    def parse_questions_from_txt(self) -> List[Dict]:
        """Extrae preguntas del archivo TXT - VERSIÓN MEJORADA"""
        print(f"\n📖 Parseando preguntas de: {INPUT_FILE.name}")

        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        questions = []
        i = 0
        global_question_num = 0

        while i < len(lines):
            line = lines[i].strip()

            # Detectar inicio de pregunta (número. ¿texto)
            if re.match(r'^\d+\.\s*¿', line):
                global_question_num += 1

                # Extraer texto de pregunta
                question_text = line[line.index('¿'):].strip()

                # Buscar opciones A-D en las siguientes líneas
                options = {}
                correct = None
                i += 1

                # Recoger opciones
                option_count = 0
                while i < len(lines) and option_count < 4:
                    current_line = lines[i].strip()

                    # Detectar opción A), B), C), D)
                    if re.match(r'^[A-D]\)', current_line):
                        letter = current_line[0]
                        # Extraer texto después de letra)
                        text = current_line[2:].strip()

                        # Detectar respuesta correcta (tiene ✅)
                        if '✅' in text:
                            correct = letter
                            text = text.replace('✅', '').strip()

                        options[letter] = text
                        option_count += 1
                        i += 1
                    # Si la opción continúa en siguiente línea
                    elif option_count > 0 and option_count < 4 and not re.match(r'^\d+\.\s*¿', current_line) and current_line and not current_line.startswith('✔') and not current_line.startswith('❌'):
                        # Agregar a última opción
                        last_letter = chr(ord('A') + option_count - 1)
                        if last_letter in options:
                            options[last_letter] += ' ' + current_line
                        i += 1
                    else:
                        break

                # Buscar respuesta correcta en línea ✔ si no la encontramos
                if not correct:
                    for j in range(i, min(i + 10, len(lines))):
                        check_line = lines[j].strip()
                        if check_line.startswith('✔') and 'Correcta:' in check_line:
                            # Extraer letra: "✔ Correcta: B)"
                            match = re.search(r'Correcta:\s*([A-D])\)', check_line)
                            if match:
                                correct = match.group(1)
                                break

                # Extraer explicación (desde línea actual hasta próxima pregunta)
                explanation_lines = []
                while i < len(lines):
                    current = lines[i].strip()

                    # Detener si encontramos otra pregunta
                    if re.match(r'^\d+\.\s*¿', current):
                        break

                    # Detener si encontramos sección nueva
                    if current.startswith('📌') or current.startswith('###') or re.match(r'^\d+\.\d+\.', current):
                        break

                    # Agregar líneas relevantes
                    if current and not current.startswith('---'):
                        explanation_lines.append(current)

                    i += 1

                explanation = ' '.join(explanation_lines)

                # Validar que tengamos pregunta completa
                if len(options) == 4 and correct and question_text:
                    questions.append({
                        'number': global_question_num,
                        'question': question_text,
                        'options': options,
                        'correct_answer': correct,
                        'explanation_original': explanation[:500]  # Limitar explicación
                    })
                elif question_text:
                    # Debug: mostrar preguntas incompletas
                    print(f"   ⚠️ Pregunta incompleta #{global_question_num}: opciones={len(options)}, correcta={correct}")

            else:
                i += 1

        print(f"   ✅ Extraídas {len(questions)} preguntas")
        return questions

    def infer_domain(self, question: str, options: Dict[str, str]) -> str:
        """Infiere el dominio CLF-C02 basado en el contenido"""
        text = (question + ' ' + ' '.join(options.values())).lower()

        for keyword, domain in TOPIC_TO_DOMAIN.items():
            if keyword in text:
                return domain

        # Default
        return "Domain 3: Cloud Technology and Services"

    def enrich_with_rag(self, question: Dict) -> Dict:
        """Enriquece la pregunta con contexto RAG y mejora la explicación"""

        # 1. Obtener contexto relevante
        query = f"{question['question']} {' '.join(question['options'].values())}"
        docs = self.vectorstore.similarity_search(query, k=2)
        context = "\n\n".join([doc.page_content[:400] for doc in docs])

        # 2. Inferir dominio
        domain = self.infer_domain(question['question'], question['options'])

        # 3. Mejorar explicación con GPT-4o-mini
        system_prompt = f"""Eres un experto en AWS CLF-C02.

Tienes una pregunta de examen real que ya fue revisada por un humano.
Tu tarea es MEJORAR Y EXPANDIR la explicación pedagógica usando el contexto oficial de AWS proporcionado.

CONTEXTO AWS OFICIAL:
{context}

IMPORTANTE:
- Mantén la pregunta y opciones EXACTAMENTE como están (no las modifiques)
- Mantén la respuesta correcta ({question['correct_answer']})
- MEJORA la explicación para que sea más completa y pedagógica
- Usa el contexto oficial de AWS para fundamentar la explicación
- Estructura: **Respuesta correcta**, Por qué las otras son incorrectas, Concepto clave
- Responde SOLO con JSON válido"""

        user_prompt = f"""Pregunta existente:
{question['question']}

Opciones:
{json.dumps(question['options'], indent=2, ensure_ascii=False)}

Respuesta correcta: {question['correct_answer']}

Explicación original: {question['explanation_original']}

Genera un JSON con esta estructura:
{{
  "question": "{question['question']}",
  "options": {json.dumps(question['options'], ensure_ascii=False)},
  "correct_answer": "{question['correct_answer']}",
  "explanation": "**Respuesta correcta: {question['correct_answer']}) ...**\\n\\nExplicación mejorada...\\n\\n**Por qué las otras opciones son incorrectas:**\\n- A) ...\\n- C) ...\\n- D) ...\\n\\n**Concepto clave:** ...",
  "domain": "{domain}"
}}

IMPORTANTE: No cambies la pregunta ni las opciones, solo mejora la explicación."""

        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            enriched = json.loads(response.choices[0].message.content)

            # Asegurar campos requeridos
            enriched['domain'] = domain  # Forzar dominio inferido
            enriched['retrieved_context'] = context[:500]
            enriched['source'] = 'real_exam_validated_by_human'

            return enriched

        except Exception as e:
            print(f"   ⚠️ Error enriqueciendo pregunta {question['number']}: {e}")
            # Fallback: devolver pregunta original con formato mínimo
            return {
                'question': question['question'],
                'options': question['options'],
                'correct_answer': question['correct_answer'],
                'explanation': question['explanation_original'],
                'domain': domain,
                'source': 'real_exam_validated_by_human',
                'retrieved_context': ''
            }

    def process_all(self, output_file: str = "questions_real_enriched.json", limit: Optional[int] = None):
        """Procesa todas las preguntas"""

        # 1. Parsear preguntas
        raw_questions = self.parse_questions_from_txt()

        if not raw_questions:
            print("❌ No se encontraron preguntas en el archivo")
            return

        # Limitar si se especifica
        if limit:
            raw_questions = raw_questions[:limit]
            print(f"   ℹ️ Limitando a primeras {limit} preguntas para prueba")

        # 2. Enriquecer con RAG
        print(f"\n🚀 Enriqueciendo {len(raw_questions)} preguntas con RAG")
        print("="*70)

        enriched_questions = []
        for q in tqdm(raw_questions, desc="Enriqueciendo"):
            enriched = self.enrich_with_rag(q)
            if enriched:
                enriched_questions.append(enriched)

        # 3. Guardar
        output_path = OUTPUT_DIR / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(enriched_questions, f, indent=2, ensure_ascii=False)

        # 4. Resumen
        print("\n" + "="*70)
        print("✅ PROCESAMIENTO COMPLETADO")
        print("="*70)
        print(f"Preguntas procesadas: {len(enriched_questions)}")
        print(f"Guardado en: {output_path}")

        # Distribución por dominio
        domain_count = {}
        for q in enriched_questions:
            domain = q.get('domain', 'Unknown')
            domain_count[domain] = domain_count.get(domain, 0) + 1

        print("\n📊 Distribución por dominio:")
        for domain, count in sorted(domain_count.items()):
            print(f"   • {domain}: {count} preguntas")

        print("\n📋 Siguiente paso:")
        print(f"   python scripts/7_merge_questions.py")

        return enriched_questions


def main():
    import argparse
    arg_parser = argparse.ArgumentParser(description="Parsea y enriquece preguntas reales")
    arg_parser.add_argument("--limit", type=int, help="Limitar número de preguntas (para pruebas)")
    args = arg_parser.parse_args()

    parser = RealQuestionParser()
    parser.load_rag_system()
    questions = parser.process_all(limit=args.limit)

    # Preview
    if questions:
        print("\n" + "="*70)
        print("📋 PREVIEW DE PRIMERA PREGUNTA")
        print("="*70)
        q = questions[0]
        print(f"\nDominio: {q['domain']}")
        print(f"Fuente: {q['source']}")
        print(f"\nPregunta: {q['question']}")
        print(f"\nOpciones:")
        for letter, text in q['options'].items():
            marker = "✅" if letter == q['correct_answer'] else "  "
            print(f"  {marker} {letter}) {text}")
        print(f"\nExplicación: {q['explanation'][:200]}...")


if __name__ == "__main__":
    main()
