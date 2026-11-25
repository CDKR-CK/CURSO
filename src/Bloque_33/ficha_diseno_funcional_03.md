# Ficha de Diseño Funcional

## 1. Problema de negocio
El equipo de atención al cliente de una chocolatería en línea ficticia responde unas 80 consultas semanales (estimación) sobre despachos, devoluciones, alérgenos, conservación y precios buscando a mano en 8 fichas de políticas y productos. Cada consulta toma cerca de 6 minutos (estimación), unas 8 horas a la semana, y las respuestas varían según quién conteste. Una respuesta equivocada sobre trazas de maní puede dañar la salud de un cliente alérgico, y una promoción inventada obliga a vender bajo costo. Se espera que cualquier integrante del equipo obtenga una respuesta con su fuente en menos de un minuto, y que toda respuesta sobre alérgenos o promociones la revise una persona antes de enviarla.

## 2. Requerimientos y alcance (MVP)
### Requerimientos funcionales
- RF-01: El usuario envía una pregunta de texto a un endpoint de consulta y recibe una respuesta en JSON.
- RF-02: Cada respuesta cita al menos una fuente con su identificador de documento, por ejemplo [doc3].
- RF-03: El servicio informa el estado de un pedido por su número (CH-1001, CH-1002) usando datos simulados.
- RF-04: El servicio descarta los documentos con instrucciones inyectadas antes de generar la respuesta y, si no queda ninguno limpio, responde que no tiene información suficiente.
- RF-05: Una persona aprueba o rechaza la respuesta antes de enviarla cuando la pregunta trata de alérgenos o la respuesta menciona una promoción sin respaldo en las fuentes.
- RF-06: Una persona aprueba o rechaza un cambio de precio antes de que se reindexe el documento.
- RF-07: Una interfaz web muestra el historial de conversaciones de cada cliente.
- RF-08: El servicio consulta el sistema de pedidos y el inventario real de la tienda.
- RF-09: Los clientes hacen sus consultas por WhatsApp.
### Requerimientos no funcionales
- RNF-01: El endpoint de consulta responde en menos de 5 segundos en al menos 9 de cada 10 consultas de prueba.
- RNF-02: En los registros de las 10 consultas de prueba, incluida una con el correo ana.perez@example.com, ninguna línea contiene el texto de la pregunta ni de los documentos, solo longitudes, huellas y conteos.
- RNF-03: El servicio levanta desde cero en un contenedor, siguiendo el README, en menos de 10 minutos.
- RNF-04: Al menos 8 de las 9 preguntas con respuesta del conjunto de evaluación del Bloque 27 citan el documento correcto, y la pregunta sin respaldo (tienda física en Valparaíso) responde que no tiene información.
- RNF-05: En el 100 % de las consultas de prueba que recuperan los 2 documentos con inyección (comentario-ticket-881 y resena-web-042), esos documentos quedan fuera del prompt.
### Alcance
Imprescindible: RF-01, RF-02, RF-04, RF-05
Deseable: RF-03, RF-06
Fuera de alcance: RF-07 (no hay frontend en el programa), RF-08 (requiere sistemas y datos reales), RF-09 (requiere una cuenta y un canal real de mensajería)

## 3. Arquitectura de la solución
Diagrama: diagrama_arquitectura.md
- Modelo: Gemini mediante API (gemini-3.5-flash-lite para generar y gemini-embedding-001 para los embeddings), con la clave en el archivo .env.
- Vector store: Chroma persistido en la carpeta vectorstore/, con actualización incremental por id (doc1 a doc10).
- Orquestación: recuperación con k=3, filtro de inyección y generación con citas [docN]; aprobación humana de alérgenos y promociones con LangGraph.
- Exposición: servicio FastAPI con un endpoint de consulta (POST /consulta).
- Empaquetado: imagen Docker con la carpeta vectorstore/ montada como volumen y la clave leída desde .env.
- Registro: logs JSON con trace_id en la carpeta logs/, sin el texto de preguntas ni documentos.

Rótulos de las cajas del diagrama (iguales a los nombres del texto): Cliente, Servicio FastAPI, Orquestación, LangGraph (aprobación humana), Chroma, Gemini (API), Logs JSON, Contenedor Docker (frontera).

## 4. Criterios de aceptación
[PENDIENTE: se completa en el Bloque 34]

## 5. Plan de construcción por hitos
[PENDIENTE: se completa en el Bloque 34]
