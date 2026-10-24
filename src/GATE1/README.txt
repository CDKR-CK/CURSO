INSTALACION:

Instalar Python 3.15.0 - www.python.org

Crear entorno virtual: venv

Instalar modulos (recomendable usar PowerShell 7.6.7): pip install requests python-dotenv

Crear variable de ambient usando como ejemplo archivo ".env.example" para crear archivo ".env" que debe contener la API_KEY de google, obtenida desde Google AI Studio (https://aistudio.google.com/app/api-keys).

Python: ejecutar en consola o en VSC el archivo "main.py".


DESCRIPCIÓN DEL CÓDIGO:
El archivo "consumir_gemini.py" le hace una pregunta al modelo gemini-3.5-flash-lite de Google (API Interactions) usando la API_KEY del archivo ".env". Se le puede pasar una instrucción de sistema y un esquema para que la respuesta llegue en JSON estructurado. Muestra la respuesta, los tokens consumidos y el costo en US$; si algo falla, devuelve un mensaje de error en español en vez de caerse. El archivo "main.py" importa "solicita_respuesta" y "esquema_respuesta" desde "consumir_gemini.py" y muestra el resultado en consola.


VARIABLE Y FUNCIONES (consumir_gemini.py):

esquema_respuesta: esquema JSON que le dice al modelo cómo responder: "Respuesta" (texto), "Fuente" (texto) y "año" (número entero), los tres obligatorios.

armar_peticion(instruccion_sistema, pregunta, esquema=None): revisa que la instrucción y la pregunta sean texto y que la pregunta no venga vacía ni con solo números (si no, lanza ValueError). Arma la URL con la API_KEY y el body con el modelo y la pregunta; si viene instrucción de sistema la agrega, y si viene esquema pide la respuesta en JSON con ese esquema. Devuelve la URL y el body.

enviar_peticion(url, body): envía el POST y devuelve la respuesta como diccionario. Si algo falla (URL mal escrita, sin conexión, error 404, otro error HTTP o respuesta que no es JSON) lanza RuntimeError con un mensaje claro.

extraer_texto(datos): saca el texto generado por el modelo desde datos["steps"][-1]["content"][0]["text"]. Si no lo encuentra, lanza RuntimeError.

parsear_respuesta_json(texto, claves_requeridas): quita las marcas de Markdown (```json ... ```) si vienen, convierte el JSON a diccionario y revisa que tenga todas las claves obligatorias. Si el JSON no es válido o falta alguna clave, lanza ValueError.

calcular_costo(datos, precio_entrada, precio_salida): toma de datos["usage"] los tokens de entrada, salida y razonamiento y calcula el costo (entrada a US$ 0,30 por millón de tokens; salida y razonamiento a US$ 2,50 por millón). Devuelve una línea con los tokens y el costo, con punto para miles y coma para decimales.
https://ai.google.dev/gemini-api/docs/pricing?hl=es-419#gemini-3.5-flash-lite

obtener_dato_de_prueba(instruccion_sistema, pregunta): versión simple para pruebas; devuelve solo el texto del modelo, sin esquema ni costo. Si hay error, devuelve "Error: ...".

solicita_respuesta(instruccion_sistema, pregunta, esquema=None): función principal, la que usa "main.py". Llama a armar_peticion, enviar_peticion y extraer_texto; si viene esquema, pasa la respuesta por parsear_respuesta_json y la muestra con una línea "clave: valor" por campo. Devuelve la pregunta, la respuesta y el costo, o la pregunta y "Error: ..." si algo falló.

if __name__ == "__main__": solo corre si se ejecuta "consumir_gemini.py" directamente (no al importarlo desde "main.py"); hace una pregunta de prueba.





