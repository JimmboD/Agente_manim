import math
from manim import YELLOW, WHITE
from Planos.generar_plano import AnimadorGrafico
from manim import *

# ==========================================
# CONFIGURACIÓN DE LA FUNCIÓN
# ==========================================
def f_objetivo(x: float) -> float:
    return math.exp(x) - 3 * (x**2)

LABEL_FUNCION = r"$$f(x) = e^x - 3x^2$$"

def generar_secante(x0, y0, x1, y1):
    return lambda x: (y1 - y0) / (x1 - x0) * (x - x0) + y0 if abs(x1 - x0) > 1e-5 else y0

if __name__ == "__main__":
    
    # Inicializamos la escena
    escena = AnimadorGrafico(f_objetivo, x_min=-0.5, x_max=2.0)
    
    # Etiqueta fija de la función en la esquina inferior derecha
    escena.agregar_algebra_flotante(LABEL_FUNCION, posicion="DR", remover_al_final=False)
    
    a, b = 0.0, 1.5
    fa, fb = f_objetivo(a), f_objetivo(b)
    
    # ==========================================
    # [00:00 - 00:16] FASE 1: REGLA FALSA 
    # ==========================================
    escena.agregar_algebra_flotante(r"$$\text{Regla Falsa}$$", posicion="UL", remover_al_final=True)
    
    escena.agregar_punto(a, fa, color=YELLOW, id="A_rf", tiempo_animacion=0.5, tiempo_espera=0.1)
    escena.agregar_punto(b, fb, color=YELLOW, id="B_rf", tiempo_animacion=0.5, tiempo_espera=0.1)
    
    c_rf = b - fb * ((b - a) / (fb - fa))
    fc_rf = f_objetivo(c_rf)
    
    escena.agregar_funcion(generar_secante(a, fa, b, fb), color=YELLOW, id="secante", tiempo_animacion=1.0)
    escena.agregar_punto(c_rf, 0.0, color=WHITE, label=False, id="punto_raiz_rf", tiempo_animacion=0.5)
    
    # Proyección Regla Falsa
    escena.animar_linea_punteada(
        x1_ini=c_rf, x1_fin=c_rf, x2_ini=c_rf, x2_fin=c_rf, 
        y1_ini=0.0, y2_ini=f_objetivo, 
        color=WHITE, id="proy_c_rf", tiempo_animacion=0.8
    )
    
    # Eliminamos la proyección antes de mover el punto
    escena.eliminar_objeto("proy_c_rf", animacion="FadeOut", tiempo_animacion=0.5, tiempo_espera=0.1)
    
    if fa * fc_rf < 0:
        escena.animar_convergencia_parametrica(
            funcion=f_objetivo, x_fijo=a, x_movil_ini=b, x_movil_fin=c_rf,
            id_secante="secante", id_punto_curva="B_rf", id_punto_raiz="punto_raiz_rf",
            tiempo_animacion=2.5, tiempo_espera=1.0
        )
    else:
        escena.animar_convergencia_parametrica(
            funcion=f_objetivo, x_fijo=b, x_movil_ini=a, x_movil_fin=c_rf,
            id_secante="secante", id_punto_curva="A_rf", id_punto_raiz="punto_raiz_rf",
            tiempo_animacion=2.5, tiempo_espera=1.0
        )

    # ==========================================
    # [00:16 - 00:27] FASE 2: BISECCIÓN
    # ==========================================
    with escena.bloque_paralelo(tiempo_animacion=1.0):
        # Limpiamos Regla Falsa
        escena.eliminar_objeto("secante")
        escena.eliminar_objeto("A_rf")
        escena.eliminar_objeto("B_rf")
        escena.eliminar_objeto("punto_raiz_rf")
        
        escena.agregar_algebra_flotante(r"$$\text{Bisección}$$", posicion="UL", remover_al_final=True)
        
        # Puntos Bisección y recta del intervalo en AMARILLO
        escena.agregar_punto(a, fa, color=YELLOW, id="A_bis")
        escena.agregar_punto(b, fb, color=YELLOW, id="B_bis")
        escena.agregar_funcion(lambda x: 0, x_min=a, x_max=b, color=YELLOW, id="intervalo_bis")
        
    c_bis = (a + b) / 2.0
    fc_bis = f_objetivo(c_bis)
    escena.agregar_punto(c_bis, 0.0, color=WHITE, label=False, id="punto_c_bis", tiempo_animacion=0.8)
    
    # Proyección Bisección
    escena.animar_linea_punteada(
        x1_ini=c_bis, x1_fin=c_bis, x2_ini=c_bis, x2_fin=c_bis, 
        y1_ini=0.0, y2_ini=f_objetivo, 
        color=WHITE, id="proy_c_bis", tiempo_animacion=0.8
    )
    
    # Eliminamos proyecciones temporales antes de iterar
    with escena.bloque_paralelo(tiempo_animacion=0.5, tiempo_espera=0.1):
        escena.eliminar_objeto("proy_c_bis")
        escena.eliminar_objeto("punto_c_bis")

    # Mover el punto sobre la curva Y acortar el intervalo simultáneamente
    with escena.bloque_paralelo(tiempo_animacion=2.0, tiempo_espera=1.0):
        if fa * fc_bis < 0:
            escena.animar_punto_sobre_curva(x_inicio=b, x_fin=c_bis, funcion=f_objetivo, color=YELLOW, id="B_bis")
            escena.transformar_objeto(origen="intervalo_bis", tipo_destino="funcion", funcion=lambda x: 0, x_min=a, x_max=c_bis, color=YELLOW, id_destino="intervalo_bis")
        else:
            escena.animar_punto_sobre_curva(x_inicio=a, x_fin=c_bis, funcion=f_objetivo, color=YELLOW, id="A_bis")
            escena.transformar_objeto(origen="intervalo_bis", tipo_destino="funcion", funcion=lambda x: 0, x_min=c_bis, x_max=b, color=YELLOW, id_destino="intervalo_bis")

    # ==========================================
    # [00:27] CIERRE Y TRANSICIÓN
    # ==========================================
    # Se reduce el tiempo a 0.5s para agilizar el corte
    escena.desvanecer_todo(tiempo_animacion=0.5, tiempo_espera=0.5)
    
    # Aparece un nuevo plano limpio, sin curva ni marcas extra
    escena.fade_in_plano(
        x_min=-0.5, 
        x_max=2.0,
        dibujar_grafica=False, 
        tiempo_animacion=1.5, 
        tiempo_espera=1.0
    )

    # ==========================================
    # [00:30 - 00:37] DELAY INICIAL (7 SEGUNDOS)
    # Narrativa: "Genuinamente desconozco qué algoritmo se inventó primero pero he de reconocer que al menos en mi cabeza, este método se parece demasiado a la bisección."
    # ==========================================
    c_val = b 
    fc_val = f_objetivo(c_val)

    # Creamos los nodos "semilla" en color NEGRO (#000000) para que sean completamente invisibles en el fondo.
    escena.agregar_punto(a, -0.5, color="#000000", id="dummy_a", tiempo_animacion=0.1, tiempo_espera=0.0)
    
    # Este dummy carga con el peso del gran delay de 7 segundos antes de continuar.
    escena.agregar_punto(c_val, -0.5, color="#000000", id="dummy_c", tiempo_animacion=0.1, tiempo_espera=7.0)

    # ==========================================
    # [00:37 - 00:46] EXTREMOS INICIALES 'a' Y 'c'
    # Narrativa: "Para empezar diremos que en este caso también se trata de un algoritmo cerrado..."
    # ==========================================
    # Los puntos y sus etiquetas aparecen con calma (2s de entrada + 7s de contemplación = 9s)
    with escena.bloque_paralelo(tiempo_animacion=2.0, tiempo_espera=7.0):
        # Puntos iniciales sobre el eje X (y = 0)
        escena.agregar_punto(a, 0.0, color=YELLOW, id="punto_a")
        escena.agregar_punto(c_val, 0.0, color=YELLOW, id="punto_c")
        
        # Transmutamos los nodos negros invisibles directamente a texto
        escena.transformar_objeto(origen="dummy_a", tipo_destino="texto", texto=r"$$a$$", posicion=(a, -0.5), id_destino="label_a")
        escena.transformar_objeto(origen="dummy_c", tipo_destino="texto", texto=r"$$c$$", posicion=(c_val, -0.5), id_destino="label_c")

    # ==========================================
    # [00:46 - 00:49] PARPADEO DE LA FUNCIÓN
    # Narrativa: "Esto lo podemos hacer con una evaluación."
    # ==========================================
    # Aparece la función en RED lenta y sutilmente (1.5s entrada + 0.5s pausa)
    escena.agregar_funcion(f_objetivo, color="RED", id="funcion_fantasma", tiempo_animacion=1.5, tiempo_espera=0.5)
    
    # Desaparece (1s salida + AÑADIMOS 2.5 SEGUNDOS DE DELAY ANTES DE PROYECTAR)
    escena.eliminar_objeto("funcion_fantasma", animacion="FadeOut", tiempo_animacion=1.0, tiempo_espera=2.5)

    # ==========================================
    # [00:49 - 00:54] EVALUACIÓN Y PROYECCIÓN
    # Narrativa: "Si escogemos dos valores y dan signos diferentes, en principio deberíamos tener una raíz en ese punto."
    # ==========================================
    # Todo se mueve fluidamente hacia sus respectivas alturas (3s animación + 1s pausa)
    with escena.bloque_paralelo(tiempo_animacion=3.0, tiempo_espera=1.0):
        # Trazamos las proyecciones desde el eje X hasta la altura evaluada
        escena.animar_linea_punteada(
            x1_ini=a, x1_fin=a, x2_ini=a, x2_fin=a, 
            y1_ini=0.0, y2_ini=fa, color=WHITE, id="proy_a"
        )
        escena.animar_linea_punteada(
            x1_ini=c_val, x1_fin=c_val, x2_ini=c_val, x2_fin=c_val, 
            y1_ini=0.0, y2_ini=fc_val, color=WHITE, id="proy_c"
        )
        
        # Movemos los puntos amarillos físicamente hasta esas alturas
        escena.transformar_objeto(origen="punto_a", tipo_destino="punto", x=a, y=fa, color=YELLOW, id_destino="punto_a")
        escena.transformar_objeto(origen="punto_c", tipo_destino="punto", x=c_val, y=fc_val, color=YELLOW, id_destino="punto_c")

    # Mutación de etiquetas para incluir el signo y acompañar al punto, con un delay fuerte de contemplación
    with escena.bloque_paralelo(tiempo_animacion=1.5, tiempo_espera=3.0):
        escena.transformar_objeto(
            origen="label_a", tipo_destino="texto", 
            texto=r"$$a (+)$$", posicion=(a, fa + 0.4), id_destino="label_a"
        )
        escena.transformar_objeto(
            origen="label_c", tipo_destino="texto", 
            texto=r"$$c (-)$$", posicion=(c_val, fc_val - 0.4), id_destino="label_c"
        )

    # ==========================================
    # [00:54 - 00:59] CONSTRUCCIÓN DE LA RECTA SECANTE
    # Narrativa: "Con el conocimiento de estos valores podemos construir una recta entre dos puntos."
    # ==========================================
    with escena.bloque_paralelo(tiempo_animacion=1.5, tiempo_espera=1.0):
        escena.eliminar_objeto("label_a", animacion="FadeOut")
        escena.eliminar_objeto("label_c", animacion="FadeOut")

    # Recta en YELLOW (amarillo)
    escena.agregar_funcion(
        generar_secante(a, fa, c_val, fc_val), 
        color=YELLOW, 
        id="secante", 
        tiempo_animacion=2.0, 
        tiempo_espera=0.5
    )

    # ==========================================
    # [00:59 - 01:05] ECUACIÓN GENERAL DE LA RECTA
    # Narrativa: "Para construir cualquier recta solo basta con recordar que la ecuación general de una recta es y = mx + b."
    # ==========================================
    # Inyectamos el HUD inicial que servirá como base para la mutación
    escena.agregar_algebra_flotante(
        fuente_o_texto=r"$$y = mx + b$$", 
        posicion="UL", 
        remover_al_final=False, 
        id="eq_recta", 
        tiempo_animacion=2.0, 
        tiempo_espera=4.0
    )

    # ==========================================
    # [01:05 - 01:13] PENDIENTE COMO DELTAS
    # Narrativa: "La pendiente de una recta es cuánto cambio de altura hay por cada unidad en el eje x..."
    # ==========================================
    # AUMENTAMOS EL TIEMPO DE ESPERA A 8.5 SEGUNDOS (+1.5s extra)
    with escena.bloque_paralelo(tiempo_animacion=3.0, tiempo_espera=10):
        escena.eliminar_objeto("proy_a", animacion="FadeOut")
        escena.eliminar_objeto("proy_c", animacion="FadeOut")
        
        # Usamos tu flamante método dedicado para metamorfosis limpia
        escena.transformar_algebra_flotante(
            id_origen="eq_recta", 
            nuevo_texto=r"$$y = \left(\frac{\Delta y}{\Delta x}\right)x + b$$", 
            posicion="UL",
            id_destino="eq_recta"
        )
        
        # Nacen las llaves SOLO con los deltas
        escena.animar_llave(
            x1_ini=a, x1_fin=a, x2_ini=c_val, x2_fin=c_val, 
            y1_ini=fc_val, y2_ini=fc_val, 
            texto=r"\Delta x", direccion=DOWN, color=WHITE, id="llave_x"
        )
        escena.animar_llave(
            x1_ini=a, x1_fin=a, x2_ini=a, x2_fin=a, 
            y1_ini=fc_val, y2_ini=fa, 
            texto=r"\Delta y", direccion=LEFT, color=WHITE, id="llave_y"
        )

    # ==========================================
    # [01:13 - 01:21] EXPANSIÓN A LAS RESTAS
    # Narrativa: "Si observas el gráfico podrás notar que las variaciones solo son restar el punto final menos el inicial..."
    # ==========================================
    # AUMENTAMOS EL TIEMPO DE ESPERA A 12.0 SEGUNDOS (+4.0s extra)
    with escena.bloque_paralelo(tiempo_animacion=3.0, tiempo_espera=7.0):
        # Segunda mutación limpia
        escena.transformar_algebra_flotante(
            id_origen="eq_recta", 
            nuevo_texto=r"$$y = \left(\frac{f(c) - f(a)}{c - a}\right)x + b$$", 
            posicion="UL",
            id_destino="eq_recta"
        )
        
        # Sustituimos las llaves cortas por las largas
        escena.eliminar_objeto("llave_x", animacion="FadeOut")
        escena.eliminar_objeto("llave_y", animacion="FadeOut")
        
        escena.animar_llave(
            x1_ini=a, x1_fin=a, x2_ini=c_val, x2_fin=c_val, 
            y1_ini=fc_val, y2_ini=fc_val, 
            texto=r"\Delta x = c - a", direccion=DOWN, color=WHITE, id="llave_x_larga"
        )
        escena.animar_llave(
            x1_ini=a, x1_fin=a, x2_ini=a, x2_fin=a, 
            y1_ini=fc_val, y2_ini=fa, 
            texto=r"\Delta y = f(c) - f(a)", direccion=LEFT, color=WHITE, id="llave_y_larga"
        )

        # ==========================================
    # [01:21 - 01:26] OBJETIVO: ENCONTRAR 'b'
    # Narrativa: "Nuestro objetivo ahora es encontrar el valor de la ordenada al origen, es decir, la letra b..."
    # ==========================================
    # Transformamos el HUD SOLO para pintar la 'b' de amarillo
    escena.transformar_algebra_flotante(
        id_origen="eq_recta", 
        nuevo_texto=r"$$y = \left(\frac{f(c) - f(a)}{c - a}\right)x + \textcolor{YELLOW}{b}$$", 
        posicion="UL",
        tiempo_animacion=1.5,
        tiempo_espera=2.0
    )

    # ==========================================
    # [01:26 - 01:31] LIMPIEZA DEL GRÁFICO
    # Narrativa: "Para lograrlo sin abrumarnos, limpiemos un poco la gráfica..."
    # ==========================================
    # Fade out de las llaves
    with escena.bloque_paralelo(tiempo_animacion=1.5, tiempo_espera=1.0):
        escena.eliminar_objeto("llave_x_larga", animacion="FadeOut")
        escena.eliminar_objeto("llave_y_larga", animacion="FadeOut")

    # ==========================================
    # [01:31 - 01:40] EXPLORACIÓN DESDE EL ORIGEN HASTA 'c'
    # Narrativa: "Para despejarla, evaluaremos la ecuación en un punto que ya conocemos sobre la recta, por ejemplo el punto c."
    # ==========================================
    f_sec = generar_secante(a, fa, c_val, fc_val)
    b_val = f_sec(0.0) 
    
    # Nace el punto explorador en el origen (0,0)
    escena.agregar_punto(0.0, 0.0, color=WHITE, id="punto_explorador", tiempo_animacion=0.5, tiempo_espera=0.5)
    
    # Viaje del punto sobre el eje X y su proyección vertical
    with escena.bloque_paralelo(tiempo_animacion=3.0, tiempo_espera=1.0):
        escena.transformar_objeto(
            origen="punto_explorador", tipo_destino="punto", 
            x=c_val, y=0.0, color=WHITE, id_destino="punto_explorador"
        )
        
        escena.animar_linea_punteada(
            x1_ini=0.0, x1_fin=c_val, 
            x2_ini=0.0, x2_fin=c_val, 
            y1_ini=0.0, y1_fin=0.0, 
            y2_ini=b_val, y2_fin=fc_val,
            color=WHITE, id="proy_movil"
        )
    
    # ==========================================
    # [01:40 - 01:45] APARICIÓN DE LAS COORDENADAS
    # Narrativa: "Cuando llegamos a c, sabemos exactamente que su altura es f(c)."
    # ==========================================
    # Aparece amablemente el label a un lado del punto
    escena.agregar_punto(c_val, fc_val, color="#000000", id="dummy_label_c", tiempo_animacion=0.1)
    escena.transformar_objeto(
        origen="dummy_label_c", tipo_destino="texto", 
        texto=r"$$(c, f(c))$$", 
        posicion=(c_val + 0.4, fc_val - 0.4), 
        id_destino="label_punto_c",
        tiempo_animacion=1.0, 
        tiempo_espera=1.0
    )

    # ==========================================
    # [01:45 - 01:52] SUSTITUCIÓN DESDE LAS COORDENADAS
    # Narrativa: "Si sustituimos 'y' por f(c) y 'x' por c..."
    # ==========================================
    # 1. El label de las coordenadas vuela hacia el HUD para sustituir a 'x' e 'y'
    with escena.bloque_paralelo(tiempo_animacion=2.0, tiempo_espera=2.0):
        escena.eliminar_objeto("eq_recta", animacion="FadeOut")
        
        escena.transformar_algebra_flotante(
            id_origen="label_punto_c", 
            nuevo_texto=r"$$\textcolor{YELLOW}{f(c)} = \left(\frac{f(c) - f(a)}{c - a}\right)\textcolor{YELLOW}{c} + b$$", 
            posicion="UL", 
            id_destino="eq_recta" 
        )
    
    # 2. Despejamos 'b' (resaltando el movimiento)
    escena.transformar_algebra_flotante(
        id_origen="eq_recta", 
        nuevo_texto=r"$$b = \textcolor{YELLOW}{f(c) - \left(\frac{f(c) - f(a)}{c - a}\right)c}$$", 
        posicion="UL", tiempo_animacion=1.5, tiempo_espera=2.0
    )

    # ==========================================
    # [01:52 - 02:00] SUSTITUCIÓN FINAL Y FACTORIZACIÓN
    # Narrativa: "Y ahora sustituimos esa 'b' en nuestra ecuación original y factorizamos la pendiente..."
    # ==========================================
    # 3. Sustituimos 'b' de vuelta en la ecuación general (y = mx + b)
    escena.transformar_algebra_flotante(
        id_origen="eq_recta", 
        nuevo_texto=r"$$y = \left(\frac{f(c) - f(a)}{c - a}\right)x + \textcolor{YELLOW}{f(c) - \left(\frac{f(c) - f(a)}{c - a}\right)c}$$", 
        posicion="UL", tiempo_animacion=2.0, tiempo_espera=6.0
    )
    
    # 4. Factorizamos la pendiente PRIMERO
    escena.transformar_algebra_flotante(
        id_origen="eq_recta", 
        nuevo_texto=r"$$y = \textcolor{YELLOW}{\left(\frac{f(c) - f(a)}{c - a}\right)(x - c)} + f(c)$$", 
        posicion="UL", id_destino="eq_recta",
        tiempo_animacion=2.0, tiempo_espera=2.0
    )
    
    # 5. DESPUÉS revelamos la forma Punto-Pendiente genérica para compararla
    escena.agregar_algebra_flotante(
        fuente_o_texto=r"$$y - y_1 = m(x - x_1)$$", 
        posicion="UR", remover_al_final=False, id="forma_punto_pendiente",
        tiempo_animacion=1.5, tiempo_espera=12.0
    )
        
    # 6. Limpiamos la forma genérica (revelación terminada) y le quitamos el amarillo al HUD principal
    with escena.bloque_paralelo(tiempo_animacion=1.5, tiempo_espera=8.0):
        escena.eliminar_objeto("forma_punto_pendiente", animacion="FadeOut")
        escena.transformar_algebra_flotante(
            id_origen="eq_recta", 
            nuevo_texto=r"$$y = \left(\frac{f(c) - f(a)}{c - a}\right)(x - c) + f(c)$$", 
            posicion="UL"
        )

    # ==========================================
    # [02:00 - 02:10] PUNTO DE PRUEBA Y DESLIZAMIENTO A LA RAÍZ
    # Narrativa: "Con esta ecuación, podemos encontrar la intersección con el eje X..."
    # ==========================================
    f_sec = generar_secante(a, fa, c_val, fc_val)
    y_25 = f_sec(2.5)
    
    escena.agregar_punto(2.5, y_25, color=WHITE, id="punto_prueba_secante", tiempo_animacion=1.0, tiempo_espera=3.0)
    
    m = (fc_val - fa) / (c_val - a)
    raiz_sec = c_val - (fc_val / m)
    
    escena.transformar_objeto(
        origen="punto_prueba_secante", tipo_destino="punto", 
        x=raiz_sec, y=0.0, color=WHITE, id_destino="punto_raiz_secante",
        tiempo_animacion=5.5, tiempo_espera=20
    )

    # ==========================================
    # [02:10 - 02:12] TRANSICIÓN: OCULTAR REGLA FALSA
    # Narrativa: "Si comparamos esto por un momento con el método de bisección..."
    # ==========================================
    # Transición más rápida
    with escena.bloque_paralelo(tiempo_animacion=1.0, tiempo_espera=0.5):
        escena.eliminar_objeto("secante", animacion="FadeOut")
        escena.eliminar_objeto("eq_recta", animacion="FadeOut")
        escena.eliminar_objeto("punto_raiz_secante", animacion="FadeOut")
        escena.eliminar_objeto("proy_movil", animacion="FadeOut") 
        escena.eliminar_objeto("label_punto_c", animacion="FadeOut")
        escena.eliminar_objeto("punto_explorador", animacion="FadeOut")
        escena.eliminar_objeto("punto_a", animacion="FadeOut")
        escena.eliminar_objeto("punto_c", animacion="FadeOut")

    # ==========================================
    # [02:12 - 02:20] BISECCIÓN EN ACCIÓN (1 sola iteración rápida)
    # Narrativa: "En la bisección, partimos el intervalo a la mitad a ciegas..."
    # ==========================================
    with escena.bloque_paralelo(tiempo_animacion=1.0, tiempo_espera=0.5):
        # ¡La curva aparece en ROJO!
        escena.agregar_funcion(f_objetivo, color=RED, id="curva_principal")
        escena.agregar_algebra_flotante(
            fuente_o_texto=r"$$f(x) = e^x - 3x^2$$", 
            posicion="DR", id="label_funcion", remover_al_final=False
        )

    a_bis, b_bis = a, c_val
    fa_bis, fb_bis = f_objetivo(a_bis), f_objetivo(b_bis)
    
    # Línea de intervalo rápida
    escena.animar_linea_punteada(
        x1_ini=a_bis, x1_fin=b_bis, x2_ini=a_bis, x2_fin=b_bis, 
        y1_ini=0.0, y1_fin=0.0, y2_ini=0.0, y2_fin=0.0,
        color=WHITE, id="linea_intervalo_bis", tiempo_animacion=0.8
    )
    
    # Extremos amarillos al instante
    escena.agregar_punto(a_bis, fa_bis, color="#FFFF00", id="punto_A_bis", tiempo_animacion=0.5)
    escena.agregar_punto(b_bis, fb_bis, color="#FFFF00", id="punto_B_bis", tiempo_animacion=0.5, tiempo_espera=0.5)
    
    # === ÚNICA ITERACIÓN ===
    c_bis = (a_bis + b_bis) / 2.0
    fc_bis = f_objetivo(c_bis)
    
    texto_hud = f"""
    $$\\text{{Bisección - Iteración: 1}}$$
    $$c_{{1}} = \\frac{{{a_bis:.4f} + {b_bis:.4f}}}{{2}} = {c_bis:.4f}$$
    $$f(c_{{1}}) \\approx {fc_bis:.4f}$$
    $$\\text{{Error: N/A}}$$
    """
    # Aparece la cuenta del punto intermedio más veloz
    escena.agregar_algebra_flotante(texto_hud, posicion="UL", remover_al_final=True, tiempo_animacion=0.8, tiempo_espera=1.0)
    
    # Proyección fugaz
    escena.agregar_punto(c_bis, 0.0, color="#FFFFFF", label=False, id="punto_c_1", tiempo_animacion=0.4)
    escena.animar_linea_punteada(
        x1_ini=c_bis, x1_fin=c_bis, x2_ini=c_bis, x2_fin=c_bis, y1_ini=0.0, y2_ini=fc_bis, 
        color="#FFFFFF", id="proy_c_1", tiempo_animacion=0.5
    )
    escena.eliminar_objeto(id="proy_c_1", animacion="Uncreate", tiempo_animacion=0.4)
    escena.eliminar_objeto(id="punto_c_1", animacion="FadeOut", tiempo_animacion=0.4, tiempo_espera=0.2)
    
    # Traslación veloz de la frontera
    if fa_bis * fc_bis < 0:
        b_viejo = b_bis
        b_bis, fb_bis = c_bis, fc_bis
        with escena.bloque_paralelo(tiempo_animacion=1.0, tiempo_espera=0.5):
            escena.animar_punto_sobre_curva(x_inicio=b_viejo, x_fin=b_bis, funcion=f_objetivo, color="#FFFF00", id="punto_B_bis")
            escena.eliminar_objeto("linea_intervalo_bis", animacion="FadeOut")
            escena.animar_linea_punteada(
                x1_ini=a_bis, x1_fin=b_bis, x2_ini=a_bis, x2_fin=b_bis, 
                y1_ini=0.0, y1_fin=0.0, y2_ini=0.0, y2_fin=0.0,
                color=WHITE, id="linea_intervalo_bis"
            )
    else:
        a_viejo = a_bis
        a_bis, fa_bis = c_bis, fc_bis
        with escena.bloque_paralelo(tiempo_animacion=1.0, tiempo_espera=0.5):
            escena.animar_punto_sobre_curva(x_inicio=a_viejo, x_fin=a_bis, funcion=f_objetivo, color="#FFFF00", id="punto_A_bis")
            escena.eliminar_objeto("linea_intervalo_bis", animacion="FadeOut")
            escena.animar_linea_punteada(
                x1_ini=a_bis, x1_fin=b_bis, x2_ini=a_bis, x2_fin=b_bis, 
                y1_ini=0.0, y1_fin=0.0, y2_ini=0.0, y2_fin=0.0,
                color=WHITE, id="linea_intervalo_bis"
            )

    # ==========================================
    # [02:20 - 02:24] LIMPIEZA Y REGRESO A REGLA FALSA
    # Narrativa: "Pero la Regla Falsa es mucho más inteligente..."
    # ==========================================
    with escena.bloque_paralelo(tiempo_animacion=1.0, tiempo_espera=0.5):
        escena.eliminar_objeto("label_funcion", animacion="FadeOut")
        escena.eliminar_objeto("linea_intervalo_bis", animacion="FadeOut")
        escena.eliminar_objeto("punto_A_bis", animacion="FadeOut")
        escena.eliminar_objeto("punto_B_bis", animacion="FadeOut")

    # Restauramos la Regla Falsa
    with escena.bloque_paralelo(tiempo_animacion=1.0, tiempo_espera=1.5):
        escena.agregar_punto(a, fa, color=YELLOW, id="punto_a")
        escena.agregar_punto(c_val, fc_val, color=YELLOW, id="punto_c")
        escena.agregar_funcion(f_sec, color=YELLOW, id="secante")
        escena.agregar_algebra_flotante(
            fuente_o_texto=r"$$y = \left(\frac{f(c) - f(a)}{c - a}\right)(x - c) + f(c)$$", 
            posicion="UL", remover_al_final=False, id="eq_recta"
        )
        escena.agregar_punto(raiz_sec, 0.0, color=WHITE, id="punto_raiz_secante")

    # ==========================================
    # [02:40 - 02:45] APARICIÓN DE LA RAÍZ (x, 0)
    # Narrativa: "Esta intersección en el eje X tiene como coordenadas (x, 0)..."
    # ==========================================
    # Aparece amablemente el label de la raíz a un lado del punto amarillo
    escena.agregar_punto(raiz_sec, 0.0, color="#000000", id="dummy_label_raiz", tiempo_animacion=0.1)
    escena.transformar_objeto(
        origen="dummy_label_raiz", tipo_destino="texto", 
        texto=r"$$(x, 0)$$", 
        posicion=(raiz_sec + 0.3, -0.4), # Ligeramente abajo y a la derecha del punto
        id_destino="label_punto_raiz",
        tiempo_animacion=1.0, 
        tiempo_espera=2.0
    )

    # ==========================================
    # [02:45 - 02:52] SUSTITUCIÓN DE LA RAÍZ EN LA ECUACIÓN
    # Narrativa: "Si sustituimos estas coordenadas en nuestra ecuación..."
    # ==========================================
    with escena.bloque_paralelo(tiempo_animacion=2.0, tiempo_espera=4.0):
        # Desvanecemos la ecuación anterior
        escena.eliminar_objeto("eq_recta", animacion="FadeOut")
        
        # El label vuela desde la gráfica hacia la esquina superior izquierda
        # Usamos transformar_algebra_flotante para que parsee los colores correctamente
        escena.transformar_algebra_flotante(
            id_origen="label_punto_raiz", 
            nuevo_texto=r"$$\textcolor{YELLOW}{0} = \left(\frac{f(c) - f(a)}{c - a}\right)(\textcolor{YELLOW}{x} - c) + f(c)$$", 
            posicion="UL", 
            id_destino="eq_recta"
        )

    # ==========================================
    # [02:52 - 03:10] DESPEJE PASO A PASO (FÓRMULA REGLA FALSA)
    # Narrativa: "Ahora simplemente despejamos x. Restamos f(c)... multiplicamos por el inverso... y sumamos c."
    # ==========================================
    # Paso 1: Restar f(c)
    escena.transformar_algebra_flotante(
        id_origen="eq_recta", 
        nuevo_texto=r"$$-\textcolor{YELLOW}{f(c)} = \left(\frac{f(c) - f(a)}{c - a}\right)(x - c)$$", 
        posicion="UL", tiempo_animacion=1.5, tiempo_espera=2.0
    )

    # Paso 2: Multiplicar por el inverso multiplicativo de la pendiente
    escena.transformar_algebra_flotante(
        id_origen="eq_recta", 
        nuevo_texto=r"$$-\textcolor{YELLOW}{\left(\frac{c - a}{f(c) - f(a)}\right)}f(c) = x - c$$", 
        posicion="UL", tiempo_animacion=2.0, tiempo_espera=2.0
    )

    # Paso 3: Sumar 'c'
    escena.transformar_algebra_flotante(
        id_origen="eq_recta", 
        nuevo_texto=r"$$\textcolor{YELLOW}{c} - \left(\frac{c - a}{f(c) - f(a)}\right)f(c) = x$$", 
        posicion="UL", tiempo_animacion=1.5, tiempo_espera=2.0
    )

    # Paso 4: Dejar todo en blanco (Y voltearlo elegantemente para tener la 'x' a la izquierda)
    escena.transformar_algebra_flotante(
        id_origen="eq_recta", 
        nuevo_texto=r"$$x = c - \left(\frac{c - a}{f(c) - f(a)}\right)f(c)$$", 
        posicion="UL", tiempo_animacion=1.5, tiempo_espera=4.0
    )

    # ==========================================
    # [03:10 - 03:18] PROYECCIÓN HACIA LA CURVA
    # Narrativa: "Evaluamos esta nueva aproximación proyectándola en nuestra función..."
    # ==========================================
    x_nueva = raiz_sec
    y_nueva = f_objetivo(x_nueva)

    # 1. Proyección vertical desde la raíz en el eje X hasta tocar la curva
    escena.animar_linea_punteada(
        x1_ini=x_nueva, x1_fin=x_nueva, x2_ini=x_nueva, x2_fin=x_nueva, 
        y1_ini=0.0, y2_ini=y_nueva,
        color=WHITE, id="proy_nueva_raiz", tiempo_animacion=1.5
    )
    
    # Nace el nuevo punto evaluado sobre la curva
    escena.agregar_punto(x_nueva, y_nueva, color=YELLOW, id="punto_nueva_raiz", tiempo_animacion=0.5, tiempo_espera=3.0)

    # ==========================================
    # [03:18 - 03:24] ANÁLISIS DE SIGNOS
    # Narrativa: "Para saber qué punto reemplazar, verificamos los signos. Izquierda es (+), derecha es (-)..."
    # ==========================================
    # 2. Creamos los nodos invisibles SECUENCIALMENTE ANTES del bloque paralelo para evitar que Manim colapse
    escena.agregar_punto(a, fa, color="#000000", id="dummy_izq", tiempo_animacion=0.1)
    escena.agregar_punto(c_val, fc_val, color="#000000", id="dummy_der", tiempo_animacion=0.1)
    escena.agregar_punto(x_nueva, y_nueva, color="#000000", id="dummy_nuevo", tiempo_animacion=0.1)

    # Ahora sí, metamorfosis a texto simultánea
    with escena.bloque_paralelo(tiempo_animacion=1.5, tiempo_espera=3.0):
        # Signo del punto izquierdo 'a' (f(0) = 1 -> Positivo)
        escena.transformar_objeto(
            origen="dummy_izq", tipo_destino="texto", 
            texto=r"$$(+)$$", posicion=(a - 0.3, fa + 0.3), id_destino="label_signo_izq"
        )
        
        # Signo del punto derecho 'c' (f(1.5) = -2.27 -> Negativo)
        escena.transformar_objeto(
            origen="dummy_der", tipo_destino="texto", 
            texto=r"$$(-)$$", posicion=(c_val + 0.3, fc_val + 0.3), id_destino="label_signo_der"
        )
        
        # Signo del nuevo punto evaluado (f(0.46) = 0.94 -> Positivo)
        escena.transformar_objeto(
            origen="dummy_nuevo", tipo_destino="texto", 
            texto=r"$$(+)$$", posicion=(x_nueva - 0.3, y_nueva + 0.3), id_destino="label_signo_nuevo"
        )

    # ==========================================
    # [03:24 - 03:30] ACTUALIZACIÓN DEL LÍMITE
    # Narrativa: "Como nuestro nuevo punto es positivo (+), toma el lugar del antiguo límite izquierdo (+)."
    # ==========================================
    # 3. Movemos el punto correspondiente a través de la curva
    with escena.bloque_paralelo(tiempo_animacion=2.5, tiempo_espera=22.0):
        # Desvanecemos la proyección y los labels temporales
        escena.eliminar_objeto("proy_nueva_raiz", animacion="FadeOut")
        escena.eliminar_objeto("punto_nueva_raiz", animacion="FadeOut") 
        escena.eliminar_objeto("label_signo_nuevo", animacion="FadeOut")
        
        # Limpiamos también el eje X y la secante vieja
        escena.eliminar_objeto("secante", animacion="FadeOut")
        escena.eliminar_objeto("punto_raiz_secante", animacion="FadeOut")
        escena.eliminar_objeto("label_punto_raiz", animacion="FadeOut")
        
        # El punto original izquierdo viaja por la curva hasta la nueva posición
        escena.animar_punto_sobre_curva(
            x_inicio=a, x_fin=x_nueva, funcion=f_objetivo, 
            color=WHITE, id="punto_a"
        )
        
        # El label del signo izquierdo viaja sincronizado persiguiendo al punto
        escena.transformar_objeto(
            origen="label_signo_izq", tipo_destino="texto",
            texto=r"$$(+)$$", posicion=(x_nueva - 0.3, y_nueva + 0.3), id_destino="label_signo_izq"
        )
        
    # Actualizamos el valor interno de 'a' para futuras matemáticas
    a = x_nueva
    fa = y_nueva

    # ==========================================
    # [03:30 - 03:32] LIMPIEZA PARA LA EXPLORACIÓN
    # Narrativa: "Ahora veamos qué pasa si elegimos otros intervalos iniciales..."
    # ==========================================
    with escena.bloque_paralelo(tiempo_animacion=1.5, tiempo_espera=0.5):
        escena.eliminar_objeto("label_signo_izq", animacion="FadeOut")
        escena.eliminar_objeto("label_signo_der", animacion="FadeOut")
        escena.eliminar_objeto("eq_recta", animacion="FadeOut")

    # ==========================================
    # [03:32 - 03:40] EXPLORACIÓN 1: PUNTOS A [-0.4, 0.6] Y NACE LA RECTA
    # ==========================================
    x1_a, x1_c = -0.4, 0.6
    
    # 1. Movemos los puntos por la curva hacia el primer intervalo
    with escena.bloque_paralelo(tiempo_animacion=2.5, tiempo_espera=0.5):
        escena.animar_punto_sobre_curva(x_inicio=a, x_fin=x1_a, funcion=f_objetivo, color=WHITE, id="punto_a")
        escena.animar_punto_sobre_curva(x_inicio=c_val, x_fin=x1_c, funcion=f_objetivo, color=WHITE, id="punto_c")

    # 2. Animamos el nacimiento de la recta secante ya en su nueva posición
    f_sec_1 = generar_secante(x1_a, f_objetivo(x1_a), x1_c, f_objetivo(x1_c))
    escena.agregar_funcion(f_sec_1, color=YELLOW, id="secante_movil", tiempo_animacion=1.5, tiempo_espera=2.0)

    # ==========================================
    # [03:40 - 03:47] EXPLORACIÓN 2: CONJUNTO A [1.5, 3.0]
    # ==========================================
    x2_a, x2_c = 1.5, 3.6
    f_sec_2 = generar_secante(x2_a, f_objetivo(x2_a), x2_c, f_objetivo(x2_c))
    
    # El conjunto de puntos y recta se mueve simultáneamente y de forma fluida
    with escena.bloque_paralelo(tiempo_animacion=3.0, tiempo_espera=4.0):
        escena.animar_punto_sobre_curva(x_inicio=x1_a, x_fin=x2_a, funcion=f_objetivo, color=WHITE, id="punto_a")
        escena.animar_punto_sobre_curva(x_inicio=x1_c, x_fin=x2_c, funcion=f_objetivo, color=WHITE, id="punto_c")
        
        # Transformación continua de la recta (sin redibujar)
        escena.transformar_objeto(
            origen="secante_movil", tipo_destino="funcion", 
            funcion=f_sec_2, color=YELLOW, id_destino="secante_movil"
        )

    # ==========================================
    # [03:47 - 03:57] EXPLORACIÓN 3: CONJUNTO A [-1.6, 3.6] Y CORTE EN X
    # ==========================================
    x3_a, x3_c = -0.6, 3.6
    f_sec_3 = generar_secante(x3_a, f_objetivo(x3_a), x3_c, f_objetivo(x3_c))

    # Viaje final del conjunto completo
    with escena.bloque_paralelo(tiempo_animacion=3.0, tiempo_espera=11):
        escena.animar_punto_sobre_curva(x_inicio=x2_a, x_fin=x3_a, funcion=f_objetivo, color=WHITE, id="punto_a")
        escena.animar_punto_sobre_curva(x_inicio=x2_c, x_fin=x3_c, funcion=f_objetivo, color=WHITE, id="punto_c")
        
        escena.transformar_objeto(
            origen="secante_movil", tipo_destino="funcion", 
            funcion=f_sec_3, color=YELLOW, id_destino="secante_movil"
        )

    # Matemáticas para encontrar el punto de corte en el eje X
    fa3, fc3 = f_objetivo(x3_a), f_objetivo(x3_c)
    m3 = (fc3 - fa3) / (x3_c - x3_a)
    raiz_x3 = x3_c - (fc3 / m3)

    # Nace el punto blanco final en la intersección
    escena.agregar_punto(
        raiz_x3, 0.0, 
        color=WHITE, 
        id="punto_corte_final", 
        tiempo_animacion=1.5, 
        tiempo_espera=15.0
    )

    # ==========================================
    # [03:57 - 04:05] EL GRAN FINAL: LA FÓRMULA DE LA REGLA FALSA
    # Narrativa: "Y así es como, a través de la interpolación lineal, llegamos a la fórmula general..."
    # ==========================================
    # 1. Colapso del entorno gráfico (FadeOut de ejes, curva y puntos)
    with escena.bloque_paralelo(tiempo_animacion=2.0, tiempo_espera=0.5):
        escena.eliminar_objeto("punto_a", animacion="FadeOut")
        escena.eliminar_objeto("punto_c", animacion="FadeOut")
        escena.eliminar_objeto("punto_corte_final", animacion="FadeOut")
        escena.eliminar_objeto("curva_principal", animacion="FadeOut")
        escena.eliminar_objeto("label_funcion", animacion="FadeOut")
        
        # Eliminamos los ejes del plano (asumiendo que tu motor los guarda bajo el ID "plano" o ejes)
        # Si tu motor usa un ID distinto para las coordenadas base, ponlo aquí
        try:
            escena.eliminar_objeto("plano", animacion="FadeOut")
        except:
            pass # Por si el ID interno del plano es otro en tu clase
            
        # 2. ¡LA MAGIA DEL MOTOR DE ÁLGEBRA!
        # Transformamos la recta secante directamente en la fórmula central
        # Recuerda NO usar $$ si la transformación va al engine de objetos del plano
        escena.transformar_objeto(
            origen="secante_movil", 
            tipo_destino="texto", 
            texto=r"x_{nueva} = c - \left(\frac{c - a}{f(c) - f(a)}\right)f(c)", 
            posicion="CENTER", # Al mismísimo centro de la pantalla
            id_destino="formula_final_regla_falsa"
        )
    
    # 3. Y el cierre definitivo (Fundido a negro general)
    escena.desvanecer_todo(tiempo_animacion=8.0)

    escena.render(previsualizar=True)