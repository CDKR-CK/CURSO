# pip install langchain-core langchain-classic langchain-google-genai pydantic python-dotenv

"""
Agente de atención al cliente de una chocolatería.

- Herramientas: políticas, estado de pedidos, total de compra y reembolso.
- Memoria por sesión con RunnableWithMessageHistory (Bloque 22).
- Supervisión humana con tiempo límite para el reembolso, acción
  irreversible, y registro de cada aprobación (Bloque 23).
- Traza de decisión guardada en z_trazas_agente.jsonl, una línea JSON
  por interacción (Bloque 23).

"""

import json
import queue
import sys
import threading
import unicodedata
from datetime import datetime, timezone
from pathlib import Path


from dotenv import load_dotenv
from langchain_classic.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import AIMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

load_dotenv()
modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")


# ---------------------------------------------------------------------------
# DATOS
# ---------------------------------------------------------------------------

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

# Memoria por sesión (Bloque 22)
historiales = {}

# Decisiones de aprobación humana (Bloque 23)
registro_aprobaciones: list[dict] = []

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


# ---------------------------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------------------------

def normalizar(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto.lower())
    return "".join(
        caracter for caracter in descompuesto
        if unicodedata.category(caracter) != "Mn"
    )


def formatear_pesos(monto: int) -> str:
    # Sin f-string: un formateador dejó {monto:,} como {monto: , }, que falla.
    return "$" + format(monto, ",").replace(",", ".")  # formato Chile


# ---------------------------------------------------------------------------
# SUPERVISIÓN HUMANA
# ---------------------------------------------------------------------------

def leer_linea_con_tiempo_limite(tiempo_limite_segundos: float) -> str | None:
    """Lee una línea de la entrada estándar. Devuelve None si se agota el
    tiempo o si la entrada se cierra sin datos."""
    cola_respuesta: queue.Queue[str] = queue.Queue(maxsize=1)

    def lector() -> None:
        try:
            cola_respuesta.put(sys.stdin.readline())
        except (OSError, ValueError):
            cola_respuesta.put("")

    # Hilo daemon: si se agota el tiempo, no impide que el programa termine
    threading.Thread(target=lector, daemon=True).start()
    try:
        linea = cola_respuesta.get(timeout=tiempo_limite_segundos)
    except queue.Empty:
        return None
    return linea or None  # "" = fin de entrada (EOF)


def esperar_aprobacion(
    mensaje: str,
    tiempo_limite_segundos: int = 300,
) -> bool:
    """Muestra el mensaje y espera 's' para aprobar. Cualquier otra
    respuesta, el fin de la entrada o el tiempo agotado se toman como
    rechazo (falla segura)."""
    print(mensaje, end="", flush=True)
    respuesta = leer_linea_con_tiempo_limite(tiempo_limite_segundos)
    if respuesta is None:
        print("\nSin respuesta: se rechaza por seguridad.")
        return False
    return respuesta.strip().lower() == "s"


def registrar_aprobacion(
    herramienta: str,
    argumentos: dict,
    aprobado: bool,
) -> None:
    registro_aprobaciones.append({
        "herramienta": herramienta,
        "argumentos": argumentos,
        "aprobado": aprobado,
        "momento": datetime.now().isoformat(),
    })


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


# HERRAMIENTA REEMBOLSO (riesgo alto: requiere aprobación humana)
@tool
def generar_reembolso(numero_pedido: str, monto: int) -> str:
    """Genera un reembolso para un pedido, con el monto en pesos chilenos
    sin decimales. Acción irreversible: requiere aprobación humana antes
    de ejecutarse."""
    if monto <= 0:
        return "Monto inválido: el reembolso debe ser mayor que cero."

    monto_texto = formatear_pesos(monto)  # $15.000
    mensaje = (
        f"El agente quiere reembolsar {monto_texto} "
        f"para el pedido {numero_pedido}. "
        f"¿Aprobar? (s/n): "
    )
    aprobado = esperar_aprobacion(mensaje)
    registrar_aprobacion(
        herramienta="generar_reembolso",
        argumentos={"numero_pedido": numero_pedido, "monto": monto},
        aprobado=aprobado,
    )

    if not aprobado:
        return (
            "Reembolso no aprobado por el "
            "supervisor humano."
        )

    return (
        f"Reembolso de {monto_texto} generado para "
        f"el pedido {numero_pedido}."
    )


# AGENTE
herramientas = [
    buscar_en_politicas,
    consultar_estado_pedido,
    calcular_total_compra,
    generar_reembolso,  # riesgo alto: pide aprobación humana (Bloque 23)
]

