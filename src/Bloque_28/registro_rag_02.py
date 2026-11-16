# pip install langchain-google-genai langchain-chroma python-dotenv
#

import argparse
import json
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# Consola de Windows: forzar UTF-8 para los símbolos ✅ / ❌
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
CARPETA_SCRIPT = Path(__file__).parent
CARPETA_VECTORES = str(CARPETA_SCRIPT / "vectorstore")       # no depende del cwd
ARCHIVO_REGISTROS = CARPETA_SCRIPT / "registros_latencia_costo.jsonl"
NOMBRE_COLECCION = "chocolateria_bloque_28"
MODELO_EMBEDDINGS = "models/gemini-embedding-001"
MODELO_CHAT = "gemini-3.5-flash-lite"
K = 3
K_ALTO = 6
SEPARADOR = "=" * 70

# ---------------------------------------------------------------------------
# Corpus de la chocolatería (el mismo del Bloque 27: doc1 a doc10, un chunk cada uno)
# ---------------------------------------------------------------------------
CORPUS = [
    "Despachos: tardan 2 días hábiles en la Región Metropolitana y de 3 a 5 días "
    "hábiles en otras regiones. Son gratis en compras desde $30.000.",
    "Devoluciones: se aceptan dentro de 5 días corridos desde la recepción, con el "
    "producto sellado y su boleta.",
    "Alérgenos: todos los productos contienen leche y soya. Se elaboran en una planta "
    "que procesa maní y frutos secos, por lo que pueden contener trazas de ambos.",
    "Conservación: los chocolates se guardan entre 15 °C y 18 °C, lejos de la luz y "
    "la humedad. Duran 6 meses; las trufas, 30 días.",
    "Pedido CH-1001: en tránsito, llega en 2 días hábiles. Contiene 2 cajas de trufas.",
    "Pedido CH-1002: entregado. Contiene 1 caja de bombones surtidos.",
    "Producto: caja de trufas. Precio: $12.900.",
    "Producto: caja de bombones surtidos. Precio: $9.900.",
    "Producto: barra de chocolate amargo. Precio: $3.500.",
    "Producto: caja de alfajores. Precio: $7.500.",
]

# Preguntas tomadas del conjunto de evaluación del Bloque 27
PREGUNTAS_PRUEBA = [
    "cuantos dias demora el despacho a regiones?",
    "los chocolates pueden tener mani?",
    "cuanto duran las trufas y cuanto vale la caja?",
]
PREGUNTA_COMPARAR_K = "cuanto duran las trufas y cuanto vale la caja?"

