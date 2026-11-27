from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="Asistente de soporte",
    version="0.1.0",
    description="Responde preguntas sobre devoluciones y envios.",
)


class Consulta(BaseModel):
    pregunta: str = Field(
        description="Pregunta del usuario, en lenguaje natural.",
        examples=["Cual es el plazo para devolver un producto?"],
    )


class Respuesta(BaseModel):
    respuesta: str = Field(description="Texto de la respuesta.")
    fuentes: list[str] = Field(
        description="Documentos que respaldan la respuesta; vacia si no hay."
    )


@app.post(
    "/consultas",
    response_model=Respuesta,
    summary="Consultar el manual",
    tags=["consultas"],
)
def consultar(consulta: Consulta):
    """Recibe una pregunta y devuelve la respuesta con sus fuentes.

    Si el manual no cubre la pregunta, la respuesta lo dice y
    la lista de fuentes va vacia.
    """
    if "devol" in consulta.pregunta.lower():
        return Respuesta(
            respuesta="Tienes 30 dias desde la compra para devolver.",
            fuentes=["manual.pdf"],
        )
    return Respuesta(
        respuesta="No encuentro esa informacion en el manual.", fuentes=[]
    )
