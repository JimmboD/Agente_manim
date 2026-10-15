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
    escena.agregar_punto(x_act, y_act, color="#FFFF00", id="punto_n", tiempo_animacion=0.5, tiempo_espera=0.1)
    
    error = 100.0
    i = 1
    
    # Bucle regido por tolerancia o límite de iteraciones
    while error > TOLERANCIA and i <= MAX_ITERACIONES:
        m_act = f_derivada(x_act)
        x_next = x_act - (y_act / m_act)
        y_next = f_objetivo(x_next)
        
        # 2. TRAZADO DE LA TANGENTE (Solo se instancia en iteración 1, luego se transforma)
        if i == 1:
            escena.agregar_funcion(generar_tangente(x_act, y_act, m_act), color="#FFFF00", id="tangente", tiempo_animacion=1.0)
            
        # 3. CÁLCULO ALGEBRAICO Y VISUALIZACIÓN EN HUD
        str_error = f"{error:.4f}\\%" if i > 1 else "\\text{N/A}"
        texto_hud = f"""
        $$\\text{{Iteración: }} {i}$$
        $$x_{{{i}}} = {x_act:.4f} - \\frac{{f({x_act:.4f})}}{{f'({x_act:.4f})}}$$
        $$x_{{{i}}} \\approx {x_next:.4f}$$
        $$\\text{{Error: }} {str_error}$$
        """
        escena.agregar_algebra_flotante(texto_hud, posicion="UL", remover_al_final=True, tiempo_animacion=1.0, tiempo_espera=1.0)
        
        # 4. MARCA DE LA RAÍZ PROYECTADA EN EL EJE X (Blanco)
        escena.agregar_punto(x_next, 0.0, color="#FFFFFF", label=False, id="punto_corte", tiempo_animacion=0.5)
        escena.animar_linea_punteada(
            x1_ini=x_next, x1_fin=x_next, x2_ini=x_next, x2_fin=x_next, y1_ini=0.0, y2_ini=f_objetivo, 
            color="#FFFFFF", id="proy_c", tiempo_animacion=0.8
        )
        
        # 5. MOVIMIENTO EN PARALELO (Antes de que la proyección desaparezca)
        m_next = f_derivada(x_next)
        
        with escena.bloque_paralelo(tiempo_animacion=2.0, tiempo_espera=1.0):
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
        escena.eliminar_objeto(id="proy_c", animacion="Uncreate", tiempo_animacion=0.5, tiempo_espera=0.1)
        escena.eliminar_objeto(id="punto_corte", animacion="FadeOut", tiempo_animacion=0.5, tiempo_espera=0.2)
        
        # 7. ACTUALIZACIÓN DE VARIABLES Y ERROR
        error = abs((x_next - x_act) / x_next) * 100 if x_next != 0 else 100
        x_act = x_next
        y_act = y_next
        i += 1
        
    escena.desvanecer_todo(tiempo_animacion=2.0)
    escena.render(previsualizar=True)
