#!/usr/bin/env python3
"""
Script 3: Cost Estimator
Calculadora interactiva de costos para generación de preguntas
"""

import os
import sys
from pathlib import Path
import tiktoken

PROJECT_ROOT = Path(__file__).parent.parent

# Precios OpenAI (2025)
PRICES = {
    "gpt-4o-mini": {
        "input": 0.15 / 1_000_000,   # $0.15 per 1M tokens
        "output": 0.60 / 1_000_000   # $0.60 per 1M tokens
    },
    "text-embedding-3-small": {
        "input": 0.02 / 1_000_000    # $0.02 per 1M tokens
    }
}

# Dominios oficiales CLF-C02
DOMAINS = {
    "Domain 1: Cloud Concepts": 24,
    "Domain 2: Security and Compliance": 30,
    "Domain 3: Cloud Technology and Services": 34,
    "Domain 4: Billing, Pricing, and Support": 12
}


def count_tokens(text: str) -> int:
    """Cuenta tokens usando tiktoken"""
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def estimate_generation_cost(num_questions: int):
    """Estima costo de generación de preguntas con RAG"""

    # Estimaciones por pregunta
    context_tokens = 800  # Contexto RAG (3 chunks de ~250 tokens c/u)
    system_prompt_tokens = 200  # System prompt
    user_prompt_tokens = 100  # User prompt con instrucciones
    examples_tokens = 300  # Few-shot examples

    input_per_question = context_tokens + system_prompt_tokens + user_prompt_tokens + examples_tokens

    # Output esperado
    question_tokens = 50  # Pregunta
    options_tokens = 100  # 4 opciones
    explanation_tokens = 250  # Explicación pedagógica detallada
    output_per_question = question_tokens + options_tokens + explanation_tokens

    # Totales
    total_input = num_questions * input_per_question
    total_output = num_questions * output_per_question

    # Costos
    input_cost = total_input * PRICES["gpt-4o-mini"]["input"]
    output_cost = total_output * PRICES["gpt-4o-mini"]["output"]
    generation_cost = input_cost + output_cost

    return {
        "num_questions": num_questions,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "generation_cost": generation_cost
    }


def estimate_evaluation_cost(num_questions: int):
    """Estima costo de evaluaciones con Phoenix"""

    # Por cada pregunta: 3 evaluaciones (QA, Hallucination, Compliance)
    evals_per_question = 3

    # Tokens por evaluación
    eval_input_per_question = 300  # Pregunta + contexto + criterios
    eval_output_per_question = 100  # Score + reasoning

    total_evals = num_questions * evals_per_question
    total_input = total_evals * eval_input_per_question
    total_output = total_evals * eval_output_per_question

    # Costos
    input_cost = total_input * PRICES["gpt-4o-mini"]["input"]
    output_cost = total_output * PRICES["gpt-4o-mini"]["output"]
    eval_cost = input_cost + output_cost

    return {
        "total_evaluations": total_evals,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "eval_cost": eval_cost
    }


def distribute_questions_by_domain(total_questions: int) -> dict:
    """Distribuye preguntas según porcentajes oficiales CLF-C02"""
    distribution = {}
    for domain, percentage in DOMAINS.items():
        count = round((percentage / 100) * total_questions)
        distribution[domain] = count

    # Ajustar para que sume exactamente total_questions
    diff = total_questions - sum(distribution.values())
    if diff != 0:
        # Agregar/quitar del dominio con mayor porcentaje
        max_domain = max(DOMAINS, key=DOMAINS.get)
        distribution[max_domain] += diff

    return distribution


