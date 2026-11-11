# pip install langchain-google-genai langchain-chroma chromadb python-dotenv
# abre la base Chroma con indexar_corpus_01.py
# cuenta sus registros y muestra el texto de cada chunk guardado.

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()
if not os.environ.get("GOOGLE_API_KEY"):
    raise SystemExit('Falta GOOGLE_API_KEY. Defínela en tu archivo ".env".')

# Carpeta de la base de vectores, junto a este script (no depende del directorio actual)
carpeta_vectores = Path(__file__).parent / "vectorstore"
nombre_coleccion = "corpus_unidad_24"

if not carpeta_vectores.is_dir():
    raise SystemExit(
        f"No existe la base {carpeta_vectores}. Ejecuta primero indexar_corpus_01.py."
    )

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# Abrir la base existente desde el disco
vectorstore_recargado = Chroma(
    collection_name=nombre_coleccion,
    persist_directory=str(carpeta_vectores),
    embedding_function=embeddings,
)

datos = vectorstore_recargado.get()
total_registros = len(datos["ids"])
print(f"Registros en la base recargada: {total_registros}")

for id_chunk, texto in zip(datos["ids"], datos["documents"]):
    print(f"- {id_chunk}: {texto}")
