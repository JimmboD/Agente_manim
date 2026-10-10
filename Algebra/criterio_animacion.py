from difflib import SequenceMatcher
import re
from manim import TransformMatchingShapes, ReplacementTransform

def decidir_animacion(tex_viejo, tex_nuevo, mobj_viejo, mobj_nuevo):
    """
    Compara dos strings LaTeX con doble criterio: orden y presencia de variables.
    """
    # 1. Limpieza más agresiva (quitamos textcolor, frac, sqrt, y llaves)
    def limpiar(t):
        t = re.sub(r'\\textcolor\{.*?\}', '', t) # Quita color
        t = re.sub(r'\\[a-zA-Z]+', '', t)        # Quita comandos como \frac, \left, \right
        t = re.sub(r'[^a-zA-Z0-9=+\-*/]', '', t) # Deja solo letras, números y operadores
        return t
    
    str1_limpio = limpiar(tex_viejo)
    str2_limpio = limpiar(tex_nuevo)
    
    # CRITERIO 1: Similitud en orden (Ideal para cambios de color o sustituciones leves)
    similitud_orden = SequenceMatcher(None, str1_limpio, str2_limpio).ratio()
    
    # CRITERIO 2: Similitud de variables (Orden irrelevante, ideal para DESPEJES)
    letras_viejas = set(filter(str.isalnum, str1_limpio))
    letras_nuevas = set(filter(str.isalnum, str2_limpio))
    
    if letras_viejas and letras_nuevas:
        interseccion = letras_viejas.intersection(letras_nuevas)
        # Porcentaje de variables/números que sobrevivieron al cambio
        similitud_variables = len(interseccion) / max(len(letras_viejas), len(letras_nuevas))
    else:
        similitud_variables = 0

    # DECISIÓN: Si el orden se mantiene (>=0.65) o si comparten las mismas letras (>=0.75)
    if similitud_orden >= 0.65 or similitud_variables >= 0.75:
        return TransformMatchingShapes(mobj_viejo, mobj_nuevo)
    else:
        return ReplacementTransform(mobj_viejo, mobj_nuevo)