prompt_agente = ChatPromptTemplate.from_messages([
    (
        "system",
        (
            "Eres un asistente que responde preguntas usando las herramientas disponibles "
            "cuando las necesites. Nunca entregues números de teléfono ni inventes datos de la "
            "tienda, como correos u horarios. Si no tienes un dato, dilo. "
            # Corrección por la traza de cliente_02 (Bloque 23): el agente
            # dijo "pendiente de aprobación" sobre un reembolso ya aprobado.
            "Basa tu respuesta final solo en lo que devolvieron las "
            "herramientas: no agregues estados, pasos pendientes ni "
            "condiciones que la herramienta no informó. Si una herramienta "
            "confirma que una acción se realizó, informa que se realizó."
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


# MEMORIA
def obtener_historial(session_id: str):
    if session_id not in historiales:
        historiales[session_id] = InMemoryChatMessageHistory()
    return historiales[session_id]


def cerrar_sesion(session_id: str):
    """Borra el historial de una sesión; no falla si ya no existe."""
    historiales.pop(session_id, None)


def texto_de_salida(resultado: dict) -> str:
    """Entrega solo el texto de la respuesta final del agente."""
    # Gemini puede devolver la salida como lista de bloques.
    return AIMessage(content=resultado["output"]).text


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


# TRAZA DE DECISIÓN
ARCHIVO_TRAZAS = Path(__file__).resolve().parent / "z_trazas_agente.jsonl"

def registrar_traza(
    session_id: str,
    entrada: str,
    resultado: dict,
    aprobaciones: list[dict] | None = None,
) -> None:
    """Guarda una interacción del agente como una
    línea JSON en z_trazas_agente.jsonl: qué se
    preguntó, qué herramientas se usaron y con qué
    argumentos, si un humano aprobó o rechazó las de
    riesgo alto, y la respuesta final. Si "resultado"
    no trae "intermediate_steps" (por ejemplo, con
    return_intermediate_steps=False), acciones queda
    como una lista vacía en vez de fallar."""

    registro = {
        "timestamp": datetime.now(timezone.utc)
        .isoformat(),
        "session_id": session_id,
        "entrada": entrada,
        "acciones": [
            {
                "herramienta": accion.tool,
                "argumentos": accion.tool_input,
                "observacion": observacion,
            }
            for accion, observacion in resultado.get(
                "intermediate_steps", [])
        ],
        # La traza refleja la aprobación o el rechazo humano (Bloque 23)
        "aprobaciones": aprobaciones or [],
        "respuesta_final": resultado["output"]
    }

    with open(
        ARCHIVO_TRAZAS, "a", encoding="utf-8"
    ) as archivo:
        archivo.write(
            json.dumps(registro, ensure_ascii=False)
            + "\n"
        )


# PRUEBAS
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


def test_agente_no_usa_herramienta_para_pregunta_general():

    session_id = "prueba_general"
    resultado = agente_con_memoria.invoke(
        {"entrada": "¿Cómo puedo contactar a soporte?"},
        {"configurable": {"session_id": session_id}},
    )
    cerrar_sesion(session_id)

    assert resultado["intermediate_steps"] == []
    print(resultado["output"])


# TEST
if __name__ == "__main__":

    # Entradas que disparan al menos una herramienta de cada nivel de
    # riesgo del agente (bajo y alto; no tiene herramientas de riesgo medio).
    # Cada interacción queda como una línea en z_trazas_agente.jsonl.
    INTERACCIONES_TRAZA = {
        "cliente_01": [
            "¿Dónde está mi pedido CH-1001?",                  # bajo
            "¿Cuánto me costaría comprar 2 cajas de trufas?",  # bajo
            "¿Las cajas de bombones contienen maní?",          # bajo
        ],
        "cliente_02": [
            # alto: el supervisor humano lo aprueba
            "Mi pedido CH-1002 llegó con la caja de bombones rota. "
            "Genera un reembolso de $9.900 para ese pedido.",
        ],
        "cliente_03": [
            # alto: el supervisor humano lo rechaza
            "Genera un reembolso de $25.000 para el pedido CH-1003.",
        ],
    }

    for session_id, preguntas in INTERACCIONES_TRAZA.items():
        config = {"configurable": {"session_id": session_id}}
        for pregunta in preguntas:
            inicio_aprobaciones = len(registro_aprobaciones)
            resultado = agente_con_memoria.invoke(
                {"entrada": pregunta}, config
            )
            registrar_traza(
                session_id,
                pregunta,
                resultado,
                registro_aprobaciones[inicio_aprobaciones:],
            )
            usadas = [
                accion.tool for accion, _ in resultado["intermediate_steps"]
            ]
            print(f"\n--- Sesión {session_id} ---")
            print(f"Cliente: {pregunta}")
            print(f"Agente: {resultado['output']}")
            print(f"Herramientas: {usadas or 'ninguna'}")
        cerrar_sesion(session_id)

    print(f"\nTrazas guardadas en: {ARCHIVO_TRAZAS.name}")
