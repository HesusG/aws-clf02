#!/usr/bin/env python3
"""
Script 2: Build RAG System
Procesa documentos AWS y crea vector database con ChromaDB
"""

import os
import sys
from pathlib import Path
from typing import List, Dict
import json

# Agregar project root al path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

# Verificar API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ Error: OPENAI_API_KEY no encontrada en .env")
    print("   Copia .env.example a .env y agrega tu API key")
    sys.exit(1)

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, UnstructuredHTMLLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from tqdm import tqdm
import tiktoken

# Directorios
DOCS_DIR = PROJECT_ROOT / "data" / "aws_docs"
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_db"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Configuración
CHUNK_SIZE = 500  # tokens
CHUNK_OVERLAP = 50
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


def count_tokens(text: str) -> int:
    """Cuenta tokens usando tiktoken"""
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def load_documents() -> List[Document]:
    """Carga todos los documentos desde data/aws_docs"""
    documents = []

    print("\n📖 Cargando documentos...")

    # Cargar PDFs
    pdf_files = list(DOCS_DIR.glob("*.pdf"))
    print(f"\n   📄 Procesando {len(pdf_files)} PDFs...")

    for pdf_path in tqdm(pdf_files, desc="PDFs"):
        try:
            loader = PyPDFLoader(str(pdf_path))
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = pdf_path.name
                doc.metadata["type"] = "pdf"
            documents.extend(docs)
        except Exception as e:
            print(f"      ⚠️  Error en {pdf_path.name}: {str(e)}")

    # Cargar HTMLs
    html_files = list(DOCS_DIR.glob("*.html"))
    print(f"\n   🌐 Procesando {len(html_files)} HTMLs...")

    for html_path in tqdm(html_files, desc="HTMLs"):
        try:
            loader = UnstructuredHTMLLoader(str(html_path))
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = html_path.name
                doc.metadata["type"] = "html"
            documents.extend(docs)
        except Exception as e:
            print(f"      ⚠️  Error en {html_path.name}: {str(e)}")

    print(f"\n   ✅ Total documentos cargados: {len(documents)}")
    return documents


def split_documents(documents: List[Document]) -> List[Document]:
    """Divide documentos en chunks con overlap"""
    print("\n✂️  Dividiendo documentos en chunks...")

    # Usar RecursiveCharacterTextSplitter con estimación de tokens
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE * 4,  # Aproximación: 1 token ≈ 4 chars
        chunk_overlap=CHUNK_OVERLAP * 4,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = text_splitter.split_documents(documents)

    # Filtrar chunks vacíos o muy pequeños
    chunks = [c for c in chunks if len(c.page_content.strip()) > 50]

    # Calcular estadísticas de tokens
    total_tokens = sum(count_tokens(c.page_content) for c in chunks[:100])  # Muestra
    avg_tokens = total_tokens / min(100, len(chunks))

    print(f"   📊 Chunks creados: {len(chunks)}")
    print(f"   📊 Tokens promedio por chunk: ~{avg_tokens:.0f}")

    return chunks


def create_vector_store(chunks: List[Document]):
    """Crea vector store con ChromaDB"""
    print("\n🔮 Creando vector database con ChromaDB...")

    # Inicializar embeddings
    print(f"   Usando modelo: {EMBEDDING_MODEL}")
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    # Crear ChromaDB en batches (para evitar rate limits)
    batch_size = 100
    total_batches = (len(chunks) + batch_size - 1) // batch_size

    print(f"   Procesando {len(chunks)} chunks en {total_batches} batches...")

    # Primer batch (crear DB)
    first_batch = chunks[:batch_size]
    vectorstore = Chroma.from_documents(
        documents=first_batch,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name="aws_docs"
    )

    # Resto de batches (agregar a DB existente)
    for i in tqdm(range(batch_size, len(chunks), batch_size), desc="Batches"):
        batch = chunks[i:i + batch_size]
        vectorstore.add_documents(batch)

    print(f"   ✅ Vector store creado en: {CHROMA_DIR}")

    return vectorstore


def test_retrieval(vectorstore):
    """Prueba el sistema de retrieval"""
    print("\n🧪 Probando sistema de retrieval...")

    test_queries = [
        "¿Qué es AWS Shield y cómo protege contra DDoS?",
        "¿Cuál es la diferencia entre Reserved Instances y Spot Instances?",
        "¿Qué dominios cubre el examen CLF-C02?",
        "¿Qué es Amazon S3 Intelligent-Tiering?"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: {query}")
        results = vectorstore.similarity_search(query, k=3)

        for j, doc in enumerate(results, 1):
            preview = doc.page_content[:150].replace("\n", " ")
            print(f"      {j}. {doc.metadata.get('source', 'Unknown')}")
            print(f"         {preview}...")


def calculate_costs(num_chunks: int):
    """Calcula costo de embeddings"""
    tokens_per_chunk = CHUNK_SIZE
    total_tokens = num_chunks * tokens_per_chunk

    # text-embedding-3-small: $0.02 per 1M tokens
    cost = (total_tokens / 1_000_000) * 0.02

    print("\n💰 Estimación de costos:")
    print(f"   Total tokens a embedd: {total_tokens:,}")
    print(f"   Modelo: {EMBEDDING_MODEL}")
    print(f"   Costo estimado: ${cost:.4f} USD")


def save_metadata(chunks: List[Document]):
    """Guarda metadata del RAG system"""
    metadata = {
        "total_chunks": len(chunks),
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "embedding_model": EMBEDDING_MODEL,
        "sources": list(set(c.metadata.get("source", "unknown") for c in chunks)),
        "avg_chunk_length": sum(len(c.page_content) for c in chunks) / len(chunks)
    }

    metadata_path = CHROMA_DIR / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n📋 Metadata guardada en: {metadata_path}")


def main():
    print("\n" + "="*60)
    print("🚀 AWS CLF-C02 RAG System Builder")
    print("="*60)

    # 1. Cargar documentos
    documents = load_documents()

    if len(documents) == 0:
        print("\n❌ No se encontraron documentos en data/aws_docs/")
        print("   Ejecuta primero: python scripts/1_fetch_aws_docs.py")
        sys.exit(1)

    # 2. Dividir en chunks
    chunks = split_documents(documents)

    # 3. Calcular costos
    calculate_costs(len(chunks))

    # 4. Crear vector store
    vectorstore = create_vector_store(chunks)

    # 5. Guardar metadata
    save_metadata(chunks)

    # 6. Probar retrieval
    test_retrieval(vectorstore)

    print("\n" + "="*60)
    print("✅ RAG System creado exitosamente!")
    print("="*60)
    print("\n📋 Siguiente paso:")
    print("   python scripts/3_estimate_cost.py")


if __name__ == "__main__":
    main()
