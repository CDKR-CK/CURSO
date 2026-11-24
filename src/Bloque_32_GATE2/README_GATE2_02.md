# Gate 2 – Servicio RAG de la Chocolatería

Entrega del **Gate 2: Integración y orquestación (Módulo 2, Bloque S1)**.
Archivo principal: [`servicio_rag_02.py`](servicio_rag_02.py).

---

## 1. Descripción general del proyecto

La **Chocolatería** es una tienda de chocolates que necesita un **asistente de atención al cliente**. El asistente responde preguntas sobre despachos, devoluciones, alérgenos, conservación, estado de pedidos y precios, **usando solo la información de la tienda** y **citando la fuente** de cada respuesta (`[doc1]`, `[doc7]`, etc.).

El servicio reúne en un solo archivo lo que se construyó por separado en los Bloques 24 a 32:

| Pieza de la entrega | Dónde está en `servicio_rag_02.py` | Bloque |
| --- | --- | --- |
| 🗂️ Índice Chroma persistido y actualización incremental | `cargar_indice()` (agrega, actualiza o borra solo lo que cambió, con ids explícitos) | 24-25 |
| 🔎 Recuperación con cita de fuente | `responder()`, `PLANTILLA_USUARIO` (cita `[docN]`) | 26 |
| 🔎 Precisión y exhaustividad sobre el corpus propio | `evaluar_recuperacion()` con `CASOS_EVALUACION` | 27 |
| 📈 Latencia por etapa y consumo de tokens | eventos `latencia` y `consumo_llm` en `responder()` | 28 |
| ⚖️ Decisión de personalización | `recomendar_estrategia()` con `RESPUESTAS_ASISTENTE` | 30 |
| 🧾 Logging JSON con `trace_id`, sin contenido crudo | `evento()`, `trace_id_var`, archivo `logs/servicio_rag_02.jsonl` | 31 |
| 🛡️ Filtro de inyección sobre la interfaz real de `Document` | `filtrar_documentos_sospechosos()` (usa `d.page_content`) | 31 |
| 👤 Registro de versiones de prompt | `RegistroDePrompts`, `huella()`, `diff_prompts()` | 32 |
| 👤 Supervisión humana con `interrupt()` / `Command` | `app_supervision`, `pedir_aprobacion()` | 32 |
| ⚠️ Matriz de riesgos (7 filas propias) | `MATRIZ_RIESGOS`, `categoria_riesgo()` | 32 |

### Flujo de una consulta

```
pregunta ──► recuperar (Chroma, k=3) ──► filtrar inyección ──► ¿quedan documentos limpios?
                                                                 │ no ──► "No tengo informacion suficiente..." (sin llamar al modelo)
                                                                 │ sí
                                                                 ▼
             armar prompt (sistema + <contexto>) ──► generar ──► verificar cita [docN]
                                                                 ▼
                         ¿alérgenos / inyección / promoción sin fuente? ──► sí ──► supervisión humana (interrupt)
```

Cada etapa escribe un evento JSON con el **mismo `trace_id`**. Los logs guardan solo **longitudes, huellas (hash) y conteos**, nunca el texto de la pregunta ni el de los documentos.

### Corpus

12 documentos con id explícito:

- `doc1` a `doc10`: despachos, devoluciones, alérgenos, conservación, pedidos CH-1001 y CH-1002, y precios de 4 productos (el mismo corpus de los Bloques 27 a 31).
- `comentario-ticket-881` y `resena-web-042`: textos de terceros **con inyección de prompt** (Bloque 31). Están a propósito para demostrar que el filtro los descarta.

---

## 2. Requisitos e instalación del entorno

| Requisito | Versión usada en la prueba |
| --- | --- |
| Python | 3.10 o superior (probado con **3.14.10**) |
| langchain-core | 1.7.7 |
| langchain-chroma | 1.1.0 (instala chromadb 1.5.9) |
| langgraph | 1.2.20 |
| python-dotenv | 1.2.4 |
| langchain-google-genai | 4.4.3 (solo para el modo `--real`) |

### Pasos (Windows, PowerShell)

