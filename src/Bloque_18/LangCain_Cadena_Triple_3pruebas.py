# pip install langchain-core langchain-google-genai python-dotenv
# Cadena de 3 pasos con Gemini (extraer puntos clave -> simplificar -> formato markdown),
# probada con los textos del archivo LangCain_Cadena_Triple_3pruebas.json.

import json
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

# Indicación común para que el modelo no agregue frases como "Aquí tienes..."
sin_comentarios = (
    "Responde únicamente con el resultado, en una sola versión, "
    "sin introducción, sin comentarios y sin cierre."
)

plantilla_extraccion = PromptTemplate.from_template(
    "Lee el siguiente texto y devuelve solo sus 3 puntos "
    "clave, uno por línea, sin desarrollarlos. "
    + sin_comentarios + "\n\n{texto}"
)
paso_extraccion = plantilla_extraccion | modelo | StrOutputParser()

plantilla_simplificacion = PromptTemplate.from_template(
    "Reescribe estos puntos en lenguaje simple, sin jerga "
    "técnica, para alguien sin conocimientos previos. "
    + sin_comentarios + "\n\n{puntos}")
paso_simplificacion = (plantilla_simplificacion | modelo | StrOutputParser())

plantilla_formato = PromptTemplate.from_template(
    "Convierte este texto en una lista de viñetas markdown, "
    "de máximo 3 líneas. "
    + sin_comentarios + "\n\n{texto_simple}"
)
paso_formato = plantilla_formato | modelo | StrOutputParser()

# Todo en una cadena
cadena_tres_pasos = (
    plantilla_extraccion
    | modelo
    | StrOutputParser()
    | (lambda puntos: {"puntos": puntos})
    | plantilla_simplificacion
    | modelo
    | StrOutputParser()
    | (lambda texto_simple: {"texto_simple": texto_simple})
    | plantilla_formato
    | modelo
    | StrOutputParser()
)

# Carga los textos de prueba desde el JSON que está junto al script
ruta_json = Path(__file__).with_suffix(".json")
with open(ruta_json, encoding="utf-8") as archivo:
    pruebas = json.load(archivo)

separador = "=" * 70

# Para cada prueba: partes 1, 2 y 3 paso a paso, y luego la cadena completa
for numero, prueba in enumerate(pruebas, start=1):
    print(separador)
    print(f"PRUEBA {numero}: {prueba['titulo']}")
    print(separador)
    print(prueba["texto"])
    print("\n")

    # Parte 1
    puntos = paso_extraccion.invoke({"texto": prueba["texto"]})
    print("--- Parte 1: puntos clave ---")
    print(puntos)
    print("\n")

    # Parte 2
    simple = paso_simplificacion.invoke({"puntos": puntos})
    print("--- Parte 2: lenguaje simple ---")
    print(simple)
    print("\n")

    # Parte 3
    formato = paso_formato.invoke({"texto_simple": simple})
    print("--- Parte 3: viñetas markdown ---")
    print(formato)
    print("\n")

    # Todo en una cadena
    resultado = cadena_tres_pasos.invoke({"texto": prueba["texto"]})
    print("--- Cadena completa ---")
    print(resultado)
    print("\n")
