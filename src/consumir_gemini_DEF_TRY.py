# pip install requests python-dotenv
# REFACTORIZADO + MANEJO DE ERRORES

import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

def armar_peticion(pregunta):
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

def obtener_dato_de_prueba(pregunta):
    try:
        url, body = armar_peticion(pregunta)
        datos = enviar_peticion(url, body)
        return extraer_texto(datos)
    except (ValueError, RuntimeError) as error:
        return f"Error: {error}"

if __name__ == "__main__":
    print(obtener_dato_de_prueba(""))
    print(obtener_dato_de_prueba("123"))
    print(obtener_dato_de_prueba("Hola. Que modelo eres?"))