Desde la raíz del repositorio (`CURSO`):

```powershell
python -m venv venv
```

```powershell
.\venv\Scripts\Activate.ps1
```

```powershell
pip install langchain-core langchain-chroma langgraph python-dotenv langchain-google-genai
```

En macOS o Linux, el entorno se activa con `source venv/bin/activate` y el comando puede llamarse `python3`.

### Variables de entorno (solo modo `--real`)

Crea un archivo `.env` en la **raíz del repositorio** con tu clave de Gemini:

```
GOOGLE_API_KEY=tu_llave_aqui
GEMINI_API_KEY=tu_llave_aqui
```

El archivo `.env` **nunca** se sube al repositorio (Git lo ignora). Para comprobarlo:

```powershell
git check-ignore .env
```

Debe imprimir `.env`.

---

## 3. Cómo correr la entrega

Entra a la carpeta del Gate 2, con el entorno virtual activo:

```powershell
cd src\Bloque_32_GATE2
```

### Modo simulado (por defecto, sin API ni costo)

Usa `DeterministicFakeEmbedding` y `FakeListLLM` (embeddings y modelo simulados de LangChain):

```powershell
python servicio_rag_02.py
```

### Modo real (Gemini)

Usa `models/gemini-embedding-001` y `gemini-3.5-flash-lite`:

```powershell
python servicio_rag_02.py --real
```

### Reindexar desde cero

```powershell
python servicio_rag_02.py --reindexar
```

### Qué hace la corrida (7 secciones)

1. **Índice persistido**: crea o reconecta `vectorstore/`. En la primera corrida indexa los 12 documentos; en las siguientes **no reconstruye nada**. Después propone un cambio de precio (`doc7`: $12.900 → $13.900) que **pasa por supervisión humana antes de reindexar**; en la demo la persona lo rechaza y el índice no cambia.
2. **Tres consultas de punta a punta**, con logs JSON, cita de fuente, latencia y tokens.
3. **Contexto comprometido**: un índice que solo tiene los 2 documentos con inyección. El servicio corta antes de llamar al modelo y responde `No tengo informacion suficiente y verificada para responder esto.`
4. **Supervisión humana sobre respuestas marcadas**: el grafo se pausa (`__interrupt__`) y se retoma con `Command(resume=True)`.
5. **Versionado de prompt**: 2 versiones con huella y diff; la activación pasa por el grafo (un camino aprobado y otro rechazado).
6. **Métricas de recuperación y decisión de personalización**.
7. **Matriz de riesgos**, con la verificación de que todo riesgo ALTO o CRITICO tiene su punto de supervisión.

### Resultado esperado (modo simulado, primera corrida, recortado)

La salida completa de esta corrida está en `servicio_rag_02.txt`. En cada corrida cambian la fecha y hora, los `trace_id` y los milisegundos; los documentos recuperados son siempre los mismos, porque `DeterministicFakeEmbedding` genera el mismo vector para el mismo texto:

