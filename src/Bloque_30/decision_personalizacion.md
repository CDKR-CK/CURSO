# Decisión de personalización: clasificador de mensajes de la Chocolatería
 
## 1. El problema
El clasificador de mensajes de la Chocolatería (Bloque 29) no devuelve siempre el JSON `{"intencion": ..., "prioridad": ...}` con valores de la lista permitida: de 20 respuestas revisadas, 6 (30 %) fallan (texto extra antes del JSON, intenciones inventadas como `"devolucion"` o prioridades fuera de la escala como `"urgente"`). El modelo entiende el mensaje del cliente; lo que falla es la consistencia de la salida.

## 2. Resultado del método de decisión
Respuestas, cada una con la evidencia que la sustenta (umbrales del curso):

| Clave | Respuesta | Evidencia |
| --- | --- | --- |
| `informacion_cambia_seguido` | False | 0 cambios en la taxonomía (6 intenciones, 3 prioridades) en los últimos 3 meses. |
| `problema_de_formato_o_tono` | True | 6 de 20 respuestas fallan (30 %, umbral 15 %). |
| `dataset_grande_y_de_calidad` | False | 18 ejemplos etiquetados (umbral 200), 0 contradicciones y 0 problemas en el validador. |
| `presupuesto_limitado_o_iterar_rapido` | True | Puedo pagar como máximo 2 intentos de entrenamiento (en el Bloque 29 el envío quedó desactivado por costo). |
| `necesita_multiples_variantes` | False | 1 solo clasificador para todos los canales. |

Puntaje:
- PEFT: 3 puntos
- RAG: 2 puntos
- Fine-tuning completo: 1 punto

**Ganador claro: PEFT** (no hay empate).

## 3. Técnica elegida y por qué
Elijo **PEFT** (`TUNING_MODE_PEFT_ADAPTER` con `ADAPTER_SIZE_FOUR`), porque el problema es de comportamiento (formato y valores permitidos), no de conocimiento, y un adapter chico aprende ese formato con pocos ejemplos y a un costo que cabe en 2 intentos de entrenamiento. Descarto RAG para el clasificador: sus 2 puntos vienen solo del presupuesto limitado, y al clasificador no le falta información que cambie (precios, stock y políticas ya los resuelve el RAG de los Bloques 24 a 28). Descarto fine-tuning completo porque con 18 ejemplos sobreajustaría y cada intento cuesta más cómputo y tiempo.

Sensibilidad: la respuesta en que más dudé es `problema_de_formato_o_tono`, porque la medición de 30 % viene de una sola muestra de 20 respuestas. Si fuera False, el puntaje pasa a RAG 2, PEFT 1, fine-tuning completo 0: sin un problema de formato real, no se justifica entrenar nada y basta con mejorar el prompt. Por eso, antes de enviar el trabajo, repito la medición con 20 respuestas nuevas. Las respuestas sobre dataset, presupuesto y variantes no cambian el ganador.

## 4. Qué necesitaría para ejecutarla
- Hoy tengo **18 ejemplos** etiquetados y validados (3 por intención, 6 intenciones).
- Meta: **120 ejemplos** (20 por intención), así que me faltan **102 ejemplos**.
- Costo de etiquetarlos a 5 minutos por ejemplo, con segunda revisión de 2 minutos sobre el 20 % (20,4 ejemplos), a US$ 14 por hora:
  - Etiquetado base: 8,50 horas, aprox US$ 119,00.
  - Segunda revisión: 0,68 horas, aprox US$ 9,52.
  - **Total: 9,18 horas, aprox US$ 128,52 (1,1 jornadas de 8 horas).**
- Balance de prioridades: hoy es baja 8, media 5, alta 5 (razón 1,6x). En los 102 nuevos ejemplos debo agregar más casos de prioridad "alta" y "media" para dejar la razón máx/mín bajo 1,5x.
- Presupuesto de cómputo: 2 intentos de entrenamiento como máximo. Antes de cada envío, el dataset debe pasar el validador del Bloque 29 con 0 problemas, y después reviso que `total_truncated_example_count` sea 0.
- Métrica de éxito: en una nueva muestra de 20 respuestas, menos de 3 fallas de formato (bajo el 15 %).
- No necesito un corpus para indexar, porque no uso RAG para esta tarea.
