# pip install langchain-chroma langchain-google-genai langchain-text-splitters python-dotenv

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Consola de Windows: forzar UTF-8 para los símbolos ✅ / ❌
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
CARPETA_SCRIPT = Path(__file__).parent
CARPETA_VECTORES = str(CARPETA_SCRIPT / "vectorstore")  # ruta absoluta, no depende del cwd
NOMBRE_COLECCION = "chocolateria_bloque_27"
MODELO_EMBEDDINGS = "models/gemini-embedding-001"
CHUNK_SIZE = 200
CHUNK_OVERLAP = 30
K = 3          # k por defecto: cuántos chunks recupera el retriever y cuántos se evalúan
K_MAXIMO = 5   # ranking que se pide una sola vez para recorrer k = 1..K_MAXIMO

# ---------------------------------------------------------------------------
# Corpus de la chocolatería (datos del agente de los Bloques 21 a 24).
# Cada documento cabe en un chunk de 200 caracteres, así que su id es docN,
# numerado desde 1 (doc1 a doc10).
# ---------------------------------------------------------------------------
CORPUS = [
    # doc1
    "Despachos: tardan 2 días hábiles en la Región Metropolitana y de 3 a 5 días "
    "hábiles en otras regiones. Son gratis en compras desde $30.000.",
    # doc2
    "Devoluciones: se aceptan dentro de 5 días corridos desde la recepción, con el "
    "producto sellado y su boleta.",
    # doc3
    "Alérgenos: todos los productos contienen leche y soya. Se elaboran en una planta "
    "que procesa maní y frutos secos, por lo que pueden contener trazas de ambos.",
    # doc4
    "Conservación: los chocolates se guardan entre 15 °C y 18 °C, lejos de la luz y "
    "la humedad. Duran 6 meses; las trufas, 30 días.",
    # doc5
    "Pedido CH-1001: en tránsito, llega en 2 días hábiles. Contiene 2 cajas de trufas.",
    # doc6
    "Pedido CH-1002: entregado. Contiene 1 caja de bombones surtidos.",
    # doc7
    "Producto: caja de trufas. Precio: $12.900.",
    # doc8
    "Producto: caja de bombones surtidos. Precio: $9.900.",
    # doc9
    "Producto: barra de chocolate amargo. Precio: $3.500.",
    # doc10
    "Producto: caja de alfajores. Precio: $7.500.",
]

# ---------------------------------------------------------------------------
# Paso 1: conjunto de evaluación, etiquetado LEYENDO EL CORPUS (no el retriever).
# Incluye un caso con dos chunks relevantes y uno sin respuesta en el corpus.
# ---------------------------------------------------------------------------
casos_evaluacion = [
    {"pregunta": "cuantos dias demora el despacho a regiones",
     "ids_relevantes": {"doc1"}},
    {"pregunta": "puedo devolver un producto si ya lo abri",
     "ids_relevantes": {"doc2"}},
    {"pregunta": "los chocolates pueden tener mani",
     "ids_relevantes": {"doc3"}},
    {"pregunta": "a que temperatura debo guardar los chocolates",
     "ids_relevantes": {"doc4"}},
    {"pregunta": "donde va mi pedido CH-1001",
     "ids_relevantes": {"doc5"}},
    {"pregunta": "que traia el pedido CH-1002 que ya me entregaron",
     "ids_relevantes": {"doc6"}},
    {"pregunta": "cuanto cuesta una barra de chocolate amargo",
     "ids_relevantes": {"doc9"}},
    {"pregunta": "precio de la caja de alfajores",
     "ids_relevantes": {"doc10"}},
    # Dos chunks relevantes: la duración está en doc4 y el precio en doc7
    {"pregunta": "cuanto duran las trufas y cuanto vale la caja",
     "ids_relevantes": {"doc4", "doc7"}},
    # Sin respuesta en el corpus: recall = None y se excluye del promedio de recall
    {"pregunta": "tienen tienda fisica en Valparaiso",
     "ids_relevantes": set()},
]


