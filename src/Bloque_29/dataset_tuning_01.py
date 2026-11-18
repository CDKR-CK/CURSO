# pip install google-genai python-dotenv
#

import json
import time
from collections import Counter

from google import genai
from google.genai import types

MODELO_BASE = "gemini-3.8-flash"
ENVIAR_TRABAJO = False  # Cambiar a True solo si tu cuenta tiene tuning habilitado (genera costo)

CLAVES_ESPERADAS = ("intencion", "prioridad")
INTENCIONES_VALIDAS = {
    "estado_pedido", "cotizacion", "reembolso",
    "alergenos", "despacho", "conservacion",
}
PRIORIDADES_VALIDAS = {"alta", "media", "baja"}


# ---------------------------------------------------------------------------
# Paso 1: tarea de la Chocolatería y 18 ejemplos (3 por intención)
# ---------------------------------------------------------------------------
ejemplos_raw: list[tuple[str, dict]] = [
    # estado_pedido
    ("Hola, ¿en qué va mi pedido CH-1001? Lo compré hace una semana.",
     {"intencion": "estado_pedido", "prioridad": "media"}),
    ("Necesito saber hoy si el pedido CH-1003 llega, es para un cumpleaños de mañana.",
     {"intencion": "estado_pedido", "prioridad": "alta"}),
    ("Cuando puedan me cuentan si ya despacharon lo que pedí, no hay apuro.",
     {"intencion": "estado_pedido", "prioridad": "baja"}),

    # cotizacion
    ("¿Cuánto me salen 3 cajas de trufas?",
     {"intencion": "cotizacion", "prioridad": "baja"}),
    ("Quiero comprar 20 cajas de alfajores para un evento de la empresa el viernes, ¿cuál es el total?",
     {"intencion": "cotizacion", "prioridad": "media"}),
    ("Precio de 2 barras de chocolate amargo y una caja de bombones surtidos.",
     {"intencion": "cotizacion", "prioridad": "baja"}),

    # reembolso
    ("Me llegaron los bombones derretidos y quiero que me devuelvan la plata.",
     {"intencion": "reembolso", "prioridad": "alta"}),
    ("Me cobraron dos veces la caja de trufas, necesito el reembolso de un cargo.",
     {"intencion": "reembolso", "prioridad": "alta"}),
    ("Pedí alfajores y vinieron barras, ¿pueden devolverme el dinero?",
     {"intencion": "reembolso", "prioridad": "media"}),

    # alergenos
    ("Mi hijo es alérgico al maní, ¿los bombones surtidos tienen trazas?",
     {"intencion": "alergenos", "prioridad": "alta"}),
    ("¿El chocolate amargo lleva leche? Soy intolerante a la lactosa.",
     {"intencion": "alergenos", "prioridad": "media"}),
    ("Por curiosidad, ¿las trufas tienen gluten?",
     {"intencion": "alergenos", "prioridad": "baja"}),

    # despacho
    ("¿Hacen envíos a Puerto Montt y cuánto tardan?",
     {"intencion": "despacho", "prioridad": "baja"}),
    ("Necesito cambiar la dirección de entrega de mi pedido antes de que salga hoy.",
     {"intencion": "despacho", "prioridad": "alta"}),
    ("¿El despacho es gratis sobre algún monto de compra?",
     {"intencion": "despacho", "prioridad": "baja"}),

    # conservacion
    ("¿Cómo guardo las trufas para que no se echen a perder?",
     {"intencion": "conservacion", "prioridad": "baja"}),
    ("Compré chocolates para regalar en un mes, ¿alcanzan a durar hasta entonces?",
     {"intencion": "conservacion", "prioridad": "media"}),
    ("¿Puedo dejar los bombones en el refrigerador?",
     {"intencion": "conservacion", "prioridad": "baja"}),
]

examples = [
    types.TuningExample(text_input=texto, output=json.dumps(salida, ensure_ascii=False))
    for texto, salida in ejemplos_raw
]

print("=== Paso 1: dataset ===")
print(len(examples), "ejemplos construidos")
print(examples[0])
print()


# ---------------------------------------------------------------------------
# Paso 2: balance entre categorías
# ---------------------------------------------------------------------------
def chequear_balance(ejemplos_raw: list[tuple[str, dict]], clave: str) -> Counter:
    categorias = Counter(salida[clave] for _, salida in ejemplos_raw)
    return categorias


def mostrar_balance(ejemplos_raw: list[tuple[str, dict]], clave: str) -> None:
    balance = chequear_balance(ejemplos_raw, clave)
    print(f"Balance por '{clave}':")
    for categoria, cuenta in balance.most_common():
        print(f"  {categoria}: {cuenta}")
    maximo = max(balance.values())
    minimo = min(balance.values())
    print(f"  razón máx/mín: {maximo / minimo:.1f}x".replace(".", ","))


