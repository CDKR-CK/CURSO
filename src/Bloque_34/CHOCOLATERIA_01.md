# CHOCOLATERIA CK

## Descripción del proyecto en palabras simples

**En una frase:** vamos a construir un asistente que responde las preguntas de los clientes de CHOCOLATERIA CK, una chocolatería en línea ficticia. Usa solo la información oficial de la tienda, dice de dónde la sacó y pide la revisión de una persona cuando la respuesta es delicada.

---

### 1. El problema que resuelve

Hoy el equipo de atención de CHOCOLATERIA CK responde unas 80 consultas a la semana sobre despachos, devoluciones, alérgenos, conservación y precios. Para cada una busca a mano en 8 fichas de políticas y productos.

- Cada consulta toma unos 6 minutos: cerca de 8 horas a la semana.
- La respuesta cambia según quién conteste.

Además, hay dos errores que salen caros:

- ❌ Decirle a un cliente alérgico que un bombón no tiene trazas de maní cuando sí las tiene.
- ❌ Prometer una promoción que no existe y tener que vender bajo costo.

**Lo que se espera lograr:** que cualquier integrante del equipo obtenga una respuesta con su fuente en menos de un minuto, y que una persona revise toda respuesta sobre alérgenos o promociones antes de enviarla.

---

### 2. Cómo funciona el asistente

1. Una persona del equipo escribe la pregunta, por ejemplo: "¿Cuánto demora un despacho a Santiago?".
2. El asistente busca en los documentos de la tienda los 3 más relacionados con la pregunta.
3. Descarta los documentos "contaminados": textos con instrucciones escondidas que intentan engañarlo, como un comentario de cliente que le pide ignorar las reglas y ofrecer un descuento. En los datos del proyecto hay 2 de estos documentos: comentario-ticket-881 y resena-web-042.
4. Con los documentos limpios, el modelo de IA (Gemini) redacta la respuesta y cita la fuente, por ejemplo [doc3].
5. Si la pregunta trata de alérgenos, o si la respuesta menciona una promoción que no aparece en los documentos, la respuesta no sale sola: queda en espera hasta que una persona la aprueba o la rechaza.
6. Si no encuentra la información, lo dice ("no tengo información suficiente") en vez de inventar.

---

### 3. Qué queda fuera, a propósito

- ❌ Página web con el historial de conversaciones.
- ❌ Conexión al sistema real de pedidos e inventario.
- ❌ Atención por WhatsApp.

Todo eso exige sistemas reales, cuentas reales y más tiempo del que tenemos. La consulta del estado de un pedido con datos simulados (por ejemplo, el pedido CH-1001) y la aprobación de cambios de precio quedan como deseables: se hacen solo si sobra tiempo.

---

### 4. Cómo lo vamos a construir (12 horas)

| Paso | Qué tendremos funcionando | Horas |
| --- | --- | --- |
| H1 | El servicio que recibe la pregunta y responde con fuentes | 1,5 |
| H2 | El filtro que descarta los documentos contaminados | 1,5 |
| H3 | La aprobación humana para alérgenos y promociones | 1,5 |
| H4 | Todo empaquetado en un contenedor (Docker), que cualquiera levanta en menos de 10 minutos | 1,5 |
| H5 | Pruebas, documentación y ensayo de la defensa | 3,6 |
| — | Margen para imprevistos (no se planifica) | 2,4 |
| | **Total** | **12,0** |

El orden sigue lo que depende de qué: primero el servicio, porque todo lo demás se apoya en él, y el contenedor al final, porque empaqueta lo que ya existe.

---

### 5. Cómo sabremos que está terminado

Con 12 pruebas concretas, cada una con resultado sí o no. Por ejemplo:

- ✅ Responde en menos de 5 segundos en al menos 9 de 10 consultas.
- ✅ Cita el documento correcto en al menos 8 de 9 preguntas de evaluación.
- ✅ Ante "¿Tienen tienda física en Valparaíso?" dice que no tiene esa información y no cita fuentes.
- ✅ Ante "¿El bombón de avellana tiene trazas de maní?" la respuesta queda en espera de aprobación.
- ✅ Los registros nunca guardan el texto de las preguntas ni datos personales, como un correo.

---

### 6. En qué etapa estamos

Hasta ahora (Bloques 33 y 34) hicimos el plano del proyecto: qué problema hay, qué se construye, con qué piezas, en qué orden y cómo se comprueba. Desde el Bloque 35 empieza la construcción, partiendo por el servicio con FastAPI.

---

### Dónde está el detalle técnico

| Tema | Archivo |
| --- | --- |
| Problema, requerimientos, arquitectura, criterios y plan | ficha_diseno_funcional_04.md |
| Diagrama de las piezas | diagrama_arquitectura_01.png y diagrama_arquitectura_01.md |
| Revisión del alcance y decisiones | revision_alcance_01.md |
