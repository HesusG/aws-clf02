#!/usr/bin/env python3
"""
Parser de Preguntas AWS CLF-C02
Convierte el archivo de texto a JSON estructurado según dominios oficiales
Incluye validaciones y reflexiones automáticas
"""

import re
import json
from typing import List, Dict, Optional
from collections import Counter

# Dominios oficiales AWS CLF-C02
OFFICIAL_DOMAINS = {
    "Domain 1: Cloud Concepts": {
        "weight": 24,
        "keywords": ["beneficios", "cloud", "escalabilidad", "elasticidad", "agilidad",
                     "alta disponibilidad", "tolerancia a fallos", "economía", "migración"]
    },
    "Domain 2: Security and Compliance": {
        "weight": 30,
        "keywords": ["seguridad", "IAM", "Shield", "WAF", "GuardDuty", "Inspector",
                     "responsabilidad compartida", "cifrado", "compliance", "políticas"]
    },
    "Domain 3: Cloud Technology and Services": {
        "weight": 34,
        "keywords": ["EC2", "S3", "Lambda", "RDS", "DynamoDB", "ECS", "EKS", "VPC",
                     "CloudFront", "Route 53", "contenedor", "almacenamiento", "base de datos"]
    },
    "Domain 4: Billing, Pricing, and Support": {
        "weight": 12,
        "keywords": ["facturación", "precio", "costo", "soporte", "Trusted Advisor",
                     "AWS Support", "Cost Explorer", "presupuesto", "TCO", "ROI", "CAF"]
    }
}

# Servicios AWS actuales (verificados 2025)
VALID_AWS_SERVICES = {
    # Security
    "AWS Shield", "Amazon GuardDuty", "AWS WAF", "Amazon Inspector", "AWS IAM",
    "AWS KMS", "AWS Secrets Manager", "AWS Certificate Manager",
    # Compute
    "Amazon EC2", "AWS Lambda", "AWS Elastic Beanstalk", "AWS Fargate",
    # Containers
    "Amazon ECS", "Amazon EKS", "Amazon ECR",
    # Storage
    "Amazon S3", "Amazon EBS", "Amazon EFS", "AWS Storage Gateway",
    "AWS Snowball", "AWS DataSync",
    # Database
    "Amazon RDS", "Amazon DynamoDB", "Amazon Aurora", "Amazon Redshift",
    "Amazon ElastiCache", "Amazon Neptune",
    # Networking
    "Amazon VPC", "Amazon CloudFront", "Amazon Route 53", "AWS Direct Connect",
    "Elastic Load Balancing", "AWS VPN",
    # AI/ML
    "Amazon Rekognition", "Amazon Textract", "Amazon Comprehend",
    "Amazon Transcribe", "Amazon Polly", "Amazon Translate", "Amazon SageMaker",
    # Analytics
    "Amazon Athena", "AWS Glue", "Amazon QuickSight", "Amazon Kinesis",
    # Management
    "AWS CloudFormation", "AWS CloudTrail", "Amazon CloudWatch",
    "AWS Config", "AWS Systems Manager", "AWS Trusted Advisor",
    # Support & Billing
    "AWS Cost Explorer", "AWS Budgets", "AWS Organizations"
}


