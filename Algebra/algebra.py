import os
from manim import *
from Algebra.ExtraerLATEX import extraer_texto_colores  
from Algebra.criterio_animacion import decidir_animacion  

def _obtener_codigos_latex(fuente):
    """Función interna para parsear archivos o textos raw."""
    if isinstance(fuente, str) and os.path.isfile(fuente):
        with open(fuente, "r", encoding="utf-8") as f:
            lines = f.readlines()
    elif isinstance(fuente, (list, tuple)):
        lines = [str(item) for item in fuente]
    else:
        lines = str(fuente).split("\n")

    latex_codes = []
    for line in lines:
        line = line.strip()
        if line.startswith("$$") and line.endswith("$$") and len(line) >= 4:
            latex_codes.append(line[2:-2].strip())
        elif line.startswith("$") and line.endswith("$") and len(line) >= 2:
            latex_codes.append(line[1:-1].strip())

    # Fallback si las líneas no venían envueltas en delimitadores $$
    if not latex_codes:
        for line in lines:
            line_str = line.strip()
            if line_str:
                latex_codes.append(line_str)

    return latex_codes


def _resolver_tiempos(
    n_pasos,
    tiempo_trans=None,
    tiempos_trans=None,
    tiempo_wait=None,
    tiempos_wait=None,
    tiempo_escritura=None,
    runtime_def=1.0,
    waittime_def=1.0
):
    """
    Construye las listas:
    - duraciones_animacion: longitud n_pasos
      * duraciones_animacion[0] = tiempo de Write inicial (o tiempo_escritura)
      * duraciones_animacion[1:] = tiempo de ReplacementTransform para cada paso
    - duraciones_espera: longitud n_pasos (tiempo en pantalla tras cada paso)
    """
    if n_pasos <= 0:
        return [], []

    # 1. Transformaciones / replacement transform
    base_trans = tiempo_trans if tiempo_trans is not None else runtime_def
    if tiempos_trans is not None and isinstance(tiempos_trans, (list, tuple)):
        lista_trans = [float(x) for x in tiempos_trans]
    elif isinstance(base_trans, (list, tuple)):
        lista_trans = [float(x) for x in base_trans]
    else:
        lista_trans = [float(base_trans if base_trans is not None else 1.0)]

    if not lista_trans:
        lista_trans = [1.0]

    if len(lista_trans) < n_pasos:
        ultimo = lista_trans[-1]
        lista_trans.extend([ultimo] * (n_pasos - len(lista_trans)))
    else:
        lista_trans = lista_trans[:n_pasos]

    if tiempo_escritura is not None:
        lista_trans[0] = float(tiempo_escritura)

    # 2. Esperas en pantalla
    base_wait = tiempo_wait if tiempo_wait is not None else waittime_def
    if tiempos_wait is not None and isinstance(tiempos_wait, (list, tuple)):
        lista_wait = [float(x) for x in tiempos_wait]
    elif isinstance(base_wait, (list, tuple)):
        lista_wait = [float(x) for x in base_wait]
    else:
        lista_wait = [float(base_wait if base_wait is not None else 1.0)]

    if not lista_wait:
        lista_wait = [1.0]

    if len(lista_wait) < n_pasos:
        ultimo = lista_wait[-1]
        lista_wait.extend([ultimo] * (n_pasos - len(lista_wait)))
    else:
        lista_wait = lista_wait[:n_pasos]

    return lista_trans, lista_wait


