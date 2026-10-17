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

# ==========================================
# VECTOR DE TIEMPOS ESTÁNDAR
# ==========================================
ESCALA_TIEMPO = 1.0

TIEMPOS_BASE = {
    "PROY_ANIM": 0.8,
    "PROY_ESPERA": 1.0,
    "HUD_ANIM": 1.0,
    "HUD_ESPERA": 0.5,
    "ELIM_ANIM": 0.3,
    "ELIM_ESPERA": 0.1,
    "RIEMANN_ANIM": 1.2,
    "RIEMANN_ESPERA": 1.0,
    "FINAL_ANIM": 2.0
}
T = {clave: valor * ESCALA_TIEMPO for clave, valor in TIEMPOS_BASE.items()}

if __name__ == "__main__":
    
    escena = AnimadorGrafico(f_objetivo, x_min=-1.0, x_max=4.0)
    
    # 1. ETIQUETA FIJA (Esquina inferior derecha)
    escena.agregar_algebra_flotante(LABEL_FUNCION, posicion="DR", remover_al_final=False)
    
    # 2. DEFINICIÓN DEL INTERVALO (Proyecciones blancas punteadas)
    escena.animar_linea_punteada(
        x1_ini=A_LIM, x1_fin=A_LIM, x2_ini=A_LIM, x2_fin=A_LIM, 
        y1_ini=0.0, y2_ini=f_objetivo, color="#FFFFFF", id="proy_A", tiempo_animacion=T["PROY_ANIM"]
    )
    escena.animar_linea_punteada(
        x1_ini=B_LIM, x1_fin=B_LIM, x2_ini=B_LIM, x2_fin=B_LIM, 
        y1_ini=0.0, y2_ini=f_objetivo, color="#FFFFFF", id="proy_B", tiempo_animacion=T["PROY_ANIM"], tiempo_espera=T["PROY_ESPERA"]
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
        escena.agregar_algebra_flotante(texto_hud, posicion="UL", remover_al_final=True, tiempo_animacion=T["HUD_ANIM"], tiempo_espera=T["HUD_ESPERA"])
        
        if i > 0:
            escena.eliminar_objeto(id="area_riemann", animacion="FadeOut", tiempo_animacion=T["ELIM_ANIM"], tiempo_espera=T["ELIM_ESPERA"])
            
        escena.animar_integral(
            funcion=f_objetivo, x_min=A_LIM, x_max=B_LIM, dx=dx,
            color="#00FFFF", opacidad=0.6, id_area="area_riemann",
            tiempo_animacion=T["RIEMANN_ANIM"], tiempo_espera=T["RIEMANN_ESPERA"]
        )
            
    # 4. EL CLÍMAX: LA INTEGRAL DEFINIDA
    area_exacta = 7.5
    
    texto_final = f"""
    $$n \\to \\infty \\quad (\\Delta x \\to 0)$$
    $$A = \\int_{{{A_LIM:.0f}}}^{{{B_LIM:.0f}}} f(x) dx$$
    $$A = {area_exacta:.4f}$$
    """
    escena.agregar_algebra_flotante(texto_final, posicion="UL", remover_al_final=False, tiempo_animacion=T["HUD_ANIM"], tiempo_espera=T["HUD_ESPERA"])
    
    # === EL CROSSFADE PARALELO ===
    # En lugar de dejar morir la animación a negro, los rectángulos se funden 
    # exactamente al mismo tiempo que el azul vibrante se cristaliza encima.
    with escena.bloque_paralelo(tiempo_animacion=T["FINAL_ANIM"], tiempo_espera=T["FINAL_ANIM"]):
        escena.eliminar_objeto(id="area_riemann", animacion="FadeOut", tiempo_animacion=T["FINAL_ANIM"])
        escena.animar_integral(
            funcion=f_objetivo, x_min=A_LIM, x_max=B_LIM, dx=None,
            color="#0066FF", opacidad=0.7, id_area="integral_final",
            tiempo_animacion=T["FINAL_ANIM"]
        )
    
    # Cierre de la escena
    escena.desvanecer_todo(tiempo_animacion=T["FINAL_ANIM"])
    escena.render(previsualizar=True)
