import math
from manim import DOWN
from Planos.generar_plano import AnimadorGrafico

# 1. Definición Funcional
def f_objetivo(x: float) -> float:
    return 0.5 * x**2 + 1

# ==========================================
# VECTOR DE TIEMPOS ESTÁNDAR
# ==========================================
ESCALA_TIEMPO = 1.0

TIEMPOS_BASE = {
    "PUNTO_ANCLA_ANIM": 1.0,
    "PUNTO_ANCLA_ESPERA": 0.5,
    "PUNTO_MOVIL_ANIM": 2.0,
    "PUNTO_MOVIL_ESPERA": 0.5,
    "PROY_PUNT_ANIM": 1.5,
    "PROY_PUNT_ESPERA": 0.5,
    "LLAVE_ANIM": 1.0,
    "LLAVE_ESPERA": 1.0,
    "HUD_ANIM": 1.0,
    "HUD_ESPERA": 1.5,
    "SECANTE_ANIM": 3.5,
    "SECANTE_ESPERA": 1.0,
    "ELIM_HUD_ANIM": 0.8,
    "CONCLUSION_ANIM": 2.0,
    "CONCLUSION_ESPERA": 2.5,
    "FINAL_ANIM": 1.5
}
T = {clave: valor * ESCALA_TIEMPO for clave, valor in TIEMPOS_BASE.items()}

if __name__ == "__main__":
    escena = AnimadorGrafico(f_objetivo, x_min=-1.0, x_max=4.0)
    
    # Nodo ancla P(1, f(1))
    escena.agregar_punto(
        x=1.0, y=f_objetivo(1.0), 
        color="#FF0000", label=True, 
        tiempo_animacion=T["PUNTO_ANCLA_ANIM"], tiempo_espera=T["PUNTO_ANCLA_ESPERA"]
    )
    
    # Punto móvil Q
    escena.animar_punto_sobre_curva(
        x_inicio=1.0, x_fin=3.5, 
        funcion=f_objetivo, 
        color="#00FF00", 
        tiempo_animacion=T["PUNTO_MOVIL_ANIM"], tiempo_espera=T["PUNTO_MOVIL_ESPERA"]
    )
    
    # Línea de acotación vertical
    escena.animar_linea_punteada(
        x1_ini=3.5, x1_fin=3.5,
        x2_ini=3.5, x2_fin=3.5,
        y1_ini=f_objetivo, y2_ini=0, 
        color="#00FFFF", 
        tiempo_animacion=T["PROY_PUNT_ANIM"], tiempo_espera=T["PROY_PUNT_ESPERA"]
    )
    
    # Llave diferencial Delta x
    escena.animar_llave(
        x1_ini=1.0, x1_fin=1.0,
        x2_ini=3.5, x2_fin=3.5,
        y1_ini=0, y2_ini=0,
        texto=r"\Delta x",
        direccion=DOWN,
        color="#FF00FF",
        tiempo_animacion=T["LLAVE_ANIM"], tiempo_espera=T["LLAVE_ESPERA"]
    )
    
    # HUD diferencial
    hud = r"""$$m = \frac{f(x+\Delta x) - f(x)}{\Delta x}$$"""
    escena.agregar_algebra_flotante(
        fuente_o_texto=hud, posicion="UL", 
        id="hud_limite", tiempo_animacion=T["HUD_ANIM"], tiempo_espera=T["HUD_ESPERA"]
    )
    
    # Secante transicionando a tangente
    escena.animar_secante(
        x1_ini=1.0, x1_fin=1.0,
        x2_ini=3.5, x2_fin=1.00001,
        funcion=f_objetivo, color="#FFFF00",
        tiempo_animacion=T["SECANTE_ANIM"], tiempo_espera=T["SECANTE_ESPERA"]
    )
    
    # Purga y conclusión
    escena.eliminar_objeto(id="hud_limite", animacion="FadeOut", tiempo_animacion=T["ELIM_HUD_ANIM"])
    conclusion = r"f'(x) = \lim_{\Delta x \to 0} \frac{f(x+\Delta x) - f(x)}{\Delta x}"
    escena.transformar_a_texto(texto_latex=conclusion, tiempo_animacion=T["CONCLUSION_ANIM"], tiempo_espera=T["CONCLUSION_ESPERA"])
    escena.desvanecer_todo(animacion="FadeOut", tiempo_animacion=T["FINAL_ANIM"])
    
    escena.render(previsualizar=True)
