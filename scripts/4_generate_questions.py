#!/usr/bin/env python3
"""
Script 4: Generate Questions with RAG
Genera preguntas de examen AWS CLF-C02 usando GPT-4o-mini con RAG
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict
import time

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
import tiktoken

# Configuración
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_db"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
OUTPUT_DIR = PROJECT_ROOT / "data"

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Dominios CLF-C02
DOMAINS = {
    "Domain 1: Cloud Concepts": 24,
    "Domain 2: Security and Compliance": 30,
    "Domain 3: Cloud Technology and Services": 34,
    "Domain 4: Billing, Pricing, and Support": 12
}

# Topics por dominio (para diversidad)
DOMAIN_TOPICS = {
    "Domain 1: Cloud Concepts": [
        "Beneficios de la nube AWS (escalabilidad, elasticidad, agilidad)",
        "Alta disponibilidad y tolerancia a fallos",
        "Economía de la nube (CapEx vs OpEx)",
        "Estrategias de migración a AWS (6Rs)",
        "Well-Architected Framework pilares"
    ],
    "Domain 2: Security and Compliance": [
        "Modelo de responsabilidad compartida",
        "AWS IAM (usuarios, grupos, roles, políticas)",
        "Servicios de seguridad (Shield, WAF, GuardDuty, Inspector)",
        "Encriptación y protección de datos",
        "Compliance y certificaciones AWS"
    ],
    "Domain 3: Cloud Technology and Services": [
        "Amazon EC2 (tipos de instancias, opciones de compra)",
        "Amazon S3 (clases de almacenamiento, características)",
        "Bases de datos AWS (RDS, DynamoDB, Aurora)",
        "Servicios de red (VPC, CloudFront, Route 53)",
        "Compute sin servidores (Lambda, Fargate)",
        "Contenedores (ECS, EKS, ECR)",
        "AI/ML services (Rekognition, Comprehend, etc.)"
    ],
    "Domain 4: Billing, Pricing, and Support": [
        "Modelos de pricing AWS",
        "AWS Cost Explorer y AWS Budgets",
        "Planes de soporte AWS",
        "AWS Trusted Advisor",
        "Cloud Adoption Framework (CAF)"
    ]
}


class QuestionGenerator:
    def __init__(self):
        self.client = OpenAI()
        self.vectorstore = None
        self.system_prompt = None
        self.examples = None
        self.encoding = tiktoken.get_encoding("cl100k_base")

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

    def load_prompts(self):
        """Carga system prompt y ejemplos"""
        print("📝 Cargando prompts...")

        # System prompt
        system_path = PROMPTS_DIR / "system.txt"
        with open(system_path, 'r', encoding='utf-8') as f:
            self.system_prompt = f.read()

        # Examples
        examples_path = PROMPTS_DIR / "examples.json"
        with open(examples_path, 'r', encoding='utf-8') as f:
            self.examples = json.load(f)

        print("   ✅ Prompts cargados")

    def get_relevant_context(self, domain: str, topic: str, k: int = 3) -> str:
        """Obtiene contexto relevante usando RAG"""
        query = f"{domain}: {topic}"
        docs = self.vectorstore.similarity_search(query, k=k)

        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('source', 'Unknown')
            content = doc.page_content[:500]  # Limitar tamaño
            context_parts.append(f"[Fuente {i}: {source}]\n{content}")

        return "\n\n".join(context_parts)

    def get_example_for_domain(self, domain: str) -> dict:
        """Obtiene ejemplo few-shot para el dominio"""
        for ex in self.examples:
            if ex["domain"] == domain:
                return ex["example"]
        return self.examples[0]["example"]  # Fallback

    def count_tokens(self, text: str) -> int:
        """Cuenta tokens"""
        return len(self.encoding.encode(text))

    def generate_question(self, domain: str, topic: str) -> dict:
        """Genera una pregunta usando RAG + GPT-4o-mini"""

        # 1. Obtener contexto relevante
        context = self.get_relevant_context(domain, topic)

        # 2. Obtener ejemplo few-shot
        example = self.get_example_for_domain(domain)

        # 3. Construir system prompt
        system_msg = self.system_prompt.format(
            context=context,
            domain=domain
        )

        # 4. Construir user prompt
        user_msg = f"""Genera UNA pregunta de examen sobre: {topic}

Sigue el formato del siguiente ejemplo:

