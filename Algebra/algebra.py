import os
from manim import *
from Algebra.ExtraerLATEX import extraer_texto_colores  
from Algebra.criterio_animacion import decidir_animacion  

def _obtener_codigos_latex(fuente):
    """Función interna para parsear archivos o textos raw."""
    if os.path.isfile(fuente):
        with open(fuente, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = fuente.split("\n")

    latex_codes = []
    for line in lines:
        line = line.strip()
        if line.startswith("$$") and line.endswith("$$"):
            latex_codes.append(line[2:-2].strip())
    return latex_codes

def procesar_pasos_algebraicos(escena, fuente, ancho_camara, runtime=1.0, waittime=1.0):
    """Motor original: Oculta la gráfica y muestra las ecuaciones en el centro (Full Screen)."""
    latex_codes = _obtener_codigos_latex(fuente)
    max_width = ancho_camara * 0.9 
    last_label, last_tex = None, None  

    for latex in latex_codes:
        fragmentos = extraer_texto_colores(latex)
        textos_limpios = [frag[0] for frag in fragmentos]
        label = MathTex(*textos_limpios).set_z_index(20)
        
        for i, frag in enumerate(fragmentos):
            if frag[1].lower() != "white": label[i].set_color(frag[1])
        
        if label.width > max_width: label.scale_to_fit_width(max_width)
        else: label.scale(ancho_camara / 10) 

        label.move_to(escena.camera.frame.get_center())

        if last_label is None:
            escena.play(Write(label), run_time=runtime)
            escena.wait(waittime)
        else:
            animacion = decidir_animacion(last_tex, latex, last_label, label)
            escena.play(animacion, run_time=runtime)
            escena.wait(waittime)
            
        last_label, last_tex = label, latex  

    if last_label is not None:
        escena.wait(0.5)
        escena.play(FadeOut(last_label), run_time=0.5)


def procesar_algebra_flotante(escena, fuente, ancho_camara, posicion="UL", remover=False, runtime=1.0, waittime=1.0):
    """Renderiza transformaciones algebraicas ancladas en una esquina sin ocultar la gráfica."""
    latex_codes = _obtener_codigos_latex(fuente)
    
    # Mapeo de posiciones Manim
    pos_map = {"UL": UL, "UR": UR, "DL": DL, "DR": DR}
    manim_pos = pos_map.get(posicion.upper(), UL)
    
    # Padding matemático para que no pegue exactamente en el borde
    buff_x = ancho_camara * 0.03
    buff_y = ancho_camara * 0.03 * (9/16) 
    
    # Dirección del offset (empuja hacia adentro de la pantalla)
    offset = -manim_pos[0] * RIGHT * buff_x + -manim_pos[1] * UP * buff_y
    
    # Reducido al 25% de la pantalla
    max_width = ancho_camara * 0.25 
    
    last_label, last_tex = None, None  

    for latex in latex_codes:
        fragmentos = extraer_texto_colores(latex)
        textos_limpios = [frag[0] for frag in fragmentos]
        
        label = MathTex(*textos_limpios).set_z_index(30)
        
        for i, frag in enumerate(fragmentos):
            if frag[1].lower() != "white": 
                label[i].set_color(frag[1])
                
        # Ajuste de tamaño al 25% o escala base
        if label.width > max_width:
            label.scale_to_fit_width(max_width)
        else:
            label.scale(ancho_camara / 20) # Reducido en proporción
            
        # CORRECCIÓN DE ANCLAJE: 
        # Al usar aligned_edge, la esquina del texto empata con la esquina del punto de anclaje.
        esquina_camara = escena.camera.frame.get_corner(manim_pos)
        label.move_to(esquina_camara + offset, aligned_edge=manim_pos)
        
        if last_label is None:
            escena.play(Write(label), run_time=runtime)
            escena.wait(waittime)
        else:
            animacion = decidir_animacion(last_tex, latex, last_label, label)
            escena.play(animacion, run_time=runtime)
            escena.wait(waittime)
            
        last_label, last_tex = label, latex
        
    if remover and last_label is not None:
        escena.play(FadeOut(last_label), run_time=0.5)