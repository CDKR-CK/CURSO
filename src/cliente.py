# pip install requests python-dotenv
# Usa cliente_api.py

from cliente_api import consultar_modelo

respuesta = consultar_modelo("Hola, que modelo eres?")
print(respuesta)
