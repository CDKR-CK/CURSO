# pip install langgraph
#
# 🛑 Paso 2 (Bloque 32): punto de supervisión humana con LangGraph (interrupt + Command)
# antes de activar una nueva versión del prompt de la Chocolatería en producción.
# Prueba el camino de aprobación y el de rechazo, cada uno con su propio thread_id.
# Ejecutar: python Paso_02_grafo_supervision_01.py

from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class EstadoDespliegue(TypedDict):
    huella_nueva: str
    aprobado: bool


def proponer(estado: EstadoDespliegue):
    print("nodo proponer: huella propuesta", estado["huella_nueva"])
    return {}


def supervisar(estado: EstadoDespliegue):
    decision = interrupt({
        "motivo": "aprobar nueva version de prompt en produccion",
        "huella_propuesta": estado["huella_nueva"],
    })
    return {"aprobado": decision}


def aplicar(estado: EstadoDespliegue):
    if estado["aprobado"]:
        print("version", estado["huella_nueva"], "activada")
    else:
        print("version", estado["huella_nueva"], "rechazada, se mantiene la anterior")
    return {}


grafo = StateGraph(EstadoDespliegue)
grafo.add_node("proponer", proponer)
grafo.add_node("supervisar", supervisar)
grafo.add_node("aplicar", aplicar)
grafo.add_edge(START, "proponer")
grafo.add_edge("proponer", "supervisar")
grafo.add_edge("supervisar", "aplicar")
grafo.add_edge("aplicar", END)

app_despliegue = grafo.compile(checkpointer=InMemorySaver())

# Huella de la versión actual del prompt, obtenida en el Paso 1 (se escribe como texto)
huella = "81542226d725"

# Camino de aprobación
config = {"configurable": {"thread_id": "chocolateria-despliegue-1"}}
resultado = app_despliegue.invoke({"huella_nueva": huella, "aprobado": False}, config=config)
print("1) tras invocar:", resultado)
print("   trae __interrupt__ (despliegue pendiente)?", "__interrupt__" in resultado)

snapshot = app_despliegue.get_state(config)
print("2) siguiente nodo:", snapshot.next)
print("   pendiente:", snapshot.interrupts[0].value)

resultado = app_despliegue.invoke(Command(resume=True), config=config)
print("3) tras aprobar:", resultado)

# Camino de rechazo (con otro thread_id, para no reusar un grafo ya resuelto)
print()
config2 = {"configurable": {"thread_id": "chocolateria-despliegue-2"}}
app_despliegue.invoke({"huella_nueva": huella, "aprobado": False}, config=config2)
resultado = app_despliegue.invoke(Command(resume=False), config=config2)
print("4) tras rechazar:", resultado)
