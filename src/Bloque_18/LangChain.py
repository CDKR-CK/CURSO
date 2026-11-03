# pip install langchain-core langchain-google-genai python-dotenv
# Ejemplo de LangChain con Gemini: plantilla de prompt, llamada directa al modelo y cadena plantilla | modelo.

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate

from langchain_google_genai import ChatGoogleGenerativeAI

# Carga las claves desde el archivo .env que está junto al script
load_dotenv()


plantilla = PromptTemplate.from_template(
    "Explica el concepto de {tema} en un párrafo, "
    "para alguien que recién empieza en {area}."
)

prompt = plantilla.invoke(
    {"tema": "tokenización", "area": "procesamiento de texto"}
)
print(prompt.text)
print("\n")

modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite",temperature=0.3,)
respuesta = modelo.invoke("¿Qué es un token?")
print(respuesta.text)
print("\n")


# dddddddddddd
cadena_simple = plantilla | modelo
respuesta = cadena_simple.invoke(
    {"tema": "embeddings", "area": "búsqueda semántica"})
print(respuesta.text)





