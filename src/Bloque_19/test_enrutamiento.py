# Necesario para pytest
from dotenv import load_dotenv
load_dotenv()

from unittest.mock import MagicMock
from langchain_core.messages import AIMessage
 
from enrutamiento import (
    construir_cadena_con_enrutamiento,
    construir_paso_clasificacion,
)

def test_enrutamiento_va_a_cadena_queja():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "queja"
    cadena_queja_falsa = MagicMock()
    cadena_queja_falsa.return_value = "respuesta de queja"
 
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_queja=cadena_queja_falsa,
    )
    resultado = cadena.invoke({"mensaje": "esto no funciona nunca"})
 
    assert cadena_queja_falsa.called
    assert resultado == "respuesta de queja"

def test_enrutamiento_va_a_cadena_pregunta():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "pregunta"
    cadena_pregunta_falsa = MagicMock()
    cadena_pregunta_falsa.return_value = "respuesta de pregunta"
 
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_pregunta=cadena_pregunta_falsa,
    )
    resultado = cadena.invoke(
        {"mensaje": "¿cómo cambio mi contraseña?"}
    )
 
    assert cadena_pregunta_falsa.called
    assert resultado == "respuesta de pregunta"

def test_enrutamiento_va_a_cadena_sugerencia():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "sugerencia"
    cadena_sugerencia_falsa = MagicMock()
    cadena_sugerencia_falsa.return_value = "respuesta de sugerencia"
 
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_sugerencia=cadena_sugerencia_falsa,
    )
    resultado = cadena.invoke(
        {"mensaje": "¿cómo cambio mi contraseña?"}
    )
 
    assert cadena_sugerencia_falsa.called
    assert resultado == "respuesta de sugerencia"

def test_enrutamiento_va_a_cadena_default():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "default - categoria_inventada"
    cadena_default_falsa = MagicMock()
    cadena_default_falsa.return_value = "respuesta de default"
 
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_pregunta=cadena_default_falsa, # lo manda a "pregunta" al no calzar con otras categorias pero podria hacerse una espacial para "default"
    )
    resultado = cadena.invoke(
        {"mensaje": "mensaje ambiguo"}
    )
 
    assert cadena_default_falsa.called
    assert resultado == "respuesta de default"

def test_clasificacion_normaliza_antes_de_comparar():
    modelo_falso = MagicMock()
    modelo_falso.return_value = AIMessage(content=" Queja \n")
 
    resultado = construir_paso_clasificacion(modelo_falso).invoke(
        {"mensaje": "algo salió mal"}
    )
 
    assert resultado == "queja"






