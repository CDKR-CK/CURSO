# pip install: no requiere módulos externos (solo librería estándar)
#
# 📊 Paso 3 (Bloque 32): matriz de riesgos de la Chocolatería (RAG de atención al cliente).
# Calcula puntaje = probabilidad × impacto, categoría, filas al límite y verifica
# que todo riesgo ALTO o CRITICO tenga un punto de supervisión humana asociado.
# Ejecutar: python Paso_03_matriz_riesgos_01.py


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


# "supervision" se documenta junto a la fila (no entra en el cálculo); vacío = no corresponde
mis_riesgos = [
    {"riesgo": "Inyección de prompt vía reseña o comentario de ticket indexado",
     "probabilidad": 4,   # el corpus ya trae 2 textos de terceros con inyeccion
     "impacto": 4,        # revela instrucciones o inventa ofertas ("trufas gratis")
     "mitigacion": "Filtro de patrones + delimitacion <contexto> (Bloque 31)",
     "supervision": "Documento marcado por el filtro frena la respuesta y pasa a revision humana"},
    {"riesgo": "Precio o promoción inventada en la respuesta (ej. caja de trufas gratis)",
     "probabilidad": 3,   # el modelo puede completar con datos que no estan en el contexto
     "impacto": 4,        # obliga a respetar un precio falso o daña la confianza
     "mitigacion": "Prompt: responder solo con contexto y citar fuente [docN] (Bloque 31)",
     "supervision": "Respuesta que menciona descuento o 'gratis' sin fuente pasa a revision"},
    {"riesgo": "Respuesta omite trazas de maní y frutos secos a cliente alérgico",
     "probabilidad": 2,   # doc3 existe, pero puede no recuperarse en el top-k
     "impacto": 5,        # riesgo para la salud del cliente
     "mitigacion": "Documento de alergenos indexado + cita obligatoria de fuente (Bloque 31)",
     "supervision": "Preguntas sobre alergenos se derivan a una persona antes de responder"},
    {"riesgo": "Precio desactualizado por chunk no reindexado tras cambio de precio",
     "probabilidad": 3,   # los precios cambian varias veces al año
     "impacto": 3,        # diferencia de precio con la boleta
     "mitigacion": "Actualizacion incremental del indice con ids explicitos doc7-doc10 (Bloque 25)",
     "supervision": "Cambio de precio aprobado por una persona antes de reindexar"},
    {"riesgo": "Pregunta o datos del pedido (CH-1001) guardados en logs sin redactar",
     "probabilidad": 2,   # los logs ya registran huella y longitud
     "impacto": 4,        # expone datos de clientes
     "mitigacion": "Registrar huella/longitud en vez de contenido (Bloque 31)",
     "supervision": ""},
    {"riesgo": "Modelo de embeddings queda deprecado sin aviso",
     "probabilidad": 2,   # ya ocurrio con text-embedding-004
     "impacto": 3,        # hay que reindexar todo el corpus
     "mitigacion": "Migrado a gemini-embedding-001 + revision periodica de la documentacion (Bloque 28)",
     "supervision": ""},
    {"riesgo": "Versión nueva del prompt cambia el tono de las respuestas sin aviso",
     "probabilidad": 1,   # todo cambio queda registrado con huella y nota
     "impacto": 3,        # molesta al cliente, no genera perdida directa
     "mitigacion": "RegistroDePrompts con huella + diff antes de desplegar (Bloque 32)",
     "supervision": ""},
]

for r in mis_riesgos:
    r["puntaje"] = puntaje_riesgo(r["probabilidad"], r["impacto"])
    r["categoria"] = categoria_riesgo(r["puntaje"])
    r["al_limite"] = esta_en_el_limite(r["probabilidad"], r["impacto"])


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")   # para mostrar ✅ y ❌ en cualquier consola

    # Matriz ordenada por puntaje
    for r in sorted(mis_riesgos, key=lambda x: -x["puntaje"]):
        marca = "[AL LIMITE]" if r["al_limite"] else ""
        print(f"{r['categoria']:8} ({r['puntaje']:2}) - {r['riesgo']} {marca}")

    # Filas a revisar con otra persona
    print()
    for r in mis_riesgos:
        if r["al_limite"]:
            print("revisar con otra persona:", r["riesgo"])

    # Verificaciones de la actividad
    print()
    severos = [r for r in mis_riesgos if r["categoria"] in ("CRITICO", "ALTO")]
    sin_supervision = [r["riesgo"] for r in severos if not r["supervision"]]
    con_bloque = [r for r in mis_riesgos if "(Bloque" in r["mitigacion"]]
    categorias = {r["categoria"] for r in mis_riesgos}

    print("✅" if len(mis_riesgos) >= 5 else "❌", "al menos 5 riesgos:", len(mis_riesgos))
    print("✅" if severos else "❌", "al menos un CRITICO o ALTO:", len(severos))
    print("✅" if not sin_supervision else "❌",
          "todo ALTO/CRITICO tiene punto de supervision", sin_supervision or "")
    print("✅" if len(con_bloque) >= 2 else "❌",
          "mitigaciones con numero de bloque:", len(con_bloque))
    print("✅" if len(categorias) > 1 else "❌",
          "no todo en la misma categoria:", sorted(categorias))

    # Puntos de supervisión de los riesgos ALTO y CRITICO
    print()
    for r in sorted(severos, key=lambda x: -x["puntaje"]):
        print(f"{r['categoria']:8} -> {r['supervision']}")
