# REFACTORIZADO
# pip install requests python-dotenv

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def armar_peticion(pregunta):
    api_key = os.getenv("API_KEY")
    modelo = "gemini-3.5-flash-lite"
    url = f"https://generativelanguage.googleapis.com/v1beta/interactions?key={api_key}"
    body = {"model": modelo, "input": pregunta}
    return url, body

def enviar_peticion(url, body):
    respuesta = requests.post(url, json=body)
    return respuesta.json()

def extraer_texto(datos):
    return datos["steps"][-1]["content"][0]["text"]

def obtener_dato_de_prueba(pregunta):
    url, body = armar_peticion(pregunta)
    datos = enviar_peticion(url, body)
    return extraer_texto(datos)

if __name__ == "__main__":
    print(obtener_dato_de_prueba("Hola. Que modelo eres?"))
    print(obtener_dato_de_prueba("Capital de Chile?"))
    print(obtener_dato_de_prueba("Que es refactorizar un codigo en 20 palabras?"))

