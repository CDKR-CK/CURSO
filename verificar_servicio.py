from fastapi.testclient import TestClient

from servicio.main import app

cliente = TestClient(app)
PREGUNTA = "Cual es el plazo para devolver un producto?"


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
        for nombre in ("Consulta", "Respuesta", "EstadoEnvio")
        for campo, datos in esquemas[nombre]["properties"].items()
        if "description" not in datos
    ]
    if sin:
        return False, f"sin descripcion: {sin}"
    return True, "todos los campos tienen descripcion"