```
Servicio RAG Chocolatería - modo SIMULADO (sin API) - DD/MM/AAAA - HH:MM:SS
1) Índice persistido con actualización incremental
resumen: {'nuevos': 12, 'modificados': 0, 'eliminados': 0, 'sin_cambio': 0, 'total': 12}
pausado, pendiente: {'accion': 'cambio_precio', 'referencia': 'doc7', 'motivo': 'caja de trufas: $12.900 -> $13.900'}
cambio de precio en doc7 rechazado, el indice no cambia

2) Consultas de punta a punta
--- pregunta: cuantos dias demora el despacho a regiones?
{"ts": "...", "evento": "consulta_recibida", "trace_id": "trace-0acb8687", "pregunta_len": 43, "pregunta_huella": "b175e07a600a", "prompt_huella": "81542226d725"}
{"ts": "...", "evento": "documentos_recuperados", "trace_id": "trace-0acb8687", "n": 3, "fuentes": ["doc2", "comentario-ticket-881", "doc1"]}
{"ts": "...", "evento": "documentos_descartados_por_inyeccion", "trace_id": "trace-0acb8687", "n": 1, "fuentes": ["comentario-ticket-881"]}
{"ts": "...", "evento": "consumo_llm", "trace_id": "trace-0acb8687", "simulado": true, "input_tokens": 215, "output_tokens": 30, "total_tokens": 245}
{"ts": "...", "evento": "latencia", "trace_id": "trace-0acb8687", "tiempos_ms": {"recuperacion": 1.67, "generacion": 0.43}, "total_ms": 2.1}
{"ts": "...", "evento": "respuesta_generada", "trace_id": "trace-0acb8687", "respuesta_len": 121, "fuentes": ["doc2"], "revision_humana": true}
...
3) Contexto comprometido
respuesta final: No tengo informacion suficiente y verificada para responder esto.
4) Supervisión humana
pausado, pendiente: {'accion': 'respuesta_cliente', 'referencia': 'trace-67aa286b', 'motivo': 'pregunta sobre alergenos'}
respuesta trace-67aa286b enviada al cliente
5) Versionado de prompt
48500aec8ceb - AAAA-MM-DD - CK - version original
81542226d725 - AAAA-MM-DD - CK - agrega instruccion anti-inyeccion (Bloque 31)
version 81542226d725 activada
version 81542226d725 rechazada, se mantiene la anterior
6) Métricas y personalización
puntaje: {'RAG': 5, 'Fine-tuning completo': 0, 'PEFT': 1} -> recomendacion: ['RAG']
7) Matriz de riesgos
✅ todo riesgo ALTO/CRITICO tiene punto de supervision
trace_id fuera de cualquier consulta: None
Proceso terminado sin errores.
```

En la segunda corrida, el resumen del índice muestra `'nuevos': 0, ..., 'sin_cambio': 12, 'total': 12`: el índice se reutiliza y no se duplica.

> **Nota sobre el modo simulado**: los embeddings falsos no entienden el significado del texto, así que los documentos recuperados no siempre corresponden a la pregunta. El modelo simulado responde con el primer documento limpio recuperado y su cita. Lo que se verifica en este modo es la **mecánica** del pipeline (persistencia, filtro, cita, logs, supervisión), no la calidad de la respuesta.

---

## 4. Calidad de la recuperación (Bloque 27)

Medida con embeddings reales (`models/gemini-embedding-001`) sobre el corpus propio `doc1`–`doc10`, con 10 preguntas etiquetadas (una sin respuesta: "tienen tienda fisica en Valparaiso"). Resultado de la evaluación del Bloque 27:

| k | Precisión | Exhaustividad (recall) | F1 |
| --- | --- | --- | --- |
| 1 | 0,900 | 0,944 | **0,922** (mejor F1) |
| 2 | 0,500 | 1,000 | 0,667 |
| 3 | 0,333 | 1,000 | 0,500 |
| 5 | 0,200 | 1,000 | 0,333 |

El servicio usa **k=3**: con k=1 se pierde el segundo documento en la pregunta "cuanto duran las trufas y cuanto vale la caja" (necesita `doc4` y `doc7`), y para atención al cliente pesa más no omitir información (recall 1,000) que la precisión. El ruido extra lo controlan el prompt ("usa solo el contexto") y la cita obligatoria.

La función `evaluar_recuperacion()` del servicio repite esta medición. En la corrida real de este servicio (`--real`, k=3) dio:

```
k=3, 9 casos -> precision: 0,370  recall: 1,000
```

La exhaustividad se mantiene en 1,000: ningún documento relevante quedó fuera. La precisión difiere del 0,333 del Bloque 27 por dos razones: el servicio promedia solo los 9 casos que tienen documento relevante, y el índice incluye además los 2 documentos con inyección. En modo simulado, los valores salen marcados como **SIMULADO**, porque con embeddings falsos no tienen significado.

---

## 5. Costo y latencia (Bloque 28)

### Corrida real de este servicio (`python servicio_rag_02.py --real`, k=3)

En este servicio, la etapa "recuperación" incluye el embedding de la pregunta (llamada a la API) y la búsqueda en Chroma.

