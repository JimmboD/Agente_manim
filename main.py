"""
PLANTILLA: Método Simplex (Investigación de Operaciones)
Visualización analítica y geométrica del método Simplex para Programación Lineal en 2D.

Muestra:
  - Formulación matemática del problema en panel HUD flotante
  - Plano cartesiano acotado automáticamente
  - Rectas de frontera de las restricciones
  - Polígono geométrico exacto de la Región Factible (poliedro convexo)
  - Vértices básicos factibles y camino de pivoteo analítico
  - Evaluación paso a paso del valor de la función objetivo Z
  - Resaltado visual y banner final de la solución óptima (Z_max)
"""

import os
import sys
from manim import *
import numpy as np

# ==========================================
# CONFIGURACIÓN DE LA ANIMACIÓN (SIMPLEX)
# ==========================================
# Función objetivo a Maximizar: Max Z = c1*x1 + c2*x2
C_OBJETIVO = [2, 3]

# Matriz de restricciones: A * x <= b
A_RESTRICCIONES = [
    [2, 1],
    [1, 1]
]

# Límites / Términos independientes (b_i >= 0)
B_LIMITES = [80, 100]

# ==========================================
# VECTOR DE TIEMPOS ESTÁNDAR
# ==========================================
ESCALA_TIEMPO = 1.0

TIEMPOS_BASE = {
    "PANEL_ANIM": 1.5,
    "PANEL_ESPERA": 0.5,
    "PLANO_ANIM": 1.0,
    "RESTRICCIONES_ANIM": 0.8,
    "REGION_ANIM": 1.0,
    "PUNTO_INICIAL_ANIM": 0.8,
    "PUNTO_INICIAL_ESPERA": 0.8,
    "PASO_ANIM": 1.8,
    "PASO_ESPERA": 0.8,
    "OPTIMO_ANIM": 1.0,
    "OPTIMO_ESPERA": 2.5,
    "FINAL_ANIM": 1.5,
    "FINAL_ESPERA": 0.5
}

T = {clave: valor * ESCALA_TIEMPO for clave, valor in TIEMPOS_BASE.items()}
# ==========================================