def procesar_pasos_algebraicos(
    escena,
    fuente,
    ancho_camara,
    runtime=1.0,
    waittime=1.0,
    tiempo_transformacion=None,
    tiempo_espera=None,
    tiempo_escritura=None,
    tiempos_transformacion=None,
    tiempos_espera=None,
    tiempo_salida=0.5,
    tiempo_replacement_transform=None,
    tiempo_pantalla=None,
    tiempo_entre_pasos=None,
    **kwargs
):
    """
    Motor original (Full Screen / Desde la normalidad):
    Oculta la gráfica y muestra las ecuaciones en el centro con transiciones algebraicas.
    
    Permite controlar:
    - tiempo_transformacion / tiempos_transformacion: duración del replacement transform entre pasos.
    - tiempo_espera / tiempos_espera: tiempo de espera en pantalla para cada ecuación.
    - tiempo_escritura: tiempo de escritura inicial de la primera ecuación.
    """
    if tiempo_replacement_transform is not None and tiempo_transformacion is None:
        tiempo_transformacion = tiempo_replacement_transform
    if tiempo_pantalla is not None and tiempo_espera is None:
        tiempo_espera = tiempo_pantalla
    if tiempo_entre_pasos is not None and tiempo_espera is None:
        tiempo_espera = tiempo_entre_pasos

    latex_codes = _obtener_codigos_latex(fuente)
    if not latex_codes:
        return None

    n_pasos = len(latex_codes)
    lista_trans, lista_wait = _resolver_tiempos(
        n_pasos,
        tiempo_trans=tiempo_transformacion,
        tiempos_trans=tiempos_transformacion,
        tiempo_wait=tiempo_espera,
        tiempos_wait=tiempos_espera,
        tiempo_escritura=tiempo_escritura,
        runtime_def=runtime,
        waittime_def=waittime
    )

    max_width = ancho_camara * 0.9 
    last_label, last_tex = None, None  

    for idx, latex in enumerate(latex_codes):
        fragmentos = extraer_texto_colores(latex)
        textos_limpios = [frag[0] for frag in fragmentos]
        label = MathTex(*textos_limpios).set_z_index(20)
        
        for i, frag in enumerate(fragmentos):
            if frag[1].lower() != "white": 
                label[i].set_color(frag[1])
        
        if label.width > max_width: 
            label.scale_to_fit_width(max_width)
        else: 
            label.scale(ancho_camara / 10) 

        label.move_to(escena.camera.frame.get_center())

        t_anim_paso = lista_trans[idx]
        t_wait_paso = lista_wait[idx]

        if last_label is None:
            escena.play(Write(label), run_time=t_anim_paso)
            if t_wait_paso > 0:
                escena.wait(t_wait_paso)
        else:
            animacion = decidir_animacion(last_tex, latex, last_label, label)
            escena.play(animacion, run_time=t_anim_paso)
            if t_wait_paso > 0:
                escena.wait(t_wait_paso)
            
        last_label, last_tex = label, latex  

    if last_label is not None:
        escena.wait(0.5)
        escena.play(FadeOut(last_label), run_time=tiempo_salida)
        return None
    return last_label


def procesar_algebra_flotante(
    escena,
    fuente,
    ancho_camara,
    posicion="UL",
    remover=False,
    runtime=1.0,
    waittime=1.0,
    tiempo_transformacion=None,
    tiempo_espera=None,
    tiempo_escritura=None,
    tiempos_transformacion=None,
    tiempos_espera=None,
    tiempo_salida=0.5,
    tiempo_replacement_transform=None,
    tiempo_pantalla=None,
    tiempo_entre_pasos=None,
    **kwargs
):
    """
    Renderiza transformaciones algebraicas ancladas en una esquina sin ocultar la gráfica (Desde los labels).
    
    Permite controlar:
    - tiempo_transformacion / tiempos_transformacion: duración del replacement transform entre pasos.
    - tiempo_espera / tiempos_espera: tiempo de espera en pantalla para cada ecuación.
    - tiempo_escritura: tiempo de escritura inicial de la primera ecuación.
    """
    if tiempo_replacement_transform is not None and tiempo_transformacion is None:
        tiempo_transformacion = tiempo_replacement_transform
    if tiempo_pantalla is not None and tiempo_espera is None:
        tiempo_espera = tiempo_pantalla
    if tiempo_entre_pasos is not None and tiempo_espera is None:
        tiempo_espera = tiempo_entre_pasos

    latex_codes = _obtener_codigos_latex(fuente)
    if not latex_codes:
        return None

    n_pasos = len(latex_codes)
    lista_trans, lista_wait = _resolver_tiempos(
        n_pasos,
        tiempo_trans=tiempo_transformacion,
        tiempos_trans=tiempos_transformacion,
        tiempo_wait=tiempo_espera,
        tiempos_wait=tiempos_espera,
        tiempo_escritura=tiempo_escritura,
        runtime_def=runtime,
        waittime_def=waittime
    )
    
    pos_map = {"UL": UL, "UR": UR, "DL": DL, "DR": DR}
    pos_key = str(posicion).upper() if posicion is not None else "UL"
    manim_pos = pos_map.get(pos_key, UL)
    
    buff_x = ancho_camara * 0.03
    buff_y = ancho_camara * 0.03 * (9/16) 
    
    offset = -manim_pos[0] * RIGHT * buff_x + -manim_pos[1] * UP * buff_y
    max_width = ancho_camara * 0.25 
    
    last_label, last_tex = None, None  

    for idx, latex in enumerate(latex_codes):
        fragmentos = extraer_texto_colores(latex)
        textos_limpios = [frag[0] for frag in fragmentos]
        
        label = MathTex(*textos_limpios).set_z_index(30)
        
        for i, frag in enumerate(fragmentos):
            if frag[1].lower() != "white": 
                label[i].set_color(frag[1])
                
        if label.width > max_width:
            label.scale_to_fit_width(max_width)
        else:
            label.scale(ancho_camara / 20)
            
        esquina_camara = escena.camera.frame.get_corner(manim_pos)
        label.move_to(esquina_camara + offset, aligned_edge=manim_pos)
        
        t_anim_paso = lista_trans[idx]
        t_wait_paso = lista_wait[idx]

        if last_label is None:
            escena.play(Write(label), run_time=t_anim_paso)
            if t_wait_paso > 0:
                escena.wait(t_wait_paso)
        else:
            animacion = decidir_animacion(last_tex, latex, last_label, label)
            escena.play(animacion, run_time=t_anim_paso)
            if t_wait_paso > 0:
                escena.wait(t_wait_paso)
            
        last_label, last_tex = label, latex
        
    if remover and last_label is not None:
        escena.play(FadeOut(last_label), run_time=tiempo_salida)
        return None
    return last_label