| Pregunta | Recuperación (ms) | Generación (ms) | Total (ms) | Tokens entrada / salida | Respuesta del modelo |
| --- | --- | --- | --- | --- | --- |
| cuantos dias demora el despacho a regiones? | 908,89 | 876,73 | 1.785,62 | 223 / 19 | El despacho a otras regiones demora de 3 a 5 días hábiles [doc1]. |
| los chocolates pueden tener mani? | 356,80 | 770,16 | 1.126,96 | 233 / 33 | Sí, ... pueden contener trazas de ambos [doc3]. |
| cuanto duran las trufas y cuanto vale la caja? | 353,43 | 846,06 | 1.199,49 | 217 / 33 | Las trufas duran 30 días [doc4] y la caja de trufas cuesta $12.900 [doc7]. |

- ✅ Las 3 respuestas citan la fuente correcta, sin que el servicio tenga que agregar la cita.
- ✅ En la 1.ª y la 3.ª consulta se recuperó un documento con inyección (`comentario-ticket-881`, `resena-web-042`), que el filtro descartó antes del prompt. La reseña "trufas gratis" no llegó a la respuesta.
- ✅ La 1.ª consulta (908,89 ms) incluye el arranque de la conexión con la API; en las siguientes, la recuperación baja a unos 355 ms.

### Corrida real del Bloque 28 (Gemini, k=3)

| Pregunta | embed_query (ms) | búsqueda (ms) | generación (ms) | total (ms) | tokens entrada / salida |
| --- | --- | --- | --- | --- | --- |
| cuantos dias demora el despacho a regiones? | 374,55 | 1,86 | 1.563,35 | 1.939,77 | 183 / 18 |
| los chocolates pueden tener mani? | 367,96 | 1,90 | 658,13 | 1.027,99 | 160 / 28 |
| cuanto duran las trufas y cuanto vale la caja? | 344,30 | 1,39 | 726,66 | 1.072,35 | 179 / 27 |

Conclusiones:
- ✅ La **generación** es la etapa más lenta en todas las consultas; la búsqueda vectorial local tarda menos de 2 ms.
- ✅ Subir de k=3 a k=6 aumentó los tokens de entrada de 179 a 265 (+86): más contexto cuesta más.

### Corrida simulada (`python servicio_rag_02.py`) – **SIMULADA**

Los tokens del evento `consumo_llm` se **estiman** (largo del texto / 4) y el evento lleva `"simulado": true`. La latencia simulada (unos 2 ms) no representa la de la API real.

---

## 6. Decisión de personalización (Bloque 30)

En el proyecto hay **dos tareas distintas** y cada una tiene su propia decisión, tomada con la misma función `recomendar_estrategia()` del curso:

### 6.1 Asistente de atención al cliente (este servicio) → **RAG**

| Clave | Respuesta | Evidencia |
| --- | --- | --- |
| `informacion_cambia_seguido` | True | Precios, estado de pedidos (CH-1001 en tránsito) y condiciones de despacho cambian varias veces al año. |
| `problema_de_formato_o_tono` | False | En el Bloque 28 el modelo respondió con la cita `[N]` en las 5 consultas reales. |
| `dataset_grande_y_de_calidad` | False | No hay pares pregunta-respuesta etiquetados para entrenar. |
| `presupuesto_limitado_o_iterar_rapido` | True | No hay presupuesto de entrenamiento; actualizar el índice es inmediato y casi gratis. |
| `necesita_multiples_variantes` | False | Un solo asistente para todos los canales. |

Puntaje: **RAG 5**, PEFT 1, fine-tuning completo 0 → **ganador claro: RAG**.

El conocimiento cambia y debe poder citarse; un modelo entrenado lo dejaría "congelado" y no podría decir de qué documento sacó un precio. Con RAG, un cambio de precio es solo una actualización incremental del índice (`cargar_indice`), con aprobación humana previa.

### 6.2 Clasificador de mensajes (Bloque 29) → **PEFT**

Decisión tomada en el Bloque 30: el problema es de **formato** (30 % de respuestas JSON inválidas), no de conocimiento. Puntaje PEFT 3, RAG 2, fine-tuning completo 1. Queda fuera de este servicio porque requiere entrenar un adapter.