class QuestionParser:
    def __init__(self, txt_file_path: str):
        self.txt_file_path = txt_file_path
        self.questions = []
        self.validation_errors = []
        self.reflection_notes = []

    def parse(self) -> List[Dict]:
        """Parse el archivo de texto y extrae preguntas"""
        with open(self.txt_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        current_question = None
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Detectar inicio de pregunta: número. ¿...?
            question_match = re.match(r'^(\d+)\.\s+(¿.+)$', line)

            if question_match:
                # Si hay una pregunta anterior, procesarla
                if current_question and current_question.get('options'):
                    self._process_question(current_question)

                # Iniciar nueva pregunta
                question_text = question_match.group(2).strip()

                # Si la pregunta continúa en la siguiente línea
                j = i + 1
                while j < len(lines) and not re.match(r'^[A-D]\)', lines[j].strip()):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith('✔') and not next_line.startswith('📌'):
                        question_text += ' ' + next_line
                    if '?' in next_line:
                        break
                    j += 1

                current_question = {
                    'number': int(question_match.group(1)),
                    'question': question_text,
                    'options': {},
                    'correct_answer': None,
                    'explanation': '',
                    'context': ''
                }

            # Detectar opciones de respuesta (A) B) C) D))
            elif current_question and re.match(r'^[A-D]\)', line):
                option_match = re.match(r'^([A-D])\)\s+(.+)', line)
                if option_match:
                    letter = option_match.group(1)
                    text = option_match.group(2).strip()

                    # Detectar si tiene ✅ (respuesta correcta)
                    if '✅' in text:
                        current_question['correct_answer'] = letter
                        text = text.replace('✅', '').strip()

                    current_question['options'][letter] = text

            # Detectar explicación
            elif current_question and line.startswith('✔ Correcta:'):
                explanation = line.replace('✔ Correcta:', '').strip()

                # Buscar respuesta correcta si no se encontró antes
                answer_match = re.search(r'([A-D])\)', explanation)
                if answer_match and not current_question['correct_answer']:
                    current_question['correct_answer'] = answer_match.group(1)

                # Continuar leyendo la explicación en líneas siguientes
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line.startswith('❌') or next_line.startswith('📌'):
                        j += 1
                        continue
                    if re.match(r'^\d+\.', next_line) or not next_line:
                        break
                    explanation += ' ' + next_line
                    j += 1

                current_question['explanation'] = explanation

            i += 1

        # Procesar última pregunta
        if current_question and current_question.get('options'):
            self._process_question(current_question)

        return self.questions

    def _process_question(self, q_data: Dict):
        """Procesa una pregunta individual"""
        options = q_data['options']
        correct_letter = q_data['correct_answer']
        explanation = q_data['explanation']

        # Asignar dominio
        domain = self._classify_domain(q_data['question'] + ' ' + ' '.join(options.values()))

        # Validar pregunta
        is_valid, errors = self._validate_question(q_data['number'], q_data['question'],
                                                     options, correct_letter)

        if is_valid:
            question_obj = {
                'id': len(self.questions) + 1,
                'originalNumber': q_data['number'],
                'domain': domain,
                'question': q_data['question'],
                'options': options,
                'correctAnswer': correct_letter,
                'explanation': explanation,
                'services': self._extract_services(q_data['question'] + ' ' + ' '.join(options.values()))
            }
            self.questions.append(question_obj)
        else:
            self.validation_errors.extend(errors)

    def _classify_domain(self, text: str) -> str:
        """Clasifica la pregunta en un dominio oficial AWS"""
        scores = {}
        text_lower = text.lower()

        for domain, info in OFFICIAL_DOMAINS.items():
            score = sum(1 for keyword in info['keywords'] if keyword.lower() in text_lower)
            scores[domain] = score

        # Retornar el dominio con mayor score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        else:
            return "Domain 3: Cloud Technology and Services"  # Default

    def _extract_services(self, text: str) -> List[str]:
        """Extrae servicios AWS mencionados en el texto"""
        services = []
        for service in VALID_AWS_SERVICES:
            if service in text or service.replace('Amazon ', '') in text or service.replace('AWS ', '') in text:
                services.append(service)
        return services

    def _validate_question(self, number: int, question: str, options: Dict,
                           correct_answer: Optional[str]) -> tuple:
        """Valida una pregunta"""
        errors = []

        # Validación 1: Debe tener 4 opciones
        if len(options) != 4:
            errors.append(f"Q{number}: Solo tiene {len(options)} opciones (necesita 4)")

        # Validación 2: Debe tener todas las letras A-D
        expected_letters = set(['A', 'B', 'C', 'D'])
        if set(options.keys()) != expected_letters:
            errors.append(f"Q{number}: Opciones incompletas {options.keys()}")

        # Validación 3: Debe tener respuesta correcta marcada
        if not correct_answer:
            errors.append(f"Q{number}: No tiene respuesta correcta marcada")

        # Validación 4: La respuesta correcta debe estar en las opciones
        if correct_answer and correct_answer not in options:
            errors.append(f"Q{number}: Respuesta correcta '{correct_answer}' no está en opciones")

        # Validación 5: Debe mencionar al menos un servicio AWS válido
        services = self._extract_services(question + ' ' + ' '.join(options.values()))
        if not services:
            self.reflection_notes.append(f"Q{number}: No menciona servicios AWS específicos")

        return len(errors) == 0, errors

    def generate_reflection_report(self) -> Dict:
        """Genera reporte de reflexión sobre la calidad del contenido"""
        # Contar preguntas por dominio
        domain_counts = Counter([q['domain'] for q in self.questions])

        # Calcular porcentajes
        total = len(self.questions)
        domain_percentages = {
            domain: (count / total * 100) for domain, count in domain_counts.items()
        }

        # Comparar con porcentajes oficiales
        domain_comparison = {}
        for domain, info in OFFICIAL_DOMAINS.items():
            actual = domain_percentages.get(domain, 0)
            expected = info['weight']
            domain_comparison[domain] = {
                'actual': round(actual, 1),
                'expected': expected,
                'difference': round(actual - expected, 1)
            }

        # Servicios más mencionados
        all_services = []
        for q in self.questions:
            all_services.extend(q['services'])
        service_counts = Counter(all_services)

        return {
            'total_questions': total,
            'valid_questions': len(self.questions),
            'validation_errors': len(self.validation_errors),
            'domain_distribution': domain_comparison,
            'top_services': service_counts.most_common(10),
            'reflection_notes': self.reflection_notes[:20]  # Top 20
        }

    def save_to_json(self, output_path: str):
        """Guarda preguntas en formato JSON"""
        data = {
            'metadata': {
                'exam': 'AWS Certified Cloud Practitioner',
                'version': 'CLF-C02',
                'total_questions': len(self.questions),
                'generated_date': '2025-10-05',
                'source': 'EXAMEN REAL MAESTRO AWS'
            },
            'domains': OFFICIAL_DOMAINS,
            'questions': self.questions
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    print("🚀 Parser de Preguntas AWS CLF-C02")
    print("=" * 60)

    input_file = "/mnt/c/Users/HG_Co/OneDrive/Documents/Github/aws-clf02/document/EXAMEN REAL  MAESTRO AWS.txt"
    output_file = "/mnt/c/Users/HG_Co/OneDrive/Documents/Github/aws-clf02/data/questions.json"

    parser = QuestionParser(input_file)

    print("\n📖 Parseando preguntas...")
    questions = parser.parse()

    print(f"\n✅ Preguntas válidas encontradas: {len(questions)}")

    if parser.validation_errors:
        print(f"\n⚠️  Errores de validación: {len(parser.validation_errors)}")
        for error in parser.validation_errors[:10]:  # Mostrar primeros 10
            print(f"   - {error}")

    print("\n🔍 Generando reporte de reflexión...")
    reflection = parser.generate_reflection_report()

    print("\n📊 DISTRIBUCIÓN POR DOMINIO:")
    for domain, stats in reflection['domain_distribution'].items():
        print(f"\n   {domain}")
        print(f"      Real: {stats['actual']}% | Esperado: {stats['expected']}% | Diff: {stats['difference']:+.1f}%")

    print("\n🔧 TOP 10 SERVICIOS AWS MENCIONADOS:")
    for service, count in reflection['top_services']:
        print(f"   - {service}: {count} veces")

    if reflection['reflection_notes']:
        print(f"\n💭 NOTAS DE REFLEXIÓN ({len(reflection['reflection_notes'])}):")
        for note in reflection['reflection_notes'][:5]:
            print(f"   - {note}")

    print(f"\n💾 Guardando en: {output_file}")
    parser.save_to_json(output_file)

    print("\n✨ Proceso completado!")

    # Guardar también el reporte
    with open("/mnt/c/Users/HG_Co/OneDrive/Documents/Github/aws-clf02/data/reflection_report.json", 'w') as f:
        json.dump(reflection, f, indent=2, ensure_ascii=False)

    print("📄 Reporte de reflexión guardado en: data/reflection_report.json")


if __name__ == "__main__":
    main()
