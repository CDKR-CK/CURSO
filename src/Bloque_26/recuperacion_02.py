import argparse
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Consola de Windows: forzar UTF-8 para los símbolos ✅ / ❌
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
CARPETA_VECTORES = str(Path(__file__).parent / "vectorstore")  # ruta absoluta, no depende del cwd
NOMBRE_COLECCION = "corpus_bloque_26"
MODELO_EMBEDDINGS = "models/gemini-embedding-001"
MODELO_CHAT = "gemini-3.5-flash-lite"
K_RECUPERACION = 3

# Corpus del proyecto: cada documento con su archivo de origen (la "fuente" que se citará)
CORPUS = {
    "doc0.md": "El cliente reintenta hasta 3 veces ante un TimeoutError, con espera creciente.",
    "doc1.md": "Los errores de autenticacion nunca se reintentan: fallan de inmediato con un "
               "ValueError.",
    "doc2.md": "El costo de cada llamada se calcula a partir de totalTokenCount y la tarifa "
               "vigente por cada 1000 tokens.",
    "doc3.md": "El agente de la Unidad 2.4 decide por si mismo que herramienta usar, segun la "
               "descripcion de cada una.",
    "doc4.md": "Las pruebas unitarias del cliente usan mocks, de forma que la suite completa "
               "corre en menos de un segundo.",
}

PROMPT_TEMPLATE = """Responde la pregunta usando SOLO el contexto de abajo. Cita la \
fuente de cada afirmacion con su numero entre corchetes, como [1]. Si el contexto no \
alcanza para responder, dilo explicitamente en vez de inventar.

Contexto:
{contexto}

Pregunta: {pregunta}

Respuesta:"""

# Preguntas de prueba: dos respondibles (temas distintos) y una que el corpus NO cubre
PREGUNTAS_PRUEBA = [
    "que pasa si mi conexion tarda demasiado",
    "cuanto cuesta cada llamada al modelo",
    "que base de datos usa la aplicacion para guardar a los usuarios",
]


# ---------------------------------------------------------------------------
# Llamadas a la API: reintentos solo ante límite de peticiones (429)
# ---------------------------------------------------------------------------
def con_reintentos(operacion, max_intentos=4, espera_inicial=5):
    """Ejecuta 'operacion'; si falla por 429/RESOURCE_EXHAUSTED espera 5, 10, 20 s y
    reintenta. Cualquier otro error (o el último intento) se relanza, no se oculta."""
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


def diagnosticar_y_salir(error, etapa):
    """Muestra un diagnóstico claro del fallo de la API y termina con código 1."""
    mensaje = str(error)
    if "429" in mensaje or "RESOURCE_EXHAUSTED" in mensaje:
        print("Límite de peticiones alcanzado. Espera un minuto y vuelve a ejecutar.")
    elif "API key" in mensaje or "401" in mensaje or "403" in mensaje:
        print('La API rechazó tu clave. Revisa el valor de la clave en tu ".env".')
    else:
        print(f"Falló la etapa '{etapa}':", type(error).__name__)
    print("Detalle técnico:", mensaje)
    raise SystemExit(1)


# ---------------------------------------------------------------------------
# Indexación (solo si hace falta) con metadata e ids predecibles
# ---------------------------------------------------------------------------
def crear_chunks(corpus, chunk_size=200, chunk_overlap=30):
    """Parte cada documento en chunks; cada chunk hereda {"fuente": archivo} y recibe un id
    predecible docN_M (documento N, chunk M), uno por chunk y no por documento."""
    fuentes = list(corpus.keys())
    textos = list(corpus.values())
    metadatas = [{"fuente": fuente} for fuente in fuentes]

    divisor = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = divisor.create_documents(textos, metadatas=metadatas)

    ids = []
    contador_por_fuente = {}
    for chunk in chunks:
        fuente = chunk.metadata["fuente"]
        numero_chunk = contador_por_fuente.get(fuente, 0)
        contador_por_fuente[fuente] = numero_chunk + 1
        ids.append(f"{Path(fuente).stem}_{numero_chunk}")
    return chunks, ids


def validar_chunks(chunks, corpus):
    """Verificación local (sin costo de API, tomada del Bloque 25): sin chunks vacíos, sin
    duplicados y sin texto perdido. Devuelve True si todo está bien."""
    vacios = [i for i, c in enumerate(chunks) if not c.page_content.strip()]
    textos = [c.page_content for c in chunks]
    hay_duplicados = len(textos) != len(set(textos))
    total_chars_chunks = sum(len(c.page_content) for c in chunks)
    total_chars_corpus = sum(len(d) for d in corpus.values())
    # Con overlap, los chunks pueden sumar MÁS caracteres que el corpus, nunca menos
    return not vacios and not hay_duplicados and total_chars_chunks >= total_chars_corpus


