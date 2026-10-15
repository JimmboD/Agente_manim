/**
 * MANIM STUDIO — WORKFLOW INTEGRADO
 * - Animación manual con main.py ajustada a pantalla sin scroll inicial (consola abajo)
 * - Constructor de funciones estilo Scratch con renderizado en vivo
 * - Panel lateral izquierdo desplegable con acordeones colapsables por click
 * - Visualizador de documentación técnica (READMI.md)
 * - Cargador de plantillas matemáticas y selector de temas de alto contraste
 */

const state = {
  activeView: 'view-manual',
  activeFile: 'main.py',
  isRendering: false,
  isDirty: false,
  theme: localStorage.getItem('manim_theme') || 'blanco',
  quality: localStorage.getItem('manim_quality') || 'low_quality',
  scratchBlocks: [],
  docsLoaded: false,
  audio: {
    file: null,
    url: null,
    name: '',
    duration: 0,
    startOffset: 0.0,
    autoSync: true,
    isPlaying: false,
    isMuted: false,
    volume: 1.0
  }
};

// ==========================================================================
// 1. PLANTILLAS MATEMÁTICAS PREDISEÑADAS
// ==========================================================================
const TEMPLATES = {
  regla_falsa: `import math
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
        str_error = f"{error:.4f}\\\\%" if i > 1 else "\\\\text{N/A}"
        texto_hud = f"""
        $$\\\\text{{Iteración: }} {i}$$
        $$x_{{{i}}} = {b:.4f} - f({b:.4f}) \\\\frac{{{b:.4f} - {a:.4f}}}{{f({b:.4f}) - f({a:.4f})}}$$
        $$x_{{{i}}} \\\\approx {c:.4f}$$
        $$\\\\text{{Error: }} {str_error}$$
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
`,

  biseccion: `import math
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

if __name__ == "__main__":
    
    escena = AnimadorGrafico(f_objetivo, x_min=-0.5, x_max=2.0)
    
    # Etiqueta fija en la esquina inferior derecha
    escena.agregar_algebra_flotante(LABEL_FUNCION, posicion="DR", remover_al_final=False)
    
    a, b = A_INICIAL, B_INICIAL
    fa, fb = f_objetivo(a), f_objetivo(b)
    
    # ESTADO INICIAL: Intervalo [a, b]
    escena.agregar_punto(a, fa, color="#FFFF00", id="punto_A", tiempo_animacion=0.5, tiempo_espera=0.1)
    escena.agregar_punto(b, fb, color="#FFFF00", id="punto_B", tiempo_animacion=0.5, tiempo_espera=0.1)
    
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
            str_error = f"{error:.4f}\\\\%"
        else:
            str_error = "\\\\text{N/A}"
            
        texto_hud = f"""
        $$\\\\text{{Bisección - Iteración: }} {i}$$
        $$c_{{{i}}} = \\\\frac{{{a:.4f} + {b:.4f}}}{{2}} = {c:.4f}$$
        $$f(c_{{{i}}}) \\\\approx {fc:.4f}$$
        $$\\\\text{{Error: }} {str_error}$$
        """
        escena.agregar_algebra_flotante(texto_hud, posicion="UL", remover_al_final=True, tiempo_animacion=1.0, tiempo_espera=1.0)
        
        # 3. PROYECCIÓN Y MARCA DEL PUNTO MEDIO EN EL EJE X
        escena.agregar_punto(c, 0.0, color="#FFFFFF", label=False, id="punto_c", tiempo_animacion=0.5)
        escena.animar_linea_punteada(
            x1_ini=c, x1_fin=c, x2_ini=c, x2_fin=c, y1_ini=0.0, y2_ini=f_objetivo, 
            color="#FFFFFF", id="proy_c", tiempo_animacion=0.8
        )
        
        # 4. ELIMINACIÓN DE LA PROYECCIÓN TEMPORAL
        escena.eliminar_objeto(id="proy_c", animacion="Uncreate", tiempo_animacion=0.5, tiempo_espera=0.1)
        escena.eliminar_objeto(id="punto_c", animacion="FadeOut", tiempo_animacion=0.5, tiempo_espera=0.2)
        
        # 5. ACTUALIZACIÓN DE LÍMITES Y TRASLACIÓN SOBRE LA CURVA
        if fa * fc < 0:
            b_viejo = b
            b, fb = c, fc
            # El extremo derecho B viaja sobre la curva hacia el punto medio c
            escena.animar_punto_sobre_curva(
                x_inicio=b_viejo, x_fin=b, funcion=f_objetivo, 
                color="#FFFF00", id="punto_B", 
                tiempo_animacion=1.5, tiempo_espera=1.0
            )
        else:
            a_viejo = a
            a, fa = c, fc
            # El extremo izquierdo A viaja sobre la curva hacia el punto medio c
            escena.animar_punto_sobre_curva(
                x_inicio=a_viejo, x_fin=a, funcion=f_objetivo, 
                color="#FFFF00", id="punto_A", 
                tiempo_animacion=1.5, tiempo_espera=1.0
            )
            
        c_prev = c
        i += 1
        
    escena.desvanecer_todo(tiempo_animacion=2.0)
    escena.render(previsualizar=True)
`,

  newton_raphson: `import math
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
        str_error = f"{error:.4f}\\\\%" if i > 1 else "\\\\text{N/A}"
        texto_hud = f"""
        $$\\\\text{{Iteración: }} {i}$$
        $$x_{{{i}}} = {x_act:.4f} - \\\\frac{{f({x_act:.4f})}}{{f'({x_act:.4f})}}$$
        $$x_{{{i}}} \\\\approx {x_next:.4f}$$
        $$\\\\text{{Error: }} {str_error}$$
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
`,

  derivada_limite: `import math
from manim import DOWN
from Planos.generar_plano import AnimadorGrafico

# 1. Definición Funcional
def f_objetivo(x: float) -> float:
    return 0.5 * x**2 + 1

if __name__ == "__main__":
    escena = AnimadorGrafico(f_objetivo, x_min=-1.0, x_max=4.0)
    
    # Nodo ancla P(1, f(1))
    escena.agregar_punto(
        x=1.0, y=f_objetivo(1.0), 
        color="#FF0000", label=True, 
        tiempo_animacion=1.0, tiempo_espera=0.5
    )
    
    # Punto móvil Q
    escena.animar_punto_sobre_curva(
        x_inicio=1.0, x_fin=3.5, 
        funcion=f_objetivo, 
        color="#00FF00", 
        tiempo_animacion=2.0, tiempo_espera=0.5
    )
    
    # Línea de acotación vertical
    escena.animar_linea_punteada(
        x1_ini=3.5, x1_fin=3.5,
        x2_ini=3.5, x2_fin=3.5,
        y1_ini=f_objetivo, y2_ini=0, 
        color="#00FFFF", 
        tiempo_animacion=1.5, tiempo_espera=0.5
    )
    
    # Llave diferencial Delta x
    escena.animar_llave(
        x1_ini=1.0, x1_fin=1.0,
        x2_ini=3.5, x2_fin=3.5,
        y1_ini=0, y2_ini=0,
        texto=r"\\Delta x",
        direccion=DOWN,
        color="#FF00FF",
        tiempo_animacion=1.0, tiempo_espera=1.0
    )
    
    # HUD diferencial
    hud = r"""$$m = \\frac{f(x+\\Delta x) - f(x)}{\\Delta x}$$"""
    escena.agregar_algebra_flotante(
        fuente_o_texto=hud, posicion="UL", 
        id="hud_limite", tiempo_animacion=1.0, tiempo_espera=1.5
    )
    
    # Secante transicionando a tangente
    escena.animar_secante(
        x1_ini=1.0, x1_fin=1.0,
        x2_ini=3.5, x2_fin=1.00001,
        funcion=f_objetivo, color="#FFFF00",
        tiempo_animacion=3.5, tiempo_espera=1.0
    )
    
    # Purga y conclusión
    escena.eliminar_objeto(id="hud_limite", animacion="FadeOut", tiempo_animacion=0.8)
    conclusion = r"f'(x) = \\lim_{\\Delta x \\to 0} \\frac{f(x+\\Delta x) - f(x)}{\\Delta x}"
    escena.transformar_a_texto(texto_latex=conclusion, tiempo_animacion=2.0, tiempo_espera=2.5)
    escena.desvanecer_todo(animacion="FadeOut", tiempo_animacion=1.5)
    
    escena.render(previsualizar=True)
`,

  serie_taylor: `import math
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
        $$\\\\text{{Grado: }} {i}$$
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
`,

  integral: `import math
from Planos.generar_plano import AnimadorGrafico

# ==========================================
# CONFIGURACIÓN DE LA ANIMACIÓN (INTEGRAL)
# ==========================================
def f_objetivo(x: float) -> float:
    return 0.5 * (x**2) + 1.0  

LABEL_FUNCION = r"$$f(x) = \\frac{1}{2}x^2 + 1$$"
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
        $$\\\\Delta x = \\\\frac{{{B_LIM:.1f} - {A_LIM:.1f}}}{{{n}}} = {dx:.4f}$$
        $$A \\\\approx \\\\sum_{{i=1}}^{{{n}}} f(x_i) \\\\Delta x$$
        $$A \\\\approx {area_aprox:.4f}$$
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
    $$n \\\\to \\\\infty \\\\quad (\\\\Delta x \\\\to 0)$$
    $$A = \\\\int_{{{A_LIM:.0f}}}^{{{B_LIM:.0f}}} f(x) dx$$
    $$A = {area_exacta:.4f}$$
    """
    escena.agregar_algebra_flotante(texto_final, posicion="UL", remover_al_final=False, tiempo_animacion=1.0, tiempo_espera=1.0)
    
    # === EL CROSSFADE PARALELO ===
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
`,

  serie_fourier: `import math
import sympy as sp
from Planos.generar_plano import AnimadorGrafico

# ==========================================
# CONFIGURACIÓN DE LA ANIMACIÓN (FOURIER)
# ==========================================
x_sym = sp.Symbol('x')
LABEL_FUNCION = r"$$f(x) = \\\\text{Onda Cuadrada}$$"
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
        $$\\\\text{{Armónicos: }} {i}$$
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
`,

  curva_polinomica: `import math
from Planos.generar_plano import AnimadorGrafico

def f_curva(x: float) -> float:
    return 0.2 * (x - 2) * (x + 2) * x

if __name__ == "__main__":
    escena = AnimadorGrafico(f_curva, x_min=-3.0, x_max=3.0)
    
    escena.agregar_punto(-2.0, f_curva(-2.0), color="#00FFCC", label=True)
    escena.agregar_punto(0.0, f_curva(0.0), color="#FFCC00", label=True)
    escena.agregar_punto(2.0, f_curva(2.0), color="#FF007F", label=True)
    
    escena.animar_punto_sobre_curva(
        x_inicio=-2.5, x_fin=2.5, funcion=f_curva, 
        color="#FFFFFF", tiempo_animacion=3.0, tiempo_espera=1.0
    )
    
    escena.desvanecer_todo(animacion="FadeOut", tiempo_animacion=1.5)
    escena.render(previsualizar=True)
`,

  hud_algebra: `import math
from manim import DOWN
from Planos.generar_plano import AnimadorGrafico

def f_parabola(x: float) -> float:
    return x**2 - 2

if __name__ == "__main__":
    escena = AnimadorGrafico(f_parabola, x_min=-2.5, x_max=2.5)
    
    hud_formula = r"""$$f(x) = x^2 - 2$$"""
    escena.agregar_algebra_flotante(hud_formula, posicion="UL", id="hud_fn", tiempo_animacion=1.0)
    
    escena.agregar_punto(1.414, 0.0, color="#00FF00", label=True)
    escena.agregar_punto(-1.414, 0.0, color="#00FF00", label=True)
    
    escena.animar_llave(
        x1_ini=-1.414, x1_fin=-1.414, x2_ini=1.414, x2_fin=1.414,
        y1_ini=0, y2_ini=0, texto=r"2\\sqrt{2}", direccion=DOWN, color="#58C4DD"
    )
    
    escena.desvanecer_todo(animacion="FadeOut", tiempo_animacion=1.5)
    escena.render(previsualizar=True)
`,

  pasos_algebraicos: `$$\\textcolor{yellow}{y} = \\frac{f(b) - f(a)}{b - a} \\textcolor{yellow}{x} + \\textcolor{yellow}{b}$$
$$y = \\frac{f(b) - f(a)}{b - a} x + \\textcolor{yellow}{b}$$
$$f(c) = \\frac{f(b) - f(a)}{b - a} c + \\textcolor{yellow}{b}$$
$$\\textcolor{yellow}{b} = f(c) - \\frac{f(b) - f(a)}{b - a} c$$
$$y = \\frac{f(b) - f(a)}{b - a} x + \\left( f(c) - \\frac{f(b) - f(a)}{b - a} c \\right)$$
$$y - f(c) = \\textcolor{yellow}{\\frac{f(b) - f(a)}{b - a}} (x - c)$$`,

  purga_ciclo_vida: `import math
from Planos.generar_plano import AnimadorGrafico

def f_onda(x: float) -> float:
    return math.sin(x)

if __name__ == "__main__":
    escena = AnimadorGrafico(f_onda, x_min=-4.0, x_max=4.0)
    
    escena.agregar_punto(0.0, 0.0, color="#FF0000", id="punto_origen")
    escena.agregar_punto(1.57, 1.0, color="#00FF00", id="punto_maximo")
    escena.agregar_punto(3.14, 0.0, color="#0000FF", id="punto_nodo")
    
    # Purga progresiva por ID
    escena.eliminar_objeto(id="punto_origen", animacion="Uncreate", tiempo_animacion=1.0)
    escena.eliminar_objeto(id="punto_maximo", animacion="ShrinkToCenter", tiempo_animacion=1.0)
    escena.eliminar_objeto(id="punto_nodo", animacion="FadeOut", tiempo_animacion=1.0)
    
    escena.desvanecer_todo(animacion="FadeOut", tiempo_animacion=1.5)
    escena.render(previsualizar=True)
`
};

