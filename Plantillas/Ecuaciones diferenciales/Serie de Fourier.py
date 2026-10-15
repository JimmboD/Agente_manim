import math
import sympy as sp
from Planos.generar_plano import AnimadorGrafico

# ==========================================
# CONFIGURACIÓN DE LA ANIMACIÓN (FOURIER)
# ==========================================
x_sym = sp.Symbol('x')
LABEL_FUNCION = r"$$f(x) = \text{Onda Cuadrada}$$"
NUM_ARMONICOS = 7  # Número de armónicos impares a sumar
# ==========================================

# Definimos una onda cuadrada periódica pura (Amplitud de -1 a 1, periodo 2*pi)
def f_objetivo(x: float) -> float:
    # Usamos el módulo para hacerla periódica infinita
    x_mod = x % (2 * math.pi)
    if x_mod < math.pi:
        return 1.0
    elif x_mod > math.pi:
        return -1.0
    return 0.0

if __name__ == "__main__":
    
    # Plano amplio para ver varios periodos de la señal
    escena = AnimadorGrafico(f_objetivo, x_min=-7.0, x_max=7.0)
    
    # 1. ETIQUETA FIJA (La onda cuadrada roja se dibuja sola)
    escena.agregar_algebra_flotante(LABEL_FUNCION, posicion="DR", remover_al_final=False)
    
    fourier_expr = 0
    armonico_mostrado = 0
    
    # 2. BUCLE DE CONSTRUCCIÓN ARMÓNICA (Solo armónicos impares para la onda cuadrada)
    for i in range(1, NUM_ARMONICOS + 1):
        n = 2 * i - 1  # 1, 3, 5, 7...
        
        # Construcción simbólica del armónico de Fourier: (4 / (n * pi)) * sin(nx)
        termino = (4 / (sp.pi * n)) * sp.sin(n * x_sym)
        fourier_expr += termino
        
        # Convertimos la suma armónica a una lambda super rápida para Manim
        f_fourier = sp.lambdify(x_sym, fourier_expr, "math")
        
        # HUD Automático: SymPy formatea la suma de senos a LaTeX
        str_fourier = sp.latex(fourier_expr)
        texto_hud = f"""
        $$\\text{{Armónicos: }} {i}$$
        $$F_{{{n}}}(x) = {str_fourier}$$
        """
        escena.agregar_algebra_flotante(texto_hud, posicion="UL", remover_al_final=True, tiempo_animacion=1.0, tiempo_espera=1.0)
        
        # 3. MORPHING ÚNICO DE LA ONDA (Amarillo)
        if armonico_mostrado == 0:
            # En la primera vuelta, nace la onda senoidal fundamental
            escena.agregar_funcion(f_fourier, color="#FFFF00", id="fourier_act", tiempo_animacion=1.5)
        else:
            # En las siguientes, la onda se deforma para acoplar las frecuencias más altas
            escena.transformar_objeto(
                origen="fourier_act", tipo_destino="funcion", funcion=f_fourier, 
                color="#FFFF00", id_destino="fourier_act", tiempo_animacion=1.5
            )
            
        armonico_mostrado += 1
        
    escena.desvanecer_todo(tiempo_animacion=2.0)
    escena.render(previsualizar=True)
