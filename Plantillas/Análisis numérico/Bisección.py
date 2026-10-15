import math
from Planos.generar_plano import AnimadorGrafico

# ==========================================
# CONFIGURACIÓN DE LA ANIMACIÓN (BISECCIÓN)
# ==========================================
def f_objetivo(x: float) -> float:
    return math.exp(x) - 3 * (x**2)

LABEL_FUNCION = r"$$f(x) = e^x - 3x^2$$"
A_INICIAL = 0.0
B_INICIAL = 1.5
TOLERANCIA = 0.0001
MAX_ITERACIONES = 4

# ==========================================
# CONFIGURACIÓN DE TIEMPOS DE ANIMACIÓN (POR PASOS)
# NOTA: Los siguientes valores representan el ritmo estándar predeterminado.
# Deben mantenerse con estos valores predefinidos y modificarse ÚNICAMENTE 
# cuando el usuario o una indicación explícita lo solicite.
# ==========================================
# Paso 0: Puntos iniciales del intervalo [a, b]
T_PUNTOS_INI_ANIM = 0.5
T_PUNTOS_INI_ESPERA = 0.1

# Paso 1: Despliegue de cálculos algebraicos en HUD
T_HUD_ANIM = 1.0
T_HUD_ESPERA = 1.0

# Paso 2: Proyección del punto medio al eje X (marca y línea guía)
T_PROY_PUNTO_ANIM = 0.5
T_PROY_PUNTO_ESPERA = 1.0
T_PROY_LINEA_ANIM = 0.8
T_PROY_LINEA_ESPERA = 1.0

# Paso 3: Limpieza de guías visuales temporales (línea punteada y punto)
T_LIMPIEZA_LINEA_ANIM = 0.5
T_LIMPIEZA_LINEA_ESPERA = 0.1
T_LIMPIEZA_PUNTO_ANIM = 0.5
T_LIMPIEZA_PUNTO_ESPERA = 0.2

# Paso 4: Traslación del extremo sobre la curva hacia la nueva aproximación
T_MOVIMIENTO_CURVA_ANIM = 1.5
T_MOVIMIENTO_CURVA_ESPERA = 1.0

# Paso 5: Cierre y desvanecimiento final de la escena
T_FINAL_ANIM = 2.0
T_FINAL_ESPERA = 1.0
# ==========================================

if __name__ == "__main__":
    
    escena = AnimadorGrafico(f_objetivo, x_min=-0.5, x_max=2.0)
    
    # Etiqueta fija en la esquina inferior derecha
    escena.agregar_algebra_flotante(LABEL_FUNCION, posicion="DR", remover_al_final=False)
    
    a, b = A_INICIAL, B_INICIAL
    fa, fb = f_objetivo(a), f_objetivo(b)
    
    # ESTADO INICIAL: Intervalo [a, b]
    escena.agregar_punto(a, fa, color="#FFFF00", id="punto_A", tiempo_animacion=T_PUNTOS_INI_ANIM, tiempo_espera=T_PUNTOS_INI_ESPERA)
    escena.agregar_punto(b, fb, color="#FFFF00", id="punto_B", tiempo_animacion=T_PUNTOS_INI_ANIM, tiempo_espera=T_PUNTOS_INI_ESPERA)
    
    error = 100.0
    c_prev = a
    i = 1
    
    # El bucle se repite mientras el error supere la tolerancia y no se excedan las iteraciones
    while error > TOLERANCIA and i <= MAX_ITERACIONES:
        # 1. CÁLCULO DEL PUNTO MEDIO
        c = (a + b) / 2.0
        fc = f_objetivo(c)
        
        # 2. CÁLCULO DE ERROR RELATIVO
        if i > 1:
            error = abs((c - c_prev) / c) * 100 if c != 0 else 100.0
            str_error = f"{error:.4f}\\%"
        else:
            str_error = "\\text{N/A}"
            
        texto_hud = f"""
        $$\\text{{Bisección - Iteración: }} {i}$$
        $$c_{{{i}}} = \\frac{{{a:.4f} + {b:.4f}}}{{2}} = {c:.4f}$$
        $$f(c_{{{i}}}) \\approx {fc:.4f}$$
        $$\\text{{Error: }} {str_error}$$
        """
        escena.agregar_algebra_flotante(
            texto_hud, posicion="UL", remover_al_final=True, 
            tiempo_animacion=T_HUD_ANIM, tiempo_espera=T_HUD_ESPERA
        )
        
        # 3. PROYECCIÓN Y MARCA DEL PUNTO MEDIO EN EL EJE X
        escena.agregar_punto(
            c, 0.0, color="#FFFFFF", label=False, id="punto_c", 
            tiempo_animacion=T_PROY_PUNTO_ANIM, tiempo_espera=T_PROY_PUNTO_ESPERA
        )
        escena.animar_linea_punteada(
            x1_ini=c, x1_fin=c, x2_ini=c, x2_fin=c, y1_ini=0.0, y2_ini=f_objetivo, 
            color="#FFFFFF", id="proy_c", 
            tiempo_animacion=T_PROY_LINEA_ANIM, tiempo_espera=T_PROY_LINEA_ESPERA
        )
        
        # 4. ELIMINACIÓN DE LA PROYECCIÓN TEMPORAL
        escena.eliminar_objeto(
            id="proy_c", animacion="Uncreate", 
            tiempo_animacion=T_LIMPIEZA_LINEA_ANIM, tiempo_espera=T_LIMPIEZA_LINEA_ESPERA
        )
        escena.eliminar_objeto(
            id="punto_c", animacion="FadeOut", 
            tiempo_animacion=T_LIMPIEZA_PUNTO_ANIM, tiempo_espera=T_LIMPIEZA_PUNTO_ESPERA
        )
        
        # 5. ACTUALIZACIÓN DE LÍMITES Y TRASLACIÓN SOBRE LA CURVA
        if fa * fc < 0:
            b_viejo = b
            b, fb = c, fc
            # El extremo derecho B viaja sobre la curva hacia el punto medio c
            escena.animar_punto_sobre_curva(
                x_inicio=b_viejo, x_fin=b, funcion=f_objetivo, 
                color="#FFFF00", id="punto_B", 
                tiempo_animacion=T_MOVIMIENTO_CURVA_ANIM, tiempo_espera=T_MOVIMIENTO_CURVA_ESPERA
            )
        else:
            a_viejo = a
            a, fa = c, fc
            # El extremo izquierdo A viaja sobre la curva hacia el punto medio c
            escena.animar_punto_sobre_curva(
                x_inicio=a_viejo, x_fin=a, funcion=f_objetivo, 
                color="#FFFF00", id="punto_A", 
                tiempo_animacion=T_MOVIMIENTO_CURVA_ANIM, tiempo_espera=T_MOVIMIENTO_CURVA_ESPERA
            )
            
        c_prev = c
        i += 1
        
    escena.desvanecer_todo(tiempo_animacion=T_FINAL_ANIM, tiempo_espera=T_FINAL_ESPERA)
    escena.render(previsualizar=True)
