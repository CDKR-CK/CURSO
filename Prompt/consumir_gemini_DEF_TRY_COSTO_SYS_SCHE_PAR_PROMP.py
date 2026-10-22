# BANCO DE PROMPTS

import os
import json
import time
from consumir_gemini_DEF_TRY_COSTO_SYS_SCHE_PAR import (
    esquema_respuesta,
    armar_peticion,
    enviar_peticion,
    extraer_texto,
    parsear_respuesta_json,
)

INSTRUCCION_CONSULTA = "Responde con un maximo de 10 palabras, al finalizar escribe FIN!"

BANCO_DE_PROMPTS = [
    {
        "nombre": "clasificar_sentimiento",
        "system_instruction": (
            "Responde únicamente con un JSON con las claves 'sentimiento' "
            "('positivo', 'negativo' o 'neutro') y 'confianza' (0 a 1)."
        ),
        "ejemplo_usuario": "El servicio llegó tarde pero el producto está perfecto.",
        "claves_esperadas": ["sentimiento", "confianza"],
        # JSON Schema en minúsculas (formato de la Interactions API)
        "response_schema": {
            "type": "object",
            "properties": {
                "sentimiento": {"type": "string", "enum": ["positivo", "negativo", "neutro"]},
                "confianza": {"type": "number"}
            },
            "required": ["sentimiento", "confianza"]
        },
    },
    {
        "nombre": "consulta_modelo",
        "system_instruction": INSTRUCCION_CONSULTA,
        "ejemplo_usuario": "Hola. Que modelo eres?",
        "claves_esperadas": esquema_respuesta["required"],
        "response_schema": esquema_respuesta,
    },
    {
        "nombre": "consulta_luna",
        "system_instruction": INSTRUCCION_CONSULTA,
        "ejemplo_usuario": "Que sabes de la Luna?",
        "claves_esperadas": esquema_respuesta["required"],
        "response_schema": esquema_respuesta,
    },
    {
        "nombre": "consulta_capitales",
        "system_instruction": INSTRUCCION_CONSULTA,
        "ejemplo_usuario": "Capitales en Sudamérica?",
        "claves_esperadas": esquema_respuesta["required"],
        "response_schema": esquema_respuesta,
    },
    {
        "nombre": "consulta_fecha_historica",
        "system_instruction": INSTRUCCION_CONSULTA,
        "ejemplo_usuario": "¿Cuándo murió Julio César?",
        "claves_esperadas": esquema_respuesta["required"],
        "response_schema": esquema_respuesta,
    },
    {
        "nombre": "consulta_calculo",
        "system_instruction": INSTRUCCION_CONSULTA,
        "ejemplo_usuario": "¿Cuánto es 7 por 8?",
        "claves_esperadas": esquema_respuesta["required"],
        "response_schema": esquema_respuesta,
    },
    {
        "nombre": "consulta_fecha_actual",
        "system_instruction": INSTRUCCION_CONSULTA,
        "ejemplo_usuario": "¿qué día es hoy?",
        "claves_esperadas": esquema_respuesta["required"],
        "response_schema": esquema_respuesta,
    },
]

if __name__ == "__main__":
    registro = {}

    for prompt in BANCO_DE_PROMPTS:
        exitos = 0
        intentos = 3
        for intento in range(intentos):
            try:
                url, body = armar_peticion(
                    prompt["system_instruction"],
                    prompt["ejemplo_usuario"],
                    prompt.get("response_schema"),
                )
                respuesta = enviar_peticion(url, body)
                texto = extraer_texto(respuesta)
                datos = parsear_respuesta_json(texto, prompt["claves_esperadas"])
                if all(clave in datos for clave in prompt["claves_esperadas"]):
                    exitos += 1
            except (ValueError, RuntimeError) as error:
                print(f"  intento {intento + 1} falló: {error}")
            time.sleep(1)
        print(f"{prompt['nombre']}: {exitos}/{intentos} respuestas válidas")
        registro[prompt["nombre"]] = {"exitos": exitos, "intentos": intentos}

    # Carpeta prompts junto a este archivo (se crea si no existe)
    carpeta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
    os.makedirs(carpeta, exist_ok=True)
    with open(os.path.join(carpeta, "registro_resultados.json"), "w", encoding="utf-8") as archivo:
        json.dump(registro, archivo, indent=2, ensure_ascii=False)