class SimplexSolver:
    """Manejador estático de la lógica matemática del método Simplex y geometría 2D."""
    
    @staticmethod
    def obtener_tablas(c, A, b):
        """Construye las tablas del simplex paso a paso hasta alcanzar el óptimo."""
        num_vars = len(c)
        num_restricciones = len(b)
        tabla = np.zeros((num_restricciones + 1, num_vars + num_restricciones + 1), dtype=float)
        
        for i in range(num_restricciones):
            tabla[i, :num_vars] = A[i]
            tabla[i, num_vars + i] = 1.0
            tabla[i, -1] = b[i]
            
        tabla[-1, :num_vars] = -np.array(c, dtype=float)
        pasos = [tabla.copy()]
        
        max_iter = 100
        iter_count = 0
        while iter_count < max_iter:
            iter_count += 1
            # Criterio de optimalidad: ningún costo reducido negativo
            if np.all(tabla[-1, :-1] >= -1e-7):
                break
                
            col_pivote = np.argmin(tabla[-1, :-1])
            razones = []
            for i in range(num_restricciones):
                if tabla[i, col_pivote] > 1e-7:
                    razones.append(tabla[i, -1] / tabla[i, col_pivote])
                else:
                    razones.append(np.inf)
                    
            if all(r == np.inf for r in razones):
                raise ValueError("El problema de optimización no está acotado (solución infinita).")
                
            fila_pivote = np.argmin(razones)
            elemento_pivote = tabla[fila_pivote, col_pivote]
            tabla[fila_pivote, :] /= elemento_pivote
            
            for i in range(num_restricciones + 1):
                if i != fila_pivote:
                    tabla[i, :] -= tabla[i, col_pivote] * tabla[fila_pivote, :]
                    
            pasos.append(tabla.copy())
            
        return pasos

    @staticmethod
    def extraer_puntos(tablas, num_vars):
        """Extrae las coordenadas del punto de decisión en cada tabla del simplex."""
        puntos = []
        for tabla in tablas:
            punto = np.zeros(num_vars, dtype=float)
            for j in range(num_vars):
                columna = tabla[:-1, j]
                if np.sum(np.isclose(columna, 1.0, atol=1e-5)) == 1 and np.sum(np.isclose(columna, 0.0, atol=1e-5)) == (len(columna) - 1):
                    fila_basica = np.argmax(columna)
                    punto[j] = tabla[fila_basica, -1]
            puntos.append(punto)
        return puntos

    @staticmethod
    def obtener_vertices_region(A, b):
        """Calcula analíticamente los vértices del poliedro convexo en el primer cuadrante."""
        lineas = [(-1.0, 0.0, 0.0), (0.0, -1.0, 0.0)]  # x1 >= 0, x2 >= 0
        for fila, val in zip(A, b):
            lineas.append((float(fila[0]), float(fila[1]), float(val)))
            
        puntos = []
        n = len(lineas)
        for i in range(n):
            for j in range(i + 1, n):
                a1, a2, b1 = lineas[i]
                c1, c2, b2 = lineas[j]
                det = a1 * c2 - a2 * c1
                if abs(det) < 1e-9:
                    continue
                x = (b1 * c2 - b2 * a2) / det
                y = (a1 * b2 - c1 * b1) / det
                
                if x < -1e-6 or y < -1e-6:
                    continue
                x, y = max(0.0, x), max(0.0, y)
                
                # Comprobar que cumpla todas las restricciones
                factible = True
                for fila, val in zip(A, b):
                    if fila[0] * x + fila[1] * y > val + 1e-4:
                        factible = False
                        break
                        
                if factible:
                    if not any(np.isclose(x, px, atol=1e-4) and np.isclose(y, py, atol=1e-4) for px, py in puntos):
                        puntos.append((round(x, 6), round(y, 6)))
                        
        if not puntos:
            return []
            
        # Ordenar en sentido antihorario respecto al centroide para generar un Polygon cerrado sin cruces
        cx = sum(p[0] for p in puntos) / len(puntos)
        cy = sum(p[1] for p in puntos) / len(puntos)
        puntos.sort(key=lambda p: np.arctan2(p[1] - cy, p[0] - cx))
        return puntos

    @staticmethod
    def calcular_segmento_restriccion(a1, a2, b_val, max_val):
        """Calcula el segmento de recta dentro del rango visible [0, max_val] x [0, max_val]."""
        candidatos = []
        if abs(a2) > 1e-9:
            y = b_val / a2
            if 0 <= y <= max_val + 1e-5:
                candidatos.append((0.0, min(float(max_val), max(0.0, y))))
            y = (b_val - a1 * max_val) / a2
            if 0 <= y <= max_val + 1e-5:
                candidatos.append((float(max_val), min(float(max_val), max(0.0, y))))
                
        if abs(a1) > 1e-9:
            x = b_val / a1
            if 0 <= x <= max_val + 1e-5:
                candidatos.append((min(float(max_val), max(0.0, x)), 0.0))
            x = (b_val - a2 * max_val) / a1
            if 0 <= x <= max_val + 1e-5:
                candidatos.append((min(float(max_val), max(0.0, x)), float(max_val)))
                
        unicos = []
        for p in candidatos:
            if not any(np.isclose(p[0], u[0], atol=1e-4) and np.isclose(p[1], u[1], atol=1e-4) for u in unicos):
                unicos.append(p)
                
        if len(unicos) >= 2:
            return unicos[0], unicos[1]
        return None


