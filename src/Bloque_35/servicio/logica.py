import unicodedata

K = 3  # maximo de documentos que respaldan una respuesta (igual que la recuperacion k=3)

SIN_INFORMACION = "No tengo información suficiente para responder esa pregunta."

# Corpus de la Chocolateria: id -> (palabras clave sin tildes, texto oficial)
CORPUS = {
    "doc1": (("despacho", "envio", "demora", "region"),
             "Despachos: tardan 2 días hábiles en la Región Metropolitana y de 3 a 5 días "
             "hábiles en otras regiones. Son gratis en compras desde $30.000."),
    "doc2": (("devol", "reembols"),
             "Devoluciones: se aceptan dentro de 5 días corridos desde la recepción, con el "
             "producto sellado y su boleta."),
    "doc3": (("alergen", "mani", "traza", "soya", "frutos secos"),
             "Alérgenos: todos los productos contienen leche y soya. Se elaboran en una planta "
             "que procesa maní y frutos secos, por lo que pueden contener trazas de ambos."),
    "doc4": (("conserv", "guardar", "temperatura", "duran"),
             "Conservación: los chocolates se guardan entre 15 °C y 18 °C, lejos de la luz y "
             "la humedad. Duran 6 meses; las trufas, 30 días."),
    "doc5": (("ch-1001",),
             "Pedido CH-1001: en tránsito, llega en 2 días hábiles. Contiene 2 cajas de trufas."),
    "doc6": (("ch-1002",),
             "Pedido CH-1002: entregado. Contiene 1 caja de bombones surtidos."),
    "doc7": (("trufa",), "Producto: caja de trufas. Precio: $12.900."),
    "doc8": (("bombon",), "Producto: caja de bombones surtidos. Precio: $9.900."),
    "doc9": (("amargo",), "Producto: barra de chocolate amargo. Precio: $3.500."),
    "doc10": (("alfajor",), "Producto: caja de alfajores. Precio: $7.500."),
}

PEDIDOS = {
    "CH-1001": "en tránsito, llega en 2 días hábiles",
    "CH-1002": "entregado",
}


def _normalizar(texto):
    """Minusculas y sin tildes, para comparar palabras clave."""
    sin_tildes = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn")


def responder(pregunta):
    """Devuelve (texto, fuentes): el texto cita [docN] y fuentes lista esos mismos ids."""
    texto = _normalizar(pregunta)
    encontrados = [
        id_doc
        for id_doc, (palabras, _) in CORPUS.items()
        if any(palabra in texto for palabra in palabras)
    ][:K]
    if not encontrados:
        return SIN_INFORMACION, []
    respuesta = " ".join(f"{CORPUS[id_doc][1]} [{id_doc}]" for id_doc in encontrados)
    return respuesta, [f"[{id_doc}]" for id_doc in encontrados]


def estado_pedido(pedido_id):
    # Provisional: en la leccion siguiente un pedido inexistente sera un error 404.
    return PEDIDOS.get(pedido_id.upper(), "sin informacion")