def procesar_algebra(
    escena,
    fuente,
    ancho_camara,
    posicion=None,
    remover=False,
    tiempo_transformacion=1.0,
    tiempo_espera=1.0,
    tiempo_escritura=None,
    tiempos_transformacion=None,
    tiempos_espera=None,
    tiempo_salida=0.5,
    runtime=None,
    waittime=None,
    tiempo_replacement_transform=None,
    tiempo_pantalla=None,
    tiempo_entre_pasos=None,
    **kwargs
):
    """
    Función unificada para el lector de álgebra.
    
    Toma los mismos argumentos y funciona tanto desde la normalidad (posicion=None o 'center',
    mostrando las ecuaciones en pantalla completa) como desde los labels en las gráficas
    (posicion='UL', 'UR', 'DL', 'DR').
    
    Permite parametrizar con exactitud:
    - Los tiempos de espera en pantalla entre cada paso (tiempo_espera / tiempos_espera / tiempo_pantalla).
    - Lo que se tarda en hacer cada replacement transform (tiempo_transformacion / tiempos_transformacion / tiempo_replacement_transform).
    - El tiempo de escritura inicial (tiempo_escritura).
    """
    if tiempo_replacement_transform is not None:
        tiempo_transformacion = tiempo_replacement_transform
    if tiempo_pantalla is not None:
        tiempo_espera = tiempo_pantalla
    if tiempo_entre_pasos is not None:
        tiempo_espera = tiempo_entre_pasos

    es_flotante = (
        posicion is not None and 
        str(posicion).upper() not in ["CENTER", "CENTRO", "NORMAL", "FULLSCREEN", "NONE", ""]
    )
    
    if es_flotante:
        return procesar_algebra_flotante(
            escena=escena,
            fuente=fuente,
            ancho_camara=ancho_camara,
            posicion=posicion,
            remover=remover,
            runtime=runtime,
            waittime=waittime,
            tiempo_transformacion=tiempo_transformacion,
            tiempo_espera=tiempo_espera,
            tiempo_escritura=tiempo_escritura,
            tiempos_transformacion=tiempos_transformacion,
            tiempos_espera=tiempos_espera,
            tiempo_salida=tiempo_salida,
            **kwargs
        )
    else:
        return procesar_pasos_algebraicos(
            escena=escena,
            fuente=fuente,
            ancho_camara=ancho_camara,
            runtime=runtime if runtime is not None else 1.0,
            waittime=waittime if waittime is not None else 1.0,
            tiempo_transformacion=tiempo_transformacion,
            tiempo_espera=tiempo_espera,
            tiempo_escritura=tiempo_escritura,
            tiempos_transformacion=tiempos_transformacion,
            tiempos_espera=tiempos_espera,
            tiempo_salida=tiempo_salida,
            **kwargs
        )

# Alias de compatibilidad y conveniencia
animar_algebra = procesar_algebra
reproducir_algebra = procesar_algebra
lector_algebra = procesar_algebra