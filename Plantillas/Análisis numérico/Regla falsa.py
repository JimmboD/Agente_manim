import math
from Planos.generar_plano import AnimadorGrafico

# ==========================================
# CONFIGURACIÓN DE LA ANIMACIÓN
# ==========================================
def f_objetivo(x: float) -> float:
    return math.exp(x) - 3 * (x**2)

LABEL_FUNCION = r"$$f(x) = e^x - 3x^2$$"
A_INICIAL = 0.0
B_INICIAL = 1.5
TOLERANCIA = 0.0001
MAX_ITERACIONES = 4
# ==========================================

def generar_secante(x0, y0, x1, y1):
    return lambda x: (y1 - y0) / (x1 - x0) * (x - x0) + y0 if abs(x1 - x0) > 1e-5 else y0

if __name__ == "__main__":
    
    escena = AnimadorGrafico(f_objetivo, x_min=-0.5, x_max=2.0)
    
    # Etiqueta fija en la esquina inferior derecha
    escena.agregar_algebra_flotante(LABEL_FUNCION, posicion="DR", remover_al_final=False)
    
    a, b = A_INICIAL, B_INICIAL
    fa, fb = f_objetivo(a), f_objetivo(b)
    c = b - fb * ((b - a) / (fb - fa))
    
    # ESTADO INICIAL
    escena.agregar_punto(a, fa, color="#FFFF00", id="punto_A", tiempo_animacion=0.5, tiempo_espera=0.1)
    escena.agregar_punto(b, fb, color="#FFFF00", id="punto_B", tiempo_animacion=0.5, tiempo_espera=0.1)
    
    error = 100.0
    i = 1
    
    # El bucle se rompe si el error es menor a la tolerancia o se excede el límite de iteraciones
    while error > TOLERANCIA and i <= MAX_ITERACIONES:
        fc = f_objetivo(c)
        
        # 1. DIBUJAR SECANTE INICIAL (Solo en la primera iteración)
        if i == 1:
            escena.agregar_funcion(generar_secante(a, fa, b, fb), color="#FFFF00", id="secante", tiempo_animacion=1.0)
        
        # 2. CÁLCULO ALGEBRAICO Y VISUALIZACIÓN DE ERROR
        str_error = f"{error:.4f}\\%" if i > 1 else "\\text{N/A}"
        texto_hud = f"""
        $$\\text{{Iteración: }} {i}$$
        $$x_{{{i}}} = {b:.4f} - f({b:.4f}) \\frac{{{b:.4f} - {a:.4f}}}{{f({b:.4f}) - f({a:.4f})}}$$
        $$x_{{{i}}} \\approx {c:.4f}$$
        $$\\text{{Error: }} {str_error}$$
        """
        escena.agregar_algebra_flotante(texto_hud, posicion="UL", remover_al_final=True, tiempo_animacion=1.0, tiempo_espera=1.0)
        
        # 3. PROYECCIÓN Y MARCA DEL PUNTO RAÍZ BLANCO
        escena.agregar_punto(c, 0.0, color="#FFFFFF", label=False, id="punto_raiz", tiempo_animacion=0.5)
        escena.animar_linea_punteada(
            x1_ini=c, x1_fin=c, x2_ini=c, x2_fin=c, y1_ini=0.0, y2_ini=f_objetivo, 
            color="#FFFFFF", id="proy_c", tiempo_animacion=0.8
        )
        
        # 4. ELIMINACIÓN DEL PUNTO BLANCO Y LA LÍNEA ANTES DEL MOVIMIENTO DE LA RECTA
        escena.eliminar_objeto(id="proy_c", animacion="Uncreate", tiempo_animacion=0.5, tiempo_espera=0.1)
        escena.eliminar_objeto(id="punto_raiz", animacion="FadeOut", tiempo_animacion=0.5, tiempo_espera=0.2)
        
        # 5. CÁLCULO DE SIGUIENTE ITERACIÓN Y MOVIMIENTO PARAMÉTRICO
        if fa * fc < 0:
            b_viejo = b
            b, fb = c, fc
            c_nuevo = b - fb * ((b - a) / (fb - fa))
            
            escena.animar_convergencia_parametrica(
                funcion=f_objetivo, x_fijo=a, 
                x_movil_ini=b_viejo, x_movil_fin=b,
                id_secante="secante", id_punto_curva="punto_B", id_punto_raiz="punto_raiz",
                tiempo_animacion=2.0, tiempo_espera=1.0
            )
        else:
            a_viejo = a
            a, fa = c, fc
            c_nuevo = b - fb * ((b - a) / (fb - fa))
            
            escena.animar_convergencia_parametrica(
                funcion=f_objetivo, x_fijo=b, 
                x_movil_ini=a_viejo, x_movil_fin=a,
                id_secante="secante", id_punto_curva="punto_A", id_punto_raiz="punto_raiz",
                tiempo_animacion=2.0, tiempo_espera=1.0
            )
        
        # 6. ACTUALIZACIÓN DE VARIABLES Y ERROR PARA EL BUCLE
        error = abs((c_nuevo - c) / c_nuevo) * 100 if c_nuevo != 0 else 100
        c = c_nuevo
        i += 1
        
    escena.desvanecer_todo(tiempo_animacion=2.0)
    escena.render(previsualizar=True)
