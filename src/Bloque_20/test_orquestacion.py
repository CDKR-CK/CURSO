from unittest.mock import MagicMock
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from enrutamiento3 import (
    construir_cadena_con_enrutamiento,
    construir_cadena_queja_segura,
    construir_cadena_segura,
    construir_paso_clasificacion,
    procesar_mensaje_seguro,
)

def test_clasificacion_normaliza_antes_de_comparar():
    modelo_falso = MagicMock()
    modelo_falso.return_value = AIMessage(content=" Queja \n")
    resultado = construir_paso_clasificacion(modelo_falso).invoke(
        {"mensaje": "algo salió mal"}
    )
    assert resultado == "queja"

def test_enrutamiento_va_a_cadena_queja():
    clasificacion_falsa = MagicMock(return_value="queja")
    cadena_queja_falsa = MagicMock(return_value="respuesta de queja")
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_queja=cadena_queja_falsa,
    )
    resultado = cadena.invoke({"mensaje": "esto no funciona nunca"})
    assert cadena_queja_falsa.called
    assert resultado == "respuesta de queja"

def test_enrutamiento_va_a_cadena_pregunta():
    clasificacion_falsa = MagicMock(return_value="pregunta")
    cadena_pregunta_falsa = MagicMock(return_value="respuesta de pregunta")
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_pregunta=cadena_pregunta_falsa,
    )
    resultado = cadena.invoke({"mensaje": "¿cómo cambio mi contraseña?"})
    assert cadena_pregunta_falsa.called
    assert resultado == "respuesta de pregunta"

def test_enrutamiento_va_a_cadena_sugerencia():
    clasificacion_falsa = MagicMock(return_value="sugerencia")
    cadena_sugerencia_falsa = MagicMock(return_value="respuesta de sugerencia")
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_sugerencia=cadena_sugerencia_falsa,
    )
    resultado = cadena.invoke({"mensaje": "sería bueno un modo oscuro"})
    assert cadena_sugerencia_falsa.called
    assert resultado == "respuesta de sugerencia"

def test_enrutamiento_usa_default_ante_categoria_desconocida():
    clasificacion_falsa = MagicMock(return_value="categoria_inventada")
    cadena_default_falsa = MagicMock(return_value="respuesta por defecto")
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_pregunta=cadena_default_falsa,  # la ruta por defecto es cadena_pregunta
    )
    resultado = cadena.invoke({"mensaje": "mensaje ambiguo"})
    assert cadena_default_falsa.called
    assert resultado == "respuesta por defecto"

def test_cadena_queja_usa_fallback_ante_fallo_del_modelo():
    def fallar_a_proposito(x):
        raise ConnectionError("simulado")

    cadena_queja_falsa = RunnableLambda(fallar_a_proposito)
    cadena_queja_segura = construir_cadena_queja_segura(cadena_queja_falsa)

    resultado = cadena_queja_segura.invoke({"mensaje": "esto no funciona"})

    assert "equipo" in resultado.lower()

def test_cadena_pregunta_usa_fallback_ante_fallo_del_modelo():
    def fallar_a_proposito(x):
        raise ConnectionError("simulado")

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=MagicMock(return_value="pregunta"),
        cadena_pregunta=construir_cadena_segura(
            RunnableLambda(fallar_a_proposito)
        ),
    )
    resultado = cadena.invoke({"mensaje": "¿cómo cambio mi contraseña?"})

    assert "equipo" in resultado.lower()

def test_cadena_sugerencia_usa_fallback_ante_fallo_del_modelo():
    def fallar_a_proposito(x):
        raise ConnectionError("simulado")

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=MagicMock(return_value="sugerencia"),
        cadena_sugerencia=construir_cadena_segura(
            RunnableLambda(fallar_a_proposito)
        ),
    )
    resultado = cadena.invoke({"mensaje": "sería bueno un modo oscuro"})

    assert "equipo" in resultado.lower()

def test_procesar_mensaje_seguro_no_propaga_excepciones():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.side_effect = ConnectionError("simulado")

    cadena_falsa = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
    )

    resultado = procesar_mensaje_seguro(cadena_falsa, "mensaje de prueba")

    assert "no pudimos procesar" in resultado.lower()





