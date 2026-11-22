from manim import ValueTracker, Line

def render_convergencia_secante(escena, plano, accion):
    """
    Controlador paramétrico asíncrono. Amarra la secante, el punto sobre la curva 
    y el punto raíz a una única variable maestra alpha [0 -> 1] para sincronización absoluta.
    """
    f = accion["funcion"]
    x_fijo = accion["x_fijo"]
    x_movil_ini = accion["x_movil_ini"]
    x_movil_fin = accion["x_movil_fin"]
    
    # Recuperamos las entidades físicas desde la memoria de la escena
    secante = escena.objetos.get(accion["id_secante"]) if hasattr(escena, "objetos") else getattr(escena, "objetos_registrados", {}).get(accion["id_secante"])
    p_curva = escena.objetos.get(accion["id_punto_curva"]) if hasattr(escena, "objetos") else getattr(escena, "objetos_registrados", {}).get(accion["id_punto_curva"])
    p_raiz = escena.objetos.get(accion["id_punto_raiz"]) if hasattr(escena, "objetos") else getattr(escena, "objetos_registrados", {}).get(accion["id_punto_raiz"])
    
    y_fijo = f(x_fijo)
    
    # El Reloj Maestro
    alpha = ValueTracker(0.0)
    
    def get_x_actual():
        return x_movil_ini + alpha.get_value() * (x_movil_fin - x_movil_ini)

    def update_punto_curva(m):
        x_act = get_x_actual()
        m.move_to(plano.c2p(x_act, f(x_act)))

    def update_secante(m):
        x_act = get_x_actual()
        y_act = f(x_act)
        if abs(x_act - x_fijo) < 1e-5:
            x_act += 1e-5
            
        m_slope = (y_act - y_fijo) / (x_act - x_fijo)
        
        # Proyectamos la línea hasta los bordes infinitos de la pantalla
        x_min, x_max = plano.x_range[0], plano.x_range[1]
        y_min = m_slope * (x_min - x_fijo) + y_fijo
        y_max = m_slope * (x_max - x_fijo) + y_fijo
        
        # Mutación geométrica en tiempo real
        nueva_linea = Line(plano.c2p(x_min, y_min), plano.c2p(x_max, y_max), color=m.get_color())
        m.become(nueva_linea)

    def update_punto_raiz(m):
        x_act = get_x_actual()
        y_act = f(x_act)
        if abs(x_act - x_fijo) < 1e-5:
            x_act += 1e-5
            
        m_slope = (y_act - y_fijo) / (x_act - x_fijo)
        # Cálculo algebraico vivo del cruce con Y=0
        x_cruce = x_fijo - (y_fijo / m_slope) if m_slope != 0 else x_fijo
        m.move_to(plano.c2p(x_cruce, 0.0))

    # Anclamos los Updaters
    if p_curva is not None:
        p_curva.add_updater(update_punto_curva)
    if secante is not None:
        secante.add_updater(update_secante)
    if p_raiz is not None:
        p_raiz.add_updater(update_punto_raiz)
    
    # Detonamos el recorrido paramétrico (Esto mueve las 3 cosas a la vez)
    escena.play(alpha.animate.set_value(1.0), run_time=accion["t_anim"])
    
    # Purgamos la memoria temporal
    if p_curva is not None:
        p_curva.clear_updaters()
    if secante is not None:
        secante.clear_updaters()
    if p_raiz is not None:
        p_raiz.clear_updaters()
    escena.wait(accion["t_wait"])
