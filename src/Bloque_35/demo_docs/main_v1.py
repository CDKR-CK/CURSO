# uvicorn main_v1:app --reload

from fastapi import FastAPI

app = FastAPI(title="Asistente de soporte", version="0.1.0")


@app.post("/consultas")
def consultar(datos: dict):
    pregunta = datos["pregunta"]
    if "devol" in pregunta.lower():
        return {
            "respuesta": "Tienes 30 dias desde la compra para devolver.",
            "fuentes": ["manual.pdf"],
        }
    return {
        "respuesta": "No encuentro esa informacion en el manual.",
        "fuentes": [],
    }
