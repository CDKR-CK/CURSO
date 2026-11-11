# pip install langchain-core langchain-text-splitters langchain-google-genai langchain-chroma chromadb python-dotenv
# Divide el corpus en pequeños en chunks, genera sus embeddings con Gemini
# los guarda en una base Chroma en carpeta vectorstore y luego la recarga para contar los registros.

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()
if not os.environ.get("GOOGLE_API_KEY"):
    raise SystemExit('Falta GOOGLE_API_KEY. Defínela en tu archivo ".env".')

# Carpeta de la base de vectores, junto a este script (no depende del directorio actual)
carpeta_vectores = str(Path(__file__).parent / "vectorstore")
nombre_coleccion = "corpus_unidad_24"

corpus = [
    "El cliente reintenta hasta 3 veces ante un TimeoutError, con espera creciente.",
    "Los errores de autenticacion nunca se reintentan: fallan de inmediato con un "
    "ValueError.",
    "El costo de cada llamada se calcula a partir de totalTokenCount y la tarifa "
    "vigente por cada 1000 tokens.",
    "El agente de la Unidad 2.4 decide por si mismo que herramienta usar, segun la "
    "descripcion de cada una.",
    "Las pruebas unitarias del cliente usan mocks, de forma que la suite completa "
    "corre en menos de un segundo.",
]

divisor = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)
chunks = divisor.create_documents(corpus)

# IDs fijos: al volver a ejecutar se reemplazan los chunks en vez de duplicarse
ids_chunks = [f"chunk_{i}" for i in range(len(chunks))]

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    ids=ids_chunks,
    collection_name=nombre_coleccion,
    persist_directory=carpeta_vectores,
)
print(f"Indexados {len(chunks)} chunks en {carpeta_vectores}")

# Recargar la base desde el disco y contar los registros
vectorstore_recargado = Chroma(
    collection_name=nombre_coleccion,
    persist_directory=carpeta_vectores,
    embedding_function=embeddings,
)
total_registros = len(vectorstore_recargado.get()["ids"])
print(f"Registros en la base recargada: {total_registros}")
