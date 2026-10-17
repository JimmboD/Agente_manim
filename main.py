import math
from Planos.generar_plano import AnimadorGrafico

# ==========================================
# CONFIGURACIÓN DE LA ANIMACIÓN (BISECCIÓN)
# ==========================================
def f_objetivo(x: float) -> float:
    return -2/3*x**2 + 10.19 + 34*math.exp(42*x)/(1444*math.sin(44*x)**2 + 23)

# Función auxiliar para renderizar la recta sobre el eje X
def f_eje_x(x: float) -> float:
    return 0.0

LABEL_FUNCION = r"$$f(x) = - \frac{2 x^{2}}{3} + 10.19 + \frac{34 e^{42 x}}{1444 \sin^{2}{\left(44 x \right)} + 23}$$"
A_INICIAL = -4.02
B_INICIAL = -2.24
TOLERANCIA = 0.0001
MAX_ITERACIONES = 5

# ==========================================
# VECTOR DE TIEMPOS ESTÁNDAR (5 iteraciones por minuto)
# ==========================================
ESCALA_TIEMPO = 0.73

TIEMPOS_BASE = {
    # Etiqueta inicial (Ajustada con la nueva API granular)
    "ETIQUETA_ESCRITURA": 0.8, 
    "ETIQUETA_ESPERA": 0.1,    
    
    # Paso 0: Puntos iniciales del intervalo [a, b]
    "PUNTOS_INI_ANIM": 0.6,
    "PUNTOS_INI_ESPERA": 0.2,

    # Paso 1: Despliegue de cálculos algebraicos en HUD
    "HUD_ANIM": 1.2,
    "HUD_ESPERA": 0.2, 

    # Paso 2: Proyección del punto medio al eje X
    "PROY_PUNTO_ANIM": 0.2,
    "PROY_PUNTO_ESPERA": 0.2,
    "PROY_LINEA_ANIM": 0.4,
    "PROY_LINEA_ESPERA": 0.2,

    # Paso 3: Limpieza de guías visuales temporales
    "LIMPIEZA_LINEA_ANIM": 0.2,
    "LIMPIEZA_LINEA_ESPERA": 0.0,
    "LIMPIEZA_PUNTO_ANIM": 0.2,
    "LIMPIEZA_PUNTO_ESPERA": 0.0,

    # Paso 4: Traslación del extremo sobre la curva
    "MOVIMIENTO_CURVA_ANIM": 1.2,
    "MOVIMIENTO_CURVA_ESPERA": 0.4,

    # Paso 5: Cierre y desvanecimiento final de la escena
    "FINAL_ANIM": 1.0,
    "FINAL_ESPERA": 0.2
}

# Vector de tiempos escalados por la variable controladora
T = {clave: valor * ESCALA_TIEMPO for clave, valor in TIEMPOS_BASE.items()}
# ==========================================

