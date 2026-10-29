from Funciones_04 import consultar_modelo
from pipeline_texto import procesar_texto

print("CASO 1:")
consulta = "¿Qué es Python?"

referencia = "Python es un lenguaje de programación interpretado."
crudo_ref = referencia.split()

respuesta = consultar_modelo(consulta, "Responde con un maximo de 10 palabras", mostrar_costo=False)
print(respuesta)
crudo_resp = respuesta.split()
print(crudo_resp)

comunes_crudo = set(crudo_ref) & set(crudo_resp)
print(comunes_crudo)

pct_crudo = len(comunes_crudo) / len(set(crudo_ref))
print(f"[Caso 1] Coincidencia texto crudo: {pct_crudo:.1%}")

tokens_ref = procesar_texto(referencia)
tokens_resp = procesar_texto(respuesta)
print(tokens_ref)
print(tokens_resp)

comunes = set(tokens_ref) & set(tokens_resp)
print(comunes)

pct_proc = len(comunes) / len(set(tokens_ref))
print(f"[Caso 1] Coincidencia texto procesado: {pct_proc:.1%}")


print("CASO 2:")

consulta = "¿Cuál es la capital de Chile?"

referencia = "Santiago."
crudo_ref = referencia.split()

respuesta = consultar_modelo(consulta, "Responde con un maximo de 10 palabras", mostrar_costo=False)
print(respuesta)
crudo_resp = respuesta.split()
print(crudo_resp)

comunes_crudo = set(crudo_ref) & set(crudo_resp)
print(comunes_crudo)

pct_crudo = len(comunes_crudo) / len(set(crudo_ref))
print(f"[Caso 2] Coincidencia texto crudo: {pct_crudo:.1%}")

tokens_ref = procesar_texto(referencia)
tokens_resp = procesar_texto(respuesta)
print(tokens_ref)
print(tokens_resp)

comunes = set(tokens_ref) & set(tokens_resp)
print(comunes)

pct_proc = len(comunes) / len(set(tokens_ref))
print(f"[Caso 2] Coincidencia texto procesado: {pct_proc:.1%}")

print("CASO 3:")

consulta = "¿Qué océano tiene Chile?"

referencia = "El océano Pacífico."
crudo_ref = referencia.split()

respuesta = consultar_modelo(consulta, "Responde con un maximo de 10 palabras", mostrar_costo=False)
print(respuesta)
crudo_resp = respuesta.split()
print(crudo_resp)

comunes_crudo = set(crudo_ref) & set(crudo_resp)
print(comunes_crudo)

pct_crudo = len(comunes_crudo) / len(set(crudo_ref))
print(f"[Caso 3] Coincidencia texto crudo: {pct_crudo:.1%}")

tokens_ref = procesar_texto(referencia)
tokens_resp = procesar_texto(respuesta)
print(tokens_ref)
print(tokens_resp)

comunes = set(tokens_ref) & set(tokens_resp)
print(comunes)

pct_proc = len(comunes) / len(set(tokens_ref))
print(f"[Caso 3] Coincidencia texto procesado: {pct_proc:.1%}")

print("CASO 4:")

consulta = "¿Cuántos lados tiene un hexágono?"

referencia = "Seis."
crudo_ref = referencia.split()

respuesta = consultar_modelo(consulta, "Responde con un maximo de 10 palabras", mostrar_costo=False)
print(respuesta)
crudo_resp = respuesta.split()
print(crudo_resp)

comunes_crudo = set(crudo_ref) & set(crudo_resp)
print(comunes_crudo)

pct_crudo = len(comunes_crudo) / len(set(crudo_ref))
print(f"[Caso 4] Coincidencia texto crudo: {pct_crudo:.1%}")

tokens_ref = procesar_texto(referencia)
tokens_resp = procesar_texto(respuesta)
print(tokens_ref)
print(tokens_resp)

comunes = set(tokens_ref) & set(tokens_resp)
print(comunes)

pct_proc = len(comunes) / len(set(tokens_ref))
print(f"[Caso 4] Coincidencia texto procesado: {pct_proc:.1%}")