class SimplexScene(Scene):
    """Escena de Manim que visualiza y anima el problema de programación lineal y el simplex."""
    
    def __init__(self, c=None, A=None, b=None, tiempos=None, **kwargs):
        super().__init__(**kwargs)
        self.c = c if c is not None else C_OBJETIVO
        self.A = A if A is not None else A_RESTRICCIONES
        self.b = b if b is not None else B_LIMITES
        self.tiempos = tiempos if tiempos is not None else T

        if len(self.c) != 2:
            raise ValueError(
                f"La visualización gráfica 2D requiere 2 variables de decisión en 'c'. Recibido: {len(self.c)}"
            )

    def construct(self):
        T_scene = self.tiempos

        # 1. Obtener la solución matemática analítica
        tablas = SimplexSolver.obtener_tablas(self.c, self.A, self.b)
        puntos_simplex = SimplexSolver.extraer_puntos(tablas, len(self.c))

        # 2. Calcular los límites del plano cartesiano 1:1
        intersecciones_x = [self.b[i] / self.A[i][0] for i in range(len(self.b)) if self.A[i][0] > 0]
        intersecciones_y = [self.b[i] / self.A[i][1] for i in range(len(self.b)) if self.A[i][1] > 0]
        todas = intersecciones_x + intersecciones_y
        max_absoluto = max(todas) if todas else 10.0
        max_val = float(int(np.ceil(max_absoluto * 1.15)))
        paso_eje = max(1.0, float(max(1, int(max_val // 5))))

        # 3. Panel HUD con la formulación matemática (Esquina Superior Derecha)
        lineas_texto = [
            MathTex(r"\mathbf{M\acute{e}todo\ Simplex}", font_size=23, color=YELLOW),
            MathTex(f"\\text{{Max }}(Z) = {self.c[0]:g}x_1 + {self.c[1]:g}x_2", font_size=21, color=YELLOW_B),
            MathTex(r"\text{Sujeto a:}", font_size=19, color=GREY_B)
        ]
        
        for i in range(len(self.b)):
            lineas_texto.append(
                MathTex(f"{self.A[i][0]:g}x_1 + {self.A[i][1]:g}x_2 \\leq {self.b[i]:g}", font_size=18, color=WHITE)
            )
        lineas_texto.append(
            MathTex(r"x_1, x_2 \geq 0", font_size=18, color=GREY_A)
        )

        panel_contenido = VGroup(*lineas_texto).arrange(DOWN, aligned_edge=LEFT, buff=0.13)
        if panel_contenido.height > 6.2:
            panel_contenido.scale_to_fit_height(6.2)

        fondo_panel = RoundedRectangle(
            corner_radius=0.15,
            width=panel_contenido.width + 0.35,
            height=panel_contenido.height + 0.35,
            fill_color="#181825",
            fill_opacity=0.85,
            stroke_color="#45475a",
            stroke_width=1.5
        ).move_to(panel_contenido.get_center())

        panel_problema = VGroup(fondo_panel, panel_contenido).to_corner(UR, buff=0.35)

        self.play(FadeIn(panel_problema, shift=LEFT * 0.3), run_time=T_scene["PANEL_ANIM"])
        self.wait(T_scene["PANEL_ESPERA"])

        # 4. Plano Cartesiano 1:1
        axes = Axes(
            x_range=[0, max_val, paso_eje],
            y_range=[0, max_val, paso_eje],
            x_length=6.8,
            y_length=6.8,
            axis_config={"include_numbers": True, "font_size": 20, "color": GREY_A},
        )
        axes.to_corner(DL, buff=0.45)

        lbl_x = axes.get_x_axis_label(MathTex("x_1", font_size=22), edge=RIGHT, direction=DOWN, buff=0.15)
        lbl_y = axes.get_y_axis_label(MathTex("x_2", font_size=22), edge=UP, direction=LEFT, buff=0.15)

        self.play(Create(axes), FadeIn(lbl_x), FadeIn(lbl_y), run_time=T_scene["PLANO_ANIM"])

        # 5. Trazado de restricciones y Región Factible exacta
        lineas_restricciones = VGroup()
        for i in range(len(self.b)):
            seg = SimplexSolver.calcular_segmento_restriccion(self.A[i][0], self.A[i][1], self.b[i], max_val)
            if seg:
                p1, p2 = seg
                linea = Line(
                    axes.c2p(p1[0], p1[1]),
                    axes.c2p(p2[0], p2[1]),
                    color=YELLOW_C,
                    stroke_width=2.0,
                    stroke_opacity=0.85
                )
                lineas_restricciones.add(linea)

        self.play(Create(lineas_restricciones), run_time=T_scene["RESTRICCIONES_ANIM"])

        vertices_region = SimplexSolver.obtener_vertices_region(self.A, self.b)
        if len(vertices_region) >= 3:
            puntos_poligono = [axes.c2p(vx, vy) for vx, vy in vertices_region]
            region_factible = Polygon(
                *puntos_poligono,
                fill_color="#89b4fa",
                fill_opacity=0.35,
                stroke_color="#b4befe",
                stroke_width=1.5
            )
            self.play(FadeIn(region_factible), run_time=T_scene["REGION_ANIM"])

        # 6. Punto Inicial en el origen P0 = (0, 0)
        p_ini = puntos_simplex[0]
        z_ini = self.c[0] * p_ini[0] + self.c[1] * p_ini[1]
        dot = Dot(point=axes.c2p(p_ini[0], p_ini[1]), color=WHITE, radius=0.08).set_z_index(10)
        
        tracker_coords = MathTex(
            f"P_0({p_ini[0]:.1f}, {p_ini[1]:.1f}) \\\\ Z = {z_ini:.1f}",
            font_size=20,
            color=YELLOW
        ).set_z_index(11)
        tracker_coords.next_to(dot, UR, buff=0.12)

        self.play(FadeIn(dot, scale=1.3), FadeIn(tracker_coords), run_time=T_scene["PUNTO_INICIAL_ANIM"])
        self.wait(T_scene["PUNTO_INICIAL_ESPERA"])

        # 7. Iteraciones del Simplex: recorrido de vértices básicos
        for idx, p in enumerate(puntos_simplex[1:], start=1):
            p_prev = puntos_simplex[idx - 1]
            z_act = self.c[0] * p[0] + self.c[1] * p[1]
            es_ultimo = (idx == len(puntos_simplex) - 1)

            # Tramo de trayectoria punteada
            tramo = DashedLine(
                axes.c2p(p_prev[0], p_prev[1]),
                axes.c2p(p[0], p[1]),
                color="#f38ba8",
                stroke_width=3.0,
                dash_length=0.08
            ).set_z_index(7)

            # Marcador fantasma en el vértice anterior
            fantasma = Dot(axes.c2p(p_prev[0], p_prev[1]), color=GREY_B, radius=0.05).set_z_index(8)

            nueva_etiqueta = MathTex(
                f"P_{{{idx}}}({p[0]:.1f}, {p[1]:.1f}) \\\\ Z = {z_act:.1f}",
                font_size=20,
                color=GREEN_A if es_ultimo else YELLOW
            ).set_z_index(11)
            nueva_etiqueta.next_to(axes.c2p(p[0], p[1]), UR, buff=0.12)

            self.play(
                Create(tramo),
                FadeIn(fantasma),
                dot.animate.move_to(axes.c2p(p[0], p[1])),
                Transform(tracker_coords, nueva_etiqueta),
                run_time=T_scene["PASO_ANIM"],
                rate_func=smooth
            )
            self.wait(T_scene["PASO_ESPERA"])

        # 8. Celebración de solución óptima
        p_opt = puntos_simplex[-1]
        z_max = self.c[0] * p_opt[0] + self.c[1] * p_opt[1]

        anillo_optimo = Circle(radius=0.22, color=GREEN_B, stroke_width=2.5).move_to(dot.get_center()).set_z_index(12)

        banner_texto = MathTex(
            r"\textbf{Solución Óptima: }",
            f"x^* = ({p_opt[0]:.2f}, {p_opt[1]:.2f})",
            r"\quad \implies \quad",
            f"Z_{{\\max}} = {z_max:.2f}",
            font_size=24,
            color=GREEN_B
        )
        banner_fondo = RoundedRectangle(
            corner_radius=0.1,
            width=banner_texto.width + 0.5,
            height=banner_texto.height + 0.3,
            fill_color="#11111b",
            fill_opacity=0.9,
            stroke_color=GREEN_C,
            stroke_width=1.5
        ).move_to(banner_texto.get_center())
        banner_grupo = VGroup(banner_fondo, banner_texto).to_edge(UP, buff=0.45).set_z_index(20)

        self.play(
            dot.animate.set_color(GREEN_A),
            Create(anillo_optimo),
            FadeIn(banner_grupo, shift=DOWN * 0.3),
            run_time=T_scene["OPTIMO_ANIM"]
        )
        self.wait(T_scene["OPTIMO_ESPERA"])

        # 9. Cierre limpio
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=T_scene["FINAL_ANIM"])
        self.wait(T_scene["FINAL_ESPERA"])


class SimplexAnimation(SimplexScene):
    """Clase envoltorio para ejecutar directamente la escena con los parámetros por defecto."""
    def __init__(self, **kwargs):
        super().__init__(c=C_OBJETIVO, A=A_RESTRICCIONES, b=B_LIMITES, tiempos=T, **kwargs)


def animar_simplex(c=None, A=None, b=None, tiempos=None, previsualizar=True, calidad=None):
    """
    Función de alto nivel para configurar y renderizar la animación del Método Simplex.
    Permite ser llamada directamente desde main.py con parámetros personalizados.
    
    Parámetros:
      - c: lista con los 2 coeficientes de la función objetivo [c1, c2].
      - A: matriz (lista de listas) con los coeficientes de las restricciones.
      - b: lista con los valores del lado derecho (términos independientes).
      - tiempos: diccionario opcional con tiempos de animación escalados.
      - previsualizar: booleano para abrir ventana de previsualización nativa.
      - calidad: 'low_quality', 'medium_quality', 'high_quality', o None.
    """
    c_vals = c if c is not None else C_OBJETIVO
    a_vals = A if A is not None else A_RESTRICCIONES
    b_vals = b if b is not None else B_LIMITES
    t_vals = tiempos if tiempos is not None else T

    if os.environ.get("MANIM_STUDIO_HEADLESS") == "1":
        previsualizar = False

    cal = calidad or os.environ.get("MANIM_QUALITY", "low_quality")

    with tempconfig({"quality": cal, "preview": previsualizar}):
        escena = SimplexScene(c=c_vals, A=a_vals, b=b_vals, tiempos=t_vals)
        escena.render()
        return escena


if __name__ == "__main__":
    animar_simplex()