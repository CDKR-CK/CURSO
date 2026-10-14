# se debe instalar pip install python-dotenv

from dotenv import load_dotenv # se importa solo lo que se necesita
import os # para acceder a la variable de entorno

load_dotenv()

print(os.getenv("API_KEY") is not None)


