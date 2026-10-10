
---

# 📄 Technical Reference: Entorno Animador Matemático (Manim Engine)

## 1. System Architecture Overview

El sistema implementa un patrón de diseño **Builder / Action Queue** construido sobre el motor gráfico de Manim. Se divide en dos módulos principales integrados: un motor de renderizado geométrico (`AnimadorGrafico`) y un pipeline de procesamiento de transformaciones simbólicas (`motor_algebra`).

**Directiva de Ejecución (Agent Note):** Ningún objeto gráfico de Manim (`Dot`, `Line`, `MathTex`) debe ser instanciado directamente en el hilo de ejecución principal. Todas las instrucciones deben añadirse a la cola de acciones `self.cola_animaciones` mediante los métodos del controlador para su posterior renderizado asíncrono dentro del método `construct()`.

**Global Pacing Control:** Todas las primitivas de animación integran dos parámetros de latencia estandarizados:

* `tiempo_animacion (float)`: Duración de la transición geométrica o transformación visual.
* `tiempo_espera (float)`: Tiempo de suspensión del hilo (freeze-frame) post-animación, crucial para sincronización de voz o asimilación del concepto.

---

## 2. Component API Reference: Módulo `AnimadorGrafico`

**Path:** `planos/generar_plano.py`

Clase orquestadora para la configuración de la escena geométrica en $\mathbb{R}^2$. Configura automáticamente la clase `MovingCameraScene` y previene desbordamientos de memoria (`memory overflow`) mediante algoritmos de clipping transversal y overscan.

### 2.1. Métodos de Estructura Topológica (Static Geometry)

* **`agregar_punto(x: float, y: float, color: str = WHITE, label: bool = False, tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0) -> self`**
Añade un nodo estático a la topología. Si `label=True`, anexa un tensor textual `MathTex` con sus coordenadas relativas al campo visual.
* **`agregar_funcion(funcion: Callable, x_min: float | None = None, x_max: float | None = None, color: str = GREEN, tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0) -> self`**
Añade una función auxiliar mapeada en el plano. Limita el subdominio dinámicamente si los umbrales no son declarados explícitamente.

### 2.2. Métodos de Cinemática y Acotación Espacial (Dynamic Geometry)

* **`animar_punto_sobre_curva(x_inicio: float, x_fin: float, funcion: Callable | None = None, color: str = YELLOW, tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0) -> self`**
Ejecuta una interpolación posicional acoplada a la trayectoria de $f(x)$ mediante el uso de `ValueTracker`.
* **`animar_secante(x1_ini: float, x1_fin: float, x2_ini: float, x2_fin: float, funcion: Callable | None = None, color: str = YELLOW, tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0) -> self`**
Genera un segmento lineal dinámico. Si $\vert{}x_2 - x_1\vert{} < 10^{-4}$, computa automáticamente la derivada numérica simétrica para transicionar a una tangente.
* **`animar_linea_punteada(x1_ini: float, x1_fin: float, x2_ini: float, x2_fin: float, y1_ini: float | Callable, y2_ini: float | Callable, y1_fin: float | None = None, y2_fin: float | None = None, color: str = WHITE, tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0) -> self`**
Proyecta un vector discontinuo (`DashedLine`) entre dos coordenadas.
*Polimorfismo:* Los parámetros `y1_ini` y `y2_ini` admiten funciones matemáticas (`Callable`). Si se provee una función, la coordenada transversal se acopla dinámicamente a la curva en tiempo de renderizado.
* **`animar_llave(x1_ini: float, x1_fin: float, x2_ini: float, x2_fin: float, y1_ini: float | Callable, y2_ini: float | Callable, y1_fin: float | None = None, y2_fin: float | None = None, texto: str = "", direccion: Vector | None = None, color: str = WHITE, tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0) -> self`**
Instancia una llave isométrica (`BraceBetweenPoints`) acoplada a dos nodos iterativos por `ValueTracker`. Soporta inyección de texto LaTeX mediante `texto` y control de vector normal mediante `direccion` (ej. `UP`, `DOWN`).

### 2.3. Métodos de Transición de Estado Visual (Geometry $\leftrightarrow$ Algebra)