print("=== Paso 2: balance ===")
mostrar_balance(ejemplos_raw, "intencion")
mostrar_balance(ejemplos_raw, "prioridad")
print()


# ---------------------------------------------------------------------------
# Paso 3: validación antes de enviar nada
# ---------------------------------------------------------------------------
def validar_dataset(
    examples: list[types.TuningExample], claves_esperadas: tuple[str, ...]
) -> list[str]:
    problemas = []
    vistos = set()
    for i, ej in enumerate(examples):
        if not ej.text_input or not ej.text_input.strip():
            problemas.append(f"ejemplo {i}: text_input vacio")
        if not ej.output or not ej.output.strip():
            problemas.append(f"ejemplo {i}: output vacio")
            continue
        if ej.text_input in vistos:
            problemas.append(f"ejemplo {i}: text_input duplicado")
        vistos.add(ej.text_input)
        try:
            salida = json.loads(ej.output)
        except json.JSONDecodeError:
            problemas.append(f"ejemplo {i}: output no es JSON valido")
            continue
        for clave in claves_esperadas:
            if clave not in salida:
                problemas.append(f'ejemplo {i}: output no tiene la clave "{clave}"')
        # Extra de la Chocolatería: valores dentro del conjunto permitido
        if "intencion" in salida and salida["intencion"] not in INTENCIONES_VALIDAS:
            problemas.append(f'ejemplo {i}: intencion "{salida["intencion"]}" no permitida')
        if "prioridad" in salida and salida["prioridad"] not in PRIORIDADES_VALIDAS:
            problemas.append(f'ejemplo {i}: prioridad "{salida["prioridad"]}" no permitida')
    return problemas


def mostrar_problemas(examples: list[types.TuningExample]) -> list[str]:
    problemas = validar_dataset(examples, claves_esperadas=CLAVES_ESPERADAS)
    print(f"{len(examples)} ejemplos, {len(problemas)} problemas encontrados")
    for p in problemas:
        print(" -", p)
    return problemas


print("=== Paso 3: validación ===")
problemas = mostrar_problemas(examples)
print("✅ Dataset listo" if not problemas else "❌ Corrige el dataset antes de enviar")
print()

# Comprobar que el validador de verdad detecta errores (dataset roto a propósito)
print("=== Paso 3b: prueba del validador con dataset roto ===")
examples_rotos = examples + [
    types.TuningExample(text_input="", output='{"intencion": "despacho"}'),
    types.TuningExample(text_input=ejemplos_raw[0][0], output="no es json"),
    types.TuningExample(text_input="¿Venden helados?",
                        output="{'intencion': 'otro', 'prioridad': 'baja'}"),
    types.TuningExample(text_input="Quiero devolver mi pedido.",
                        output='{"intencion": "devolucion", "prioridad": "urgente"}'),
]
mostrar_problemas(examples_rotos)
print()


# ---------------------------------------------------------------------------
# Paso 4: enviar (opcional) y seguir el estado del trabajo hasta que termine
# ---------------------------------------------------------------------------
def esperar_a_que_termine(
    client: genai.Client, nombre_trabajo: str, intervalo_segundos: int = 30
) -> types.TuningJob:
    estados_finales = {
        types.JobState.JOB_STATE_SUCCEEDED,
        types.JobState.JOB_STATE_FAILED,
        types.JobState.JOB_STATE_CANCELLED,
        types.JobState.JOB_STATE_PARTIALLY_SUCCEEDED,
    }
    while True:
        trabajo = client.tunings.get(name=nombre_trabajo)
        print(f"estado actual: {trabajo.state}")
        if trabajo.state in estados_finales:
            return trabajo
        time.sleep(intervalo_segundos)


dataset = types.TuningDataset(examples=examples)
config = types.CreateTuningJobConfig(
    tuning_mode=types.TuningMode.TUNING_MODE_PEFT_ADAPTER,
    adapter_size=types.AdapterSize.ADAPTER_SIZE_FOUR,  # chico: dataset de 18 ejemplos
    epoch_count=5,
    tuned_model_display_name="clasificador-mensajes-chocolateria",
)

print("=== Paso 4: trabajo de tuning ===")
print(f"Configuración construida: modo={config.tuning_mode}, "
      f"adapter={config.adapter_size}, épocas={config.epoch_count}")

if ENVIAR_TRABAJO and not problemas:
    from dotenv import load_dotenv

    load_dotenv()
    cliente = genai.Client()
    try:
        trabajo = cliente.tunings.tune(
            base_model=MODELO_BASE,
            training_dataset=dataset,
            config=config,
        )
        print("Trabajo creado:", trabajo.name)
        trabajo_final = esperar_a_que_termine(cliente, trabajo.name)
        print("Estado final:", trabajo_final.state)
    except Exception as error:
        print("No se pudo crear el trabajo de tuning:", error)
else:
    print("Envío desactivado (ENVIAR_TRABAJO = False): no se llamó a la API.")