# ---------------------------------------------------------------------------
# Formatos para mostrar a CK: coma decimal y fecha DD/MM/AAAA - HH:MM:SS
# ---------------------------------------------------------------------------
def num(valor, decimales=2):
    """Número con coma decimal; 'n/a' si el valor es None."""
    if valor is None:
        return "n/a"
    return f"{valor:.{decimales}f}".replace(".", ",")


# ---------------------------------------------------------------------------
# Llamadas a la API: reintentos solo ante límite de peticiones (429)
# ---------------------------------------------------------------------------
def con_reintentos(operacion, max_intentos=4, espera_inicial=5):
    """Ejecuta 'operacion'; si falla por 429/RESOURCE_EXHAUSTED espera 5, 10, 20 s y
    reintenta. Cualquier otro error (o el último intento) se relanza."""
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


# ---------------------------------------------------------------------------
# Indexación con ids explícitos (solo si hace falta)
# ---------------------------------------------------------------------------
def crear_chunks(corpus, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """Parte el corpus en chunks con ids predecibles: docN si el documento N cabe en un
    chunk (este corpus), o docN_M si se partió en varios."""
    divisor = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    metadatas = [{"fuente": f"doc{n}"} for n in range(1, len(corpus) + 1)]  # doc1, doc2, ...
    chunks = divisor.create_documents(corpus, metadatas=metadatas)

    por_fuente = {}
    for chunk in chunks:
        por_fuente.setdefault(chunk.metadata["fuente"], []).append(chunk)
    ids = []
    for chunk in chunks:
        fuente = chunk.metadata["fuente"]
        hermanos = por_fuente[fuente]
        ids.append(fuente if len(hermanos) == 1 else f"{fuente}_{hermanos.index(chunk)}")
    return chunks, ids


def cargar_o_indexar(embeddings, reindexar=False):
    """Reconecta al índice persistido; indexa solo si está vacío, si se pide --reindexar
    o si sus ids no coinciden con los del corpus actual (por ejemplo, tras renumerar)."""
    vectorstore = Chroma(
        collection_name=NOMBRE_COLECCION,
        embedding_function=embeddings,
        persist_directory=CARPETA_VECTORES,
    )
    chunks, ids = crear_chunks(CORPUS)
    ids_guardados = set(vectorstore.get()["ids"])
    if ids_guardados and ids_guardados != set(ids):
        print("Los ids del índice no coinciden con el corpus actual: se reindexa.")
        reindexar = True
    if reindexar:
        vectorstore.reset_collection()
        print("Colección borrada para reindexar desde cero.")

    total = vectorstore._collection.count()
    if total > 0:
        print(f"Índice reconectado: {total} chunks en {CARPETA_VECTORES}")
        return vectorstore

    con_reintentos(lambda: vectorstore.add_documents(chunks, ids=ids))
    print(f"Indexados {vectorstore._collection.count()} chunks en {CARPETA_VECTORES}, con ids explícitos")
    return vectorstore


def listar_ids(vectorstore):
    """Muestra cada id con su texto, para etiquetar leyendo el corpus."""
    datos = vectorstore.get()
    pares = sorted(zip(datos["ids"], datos["documents"]),
                   key=lambda par: int(par[0].replace("doc", "").split("_")[0]))
    print(f"ids del índice: {[i for i, _ in pares]}\n")
    for id_chunk, texto in pares:
        print(f"{id_chunk:>6}  {texto}")


# ---------------------------------------------------------------------------
# Métricas (con validaciones para los casos borde)
# ---------------------------------------------------------------------------
def precision_at_k(ids_recuperados, ids_relevantes):
    """Fracción de los ids recuperados que son relevantes (0.0 si no hay ninguno)."""
    if not ids_recuperados:
        return 0.0
    acertados = [i for i in ids_recuperados if i in ids_relevantes]
    return len(acertados) / len(ids_recuperados)


def recall_at_k(ids_recuperados, ids_relevantes):
    """Fracción de los ids relevantes que se recuperaron (None si el caso no tiene ninguno)."""
    if not ids_relevantes:
        return None
    acertados = [i for i in ids_recuperados if i in ids_relevantes]
    return len(acertados) / len(ids_relevantes)


def f1(precision, recall):
    """Media armónica de precisión y recall (None si el recall no está definido)."""
    if recall is None:
        return None
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def promediar(valores):
    """Promedio que ignora los None y evita dividir por cero."""
    validos = [v for v in valores if v is not None]
    return sum(validos) / len(validos) if validos else 0.0


# ---------------------------------------------------------------------------
# Paso 2: evaluación
# ---------------------------------------------------------------------------
def obtener_rankings(retriever, casos):
    """Una sola llamada al retriever por pregunta: devuelve {pregunta: [ids en orden]}."""
    rankings = {}
    for caso in casos:
        chunks = con_reintentos(lambda: retriever.invoke(caso["pregunta"]))
        ids = [c.id for c in chunks]
        if any(i is None for i in ids):
            raise SystemExit("Hay chunks sin id: reindexa con --reindexar para usar ids explícitos.")
        rankings[caso["pregunta"]] = ids
    return rankings


def evaluar_recuperacion(rankings, casos, k=K):
    """Evalúa cada caso con los primeros k ids de su ranking y promedia las métricas."""
    resultados = []
    for caso in casos:
        ids_recuperados = rankings[caso["pregunta"]][:k]
        p = precision_at_k(ids_recuperados, caso["ids_relevantes"])
        r = recall_at_k(ids_recuperados, caso["ids_relevantes"])
        resultados.append({"pregunta": caso["pregunta"], "recuperados": ids_recuperados,
                           "relevantes": caso["ids_relevantes"],
                           "precision": p, "recall": r, "f1": f1(p, r)})

    precision_promedio = promediar(x["precision"] for x in resultados)
    recall_promedio = promediar(x["recall"] for x in resultados)
    f1_promedio = f1(precision_promedio, recall_promedio)
    return resultados, precision_promedio, recall_promedio, f1_promedio


def comprobar_propiedades(resultados, precision_promedio, recall_promedio, casos):
    """Propiedades que deben cumplirse siempre (sección 'Paso 2' de la actividad)."""
    en_rango = all(0.0 <= x["precision"] <= 1.0 and (x["recall"] is None or 0.0 <= x["recall"] <= 1.0)
                   for x in resultados)
    un_solo_relevante = all(len(c["ids_relevantes"]) == 1 for c in casos if c["ids_relevantes"])
    lineas = [f"{'✅' if en_rango else '❌'} cada precisión y recall está entre 0 y 1"]
    if un_solo_relevante:
        cumple = recall_promedio >= precision_promedio
        lineas.append(f"{'✅' if cumple else '❌'} recall promedio >= precisión promedio")
    else:
        lineas.append("ℹ️  hay casos con más de un relevante: recall >= precisión no es obligatorio")
    fallidos = [x["pregunta"] for x in resultados if x["recall"] == 0.0]
    if fallidos:
        lineas.append("❌ casos con recall 0 (revisar primero): " + "; ".join(fallidos))
    else:
        lineas.append("✅ ningún caso con respuesta quedó con recall 0")
    return lineas


# ---------------------------------------------------------------------------
# Reporte (consola y archivo usan las mismas líneas)
# ---------------------------------------------------------------------------
def armar_reporte(fecha, k, resultados, precision_promedio, recall_promedio, f1_promedio,
                  tabla_k, mejor_k, propiedades):
    lineas = [
        f"Fecha: {fecha}",
        f"Configuracion: k={k}, chunk_size={CHUNK_SIZE}, chunk_overlap={CHUNK_OVERLAP}, "
        f"modelo={MODELO_EMBEDDINGS}, casos={len(resultados)}",
        "",
        "prec  recall  F1    recuperados                 relevantes      pregunta",
    ]
    for r in resultados:
        recuperados = ",".join(r["recuperados"])
        relevantes = ",".join(sorted(r["relevantes"])) or "(ninguno)"
        lineas.append(f"{num(r['precision'])}  {num(r['recall']):>6}  {num(r['f1']):>4}  "
                      f"{recuperados:<27} {relevantes:<15} {r['pregunta']}")
    lineas += [
        "",
        f"promedio -> precision: {num(precision_promedio, 3)}  recall: {num(recall_promedio, 3)}  "
        f"F1: {num(f1_promedio, 3)}",
        "",
        "Trade-off de k (mismo ranking recortado):",
    ]
    for fila in tabla_k:
        marca = "  <- mejor F1" if fila["k"] == mejor_k else ""
        lineas.append(f"k={fila['k']}: precision={num(fila['precision'], 3)}  "
                      f"recall={num(fila['recall'], 3)}  F1={num(fila['f1'], 3)}{marca}")
    lineas += ["", "Comprobaciones:"] + [f"  {p}" for p in propiedades]
    return lineas


def main():
    parser = argparse.ArgumentParser(description="Evaluación de la recuperación (Bloque 27)")
    parser.add_argument("--k", type=int, default=K, help=f"k a evaluar (1 a {K_MAXIMO}, por defecto {K})")
    parser.add_argument("--reindexar", action="store_true", help="borra la colección e indexa de nuevo")
    parser.add_argument("--listar-ids", action="store_true", help="solo lista los ids y textos del índice")
    argumentos = parser.parse_args()
    if not 1 <= argumentos.k <= K_MAXIMO:
        raise SystemExit(f"--k debe estar entre 1 y {K_MAXIMO}.")

    load_dotenv()
    if not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        raise SystemExit('Falta GOOGLE_API_KEY (o GEMINI_API_KEY). Defínela en tu archivo ".env".')

    embeddings = GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS)
    vectorstore = cargar_o_indexar(embeddings, reindexar=argumentos.reindexar)
    if argumentos.listar_ids:
        listar_ids(vectorstore)
        return

    retriever = vectorstore.as_retriever(search_kwargs={"k": K_MAXIMO})
    rankings = obtener_rankings(retriever, casos_evaluacion)

    resultados, precision_promedio, recall_promedio, f1_promedio = evaluar_recuperacion(
        rankings, casos_evaluacion, k=argumentos.k
    )

    tabla_k = []
    for k in range(1, K_MAXIMO + 1):
        _, p, r, f = evaluar_recuperacion(rankings, casos_evaluacion, k=k)
        tabla_k.append({"k": k, "precision": p, "recall": r, "f1": f})
    mejor_k = max(tabla_k, key=lambda fila: fila["f1"])["k"]  # empate: gana el k más chico

    propiedades = comprobar_propiedades(resultados, precision_promedio, recall_promedio,
                                        casos_evaluacion)
    ahora = datetime.now()
    lineas = armar_reporte(ahora.strftime("%d/%m/%Y - %H:%M:%S"), argumentos.k, resultados,
                           precision_promedio, recall_promedio, f1_promedio,
                           tabla_k, mejor_k, propiedades)
    print("\n" + "\n".join(lineas))

    # Paso 3: un solo archivo; cada corrida se AGREGA al final (modo "a") para poder
    # comparar corridas sin perder las anteriores
    archivo_entrega = CARPETA_SCRIPT / "resultados_evaluacion.txt"
    separador = "=" * 100
    with open(archivo_entrega, "a", encoding="utf-8") as archivo:
        if archivo.tell() > 0:
            archivo.write("\n")
        archivo.write(separador + "\n" + "\n".join(lineas) + "\n")
    print(f"\nResultados agregados al final de {archivo_entrega.name}")


if __name__ == "__main__":
    main()
