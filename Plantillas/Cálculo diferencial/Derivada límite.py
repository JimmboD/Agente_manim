import math
from manim import DOWN
from Planos.generar_plano import AnimadorGrafico

# 1. Definición Funcional
def f_objetivo(x: float) -> float:
    return 0.5 * x**2 + 1

if __name__ == "__main__":
    escena = AnimadorGrafico(f_objetivo, x_min=-1.0, x_max=4.0)
    
    # Nodo ancla P(1, f(1))
    escena.agregar_punto(
        x=1.0, y=f_objetivo(1.0), 
        color="#FF0000", label=True, 
        tiempo_animacion=1.0, tiempo_espera=0.5
    )
    
    # Punto móvil Q
    escena.animar_punto_sobre_curva(
        x_inicio=1.0, x_fin=3.5, 
        funcion=f_objetivo, 
        color="#00FF00", 
        tiempo_animacion=2.0, tiempo_espera=0.5
    )
    
    # Línea de acotación vertical
    escena.animar_linea_punteada(
        x1_ini=3.5, x1_fin=3.5,
        x2_ini=3.5, x2_fin=3.5,
        y1_ini=f_objetivo, y2_ini=0, 
        color="#00FFFF", 
        tiempo_animacion=1.5, tiempo_espera=0.5
    )
    
    # Llave diferencial Delta x
    escena.animar_llave(
        x1_ini=1.0, x1_fin=1.0,
        x2_ini=3.5, x2_fin=3.5,
        y1_ini=0, y2_ini=0,
        texto=r"\Delta x",
        direccion=DOWN,
        color="#FF00FF",
        tiempo_animacion=1.0, tiempo_espera=1.0
    )
    
    # HUD diferencial
    hud = r"""$$m = \frac{f(x+\Delta x) - f(x)}{\Delta x}$$"""
    escena.agregar_algebra_flotante(
        fuente_o_texto=hud, posicion="UL", 
        id="hud_limite", tiempo_animacion=1.0, tiempo_espera=1.5
    )
    
    # Secante transicionando a tangente
    escena.animar_secante(
        x1_ini=1.0, x1_fin=1.0,
        x2_ini=3.5, x2_fin=1.00001,
        funcion=f_objetivo, color="#FFFF00",
        tiempo_animacion=3.5, tiempo_espera=1.0
    )
    
    # Purga y conclusión
    escena.eliminar_objeto(id="hud_limite", animacion="FadeOut", tiempo_animacion=0.8)
    conclusion = r"f'(x) = \lim_{\Delta x \to 0} \frac{f(x+\Delta x) - f(x)}{\Delta x}"
    escena.transformar_a_texto(texto_latex=conclusion, tiempo_animacion=2.0, tiempo_espera=2.5)
    escena.desvanecer_todo(animacion="FadeOut", tiempo_animacion=1.5)
    
    escena.render(previsualizar=True)
