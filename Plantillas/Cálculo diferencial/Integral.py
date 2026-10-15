import math
from Planos.generar_plano import AnimadorGrafico

# ==========================================
# CONFIGURACIÓN DE LA ANIMACIÓN (INTEGRAL)
# ==========================================
def f_objetivo(x: float) -> float:
    return 0.5 * (x**2) + 1.0  

LABEL_FUNCION = r"$$f(x) = \frac{1}{2}x^2 + 1$$"
A_LIM = 0.0
B_LIM = 3.0

PASOS_N = [3, 6, 12, 30] 
# ==========================================

if __name__ == "__main__":
    
    escena = AnimadorGrafico(f_objetivo, x_min=-1.0, x_max=4.0)
    
    # 1. ETIQUETA FIJA (Esquina inferior derecha)
    escena.agregar_algebra_flotante(LABEL_FUNCION, posicion="DR", remover_al_final=False)
    
    # 2. DEFINICIÓN DEL INTERVALO (Proyecciones blancas punteadas)
    escena.animar_linea_punteada(
        x1_ini=A_LIM, x1_fin=A_LIM, x2_ini=A_LIM, x2_fin=A_LIM, 
        y1_ini=0.0, y2_ini=f_objetivo, color="#FFFFFF", id="proy_A", tiempo_animacion=0.8
    )
    escena.animar_linea_punteada(
        x1_ini=B_LIM, x1_fin=B_LIM, x2_ini=B_LIM, x2_fin=B_LIM, 
        y1_ini=0.0, y2_ini=f_objetivo, color="#FFFFFF", id="proy_B", tiempo_animacion=0.8, tiempo_espera=1.0
    )
    
    # 3. BUCLE DE SUMAS DE RIEMANN
    for i, n in enumerate(PASOS_N):
        dx = (B_LIM - A_LIM) / n
        area_aprox = sum(f_objetivo(A_LIM + k * dx) * dx for k in range(n))
        
        # HUD: Desglose de dónde sale Delta X
        texto_hud = f"""
        $$n = {n}$$
        $$\\Delta x = \\frac{{{B_LIM:.1f} - {A_LIM:.1f}}}{{{n}}} = {dx:.4f}$$
        $$A \\approx \\sum_{{i=1}}^{{{n}}} f(x_i) \\Delta x$$
        $$A \\approx {area_aprox:.4f}$$
        """
        escena.agregar_algebra_flotante(texto_hud, posicion="UL", remover_al_final=True, tiempo_animacion=1.0, tiempo_espera=0.5)
        
        if i > 0:
            escena.eliminar_objeto(id="area_riemann", animacion="FadeOut", tiempo_animacion=0.3, tiempo_espera=0.1)
            
        escena.animar_integral(
            funcion=f_objetivo, x_min=A_LIM, x_max=B_LIM, dx=dx,
            color="#00FFFF", opacidad=0.6, id_area="area_riemann",
            tiempo_animacion=1.2, tiempo_espera=1.0
        )
            
    # 4. EL CLÍMAX: LA INTEGRAL DEFINIDA
    area_exacta = 7.5
    
    texto_final = f"""
    $$n \\to \\infty \\quad (\\Delta x \\to 0)$$
    $$A = \\int_{{{A_LIM:.0f}}}^{{{B_LIM:.0f}}} f(x) dx$$
    $$A = {area_exacta:.4f}$$
    """
    escena.agregar_algebra_flotante(texto_final, posicion="UL", remover_al_final=False, tiempo_animacion=1.0, tiempo_espera=1.0)
    
    # === EL CROSSFADE PARALELO ===
    # En lugar de dejar morir la animación a negro, los rectángulos se funden 
    # exactamente al mismo tiempo que el azul vibrante se cristaliza encima.
    with escena.bloque_paralelo(tiempo_animacion=2.0, tiempo_espera=2.0):
        escena.eliminar_objeto(id="area_riemann", animacion="FadeOut", tiempo_animacion=2.0)
        escena.animar_integral(
            funcion=f_objetivo, x_min=A_LIM, x_max=B_LIM, dx=None,
            color="#0066FF", opacidad=0.7, id_area="integral_final",
            tiempo_animacion=2.0
        )
    
    # Cierre de la escena
    escena.desvanecer_todo(tiempo_animacion=2.0)
    escena.render(previsualizar=True)