def print_cost_breakdown(generation, evaluation, buffer_pct=30):
    """Imprime desglose detallado de costos"""

    print("\n" + "="*70)
    print("💰 DESGLOSE DE COSTOS")
    print("="*70)

    print(f"\n📊 Generación de {generation['num_questions']} preguntas con RAG:")
    print(f"   Input tokens:  {generation['total_input_tokens']:,} tokens")
    print(f"   Output tokens: {generation['total_output_tokens']:,} tokens")
    print(f"   Costo input:   ${generation['input_cost']:.4f}")
    print(f"   Costo output:  ${generation['output_cost']:.4f}")
    print(f"   {'─'*66}")
    print(f"   Subtotal:      ${generation['generation_cost']:.4f}")

    print(f"\n🔍 Phoenix Evaluations ({evaluation['total_evaluations']} evals):")
    print(f"   Input tokens:  {evaluation['total_input_tokens']:,} tokens")
    print(f"   Output tokens: {evaluation['total_output_tokens']:,} tokens")
    print(f"   Costo input:   ${evaluation['input_cost']:.4f}")
    print(f"   Costo output:  ${evaluation['output_cost']:.4f}")
    print(f"   {'─'*66}")
    print(f"   Subtotal:      ${evaluation['eval_cost']:.4f}")

    subtotal = generation['generation_cost'] + evaluation['eval_cost']
    buffer_amount = subtotal * (buffer_pct / 100)
    total_with_buffer = subtotal + buffer_amount

    print(f"\n{'═'*70}")
    print(f"   Subtotal:                ${subtotal:.4f}")
    print(f"   Buffer (+{buffer_pct}%):           ${buffer_amount:.4f}")
    print(f"   {'─'*66}")
    print(f"   TOTAL ESTIMADO:          ${total_with_buffer:.4f} USD")
    print(f"{'═'*70}")


def print_distribution(distribution: dict, total: int):
    """Imprime distribución de preguntas por dominio"""

    print("\n" + "="*70)
    print("📋 DISTRIBUCIÓN POR DOMINIO CLF-C02")
    print("="*70)

    for domain, count in distribution.items():
        percentage = DOMAINS[domain]
        bar_length = int(percentage / 2)  # Scale for display
        bar = "█" * bar_length

        print(f"\n{domain.split(': ')[1]}")
        print(f"   {bar} {percentage}%")
        print(f"   {count} preguntas")


def interactive_estimator():
    """Calculadora interactiva"""

    print("\n" + "="*70)
    print("🧮 CALCULADORA DE COSTOS - GENERACIÓN DE PREGUNTAS AWS CLF-C02")
    print("="*70)

    print("\nEste script te ayudará a estimar el costo de generar preguntas")
    print("usando GPT-4o-mini con RAG + Phoenix Evaluations")

    # Preguntar cantidad
    print("\n" + "-"*70)
    print("¿Cuántas preguntas deseas generar?")
    print("  Sugerencias:")
    print("    - 100 preguntas = práctica básica (~$0.10)")
    print("    - 200 preguntas = práctica completa (~$0.20)")
    print("    - 300 preguntas = banco extenso (~$0.30)")
    print("    - 500 preguntas = banco profesional (~$0.50)")

    while True:
        try:
            num_questions = int(input("\nCantidad de preguntas: "))
            if num_questions <= 0:
                print("❌ Debe ser un número positivo")
                continue
            if num_questions > 1000:
                print("⚠️  Advertencia: Más de 1000 preguntas puede ser costoso")
                confirm = input("   ¿Continuar? (s/n): ")
                if confirm.lower() != 's':
                    continue
            break
        except ValueError:
            print("❌ Por favor ingresa un número válido")

    # Calcular costos
    generation = estimate_generation_cost(num_questions)
    evaluation = estimate_evaluation_cost(num_questions)

    # Mostrar distribución por dominio
    distribution = distribute_questions_by_domain(num_questions)
    print_distribution(distribution, num_questions)

    # Mostrar costos
    print_cost_breakdown(generation, evaluation)

    # Confirmación
    print("\n" + "="*70)
    print("¿Deseas proceder con la generación?")
    print("="*70)
    print("\nSiguiente paso:")
    print("   python scripts/4_generate_questions.py --count", num_questions)

    confirm = input("\n¿Generar preguntas ahora? (s/n): ")

    if confirm.lower() == 's':
        print("\n✅ Ejecutando generador...")
        import subprocess
        subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "4_generate_questions.py"), "--count", str(num_questions)])
    else:
        print("\n👋 ¡Hasta luego! Puedes ejecutar el generador cuando estés listo.")


def main():
    try:
        interactive_estimator()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelado por el usuario")
        sys.exit(0)


if __name__ == "__main__":
    main()