// ==========================================================================
// 2. INICIALIZACIÓN
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initQuality();
  initEditor();
  initNavigation();
  initCollapsibleAccordions();
  initScratchSystem();
  initTemplatesModal();
  initAudioModule();
  initEventListeners();
  initSSE();
  fetchLatestVideo();
  loadMainPy();
});

// ==========================================================================
// 3. SISTEMA DE TEMAS Y CALIDAD
// ==========================================================================
function initTheme() {
  const savedTheme = localStorage.getItem('manim_theme') || 'blanco';
  setTheme(savedTheme, false);
}

function setTheme(themeVal, notify = true) {
  state.theme = themeVal;
  localStorage.setItem('manim_theme', themeVal);
  document.body.setAttribute('data-theme', themeVal);

  document.querySelectorAll('.theme-card').forEach(card => {
    if (card.getAttribute('data-theme-val') === themeVal) {
      card.classList.add('active');
    } else {
      card.classList.remove('active');
    }
  });

  if (notify) {
    appendTerminalLine('system', `Tema activo: ${themeVal.toUpperCase()} (Lienzo negro de alto contraste)`);
  }
}

function initQuality() {
  const savedQuality = localStorage.getItem('manim_quality') || 'low_quality';
  state.quality = savedQuality;
  document.querySelectorAll(`input[name="manim-quality"], input[name="manim-quality-full"]`).forEach(radio => {
    if (radio.value === savedQuality) {
      radio.checked = true;
    }
  });
}

function setQuality(qualityVal) {
  state.quality = qualityVal;
  localStorage.setItem('manim_quality', qualityVal);
  document.querySelectorAll(`input[name="manim-quality"], input[name="manim-quality-full"]`).forEach(radio => {
    if (radio.value === qualityVal) {
      radio.checked = true;
    }
  });
  appendTerminalLine('system', `Calidad de render configurada a: ${qualityVal}`);
}

// ==========================================================================
// 4. NAVEGACIÓN Y VISTAS
// ==========================================================================
function initNavigation() {
  // Conectar botones del menú lateral
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const viewId = btn.getAttribute('data-view');
      switchView(viewId);
      closeLeftMenu();
    });
  });

  // Drawer izquierdo
  const btnToggle = document.getElementById('btn-toggle-left-menu');
  const btnClose = document.getElementById('btn-close-left-menu');
  const backdrop = document.getElementById('drawer-backdrop');

  if (btnToggle) btnToggle.addEventListener('click', toggleLeftMenu);
  if (btnClose) btnClose.addEventListener('click', closeLeftMenu);
  if (backdrop) backdrop.addEventListener('click', closeLeftMenu);
}

function toggleLeftMenu() {
  const drawer = document.getElementById('left-sidebar');
  const backdrop = document.getElementById('drawer-backdrop');
  const isOpen = drawer.classList.contains('open');
  if (isOpen) {
    closeLeftMenu();
  } else {
    drawer.classList.add('open');
    backdrop.classList.remove('hidden');
    backdrop.classList.add('active');
  }
}

function closeLeftMenu() {
  const drawer = document.getElementById('left-sidebar');
  const backdrop = document.getElementById('drawer-backdrop');
  if (drawer) drawer.classList.remove('open');
  if (backdrop) {
    backdrop.classList.remove('active');
    backdrop.classList.add('hidden');
  }
}