{json.dumps(example, indent=2, ensure_ascii=False)}

IMPORTANTE:
- Usa SOLO información del contexto proporcionado
- La pregunta debe ser basada en un escenario real
- Las 4 opciones deben ser plausibles
- La explicación debe ser educativa y completa
- Responde SOLO con JSON válido, sin texto adicional"""

        # 5. Llamar a GPT-4o-mini
        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.8,  # Mayor creatividad
                response_format={"type": "json_object"}
            )

            # 6. Parsear respuesta
            content = response.choices[0].message.content
            question_data = json.loads(content)

            # 7. Agregar metadata
            question_data["domain"] = domain
            question_data["topic"] = topic
            question_data["retrieved_context"] = context[:500]  # Guardar para evals
            question_data["tokens_used"] = {
                "input": response.usage.prompt_tokens,
                "output": response.usage.completion_tokens,
                "total": response.usage.total_tokens
            }

            return question_data

        except Exception as e:
            print(f"\n❌ Error generando pregunta: {str(e)}")
            return None

    def distribute_questions(self, total: int) -> List[tuple]:
        """Distribuye preguntas por dominio y topic"""
        distribution = []

        for domain, percentage in DOMAINS.items():
            count = round((percentage / 100) * total)
            topics = DOMAIN_TOPICS[domain]

            # Distribuir entre topics
            questions_per_topic = count // len(topics)
            remainder = count % len(topics)

            for i, topic in enumerate(topics):
                topic_count = questions_per_topic
                if i < remainder:
                    topic_count += 1

                for _ in range(topic_count):
                    distribution.append((domain, topic))

        return distribution

    def generate_batch(self, count: int, output_file: str = "questions_raw.json"):
        """Genera un batch de preguntas"""

        print(f"\n🚀 Generando {count} preguntas con RAG + GPT-4o-mini")
        print(f"   Modelo: {MODEL}")
        print("="*70)

        # Distribuir preguntas
        distribution = self.distribute_questions(count)

        questions = []
        total_cost = 0.0
        failed_count = 0

        # Generar con progress bar
        for i, (domain, topic) in enumerate(tqdm(distribution, desc="Generando"), 1):
            question = self.generate_question(domain, topic)

            if question:
                questions.append(question)

                # Calcular costo
                input_cost = (question["tokens_used"]["input"] / 1_000_000) * 0.15
                output_cost = (question["tokens_used"]["output"] / 1_000_000) * 0.60
                total_cost += input_cost + output_cost
            else:
                failed_count += 1

            # Rate limiting (evitar rate limits de OpenAI)
            if i % 10 == 0:
                time.sleep(1)

        # Guardar preguntas
        output_path = OUTPUT_DIR / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)

        # Resumen
        print("\n" + "="*70)
        print("✅ GENERACIÓN COMPLETADA")
        print("="*70)
        print(f"Preguntas generadas: {len(questions)}")
        print(f"Preguntas fallidas: {failed_count}")
        print(f"Costo total: ${total_cost:.4f} USD")
        print(f"Guardado en: {output_path}")
        print("\n📋 Siguiente paso:")
        print(f"   python scripts/5_evaluate_with_phoenix.py --input {output_file}")

        return questions


def main():
    parser = argparse.ArgumentParser(description="Genera preguntas AWS CLF-C02 con RAG")
    parser.add_argument("--count", type=int, default=50, help="Número de preguntas a generar")
    parser.add_argument("--output", type=str, default="questions_raw.json", help="Archivo de salida")
    args = parser.parse_args()

    # Inicializar generador
    generator = QuestionGenerator()
    generator.load_rag_system()
    generator.load_prompts()

    # Generar preguntas
    questions = generator.generate_batch(args.count, args.output)

    # Mostrar preview de primera pregunta
    if questions:
        print("\n" + "="*70)
        print("📋 PREVIEW DE PRIMERA PREGUNTA")
        print("="*70)
        q = questions[0]
        print(f"\nDominio: {q['domain']}")
        print(f"Topic: {q['topic']}")
        print(f"\nPregunta: {q['question']}")
        print(f"\nOpciones:")
        for letter, text in q['options'].items():
            marker = "✅" if letter == q['correct_answer'] else "  "
            print(f"  {marker} {letter}) {text}")
        print(f"\nExplicación: {q['explanation'][:200]}...")


if __name__ == "__main__":
    main()
