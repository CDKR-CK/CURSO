# Límites de autonomía: asistente de atención al cliente de la chocolatería

Agente implementado en `z_mi_agente.py` (LangChain + Gemini, con memoria por
sesión). Este documento describe el agente tal como está construido y
ejecutado, respaldado por la traza real `z_trazas_agente.jsonl`: 10
interacciones del 09/11/2026, en dos ejecuciones de las mismas 5 entradas
(antes y después de la corrección descrita en "Revisión de trazas").

## Herramientas y nivel de riesgo

- buscar_en_politicas: bajo (solo lee las políticas de despacho,
  devoluciones, alérgenos y conservación; no modifica nada)

- consultar_estado_pedido: bajo (solo lee el estado y el contenido de un
  pedido; no modifica nada)

- calcular_total_compra: bajo (solo calcula un precio a partir del
  catálogo; no ejecuta ninguna acción externa ni registra una compra)

- generar_reembolso: alto (mueve dinero de forma irreversible y tiene
  impacto económico directo; requiere aprobación humana)

El agente no tiene herramientas de riesgo medio (escritura reversible).

## Herramientas que requieren aprobación humana

- generar_reembolso: un reembolso mal decidido, o con el pedido o el monto
  equivocados, no se puede deshacer y es una pérdida directa de dinero.
  Antes de ejecutarse llama a `esperar_aprobacion`, que muestra el pedido y
  el monto (por ejemplo, $9.900) y espera "s" por teclado durante 300
  segundos como máximo. Cualquier otra respuesta, o la falta de respuesta,
  se toma como rechazo (falla segura). Cada decisión se guarda con
  `registrar_aprobacion` y queda también en la traza, en el campo
  `aprobaciones`.

Las tres herramientas de riesgo bajo se ejecutan sin aprobación: pedir
confirmación para todo haría que quien aprueba deje de leer con atención.
Se controlan después, revisando la traza.

Limitaciones actuales, declaradas explícitamente:

- La aprobación se pide por consola; no existe todavía un panel de
  aprobaciones separado.
- `registro_aprobaciones` vive en memoria y se pierde al cerrar el
  programa; la copia persistente es la que queda en la traza.
- El reembolso es simulado: la herramienta devuelve el texto de
  confirmación, pero no está conectada a un sistema de pagos real.

## Revisión de trazas

- Frecuencia: cada semana, una muestra de las interacciones de riesgo bajo
  (las primeras 5 y las últimas 5 de la semana), más el 100 % de las
  interacciones donde se usó `generar_reembolso`, sin muestreo.

- Qué se busca:
  - La misma herramienta invocada varias veces seguidas con argumentos
    parecidos (el agente no avanza o reintenta sin necesidad). Primera
    pasada automática con `marcar_repeticiones_sospechosas`.
  - Un `generar_reembolso` sin su registro de aprobación: cada acción de
    reembolso en `acciones` debe tener su entrada en `aprobaciones`. Si
    falta, el flujo de supervisión no está funcionando.
  - Una respuesta final que no coincide con ninguna observación (el agente
    afirma algo que ninguna herramienta le devolvió).

- Verificación de que la traza existe y cubre el riesgo alto:
  `wc -l z_trazas_agente.jsonl` → 10;
  `grep -c '"herramienta": "generar_reembolso"' z_trazas_agente.jsonl` → 4
  (2 aprobados y 2 rechazados, todos con su registro en `aprobaciones`).

- Hallazgo real de la traza del 09/11/2026 (línea 4, sesión `cliente_02`):
  el reembolso de $9.900 fue aprobado y la herramienta respondió "Reembolso
  de $9.900 generado para el pedido CH-1002", pero la respuesta final del
  agente dijo "Queda pendiente de aprobación humana para completarse". Era
  una respuesta que no coincidía con la observación.

- Corrección aplicada (paso 3 del plan): se agregó al prompt del sistema
  que la respuesta final debe basarse solo en lo que devolvieron las
  herramientas, sin agregar estados ni pasos pendientes que la herramienta
  no informó. Al ejecutar de nuevo las mismas entradas (paso 4), la línea
  9 de la traza muestra la respuesta correcta: "El reembolso de $9.900 ha
  sido generado para el pedido CH-1002." Las demás respuestas siguen
  coincidiendo con sus observaciones.

## Qué hacer ante un comportamiento inesperado

1. Si involucra `generar_reembolso`: quitarla de la lista `herramientas`
   en `z_mi_agente.py` hasta resolver el problema; los reembolsos de ese
   período se procesan a mano.
2. Buscar en `z_trazas_agente.jsonl` las líneas de esa sesión
   (`session_id`) y comparar `entrada`, `acciones`, `aprobaciones` y
   `respuesta_final` para ubicar en qué paso se desvió.
3. Corregir según la causa:
   - Herramienta equivocada: ajustar el docstring (la descripción) de las
     herramientas involucradas.
   - Argumentos equivocados (pedido o monto): reforzar la validación dentro
     de la herramienta o su `args_schema`.
   - Respuesta final que contradice la observación (caso `cliente_02`):
     agregar al prompt del sistema que la respuesta debe basarse solo en lo
     que devolvió la herramienta, sin agregar estados que la herramienta no
     informó.
4. Ejecutar de nuevo las mismas entradas y confirmar en la traza nueva que
   el comportamiento quedó corregido.
5. Reactivar la herramienta, si se había quitado, y actualizar este
   documento con el cambio y la fecha.