function switchView(viewId) {
  state.activeView = viewId;

  // Actualizar clases activas en views
  document.querySelectorAll('.app-view').forEach(view => {
    view.classList.remove('active');
  });
  const targetView = document.getElementById(viewId);
  if (targetView) targetView.classList.add('active');

  // Actualizar nav items
  document.querySelectorAll('.nav-item').forEach(item => {
    if (item.getAttribute('data-view') === viewId) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // Actualizar etiqueta del header
  const tabLabel = document.getElementById('active-tab-label');
  const titles = {
    'view-manual': 'Animación manual',
    'view-scratch': 'Insertar funciones',
    'view-settings': 'Ajustes',
    'view-docs': 'Documentación'
  };
  if (tabLabel && titles[viewId]) {
    tabLabel.textContent = titles[viewId];
  }

  // Cargar documentación si se entra en view-docs
  if (viewId === 'view-docs' && !state.docsLoaded) {
    loadDocs();
  }
}

// ==========================================================================
// 5. ACORDEONES COLAPSABLES POR CLICK (LABELS EXPANDIBLES / CONTRAÍBLES)
// ==========================================================================
function initCollapsibleAccordions() {
  const btnToggleAll = document.getElementById('btn-toggle-all-sections');

  const updateToggleAllButton = () => {
    if (!btnToggleAll) return;
    const contents = document.querySelectorAll('.drawer-body .collapsible-content');
    const allExpanded = Array.from(contents).every(c => !c.classList.contains('collapsed'));
    btnToggleAll.textContent = allExpanded ? 'Contraer todo' : 'Expandir todo';
  };

  document.querySelectorAll('.collapsible-header').forEach(header => {
    header.addEventListener('click', () => {
      const parent = header.closest('.collapsible-section');
      const content = parent.querySelector('.collapsible-content');
      const arrow = header.querySelector('.collapsible-arrow');
      
      if (!content) return;

      const isCollapsed = content.classList.contains('collapsed');
      if (isCollapsed) {
        content.classList.remove('collapsed');
        if (parent) parent.classList.add('expanded');
        if (arrow) arrow.innerHTML = '&blacktriangledown;';
      } else {
        content.classList.add('collapsed');
        if (parent) parent.classList.remove('expanded');
        if (arrow) arrow.innerHTML = '&blacktriangleright;';
      }
      updateToggleAllButton();
    });
  });

  if (btnToggleAll) {
    btnToggleAll.addEventListener('click', () => {
      const contents = document.querySelectorAll('.drawer-body .collapsible-content');
      const anyCollapsed = Array.from(contents).some(c => c.classList.contains('collapsed'));

      contents.forEach(content => {
        const parent = content.closest('.collapsible-section');
        const arrow = parent.querySelector('.collapsible-arrow');
        if (anyCollapsed) {
          // Si alguno está cerrado, abrir todos
          content.classList.remove('collapsed');
          if (parent) parent.classList.add('expanded');
          if (arrow) arrow.innerHTML = '&blacktriangledown;';
        } else {
          // Si todos están abiertos, cerrar todos
          content.classList.add('collapsed');
          if (parent) parent.classList.remove('expanded');
          if (arrow) arrow.innerHTML = '&blacktriangleright;';
        }
      });
      updateToggleAllButton();
    });
  }

  // Asegurar estado inicial del botón
  updateToggleAllButton();
}

// ==========================================================================
// 6. EDITOR DE CÓDIGO (MAIN.PY AJUSTADO A PANTALLA)
// ==========================================================================
function initEditor() {
  const editor = document.getElementById('code-editor');
  const lineNumbers = document.getElementById('line-numbers');
  const cursorLabel = document.getElementById('editor-cursor-pos');
  const unsavedBadge = document.getElementById('unsaved-badge');

  editor.addEventListener('input', () => {
    updateLineNumbers();
    state.isDirty = true;
    unsavedBadge.classList.remove('hidden');
  });

  editor.addEventListener('scroll', () => {
    lineNumbers.scrollTop = editor.scrollTop;
  });

  const updateCursor = () => {
    const selStart = editor.selectionStart;
    const textBefore = editor.value.substring(0, selStart);
    const lines = textBefore.split('\n');
    const lineNum = lines.length;
    const colNum = lines[lines.length - 1].length + 1;
    cursorLabel.textContent = `Línea ${lineNum}, Col ${colNum}`;
  };

  editor.addEventListener('keyup', updateCursor);
  editor.addEventListener('click', updateCursor);

  editor.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = editor.selectionStart;
      const end = editor.selectionEnd;
      editor.value = editor.value.substring(0, start) + '    ' + editor.value.substring(end);
      editor.selectionStart = editor.selectionEnd = start + 4;
      updateLineNumbers();
      state.isDirty = true;
      unsavedBadge.classList.remove('hidden');
    }

    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
      e.preventDefault();
      saveMainPy();
    }

    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleRunMain();
    }
  });
}

function updateLineNumbers() {
  const editor = document.getElementById('code-editor');
  const lineNumbers = document.getElementById('line-numbers');
  const lineCount = editor.value.split('\n').length;
  let html = '';
  for (let i = 1; i <= lineCount; i++) {
    html += i + '<br>';
  }
  lineNumbers.innerHTML = html;
}

function updateActiveFileUI(fileName) {
  state.activeFile = fileName;
  const fileNameEl = document.getElementById('editor-file-name');
  if (fileNameEl) fileNameEl.textContent = fileName;
  const indicatorEl = document.getElementById('active-file-indicator');
  if (indicatorEl) indicatorEl.textContent = fileName;
  const btnRunText = document.getElementById('btn-run-text');
  if (btnRunText) {
    btnRunText.textContent = fileName === 'pasos_algebraicos.txt' ? 'Ejecutar Pasos algebráicos' : 'Ejecutar main.py';
  }
}

async function loadMainPy(targetFile = null) {
  const fileToLoad = targetFile || state.activeFile || 'main.py';
  state.activeFile = fileToLoad;
  try {
    const res = await fetch(`/api/get_main?file=${encodeURIComponent(fileToLoad)}`);
    if (!res.ok) throw new Error(`Error al leer ${fileToLoad}`);
    const data = await res.json();
    const editor = document.getElementById('code-editor');
    editor.value = data.code;
    updateLineNumbers();
    state.isDirty = false;
    document.getElementById('unsaved-badge').classList.add('hidden');
    updateActiveFileUI(fileToLoad);
    appendTerminalLine('system', `${fileToLoad} cargado desde disco (${editor.value.split('\n').length} líneas).`);
  } catch (err) {
    appendTerminalLine('error', `Error cargando ${fileToLoad}: ${err.message}`);
  }
}

async function saveMainPy() {
  const editor = document.getElementById('code-editor');
  const fileToSave = state.activeFile || 'main.py';
  try {
    const res = await fetch('/api/save_main', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: editor.value, file: fileToSave })
    });
    if (!res.ok) throw new Error(`Error al guardar ${fileToSave}`);
    state.isDirty = false;
    document.getElementById('unsaved-badge').classList.add('hidden');
    appendTerminalLine('system', `${fileToSave} guardado en disco exitosamente.`);
  } catch (err) {
    appendTerminalLine('error', `Error guardando ${fileToSave}: ${err.message}`);
  }
}

// ==========================================================================
// 7. EJECUCIÓN DEL MOTOR MANIM
// ==========================================================================
async function handleRunMain(customCode = null) {
  if (state.isRendering) return;

  const editor = document.getElementById('code-editor');
  const codeToRun = customCode !== null ? customCode : editor.value;
  const activeFile = state.activeFile || 'main.py';

  appendTerminalLine('info', '==========================================================');
  appendTerminalLine('info', `Iniciando ejecución de ${activeFile} (Calidad: ${state.quality})...`);

  try {
    const res = await fetch('/api/run_main', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: codeToRun, file: activeFile, quality: state.quality })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Fallo al iniciar ejecución');
    }

    state.isDirty = false;
    document.getElementById('unsaved-badge').classList.add('hidden');
  } catch (err) {
    appendTerminalLine('error', `Error al ejecutar: ${err.message}`);
    handleServerStatusUpdate({ state: 'error' });
  }
}

// ==========================================================================
// 8. EVENTOS SSE Y CONSOLA EN TIEMPO REAL
// ==========================================================================
function initSSE() {
  const eventSource = new EventSource('/api/events');

  eventSource.addEventListener('connected', () => {
    appendTerminalLine('system', 'Conexión SSE activa con Manim Studio.');
  });

  eventSource.addEventListener('log', (e) => {
    const data = JSON.parse(e.data);
    appendTerminalLine(data.level || 'info', data.text);
  });

  eventSource.addEventListener('status', (e) => {
    const data = JSON.parse(e.data);
    handleServerStatusUpdate(data);
  });

  eventSource.addEventListener('video', (e) => {
    const data = JSON.parse(e.data);
    if (data.video_url) {
      loadVideoPlayer(data.video_url);
    }
  });
}

function handleServerStatusUpdate(data) {
  const statusPill = document.getElementById('engine-status-pill');
  const overlay = document.getElementById('render-overlay');
  const btnRun = document.getElementById('btn-run');
  const btnRunText = document.getElementById('btn-run-text');

  if (data.state === 'rendering') {
    state.isRendering = true;
    statusPill.className = 'status-indicator rendering';
    statusPill.textContent = 'Ejecutando';
    btnRun.disabled = true;
    btnRunText.textContent = 'Compilando...';
    overlay.classList.remove('hidden');
  } else if (data.state === 'success') {
    state.isRendering = false;
    statusPill.className = 'status-indicator ready';
    statusPill.textContent = 'Listo';
    btnRun.disabled = false;
    btnRunText.textContent = 'Ejecutar main.py';
    overlay.classList.add('hidden');

    if (data.video_url) {
      loadVideoPlayer(data.video_url);
    }
  } else if (data.state === 'error') {
    state.isRendering = false;
    statusPill.className = 'status-indicator error';
    statusPill.textContent = 'Error';
    btnRun.disabled = false;
    btnRunText.textContent = 'Reintentar Ejecución';
    overlay.classList.add('hidden');
  }
}

function appendTerminalLine(level, text) {
  const terminal = document.getElementById('terminal-screen');
  const line = document.createElement('div');
  line.className = `term-line term-${level}`;

  const now = new Date();
  const timeStr = now.toTimeString().split(' ')[0];
  line.innerHTML = `<span class="term-timestamp">[${timeStr}]</span> ${escapeHtml(text)}`;

  terminal.appendChild(line);
  terminal.scrollTop = terminal.scrollHeight;
}

function clearTerminal() {
  const terminal = document.getElementById('terminal-screen');
  terminal.innerHTML = '<div class="term-line term-system"><span class="term-timestamp">[00:00:00]</span> Consola limpiada por el usuario.</div>';
}

