# Decisión de arquitectura: elección de modelo
  
## Modelo elegido:
gemini-3.5-flash-lite
  
## Diagrama de arquitectura:
El diagrama está en un archivo JPG llamado consumir_gemini_DEF_TRY_COSTO_DIAGRAMA.jpg
Este diagrama fue realizado según lo descrito en la actividad del bloque 8, codigo consumir_gemini_DEF_TRY.py
  
## Comparación de candidatos:
Ver tabla en archivo Excel: Desicion-Tabla.
Nota: hice 2 consultas por modelos solamente para no agotar la API con tantas consultas, Obviamente siempre es mejor hacer más.

## Justificación:
Por la simplicidad de la pregunta, el bajo costo logrado y por entregar una respuesta correcta, me quedo con el modelo gemini-3.5-flash-lite.
Si los requerimientos de la aplicación cambian, el modelo puede cambiar. 
  
## Alternativa descartada y por qué:
Se descarta el modelo que no responde inicialmente, que es gemini-3.8-live.

Luego se verifica que la respuesta sea correctas. Los tres modelos siguientes cumplen esto:
* gemini-3.5-flash-lite
* gemini-3.8-flash
* gemini-3.6-flash

Luego se verifica el costo más económico, que es el modelo gemini-3.5-flash-lite.