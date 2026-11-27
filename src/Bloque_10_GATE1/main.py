# pip install requests python-dotenv

from consumir_gemini import solicita_respuesta, esquema_respuesta

print(solicita_respuesta("Responde con un maximo de 10 palabras, al finalizar escribe FIN!", "Hola. Que modelo eres?", esquema_respuesta))
print(solicita_respuesta("Responde con un maximo de 10 palabras, al finalizar escribe FIN!", "Que sabes de la Luna?", esquema_respuesta))
print(solicita_respuesta("Responde con un maximo de 10 palabras, al finalizar escribe FIN!", "Capitales en Sudamérica?", esquema_respuesta))
print(solicita_respuesta("Responde con un maximo de 10 palabras, al finalizar escribe FIN!", "¿Cuándo murió Julio César?", esquema_respuesta))
print(solicita_respuesta("Responde con un maximo de 10 palabras, al finalizar escribe FIN!", "¿Cuánto es 7 por 8?", esquema_respuesta))
print(solicita_respuesta("Responde con un maximo de 10 palabras, al finalizar escribe FIN!", "¿qué día es hoy?", esquema_respuesta))

# errores TRY
print(solicita_respuesta("Responde con un maximo de 10 palabras, al finalizar escribe FIN!", "", esquema_respuesta))
print(solicita_respuesta("Responde con un maximo de 10 palabras, al finalizar escribe FIN!", "123", esquema_respuesta))
print(solicita_respuesta("Responde con un maximo de 10 palabras, al finalizar escribe FIN!", 42, esquema_respuesta))
print(solicita_respuesta(None, "Hola", esquema_respuesta))


