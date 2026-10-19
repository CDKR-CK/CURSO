# pip install requests python-dotenv

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

clave_api = os.getenv("API_KEY")
  
url_api = "https://generativelanguage.googleapis.com/v1beta/interactions"

carga_util = json.dumps({
    "model": "gemini-3.5-flash-lite",
    "input": "Hola. Que modelo eres?"
})

encabezados = {
    "x-goog-api-key": clave_api,
    "Content-Type": "application/json"
}

respuesta = requests.request("POST", url_api, headers=encabezados, data=carga_util)

print(respuesta)
print("\n")

print(respuesta.text)
print("\n")

datos_respuesta = respuesta.json()
texto_modelo = datos_respuesta["steps"][-1]["content"][0]["text"]

print(texto_modelo)




