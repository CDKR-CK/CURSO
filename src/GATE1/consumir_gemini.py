# pip install requests python-dotenv
# REFACTORIZADO DEF + COSTO + MANEJO DE ERRORES + SCHEMA + PARSEO

import os
import re
import json
import requests
from dotenv import load_dotenv

load_dotenv()

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

def armar_peticion(instruccion_sistema, pregunta, esquema=None):
    if not isinstance(instruccion_sistema, str):
        raise ValueError("La instrucción de sistema debe ser texto")
    if not isinstance(pregunta, str):
        raise ValueError("La pregunta debe ser texto")
    if not pregunta.strip():
        raise ValueError("La pregunta no puede estar vacía")
    if re.fullmatch(r"[\d\s.,+\-]+", pregunta):
        raise ValueError("La pregunta no puede contener solo números")
    api_key = os.getenv("API_KEY")
    modelo = "gemini-3.5-flash-lite"
    url = f"https://generativelanguage.googleapis.com/v1beta/interactions?key={api_key}" #URL correcta
    # url = f"https://generativelanguage.xxxgoogleapis.com/v1beta/interactions?key={api_key}"

    body = {"model": modelo, "input": pregunta}
    # Instrucción de sistema separada de la pregunta (se omite si viene vacía)
    if instruccion_sistema.strip():
        body["system_instruction"] = instruccion_sistema
    # Respuesta estructurada en JSON según el esquema (se omite si no viene esquema)
    if esquema is not None:
        body["response_format"] = {
            "type": "text",
            "mime_type": "application/json",
            "schema": esquema
        }
    #print(body) #muestra el body
    return url, body

def enviar_peticion(url, body):
    try:
        respuesta = requests.post(url, json=body)
    except (requests.exceptions.MissingSchema, requests.exceptions.InvalidSchema, requests.exceptions.InvalidURL):
        raise RuntimeError("La URL del servicio está mal escrita.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("No se pudo conectar con el servicio. Intenta de nuevo en unos segundos.")
    try:
        respuesta.raise_for_status()
    except requests.exceptions.HTTPError:
        if respuesta.status_code == 404:
            raise RuntimeError("La URL del servicio no existe (error 404). Revisa la dirección.")
        raise RuntimeError(f"El servicio respondió con un error {respuesta.status_code}.")
    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llegó en el formato esperado.")

def extraer_texto(datos):
    try:
        return datos["steps"][-1]["content"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("La respuesta no trae el texto generado en el lugar esperado.")

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
    costo_texto = f"{costo:,.6f}".replace(",", "#").replace(".", ",").replace("#", ".")
    return (f"Tokens entrada: {miles(tokens_entrada)} | "
            f"salida: {miles(tokens_salida)} | "
            f"razonamiento: {miles(tokens_razonamiento)} | "
            f"Costo: US$ {costo_texto}")

def obtener_dato_de_prueba(instruccion_sistema, pregunta):
    try:
        url, body = armar_peticion(instruccion_sistema, pregunta)
        datos = enviar_peticion(url, body)
        return extraer_texto(datos)
    except (ValueError, RuntimeError) as error:
        return f"Error: {error}"

def solicita_respuesta(instruccion_sistema, pregunta, esquema=None):
    encabezado = f"Pregunta: {pregunta}"
    try:
        url, body = armar_peticion(instruccion_sistema, pregunta, esquema)
        datos = enviar_peticion(url, body)
        texto = extraer_texto(datos)

        # verifica esquema y convierte el JSON a diccionario y valida las claves.
        if esquema is not None:
            respuesta = parsear_respuesta_json(texto, esquema.get("required", []))
            texto = "\n".join(f"{clave}: {valor}" for clave, valor in respuesta.items())
        return f"{encabezado}\n{texto}\n{calcular_costo(datos)}\n"
    except (ValueError, RuntimeError) as error:
        return f"{encabezado}\nError: {error}\n"

if __name__ == "__main__":
    # preguntas:
    print(solicita_respuesta("Responde con un maximo de 10 palabras, al finalizar escribe FIN!", "Hola. Que modelo eres?", esquema_respuesta))
    


