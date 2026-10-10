import math
from manim import DOWN
from Planos.generar_plano import AnimadorGrafico

# 1. Definición Funcional 
def f_objetivo(x: float) -> float:
    # Parábola suave para visualizar claramente la secante y la tangente
    return 0.5 * x**2 + 1

if __name__ == "__main__":
    
    # 2. Instanciación Topológica y Overscan
    escena = AnimadorGrafico(f_objetivo, x_min=-1.0, x_max=4.0)
    
    # 3. Nodos Estáticos (Geometría Base)
    # Punto ancla P(1, f(1))
    escena.agregar_punto(
        x=1.0, y=f_objetivo(1.0), 
        color="#FF0000", label=True, 
        tiempo_animacion=1.0, tiempo_espera=0.5
    )
    
    # 4. Interpolación Espacial Dinámica (Punto viajero)
    # Genera un segundo punto Q que nace en el ancla y viaja por la curva hasta x=3.5
    escena.animar_punto_sobre_curva(
        x_inicio=1.0, x_fin=3.5, 
        funcion=f_objetivo, 
        color="#00FF00", 
        tiempo_animacion=2.0, tiempo_espera=0.5
    )
    
    # 5. Acotación Polimórfica Curve-Aware (Línea punteada)
    # La coordenada y superior rastrea f(x) dinámicamente
    escena.animar_linea_punteada(
        x1_ini=3.5, x1_fin=3.5,
        x2_ini=3.5, x2_fin=3.5,
        y1_ini=f_objetivo, y2_ini=0, 
        color="#00FFFF", 
        tiempo_animacion=1.5, tiempo_espera=0.5
    )
    
    # 6. Llave Isométrica acoplada a ValueTracker
    # Muestra el diferencial Delta X en el plano
    escena.animar_llave(
        x1_ini=1.0, x1_fin=1.0,
        x2_ini=3.5, x2_fin=3.5,
        y1_ini=0, y2_ini=0,
        texto=r"\Delta x",
        direccion=DOWN,
        color="#FF00FF",
        tiempo_animacion=1.0, tiempo_espera=1.0
    )
    
    # 7. Inyección de HUD Vectorial Persistente
    hud_derivada = r"""
    $$m = \frac{f(x+\Delta x) - f(x)}{\Delta x}$$
    """
    escena.agregar_algebra_flotante(
        fuente_o_texto=hud_derivada, 
        posicion="UL", 
        remover_al_final=False, 
        id="hud_limite",
        tiempo_animacion=1.0, tiempo_espera=1.5
    )
    
    # 8. Cinemática de Límite (Secante -> Tangente)
    # Al reducir la distancia entre x1 y x2 a < 10^-4, el motor transiciona a tangente
    escena.animar_secante(
        x1_ini=1.0, x1_fin=1.0,
        x2_ini=3.5, x2_fin=1.00001,
        funcion=f_objetivo,
        color="#FFFF00",
        tiempo_animacion=4.0, tiempo_espera=1.5
    )
    
    # 9. Purga de Entidades por ID
    escena.eliminar_objeto(
        id="hud_limite", 
        animacion="FadeOut", 
        tiempo_animacion=1.0, tiempo_espera=0.5
    )
    
    # 10. Transformación de Estado (Topología -> Escalar Lógico)
    texto_conclusion = r"f'(x) = \lim_{\Delta x \to 0} \frac{f(x+\Delta x) - f(x)}{\Delta x}"
    escena.transformar_a_texto(
        texto_latex=texto_conclusion, 
        tiempo_animacion=2.0, tiempo_espera=3.0
    )
    
    # 11. Finalización y Teardown
    escena.desvanecer_todo(animacion="FadeOut", tiempo_animacion=1.5)
    
    # 12. Ejecución asíncrona en el construct() del Engine
    escena.render(previsualizar=True)