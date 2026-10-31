# pip install requests python-dotenv
# REFACTORIZADO DEF + COSTO + MANEJO DE ERRORES + SCHEMA + PARSEO + REINTENTOS CON ESPERA EXPONENCIAL

import os
import re
import json
import time
import random
import requests
from typing import Callable, Any
from dotenv import load_dotenv

load_dotenv()

INTENTOS = 3            # intentos ante errores momentáneos (timeout, sin conexión, 429, 5xx)
ESPERA_BASE = 2         # segundos de espera tras el 1.er fallo; se duplica en cada intento
ESPERA_MAXIMA = 30      # tope de segundos de espera entre intentos
TIEMPO_LIMITE = 10      # segundos máximos de espera por cada petición

# response_schema https://ai.google.dev/gemini-api/docs/structured-output?hl=es-419
esquema_respuesta = {
    "type": "object",
    "properties": {
        "Respuesta": {"type": "string"},
        "Fuente": {"type": "string"},
        "año": {"type": "integer"}
    },
    "required": ["Respuesta", "Fuente", "año"]
}

# Acumula el costo (US$) de todas las preguntas
costo_total_sesion = 0.0


def parsear_respuesta_json(texto, claves_requeridas=("Respuesta", "Fuente")):
    # Quita Markdown (```json ... ```).
    texto_limpio = texto.strip()
    texto_limpio = re.sub(r"^```(?:json)?\s*", "", texto_limpio)
    texto_limpio = re.sub(r"\s*```$", "", texto_limpio)
    try:
        datos = json.loads(texto_limpio)
    except json.JSONDecodeError:
        raise ValueError("La respuesta del modelo no es JSON válido.")
    if not isinstance(datos, dict) or any(clave not in datos for clave in claves_requeridas):
        raise ValueError("La respuesta no tiene la estructura esperada.")
    return datos

