# pip install langchain-core langchain-classic langchain-google-genai python-dotenv

"""
Agente de soporte Chocolatería con tres herramientas:
- políticas de la tienda
- estado de pedidos.
- total de compra.

Valida con intermediate_steps qué herramienta eligió el agente en cada caso.
"""

import unicodedata

from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)

load_dotenv()
modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")


# POLITICAS
POLITICAS = {
    "despacho": {
        "palabras": ("despach", "envio", "envia", "entrega", "demora"),
        "texto": (
            "Los despachos tardan 2 días hábiles en la Región "
            "Metropolitana y de 3 a 5 días hábiles en otras regiones. "
            "Son gratis en compras desde $30.000."
        ),
    },
    "devoluciones": {
        "palabras": ("devol", "reembols", "cambio", "garantia"),
        "texto": (
            "Se aceptan devoluciones dentro de 5 días corridos desde "
            "la recepción, con el producto sellado y su boleta."
        ),
    },
    "alergenos": {
        "palabras": (
            "alerg", "mani", "leche", "soya", "gluten",
            "frutos secos", "ingrediente", "contiene", "contienen",
        ),
        "texto": (
            "Todos los productos contienen leche y soya. Se elaboran "
            "en una planta que procesa maní y frutos secos, por lo "
            "que pueden contener trazas de ambos."
        ),
    },
    "conservacion": {
        "palabras": (
            "conserv", "guard", "refriger", "vencimiento",
            "duran", "temperatura",
        ),
        "texto": (
            "Los chocolates se guardan entre 15 °C y 18 °C, lejos de "
            "la luz y la humedad. Duran 6 meses; las trufas, 30 días."
        ),
    },
}

# PEDIDOS
PEDIDOS = {
    "CH-1001": (
        "En tránsito, llega en 2 días hábiles. "
        "Contiene 2 cajas de trufas."
    ),
    "CH-1002": (
        "Entregado. Contiene 1 caja de bombones surtidos."
    ),
    "CH-1003": (
        "En preparación. Contiene 3 barras de chocolate amargo."
    ),
}

# PRODUCTOS
CATALOGO = {
    "trufas": ("caja de trufas", 12900),
    "bombones": ("caja de bombones surtidos", 9900),
    "barra": ("barra de chocolate amargo", 3500),
    "alfajores": ("caja de alfajores", 7500),
}


def normalizar(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto.lower())
    return "".join(
        caracter for caracter in descompuesto
        if unicodedata.category(caracter) != "Mn"
    )


def formatear_pesos(monto: int) -> str:
    return f"${monto:,}".replace(",", ".")  # formato Chile


# HERRAMIENTA POLÍTICAS
@tool
def buscar_en_politicas(consulta: str) -> str:
    """Busca las reglas de la chocolatería sobre despachos, devoluciones,
    alérgenos e ingredientes, y conservación de los productos. Usar solo
    cuando el cliente pregunta por esos temas, por ejemplo si un producto
    contiene un ingrediente. No usar para pedidos específicos, precios,
    datos de contacto ni otros temas."""
    consulta_normalizada = normalizar(consulta)
    encontradas = [
        politica["texto"]
        for politica in POLITICAS.values()
        if any(p in consulta_normalizada for p in politica["palabras"])
    ]
    if encontradas:
        return " ".join(encontradas)
    return "No se encontró una política sobre esa consulta."


# HERRAMIENTA PEDIDOS
@tool
def consultar_estado_pedido(numero_pedido: str) -> str:
    """Consulta el estado y el contenido de un pedido a partir de su número,
    con formato CH-1001. Usar cuando el cliente pregunta dónde está su
    pedido, cuándo llega o qué productos incluía."""
    numero = numero_pedido.strip().upper()
    try:
        return PEDIDOS[numero]
    except KeyError:
        return f"No se encontró un pedido con el número {numero}."


# HERRAMIENTA TOTAL COMPRA
@tool
def calcular_total_compra(producto: str, cantidad: int) -> str:
    """Calcula el total en pesos chilenos de una compra según el producto y
    la cantidad. Usar cuando el cliente pregunta cuánto cuesta o cuánto
    costaría comprar productos de la chocolatería."""
    if cantidad <= 0:
        return "La cantidad debe ser mayor que cero."
    producto_normalizado = normalizar(producto)
    for clave, (nombre, precio) in CATALOGO.items():
        if clave in producto_normalizado:
            total = precio * cantidad
            return (
                f"{cantidad} x {nombre} a {formatear_pesos(precio)} "
                f"cada una: total {formatear_pesos(total)}."
            )
    disponibles = ", ".join(nombre for nombre, _ in CATALOGO.values())
    return (
        f"No se encontró el producto '{producto}'. "
        f"Productos disponibles: {disponibles}."
    )


herramientas = [
    buscar_en_politicas,
    consultar_estado_pedido,
    calcular_total_compra,
]

prompt_agente = ChatPromptTemplate.from_messages([
    (
        "system",
        "Eres un asistente que responde preguntas usando las herramientas disponibles cuando las necesites. Nunca entregues números de teléfono ni inventes datos de la tienda, como correos u horarios. Si no tienes un dato, dilo.",
    ),
    ("human", "{entrada}"),
    MessagesPlaceholder("agent_scratchpad"),
])

agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)

ejecutor_agente = AgentExecutor(
    agent=agente,
    tools=herramientas,
    verbose=True,
    return_intermediate_steps=True,
)


def texto_de_salida(resultado: dict) -> str:
    """Entrega solo el texto de la respuesta final del agente."""
    # Gemini puede devolver la salida como lista de bloques.
    return AIMessage(content=resultado["output"]).text


def test_agente_no_usa_herramienta_para_pregunta_general():

    resultado = ejecutor_agente.invoke({
        "entrada": (
            "¿Cómo puedo contactar a soporte?"
        )
    })

    assert resultado["intermediate_steps"] == []
    print(texto_de_salida(resultado))


if __name__ == "__main__":

    # Prueba manual: política de la tienda.
    resultado = ejecutor_agente.invoke({
        "entrada": "¿Sus bombones contienen maní?"
    })
    herramienta_usada = (
        resultado["intermediate_steps"][0][0].tool
    )
    assert herramienta_usada == "buscar_en_politicas"
    print(texto_de_salida(resultado))

    # Prueba manual: estado de un pedido.
    resultado = ejecutor_agente.invoke({
        "entrada": "¿Dónde está mi pedido CH-1001?"
    })
    herramienta_usada = (
        resultado["intermediate_steps"][0][0].tool
    )
    assert herramienta_usada == "consultar_estado_pedido"
    print(texto_de_salida(resultado))

    # Prueba manual: total de una compra.
    resultado = ejecutor_agente.invoke({
        "entrada": "¿Cuánto cuestan 3 cajas de trufas?"
    })
    herramienta_usada = (
        resultado["intermediate_steps"][0][0].tool
    )
    assert herramienta_usada == "calcular_total_compra"
    print(texto_de_salida(resultado))

    # Prueba manual: el agente debe leer el pedido para saber qué calcular.
    resultado = ejecutor_agente.invoke({
        "entrada": "Quiero repetir mi pedido CH-1001. ¿Cuánto me costaría?"
    })
    herramientas_usadas = [
        accion.tool for accion, _ in resultado["intermediate_steps"]
    ]
    assert herramientas_usadas == [
        "consultar_estado_pedido",
        "calcular_total_compra",
    ]
    print(texto_de_salida(resultado))

    # Prueba manual: pregunta general, sin herramientas.
    test_agente_no_usa_herramienta_para_pregunta_general()
