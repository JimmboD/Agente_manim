import math
import sympy as sp
from Planos.generar_plano import AnimadorGrafico

# ==========================================
# CONFIGURACIÓN DE LA ANIMACIÓN (TAYLOR)
# ==========================================
x_sym = sp.Symbol('x')
f_expr = sp.sin(x_sym)  # Función objetivo simbólica

A_EXPANSION = 0.0       # Centro de la serie (0.0 = Maclaurin)
NUM_TERMINOS = 10       # Hasta qué derivada calcular
# ==========================================

# Puente entre el mundo simbólico y el motor geométrico
def f_objetivo(x: float) -> float:
    return float(f_expr.subs(x_sym, x))

if __name__ == "__main__":
    
    # La clase AnimadorGrafico dibuja 'f_objetivo' de forma automática
    escena = AnimadorGrafico(f_objetivo, x_min=-8.0, x_max=8.0)
    
    # 1. ETIQUETA FIJA (La función roja ya está en el plano)
    str_f = sp.latex(f_expr)
    escena.agregar_algebra_flotante(f"$$f(x) = {str_f}$$", posicion="DR", remover_al_final=False)
    
    # 2. PUNTO DE EXPANSIÓN (Anclaje estático Blanco)
    y_anclaje = f_objetivo(A_EXPANSION)
    escena.agregar_punto(A_EXPANSION, y_anclaje, color="#FFFFFF", id="punto_ancla", tiempo_animacion=0.5)

    taylor_expr = 0
    grado_mostrado = 0
    
    # 3. BUCLE DE CONSTRUCCIÓN DEL POLINOMIO
    for i in range(NUM_TERMINOS):
        # Derivada exacta con SymPy
        derivada_expr = sp.diff(f_expr, x_sym, i)
        derivada_eval = derivada_expr.subs(x_sym, A_EXPANSION)
        
        # Saltamos términos que valen 0
        if derivada_eval == 0 and i > 0:
            continue
            
        # Construcción simbólica del nuevo término
        termino = (derivada_eval / math.factorial(i)) * ((x_sym - A_EXPANSION)**i)
        taylor_expr += termino
        
        f_taylor = sp.lambdify(x_sym, taylor_expr, "math")
        
        # HUD Automático
        str_taylor = sp.latex(taylor_expr)
        texto_hud = f"""
        $$\\text{{Grado: }} {i}$$
        $$T_{{{i}}}(x) = {str_taylor}$$
        """
        escena.agregar_algebra_flotante(texto_hud, posicion="UL", remover_al_final=True, tiempo_animacion=1.0, tiempo_espera=0.5)
        
        # 4. MORPHING ÚNICO DE LA CURVA AMARILLA
        if grado_mostrado == 0:
            # En la primera vuelta, la función nace
            escena.agregar_funcion(f_taylor, color="#FFFF00", id="taylor_act", tiempo_animacion=1.0)
        else:
            # En las siguientes, la MISMA función se deforma in-place
            escena.transformar_objeto(
                origen="taylor_act", tipo_destino="funcion", funcion=f_taylor, 
                color="#FFFF00", id_destino="taylor_act", tiempo_animacion=1.5
            )
            
        grado_mostrado += 1
        
    escena.desvanecer_todo(tiempo_animacion=2.0)
    escena.render(previsualizar=True)