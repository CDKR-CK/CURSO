# pip install pytest requests python-dotenv
# Pruebas de Funciones_04.py: envío de la petición, reintentos, cálculo de costo y consultar_modelo.
# Ejecutar con: python -m pytest test_cliente.py -v

from unittest.mock import Mock, patch

import pytest

import Funciones_04
from Funciones_04 import calcular_costo, con_reintento, consultar_modelo, enviar_peticion

URL_PRUEBA = "https://ejemplo.test/v1beta/interactions?key=clave_de_prueba"
BODY_PRUEBA = {"model": "modelo-de-prueba", "input": "test"}


@pytest.fixture(autouse=True)
def reiniciar_costo_total():
    # Cada prueba parte con el acumulado de la sesión en cero.
    Funciones_04.costo_total_sesion = 0.0
    yield


@pytest.fixture
def clave_api(monkeypatch):
    # armar_peticion exige API_KEY; se usa una clave falsa para no depender del .env.
    monkeypatch.setenv("API_KEY", "clave_de_prueba")


# ---------- enviar_peticion ----------

def test_enviar_peticion_credencial_invalida():
    respuesta_falsa = Mock(status_code=401)

    with patch("Funciones_04.requests.post", return_value=respuesta_falsa):
        with pytest.raises(ValueError):
            enviar_peticion(URL_PRUEBA, BODY_PRUEBA)


def test_enviar_peticion_limite_de_uso():
    respuesta_falsa = Mock(status_code=429)

    with patch("Funciones_04.requests.post", return_value=respuesta_falsa):
        with pytest.raises(TimeoutError):
            enviar_peticion(URL_PRUEBA, BODY_PRUEBA)


def test_enviar_peticion_exito():
    respuesta_falsa = Mock(status_code=200)
    respuesta_falsa.json.return_value = {"texto": "respuesta simulada"}

    with patch("Funciones_04.requests.post", return_value=respuesta_falsa) as mock_post:
        resultado = enviar_peticion(URL_PRUEBA, BODY_PRUEBA)

    assert resultado == {"texto": "respuesta simulada"}
    mock_post.assert_called_once_with(URL_PRUEBA, json=BODY_PRUEBA, timeout=Funciones_04.TIEMPO_LIMITE)


# ---------- con_reintento ----------

def test_con_reintento_espera_entre_intentos():
    intentos = {"n": 0}

    def funcion_que_falla_una_vez():
        intentos["n"] += 1
        if intentos["n"] == 1:
            raise TimeoutError("simulado")
        return "ok"

    with patch("Funciones_04.time.sleep") as mock_sleep:
        resultado = con_reintento(funcion_que_falla_una_vez)

    assert resultado == "ok"
    mock_sleep.assert_called_once()


def test_con_reintento_agota_intentos():
    def siempre_falla():
        raise TimeoutError("simulado")

    with patch("Funciones_04.time.sleep") as mock_sleep:
        with pytest.raises(TimeoutError):
            con_reintento(siempre_falla, intentos=3)

    # Espera entre intentos, no después del último: 3 intentos = 2 esperas.
    assert mock_sleep.call_count == 2


def test_con_reintento_no_reintenta_value_error():
    llamadas = {"n": 0}

    def falla_con_value_error():
        llamadas["n"] += 1
        raise ValueError("credencial inválida simulada")

    with patch("Funciones_04.time.sleep") as mock_sleep:
        with pytest.raises(ValueError):
            con_reintento(falla_con_value_error, intentos=3)

    # ValueError fallaría igual en cada intento: se lanza de inmediato, sin esperar.
    assert llamadas["n"] == 1
    mock_sleep.assert_not_called()


# ---------- calcular_costo ----------

def test_calcular_costo():
    datos = {"usage": {"total_input_tokens": 1000, "total_output_tokens": 500, "total_thought_tokens": 500}}

    costo, texto = calcular_costo(datos, precio_entrada=0.001, precio_salida=0.002)

    assert costo == pytest.approx(1000 * 0.001 + (500 + 500) * 0.002)
    assert "Tokens entrada: 1.000" in texto


# ---------- consultar_modelo ----------

def test_consultar_modelo_convierte_error(clave_api):
    # consultar_modelo no lanza la excepción: la devuelve como texto "Error: ...".
    with patch("Funciones_04.con_reintento", side_effect=TimeoutError("simulado")):
        resultado = consultar_modelo("pregunta de prueba")

    assert "Error: simulado" in resultado


def test_consultar_modelo_acumula_costo(clave_api):
    datos_falsos = {
        "steps": [{"content": [{"text": "respuesta simulada"}]}],
        "usage": {"total_input_tokens": 1000, "total_output_tokens": 0, "total_thought_tokens": 0},
    }
    costo_esperado, _ = calcular_costo(datos_falsos)

    with patch("Funciones_04.con_reintento", return_value=datos_falsos):
        resultado = consultar_modelo("pregunta de prueba")

    assert "respuesta simulada" in resultado
    assert Funciones_04.costo_total_sesion == pytest.approx(costo_esperado)



