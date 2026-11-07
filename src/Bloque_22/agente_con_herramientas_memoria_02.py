# pip install langchain-core langchain-classic langchain-google-genai pydantic python-dotenv

"""
Agente de soporte Chocolatería con tres herramientas:
- políticas de la tienda
- estado de pedidos.
- total de compra.

Recuerda la conversación de cada cliente con RunnableWithMessageHistory.
Ejecuta 2 sesiones de 4 interacciones cada una y valida con
intermediate_steps las herramientas usadas y con el historial que las
sesiones no se mezclen.
"""

from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import (
    RunnableWithMessageHistory,
)
from langchain_core.chat_history import (
    InMemoryChatMessageHistory,
)
import unicodedata

from dotenv import load_dotenv
from pydantic import BaseModel, Field
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
            "duran", "duracion", "temperatura",
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
    # Sin f-string: un formateador dejó {monto:,} como {monto: , }, que falla.
    return "$" + format(monto, ",").replace(",", ".")  # formato Chile


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
class ArgumentosTotalCompra(BaseModel):
    producto: str = Field(
        description=(
            "Producto que se quiere comprar: trufas, bombones, barra "
            "o alfajores."
        ),
    )
    cantidad: int = Field(
        description="Número de unidades que se quieren comprar.",
    )


@tool(args_schema=ArgumentosTotalCompra)
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
        (
            "Eres un asistente que responde preguntas usando las herramientas disponibles "
            "cuando las necesites. Nunca entregues números de teléfono ni inventes datos de la "
            "tienda, como correos u horarios. Si no tienes un dato, dilo."
        ),
    ),
    MessagesPlaceholder("chat_history"),
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

    session_id = "prueba_general"
    resultado = agente_con_memoria.invoke(
        {"entrada": "¿Cómo puedo contactar a soporte?"},
        {"configurable": {"session_id": session_id}},
    )
    cerrar_sesion(session_id)

    assert resultado["intermediate_steps"] == []
    print(resultado["output"])


# Bloque 22 >>>

historiales = {}


def obtener_historial(session_id: str):
    if session_id not in historiales:
        historiales[session_id] = InMemoryChatMessageHistory()
    return historiales[session_id]


def cerrar_sesion(session_id: str):
    """Borra el historial de una sesión; no falla si ya no existe."""
    historiales.pop(session_id, None)


def salida_como_texto(resultado: dict) -> dict:
    """Deja "output" como texto para que el historial guarde un mensaje."""
    # Si Gemini devuelve una lista de bloques, el historial la guardaría
    # tal cual y el turno siguiente fallaría al armar el prompt.
    return {**resultado, "output": str(texto_de_salida(resultado))}


agente_con_memoria = RunnableWithMessageHistory(
    ejecutor_agente | RunnableLambda(salida_como_texto),
    obtener_historial,
    input_messages_key="entrada",
    history_messages_key="chat_history",
)


SIN_HERRAMIENTAS = ""

# Cada interacción es (pregunta, herramienta que el agente debe usar).
# None: no se valida, porque puede responder con lo que ya recuerda.
SESIONES = {
    # Las preguntas 2, 3 y 4 no repiten el pedido: salen de la memoria.
    "cliente_01": [
        ("¿Dónde está mi pedido CH-1001?", "consultar_estado_pedido"),
        ("¿Qué productos incluye ese pedido?", None),
        (
            "¿Cuánto me costaría comprar el doble de lo que traía?",
            "calcular_total_compra",
        ),
        (
            "¿Cómo debo guardar esas cajas y cuánto duran?",
            "buscar_en_politicas",
        ),
    ],
    # La pregunta 1 prueba que no conoce la conversación de cliente_01.
    "cliente_02": [
        ("¿Por qué pedido te pregunté antes?", SIN_HERRAMIENTAS),
        (
            "Me interesan las cajas de bombones. ¿Contienen maní?",
            "buscar_en_politicas",
        ),
        (
            "Si compro 3 de esas cajas, ¿cuánto pagaría?",
            "calcular_total_compra",
        ),
        (
            "¿Cuánto me falta con esa compra para tener despacho gratis?",
            "buscar_en_politicas",
        ),
    ],
}


def ejecutar_sesion(session_id: str, interacciones: list):
    config = {"configurable": {"session_id": session_id}}

    for turno, (pregunta, esperada) in enumerate(interacciones, start=1):
        resultado = agente_con_memoria.invoke({"entrada": pregunta}, config)
        usadas = [
            accion.tool for accion, _ in resultado["intermediate_steps"]
        ]
        mensajes = len(obtener_historial(session_id).messages)

        print(f"\n--- Sesión {session_id} | Turno {turno} ---")
        print(f"Cliente: {pregunta}")
        print(f"Agente: {resultado['output']}")
        print(f"Herramientas: {usadas or 'ninguna'}")
        print(f"Mensajes en el historial: {mensajes}")

        if esperada == SIN_HERRAMIENTAS:
            assert usadas == []
        elif esperada is not None:
            assert esperada in usadas

        # Cada turno agrega solo su pregunta y su respuesta. Otro número
        # indicaría que el historial no se guarda o que se mezcla.
        assert mensajes == turno * 2


if __name__ == "__main__":

    for session_id, interacciones in SESIONES.items():
        ejecutar_sesion(session_id, interacciones)

    print("\n--- Resumen de sesiones ---")
    for session_id in SESIONES:
        mensajes = len(obtener_historial(session_id).messages)
        print(f"{session_id}: {mensajes} mensajes")
        cerrar_sesion(session_id)
