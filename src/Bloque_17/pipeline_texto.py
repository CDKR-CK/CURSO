import re
from collections import Counter
from Funciones_05 import consultar_modelo
import json


def limpiar_texto(texto: str) -> str:
    """Normaliza el texto: minúsculas y sin puntuación."""
    if not isinstance(texto, str):
        tipo = type(texto).__name__
        raise TypeError(f"limpiar_texto espera str, no {tipo}")

    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

def tokenizar(texto_limpio: str) -> list[str]:
    """Convierte texto limpio en una lista de tokens."""
    return texto_limpio.split()

def vectorizar(tokens: list[str]) -> Counter:
    """Cuenta cuántas veces aparece cada token."""
    return Counter(tokens)

def procesar_texto(texto):
    texto_limpio = limpiar_texto(texto)
    return tokenizar(texto_limpio)

def contar_coincidencias(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> int:
    """Cuenta las coincidencias entre referencia y respuesta."""
    conteo_referencia = Counter(tokens_referencia)
    conteo_respuesta = Counter(tokens_respuesta)
    interseccion = conteo_referencia & conteo_respuesta
    return sum(interseccion.values())

def calcular_precision_cobertura_f1(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> dict[str, float]:
    """Calcula precisión, cobertura y F1 de dos listas de tokens."""
    coincidencias = contar_coincidencias(
        tokens_referencia, tokens_respuesta
    )

    if not tokens_respuesta or not tokens_referencia:
        return {"precision": 0.0, "cobertura": 0.0, "f1": 0.0}

    precision = coincidencias / len(tokens_respuesta)
    cobertura = coincidencias / len(tokens_referencia)

    if precision + cobertura == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * cobertura / (precision + cobertura)

    resultado = {
        "precision": precision,
        "cobertura": cobertura,
        "f1": f1,
    }

    return resultado

def calcular_metricas(texto_referencia, texto_respuesta):

    tokens_referencia = procesar_texto(texto_referencia)

    tokens_respuesta = procesar_texto(texto_respuesta)

    return calcular_precision_cobertura_f1(
        tokens_referencia, tokens_respuesta
    )

def extraer_respuesta(texto_modelo: str) -> str:
    """Devuelve solo el texto del modelo, sin el encabezado "Pregunta: ...".

    consultar_modelo devuelve "Pregunta: <consulta>\\nRespuesta: <texto>\\n";
    si se compara todo, las palabras de la pregunta se cuentan como si
    las hubiera escrito el modelo. Si no hay "Respuesta:" (por ejemplo,
    un "Error: ..."), devuelve "" y las métricas quedan en 0.0.
    """
    if "Respuesta:" not in texto_modelo:
        return ""
    return texto_modelo.split("Respuesta:", 1)[1].strip()


if __name__ == "__main__":

    casos = [

        ("¿Qué es Python?",
         "Python es un lenguaje de programación interpretado.",
        ),
        ("¿Cuándo se creó Python?",
         "Python fue creado en 1991."),

        ("¿Qué es una lista en Python?",
         "Una lista es una colección ordenada y modificable.",
        ),
        ("¿Quién creó Python?",
         "Python fue creado por Guido van Rossum."),

        ("¿Qué es una tupla en Python?",
         "Una tupla es una colección ordenada e inmutable."),

        ("¿Qué es un diccionario en Python?",
         "Un diccionario es una colección de pares clave valor."),

        ("¿Qué es un conjunto en Python?",
         "Un conjunto es una colección no ordenada de elementos únicos."),

        ("¿Qué es una función en Python?",
         "Una función es un bloque de código reutilizable."),

        ("¿Para qué sirve la palabra def en Python?",
         "La palabra def sirve para definir una función."),

        ("¿Qué es un módulo en Python?",
         "Un módulo es un archivo con código Python reutilizable."),

        ("¿Qué es pip en Python?",
         "Pip es el gestor de paquetes de Python."),

        ("¿Qué es una clase en Python?",
         "Una clase es una plantilla para crear objetos."),

        ("¿Qué es un bucle for en Python?",
         "Un bucle for recorre los elementos de una secuencia."),

        ("¿Qué es un bucle while en Python?",
         "Un bucle while se repite mientras una condición sea verdadera."),

        ("¿Para qué sirve la función print en Python?",
         "La función print muestra información en la pantalla."),

        ("¿Para qué sirve la función len en Python?",
         "La función len devuelve la longitud de un objeto."),

        ("¿Qué es una excepción en Python?",
         "Una excepción es un error que ocurre durante la ejecución."),

        ("¿Para qué sirve try except en Python?",
         "Try except sirve para capturar y manejar excepciones."),

        ("¿Qué es una cadena de texto en Python?",
         "Una cadena es una secuencia inmutable de caracteres."),

        ("¿Qué es la indentación en Python?",
         "La indentación son espacios que definen los bloques de código."),
        ]

    resultados = []

    for consulta, referencia in casos:
        texto_modelo = consultar_modelo(consulta,"Responde con un maximo de 10 palabras", mostrar_costo=False)
        respuesta = extraer_respuesta(texto_modelo)
        metricas = calcular_metricas(referencia, respuesta)
        print(respuesta, referencia,"\n", metricas)

        resultados.append({
            "consulta": consulta,
            "referencia": referencia,
            "respuesta": respuesta,
            "metricas": metricas,
        })

    # Ordena los resultados de mayor a menor según el F1
    resultados.sort(
        key=lambda resultado: resultado["metricas"]["f1"], reverse=True
    )

    with open(
        "resultados_metricas.json", "w", encoding="utf-8"
    ) as archivo:

        json.dump(resultados, archivo, indent=2, ensure_ascii=False)

