import math
from Planos.generar_plano import AnimadorGrafico

def f_curva(x: float) -> float:
    return 0.2 * (x - 2) * (x + 2) * x

if __name__ == "__main__":
    escena = AnimadorGrafico(f_curva, x_min=-3.0, x_max=3.0)
    
    escena.agregar_punto(-2.0, f_curva(-2.0), color="#00FFCC", label=True)
    escena.agregar_punto(0.0, f_curva(0.0), color="#FFCC00", label=True)
    escena.agregar_punto(2.0, f_curva(2.0), color="#FF007F", label=True)
    
    escena.animar_punto_sobre_curva(
        x_inicio=-2.5, x_fin=2.5, funcion=f_curva, 
        color="#FFFFFF", tiempo_animacion=3.0, tiempo_espera=1.0
    )
    
    escena.desvanecer_todo(animacion="FadeOut", tiempo_animacion=1.5)
    escena.render(previsualizar=True)
