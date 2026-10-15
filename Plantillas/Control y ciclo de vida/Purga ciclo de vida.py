import math
from Planos.generar_plano import AnimadorGrafico

def f_onda(x: float) -> float:
    return math.sin(x)

if __name__ == "__main__":
    escena = AnimadorGrafico(f_onda, x_min=-4.0, x_max=4.0)
    
    escena.agregar_punto(0.0, 0.0, color="#FF0000", id="punto_origen")
    escena.agregar_punto(1.57, 1.0, color="#00FF00", id="punto_maximo")
    escena.agregar_punto(3.14, 0.0, color="#0000FF", id="punto_nodo")
    
    # Purga progresiva por ID
    escena.eliminar_objeto(id="punto_origen", animacion="Uncreate", tiempo_animacion=1.0)
    escena.eliminar_objeto(id="punto_maximo", animacion="ShrinkToCenter", tiempo_animacion=1.0)
    escena.eliminar_objeto(id="punto_nodo", animacion="FadeOut", tiempo_animacion=1.0)
    
    escena.desvanecer_todo(animacion="FadeOut", tiempo_animacion=1.5)
    escena.render(previsualizar=True)
