#!/usr/bin/env python3
"""
Script 7: Merge Questions
Combina preguntas reales enriquecidas con preguntas generadas para el simulador
"""

import json
import sys
from pathlib import Path
from typing import List, Dict

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

def load_questions(filename: str) -> List[Dict]:
    """Carga preguntas desde un archivo JSON"""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"⚠️ Archivo no encontrado: {filepath}")
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Si es un array directo, devolverlo
    if isinstance(data, list):
        return data
    # Si tiene wrapper "questions", extraerlo
    elif isinstance(data, dict) and 'questions' in data:
        return data['questions']
    else:
        print(f"⚠️ Formato desconocido en {filename}")
        return []


def format_for_simulator(questions: List[Dict]) -> Dict:
    """Formatea preguntas para el simulador"""

    formatted = []
    for i, q in enumerate(questions, 1):
        # Asegurar que tiene todos los campos requeridos
        formatted_q = {
            'id': f"q{i}",
            'question': q.get('question', ''),
            'options': q.get('options', {}),
            'correctAnswer': q.get('correct_answer') or q.get('correctAnswer', ''),
            'explanation': q.get('explanation', ''),
            'domain': q.get('domain', 'Domain 3: Cloud Technology and Services'),
        }

        # Campos opcionales
        if 'topic' in q:
            formatted_q['topic'] = q['topic']
        if 'source' in q:
            formatted_q['source'] = q['source']
        if 'scenario' in q:
            formatted_q['scenario'] = q['scenario']

        formatted.append(formatted_q)

    return {'questions': formatted}


def merge_questions():
    """Combina todas las preguntas disponibles"""

    print("🔄 Combinando preguntas para el simulador")
    print("="*70)

    all_questions = []

    # 1. Cargar preguntas reales enriquecidas
    real_questions = load_questions("questions_real_enriched.json")
    if real_questions:
        print(f"✅ Preguntas reales validadas: {len(real_questions)}")
        all_questions.extend(real_questions)
    else:
        print("⚠️ No se encontraron preguntas reales enriquecidas")
        print("   Ejecuta: python scripts/6_parse_real_questions.py")

    # 2. Cargar preguntas generadas evaluadas (si existen)
    evaluated_questions = load_questions("questions_evaluated.json")
    if evaluated_questions:
        print(f"✅ Preguntas generadas (evaluadas): {len(evaluated_questions)}")
        all_questions.extend(evaluated_questions)

    # 3. Si no hay evaluated, usar las raw
    if not evaluated_questions:
        raw_questions = load_questions("questions_raw.json")
        if raw_questions:
            print(f"⚠️ Usando preguntas raw (no evaluadas): {len(raw_questions)}")
            all_questions.extend(raw_questions)

    if not all_questions:
        print("\n❌ No se encontraron preguntas para combinar")
        print("\nEjecuta primero:")
        print("   python scripts/6_parse_real_questions.py")
        print("   python scripts/4_generate_questions.py --count 100")
        sys.exit(1)

    # 4. Formatear para simulador
    formatted = format_for_simulator(all_questions)

    # 5. Guardar
    output_path = DATA_DIR / "questions.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(formatted, f, indent=2, ensure_ascii=False)

    # 6. Resumen
    print("\n" + "="*70)
    print("✅ COMBINACIÓN COMPLETADA")
    print("="*70)
    print(f"Total de preguntas: {len(all_questions)}")
    print(f"Guardado en: {output_path}")

    # Distribución por dominio
    domain_count = {}
    source_count = {}

    for q in all_questions:
        domain = q.get('domain', 'Unknown')
        domain_count[domain] = domain_count.get(domain, 0) + 1

        source = q.get('source', 'generated')
        source_count[source] = source_count.get(source, 0) + 1

    print("\n📊 Distribución por dominio:")
    for domain, count in sorted(domain_count.items()):
        pct = (count / len(all_questions)) * 100
        print(f"   • {domain}: {count} ({pct:.1f}%)")

    print("\n📚 Distribución por fuente:")
    for source, count in sorted(source_count.items()):
        pct = (count / len(all_questions)) * 100
        print(f"   • {source}: {count} ({pct:.1f}%)")

    print("\n🚀 Siguiente paso:")
    print("   git add data/questions.json")
    print("   git commit -m 'Actualizar preguntas con contenido real validado'")
    print("   git push origin main")

    return formatted


if __name__ == "__main__":
    merge_questions()
