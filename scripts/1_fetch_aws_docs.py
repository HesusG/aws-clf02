#!/usr/bin/env python3
"""
Script 1: Fetch AWS Documentation
Descarga documentación oficial de AWS para usar en RAG
"""

import os
import requests
from pathlib import Path
from typing import List, Dict
import time

# Directorios
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "data" / "aws_docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# URLs de documentación oficial AWS
AWS_DOCS_SOURCES = {
    "exam_guide": {
        "url": "https://d1.awsstatic.com/training-and-certification/docs-cloud-practitioner/AWS-Certified-Cloud-Practitioner_Exam-Guide.pdf",
        "filename": "AWS-CLF-C02-Exam-Guide.pdf",
        "type": "pdf"
    },
    "well_architected": {
        "url": "https://docs.aws.amazon.com/wellarchitected/latest/framework/wellarchitected-framework.pdf",
        "filename": "AWS-Well-Architected-Framework.pdf",
        "type": "pdf"
    },
    "caf_whitepaper": {
        "url": "https://docs.aws.amazon.com/whitepapers/latest/overview-aws-cloud-adoption-framework/welcome.html",
        "filename": "AWS-CAF.html",
        "type": "html"
    }
}

# Service FAQs (formato HTML)
SERVICE_FAQS = {
    "ec2": "https://aws.amazon.com/ec2/faqs/",
    "s3": "https://aws.amazon.com/s3/faqs/",
    "lambda": "https://aws.amazon.com/lambda/faqs/",
    "rds": "https://aws.amazon.com/rds/faqs/",
    "dynamodb": "https://aws.amazon.com/dynamodb/faqs/",
    "vpc": "https://aws.amazon.com/vpc/faqs/",
    "iam": "https://aws.amazon.com/iam/faqs/",
    "cloudformation": "https://aws.amazon.com/cloudformation/faqs/",
    "cloudwatch": "https://aws.amazon.com/cloudwatch/faqs/",
    "cloudtrail": "https://aws.amazon.com/cloudtrail/faqs/",
    "elasticbeanstalk": "https://aws.amazon.com/elasticbeanstalk/faqs/",
    "ecs": "https://aws.amazon.com/ecs/faqs/",
    "eks": "https://aws.amazon.com/eks/faqs/",
    "fargate": "https://aws.amazon.com/fargate/faqs/",
    "elasticache": "https://aws.amazon.com/elasticache/faqs/",
    "route53": "https://aws.amazon.com/route53/faqs/",
    "cloudfront": "https://aws.amazon.com/cloudfront/faqs/",
}


def download_file(url: str, output_path: Path, desc: str = "") -> bool:
    """Descarga un archivo desde URL"""
    try:
        print(f"📥 Descargando: {desc or url}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)

        print(f"   ✅ Guardado en: {output_path}")
        return True

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False


def fetch_aws_official_docs():
    """Descarga documentos oficiales AWS"""
    print("\n" + "="*60)
    print("📚 DESCARGANDO DOCUMENTACIÓN OFICIAL AWS")
    print("="*60)

    success_count = 0
    total_count = len(AWS_DOCS_SOURCES)

    for key, doc_info in AWS_DOCS_SOURCES.items():
        output_path = DOCS_DIR / doc_info["filename"]

        if output_path.exists():
            print(f"\n⏭️  Ya existe: {doc_info['filename']}")
            success_count += 1
            continue

        if download_file(doc_info["url"], output_path, doc_info["filename"]):
            success_count += 1

        time.sleep(1)  # Rate limiting

    print(f"\n✨ Documentos oficiales: {success_count}/{total_count} descargados")


def fetch_service_faqs():
    """Descarga FAQs de servicios AWS"""
    print("\n" + "="*60)
    print("📚 DESCARGANDO FAQs DE SERVICIOS AWS")
    print("="*60)

    success_count = 0
    total_count = len(SERVICE_FAQS)

    for service, url in SERVICE_FAQS.items():
        output_path = DOCS_DIR / f"{service}_faq.html"

        if output_path.exists():
            print(f"\n⏭️  Ya existe: {service}_faq.html")
            success_count += 1
            continue

        if download_file(url, output_path, f"{service.upper()} FAQ"):
            success_count += 1

        time.sleep(1)  # Rate limiting

    print(f"\n✨ Service FAQs: {success_count}/{total_count} descargados")


def create_summary():
    """Crea un resumen de documentos descargados"""
    files = list(DOCS_DIR.glob("*"))

    summary = {
        "total_files": len(files),
        "pdfs": len(list(DOCS_DIR.glob("*.pdf"))),
        "htmls": len(list(DOCS_DIR.glob("*.html"))),
        "total_size_mb": sum(f.stat().st_size for f in files) / (1024 * 1024)
    }

    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)
    print(f"Total archivos: {summary['total_files']}")
    print(f"  - PDFs: {summary['pdfs']}")
    print(f"  - HTMLs: {summary['htmls']}")
    print(f"  - Tamaño total: {summary['total_size_mb']:.2f} MB")
    print(f"\n📂 Ubicación: {DOCS_DIR}")


def main():
    print("\n🚀 AWS Documentation Fetcher")
    print("   Descargando documentación oficial para RAG system")

    # Descargar docs oficiales
    fetch_aws_official_docs()

    # Descargar FAQs de servicios
    fetch_service_faqs()

    # Crear resumen
    create_summary()

    print("\n✅ ¡Completado! Ahora puedes ejecutar: python scripts/2_build_rag.py")


if __name__ == "__main__":
    main()
