# pip install requests python-dotenv
# Hace una pregunta al modelo usando las funciones de Funciones_04.py y muestra el costo total de la sesión.

import Funciones_04 as TODO
from Funciones_04 import consultar_modelo, esquema_respuesta

print(consultar_modelo("Hola. Que modelo eres?", "Responde con un maximo de 10 palabras, al finalizar escribe FIN!", esquema_respuesta))
print(consultar_modelo("Hola. Que modelo eres?", "Responde con un maximo de 10 palabras"))  # sin esquema
print(consultar_modelo("Hola. Que modelo eres?"))  # sin instrucción ni esquema

# Se lee desde el módulo (funciones.costo_total_sesion) porque consultar_modelo lo actualiza allí.
print(f"Costo total de la sesión: US$ {TODO.formatear_usd(TODO.costo_total_sesion)}")







