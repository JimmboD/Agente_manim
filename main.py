import math
from manim import DOWN, RIGHT, UL
from Planos.generar_plano import AnimadorGrafico

# 1. Definición Funcional Principal
def f_objetivo(x: float) -> float:
    return math.exp(x) - 3 * (x**2)

# Funciones adicionales
def f_u_positiva(x: float) -> float: return (x - 0.5)**2 + 0.5
def f_u_negativa(x: float) -> float: return -(x - 0.5)**2 - 0.5
def f_w(x: float) -> float: return math.cos(4*x)
def f_eje_x(x: float) -> float: return 0.0

def f_secante(x: float) -> float:
    x0, x1 = 0.0, 1.5
    y0, y1 = f_objetivo(x0), f_objetivo(x1)
    m = (y1 - y0) / (x1 - x0)
    return m * (x - x0) + y0

if __name__ == "__main__":
    
    # 2. Instanciación Topológica
    escena = AnimadorGrafico(f_objetivo, x_min=-0.5, x_max=2.0)
    
    # --- 00:00 - 00:07 ---
    #escena.agregar_funcion(f_objetivo, color="#FF0000", tiempo_animacion=4.0, tiempo_espera=3.0)
    
    # --- 00:07 - 00:15 ---
    # ESTÁNDAR 1: transformar_a_texto va directo a MathTex -> NO lleva $$
    escena.transformar_a_texto(r"f(x) = 0", tiempo_animacion=3.0, tiempo_espera=5.0)
    
    # --- 00:15 - 00:23 ---
    escena.transformar_a_plano(tiempo_animacion=1.5, tiempo_espera=0.1)
    escena.agregar_punto(0.0, 0.0, color="#FFFFFF", tiempo_animacion=0.75, tiempo_espera=0.1)
    escena.agregar_punto(1.5, 0.0, color="#FFFFFF", tiempo_animacion=0.75, tiempo_espera=0.1)
    escena.animar_linea_punteada(0.0, 0.0, 0.0, 0.0, 0.0, f_objetivo, tiempo_animacion=0.75, tiempo_espera=0.1)
    escena.animar_linea_punteada(1.5, 1.5, 1.5, 1.5, 0.0, f_objetivo, tiempo_animacion=0.75, tiempo_espera=0.1)
    escena.animar_punto_sobre_curva(1.5, 0.75, f_eje_x, color="#FFFFFF", tiempo_animacion=2.0, tiempo_espera=3.0)
    
    # --- 00:23 - 00:36 ---
    escena.animar_secante(0.0, 0.0, 1.5, 1.5, f_objetivo, color="#FFFF00", tiempo_animacion=2.0, tiempo_espera=11.0)
    
    # --- 00:36 - 00:46 ---
    # Desvanecimiento creativo usando \quad (espacio en blanco válido en MathTex)
    escena.transformar_a_texto(r"\quad", tiempo_animacion=1.0, tiempo_espera=0.1)
    escena.transformar_a_plano(tiempo_animacion=0.1, tiempo_espera=0.1)
    escena.agregar_punto(0.0, 0.0, color="#FFFFFF", tiempo_animacion=0.5, tiempo_espera=0.1)
    escena.agregar_punto(1.5, 0.0, color="#FFFFFF", tiempo_animacion=0.5, tiempo_espera=8.0)
    
    # --- 00:46 - 00:54 ---
    escena.agregar_funcion(f_objetivo, color="#FF0000", tiempo_animacion=2.0, tiempo_espera=0.1)
    escena.animar_linea_punteada(0.0, 0.0, 0.0, 0.0, 0.0, f_objetivo, tiempo_animacion=0.75, tiempo_espera=0.1)
    escena.animar_linea_punteada(1.5, 1.5, 1.5, 1.5, 0.0, f_objetivo, tiempo_animacion=0.75, tiempo_espera=0.1)
    escena.agregar_punto(0.0, f_objetivo(0.0), color="#FFFF00", tiempo_animacion=0.25, tiempo_espera=0.1)
    escena.agregar_punto(1.5, f_objetivo(1.5), color="#FFFF00", tiempo_animacion=0.25, tiempo_espera=4.0)
    
    # --- 00:54 - 00:58 ---
    escena.animar_secante(0.0, 0.0, 1.5, 1.5, f_objetivo, color="#FFFF00", tiempo_animacion=1.5, tiempo_espera=2.5)
    
    # --- 00:58 - 01:05 ---
    # ESTÁNDAR 2: agregar_algebra_flotante va por motor_algebra -> SÍ lleva $$
    escena.agregar_algebra_flotante(r"$$y = mx + b$$", posicion="UL", tiempo_animacion=1.0, tiempo_espera=6.0)
    
    # --- 01:05 - 01:13 ---
    escena.agregar_algebra_flotante(r"$$y = \textcolor{yellow}{\frac{f(b) - f(a)}{b - a}} x + b$$", posicion="UL", tiempo_animacion=2.0, tiempo_espera=5.0)
    
    # --- 01:13 - 01:21 ---
    # ESTÁNDAR 3: animar_llave pasa texto directo a MathTex -> NO lleva $$
    escena.animar_llave(0.0, 0.0, 1.5, 1.5, f_objetivo(0.0), f_objetivo(0.0), texto=r"\Delta x", direccion=DOWN, color="#FFFFFF", tiempo_animacion=1.0, tiempo_espera=0.1)
    escena.animar_llave(1.5, 1.5, 1.5, 1.5, f_objetivo(0.0), f_objetivo(1.5), texto=r"\Delta y", direccion=RIGHT, color="#FFFFFF", tiempo_animacion=1.0, tiempo_espera=6.0)
    
    # --- 01:21 - 01:25 ---
    # CORREGIDO: Sin \textcolor porque es un transformar_a_texto
    escena.transformar_a_texto(r"y = \frac{f(b) - f(a)}{b - a} x + b", tiempo_animacion=2.0, tiempo_espera=2.0)
    
    # --- 01:25 - 01:49 (EL BLOQUE MAESTRO) ---
    # CORREGIDO: Todo en un solo string gigante. El motor detectará los \textcolor, 
    # y nuestro criterio_animacion hará ReplacementTransforms entre ellas sin que 
    # la gráfica parpadee de fondo.
    desarrollo_algebraico = r"""
    $$\textcolor{yellow}{y} = \frac{f(b) - f(a)}{b - a} \textcolor{yellow}{x} + \textcolor{yellow}{b}$$
    $$y = \frac{f(b) - f(a)}{b - a} x + \textcolor{yellow}{b}$$
    $$f(c) = \frac{f(b) - f(a)}{b - a} c + \textcolor{yellow}{b}$$
    $$\textcolor{yellow}{b} = f(c) - \frac{f(b) - f(a)}{b - a} c$$
    $$y = \frac{f(b) - f(a)}{b - a} x + \left( f(c) - \frac{f(b) - f(a)}{b - a} c \right)$$
    $$y - f(c) = \textcolor{yellow}{\frac{f(b) - f(a)}{b - a}} (x - c)$$
    """
    escena.insertar_algebra(desarrollo_algebraico, tiempo_animacion=1.5, tiempo_espera=2.0)
    
    # --- 01:49 - 01:54 ---
    hud_comparacion = r"""
    $$y - f(c) = \textcolor{yellow}{\frac{f(b) - f(a)}{b - a}} (x - c)$$
    $$y - y_1 = m(x - x_1)$$
    """
    escena.insertar_algebra(hud_comparacion, tiempo_animacion=1.5, tiempo_espera=3.5)
    
    # --- 01:54 - 02:03 ---
    # CORREGIDO: Ya no usamos transformar_a_plano() porque insertar_algebra ya nos lo devolvió.
    # CORREGIDO: Tampoco agregamos f_objetivo de nuevo porque ya estaba.
    escena.agregar_algebra_flotante(r"$$y - f(c) = m(x - c)$$", posicion="UL", tiempo_animacion=0.1, tiempo_espera=0.1)
    escena.animar_secante(0.0, 0.0, 1.5, 1.5, f_objetivo, color="#FFFF00", tiempo_animacion=0.1, tiempo_espera=7.0)

    # --- 02:03 - 02:11 ---
    escena.agregar_algebra_flotante(r"$$y - f(c) = \frac{f(b) - f(a)}{b - a} (x - c)$$", posicion="UL", tiempo_animacion=1.5, tiempo_espera=0.1)
    escena.animar_secante(0.0, 0.0, 1.5, 1.5, f_objetivo, color="#FFFFFF", tiempo_animacion=0.75, tiempo_espera=0.1)
    escena.animar_secante(0.0, 0.0, 1.5, 1.5, f_objetivo, color="#FFFF00", tiempo_animacion=0.75, tiempo_espera=5.0)
    
    # --- 02:11 - 02:22 ---
    m_secante = (f_objetivo(1.5) - f_objetivo(0.0)) / (1.5 - 0.0)
    x_raiz = 0.0 - (f_objetivo(0.0) / m_secante)
    
    escena.agregar_punto(1.5, f_secante(1.5), color="#FFFFFF", tiempo_animacion=1.0, tiempo_espera=0.1)
    escena.animar_punto_sobre_curva(1.5, x_raiz, f_secante, color="#FFFFFF", tiempo_animacion=4.0, tiempo_espera=6.0)
    
    # --- 02:22 - 02:42 ---
    escena.agregar_punto(x_raiz, 0.0, color="#FFFF00", tiempo_animacion=0.5, tiempo_espera=0.1)
    escena.agregar_punto(x_raiz, 0.0, color="#FFFFFF", tiempo_animacion=0.5, tiempo_espera=0.1)
    escena.agregar_punto(x_raiz, 0.0, color="#FFFFFF", label=True, tiempo_animacion=1.0, tiempo_espera=16.5)
    
    # --- 02:42 - 02:46 ---
    escena.transformar_a_texto(r"0 - f(c) = m(x_{nueva} - c)", tiempo_animacion=3.0, tiempo_espera=1.0)
    
    # --- 02:46 - 02:59 ---
    escena.insertar_algebra(r"$$-f(c) = \textcolor{yellow}{\frac{f(b) - f(a)}{b - a}} (x_{nueva} - c)$$", tiempo_animacion=2.0, tiempo_espera=1.0)
    escena.insertar_algebra(r"$$-f(c) \textcolor{yellow}{\frac{b - a}{f(b) - f(a)}} = x_{nueva} - c$$", tiempo_animacion=2.0, tiempo_espera=1.0)
    escena.insertar_algebra(r"$$x_{nueva} = c - f(c) \textcolor{yellow}{\frac{b - a}{f(b) - f(a)}}$$", tiempo_animacion=2.0, tiempo_espera=5.0)
    
    # --- 02:59 - 03:04 ---
    escena.transformar_a_plano(tiempo_animacion=1.5, tiempo_espera=0.1)
    escena.agregar_punto(x_raiz, 0.0, color="#FFFF00", tiempo_animacion=1.0, tiempo_espera=2.5)
    
    # --- 03:04 - 03:12 ---
    escena.animar_linea_punteada(x_raiz, x_raiz, x_raiz, x_raiz, 0.0, f_objetivo, tiempo_animacion=1.0, tiempo_espera=0.1)
    escena.animar_secante(1.5, x_raiz, 0.0, 0.0, f_objetivo, color="#FFFF00", tiempo_animacion=3.0, tiempo_espera=4.0)
    
    # --- 03:12 - 03:20 ---
    escena.agregar_punto(x_raiz, f_objetivo(x_raiz), color="#FFFFFF", tiempo_animacion=0.5, tiempo_espera=0.1)
    escena.agregar_punto(x_raiz, f_objetivo(x_raiz), color="#FFFF00", tiempo_animacion=0.5, tiempo_espera=0.1)
    escena.agregar_punto(0.0, f_objetivo(0.0), color="#FFFFFF", tiempo_animacion=0.5, tiempo_espera=0.1)
    escena.agregar_punto(0.0, f_objetivo(0.0), color="#FFFF00", tiempo_animacion=0.5, tiempo_espera=6.0)
    
    # --- 03:20 - 04:05 ---
    escena.agregar_funcion(f_u_positiva, color="#00FF00", tiempo_animacion=2.0, tiempo_espera=8.0)
    escena.agregar_funcion(f_u_negativa, color="#0088FF", tiempo_animacion=2.0, tiempo_espera=8.0)
    escena.agregar_funcion(f_w, color="#FF8800", tiempo_animacion=2.0, tiempo_espera=10.0)
    
    # 6. Trigger Asíncrono
    escena.render(previsualizar=True)