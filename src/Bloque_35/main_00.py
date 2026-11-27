# PowerShell: uvicorn main_00:app --reload
# http://127.0.0.1:8000/salud


# Paso 1: tu primer endpoint

from fastapi import FastAPI
 
app = FastAPI(title="Asistente de soporte", version="0.1.0")
 
 
@app.get("/salud")
def salud():
    return {"estado": "ok"}



# Paso 2: parámetros en la ruta y en la dirección
# http://127.0.0.1:8000/envios/PED-1001

PEDIDOS = {
    "PED-1001": "en transito, llega en 2 dias habiles",
    "PED-1002": "entregado",
}
 
 
@app.get("/envios/{pedido_id}")
def estado_envio(pedido_id: str, detalle: bool = False):
    estado = PEDIDOS.get(pedido_id, "sin informacion")
    if detalle:
        return {"pedido_id": pedido_id, "estado": estado, "simulado": True}
    return {"pedido_id": pedido_id, "estado": estado}


# Paso 3: el cuerpo de una petición con un modelo Pydantic
# curl -X POST http://127.0.0.1:8000/consultas -H "Content-Type: application/json" -d '{"pregunta": "Cual es el plazo para devolver?"}'

class Consulta(BaseModel):
    pregunta: str
 
 
class Respuesta(BaseModel):
    respuesta: str
    fuentes: list[str]
 
 
@app.post("/consultas", response_model=Respuesta)
def consultar(consulta: Consulta):
    if "devol" in consulta.pregunta.lower():
        return Respuesta(
            respuesta="Tienes 30 dias desde la compra para devolver.",
            fuentes=["manual.pdf"],
        )
    return Respuesta(
        respuesta="No encuentro esa informacion en el manual.", fuentes=[]
    )


# Paso 4: respuestas claras
# http://127.0.0.1:8000/salud
# http://127.0.0.1:8000/docs    - crea documentación
# http://127.0.0.1:8000/redoc
# http://127.0.0.1:8000/openapi.json






