import math
from Planos.generar_plano import AnimadorGrafico

# ==========================================
# CONFIGURACIÓN DE LA ANIMACIÓN (NEWTON-RAPHSON)
# ==========================================
def f_objetivo(x: float) -> float:
    return math.exp(x) - 3 * (x**2)

def f_derivada(x: float) -> float:
    return math.exp(x) - 6 * x

LABEL_FUNCION = r"$$f(x) = e^x - 3x^2$$"
X_INICIAL = 1.5
TOLERANCIA = 0.0001
MAX_ITERACIONES = 5

# ==========================================
# CONFIGURACIÓN DE TIEMPOS DE ANIMACIÓN (POR PASOS)
# NOTA: Los siguientes valores representan el ritmo estándar predeterminado.
# Deben mantenerse con estos valores predefinidos y modificarse ÚNICAMENTE 
# cuando el usuario o una indicación explícita lo solicite.
# ==========================================
# Paso 0: Punto ancla inicial sobre la curva
T_PUNTO_INI_ANIM = 0.5
T_PUNTO_INI_ESPERA = 0.1

# Paso 1: Trazado de la recta tangente inicial (primera iteración)
T_TANGENTE_INI_ANIM = 1.0
T_TANGENTE_INI_ESPERA = 1.0

# Paso 2: Despliegue de cálculos algebraicos en HUD
T_HUD_ANIM = 1.0
T_HUD_ESPERA = 1.0

# Paso 3: Proyección de la raíz estimada al eje X (marca y línea guía)
T_PROY_PUNTO_ANIM = 0.5
T_PROY_PUNTO_ESPERA = 1.0
T_PROY_LINEA_ANIM = 0.8
T_PROY_LINEA_ESPERA = 1.0

# Paso 4: Transición paralela (rotación de tangente y traslación de punto sobre la curva)
T_TRANSICION_PARALELO_ANIM = 2.0
T_TRANSICION_PARALELO_ESPERA = 1.0

# Paso 5: Limpieza de guías visuales temporales (línea punteada y punto)
T_LIMPIEZA_LINEA_ANIM = 0.5
T_LIMPIEZA_LINEA_ESPERA = 0.1
T_LIMPIEZA_PUNTO_ANIM = 0.5
T_LIMPIEZA_PUNTO_ESPERA = 0.2

# Paso 6: Cierre y desvanecimiento final de la escena
T_FINAL_ANIM = 2.0
T_FINAL_ESPERA = 1.0
# ==========================================

def generar_tangente(x0, y0, m):
    # En Newton-Raphson la pendiente 'm' viene de la derivada exacta
    return lambda x: m * (x - x0) + y0

if __name__ == "__main__":
    
    escena = AnimadorGrafico(f_objetivo, x_min=-0.5, x_max=2.0)
    
    # Etiqueta fija en la esquina inferior derecha
    escena.agregar_algebra_flotante(LABEL_FUNCION, posicion="DR", remover_al_final=False)
    
    x_act = X_INICIAL
    y_act = f_objetivo(x_act)
    
    # 1. ESTADO INICIAL: Punto ancla en la curva (Color Amarillo)
    escena.agregar_punto(
        x_act, y_act, color="#FFFF00", id="punto_n", 
        tiempo_animacion=T_PUNTO_INI_ANIM, tiempo_espera=T_PUNTO_INI_ESPERA
    )
    
    error = 100.0
    i = 1
    
    # Bucle regido por tolerancia o límite de iteraciones
    while error > TOLERANCIA and i <= MAX_ITERACIONES:
        m_act = f_derivada(x_act)
        x_next = x_act - (y_act / m_act)
        y_next = f_objetivo(x_next)
        
        # 2. TRAZADO DE LA TANGENTE (Solo se instancia en iteración 1, luego se transforma)
        if i == 1:
            escena.agregar_funcion(
                generar_tangente(x_act, y_act, m_act), color="#FFFF00", id="tangente", 
                tiempo_animacion=T_TANGENTE_INI_ANIM, tiempo_espera=T_TANGENTE_INI_ESPERA
            )
            
        # 3. CÁLCULO ALGEBRAICO Y VISUALIZACIÓN EN HUD
        str_error = f"{error:.4f}\\%" if i > 1 else "\\text{N/A}"
        texto_hud = f"""
        $$\\text{{Iteración: }} {i}$$
        $$x_{{{i}}} = {x_act:.4f} - \\frac{{f({x_act:.4f})}}{{f'({x_act:.4f})}}$$
        $$x_{{{i}}} \\approx {x_next:.4f}$$
        $$\\text{{Error: }} {str_error}$$
        """
        escena.agregar_algebra_flotante(
            texto_hud, posicion="UL", remover_al_final=True, 
            tiempo_animacion=T_HUD_ANIM, tiempo_espera=T_HUD_ESPERA
        )
        
        # 4. MARCA DE LA RAÍZ PROYECTADA EN EL EJE X (Blanco)
        escena.agregar_punto(
            x_next, 0.0, color="#FFFFFF", label=False, id="punto_corte", 
            tiempo_animacion=T_PROY_PUNTO_ANIM, tiempo_espera=T_PROY_PUNTO_ESPERA
        )
        escena.animar_linea_punteada(
            x1_ini=x_next, x1_fin=x_next, x2_ini=x_next, x2_fin=x_next, y1_ini=0.0, y2_ini=f_objetivo, 
            color="#FFFFFF", id="proy_c", 
            tiempo_animacion=T_PROY_LINEA_ANIM, tiempo_espera=T_PROY_LINEA_ESPERA
        )
        
        # 5. MOVIMIENTO EN PARALELO (Antes de que la proyección desaparezca)
        m_next = f_derivada(x_next)
        
        with escena.bloque_paralelo(tiempo_animacion=T_TRANSICION_PARALELO_ANIM, tiempo_espera=T_TRANSICION_PARALELO_ESPERA):
            # La tangente pivotea y "rueda" sobre la curva hasta la nueva pendiente
            escena.transformar_objeto(
                origen="tangente", tipo_destino="funcion", funcion=generar_tangente(x_next, y_next, m_next), 
                color="#FFFF00", id_destino="tangente"
            )
            # El punto viaja físicamente arrastrándose por el contorno de f(x)
            escena.animar_punto_sobre_curva(
                x_inicio=x_act, x_fin=x_next, funcion=f_objetivo, 
                color="#FFFF00", id="punto_n"
            )
            
        # 6. ELIMINACIÓN DE GUÍAS VISUALES
        escena.eliminar_objeto(
            id="proy_c", animacion="Uncreate", 
            tiempo_animacion=T_LIMPIEZA_LINEA_ANIM, tiempo_espera=T_LIMPIEZA_LINEA_ESPERA
        )
        escena.eliminar_objeto(
            id="punto_corte", animacion="FadeOut", 
            tiempo_animacion=T_LIMPIEZA_PUNTO_ANIM, tiempo_espera=T_LIMPIEZA_PUNTO_ESPERA
        )
        
        # 7. ACTUALIZACIÓN DE VARIABLES Y ERROR
        error = abs((x_next - x_act) / x_next) * 100 if x_next != 0 else 100
        x_act = x_next
        y_act = y_next
        i += 1
        
    escena.desvanecer_todo(tiempo_animacion=T_FINAL_ANIM, tiempo_espera=T_FINAL_ESPERA)
    escena.render(previsualizar=True)
