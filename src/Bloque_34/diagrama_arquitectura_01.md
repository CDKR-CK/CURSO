# Diagrama de arquitectura: asistente de atención al cliente de la Chocolatería (Bloque 34)

Versión en Mermaid de `diagrama_arquitectura_01.png`. Los rótulos de las cajas son los mismos que se usan en la sección 3 de `ficha_diseno_funcional_04.md`.

```mermaid
flowchart LR
    cliente["Cliente<br/>(equipo de atención)"]

    subgraph docker["Contenedor Docker (frontera)"]
        direction LR
        fastapi["Servicio FastAPI<br/>POST /consulta"]
        orquestacion["Orquestación<br/>recuperación k=3<br/>filtro de inyección<br/>generación con [docN]"]
        langgraph["LangGraph (aprobación humana)<br/>alérgenos y promociones"]
        chroma[("Chroma<br/>vectorstore/ (volumen)<br/>doc1 a doc10")]
        logs[("Logs JSON<br/>logs/ con trace_id<br/>sin texto de preguntas")]
    end

    gemini["Gemini (API)<br/>gemini-3.5-flash-lite<br/>gemini-embedding-001"]
    env[".env<br/>clave de Gemini"]

    cliente -- "pregunta" --> fastapi
    fastapi -- "JSON: respuesta + fuentes" --> cliente
    fastapi --> orquestacion
    orquestacion -- "búsqueda" --> chroma
    orquestacion -- "revisión" --> langgraph
    orquestacion -- "prompt limpio" --> gemini
    orquestacion -- "longitudes y conteos" --> logs
    env -.-> gemini

    classDef externo stroke-dasharray: 4 3;
    class gemini,env externo;
```

## Componentes

| Caja | Función |
| --- | --- |
| Cliente | Integrante del equipo de atención que envía la pregunta y recibe la respuesta en JSON. |
| Servicio FastAPI | Expone el endpoint POST /consulta (RF-01). |
| Orquestación | Recupera 3 documentos, descarta los que traen inyección (RF-04) y genera la respuesta con citas [docN] (RF-02). |
| LangGraph (aprobación humana) | Retiene las respuestas sobre alérgenos o promociones sin respaldo hasta que una persona las apruebe o rechace (RF-05). |
| Chroma | Vector store persistido en vectorstore/, montado como volumen del contenedor. |
| Logs JSON | Registro con trace_id en logs/, solo con longitudes, huellas y conteos (RNF-02). |
| Gemini (API) | Modelo externo, fuera del contenedor. La clave se lee desde .env. |
| Contenedor Docker (frontera) | Empaqueta el servicio para que levante siguiendo el README (RNF-03). |
