# ejecutar como en el entorno virtual: python inspeccionar.py main_v1

import importlib
import json
import sys

from fastapi.testclient import TestClient

modulo = importlib.import_module(sys.argv[1])
cliente = TestClient(modulo.app)
esquema = cliente.get("/openapi.json").json()
operacion = esquema["paths"]["/consultas"]["post"]
contenido = operacion["requestBody"]["content"]["application/json"]

print("resumen:", operacion.get("summary"))
print("descripcion:", repr(operacion.get("description")))
print("cuerpo de la peticion:", json.dumps(contenido["schema"]))
respuesta_200 = operacion["responses"]["200"]["content"]
print(
    "respuesta 200:",
    json.dumps(respuesta_200["application/json"]["schema"]),
)
print(
    "esquemas definidos:",
    sorted(esquema.get("components", {}).get("schemas", {})),
)