if __name__ == "__main__":
    
    escena = AnimadorGrafico(f_objetivo, x_min=-5.5, x_max=-0.7)
    
    # Etiqueta fija en la esquina inferior derecha haciendo uso de la API granular
    escena.agregar_algebra_flotante(
        LABEL_FUNCION, posicion="DR", remover_al_final=False,
        tiempo_escritura=T["ETIQUETA_ESCRITURA"], tiempo_espera=T["ETIQUETA_ESPERA"]
    )
    
    a, b = A_INICIAL, B_INICIAL
    fa, fb = f_objetivo(a), f_objetivo(b)
    
    # ESTADO INICIAL
    with escena.bloque_paralelo(tiempo_animacion=T["PUNTOS_INI_ANIM"], tiempo_espera=T["PUNTOS_INI_ESPERA"]):
        escena.agregar_punto(a, fa, color="#FFFF00", id="punto_A")
        escena.agregar_punto(b, fb, color="#FFFF00", id="punto_B")
        escena.agregar_funcion(f_eje_x, x_min=a, x_max=b, color="#FFFF00", id="recta_intervalo")
    
    error = 100.0
    c_prev = a
    i = 1
    
    # Bucle de Bisección
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
        $$\\text{{Iteración: }} {i}$$
        $$c_{{{i}}} = \\frac{{{a:.4f} + {b:.4f}}}{{2}} = {c:.4f}$$
        $$f(c_{{{i}}}) \\approx {fc:.4f}$$
        $$\\text{{Error: }} {str_error}$$
        """
        escena.agregar_algebra_flotante(
            texto_hud, posicion="UL", remover_al_final=True, 
            tiempo_animacion=T["HUD_ANIM"], tiempo_espera=T["HUD_ESPERA"]
        )
        
        # 3. PROYECCIÓN Y MARCA DEL PUNTO MEDIO EN EL EJE X
        escena.agregar_punto(
            c, 0.0, color="#FFFFFF", label=False, id="punto_c", 
            tiempo_animacion=T["PROY_PUNTO_ANIM"], tiempo_espera=T["PROY_PUNTO_ESPERA"]
        )
        escena.animar_linea_punteada(
            x1_ini=c, x1_fin=c, x2_ini=c, x2_fin=c, y1_ini=0.0, y2_ini=f_objetivo, 
            color="#FFFFFF", id="proy_c", 
            tiempo_animacion=T["PROY_LINEA_ANIM"], tiempo_espera=T["PROY_LINEA_ESPERA"]
        )
        
        # 4. ELIMINACIÓN DE LA PROYECCIÓN TEMPORAL
        escena.eliminar_objeto(
            id="proy_c", animacion="Uncreate", 
            tiempo_animacion=T["LIMPIEZA_LINEA_ANIM"], tiempo_espera=T["LIMPIEZA_LINEA_ESPERA"]
        )
        escena.eliminar_objeto(
            id="punto_c", animacion="FadeOut", 
            tiempo_animacion=T["LIMPIEZA_PUNTO_ANIM"], tiempo_espera=T["LIMPIEZA_PUNTO_ESPERA"]
        )
        
        # 5. ACTUALIZACIÓN DE LÍMITES Y TRASLACIÓN CONCURRENTE
        if fa * fc < 0:
            b_viejo = b
            b, fb = c, fc
            
            with escena.bloque_paralelo(tiempo_animacion=T["MOVIMIENTO_CURVA_ANIM"], tiempo_espera=T["MOVIMIENTO_CURVA_ESPERA"]):
                escena.animar_punto_sobre_curva(
                    x_inicio=b_viejo, x_fin=b, funcion=f_objetivo, 
                    color="#FFFF00", id="punto_B"
                )
                escena.transformar_objeto(
                    origen="recta_intervalo",
                    tipo_destino="funcion",
                    funcion=f_eje_x,
                    x_min=a,
                    x_max=b,
                    color="#FFFF00",
                    id_destino="recta_intervalo"
                )
        else:
            a_viejo = a
            a, fa = c, fc
            
            with escena.bloque_paralelo(tiempo_animacion=T["MOVIMIENTO_CURVA_ANIM"], tiempo_espera=T["MOVIMIENTO_CURVA_ESPERA"]):
                escena.animar_punto_sobre_curva(
                    x_inicio=a_viejo, x_fin=a, funcion=f_objetivo, 
                    color="#FFFF00", id="punto_A"
                )
                escena.transformar_objeto(
                    origen="recta_intervalo",
                    tipo_destino="funcion",
                    funcion=f_eje_x,
                    x_min=a,
                    x_max=b,
                    color="#FFFF00",
                    id_destino="recta_intervalo"
                )
                
        c_prev = c
        i += 1
        
    escena.desvanecer_todo(tiempo_animacion=T["FINAL_ANIM"], tiempo_espera=T["FINAL_ESPERA"])
    escena.render(previsualizar=True)