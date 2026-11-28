from pydantic import BaseModel, Field


class Consulta(BaseModel):
    pregunta: str = Field(
        min_length=1,  # CA-03: una pregunta vacia se rechaza con 422
        description="Pregunta del cliente, en lenguaje natural.",
        examples=["¿Cuánto demora un despacho a Santiago?"],
    )


class Respuesta(BaseModel):
    respuesta: str = Field(
        description="Texto de la respuesta, con la cita de cada fuente, por ejemplo [doc1]."
    )
    fuentes: list[str] = Field(
        description="Identificadores de los documentos que la respaldan, con la forma [docN]; vacia si no hay."
    )


class EstadoPedido(BaseModel):
    pedido_id: str = Field(description="Número del pedido, por ejemplo CH-1001.")
    estado: str = Field(description="Estado del pedido según los datos simulados.")
