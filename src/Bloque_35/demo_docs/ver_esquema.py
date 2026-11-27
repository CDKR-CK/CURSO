import json

from fastapi.testclient import TestClient

from main_v3 import app

esquemas = (
    TestClient(app).get("/openapi.json").json()["components"]["schemas"]
)
print(json.dumps(esquemas["Consulta"], indent=2, ensure_ascii=False))
