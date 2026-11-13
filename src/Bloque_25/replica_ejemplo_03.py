# pip install langchain-text-splitters langchain-google-genai langchain-chroma chromadb python-dotenv
#
# Réplica guiada del Bloque 25 sobre el corpus de ejemplo (política de devoluciones):
#   Paso 1: chunking del corpus con RecursiveCharacterTextSplitter.
#   Paso 2: verificación local de integridad de los chunks (sin gastar API).
#   Paso 3 y 4: embeddings con Gemini e indexación en Chroma (persistente).
#   Paso 5: reconexión al índice y conteo de chunks, sin recalcular embeddings.
#
# Diferencia con replica_ejemplo_02.py: indexar_chunks() valida los chunks por dentro
# antes de llamar a la API, así la validación no depende del main y no se puede saltar
# si la función se reutiliza desde otro script (por ejemplo, en el Gate 2).

import os

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configuración (mismos valores en indexación y en consulta)
CARPETA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PERSIST_DIR = os.path.join(CARPETA_SCRIPT, "vectorstore_ejemplo")
NOMBRE_COLECCION = "corpus_ejemplo"
MODELO_EMBEDDINGS = "models/gemini-embedding-001"
CHUNK_SIZE = 150
CHUNK_OVERLAP = 20

corpus_ejemplo = [
    "Los pedidos se pueden cancelar dentro de las primeras 24 horas despues de "
    "realizados, sin costo adicional.",
    "Las devoluciones se aceptan hasta 30 dias despues de la entrega, siempre que "
    "el producto este sin usar.",
    "El reembolso se procesa en un plazo de 5 a 10 dias habiles despues de recibir "
    "el producto devuelto.",
    "Los productos en oferta o liquidacion no tienen devolucion, salvo defecto de "
    "fabrica.",
    "El envio de una devolucion corre por cuenta del cliente, excepto cuando el "
    "producto llego danado.",
]


# PASO 1: partir el corpus en chunks
def generar_chunks(corpus, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """Parte cada documento del corpus en chunks y los muestra."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = splitter.create_documents(corpus)

    print(f"{len(chunks)} chunks generados")
    for i, chunk in enumerate(chunks):
        print(f"--- chunk {i} ({len(chunk.page_content)} caracteres) ---")
        print(chunk.page_content)
    return chunks


# PASO 2: verificar la integridad de los chunks (local, sin costo)
def validar_chunks(chunks, corpus, mostrar=True):
    """Revisa chunks vacíos, duplicados y pérdida de texto. Devuelve True si todo está bien.

    Con mostrar=False no imprime nada (lo usa indexar_chunks para no repetir el reporte).
    """
    vacios = [i for i, c in enumerate(chunks) if not c.page_content.strip()]
    textos = [c.page_content for c in chunks]
    hay_duplicados = len(textos) != len(set(textos))
    total_chars_chunks = sum(len(c.page_content) for c in chunks)
    total_chars_corpus = sum(len(d) for d in corpus)

    if mostrar:
        print("chunks vacios:", vacios)
        print("hay duplicados:", hay_duplicados)
        print("total de caracteres en los chunks:", total_chars_chunks)
        print("total de caracteres en el corpus original:", total_chars_corpus)

    # Con overlap real, los chunks pueden sumar MÁS caracteres que el corpus (es esperable);
    # lo que nunca debe pasar es que sumen MENOS (se perdió texto).
    chunks_validos = (
        not vacios
        and not hay_duplicados
        and total_chars_chunks >= total_chars_corpus
    )
    return chunks_validos


# PASO 3 y 4: calcular embeddings e indexar en Chroma
def crear_embeddings():
    """Carga el .env, valida la clave y devuelve el objeto de embeddings."""
    load_dotenv()
    clave = os.environ.get("GOOGLE_API_KEY")
    if not clave:
        raise SystemExit('Falta GOOGLE_API_KEY. Defínela en tu archivo ".env" y vuelve a ejecutar.')
    return GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS, google_api_key=clave)


def indexar_chunks(chunks, corpus, embeddings, persist_directory=PERSIST_DIR):
    """Valida los chunks, calcula sus embeddings y los guarda en Chroma. Devuelve el vector store."""
    # Validación obligatoria antes de gastar API (fuera del try, para que no se
    # confunda con un error de la API).
    if not validar_chunks(chunks, corpus, mostrar=False):
        raise SystemExit("❌ Los chunks no pasaron la verificación: no se indexa nada.")

    # ids explícitos: al re-ejecutar el script se reemplazan los mismos chunks
    # (no se duplican), y el conteo del Paso 5 sigue dando 5.
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    try:
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            ids=ids,
            collection_name=NOMBRE_COLECCION,
            persist_directory=persist_directory,
        )
    except Exception as error:
        mensaje = str(error)
        if "429" in mensaje or "RESOURCE_EXHAUSTED" in mensaje:
            print("Límite de peticiones alcanzado. Espera un minuto y vuelve a ejecutar.")
        elif "API key" in mensaje or "401" in mensaje or "403" in mensaje:
            print('La API rechazó tu clave. Revisa el valor de GOOGLE_API_KEY en tu ".env".')
        else:
            print("No se pudo indexar el corpus:", type(error).__name__)
        print("Detalle técnico:", mensaje)
        raise SystemExit(1)

    print(f"Indexados {len(chunks)} chunks en {os.path.basename(persist_directory)}/")
    return vectorstore


# PASO 5: verificar la persistencia (reconectar sin recalcular embeddings)
def cargar_vectorstore(embeddings, persist_directory=PERSIST_DIR):
    """Reconecta al vector store ya indexado y devuelve el objeto."""
    return Chroma(
        collection_name=NOMBRE_COLECCION,
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )


def titulo(texto):
    """Imprime el encabezado de cada paso entre dos líneas de '='."""
    separador = "=" * 60
    print(separador)
    print(texto)
    print(separador)


if __name__ == "__main__":
    titulo("PASO 1: chunking del corpus de ejemplo")
    chunks = generar_chunks(corpus_ejemplo)
    print()

    # Reporte visible; si falla, se detiene aquí antes de crear los embeddings.
    titulo("PASO 2: verificando integridad de los chunks (sin gastar API)")
    if not validar_chunks(chunks, corpus_ejemplo):
        raise SystemExit("❌ Los chunks no pasaron la verificación: no se indexa nada.")
    print()

    titulo("PASO 3 y 4: embeddings e indexacion en Chroma (esto llama a la API)")
    embeddings = crear_embeddings()
    indexar_chunks(chunks, corpus_ejemplo, embeddings)
    print()

    titulo("PASO 5: verificar la persistencia (reconectando, sin recalcular)")
    vectorstore_ejemplo_recargado = cargar_vectorstore(embeddings)
    print(vectorstore_ejemplo_recargado._collection.count())