def extraer_texto(datos):
    try:
        return datos["steps"][-1]["content"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("La respuesta no trae el texto generado en el lugar esperado.")

def formatear_usd(valor):
    # Formato chileno: punto para miles y coma para decimales (6 decimales).
    return f"{valor:,.6f}".replace(",", "#").replace(".", ",").replace("#", ".")

def calcular_costo(datos, precio_entrada=0.30/1_000_000, precio_salida=2.50/1_000_000):
    # costo: https://ai.google.dev/gemini-api/docs/pricing?hl=es-419#gemini-3.5-flash-lite
    try:
        uso = datos["usage"]
    except KeyError:
        raise RuntimeError("La respuesta no trae el uso de tokens.")
    tokens_entrada = uso.get("total_input_tokens", 0)
    tokens_salida = uso.get("total_output_tokens", 0)
    tokens_razonamiento = uso.get("total_thought_tokens", 0)
    costo = (tokens_entrada * precio_entrada) + ((tokens_salida + tokens_razonamiento) * precio_salida)

    miles = lambda n: f"{n:,}".replace(",", ".")
    # Devuelve el costo numérico (para acumular) y el texto para mostrar.
    return costo, (f"Tokens entrada: {miles(tokens_entrada)} | "
                   f"salida: {miles(tokens_salida)} | "
                   f"razonamiento: {miles(tokens_razonamiento)} | "
                   f"Costo: US$ {formatear_usd(costo)}")

def enviar_peticion(url, body):
    # Hace una sola llamada. Los errores momentáneos se lanzan como TimeoutError para que con_reintento los repita.
    try:
        respuesta = requests.post(url, json=body, timeout=TIEMPO_LIMITE)
    except (requests.exceptions.MissingSchema, requests.exceptions.InvalidSchema, requests.exceptions.InvalidURL):
        raise RuntimeError("La URL del servicio está mal escrita.")
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        raise TimeoutError("No se pudo contactar al proveedor. Puede ser momentáneo.")
    if respuesta.status_code == 400 and "API_KEY_INVALID" in respuesta.text:
        raise ValueError("Clave API inválida (error 400). Revisa el valor de API_KEY.")
    if respuesta.status_code in (401, 403):
        raise ValueError("Credencial inválida o sin permiso. Revisa tu API_KEY.")
    if respuesta.status_code == 404:
        raise RuntimeError("La URL del servicio no existe (error 404). Revisa la dirección.")
    if respuesta.status_code == 429:
        raise TimeoutError("Límite de peticiones excedido (error 429).")
    if respuesta.status_code >= 500:
        raise TimeoutError(f"El proveedor no pudo procesar la petición (error {respuesta.status_code}).")
    if respuesta.status_code >= 400:
        raise RuntimeError(f"El servicio respondió con un error {respuesta.status_code}.")
    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llegó en el formato esperado.")

def con_reintento(
    funcion: Callable[[], Any],
    intentos: int = INTENTOS,
    espera_base: float = ESPERA_BASE,
    espera_maxima: float = ESPERA_MAXIMA,
) -> Any:
    # Repite la función solo ante TimeoutError, con espera exponencial (2, 4, 8... s) más un 0-10 % al azar.
    # ValueError y RuntimeError no se repiten: fallarían igual en cada intento.
    for intento in range(1, intentos + 1):
        try:
            return funcion()
        except TimeoutError as error:
            if intento == intentos:
                raise TimeoutError(f"{error} Se hicieron {intentos} intentos.") from error
            espera = min(espera_base * (2 ** (intento - 1)), espera_maxima)
            espera_con_jitter = espera + random.uniform(0, espera * 0.1)
            segundos = f"{espera_con_jitter:.1f}".replace(".", ",")
            print(f"Intento {intento} de {intentos} falló: {error} Reintentando en {segundos} s...")
            time.sleep(espera_con_jitter)

def armar_peticion(pregunta, instruccion_sistema="", esquema=""):
    if not isinstance(instruccion_sistema, str):
        raise ValueError("La instrucción de sistema debe ser texto")
    if not isinstance(pregunta, str):
        raise ValueError("La pregunta debe ser texto")
    if not pregunta.strip():
        raise ValueError("La pregunta no puede estar vacía")
    if re.fullmatch(r"[\d\s.,+\-]+", pregunta):
        raise ValueError("La pregunta no puede contener solo números")
    api_key = os.getenv("API_KEY")
    # Sin clave en el .env, API_KEY es None y la URL lleva "key=None" (Google respondería 400)
    if not api_key:
        raise ValueError("Clave API vacía o faltante. Agrega API_KEY en el .env.")
    modelo = "gemini-3.5-flash-lite"
    url = f"https://generativelanguage.googleapis.com/v1beta/interactions?key={api_key}" #URL correcta
    # url = f"https://generativelanguage.xxxgoogleapis.com/v1beta/interactions?key={api_key}"

    body = {"model": modelo, "input": pregunta}
    # Instrucción de sistema separada de la pregunta (se omite si viene vacía)
    if instruccion_sistema.strip():
        body["system_instruction"] = instruccion_sistema
    # Respuesta estructurada en JSON según el esquema (se omite si no viene esquema)
    if esquema:
        body["response_format"] = {
            "type": "text",
            "mime_type": "application/json",
            "schema": esquema
        }
    #print(body) #muestra el body
    return url, body

def consultar_modelo(pregunta, instruccion_sistema="", esquema="", mostrar_costo=True):
    # Orden: pregunta, instruccion_sistema, esquema. Los dos últimos son opcionales ("" = no entregado).
    # mostrar_costo=False omite la línea de tokens y costo (el costo igual se suma a costo_total_sesion).
    global costo_total_sesion
    encabezado = f"Pregunta: {pregunta}"
    try:
        url, body = armar_peticion(pregunta, instruccion_sistema, esquema)
        # Solo se reintenta el envío; la petición se arma una sola vez.
        datos = con_reintento(lambda: enviar_peticion(url, body))
        # Se suma apenas llega la respuesta: los tokens se cobran aunque después falle el parseo.
        costo, texto_costo = calcular_costo(datos)
        costo_total_sesion += costo
        texto = extraer_texto(datos)

        # verifica esquema y convierte el JSON a diccionario y valida las claves.
        if esquema:
            respuesta = parsear_respuesta_json(texto, esquema.get("required", []))
            texto = "\n".join(f"{clave}: {valor}" for clave, valor in respuesta.items())
        else:
            texto = f"Respuesta: {texto}"
        if not mostrar_costo:
            return f"{encabezado}\n{texto}\n"
        return f"{encabezado}\n{texto}\n{texto_costo}\n"
    except (ValueError, RuntimeError, TimeoutError) as error:
        return f"{encabezado}\nError: {error}\n"

if __name__ == "__main__":
    # preguntas:
    print(consultar_modelo("¿Qué es Python?","Responde con un maximo de 10 palabras"))
    #print(consultar_modelo("Hola. Que modelo eres?", "Responde con un maximo de 10 palabras, al finalizar escribe FIN!", esquema_respuesta))
    #print(consultar_modelo("Hola. Que modelo eres?", "Responde con un maximo de 10 palabras"))  # sin esquema
    #print(consultar_modelo("Hola. Que modelo eres?"))  # sin instrucción ni esquema
    #print(f"Costo total de la sesión: US$ {formatear_usd(costo_total_sesion)}")
    


