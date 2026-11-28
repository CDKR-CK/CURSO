# pip install fastapi==0.143.0 httpx2
# Verifica el servicio de la CHOCOLATERIA CK contra la documentacion y los criterios de
# aceptacion de la ficha (Bloque 34) que corresponden al hito H1. Usa el cliente de pruebas
# de FastAPI: no necesita servidor ni clave de API. Termina con codigo 0 si todo se cumple.
# Ejecutar desde la carpeta Bloque_35: python verificar_servicio.py

import re
import sys

from fastapi.testclient import TestClient

from servicio.main import app

# Consola de Windows: forzar UTF-8 para las tildes de las respuestas
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

cliente = TestClient(app)
PREGUNTA = "¿Cuánto demora un despacho a Santiago?"
PATRON_FUENTE = re.compile(r"^\[doc([1-9]|10)\]$")  # [doc1] a [doc10]


def esquema():
    return cliente.get("/openapi.json").json()


def docs_navegables():
    r = cliente.get("/docs")
    if r.status_code != 200:
        return False, f"/docs responde {r.status_code}"
    return True, f"rutas documentadas: {sorted(esquema()['paths'])}"


def campos_documentados():
    esquemas = esquema()["components"]["schemas"]
    sin = [
        f"{nombre}.{campo}"
        for nombre in ("Consulta", "Respuesta", "EstadoPedido")
        for campo, datos in esquemas[nombre]["properties"].items()
        if "description" not in datos
    ]
    if sin:
        return False, f"sin descripcion: {sin}"
    return True, "todos los campos tienen descripcion"


def ca_01():
    # RF-01: POST /consulta responde 200 con los campos "respuesta" y "fuentes"
    r = cliente.post("/consulta", json={"pregunta": PREGUNTA})
    ok = r.status_code == 200 and set(r.json()) == {"respuesta", "fuentes"}
    return ok, f"estado {r.status_code}, campos {sorted(r.json())}"


def ca_02():
    # RF-02: "fuentes" trae al menos un [docN] (N de 1 a 10) citado en el texto
    datos = cliente.post("/consulta", json={"pregunta": PREGUNTA}).json()
    validas = [f for f in datos["fuentes"] if PATRON_FUENTE.match(f)]
    ok = bool(validas) and all(f in datos["respuesta"] for f in validas)
    return ok, f"fuentes: {datos['fuentes']}"


def ca_03():
    # RF-01: pregunta vacia -> 422 con error en JSON, y la consulta siguiente vuelve a 200
    r_vacia = cliente.post("/consulta", json={"pregunta": ""})
    r_siguiente = cliente.post("/consulta", json={"pregunta": PREGUNTA})
    ok = (
        r_vacia.status_code == 422
        and "detail" in r_vacia.json()
        and r_siguiente.status_code == 200
    )
    return ok, f"vacia: {r_vacia.status_code}, siguiente: {r_siguiente.status_code}"


def ca_12():
    # RNF-04: pregunta sin respaldo -> dice que no tiene informacion y sin fuentes
    datos = cliente.post(
        "/consulta", json={"pregunta": "¿Tienen tienda física en Valparaíso?"}
    ).json()
    ok = datos["fuentes"] == [] and "no tengo información" in datos["respuesta"].lower()
    return ok, f"fuentes: {datos['fuentes']}"


def rf_03():
    # RF-03 (deseable): estado de un pedido con datos simulados
    r = cliente.get("/pedidos/CH-1001")
    return (
        r.status_code == 200 and "tránsito" in r.json()["estado"],
        f"estado: {r.json()['estado']}",
    )


COMPROBACIONES = [
    ("DOC-1", "documentacion en /docs", docs_navegables),
    ("DOC-2", "campos documentados", campos_documentados),
    ("CA-01", "respuesta con respuesta y fuentes", ca_01),
    ("CA-02", "fuente [docN] citada en el texto", ca_02),
    ("CA-03", "pregunta vacia: 422 y luego 200", ca_03),
    ("CA-12", "sin informacion: no inventa", ca_12),
    ("RF-03", "estado del pedido simulado CH-1001", rf_03),
]


def ejecutar(comprobaciones):
    cumplidas = 0
    for id_, descripcion, prueba in comprobaciones:
        try:
            ok, evidencia = prueba()
        except Exception as error:
            ok = False
            evidencia = f"error: {type(error).__name__}({error})"
        estado = "PASA " if ok else "FALLA"
        print(f"{estado} {id_} {descripcion} -> {evidencia}")
        cumplidas += 1 if ok else 0
    print(f"\n{cumplidas} de {len(comprobaciones)} comprobaciones cumplidas")
    return cumplidas == len(comprobaciones)


if __name__ == "__main__":
    raise SystemExit(0 if ejecutar(COMPROBACIONES) else 1)
