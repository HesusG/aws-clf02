#!/usr/bin/env python3
"""
Script 6b: LLM-Based Question Parser
Usa GPT-4o-mini para extraer TODAS las preguntas del archivo EXAMEN REAL MAESTRO AWS.txt
Maneja formatos inconsistentes usando AI
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("❌ Error: OPENAI_API_KEY no encontrada en .env")
    sys.exit(1)

from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# Configuración
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_db"
INPUT_FILE = PROJECT_ROOT / "document" / "EXAMEN REAL  MAESTRO AWS.txt"
OUTPUT_DIR = PROJECT_ROOT / "data"

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Dominio mapping (mismo que antes)
TOPIC_TO_DOMAIN = {
    "shield": "Domain 2: Security and Compliance",
    "guardduty": "Domain 2: Security and Compliance",
    "waf": "Domain 2: Security and Compliance",
    "iam": "Domain 2: Security and Compliance",
    "inspector": "Domain 2: Security and Compliance",
    "responsabilidad": "Domain 2: Security and Compliance",
    "seguridad": "Domain 2: Security and Compliance",
    "ecs": "Domain 3: Cloud Technology and Services",
    "eks": "Domain 3: Cloud Technology and Services",
    "ecr": "Domain 3: Cloud Technology and Services",
    "fargate": "Domain 3: Cloud Technology and Services",
    "contenedor": "Domain 3: Cloud Technology and Services",
    "ec2": "Domain 3: Cloud Technology and Services",
    "spot": "Domain 3: Cloud Technology and Services",
    "reserved": "Domain 3: Cloud Technology and Services",
    "compute optimizer": "Domain 3: Cloud Technology and Services",
    "s3": "Domain 3: Cloud Technology and Services",
    "glacier": "Domain 3: Cloud Technology and Services",
    "ebs": "Domain 3: Cloud Technology and Services",
    "efs": "Domain 3: Cloud Technology and Services",
    "rds": "Domain 3: Cloud Technology and Services",
    "dynamodb": "Domain 3: Cloud Technology and Services",
    "aurora": "Domain 3: Cloud Technology and Services",
    "redshift": "Domain 3: Cloud Technology and Services",
    "vpc": "Domain 3: Cloud Technology and Services",
    "cloudfront": "Domain 3: Cloud Technology and Services",
    "route 53": "Domain 3: Cloud Technology and Services",
    "elastic load": "Domain 3: Cloud Technology and Services",
    "lambda": "Domain 3: Cloud Technology and Services",
    "pricing": "Domain 4: Billing, Pricing, and Support",
    "billing": "Domain 4: Billing, Pricing, and Support",
    "cost": "Domain 4: Billing, Pricing, and Support",
    "support": "Domain 4: Billing, Pricing, and Support",
    "trusted advisor": "Domain 4: Billing, Pricing, and Support",
    "escalabilidad": "Domain 1: Cloud Concepts",
    "elasticidad": "Domain 1: Cloud Concepts",
    "alta disponibilidad": "Domain 1: Cloud Concepts",
    "well-architected": "Domain 1: Cloud Concepts",
    "caf": "Domain 1: Cloud Concepts",
}


class LLMQuestionParser:
    def __init__(self):
        self.client = OpenAI()
        self.vectorstore = None

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

    def split_into_chunks(self, text: str, chunk_size: int = 3000) -> List[str]:
        """Divide el texto en chunks para procesar con LLM"""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1
            if current_size + line_size > chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(line)
            current_size += line_size

        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def extract_questions_from_chunk(self, chunk: str) -> List[Dict]:
        """Usa LLM para extraer preguntas de un chunk de texto"""

        system_prompt = """Eres un parser especializado en extraer preguntas de examen AWS de documentos de estudio.

Tu tarea es identificar TODAS las preguntas de examen en el texto proporcionado y extraerlas en formato JSON.

Formato de preguntas en el texto:
- Empiezan con número seguido de punto: "1. ¿Pregunta?"
- Tienen 4 opciones (A, B, C, D)
- Una opción tiene ✅ marcando la correcta
- Puede haber explicación después

IMPORTANTE:
- Extrae TODAS las preguntas que encuentres
- Si una pregunta no tiene las 4 opciones completas, ignórala
- Si no puedes determinar la respuesta correcta, usa null
- NO inventes información, solo extrae lo que está en el texto

Responde SOLO con un JSON array de preguntas."""

        user_prompt = f"""Extrae todas las preguntas de examen del siguiente texto:

{chunk}

Formato de salida:
[
  {{
    "question": "¿Texto de la pregunta?",
    "options": {{
      "A": "Opción A",
      "B": "Opción B",
      "C": "Opción C",
      "D": "Opción D"
    }},
    "correct_answer": "B"
  }}
]

