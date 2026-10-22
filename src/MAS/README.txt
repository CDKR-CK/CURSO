Inatalación:

Instalar Python 3.15.0 - www.python.org/

Crear entorno virtual.

Instalar modulos (recomendable usar PowerShell 7.6.7): pip install python-dotenv

Crear variable de ambient usando como ejemplo archivo ".env.example" para crear archivo ".env" que debe contener la API_KEY de google obtenida desde Google AI Studio (https://aistudio.google.com/app/api-keys).

Python: ejecutar en consola o en VSC la ultima versión del codigo llamada "consumir_gemini_DEF_TRY_COSTO.py"

Descripción del código:
Al ejecutarse por ejemplo la linea "print(obtener_dato_con_costo("Hola. Que modelo eres?"))", la función valida el texto ingresado, arma una solicitud HTTP hacia la API de Gemini, la envía mediante un POST, extrae la respuesta generada por el modelo, calcula el costo total consumido en dólares según los tokens reportados y devuelve ambos valores formateados para imprimirlos en consola; si ocurre un fallo en cualquier etapa, captura la excepción y devuelve un mensaje de error legible.   





