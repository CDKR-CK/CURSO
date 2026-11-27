from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Asistente de soporte", version="0.1.0")


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
