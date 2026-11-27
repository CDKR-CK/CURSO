import re
import sys
from pathlib import Path

from Paso1_ficha_datos_01 import RUTA, cargar
from verificar_ficha_02 import verificar

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REVISION = Path(__file__).parent / "revision_alcance_01.md"
MIN_HITOS, MAX_HITOS = 3, 6


def verificar_pendientes(ficha):
    errores = []
    for numero in (4, 5):
        texto = ficha[f"texto{numero}"]
        if "[PENDIENTE" in texto or "[COMPLETAR" in texto:
            errores.append(f"la seccion {numero} todavia tiene marcas")
    return errores


def verificar_criterios(ficha):
    errores, avisos = [], []
    existentes = set(ficha["rf"]) | set(ficha["rnf"])
    if not ficha["criterios"]:
        errores.append("la seccion 4 no tiene criterios (formato CA-NN)")
    escritos = len(re.findall(r"(?m)^- CA", ficha["texto4"]))
    if escritos != len(ficha["criterios"]):
        errores.append(
            f"{escritos - len(ficha['criterios'])} criterio(s) "
            "no siguen el formato '- CA-NN (RF-NN): texto'"
        )
    cubiertos = set()
    for c in ficha["criterios"]:
        if not c["cubre"]:
            errores.append(f"{c['id']} no indica que RF o RNF cubre")
        for rid in c["cubre"]:
            if rid not in existentes:
                errores.append(f"{c['id']} cubre {rid}, que no existe")
        cubiertos.update(c["cubre"])
        if not re.search(r'\d|"', c["texto"]):
            avisos.append(f"{c['id']} no tiene ningun dato concreto")
    exigidos = ficha["cajones"]["Imprescindible"] + list(ficha["rnf"])
    for rid in exigidos:
        if rid not in cubiertos:
            errores.append(f"{rid} no tiene criterio de aceptacion")
    return errores, avisos


def verificar_plan(ficha):
    errores = []
    hitos = ficha["hitos"]
    ids_ca = {c["id"] for c in ficha["criterios"]}
    existentes = set(ficha["rf"]) | set(ficha["rnf"])
    escritos = len(re.findall(r"(?m)^- H\d", ficha["texto5"]))
    if escritos != len(hitos):
        errores.append(
            f"{escritos - len(hitos)} hito(s) no siguen el formato "
            "'- H1 (3 h): descripcion. Cubre: ... Se comprueba con: ...'"
        )
    if not MIN_HITOS <= len(hitos) <= MAX_HITOS:
        errores.append(
            f"hay {len(hitos)} hitos y se piden entre "
            f"{MIN_HITOS} y {MAX_HITOS}"
        )
    if ficha["disponibles"] is None or ficha["margen"] is None:
        errores.append(
            "faltan las lineas 'Horas disponibles:' y "
            "'Margen de imprevistos:'"
        )
    else:
        tope = ficha["disponibles"] - ficha["margen"]
        total = sum(h["horas"] for h in hitos)
        # Tolerancia mínima por la suma de decimales (ej. 1,5 + 3,6)
        if total > tope + 1e-9:
            errores.append(
                f"los hitos suman {total:.1f} h y el tope es {tope:.1f} h"
            )
    cubiertos, probados = set(), set()
    for h in hitos:
        if not h["cubre"]:
            errores.append(f"{h['id']} no indica que cubre")
        if not h["criterios"]:
            errores.append(f"{h['id']} no tiene criterio de aceptacion")
        for rid in h["cubre"]:
            if rid not in existentes:
                errores.append(f"{h['id']} cubre {rid}, que no existe")
        for cid in h["criterios"]:
            if cid not in ids_ca:
                errores.append(f"{h['id']} usa {cid}, que no existe")
        cubiertos.update(h["cubre"])
        probados.update(h["criterios"])
    for rid in ficha["cajones"]["Imprescindible"]:
        if rid not in cubiertos:
            errores.append(f"{rid} imprescindible sin hito que lo cubra")
    for cid in sorted(ids_ca - probados):
        errores.append(f"{cid} no lo comprueba ningun hito")
    return errores


def verificar_revision(ruta=REVISION):
    ruta = Path(ruta)
    if not ruta.exists():
        return [f"falta {ruta.name}: registra la revision cruzada"]
    with open(ruta, encoding="utf-8") as archivo:
        texto = archivo.read()
    patron = r"(?m)^- Hallazgo \d+(?: \([^)]*\))?: .+$"
    hallazgos = re.findall(patron, texto)
    decisiones = re.findall(
        r"(?m)^  Decisión: (?:aceptado|rechazado|aplazado)\b", texto
    )
    errores = []
    if len(hallazgos) < 2:
        errores.append(f"hay {len(hallazgos)} hallazgos y se piden 2")
    if len(decisiones) != len(hallazgos):
        errores.append("cada hallazgo necesita su linea 'Decisión:'")
    return errores


if __name__ == "__main__":
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else RUTA
    revision = Path(sys.argv[2]) if len(sys.argv) > 2 else REVISION
    if not ruta.exists():
        sys.exit(f"No existe {ruta}. Revisa la ruta de la ficha.")
    print(f"Ficha: {ruta.name} | Revision: {revision.name}")
    with open(ruta, encoding="utf-8") as archivo:
        errores, avisos = verificar(archivo.read(), ruta.parent)
    if not errores:
        ficha = cargar(ruta)
        errores = verificar_pendientes(ficha)
        if not errores:
            errores, avisos_ca = verificar_criterios(ficha)
            errores += verificar_plan(ficha)
            avisos += avisos_ca
        if not errores:
            errores = verificar_revision(revision)
    for aviso in avisos:
        print("AVISO:", aviso)
    for error in errores:
        print("ERROR:", error)
    if errores:
        print(f"\n{len(errores)} problema(s) por resolver")
        sys.exit(1)
    print("Ficha verificada: las cinco secciones son coherentes")