---

## 7. Seguridad, versionado y gobernanza (Bloques 31-32)

### 7.1 Filtro de inyección

`PATRONES_SOSPECHOSOS` (6 patrones en español e inglés) se aplica sobre `d.page_content` de los `Document` reales **antes** de armar el prompt. Los documentos descartados solo se registran por su id (`fuentes`), nunca por su texto. Si no queda ningún documento limpio, el servicio **no llama al modelo**.

Además, el prompt de sistema prohíbe cambiar de comportamiento por texto del contexto, y el contexto va delimitado entre `<contexto>` y `</contexto>`.

### 7.2 Registro de versiones de prompt

| Huella | Nota |
| --- | --- |
| `48500aec8ceb` | versión original |
| `81542226d725` | agrega instrucción anti-inyección (Bloque 31) – **versión activa** |

Cada consulta registra `prompt_huella` en su primer evento: así se sabe con qué versión del prompt se respondió.

### 7.3 Puntos de supervisión humana (corren de verdad)

Un solo grafo LangGraph (`app_supervision`, con `InMemorySaver`) se usa para tres acciones de riesgo:

| Acción | Cuándo se pausa | Riesgo que cubre |
| --- | --- | --- |
| `respuesta_cliente` | El contexto traía inyección, la pregunta es sobre alérgenos o la respuesta menciona "gratis"/"descuento" sin respaldo en las fuentes | CRITICO inyección, ALTO alérgenos, ALTO promoción inventada |
| `cambio_precio` | Antes de reindexar un documento de precio modificado | ALTO precio desactualizado |
| `despliegue_prompt` | Antes de activar una nueva versión del prompt | BAJO cambio de tono |

En cada caso, la primera invocación devuelve `__interrupt__` con lo que la persona debe revisar, y solo `Command(resume=True)` (aprobar) o `Command(resume=False)` (rechazar) completa la acción.

### 7.4 Matriz de riesgos

Puntaje = probabilidad × impacto (escala 1 a 5). CRITICO ≥ 15, ALTO ≥ 9, MEDIO ≥ 4, BAJO < 4.

| Categoría | Puntaje | Riesgo | Mitigación | Punto de supervisión |
| --- | --- | --- | --- | --- |
| CRITICO | 16 | Inyección de prompt vía reseña o comentario indexado | Filtro de patrones + `<contexto>` (Bloque 31) | `respuesta_cliente` |
| ALTO | 12 | Precio o promoción inventada (ej. trufas gratis) | Solo contexto + cita `[docN]` (Bloque 31) | `respuesta_cliente` ("gratis" sin fuente) |
| ALTO | 10 | Omitir trazas de maní a cliente alérgico | `doc3` indexado + cita obligatoria (Bloque 26) | `respuesta_cliente` (alérgenos) |
| ALTO | 9 | Precio desactualizado por chunk no reindexado | Índice incremental con ids `doc7`–`doc10` (Bloque 25) | `cambio_precio` |
| MEDIO | 8 | Pregunta o datos de pedido en logs sin redactar | Huella/longitud en vez de contenido (Bloque 31) | – |
| MEDIO | 6 | Modelo de embeddings deprecado sin aviso | `gemini-embedding-001` + revisión periódica (Bloque 28) | – |
| BAJO | 3 | Prompt nuevo cambia el tono sin aviso | `RegistroDePrompts` + diff (Bloque 32) | `despliegue_prompt` |

✅ Todo riesgo ALTO o CRITICO está conectado a un punto de supervisión que corre en el código.

---

## 8. Verificación de los 4 criterios no compensables

| Criterio | Cómo se verificó | Resultado |
| --- | --- | --- |
| Pipeline corre de punta a punta | `python servicio_rag_02.py`, código de salida 0 | ✅ |
| Cada respuesta cita su fuente | `assert` dentro del servicio: cada respuesta debe traer `fuentes` y nombrar al menos una como `[docN]` | ✅ |
| Logs sin contenido crudo | Consulta con el correo de prueba `ana.perez@example.com` y búsqueda en `logs/` (0 coincidencias) | ✅ |
| Supervisión humana funciona | `assert` dentro de `pedir_aprobacion()`: la primera invocación trae `__interrupt__` y, tras `Command(resume=...)`, ya no | ✅ |