PROMPT_TEMPLATE = """Responde la pregunta usando SOLO el contexto de abajo. Cita la \
fuente de cada afirmacion con su numero entre corchetes, como [1]. Si el contexto no \
alcanza para responder, dilo explicitamente en vez de inventar.

Contexto:
{contexto}

Pregunta: {pregunta}

Respuesta:"""


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def num(valor, decimales=2):
    """Número con punto de miles y coma decimal, para mostrar en consola."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def con_reintentos(operacion, max_intentos=4, espera_inicial=5):
    """Reintenta solo ante límite de peticiones (429 / RESOURCE_EXHAUSTED)."""
    espera = espera_inicial
    for intento in range(1, max_intentos + 1):
        try:
            return operacion()
        except Exception as error:
            mensaje = str(error)
            es_limite = "429" in mensaje or "RESOURCE_EXHAUSTED" in mensaje
            if not es_limite or intento == max_intentos:
                raise
            print(f"Límite de peticiones alcanzado. Reintento {intento} de "
                  f"{max_intentos - 1} en {espera} s...")
            time.sleep(espera)
            espera *= 2


@contextmanager
def medir(tiempos, etapa):
    """Guarda en tiempos[etapa] los segundos que tardó el bloque 'with'."""
    inicio = time.perf_counter()
    yield
    tiempos[etapa] = time.perf_counter() - inicio


def formatear_contexto(chunks_recuperados):
    """Numera los chunks como [1], [2], ... para que el modelo pueda citarlos."""
    return "\n\n".join(f"[{i}] {doc.page_content}"
                       for i, doc in enumerate(chunks_recuperados, start=1))


# ---------------------------------------------------------------------------
# Componentes (funciones aparte para poder cambiarlos por otros en pruebas)
# ---------------------------------------------------------------------------
def crear_embeddings():
    return GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS)


def crear_chat():
    return ChatGoogleGenerativeAI(model=MODELO_CHAT)


def cargar_o_indexar(embeddings, reindexar=False):
    """Reconecta al índice persistido e indexa solo si está vacío o se pide.
    Se hace FUERA de la medición: indexar es un costo único, no por consulta."""
    vectorstore = Chroma(collection_name=NOMBRE_COLECCION, embedding_function=embeddings,
                         persist_directory=CARPETA_VECTORES)
    if reindexar:
        vectorstore.reset_collection()
        print("Colección borrada para reindexar desde cero.")

    total = vectorstore._collection.count()
    if total > 0:
        print(f"Índice reconectado: {total} chunks en {CARPETA_VECTORES}")
        return vectorstore

    documentos = [Document(page_content=texto, metadata={"fuente": f"doc{n}"})
                  for n, texto in enumerate(CORPUS, start=1)]
    ids = [f"doc{n}" for n in range(1, len(CORPUS) + 1)]
    con_reintentos(lambda: vectorstore.add_documents(documentos, ids=ids))
    print(f"Indexados {vectorstore._collection.count()} chunks en {CARPETA_VECTORES}")
    return vectorstore


# ---------------------------------------------------------------------------
# Consulta RAG instrumentada
# ---------------------------------------------------------------------------
def registrar_consulta(pregunta, vectorstore, embeddings, chat_model, k=K):
    """Corre una consulta RAG real midiendo cada etapa por separado y devuelve el
    registro con los tokens reales de la respuesta del modelo."""
    tiempos = {}

    with medir(tiempos, "embed_query"):            # red
        vector = con_reintentos(lambda: embeddings.embed_query(pregunta))

    with medir(tiempos, "busqueda_vectorial"):     # local
        chunks = vectorstore.similarity_search_by_vector(vector, k=k)

    prompt = PROMPT_TEMPLATE.format(contexto=formatear_contexto(chunks), pregunta=pregunta)

    with medir(tiempos, "generacion"):             # red
        respuesta = con_reintentos(lambda: chat_model.invoke(prompt))

    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pregunta": pregunta,
        "k": k,
        "tiempos_ms": {etapa: round(s * 1000, 2) for etapa, s in tiempos.items()},
        "tiempo_total_ms": round(sum(tiempos.values()) * 1000, 2),
        "tokens": dict(respuesta.usage_metadata) if respuesta.usage_metadata else None,
    }
    return registro, respuesta.text


def guardar_registro(registro):
    """Agrega el registro como UNA línea JSON al final del archivo (JSON Lines)."""
    with open(ARCHIVO_REGISTROS, "a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")


def contar_lineas():
    if not ARCHIVO_REGISTROS.exists():
        return 0
    with open(ARCHIVO_REGISTROS, encoding="utf-8") as archivo:
        return sum(1 for linea in archivo if linea.strip())


def tokens_entrada(registro):
    return registro["tokens"]["input_tokens"] if registro["tokens"] else None


def titulo(texto):
    print(f"\n{SEPARADOR}\n{texto}\n{SEPARADOR}")


# ---------------------------------------------------------------------------
# Programa principal: las 3 pruebas de "Cómo se prueba"
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Registro de latencia y costo del RAG (Bloque 28)")
    parser.add_argument("--reindexar", action="store_true", help="borra la colección e indexa de nuevo")
    argumentos = parser.parse_args()

    load_dotenv(CARPETA_SCRIPT.parents[1] / ".env")   # .env en la raíz del proyecto
    load_dotenv()                                      # y, por si acaso, el del cwd
    if not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        raise SystemExit('Falta GOOGLE_API_KEY (o GEMINI_API_KEY). Defínela en tu archivo ".env".')

    embeddings = crear_embeddings()
    chat_model = crear_chat()
    vectorstore = cargar_o_indexar(embeddings, reindexar=argumentos.reindexar)

    lineas_iniciales = contar_lineas()
    registros = []

    def correr(pregunta, k):
        registro, texto_respuesta = registrar_consulta(pregunta, vectorstore, embeddings,
                                                       chat_model, k=k)
        guardar_registro(registro)
        registros.append(registro)
        print(json.dumps(registro, indent=2, ensure_ascii=False))
        print(f"Respuesta del modelo:\n{texto_respuesta}\n")
        return registro

    # Prueba 1: tres preguntas distintas del conjunto de evaluación del Bloque 27
    titulo(f"PASO 1: registrando {len(PREGUNTAS_PRUEBA)} consultas distintas (Cómo se prueba, chequeo 1)")
    for pregunta in PREGUNTAS_PRUEBA:
        correr(pregunta, K)

    # Prueba 2: la misma pregunta con k=3 y k=6
    titulo(f"PASO 2: misma pregunta con k={K} y k={K_ALTO} (Cómo se prueba, chequeo 2)")
    registro_k_bajo = correr(PREGUNTA_COMPARAR_K, K)
    registro_k_alto = correr(PREGUNTA_COMPARAR_K, K_ALTO)
    entrada_baja, entrada_alta = tokens_entrada(registro_k_bajo), tokens_entrada(registro_k_alto)
    print(f"k={K} -> input_tokens: {entrada_baja}")
    print(f"k={K_ALTO} -> input_tokens: {entrada_alta}")
    if entrada_baja is None or entrada_alta is None:
        print("❌ alguna consulta no devolvió usage_metadata: no se puede comparar")
    else:
        crecio = entrada_alta > entrada_baja
        print(f"{'✅' if crecio else '❌'} input_tokens creció al subir k "
              f"({entrada_baja} -> {entrada_alta}, +{entrada_alta - entrada_baja})")

    # Prueba 3: archivo de registros y etapa más lenta
    titulo("PASO 3: confirmando el archivo de registros y la etapa más lenta (chequeo 3)")
    lineas_finales = contar_lineas()
    nuevas = lineas_finales - lineas_iniciales
    print(f"{'✅' if nuevas == len(registros) else '❌'} {ARCHIVO_REGISTROS.name} tiene "
          f"{lineas_finales} líneas ({nuevas} nuevas en esta corrida, una por consulta)")

    claves = {"timestamp", "pregunta", "k", "tiempos_ms", "tiempo_total_ms", "tokens"}
    with open(ARCHIVO_REGISTROS, encoding="utf-8") as archivo:
        ultimas = [json.loads(linea) for linea in archivo if linea.strip()][-nuevas:]
    completas = all(claves <= set(r) for r in ultimas)
    print(f"{'✅' if completas else '❌'} cada línea nueva es un JSON completo con las 6 claves")

    print("\nTiempos por etapa (ms):")
    print(f"{'k':>2}  {'embed_query':>12}  {'busqueda':>9}  {'generacion':>11}  {'total':>10}  pregunta")
    for r in registros:
        t = r["tiempos_ms"]
        print(f"{r['k']:>2}  {num(t['embed_query']):>12}  {num(t['busqueda_vectorial']):>9}  "
              f"{num(t['generacion']):>11}  {num(r['tiempo_total_ms']):>10}  {r['pregunta']}")

    generacion_mas_lenta = all(max(r["tiempos_ms"], key=r["tiempos_ms"].get) == "generacion"
                               for r in registros)
    print(f"\n{'✅' if generacion_mas_lenta else '❌'} 'generacion' es la etapa más lenta "
          f"en las {len(registros)} consultas")

    ahora = datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
    print(f"\nCorrida terminada: {ahora} (hora de Chile). "
          f"Revisa el historial con: python leer_registros_00.py")


if __name__ == "__main__":
    main()
