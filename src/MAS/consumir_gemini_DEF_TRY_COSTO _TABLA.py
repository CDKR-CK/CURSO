# pip install requests python-dotenv
# COMPARA 4 MODELOS GEMINI: COSTO, LATENCIA Y RESPUESTA + PROMEDIOS Y TOTALES

import os
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# modelo y precio US$/1.000.000 tokens (entrada, salida)
MODELOS = {
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-3.8-flash": (0.75, 3.75),
    "gemini-3.6-flash": (0.75, 3.75),
    "gemini-3.8-live": (0.75, 4.50),
}
PREGUNTA = "Cual es la capital de Chile? solo debes dar el nombre."
PRUEBAS = 2 # numero de pruebas

def armar_peticion(pregunta, modelo):
    if not isinstance(pregunta, str):
        raise ValueError("La pregunta debe ser texto")
    if not pregunta.strip():
        raise ValueError("La pregunta no puede estar vacía")
    if re.fullmatch(r"[\d\s.,+\-]+", pregunta):
        raise ValueError("La pregunta no puede contener solo números")
    api_key = os.getenv("API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/interactions?key={api_key}" #URL correcta
    # url = f"https://generativelanguage.xxxgoogleapis.com/v1beta/interactions?key={api_key}"

    body = {"model": modelo, "input": pregunta}
    return url, body

def enviar_peticion(url, body):
    try:
        respuesta = requests.post(url, json=body, timeout=60)
    except (requests.exceptions.MissingSchema, requests.exceptions.InvalidSchema, requests.exceptions.InvalidURL):
        raise RuntimeError("La URL del servicio está mal escrita.")
    except requests.exceptions.Timeout:
        raise RuntimeError("El servicio no respondió dentro de 60 segundos.")
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


def calcular_costo(datos, precio_entrada, precio_salida):
    # Precios en US$ por 1.000.000 tokens. El razonamiento se cobra como salida.
    # https://ai.google.dev/gemini-api/docs/pricing?hl=es-419
    try:
        uso = datos["usage"]
    except KeyError:
        raise RuntimeError("La respuesta no trae el uso de tokens.")
    tokens_entrada = uso.get("total_input_tokens", 0)
    tokens_salida = uso.get("total_output_tokens", 0)
    tokens_razonamiento = uso.get("total_thought_tokens", 0)
    return (tokens_entrada * precio_entrada + (tokens_salida + tokens_razonamiento) * precio_salida) / 1_000_000

def formato_cl(numero, decimales):
    # Punto para miles y coma para decimales
    return f"{numero:,.{decimales}f}".replace(",", "#").replace(".", ",").replace("#", ".")

def probar_modelo(modelo, precios):
    # Devuelve (costo, latencia en segundos, respuesta); costo y latencia son None si hubo error
    try:
        url, body = armar_peticion(PREGUNTA, modelo)
        inicio = time.perf_counter()
        datos = enviar_peticion(url, body)
        latencia = time.perf_counter() - inicio
        return calcular_costo(datos, *precios), latencia, extraer_texto(datos).strip()
    except (ValueError, RuntimeError) as error:
        return None, None, f"Error: {error}"

if __name__ == "__main__":
    print(f"Pregunta: {PREGUNTA}\n")
    print(f"{'Modelo':<24}{'Prueba':>7}{'Costo US$':>14}{'Latencia s':>12}  Respuesta")
    resultados = {modelo: [] for modelo in MODELOS}
    for modelo, precios in MODELOS.items():
        for prueba in range(1, PRUEBAS + 1):
            costo, latencia, respuesta = probar_modelo(modelo, precios)
            if costo is None:
                print(f"{modelo:<24}{prueba:>7}{'-':>14}{'-':>12}  {respuesta}")
            else:
                resultados[modelo].append((costo, latencia))
                print(f"{modelo:<24}{prueba:>7}{formato_cl(costo, 8):>14}{formato_cl(latencia, 3):>12}  {respuesta}")

    print(f"\n{'Modelo':<24}{'Costo prom.':>14}{'Costo total':>14}{'Latencia prom.':>16}{'Latencia total':>16}")
    todos = []
    for modelo, lista in resultados.items():
        if not lista:
            print(f"{modelo:<24}  Sin pruebas exitosas")
            continue
        todos += lista
        costos = [costo for costo, _ in lista]
        latencias = [latencia for _, latencia in lista]
        print(f"{modelo:<24}{formato_cl(sum(costos) / len(costos), 8):>14}{formato_cl(sum(costos), 8):>14}"
              f"{formato_cl(sum(latencias) / len(latencias), 3):>16}{formato_cl(sum(latencias), 3):>16}")
    if todos:
        costos = [costo for costo, _ in todos]
        latencias = [latencia for _, latencia in todos]
        print(f"{'TODOS':<24}{formato_cl(sum(costos) / len(costos), 8):>14}{formato_cl(sum(costos), 8):>14}"
              f"{formato_cl(sum(latencias) / len(latencias), 3):>16}{formato_cl(sum(latencias), 3):>16}")
