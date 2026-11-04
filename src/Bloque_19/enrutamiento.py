# Necesario para pytest
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langchain_core.runnables import (
    RunnableBranch,
    RunnablePassthrough,
)

modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica el siguiente mensaje de soporte en una sola "
    "palabra: pregunta, queja o sugerencia. Responde solo "
    "con esa palabra.\n\n{mensaje}"
)

cadena_pregunta = (
    PromptTemplate.from_template(
        "Responde esta pregunta técnica con precisión:\n\n{mensaje}"
    )
    | modelo
    | StrOutputParser()
)

cadena_queja = (
    PromptTemplate.from_template(
        "Responde a esta queja con empatía, reconociendo el "
        "problema antes de ofrecer una solución:\n\n{mensaje}"
    )
    | modelo
    | StrOutputParser()
)

cadena_sugerencia = (
    PromptTemplate.from_template(
        "Agradece esta sugerencia y explica cómo se evaluará "
        "dentro del producto:\n\n{mensaje}"
    )
    | modelo
    | StrOutputParser()
)

def construir_paso_clasificacion(modelo):
    return (
        plantilla_clasificacion
        | modelo
        | StrOutputParser()
        | (lambda texto: texto.strip().lower())
    )
 
def construir_cadena_con_enrutamiento(
    paso_clasificacion,
    cadena_queja=None,
    cadena_sugerencia=None,
    cadena_pregunta=None,
):
    cadena_queja = cadena_queja or RunnablePassthrough()
    cadena_sugerencia = cadena_sugerencia or RunnablePassthrough()
    cadena_pregunta = cadena_pregunta or RunnablePassthrough()
    bifurcacion = RunnableBranch(
        (lambda x: x["categoria"] == "pregunta", cadena_pregunta),
        (lambda x: x["categoria"] == "queja", cadena_queja),
        (lambda x: x["categoria"] == "sugerencia", cadena_sugerencia),
        cadena_pregunta,
    )
    return (
        RunnablePassthrough.assign(categoria=paso_clasificacion)
        | bifurcacion
    )
 
paso_clasificacion = construir_paso_clasificacion(modelo)
cadena_con_enrutamiento = construir_cadena_con_enrutamiento(
    paso_clasificacion=paso_clasificacion,
    cadena_queja=cadena_queja,
    cadena_sugerencia=cadena_sugerencia,
    cadena_pregunta=cadena_pregunta,
)


if __name__ == "__main__":
    texto = "Pueden aplicar una fuente más grande?"
    resultado = cadena_con_enrutamiento.invoke({"mensaje": texto})
    print(resultado)


