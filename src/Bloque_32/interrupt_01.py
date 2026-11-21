from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
 
class Estado(TypedDict):
    version_nueva: str
    aprobado: bool
 
def proponer_version(estado: Estado):
    print("nodo: proponer_version, version propuesta:", estado["version_nueva"])
    return {}
 
def punto_de_supervision(estado: Estado):
    decision = interrupt({
        "motivo": "aprobar despliegue de nueva version de prompt a produccion",
        "version_propuesta": estado["version_nueva"],
    })
    return {"aprobado": decision}
 
def desplegar(estado: Estado):
    print("nodo: desplegar. aprobado =", estado["aprobado"])
    if estado["aprobado"]:
        print("  -> version", estado["version_nueva"], "desplegada a produccion")
    else:
        print("  -> despliegue RECHAZADO, version anterior se mantiene")
    return {}
 
grafo = StateGraph(Estado)
grafo.add_node("proponer_version", proponer_version)
grafo.add_node("punto_de_supervision", punto_de_supervision)
grafo.add_node("desplegar", desplegar)
grafo.add_edge(START, "proponer_version")
grafo.add_edge("proponer_version", "punto_de_supervision")
grafo.add_edge("punto_de_supervision", "desplegar")
grafo.add_edge("desplegar", END)
 
app = grafo.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "despliegue-1"}}
 
resultado = app.invoke({"version_nueva": "v3", "aprobado": False}, config=config)
print("estado tras primera corrida (interrumpido):")
print(resultado)


print("reanudando con aprobacion humana = True") # un humano debe dar esta aprobacion
resultado2 = app.invoke(Command(resume=True), config=config)
print("estado final:", resultado2)


