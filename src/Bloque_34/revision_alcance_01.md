# Revisión del alcance
Revisor: CK (autorrevisión)
Fecha: 26/11/2026

- Hallazgo 1 (criterio 4): En la primera redacción, CA-04 pedía que todos los documentos recuperados tuvieran inyección, pero no decía cómo provocar ese caso: otra persona no podía reproducirlo.
  Decisión: aceptado. Cambio: CA-04 ahora se ejecuta con un índice de prueba que contiene solo comentario-ticket-881 y resena-web-042, con una pregunta concreta y el texto esperado "no tengo información suficiente".

- Hallazgo 2 (criterio 5): El plan suma exactamente el tope de 9,6 h y H3 (aprobación humana con LangGraph) es la pieza menos practicada; no queda holgura dentro de los hitos.
  Decisión: rechazado. Motivo: el margen de 2,4 h existe justamente para ese riesgo, y H3 reutiliza el grafo de aprobación ya construido en el GATE 2 (Bloque 32).

- Hallazgo 3 (criterio 2): RF-03 (estado del pedido CH-1001 con datos simulados) es deseable y no tiene hito; es barato de construir y luce en la defensa.
  Decisión: aplazado. Se vuelve a evaluar al terminar H4, solo si H1 a H4 se cerraron con horas sobrantes de construcción, sin tocar el margen.

Acierto: los criterios de los RNF reutilizan las cifras ya escritas en la sección 2 (5 segundos, 9 de 10, 10 minutos, 8 de 9, 100 %), así que no hay que reinterpretar nada.
