import os
 
RUTA = "docs/ficha_diseno_funcional.md"
 
ESQUELETO = """# Ficha de Diseño Funcional
 
## 1. Problema de negocio
[COMPLETAR: quién tiene el problema, qué pasa hoy, cuánto cuesta
(estimación) y qué resultado se espera. Sin nombrar la solución.]
 
## 2. Requerimientos y alcance (MVP)
### Requerimientos funcionales
- RF-01: [COMPLETAR: algo que el sistema hace y se puede observar]
### Requerimientos no funcionales
- RNF-01: [COMPLETAR: qué tan bien lo hace, con un número]
### Alcance
Imprescindible: [COMPLETAR: ids de los RF que forman el MVP]
Deseable: [COMPLETAR: ids de los RF que solo entran si sobra tiempo]
Fuera de alcance: [COMPLETAR: ids de los RF descartados, con motivo]
 
## 3. Arquitectura de la solución
[COMPLETAR: referencia al diagrama (por ejemplo,
docs/diagrama_arquitectura.png) y una frase por cada decisión: modelo,
vector store, orquestación, exposición y empaquetado.]
 
## 4. Criterios de aceptación
[PENDIENTE: se completa en el Bloque 34]
 
## 5. Plan de construcción por hitos
[PENDIENTE: se completa en el Bloque 34]
"""
 
if os.path.exists(RUTA):
	raise SystemExit(
    	f"{RUTA} ya existe: no se sobrescribe para no perder tu trabajo."
	)
os.makedirs("docs", exist_ok=True)
with open(RUTA, "w", encoding="utf-8") as archivo:
	archivo.write(ESQUELETO)
print("Ficha creada en", RUTA)
