#📝 Paso 1: registra al menos dos versiones de tu propio prompt


import hashlib
from datetime import date
 
def huella_prompt(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]
 
class RegistroDePrompts:
    def __init__(self):
        self.versiones = []
 
    def registrar(self, nombre, texto, autor, nota):
        version = {
            "nombre": nombre, "huella": huella_prompt(texto), "texto": texto,
            "autor": autor, "fecha": str(date.today()), "nota": nota,
        }
        self.versiones.append(version)
        return version
 
    def ultima(self, nombre):
        candidatas = [v for v in self.versiones if v["nombre"] == nombre]
        return candidatas[-1] if candidatas else None
 
registro = RegistroDePrompts()
# registro.registrar("prompt_de_mi_proyecto", tu_prompt_anterior, "tu nombre", "version original")
# registro.registrar("prompt_de_mi_proyecto", tu_prompt_actual, "tu nombre", "que cambio y por que")
