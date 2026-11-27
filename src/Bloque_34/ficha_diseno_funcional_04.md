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
Diagrama: diagrama_arquitectura_01.png
- Modelo: Gemini mediante API (gemini-3.5-flash-lite para generar y gemini-embedding-001 para los embeddings), con la clave en el archivo .env.
- Vector store: Chroma persistido en la carpeta vectorstore/, con actualización incremental por id (doc1 a doc10).
- Orquestación: recuperación con k=3, filtro de inyección y generación con citas [docN]; aprobación humana de alérgenos y promociones con LangGraph.
- Exposición: servicio FastAPI con un endpoint de consulta (POST /consulta).
- Empaquetado: imagen Docker con la carpeta vectorstore/ montada como volumen y la clave leída desde .env.
- Registro: logs JSON con trace_id en la carpeta logs/, sin el texto de preguntas ni documentos.

Rótulos de las cajas del diagrama (iguales a los nombres del texto): Cliente, Servicio FastAPI, Orquestación, LangGraph (aprobación humana), Chroma, Gemini (API), Logs JSON, Contenedor Docker (frontera).

## 4. Criterios de aceptación
- CA-01 (RF-01): Al enviar POST /consulta con {"pregunta": "¿Cuánto demora un despacho a Santiago?"}, la respuesta tiene código 200 y es un JSON con los campos "respuesta" y "fuentes".
- CA-02 (RF-02): Para esa misma pregunta, "fuentes" contiene al menos un identificador con la forma [docN], con N entre 1 y 10, y ese identificador aparece citado en el texto de "respuesta".
- CA-03 (RF-01): Al enviar POST /consulta con {"pregunta": ""}, el servicio responde con código 422 y un mensaje de error en JSON, y la consulta siguiente de CA-01 vuelve a responder con código 200.
- CA-04 (RF-04): Con un índice de prueba que contiene solo comentario-ticket-881 y resena-web-042, la pregunta "¿Qué dicen los clientes del despacho?" recibe una respuesta que dice "no tengo información suficiente" y "fuentes" va vacía.
- CA-05 (RNF-05): En las 10 consultas de prueba, cada vez que la recuperación trae comentario-ticket-881 o resena-web-042, el registro de esa consulta los marca como descartados y ninguno de los 2 aparece en "fuentes" (100 % de los casos).
- CA-06 (RF-05): Ante la pregunta "¿El bombón de avellana tiene trazas de maní?", el servicio responde con "estado": "pendiente_aprobacion" y sin el texto de la respuesta, hasta que una persona la apruebe.
- CA-07 (RF-05): Si la persona rechaza la respuesta pendiente de CA-06, el estado final es "rechazada" y el cliente no recibe el texto generado.
- CA-08 (RNF-01): En las 10 consultas de prueba, al menos 9 responden en menos de 5 segundos.
- CA-09 (RNF-02): Tras ejecutar las 10 consultas de prueba, incluida una con el correo ana.perez@example.com, ninguna línea de la carpeta logs/ contiene "ana.perez@example.com" ni el texto completo de una pregunta.
- CA-10 (RNF-03): Siguiendo solo el README en un equipo limpio, el contenedor responde a la consulta de CA-01 a los 10 minutos o antes desde el inicio.
- CA-11 (RNF-04): Al ejecutar el conjunto de evaluación del Bloque 27, al menos 8 de las 9 preguntas con respuesta citan en "fuentes" el documento correcto.
- CA-12 (RNF-04): Ante la pregunta "¿Tienen tienda física en Valparaíso?", que ningún documento cubre, la respuesta dice que no tiene información y "fuentes" va vacía.

## 5. Plan de construcción por hitos
Horas disponibles: 12 h
Margen de imprevistos: 2,4 h
- H1 (1,5 h): Servicio FastAPI con POST /consulta que responde con fuentes [docN] desde Chroma. Cubre: RF-01, RF-02. Se comprueba con: CA-01, CA-02, CA-03.
- H2 (1,5 h): Filtro de inyección antes de generar, con descarte registrado en los logs. Cubre: RF-04, RNF-05. Se comprueba con: CA-04, CA-05.
- H3 (1,5 h): Aprobación humana con LangGraph para alérgenos y promociones sin respaldo. Cubre: RF-05. Se comprueba con: CA-06, CA-07.
- H4 (1,5 h): Servicio empaquetado en un contenedor Docker con vectorstore/ como volumen. Cubre: RNF-03. Se comprueba con: CA-10.
- H5 (3,6 h): Pruebas, documentación y ensayo de la defensa. Cubre: RNF-01, RNF-02, RNF-04. Se comprueba con: CA-08, CA-09, CA-11, CA-12.

Cálculo de horas: 12 h disponibles; margen de imprevistos 20 % (2,4 h, no se asigna); reserva de pruebas, documentación y defensa 30 % (3,6 h, hito H5); construcción 6 h (H1 a H4). Tope de los hitos: 12 h - 2,4 h = 9,6 h.
