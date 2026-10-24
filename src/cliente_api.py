# pip install requests python-dotenv

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

MODELO = "gemini-3.5-flash-lite"

URL = f"https://generativelanguage.googleapis.com/v1beta/interactions?key={API_KEY}"

# Reintentos ante error 429.
INTENTOS = 3
ESPERA_SEGUNDOS = 15


def enviar_peticion(pregunta):
    # Sin clave en el .env, API_KEY es None y la URL lleva "key=None" (Google respondería 400)
    if not API_KEY:
        raise ValueError("Clave API vacía o faltante. Agrega API_KEY en el .env.")
    cuerpo = {"model": MODELO, "input": pregunta}
    for intento in range(1, INTENTOS + 1):
        try:
            respuesta = requests.post(
                URL, json=cuerpo, timeout=10
            )
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ):
            raise TimeoutError("No se pudo contactar al proveedor. Puede ser momentáneo.")
        if respuesta.status_code == 400 and "API_KEY_INVALID" in respuesta.text:
            raise ValueError("Clave API inválida (error 400). Revisa el valor de API_KEY")
        if respuesta.status_code in (401, 403):
            raise ValueError("Credencial inválida o sin permiso. Revisa tu API_KEY.")
        if respuesta.status_code == 429:
            segundos = respuesta.headers.get("Retry-After")
            if intento < INTENTOS:
                espera = int(segundos) if segundos and segundos.isdigit() else ESPERA_SEGUNDOS
                print(f"Límite excedido. Intento {intento} de {INTENTOS}, reintentando en {espera}s...")
                time.sleep(espera)
                continue
            mensaje = f"Límite excedido. Reintentar en {segundos}s." if segundos else "Límite excedido."
            raise TimeoutError(f"{mensaje} Se hicieron {INTENTOS} intentos.")
        if respuesta.status_code >= 500:
            raise TimeoutError("El proveedor no pudo procesar la petición. Hay que esperar y reintentar.")
        if respuesta.status_code >= 400:
            raise RuntimeError(f"El servicio respondió con un error {respuesta.status_code}.")
        return respuesta.json()


def extraer_texto(datos):
    try:
        return datos["steps"][-1]["content"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("La respuesta no trae el texto generado en el lugar esperado.")


def consultar_modelo(pregunta):
    try:
        return extraer_texto(enviar_peticion(pregunta))
    except (ValueError, TimeoutError, RuntimeError) as error:
        return f"Error: {error}"


if __name__ == "__main__":
    respuesta = consultar_modelo("Hola, que modelo eres?")
    print(respuesta)
