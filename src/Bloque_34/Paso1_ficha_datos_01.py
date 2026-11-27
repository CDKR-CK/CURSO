import re

from verificar_ficha_02 import RUTA, leer_secciones

NUMERO = r"(\d+(?:[.,]\d+)?)"
# "- CA-01 (RF-01): texto"
PATRON_CA = r"(?m)^- (CA-\d{2}) \(([^)]*)\): (.+)$"
# "- H1 (1,5 h): descripción. Cubre: RF-01. Se comprueba con: CA-01."
PATRON_H = rf"(?m)^- (H\d+) \({NUMERO} h\): (.+)$"
PATRON_ID_REQ = r"RNF-\d{2}|RF-\d{2}"


def a_numero(texto):
    return float(texto.replace(",", "."))


def cargar(ruta=RUTA):
    with open(ruta, encoding="utf-8") as archivo:
        secciones = leer_secciones(archivo.read())
    req = secciones[2][1]
    cuerpo4 = secciones.get(4, ("", ""))[1]
    cuerpo5 = secciones.get(5, ("", ""))[1]
    ficha = {
        "rf": dict(re.findall(r"(?m)^- (RF-\d{2}): (.+)$", req)),
        "rnf": dict(re.findall(r"(?m)^- (RNF-\d{2}): (.+)$", req)),
        "cajones": {},
        "criterios": [],
        "hitos": [],
        "texto4": cuerpo4,
        "texto5": cuerpo5,
    }
    for nombre in ("Imprescindible", "Deseable", "Fuera de alcance"):
        m = re.search(rf"(?m)^{nombre}:\s*(.*)$", req)
        ficha["cajones"][nombre] = (
            re.findall(r"RF-\d{2}", m.group(1)) if m else []
        )
    for id_, cubre, texto in re.findall(PATRON_CA, cuerpo4):
        ficha["criterios"].append(
            {
                "id": id_,
                "cubre": re.findall(PATRON_ID_REQ, cubre),
                "texto": texto,
            }
        )
    for clave, etiqueta in (
        ("disponibles", "Horas disponibles"),
        ("margen", "Margen de imprevistos"),
    ):
        m = re.search(rf"(?m)^{etiqueta}:\s*{NUMERO} h", cuerpo5)
        ficha[clave] = a_numero(m.group(1)) if m else None
    for id_, horas, resto in re.findall(PATRON_H, cuerpo5):
        m = re.search(r"Cubre:(.*?)Se comprueba con:(.*)$", resto)
        ficha["hitos"].append(
            {
                "id": id_,
                "horas": a_numero(horas),
                "cubre": re.findall(PATRON_ID_REQ, m.group(1)) if m else [],
                "criterios": re.findall(r"CA-\d{2}", m.group(2)) if m else [],
            }
        )
    return ficha