def cargar_o_indexar(embeddings, reindexar=False):
    """Reconecta al índice persistido. Solo indexa si está vacío o si se pide --reindexar
    (en ese caso borra la colección antes, para no duplicar chunks)."""
    vectorstore = Chroma(
        collection_name=NOMBRE_COLECCION,
        embedding_function=embeddings,
        persist_directory=CARPETA_VECTORES,
    )
    if reindexar:
        vectorstore.reset_collection()
        print("Colección borrada para reindexar desde cero.")

    total = vectorstore._collection.count()
    if total > 0:
        print(f"Índice reconectado: {total} chunks en {CARPETA_VECTORES} (sin recalcular embeddings)")
        return vectorstore

    chunks, ids = crear_chunks(CORPUS)
    if not validar_chunks(chunks, CORPUS):
        raise SystemExit("Chunks inválidos (vacíos, duplicados o texto perdido): no se indexa.")
    try:
        con_reintentos(lambda: vectorstore.add_documents(chunks, ids=ids))
    except Exception as error:
        diagnosticar_y_salir(error, "indexación")
    print(f"Indexados {vectorstore._collection.count()} chunks en {CARPETA_VECTORES}, "
          f"con metadata e ids")
    return vectorstore


# ---------------------------------------------------------------------------
# Recuperación y prompt dinámico
# ---------------------------------------------------------------------------
def formatear_contexto(chunks_recuperados):
    """Arma un bloque de contexto numerado para el prompt, y un mapa
    numero -> fuente para reconstruir la cita despues."""
    lineas = []
    citas = {}
    for i, doc in enumerate(chunks_recuperados, start=1):
        fuente = doc.metadata.get("fuente", "desconocida")
        lineas.append(f"[{i}] {doc.page_content}")
        citas[i] = fuente
    contexto = "\n\n".join(lineas)
    return contexto, citas


