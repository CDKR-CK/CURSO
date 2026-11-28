from fastapi import FastAPI

from servicio import logica
from servicio.esquemas import Consulta, EstadoPedido, Respuesta

app = FastAPI(
    title="Asistente CHOCOLATERIA CK",
    version="0.1.0",
    description="Responde preguntas de clientes sobre despachos, devoluciones, alérgenos, "
                "conservación y precios, citando sus fuentes [docN].",
)


@app.get("/salud", tags=["sistema"], summary="Comprobar el servicio")
def salud():
    return {"estado": "ok"}


@app.post(
    "/consulta",
    response_model=Respuesta,
    tags=["consultas"],
    summary="Consultar la información de la tienda",
)
def consultar(consulta: Consulta):
    """Devuelve la respuesta y los documentos [docN] que la respaldan.

    Si la información de la tienda no cubre la pregunta, la respuesta lo dice
    y la lista de fuentes va vacía.
    """
    texto, fuentes = logica.responder(consulta.pregunta)
    return Respuesta(respuesta=texto, fuentes=fuentes)


@app.get(
    "/pedidos/{pedido_id}",
    response_model=EstadoPedido,
    tags=["pedidos"],
    summary="Consultar el estado de un pedido",
)
def consultar_pedido(pedido_id: str):
    """Devuelve el estado del pedido según los datos simulados (CH-1001, CH-1002)."""
    return EstadoPedido(pedido_id=pedido_id, estado=logica.estado_pedido(pedido_id))
