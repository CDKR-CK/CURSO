# Límites de la métrica de evaluación


## Qué mide

Coincidencia entre frases revisando palabras y la cantidad de ocurrencias,
después de pasar a minúsculas y quitar la puntuación.
Calcula precisión, cobertura y F1.


## Modos de falla conocidos

- Las variaciones de una misma palabra no coinciden, aunque la respuesta
  sea correcta ("funciones" no coincide con "función").
```
F1("La palabra def sirve para definir una función.","Sirve para definir y crear funciones nuevas.")=0.40
```
- Sinónimos y paráfrasis correctas puntúan bajo ("mostrar texto o datos"
  no coincide con "muestra información").
```
F1("La función print muestra información en la pantalla.","Para mostrar texto o datos en la pantalla.")=0.38
```
- Un F1 bajo no distingue una respuesta correcta de una deficiente: la
  respuesta genérica e incompleta sobre el bucle for puntúa casi igual que
  la respuesta correcta sobre def (0.40).
```
F1("Un bucle for recorre los elementos de una secuencia.","Una estructura para repetir un bloque de código.")=0.35
```
- Datos incorrectos (fechas, cifras) pueden puntuar alto si el resto de la
  oración coincide. No apareció en la muestra.
```
F1("Python fue creado en 1991.","Python fue creado en 1989.")=0.80
```
- Negaciones ausentes casi no bajan el puntaje, aunque inviertan el
  significado. No apareció en la muestra.
```
F1("Python no es un lenguaje compilado.","Python es un lenguaje compilado.")=0.91
```


## Muestra revisada

10 casos: los 5 con mayor F1 y los 5 con menor F1, sobre 20 respuestas
de resultados_metricas.json, calificados con la rúbrica de tres preguntas
(corrección factual, completitud, contradicción).

**Los 5 mejores**

- **Pregunta:** ¿Quién creó Python? (F1 = 1,00)
  - Referencia: "Python fue creado por Guido van Rossum."
  - Respuesta: "Python fue creado por Guido van Rossum."
  - Rúbrica: corrección factual sí, completitud sí, contradicción no.
  - Comentario: la respuesta repite la referencia palabra por palabra; el
    F1 perfecto es merecido.
- **Pregunta:** ¿Qué es un módulo en Python? (F1 = 0,80)
  - Referencia: "Un módulo es un archivo con código Python reutilizable."
  - Respuesta: "Un archivo con código Python reutilizable."
  - Rúbrica: corrección factual sí, completitud sí, contradicción no.
  - Comentario: respuesta correcta; omite "un módulo es", que ya está en
    la pregunta.
- **Pregunta:** ¿Qué es una función en Python? (F1 = 0,71)
  - Referencia: "Una función es un bloque de código reutilizable."
  - Respuesta: "Un bloque de código reutilizable que realiza una tarea."
  - Rúbrica: corrección factual sí, completitud sí, contradicción no.
  - Comentario: respuesta correcta; agrega "que realiza una tarea",
    información adicional correcta.
- **Pregunta:** ¿Qué es una lista en Python? (F1 = 0,67)
  - Referencia: "Una lista es una colección ordenada y modificable."
  - Respuesta: "Una colección ordenada y modificable de elementos."
  - Rúbrica: corrección factual sí, completitud sí, contradicción no.
  - Comentario: respuesta correcta; agrega "de elementos", que la métrica
    cuenta como palabras de más.
- **Pregunta:** ¿Qué es un bucle while en Python? (F1 = 0,60)
  - Referencia: "Un bucle while se repite mientras una condición sea
    verdadera."
  - Respuesta: "Repite un bloque de código mientras su condición sea
    verdadera."
  - Rúbrica: corrección factual sí, completitud sí, contradicción no.
  - Comentario: respuesta correcta; no repite "bucle while", usa "su" en
    vez de "una" y agrega "un bloque de código".

**Los 5 peores**

- **Pregunta:** ¿Para qué sirve la palabra def en Python? (F1 = 0,40)
  - Referencia: "La palabra def sirve para definir una función."
  - Respuesta: "Sirve para definir y crear funciones nuevas."
  - Rúbrica: corrección factual sí, completitud sí, contradicción no.
  - Comentario: respuesta correcta; "funciones" no coincide con "función"
    (falso negativo).
- **Pregunta:** ¿Para qué sirve la función print en Python? (F1 = 0,38)
  - Referencia: "La función print muestra información en la pantalla."
  - Respuesta: "Para mostrar texto o datos en la pantalla."
  - Rúbrica: corrección factual sí, completitud sí, contradicción no.
  - Comentario: respuesta correcta; "mostrar" no coincide con "muestra" ni
    "datos" con "información" (falso negativo).
- **Pregunta:** ¿Qué es un bucle for en Python? (F1 = 0,35)
  - Referencia: "Un bucle for recorre los elementos de una secuencia."
  - Respuesta: "Una estructura para repetir un bloque de código."
  - Rúbrica: corrección factual sí, completitud no, contradicción no.
  - Comentario: respuesta genérica; no dice que recorre los elementos de
    una secuencia y podría describir un while. El F1 bajo es merecido.
- **Pregunta:** ¿Para qué sirve try except en Python? (F1 = 0,35)
  - Referencia: "Try except sirve para capturar y manejar excepciones."
  - Respuesta: "Para manejar errores y evitar que el programa falle."
  - Rúbrica: corrección factual sí, completitud parcialmente, contradicción
    no.
  - Comentario: dice "manejar errores" pero no menciona "capturar";
    "errores" es sinónimo de "excepciones" y la métrica no lo reconoce.
- **Pregunta:** ¿Qué es una excepción en Python? (F1 = 0,33)
  - Referencia: "Una excepción es un error que ocurre durante la
    ejecución."
  - Respuesta: "Un error que interrumpe el flujo del programa."
  - Rúbrica: corrección factual sí, completitud parcialmente, contradicción
    no.
  - Comentario: es correcta, pero no dice explícitamente "durante la
    ejecución".


## Recomendación de uso

Usar F1 para comparar en volumen entre versiones del cliente o del prompt.
Revisar siempre a mano toda respuesta con F1 < 0,50 y cualquier respuesta
con fechas, cifras o nombres propios.