Responde SOLO con el JSON array, sin texto adicional."""

        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Baja creatividad para extracción precisa
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content

            # El LLM puede devolver {"questions": [...]} o directamente [...]
            parsed = json.loads(content)
            if isinstance(parsed, dict) and 'questions' in parsed:
                return parsed['questions']
            elif isinstance(parsed, list):
                return parsed
            else:
                return []

        except Exception as e:
            print(f"   ⚠️ Error parseando chunk: {e}")
            return []

    def infer_domain(self, question: str, options: Dict[str, str]) -> str:
        """Infiere el dominio CLF-C02"""
        text = (question + ' ' + ' '.join(options.values())).lower()

        for keyword, domain in TOPIC_TO_DOMAIN.items():
            if keyword in text:
                return domain

        return "Domain 3: Cloud Technology and Services"

    def enrich_with_rag(self, question: Dict) -> Dict:
        """Enriquece explicación con RAG"""

        query = f"{question['question']} {' '.join(question['options'].values())}"
        docs = self.vectorstore.similarity_search(query, k=2)
        context = "\n\n".join([doc.page_content[:400] for doc in docs])

        domain = self.infer_domain(question['question'], question['options'])

        system_prompt = f"""Eres un experto en AWS CLF-C02.

Tienes una pregunta de examen real. Tu tarea es crear una explicación pedagógica completa usando el contexto oficial de AWS.

CONTEXTO AWS OFICIAL:
{context}

Mantén la pregunta, opciones y respuesta correcta EXACTAMENTE como están.
Genera una explicación estructurada y completa.
Responde SOLO con JSON válido."""

        user_prompt = f"""Pregunta:
{question['question']}

Opciones:
{json.dumps(question['options'], indent=2, ensure_ascii=False)}

Respuesta correcta: {question['correct_answer']}

Genera un JSON:
{{
  "question": "{question['question']}",
  "options": {json.dumps(question['options'], ensure_ascii=False)},
  "correct_answer": "{question['correct_answer']}",
  "explanation": "**Respuesta correcta: {question['correct_answer']}) ...**\\n\\n...\\n\\n**Por qué las otras opciones son incorrectas:**\\n- A) ...\\n\\n**Concepto clave:** ...",
  "domain": "{domain}"
}}"""

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
            enriched['domain'] = domain
            enriched['retrieved_context'] = context[:500]
            enriched['source'] = 'real_exam_validated_by_human'

            return enriched

        except Exception as e:
            print(f"   ⚠️ Error enriqueciendo: {e}")
            return {
                'question': question['question'],
                'options': question['options'],
                'correct_answer': question['correct_answer'],
                'explanation': 'Explicación no disponible',
                'domain': domain,
                'source': 'real_exam_validated_by_human',
                'retrieved_context': ''
            }

    def process_all(self, output_file: str = "questions_real_enriched.json"):
        """Procesa TODO el archivo usando LLM"""

        print(f"\n📖 Leyendo archivo: {INPUT_FILE.name}")
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            full_text = f.read()

        # Dividir en chunks
        chunks = self.split_into_chunks(full_text, chunk_size=4000)
        print(f"   📄 Dividido en {len(chunks)} chunks")

        # Extraer preguntas de cada chunk
        print(f"\n🤖 Extrayendo preguntas con LLM...")
        all_questions = []
        seen_questions = set()  # Deduplicar

        for i, chunk in enumerate(tqdm(chunks, desc="Procesando chunks"), 1):
            questions = self.extract_questions_from_chunk(chunk)

            for q in questions:
                # Deduplicar por texto de pregunta
                if q['question'] not in seen_questions:
                    seen_questions.add(q['question'])
                    all_questions.append(q)

        print(f"\n   ✅ Extraídas {len(all_questions)} preguntas únicas")

        # Enriquecer con RAG
        print(f"\n🚀 Enriqueciendo con RAG...")
        enriched_questions = []

        for q in tqdm(all_questions, desc="Enriqueciendo"):
            enriched = self.enrich_with_rag(q)
            if enriched:
                enriched_questions.append(enriched)

        # Guardar
        output_path = OUTPUT_DIR / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(enriched_questions, f, indent=2, ensure_ascii=False)

        # Resumen
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
            pct = (count / len(enriched_questions)) * 100 if enriched_questions else 0
            print(f"   • {domain}: {count} ({pct:.1f}%)")

        return enriched_questions


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Parsea preguntas usando LLM")
    parser.add_argument("--output", default="questions_real_enriched.json", help="Archivo de salida")
    args = parser.parse_args()

    llm_parser = LLMQuestionParser()
    llm_parser.load_rag_system()
    questions = llm_parser.process_all(args.output)

    # Preview
    if questions:
        print("\n" + "="*70)
        print("📋 PREVIEW (primeras 3 preguntas)")
        print("="*70)
        for i, q in enumerate(questions[:3], 1):
            print(f"\n{i}. {q['question'][:80]}...")
            print(f"   Dominio: {q['domain']}")
            print(f"   Respuesta: {q['correct_answer']}")


if __name__ == "__main__":
    main()