function copyTerminalLogs() {
  const terminal = document.getElementById('terminal-screen');
  navigator.clipboard.writeText(terminal.innerText).then(() => {
    alert('Registros copiados al portapapeles.');
  });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ==========================================================================
// 9. REPRODUCTOR DE VIDEO
// ==========================================================================
async function fetchLatestVideo() {
  try {
    const res = await fetch('/api/latest_video');
    if (res.ok) {
      const data = await res.json();
      if (data.video_url) {
        loadVideoPlayer(data.video_url);
      }
    }
  } catch (err) {}
}

function loadVideoPlayer(videoUrl) {
  // 1. Reproductor en Animación Manual
  const video = document.getElementById('manim-video-player');
  const source = document.getElementById('video-source');
  const placeholder = document.getElementById('video-placeholder');
  const metaBadge = document.getElementById('video-meta');
  const btnDownload = document.getElementById('btn-download-video');
  const btnRestart = document.getElementById('btn-restart-video');

  source.src = videoUrl;
  video.load();

  state.currentVideoUrl = videoUrl;
  video.onloadeddata = () => {
    placeholder.style.display = 'none';
    metaBadge.textContent = `${video.videoWidth}x${video.videoHeight} &bull; ${video.duration.toFixed(1)}s`;
    btnDownload.href = videoUrl;
    btnDownload.classList.remove('disabled');
    btnRestart.disabled = false;
    updateDownloadButtonUI();
    
    // Si hay audio activo, posicionar en el offset inicial configurado
    if (state.audio.url && state.audio.autoSync) {
      const audio = document.getElementById('manim-audio-player');
      if (audio) {
        audio.currentTime = state.audio.startOffset;
      }
    }
    video.play().catch(() => {});
  };

  // 2. Reproductor en Insertar Funciones (Scratch)
  const scratchVideo = document.getElementById('scratch-video-player');
  const scratchSource = document.getElementById('scratch-video-source');
  const scratchPlaceholder = document.getElementById('scratch-video-placeholder');

  if (scratchVideo && scratchSource) {
    scratchSource.src = videoUrl;
    scratchVideo.load();
    scratchVideo.onloadeddata = () => {
      if (scratchPlaceholder) scratchPlaceholder.style.display = 'none';
      scratchVideo.play().catch(() => {});
    };
  }
}

// ==========================================================================
// 10. CONSTRUCTOR DE FUNCIONES ESTILO SCRATCH
// ==========================================================================
const BLOCK_DEFS = {
  punto: {
    name: 'agregar_punto',
    category: 'geo',
    badge: '⊙',
    fields: [
      { key: 'x', label: 'X', type: 'number', default: 1.0, step: 0.5 },
      { key: 'y', label: 'Y (f(x) o número)', type: 'text', default: 'f_objetivo(1.0)' },
      { key: 'color', label: 'Color', type: 'color', default: '#FF0000' },
      { key: 'label', label: 'Mostrar Etiqueta', type: 'select', default: 'True', options: ['True', 'False'] },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.0, step: 0.25 },
      { key: 't_wait', label: 'T. Espera (s)', type: 'number', default: 0.5, step: 0.25 }
    ],
    toCode: (v) => `    escena.agregar_punto(${v.x}, ${v.y}, color="${v.color}", label=${v.label}, tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`
  },

  punto_curva: {
    name: 'animar_punto_sobre_curva',
    category: 'geo',
    badge: '●→',
    fields: [
      { key: 'x_ini', label: 'X Inicio', type: 'number', default: 1.0, step: 0.5 },
      { key: 'x_fin', label: 'X Fin', type: 'number', default: 3.5, step: 0.5 },
      { key: 'color', label: 'Color', type: 'color', default: '#00FF00' },
      { key: 'id', label: 'ID (Opcional p/ Memoria)', type: 'text', default: '' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 2.0, step: 0.25 },
      { key: 't_wait', label: 'T. Espera (s)', type: 'number', default: 0.5, step: 0.25 }
    ],
    toCode: (v) => {
      const idParam = v.id ? `, id="${v.id}"` : '';
      return `    escena.animar_punto_sobre_curva(x_inicio=${v.x_ini}, x_fin=${v.x_fin}, funcion=f_objetivo, color="${v.color}"${idParam}, tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`;
    }
  },

  fade_in_plano: {
    name: 'fade_in_plano',
    category: 'geo',
    badge: '⊞',
    fields: [
      { key: 'x_min', label: 'X Mínimo', type: 'number', default: -5.0, step: 0.5 },
      { key: 'x_max', label: 'X Máximo', type: 'number', default: 5.0, step: 0.5 },
      { key: 'color', label: 'Color Cuadrícula', type: 'color', default: '#2563EB' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.5, step: 0.25 },
      { key: 't_wait', label: 'T. Espera (s)', type: 'number', default: 1.0, step: 0.25 }
    ],
    toCode: (v) => `    escena.fade_in_plano(x_min=${v.x_min}, x_max=${v.x_max}, color="${v.color}", tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`
  },

  funcion: {
    name: 'agregar_funcion',
    category: 'func',
    badge: 'ƒ(x)',
    fields: [
      { key: 'color', label: 'Color Curva', type: 'color', default: '#00FFCC' },
      { key: 'id', label: 'ID del Objeto', type: 'text', default: 'curva_auxiliar' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 2.0, step: 0.25 },
      { key: 't_wait', label: 'T. Espera (s)', type: 'number', default: 1.0, step: 0.25 }
    ],
    toCode: (v) => `    escena.agregar_funcion(f_objetivo, color="${v.color}", id="${v.id}", tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`
  },

  secante: {
    name: 'animar_secante',
    category: 'func',
    badge: '⊿',
    fields: [
      { key: 'x1_ini', label: 'X1 Inicio', type: 'number', default: 1.0, step: 0.5 },
      { key: 'x1_fin', label: 'X1 Fin', type: 'number', default: 1.0, step: 0.5 },
      { key: 'x2_ini', label: 'X2 Inicio', type: 'number', default: 3.5, step: 0.5 },
      { key: 'x2_fin', label: 'X2 Fin (1.00001 -> Tangente)', type: 'number', default: 1.00001, step: 0.0001 },
      { key: 'color', label: 'Color Recta', type: 'color', default: '#FFFF00' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 3.5, step: 0.25 }
    ],
    toCode: (v) => `    escena.animar_secante(x1_ini=${v.x1_ini}, x1_fin=${v.x1_fin}, x2_ini=${v.x2_ini}, x2_fin=${v.x2_fin}, funcion=f_objetivo, color="${v.color}", tiempo_animacion=${v.t_anim}, tiempo_espera=1.0)`
  },

  convergencia_parametrica: {
    name: 'animar_convergencia_parametrica',
    category: 'func',
    badge: '⟳',
    fields: [
      { key: 'x_fijo', label: 'X Fijo (Ancla)', type: 'number', default: 0.0, step: 0.25 },
      { key: 'x_movil_ini', label: 'X Móvil Inicio', type: 'number', default: 1.5, step: 0.25 },
      { key: 'x_movil_fin', label: 'X Móvil Fin (C)', type: 'number', default: 0.8, step: 0.05 },
      { key: 'id_secante', label: 'ID Secante', type: 'text', default: 'secante' },
      { key: 'id_punto_curva', label: 'ID Punto Curva', type: 'text', default: 'punto_B' },
      { key: 'id_punto_raiz', label: 'ID Punto Raíz', type: 'text', default: 'punto_raiz' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 2.0, step: 0.25 },
      { key: 't_wait', label: 'T. Espera (s)', type: 'number', default: 1.0, step: 0.25 }
    ],
    toCode: (v) => `    escena.animar_convergencia_parametrica(funcion=f_objetivo, x_fijo=${v.x_fijo}, x_movil_ini=${v.x_movil_ini}, x_movil_fin=${v.x_movil_fin}, id_secante="${v.id_secante}", id_punto_curva="${v.id_punto_curva}", id_punto_raiz="${v.id_punto_raiz}", tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`
  },

  integral: {
    name: 'animar_integral',
    category: 'func',
    badge: '∫',
    fields: [
      { key: 'x_min', label: 'X Mínimo', type: 'number', default: 0.0, step: 0.5 },
      { key: 'x_max', label: 'X Máximo', type: 'number', default: 2.0, step: 0.5 },
      { key: 'dx', label: 'dx Riemann (vacío = continua)', type: 'text', default: '0.2' },
      { key: 'color', label: 'Color', type: 'color', default: '#00FFFF' },
      { key: 'opacidad', label: 'Opacidad (0 a 1)', type: 'number', default: 0.5, step: 0.1 },
      { key: 'id', label: 'ID', type: 'text', default: 'area_1' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.0, step: 0.25 },
      { key: 't_wait', label: 'T. Espera (s)', type: 'number', default: 0.5, step: 0.25 }
    ],
    toCode: (v) => {
      const dxParam = (v.dx && v.dx.trim() && v.dx.trim().toLowerCase() !== 'none') ? `dx=${v.dx.trim()}` : `dx=None`;
      const idParam = v.id ? `, id_area="${v.id}"` : '';
      return `    escena.animar_integral(f_objetivo, x_min=${v.x_min}, x_max=${v.x_max}, ${dxParam}, color="${v.color}", opacidad=${v.opacidad}${idParam}, tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`;
    }
  },

  linea_punteada: {
    name: 'animar_linea_punteada',
    category: 'dim',
    badge: '┊',
    fields: [
      { key: 'x', label: 'Coordenada X', type: 'number', default: 3.5, step: 0.5 },
      { key: 'color', label: 'Color', type: 'color', default: '#00FFFF' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.5, step: 0.25 }
    ],
    toCode: (v) => `    escena.animar_linea_punteada(x1_ini=${v.x}, x1_fin=${v.x}, x2_ini=${v.x}, x2_fin=${v.x}, y1_ini=f_objetivo, y2_ini=0, color="${v.color}", tiempo_animacion=${v.t_anim}, tiempo_espera=0.5)`
  },

  llave: {
    name: 'animar_llave',
    category: 'dim',
    badge: '{ }',
    fields: [
      { key: 'x1', label: 'X Inicio', type: 'number', default: 1.0, step: 0.5 },
      { key: 'x2', label: 'X Fin', type: 'number', default: 3.5, step: 0.5 },
      { key: 'texto', label: 'Etiqueta LaTeX', type: 'latex', default: '\\Delta x' },
      { key: 'color', label: 'Color', type: 'color', default: '#FF00FF' },
      { key: 'dir', label: 'Dirección', type: 'select', default: 'DOWN', options: ['DOWN', 'UP', 'LEFT', 'RIGHT'] }
    ],
    toCode: (v) => `    escena.animar_llave(x1_ini=${v.x1}, x1_fin=${v.x1}, x2_ini=${v.x2}, x2_fin=${v.x2}, y1_ini=0, y2_ini=0, texto=r"${v.texto}", direccion=${v.dir}, color="${v.color}", tiempo_animacion=1.0, tiempo_espera=1.0)`
  },

  algebra_flotante: {
    name: 'agregar_algebra_flotante',
    category: 'tex',
    badge: '∑',
    fields: [
      { key: 'pos', label: 'Posición Viewport', type: 'select', default: 'UL', options: ['UL', 'UR', 'DL', 'DR'] },
      { key: 'id', label: 'ID para Purga', type: 'text', default: 'hud_limite' },
      { key: 'formula', label: 'Fórmula en LaTeX', type: 'latex', default: 'm = \\frac{f(x+\\Delta x) - f(x)}{\\Delta x}' }
    ],
    toCode: (v) => `    escena.agregar_algebra_flotante(r"""$$${v.formula}$$""", posicion="${v.pos}", id="${v.id}", tiempo_animacion=1.0, tiempo_espera=1.0)`
  },

  transformar_texto: {
    name: 'transformar_a_texto',
    category: 'tex',
    badge: 'Tx',
    fields: [
      { key: 'formula', label: 'Ecuación Final', type: 'latex', default: 'f\'(x) = \\lim_{\\Delta x \\to 0} \\frac{f(x+\\Delta x) - f(x)}{\\Delta x}' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 2.0, step: 0.25 },
      { key: 't_wait', label: 'T. Espera (s)', type: 'number', default: 2.0, step: 0.25 }
    ],
    toCode: (v) => `    escena.transformar_a_texto(texto_latex=r"${v.formula}", tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`
  },

  transformar_objeto: {
    name: 'transformar_objeto',
    category: 'tex',
    badge: '⇄',
    fields: [
      { key: 'origen', label: 'ID Origen (vacío = último)', type: 'text', default: '' },
      { key: 'tipo_dest', label: 'Tipo Destino', type: 'select', default: 'funcion', options: ['funcion', 'punto', 'label'] },
      { key: 'dest_valor', label: 'Valor / Fórmula / Coord (X, Y)', type: 'latex', default: 'x**2 - 1' },
      { key: 'color', label: 'Color Destino', type: 'color', default: '#FFFF00' },
      { key: 'id_dest', label: 'ID Destino (opcional)', type: 'text', default: '' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.5, step: 0.25 }
    ],
    toCode: (v) => {
      const origArg = v.origen ? `origen="${v.origen}", ` : '';
      const idDestArg = v.id_dest ? `, id_destino="${v.id_dest}"` : '';
      if (v.tipo_dest === 'funcion') {
        const expr = v.dest_valor.replace(/^f\(x\)\s*=\s*/, '');
        return `    escena.transformar_objeto(${origArg}tipo_destino="funcion", funcion=lambda x: ${expr}, color="${v.color}"${idDestArg}, tiempo_animacion=${v.t_anim}, tiempo_espera=1.0)`;
      } else if (v.tipo_dest === 'punto') {
        const parts = v.dest_valor.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
        const px = parts[0] !== undefined ? parts[0] : 1.0;
        const py = parts[1] !== undefined ? parts[1] : 1.0;
        return `    escena.transformar_objeto(${origArg}tipo_destino="punto", x=${px}, y=${py}, color="${v.color}", label=True${idDestArg}, tiempo_animacion=${v.t_anim}, tiempo_espera=1.0)`;
      } else {
        return `    escena.transformar_objeto(${origArg}tipo_destino="label", texto=r"""${v.dest_valor}""", color="${v.color}", posicion="center"${idDestArg}, tiempo_animacion=${v.t_anim}, tiempo_espera=1.0)`;
      }
    }
  },

  transformar_plano: {
    name: 'transformar_a_plano',
    category: 'tex',
    badge: 'ℝ²',
    fields: [
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.5, step: 0.25 },
      { key: 't_wait', label: 'T. Espera (s)', type: 'number', default: 0.5, step: 0.25 }
    ],
    toCode: (v) => `    escena.transformar_a_plano(tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`
  },

  eliminar_objeto: {
    name: 'eliminar_objeto',
    category: 'purge',
    badge: '⊖',
    fields: [
      { key: 'id', label: 'ID del Objeto a Purgar', type: 'text', default: 'hud_limite' },
      { key: 'anim', label: 'Animación de Salida', type: 'select', default: 'FadeOut', options: ['FadeOut', 'Uncreate', 'ShrinkToCenter'] },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.0, step: 0.25 }
    ],
    toCode: (v) => `    escena.eliminar_objeto(id="${v.id}", animacion="${v.anim}", tiempo_animacion=${v.t_anim}, tiempo_espera=0.5)`
  },

  fade_out_plano: {
    name: 'fade_out_plano',
    category: 'purge',
    badge: '⊞⁻',
    fields: [
      { key: 'anim', label: 'Animación de Salida', type: 'select', default: 'FadeOut', options: ['FadeOut', 'Uncreate', 'ShrinkToCenter'] },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.5, step: 0.25 }
    ],
    toCode: (v) => `    escena.fade_out_plano(animacion="${v.anim}", tiempo_animacion=${v.t_anim}, tiempo_espera=0.5)`
  },

  desvanecer_todo: {
    name: 'desvanecer_todo',
    category: 'purge',
    badge: '∅',
    fields: [
      { key: 'anim', label: 'Efecto de Salida', type: 'select', default: 'FadeOut', options: ['FadeOut', 'ShrinkToCenter'] },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.5, step: 0.25 }
    ],
    toCode: (v) => `    escena.desvanecer_todo(animacion="${v.anim}", tiempo_animacion=${v.t_anim})`
  },

  iniciar_bloque_paralelo: {
    name: 'iniciar_bloque_paralelo',
    category: 'parallel',
    badge: '⫘',
    fields: [],
    toCode: () => `    escena.iniciar_bloque_paralelo()`
  },

  cerrar_bloque_paralelo: {
    name: 'cerrar_bloque_paralelo',
    category: 'parallel',
    badge: '⫙',
    fields: [
      { key: 't_anim', label: 'T. Anim Simultánea (s)', type: 'number', default: 1.5, step: 0.25 },
      { key: 't_wait', label: 'T. Espera Posterior (s)', type: 'number', default: 1.0, step: 0.25 }
    ],
    toCode: (v) => `    escena.cerrar_bloque_paralelo(tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`
  }
};