def construir_prompt(pregunta, vectorstore, k=K_RECUPERACION):
    """Recupera los k chunks más relevantes para la pregunta (reconectando, nunca
    reindexando) y arma el prompt dinámico con contexto numerado."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    try:
        chunks_recuperados = con_reintentos(lambda: retriever.invoke(pregunta))
    except Exception as error:
        diagnosticar_y_salir(error, "recuperación")
    contexto, citas = formatear_contexto(chunks_recuperados)
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta)
    return prompt, citas


def validar_prompt(pregunta, prompt, citas, k):
    """Comprueba los 4 requisitos de 'Qué debe cumplirse siempre'. Devuelve True si todos pasan."""
    numeros_en_contexto = [int(n) for n in re.findall(r"^\[(\d+)\] ", prompt, flags=re.MULTILINE)]
    comprobaciones = [
        (f"citas tiene exactamente k={k} entradas con claves 1..{k}",
         list(citas.keys()) == list(range(1, k + 1))),
        ("ningún valor de citas es 'desconocida'",
         all(fuente != "desconocida" for fuente in citas.values())),
        ("el prompt contiene la pregunta exacta en 'Pregunta: ...'",
         f"\nPregunta: {pregunta}\n" in prompt),
        ("el contexto tiene un bloque [N] por chunk, consecutivos desde 1",
         numeros_en_contexto == list(range(1, len(citas) + 1))),
    ]
    for descripcion, cumple in comprobaciones:
        print(f"  {'✅' if cumple else '❌'} {descripcion}")
    return all(cumple for _, cumple in comprobaciones)


# ---------------------------------------------------------------------------
# Respuesta del modelo y verificación de citas
# ---------------------------------------------------------------------------
def texto_de_respuesta(respuesta):
    """Extrae el texto de la respuesta del chat (content puede ser str o lista de bloques)."""
    contenido = respuesta.content
    if isinstance(contenido, list):
        return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in contenido)
    return contenido


def responder(prompt, llm):
    """Envía el prompt dinámico al modelo de chat y devuelve el texto de la respuesta."""
    try:
        return texto_de_respuesta(con_reintentos(lambda: llm.invoke(prompt)))
    except Exception as error:
        diagnosticar_y_salir(error, "respuesta del modelo")


def extraer_citas(respuesta, citas):
    """Devuelve [(numero, fuente)] de cada [N] de la respuesta; las citas alucinadas
    (números que no estaban en el contexto) quedan marcadas como inválidas."""
    numeros = sorted({int(n) for n in re.findall(r"\[(\d+)\]", respuesta)})
    return [(n, citas.get(n, "Cita inválida / no encontrada")) for n in numeros]


def palabras_clave(texto):
    """Palabras de 4 o más letras, en minúsculas, para comparar respuesta y fuente."""
    return set(re.findall(r"[a-záéíóúñ0-9]{4,}", texto.lower()))


def verificar_cita(respuesta, citas, numero=1):
    """Verificación de la cita [numero]: busca su fuente en 'citas' y muestra el texto del
    archivo original junto con las palabras que comparte con la respuesta."""
    fuente = citas.get(numero)
    if fuente is None or fuente not in CORPUS:
        print(f"  ❌ La cita [{numero}] no existe en el mapa de citas o su fuente no está en el corpus.")
        return False
    texto_fuente = CORPUS[fuente]
    comunes = palabras_clave(respuesta) & palabras_clave(texto_fuente)
    print(f"  Cita [{numero}] -> {fuente}")
    print(f"  Texto de {fuente}: {texto_fuente}")
    print(f"  Palabras en común con la respuesta: {', '.join(sorted(comunes)) or '(ninguna)'}")
    cumple = len(comunes) >= 2
    print(f"  {'✅' if cumple else '❌'} la fuente citada respalda la respuesta "
          f"(revísalo también a simple vista)")
    return cumple


FRASES_SIN_INFORMACION = (
    "no alcanza", "no contiene", "no tengo", "no hay informacion", "no hay información",
    "no se menciona", "no menciona", "no proporciona", "no es posible", "no puedo",
    "insuficiente", "no se especifica", "no especifica",
)


def admite_falta_de_informacion(respuesta):
    """True si la respuesta reconoce explícitamente que el contexto no alcanza."""
    texto = respuesta.lower()
    return any(frase in texto for frase in FRASES_SIN_INFORMACION)


# ---------------------------------------------------------------------------
# Programa principal: los 3 escenarios de "Cómo se prueba"
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Recuperación semántica y prompt con citas")
    parser.add_argument("--reindexar", action="store_true", help="borra la colección e indexa de nuevo")
    parser.add_argument("--sin-modelo", action="store_true", help="no envía los prompts al modelo de chat")
    argumentos = parser.parse_args()

    load_dotenv()
    if not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        raise SystemExit('Falta GOOGLE_API_KEY (o GEMINI_API_KEY). Defínela en tu archivo ".env".')

    embeddings = GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS)
    vectorstore = cargar_o_indexar(embeddings, reindexar=argumentos.reindexar)
    llm = None if argumentos.sin_modelo else ChatGoogleGenerativeAI(model=MODELO_CHAT)

    resultados = []
    for pregunta in PREGUNTAS_PRUEBA:
        print("\n" + "=" * 80)
        print(f"PREGUNTA: {pregunta}")
        print("=" * 80)
        prompt, citas = construir_prompt(pregunta, vectorstore, k=K_RECUPERACION)
        print(prompt)
        print("\nMapa de citas:", citas)
        print("\nValidación del prompt:")
        prompt_ok = validar_prompt(pregunta, prompt, citas, K_RECUPERACION)

        respuesta = None
        if llm is not None:
            respuesta = responder(prompt, llm)
            print("\nRespuesta del modelo:\n" + respuesta)
            for numero, fuente in extraer_citas(respuesta, citas):
                print(f"  Cita [{numero}]: {fuente}")
        resultados.append({"pregunta": pregunta, "citas": citas,
                           "prompt_ok": prompt_ok, "respuesta": respuesta})

    # ---- Resumen de los 3 escenarios de prueba ----
    print("\n" + "=" * 80)
    print("RESUMEN DE PRUEBAS")
    print("=" * 80)

    print("\n1) El contexto recuperado cambia entre dos preguntas distintas:")
    citas_1 = list(resultados[0]["citas"].values())
    citas_2 = list(resultados[1]["citas"].values())
    print(f"  Pregunta 1 -> {citas_1}")
    print(f"  Pregunta 2 -> {citas_2}")
    print(f"  {'✅' if citas_1 != citas_2 else '❌'} la recuperación depende de la pregunta "
          f"(el chunk más relevante: {citas_1[0]} vs {citas_2[0]})")

    print("\n4 requisitos del prompt en todas las preguntas:")
    print(f"  {'✅' if all(r['prompt_ok'] for r in resultados) else '❌'} validación del prompt")

    if llm is None:
        print("\n(--sin-modelo: se omiten las pruebas 2 y 3, que necesitan la respuesta del modelo)")
        return

    print("\n2) Pregunta que el corpus no puede responder:")
    sin_info = resultados[2]["respuesta"]
    print(f"  Respuesta: {sin_info}")
    print(f"  {'✅' if admite_falta_de_informacion(sin_info) else '❌'} "
          f"el modelo admite que no tiene información suficiente")

    print("\n3) Verificación de la cita [1] de una respuesta real (pregunta 1):")
    verificar_cita(resultados[0]["respuesta"], resultados[0]["citas"], numero=1)


if __name__ == "__main__":
    main()
