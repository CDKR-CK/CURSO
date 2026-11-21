def puntaje_riesgo(probabilidad, impacto):
    return probabilidad * impacto
 
def categoria_riesgo(puntaje):
    if puntaje >= 15:
        return "CRITICO"
    if puntaje >= 9:
        return "ALTO"
    if puntaje >= 4:
        return "MEDIO"
    return "BAJO"


riesgos = [
    {"riesgo": "Inyeccion de prompt via documento recuperado",
    "probabilidad": 4, "impacto": 4,
    "mitigacion": "Filtro de patrones + delimitacion de contexto (Bloque 31)"},
    {"riesgo": "Filtracion de PII en logs sin redactar",
    "probabilidad": 3, "impacto": 5,
    "mitigacion": "Registrar huella/longitud en vez de contenido (Bloque 31)"},
    {"riesgo": "Dataset de tuning desbalanceado produce sesgo",
    "probabilidad": 3, "impacto": 3,
    "mitigacion": "Chequeo de balance por categoria antes de enviar (Bloque 29)"},
    {"riesgo": "Modelo de embeddings usado queda deprecado sin aviso",
    "probabilidad": 2, "impacto": 4,
    "mitigacion": "Revision periodica de la documentacion oficial (Bloque 28)"},
    {"riesgo": "Respuesta con informacion vieja por chunk no reindexado",
    "probabilidad": 3, "impacto": 2,
    "mitigacion": "Actualizacion incremental del indice con ids explicitos (Bloque 25)"},
]
 
for r in riesgos:
    r["puntaje"] = puntaje_riesgo(r["probabilidad"], r["impacto"])
    r["categoria"] = categoria_riesgo(r["puntaje"])
 
for r in sorted(riesgos, key=lambda x: -x["puntaje"]):
    print(f"{r['categoria']:8} ({r['puntaje']:2}) - {r['riesgo']}")

print("\n")

def esta_en_el_limite(probabilidad, impacto):
    categoria_actual = categoria_riesgo(puntaje_riesgo(probabilidad, impacto))
    vecinos = [
        (probabilidad + 1, impacto), (probabilidad - 1, impacto),
        (probabilidad, impacto + 1), (probabilidad, impacto - 1),
    ]
    for p2, i2 in vecinos:
        if not (1 <= p2 <= 5 and 1 <= i2 <= 5):
            continue
        if categoria_riesgo(puntaje_riesgo(p2, i2)) != categoria_actual:
            return True
    return False
 
for r in riesgos:
    r["al_limite"] = esta_en_el_limite(r["probabilidad"], r["impacto"])
 
for r in sorted(riesgos, key=lambda x: -x["puntaje"]):
    marca = "[AL LIMITE]" if r["al_limite"] else ""
    print(f"{r['categoria']:8} ({r['puntaje']:2}) - {r['riesgo']} {marca}")
 
# riesgo de contraste, deliberadamente lejos de cualquier limite
print("\n")
print("riesgo de contraste (probabilidad=1, impacto=1):",
    "AL LIMITE" if esta_en_el_limite(1, 1) else "no al limite",
    "- puntaje", puntaje_riesgo(1, 1), categoria_riesgo(puntaje_riesgo(1, 1)))