function initScratchSystem() {
  // Click en bloques de la paleta
  document.querySelectorAll('[data-add-block]').forEach(el => {
    el.addEventListener('click', () => {
      const blockKey = el.getAttribute('data-add-block');
      addScratchBlock(blockKey);
    });
  });

  // Botones de acción del Scratch Stack
  document.getElementById('btn-scratch-render').addEventListener('click', handleScratchRender);
  document.getElementById('btn-scratch-to-main').addEventListener('click', handleScratchExportToMain);
  document.getElementById('btn-scratch-clear').addEventListener('click', () => {
    state.scratchBlocks = [];
    renderScratchStack();
  });

  // Cargar bloques iniciales por defecto
  state.scratchBlocks = [
    createBlockInstance('punto', { x: 1.0, y: 'f_objetivo(1.0)', color: '#FF0000', label: 'True', t_anim: 1.0, t_wait: 0.5 }),
    createBlockInstance('punto_curva', { x_ini: 1.0, x_fin: 3.5, color: '#00FF00', t_anim: 2.0, t_wait: 0.5 }),
    createBlockInstance('llave', { x1: 1.0, x2: 3.5, texto: '\\Delta x', color: '#FF00FF', dir: 'DOWN' }),
    createBlockInstance('desvanecer_todo', { anim: 'FadeOut', t_anim: 1.5 })
  ];

  renderScratchStack();
}

function createBlockInstance(type, customValues = {}) {
  const def = BLOCK_DEFS[type];
  if (!def) return null;
  const values = {};
  def.fields.forEach(f => {
    values[f.key] = customValues[f.key] !== undefined ? customValues[f.key] : f.default;
  });
  return {
    id: 'block_' + Math.random().toString(36).substring(2, 9),
    type,
    values
  };
}

