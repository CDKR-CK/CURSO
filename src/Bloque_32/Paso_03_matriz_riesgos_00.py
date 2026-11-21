# 📊 Paso 3: completa tu matriz de riesgos con al menos cinco filas


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
 
mis_riesgos = [
    # Fila modelo: quita los # para ver el resultado y luego reemplaza la fila por un riesgo de tu proyecto.
    # {"riesgo": "Inyeccion de prompt via comentario de usuario indexado",
    #  "probabilidad": 4,   # 1 a 5: probable, con la informacion que tienes hoy
    #  "impacto": 4,        # 1 a 5: expone instrucciones internas y datos de clientes
    #  "mitigacion": "Filtro de patrones + delimitacion de contexto (Bloque 31)"},
    # Tus otras filas aqui, con la misma estructura (cinco como minimo)
]
 
for r in mis_riesgos:
    r["puntaje"] = puntaje_riesgo(r["probabilidad"], r["impacto"])
    r["categoria"] = categoria_riesgo(r["puntaje"])
 
for r in sorted(mis_riesgos, key=lambda x: -x["puntaje"]):
    print(f"{r['categoria']:8} ({r['puntaje']:2}) - {r['riesgo']}")


