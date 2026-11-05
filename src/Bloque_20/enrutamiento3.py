import logging

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnablePassthrough,
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

modelo = ChatGoogleGenerativeAI(model="gemini-3.8-flash")

# modelo de respaldo, más simple, por si falla el principal
modelo_secundario = ChatGoogleGenerativeAI(model="gemini-3.8-flash-lite")

plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica el siguiente mensaje de soporte en una sola "
    "palabra: pregunta, queja o sugerencia. Responde solo "
    "con esa palabra.\n\n{mensaje}"
)

plantilla_queja = PromptTemplate.from_template(
    "Responde a esta queja con empatía, reconociendo el "
    "problema antes de ofrecer una solución:\n\n{mensaje}"
)

cadena_pregunta = (
    PromptTemplate.from_template(
        "Responde esta pregunta técnica con precisión:\n\n{mensaje}"
    )
    | modelo
    | StrOutputParser()
)

cadena_queja = plantilla_queja | modelo | StrOutputParser()

cadena_sugerencia = (
    PromptTemplate.from_template(
        "Agradece esta sugerencia y explica cómo se evaluará "
        "dentro del producto:\n\n{mensaje}"
    )
    | modelo
    | StrOutputParser()
)


respuesta_generica = RunnableLambda(
    lambda x: (
        "Gracias por tu mensaje. Un miembro de nuestro "
        "equipo te va a responder pronto."
    )
)

# fallback
cadena_queja_con_modelo_secundario = (
    plantilla_queja | modelo_secundario | StrOutputParser()
)

def construir_cadena_queja_segura(cadena_queja):
    return cadena_queja.with_fallbacks([respuesta_generica])

# versión de producción
cadena_queja_segura = cadena_queja.with_fallbacks(
    [cadena_queja_con_modelo_secundario, respuesta_generica]
)


# fallback
def construir_cadena_segura(cadena):
    return cadena.with_fallbacks([respuesta_generica])


cadena_pregunta_segura = construir_cadena_segura(cadena_pregunta)
cadena_sugerencia_segura = construir_cadena_segura(cadena_sugerencia)

# --- Enrutamiento

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
    cadena_queja=cadena_queja_segura,
    cadena_sugerencia=cadena_sugerencia_segura,
    cadena_pregunta=cadena_pregunta_segura,
)

# --- Red de seguridad
def procesar_mensaje_seguro(cadena, mensaje):
    try:
        return cadena.invoke({"mensaje": mensaje})
    except Exception as error:
        logger.error(f"Error procesando mensaje: {error}")
        return (
            "No pudimos procesar tu mensaje en este "
            "momento. Intenta de nuevo más tarde."
        )



if __name__ == "__main__":
    # fallo forzado
    def fallar_a_proposito(x):
        raise Exception("Error de red simulado")

    cadena_rota = RunnableLambda(fallar_a_proposito)
    print(construir_cadena_queja_segura(cadena_rota).invoke(
        {"mensaje": "la app se cierra sola"}
    ))

    # fallo forzado fuera de una ruta
    print(procesar_mensaje_seguro(cadena_rota, "la app se cierra sola"))

    # flujo real completo
    print(procesar_mensaje_seguro(
        cadena_con_enrutamiento, "La app se cierra cada vez que subo una foto."
    ))