function addScratchBlock(type) {
  const inst = createBlockInstance(type);
  if (inst) {
    state.scratchBlocks.push(inst);
    renderScratchStack();
  }
}

function renderScratchStack() {
  const container = document.getElementById('scratch-stack-list');
  if (!container) return;

  if (state.scratchBlocks.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding:3rem 1rem; color:var(--color-subtle);">
        <p style="font-size:1.1rem; margin-bottom:0.5rem; color:var(--color-primary);">La secuencia está vacía</p>
        <p style="font-size:0.8rem;">Haz click en cualquier bloque de la paleta izquierda para agregarlo a la animación.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = '';
  state.scratchBlocks.forEach((block, idx) => {
    const def = BLOCK_DEFS[block.type];
    if (!def) return;

    const el = document.createElement('div');
    el.className = `scratch-stack-item block-${def.category}`;
    el.setAttribute('data-block-id', block.id);

    // Cabecera del bloque
    let fieldsHtml = '';
    def.fields.forEach(f => {
      const val = block.values[f.key];
      if (f.type === 'select') {
        const opts = f.options.map(o => `<option value="${o}" ${o == val ? 'selected' : ''}>${o}</option>`).join('');
        fieldsHtml += `
          <div class="block-field">
            <label>${f.label}</label>
            <select data-field-key="${f.key}">${opts}</select>
          </div>
        `;
      } else if (f.type === 'latex') {
        fieldsHtml += `
          <div class="block-field" style="grid-column: span 2;">
            <label>${f.label}</label>
            <input type="text" data-field-key="${f.key}" value="${escapeHtml(val)}" class="code-font latex-input">
            <div class="block-latex-preview" id="prev-${block.id}-${f.key}"></div>
          </div>
        `;
      } else {
        const stepAttr = f.step ? `step="${f.step}"` : '';
        fieldsHtml += `
          <div class="block-field">
            <label>${f.label}</label>
            <input type="${f.type}" data-field-key="${f.key}" value="${escapeHtml(val)}" ${stepAttr}>
          </div>
        `;
      }
    });

    el.innerHTML = `
      <div class="stack-item-top">
        <div class="stack-item-info">
          <span class="block-badge">${def.badge}</span>
          <span>${idx + 1}. ${def.name}()</span>
        </div>
        <div class="stack-item-tools">
          <button class="btn-block-tool btn-move-up" title="Mover arriba" ${idx === 0 ? 'disabled' : ''}>▲</button>
          <button class="btn-block-tool btn-move-down" title="Mover abajo" ${idx === state.scratchBlocks.length - 1 ? 'disabled' : ''}>▼</button>
          <button class="btn-block-tool btn-block-delete" title="Eliminar bloque">&times;</button>
        </div>
      </div>
      <div class="stack-params-grid">
        ${fieldsHtml}
      </div>
    `;

    // Conectar eventos de cambio
    el.querySelectorAll('input, select').forEach(input => {
      const key = input.getAttribute('data-field-key');
      input.addEventListener('input', () => {
        block.values[key] = input.value;
        if (input.classList.contains('latex-input')) {
          renderLatexPreview(document.getElementById(`prev-${block.id}-${key}`), input.value);
        }
      });
    });

    // Reordenar y eliminar
    el.querySelector('.btn-move-up').addEventListener('click', () => {
      if (idx > 0) {
        const temp = state.scratchBlocks[idx];
        state.scratchBlocks[idx] = state.scratchBlocks[idx - 1];
        state.scratchBlocks[idx - 1] = temp;
        renderScratchStack();
      }
    });

    el.querySelector('.btn-move-down').addEventListener('click', () => {
      if (idx < state.scratchBlocks.length - 1) {
        const temp = state.scratchBlocks[idx];
        state.scratchBlocks[idx] = state.scratchBlocks[idx + 1];
        state.scratchBlocks[idx + 1] = temp;
        renderScratchStack();
      }
    });

    el.querySelector('.btn-block-delete').addEventListener('click', () => {
      state.scratchBlocks.splice(idx, 1);
      renderScratchStack();
    });

    container.appendChild(el);

    // Renderizar KaTeX previews iniciales
    def.fields.filter(f => f.type === 'latex').forEach(f => {
      const prevEl = document.getElementById(`prev-${block.id}-${f.key}`);
      renderLatexPreview(prevEl, block.values[f.key]);
    });
  });
}

function renderLatexPreview(element, texString) {
  if (!element) return;
  const cleanTex = (texString || '').trim();
  if (!cleanTex) {
    element.innerHTML = '<span class="preview-placeholder">Escribe una fórmula LaTeX</span>';
    return;
  }
  let formula = cleanTex;
  if (formula.startsWith('$$') && formula.endsWith('$$')) formula = formula.slice(2, -2).trim();
  else if (formula.startsWith('$') && formula.endsWith('$')) formula = formula.slice(1, -1).trim();

  if (window.katex) {
    try {
      katex.render(formula, element, { throwOnError: false, displayMode: true });
    } catch {
      element.textContent = formula;
    }
  } else {
    element.textContent = formula;
  }
}

function generatePythonFromScratch() {
  const codeLines = state.scratchBlocks.map(b => {
    const def = BLOCK_DEFS[b.type];
    return def ? def.toCode(b.values) : '';
  }).filter(Boolean);

  return `import math
from manim import DOWN, UP, LEFT, RIGHT
from Planos.generar_plano import AnimadorGrafico

# Definición Funcional
def f_objetivo(x: float) -> float:
    return 0.5 * x**2 + 1

if __name__ == "__main__":
    escena = AnimadorGrafico(f_objetivo, x_min=-1.0, x_max=4.0)
    
${codeLines.join('\n\n')}
    
    escena.render(previsualizar=True)
`;
}

async function handleScratchRender() {
  const pyCode = generatePythonFromScratch();
  const editor = document.getElementById('code-editor');
  editor.value = pyCode;
  updateLineNumbers();
  appendTerminalLine('info', 'Compilando secuencia de bloques visuales en Manim...');
  await handleRunMain(pyCode);
}

function handleScratchExportToMain() {
  const pyCode = generatePythonFromScratch();
  const editor = document.getElementById('code-editor');
  editor.value = pyCode;
  updateLineNumbers();
  saveMainPy();
  switchView('view-manual');
  appendTerminalLine('system', 'Bloques exportados a main.py con éxito.');
}

// ==========================================================================
// 11. VISUALIZADOR DE DOCUMENTACIÓN (READMI.MD)
// ==========================================================================
async function loadDocs() {
  const docsContainer = document.getElementById('docs-content');
  try {
    const res = await fetch('/api/get_readme');
    if (!res.ok) throw new Error('No se pudo acceder a READMI.md');
    const data = await res.json();
    
    if (window.marked) {
      docsContainer.innerHTML = marked.parse(data.content);
      // Procesar fórmulas matemáticas si hay KaTeX
      if (window.katex) {
        docsContainer.querySelectorAll('p, li').forEach(el => {
          if (el.textContent.includes('$')) {
            // Reemplazo básico de delimitadores matemáticos
            el.innerHTML = el.innerHTML.replace(/\$\$([^$]+)\$\$/g, (m, tex) => {
              try { return katex.renderToString(tex, { displayMode: true }); } catch { return m; }
            }).replace(/\$([^$]+)\$/g, (m, tex) => {
              try { return katex.renderToString(tex, { displayMode: false }); } catch { return m; }
            });
          }
        });
      }
    } else {
      docsContainer.innerHTML = `<pre><code>${escapeHtml(data.content)}</code></pre>`;
    }
    state.docsLoaded = true;
  } catch (err) {
    docsContainer.innerHTML = `<p class="term-error">Error al cargar documentación: ${err.message}</p>`;
  }
}

// ==========================================================================
// 12. CARGADOR DE PLANTILLAS
// ==========================================================================
function initTemplatesModal() {
  const btnOpen = document.getElementById('btn-load-template');
  const btnClose = document.getElementById('btn-close-templates-modal');
  const btnCancel = document.getElementById('btn-cancel-template');
  const modal = document.getElementById('modal-templates');

  const openModal = () => modal.classList.remove('hidden');
  const closeModal = () => modal.classList.add('hidden');

  if (btnOpen) btnOpen.addEventListener('click', openModal);
  if (btnClose) btnClose.addEventListener('click', closeModal);
  if (btnCancel) btnCancel.addEventListener('click', closeModal);

  document.querySelectorAll('.template-item').forEach(item => {
    item.addEventListener('click', async () => {
      const templateId = item.getAttribute('data-template-id');
      if (templateId === 'pasos_algebraicos') {
        state.activeFile = 'pasos_algebraicos.txt';
        await loadMainPy('pasos_algebraicos.txt');
        closeModal();
        switchView('view-manual');
        appendTerminalLine('system', 'Plantilla especial "Pasos algebráicos" activada. Editando pasos_algebraicos.txt.');
        return;
      }

      state.activeFile = 'main.py';
      updateActiveFileUI('main.py');
      const templateCode = TEMPLATES[templateId];
      if (templateCode) {
        const editor = document.getElementById('code-editor');
        editor.value = templateCode;
        updateLineNumbers();
        await saveMainPy();
        closeModal();
        switchView('view-manual');
        appendTerminalLine('system', `Plantilla "${templateId}" cargada en main.py.`);
      }
    });
  });
}

// ==========================================================================
// 12b. MÓDULO DE AUDIO SINCRONIZADO
// ==========================================================================
function formatSeconds(sec) {
  if (isNaN(sec) || sec < 0) sec = 0;
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

function parseTimeStr(str) {
  if (!str) return 0;
  str = str.trim();
  if (str.includes(':')) {
    const parts = str.split(':');
    const m = parseFloat(parts[0]) || 0;
    const s = parseFloat(parts[1]) || 0;
    return Math.max(0, m * 60 + s);
  }
  const val = parseFloat(str);
  return isNaN(val) ? 0 : Math.max(0, val);
}

function updateDownloadButtonUI() {
  const btnDownload = document.getElementById('btn-download-video');
  if (!btnDownload) return;
  const hasAudio = !!(state.audio.url && state.audio.name);
  const downloadText = hasAudio ? 'Descargar Video MP4 (Con Audio)' : 'Descargar Video MP4';

  if (!btnDownload.dataset.downloading) {
    btnDownload.innerHTML = `
      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      <span>${downloadText}</span>
    `;
    btnDownload.title = hasAudio
      ? `Descargar animación con el audio integrado desde ${formatSeconds(state.audio.startOffset)}`
      : 'Descargar archivo de video MP4';
  }
}

function initAudioModule() {
  const audioEl = document.getElementById('manim-audio-player');
  const videoEl = document.getElementById('manim-video-player');
  const fileInput = document.getElementById('audio-file-input');
  const dropzone = document.getElementById('audio-dropzone');
  const btnBrowse = document.getElementById('btn-browse-audio');
  const controlsPanel = document.getElementById('audio-controls-panel');
  const statusBadge = document.getElementById('audio-status-badge');
  const statusText = document.getElementById('audio-status-text');
  const equalizer = document.getElementById('audio-equalizer');
  const fileNameLabel = document.getElementById('audio-file-name');
  const fileDurationLabel = document.getElementById('audio-file-duration');
  const btnChange = document.getElementById('btn-change-audio');
  const btnRemove = document.getElementById('btn-remove-audio');
  const curTimeLabel = document.getElementById('audio-cur-time');
  const totalTimeLabel = document.getElementById('audio-total-time');
  const progressBar = document.getElementById('audio-progress-bar');
  const btnPlay = document.getElementById('btn-audio-play');
  const playLabel = document.getElementById('audio-play-label');
  const playIcon = document.getElementById('audio-play-icon');
  const btnStop = document.getElementById('btn-audio-stop');
  const btnMute = document.getElementById('btn-audio-mute');
  const volIcon = document.getElementById('audio-vol-icon');
  const volSlider = document.getElementById('audio-volume-slider');
  const volLabel = document.getElementById('audio-vol-label');
  const startInput = document.getElementById('audio-start-input');
  const startSecInput = document.getElementById('audio-start-seconds');
  const btnSetCurrentStart = document.getElementById('btn-set-current-as-start');
  const btnResetOffset = document.getElementById('btn-reset-offset');
  const checkAutoSync = document.getElementById('check-auto-sync');

  function updateOffset(newSec, notify = false) {
    const maxDur = state.audio.duration || 3600;
    newSec = Math.max(0, Math.min(newSec, maxDur));
    state.audio.startOffset = Math.round(newSec * 10) / 10;
    if (startSecInput) startSecInput.value = state.audio.startOffset.toFixed(1);
    if (startInput) startInput.value = formatSeconds(state.audio.startOffset);
    updateDownloadButtonUI();

    // Si el video está en 0 y pausado, posicionamos el audio en el offset
    if (videoEl && videoEl.currentTime < 0.1 && videoEl.paused && !state.audio.isPlaying) {
      audioEl.currentTime = state.audio.startOffset;
      if (curTimeLabel) curTimeLabel.textContent = formatSeconds(audioEl.currentTime);
      if (progressBar) progressBar.value = audioEl.currentTime;
    }

    if (notify) {
      appendTerminalLine('system', `Punto de inicio del audio configurado en: ${formatSeconds(state.audio.startOffset)} (${state.audio.startOffset.toFixed(1)}s)`);
    }
  }

  // Carga de archivo de audio
  function handleAudioFile(file) {
    if (!file) return;
    if (!file.type.startsWith('audio/') && !file.name.match(/\.(mp3|wav|ogg|aac|flac|m4a)$/i)) {
      appendTerminalLine('error', 'El archivo seleccionado no es un formato de audio compatible.');
      return;
    }

    const objectUrl = URL.createObjectURL(file);
    state.audio.file = file;
    state.audio.name = file.name;
    state.audio.url = objectUrl;

    audioEl.src = objectUrl;
    audioEl.load();

    if (fileNameLabel) fileNameLabel.textContent = file.name;
    if (dropzone) dropzone.style.display = 'none';
    if (controlsPanel) controlsPanel.classList.remove('hidden');

    if (statusBadge) statusBadge.className = 'audio-status-badge linked';
    if (statusText) statusText.textContent = 'Audio vinculado';

    appendTerminalLine('system', `Audio cargado: ${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`);
    updateDownloadButtonUI();

    // Subir en segundo plano al servidor para persistencia local en /audios/
    fetch('/api/upload_audio', {
      method: 'POST',
      headers: { 'X-Filename': file.name },
      body: file
    }).catch(() => {});
  }

  // Evento metadata de audio
  audioEl.addEventListener('loadedmetadata', () => {
    state.audio.duration = audioEl.duration;
    const durStr = formatSeconds(audioEl.duration);
    if (fileDurationLabel) fileDurationLabel.textContent = durStr;
    if (totalTimeLabel) totalTimeLabel.textContent = durStr;
    if (progressBar) progressBar.max = audioEl.duration;
    if (startSecInput) startSecInput.max = audioEl.duration;

    // Colocar en el segundo de inicio configurado
    audioEl.currentTime = state.audio.startOffset;
    if (curTimeLabel) curTimeLabel.textContent = formatSeconds(audioEl.currentTime);
    if (progressBar) progressBar.value = audioEl.currentTime;
    updateDownloadButtonUI();

    // Si el video ya está reproduciéndose, sincronizar de inmediato
    if (videoEl && !videoEl.paused && state.audio.autoSync) {
      const targetTime = videoEl.currentTime + state.audio.startOffset;
      if (targetTime < audioEl.duration) {
        audioEl.currentTime = targetTime;
        audioEl.play().catch(() => {});
      }
    }
  });

  // Selector de archivos y Drag & Drop
  if (btnBrowse) {
    btnBrowse.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });
  }

  if (dropzone) {
    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleAudioFile(e.dataTransfer.files[0]);
      }
    });
  }

  if (fileInput) {
    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files[0]) {
        handleAudioFile(fileInput.files[0]);
      }
    });
  }

  if (btnChange) {
    btnChange.addEventListener('click', () => fileInput.click());
  }

  if (btnRemove) {
    btnRemove.addEventListener('click', () => {
      audioEl.pause();
      audioEl.removeAttribute('src');
      audioEl.load();
      state.audio.file = null;
      state.audio.url = null;
      state.audio.name = '';
      state.audio.duration = 0;
      state.audio.isPlaying = false;

      if (controlsPanel) controlsPanel.classList.add('hidden');
      if (dropzone) dropzone.style.display = 'flex';
      if (statusBadge) statusBadge.className = 'audio-status-badge';
      if (statusText) statusText.textContent = 'Sin audio';
      if (equalizer) equalizer.classList.remove('playing');

      updateDownloadButtonUI();
      appendTerminalLine('system', 'Audio desvinculado de la animación.');
    });
  }

  // Controles independientes de reproducción
  function updatePlayButtonUI(isPlaying) {
    state.audio.isPlaying = isPlaying;
    if (isPlaying) {
      if (playLabel) playLabel.textContent = 'Pausa';
      if (playIcon) playIcon.innerHTML = '<rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect>';
      if (equalizer) equalizer.classList.add('playing');
      if (statusBadge) statusBadge.className = 'audio-status-badge playing';
      if (statusText) statusText.textContent = 'Reproduciendo';
    } else {
      if (playLabel) playLabel.textContent = 'Play';
      if (playIcon) playIcon.innerHTML = '<polygon points="5 3 19 12 5 21 5 3"></polygon>';
      if (equalizer) equalizer.classList.remove('playing');
      if (statusBadge) statusBadge.className = 'audio-status-badge linked';
      if (statusText) statusText.textContent = 'Audio vinculado';
    }
  }

  if (btnPlay) {
    btnPlay.addEventListener('click', () => {
      if (!state.audio.url) return;
      if (audioEl.paused) {
        audioEl.play().catch(() => {});
      } else {
        audioEl.pause();
      }
    });
  }

  if (btnStop) {
    btnStop.addEventListener('click', () => {
      if (!state.audio.url) return;
      audioEl.pause();
      audioEl.currentTime = state.audio.startOffset;
      if (progressBar) progressBar.value = state.audio.startOffset;
      if (curTimeLabel) curTimeLabel.textContent = formatSeconds(state.audio.startOffset);
    });
  }

  // Scrubbing de barra de progreso del audio
  if (progressBar) {
    progressBar.addEventListener('input', () => {
      if (!state.audio.url) return;
      const targetSec = parseFloat(progressBar.value);
      audioEl.currentTime = targetSec;
      if (curTimeLabel) curTimeLabel.textContent = formatSeconds(targetSec);
    });
  }

  audioEl.addEventListener('timeupdate', () => {
    if (!state.audio.url) return;
    if (curTimeLabel) curTimeLabel.textContent = formatSeconds(audioEl.currentTime);
    if (progressBar) progressBar.value = audioEl.currentTime;
  });

  audioEl.addEventListener('play', () => updatePlayButtonUI(true));
  audioEl.addEventListener('pause', () => updatePlayButtonUI(false));
  audioEl.addEventListener('ended', () => {
    updatePlayButtonUI(false);
    audioEl.currentTime = state.audio.startOffset;
    if (progressBar) progressBar.value = state.audio.startOffset;
    if (curTimeLabel) curTimeLabel.textContent = formatSeconds(state.audio.startOffset);
  });

  // Volumen y Silencio
  if (volSlider) {
    volSlider.addEventListener('input', () => {
      const vol = parseFloat(volSlider.value);
      audioEl.volume = vol;
      audioEl.muted = false;
      state.audio.volume = vol;
      state.audio.isMuted = false;
      if (volLabel) volLabel.textContent = `${Math.round(vol * 100)}%`;
      updateVolumeIcon(vol, false);
    });
  }

  if (btnMute) {
    btnMute.addEventListener('click', () => {
      audioEl.muted = !audioEl.muted;
      state.audio.isMuted = audioEl.muted;
      updateVolumeIcon(audioEl.volume, audioEl.muted);
      if (volLabel) volLabel.textContent = audioEl.muted ? '0%' : `${Math.round(audioEl.volume * 100)}%`;
    });
  }

  function updateVolumeIcon(vol, muted) {
    if (!volIcon) return;
    if (muted || vol === 0) {
      volIcon.innerHTML = '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line>';
    } else if (vol < 0.5) {
      volIcon.innerHTML = '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>';
    } else {
      volIcon.innerHTML = '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>';
    }
  }

  // Controles del Segundo de Inicio (Offset)
  if (startInput) {
    startInput.addEventListener('change', () => {
      const sec = parseTimeStr(startInput.value);
      updateOffset(sec, true);
    });
  }

  if (startSecInput) {
    startSecInput.addEventListener('input', () => {
      const sec = parseFloat(startSecInput.value) || 0;
      updateOffset(sec, false);
    });
    startSecInput.addEventListener('change', () => {
      const sec = parseFloat(startSecInput.value) || 0;
      updateOffset(sec, true);
    });
  }

  if (btnSetCurrentStart) {
    btnSetCurrentStart.addEventListener('click', () => {
      if (!state.audio.url) return;
      updateOffset(audioEl.currentTime, true);
    });
  }

  if (btnResetOffset) {
    btnResetOffset.addEventListener('click', () => {
      updateOffset(0, true);
    });
  }

  document.querySelectorAll('.btn-nudge[data-nudge]').forEach(btn => {
    btn.addEventListener('click', () => {
      const delta = parseFloat(btn.getAttribute('data-nudge')) || 0;
      updateOffset(state.audio.startOffset + delta, true);
    });
  });

  if (checkAutoSync) {
    checkAutoSync.addEventListener('change', () => {
      state.audio.autoSync = checkAutoSync.checked;
      appendTerminalLine('system', `Auto-sincronización de audio ${state.audio.autoSync ? 'ACTIVADA' : 'DESACTIVADA'}.`);
    });
  }

  // ========================================================================
  // SINCRONIZACIÓN ACOPLADA CON EL REPRODUCTOR DE VIDEO MANIM
  // ========================================================================
  if (videoEl) {
    // Al reproducir la animación
    videoEl.addEventListener('play', () => {
      if (!state.audio.url || !state.audio.autoSync) return;
      const targetTime = videoEl.currentTime + state.audio.startOffset;
      if (targetTime < (state.audio.duration || Infinity)) {
        audioEl.currentTime = targetTime;
        audioEl.play().catch(() => {});
      }
    });

    // Al pausar la animación
    videoEl.addEventListener('pause', () => {
      if (!state.audio.url || !state.audio.autoSync) return;
      audioEl.pause();
    });

    // Al desplazar la barra del video (seeking/seeked)
    const handleVideoSeek = () => {
      if (!state.audio.url || !state.audio.autoSync) return;
      const targetTime = videoEl.currentTime + state.audio.startOffset;
      if (targetTime >= 0 && targetTime <= (state.audio.duration || Infinity)) {
        audioEl.currentTime = targetTime;
      }
    };
    videoEl.addEventListener('seeking', handleVideoSeek);
    videoEl.addEventListener('seeked', handleVideoSeek);

    // Si cambia la velocidad de reproducción del video
    videoEl.addEventListener('ratechange', () => {
      if (state.audio.url) {
        audioEl.playbackRate = videoEl.playbackRate;
      }
    });

    // Al finalizar la animación
    videoEl.addEventListener('ended', () => {
      if (state.audio.url) {
        audioEl.pause();
        audioEl.currentTime = state.audio.startOffset;
      }
    });

    // Sincronización continua de deriva (Anti-drift)
    videoEl.addEventListener('timeupdate', () => {
      if (!state.audio.url || !state.audio.autoSync || videoEl.paused) return;
      const expectedTime = videoEl.currentTime + state.audio.startOffset;
      if (expectedTime < (state.audio.duration || Infinity)) {
        // Si hay una diferencia perceptible mayor a 180ms entre video y audio, corregir
        if (Math.abs(audioEl.currentTime - expectedTime) > 0.18) {
          audioEl.currentTime = expectedTime;
        }
        if (audioEl.paused) {
          audioEl.play().catch(() => {});
        }
      } else {
        if (!audioEl.paused) {
          audioEl.pause();
        }
      }
    });
  }
}