* **`transformar_a_texto(texto_latex: str, tiempo_animacion: float = 1.5, tiempo_espera: float = 1.0) -> self`**
Compresión topológica mediante `ReplacementTransform` global hacia un tensor lógico escalar (`MathTex`).
* **`transformar_a_plano(tiempo_animacion: float = 1.5, tiempo_espera: float = 1.0) -> self`**
Descompresión del estado escalar y retorno a geometría $\mathbb{R}^2$.
* **`insertar_algebra(fuente_o_texto: str, tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0) -> self`**
Suspende la topología gráfica activa e invoca el pipeline simbólico. Acepta `.txt` o raw strings.
* **`agregar_algebra_flotante(fuente_o_texto: str, posicion: str = "UL", remover_al_final: bool = False, tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0) -> self`**
Inyecta un HUD vectorial superpuesto (`aligned_edge` routing).

---

## 3. Arquitectura del Motor Computacional

**Paths:** `algebra/motor_algebra.py` & `planos/generar_plano.py`

### 3.1. Historial de Control de Versiones (Changelog)

* **v1.0 - Parser Base:** Filtro regex para asilar bloques `$$...$$`.
* **v2.0 - AST Styling & Dynamic Scaling:** Escalabilidad dependiente del `FOV` y mapeo de sub-nodos LaTeX a tensores de color.
* **v3.0 - Transformación Heurística:** Implementación de `criterio_animacion.py` para análisis de grafos lógicos ($T_{n-1} \leftrightarrow T_n$).
* **v4.0 - Global Pacing Integration:** Inyección de `runtime` y `waittime` en los workers atómicos de la escena.
* **v5.0 - HUD Vectorial (Overlay Analytics):** Implementación de álgebra persistente en esquinas absolutas del viewport.
* **v6.0 - Optimizaciones Topológicas:** Bounding boxes calculados vía `scipy.optimize`, y limitadores perimetrales (Overscan + FOV Padding) para prevención algorítmica de clipping geométrico.
* **v7.0 - Interpolación Espacial Paramétrica:** Inyección de un `ValueTracker` maestro paramétrico ($\alpha \in [0,1]$) capaz de manejar polimorfismo de coordenadas. Transforma las primitivas de acotación (líneas punteadas y llaves) en entidades "curve-aware" (que detectan e interpolan su posición vertical dinámicamente rastreando la función principal).

---

## 4. Execution Pipeline Protocol (Plantilla para Agentes)

**Directiva para escritura de scripts principales (`main.py`):**
La instanciación y ejecución debe seguir estrictamente un flujo declarativo.

```python
import math
from manim import DOWN
from planos.generar_plano import AnimadorGrafico

# 1. Definición Funcional
def f_objetivo(x: float) -> float:
    return math.e**x - 3*x**2

if __name__ == "__main__":
    
    # 2. Instanciación Topológica
    escena = AnimadorGrafico(f_objetivo, x_min=-2.0, x_max=2.5)
    
    # 3. Proyección Analítica Curve-Aware (El extremo superior sigue la función matemática)
    escena.animar_linea_punteada(
        x1_ini=0, x1_fin=1.5,
        x2_ini=0, x2_fin=1.5,
        y1_ini=f_objetivo, # Polimorfismo Funcional
        y2_ini=0,
        color="#00FFFF", 
        tiempo_animacion=2.0, tiempo_espera=0.5
    )
    
    # 4. Acotación Topológica (Llave $\Delta x$)
    escena.animar_llave(
        x1_ini=0, x1_fin=0,
        x2_ini=1.5, x2_fin=1.5,
        y1_ini=0, y2_ini=0,
        texto=r"\Delta x",
        direccion=DOWN,
        color="#FF00FF",
        tiempo_animacion=1.0, tiempo_espera=1.0
    )
    
    # 5. Inyección de Overlay Analítico (HUD)
    hud_logica = r"""
    $$m = \frac{f(1.5) - f(0)}{1.5 - 0}$$
    $$\textcolor{yellow}{m \approx -1.45}$$
    """
    escena.agregar_algebra_flotante(
        fuente_o_texto=hud_logica, 
        posicion="UR", # Anclaje Superior-Derecho
        remover_al_final=False,
        tiempo_animacion=1.0, tiempo_espera=1.5
    )
    
    # 6. Trigger final del renderizador asíncrono
    escena.render(previsualizar=True)

```