from fastapi import FastAPI

from servicio import logica
from servicio.esquemas import Consulta, EstadoEnvio, Respuesta

app = FastAPI(
    title="Asistente de soporte",
    version="0.1.0",
    description="Responde sobre devoluciones y envios, con sus fuentes.",
)


@app.get("/salud", tags=["sistema"], summary="Comprobar el servicio")
def salud():
    return {"estado": "ok"}


@app.post(
    "/consultas",
    response_model=Respuesta,
    tags=["consultas"],
    summary="Consultar el manual",
)
def consultar(consulta: Consulta):
    """Devuelve la respuesta y los documentos que la respaldan."""
    texto, fuentes = logica.responder(consulta.pregunta)
    return Respuesta(respuesta=texto, fuentes=fuentes)


@app.get(
    "/envios/{pedido_id}",
    response_model=EstadoEnvio,
    tags=["envios"],
    summary="Consultar el estado de un envio",
)
def consultar_envio(pedido_id: str):
    """Devuelve el estado del pedido segun los datos simulados."""
    return EstadoEnvio(
        pedido_id=pedido_id, estado=logica.estado_envio(pedido_id)
    )