// ==========================================================================
// 13. EVENT LISTENERS GENERALES
// ==========================================================================
function initEventListeners() {
  // Botón Ejecutar del Header
  document.getElementById('btn-run').addEventListener('click', () => handleRunMain());

  // Botones de la Consola
  document.getElementById('btn-clear-console').addEventListener('click', clearTerminal);
  document.getElementById('btn-copy-console').addEventListener('click', copyTerminalLogs);

  // Descarga inteligente de video (con audio integrado si existe, o directo si no)
  const btnDownload = document.getElementById('btn-download-video');
  if (btnDownload) {
    btnDownload.addEventListener('click', async (e) => {
      // Si NO hay audio activo, se permite la descarga estándar del enlace <a>
      if (!state.audio.url || !state.audio.name) {
        return;
      }

      // Si HAY audio activo, se intercepta para multiplexar mediante FFmpeg
      e.preventDefault();
      if (btnDownload.classList.contains('disabled') || btnDownload.dataset.downloading === 'true') {
        return;
      }

      btnDownload.dataset.downloading = 'true';
      btnDownload.innerHTML = `
        <span class="spinner-sm" style="display:inline-block; width:12px; height:12px; border:2px solid rgba(255,255,255,0.3); border-top-color:#fff; border-radius:50%; animation:spin 1s infinite linear; margin-right:5px; vertical-align:middle;"></span>
        <span>Integrando audio...</span>
      `;

      appendTerminalLine('info', `Iniciando multiplexación: Seccionando audio desde ${formatSeconds(state.audio.startOffset)} para la duración exacta del video...`);

      try {
        // Garantizar que el archivo esté subido en el servidor
        if (state.audio.file) {
          await fetch('/api/upload_audio', {
            method: 'POST',
            headers: { 'X-Filename': state.audio.name },
            body: state.audio.file
          });
        }

        const res = await fetch('/api/merge_audio_video', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            audio_name: state.audio.name,
            start_offset: state.audio.startOffset,
            video_url: state.currentVideoUrl || ''
          })
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.error || 'Error al integrar audio y video');
        }

        const data = await res.json();
        appendTerminalLine('success', `Audio integrado exitosamente en ${data.filename} (${data.duration.toFixed(1)}s). Iniciando descarga.`);

        // Iniciar descarga del video con audio incrustado
        const tempLink = document.createElement('a');
        tempLink.href = data.download_url;
        tempLink.download = data.filename || 'EscenaAutomatica_con_audio.mp4';
        document.body.appendChild(tempLink);
        tempLink.click();
        document.body.removeChild(tempLink);
      } catch (err) {
        appendTerminalLine('error', `Error al integrar audio en el video: ${err.message}`);
      } finally {
        delete btnDownload.dataset.downloading;
        updateDownloadButtonUI();
      }
    });
  }

  // Reiniciar video y sincronizar audio
  document.getElementById('btn-restart-video').addEventListener('click', () => {
    const video = document.getElementById('manim-video-player');
    video.currentTime = 0;
    const audio = document.getElementById('manim-audio-player');
    if (audio && state.audio.url) {
      audio.currentTime = state.audio.startOffset;
      if (state.audio.autoSync) {
        audio.play().catch(() => {});
      }
    }
    video.play();
  });

  // Recargar documentación
  const btnReloadDocs = document.getElementById('btn-reload-docs');
  if (btnReloadDocs) btnReloadDocs.addEventListener('click', loadDocs);

  // Selector de temas (en drawer y en view-settings)
  document.querySelectorAll('.theme-card').forEach(card => {
    card.addEventListener('click', () => {
      const themeVal = card.getAttribute('data-theme-val');
      setTheme(themeVal);
    });
  });

  // Selector de calidad (en drawer y en view-settings)
  document.querySelectorAll('input[name="manim-quality"], input[name="manim-quality-full"]').forEach(radio => {
    radio.addEventListener('change', () => {
      setQuality(radio.value);
    });
  });

  // Atajo de teclado Escape
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeLeftMenu();
      const modal = document.getElementById('modal-templates');
      if (modal) modal.classList.add('hidden');
    }
  });
}
