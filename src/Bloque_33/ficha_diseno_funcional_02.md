# Ficha de Diseño Funcional
 
## 1. Problema de negocio
El equipo de soporte de una tienda en línea ficticia responde unas 60 consultas semanales (estimación) sobre devoluciones y envíos buscando a mano en un PDF de 40 páginas. Cada consulta toma cerca de 8 minutos y las respuestas varían según quién conteste. Se espera que cualquier integrante del equipo obtenga una respuesta con su fuente en menos de un minuto.
 
## 2. Requerimientos y alcance (MVP)
### Requerimientos funcionales
- RF-01: El usuario envía una pregunta de texto a un endpoint de consulta y recibe una respuesta en JSON.
- RF-02: Cada respuesta incluye al menos una fuente citada con el nombre del documento.
- RF-03: El servicio consulta el estado de un envío por número de pedido usando datos simulados.
- RF-04: Una persona aprueba o rechaza antes de que se genere un reembolso.
- RF-05: Una interfaz web muestra el historial de conversaciones.
- RF-06: El servicio consulta el sistema de pedidos real de la empresa.
### Requerimientos no funcionales
- RNF-01: El endpoint de consulta responde en menos de 5 segundos en al menos 9 de cada 10 consultas de prueba.
- RNF-02: En los registros de las 10 consultas de prueba, ninguna línea contiene el texto completo de la pregunta ni de los documentos, solo longitudes y conteos.
- RNF-03: El servicio levanta desde cero en un contenedor, siguiendo el README, en menos de 10 minutos.
### Alcance
Imprescindible: RF-01, RF-02, RF-03
Deseable: RF-04
Fuera de alcance: RF-05 (no hay frontend en el programa), RF-06 (requiere sistemas y datos reales)
 
## 3. Arquitectura de la solución
Diagrama: docs/diagrama_arquitectura.png
- Modelo: Gemini mediante API, con la clave en el archivo .env.
- Vector store: Chroma persistido en la carpeta indice/.
- Orquestación: recuperación, filtro de inyección y generación con citas; aprobación humana con LangGraph.
- Exposición: servicio FastAPI con un endpoint de consulta.
- Empaquetado: imagen Docker con el índice montado como volumen.
 
## 4. Criterios de aceptación
[PENDIENTE: se completa en el Bloque 34]
 
## 5. Plan de construcción por hitos
[PENDIENTE: se completa en el Bloque 34]