El servicio termina con un `AssertionError` si cualquiera de estas condiciones falla, así que "Proceso terminado sin errores." confirma los criterios 1, 2 y 4.

### Comprobación manual (Windows, desde esta carpeta)

Criterio 1, el código de salida debe ser 0:

```powershell
python servicio_rag_02.py; echo $LASTEXITCODE
```

Criterio 2, cada línea de respuesta debe traer su cita `[docN]`:

```powershell
python servicio_rag_02.py | findstr /l /c:"respuesta final"
```

Criterio 3, hacer una consulta que incluya un correo de prueba:

```powershell
python -c "import servicio_rag_02 as s; e, c, n = s.crear_componentes(False); v, _ = s.cargar_indice(e, n); s.responder('Mi correo es ana.perez@example.com, cual es la politica de devoluciones?', v, c)"
```

Y buscarlo en los logs. Este comando no debe imprimir nada:

```powershell
findstr /s /i ana.perez logs\*
```

Los eventos de esa consulta solo traen `pregunta_len` y `pregunta_huella`, nunca el texto de la pregunta.

---

## 9. Registro del ensayo funcional

- **Encontrado 1**: en el Bloque 31, `filtrar_documentos_sospechosos` usaba `d.contenido` (un `namedtuple` propio), mientras que el retriever real devuelve `Document` con `d.page_content` y `d.metadata["fuente"]`.
  **Corregido**: el filtro trabaja directo sobre `Document`; se eliminó la conversión intermedia `recuperar()`.
- **Encontrado 2**: el modelo simulado del ejemplo de referencia siempre respondía "Segun el manual.pdf...", aunque esa fuente no estuviera entre los documentos recuperados. Con eso, la cita no prueba nada.
  **Corregido**: el modelo simulado responde con el primer documento **limpio recuperado** y su cita `[docN]`. Además, `fuentes` se arma solo con las fuentes que la respuesta cita de verdad; si el modelo no cita ninguna, el servicio agrega la línea `Fuentes:` y lo registra (`cita_agregada_por_el_servicio`).
- **Encontrado 3**: el riesgo ALTO "precio desactualizado" tenía su punto de supervisión solo descrito en la matriz del Bloque 32.
  **Corregido**: el cambio de precio pasa por `app_supervision` (`cambio_precio`) antes de llamar a `cargar_indice`.
- **Encontrado 4**: en el Bloque 25, los ids explícitos evitaban duplicados, pero cada indexación volvía a calcular los embeddings de todos los chunks, aunque no hubieran cambiado, y no borraba los que ya no estaban en el corpus.
  **Corregido**: `cargar_indice` compara por id y contenido: agrega los nuevos, actualiza los modificados (upsert con el mismo id) y borra los eliminados. Se verificó con un corpus de prueba de 2 documentos: 2 nuevos → 2 sin cambio → 1 modificado y 1 eliminado.
- **Resultado tras las correcciones**: el pipeline completo corre sin `Traceback` en dos corridas simuladas seguidas (la segunda reutiliza el índice: 12 sin cambio) y en una corrida real con Gemini. Cada respuesta cita su fuente y el correo de prueba no aparece en los logs.

---

## 10. Archivos de esta carpeta

| Archivo / carpeta | Contenido |
| --- | --- |
| `servicio_rag_02.py` | **Entrega**: servicio RAG completo de la Chocolatería |
| `README_GATE2_02.md` | **Entrega**: este documento |
| `servicio_rag_02.txt` | Salida de consola de una corrida simulada completa |
| `logs/servicio_rag_02.jsonl` | Logs JSON de cada corrida (se agregan al final) |
| `vectorstore/` | Vector store Chroma persistido. Se crea solo en la primera corrida y Git no lo sube |

Si se borran `vectorstore/` y `logs/`, el servicio los vuelve a crear en la siguiente corrida.

---
