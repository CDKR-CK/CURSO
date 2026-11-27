import importlib

from fastapi.testclient import TestClient

for nombre in ("main_v1", "main_v2"):
    modulo = importlib.import_module(nombre)
    cliente = TestClient(modulo.app, raise_server_exceptions=False)
    r = cliente.post("/consultas", json={"texto": "hola"})
    print(nombre, r.status_code, r.text)





