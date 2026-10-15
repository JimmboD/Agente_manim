import math
from manim import DOWN
from Planos.generar_plano import AnimadorGrafico

def f_parabola(x: float) -> float:
    return x**2 - 2

if __name__ == "__main__":
    escena = AnimadorGrafico(f_parabola, x_min=-2.5, x_max=2.5)
    
    hud_formula = r"""$$f(x) = x^2 - 2$$"""
    escena.agregar_algebra_flotante(hud_formula, posicion="UL", id="hud_fn", tiempo_animacion=1.0)
    
    escena.agregar_punto(1.414, 0.0, color="#00FF00", label=True)
    escena.agregar_punto(-1.414, 0.0, color="#00FF00", label=True)
    
    escena.animar_llave(
        x1_ini=-1.414, x1_fin=-1.414, x2_ini=1.414, x2_fin=1.414,
        y1_ini=0, y2_ini=0, texto=r"2\sqrt{2}", direccion=DOWN, color="#58C4DD"
    )
    
    escena.desvanecer_todo(animacion="FadeOut", tiempo_animacion=1.5)
    escena.render(previsualizar=True)
