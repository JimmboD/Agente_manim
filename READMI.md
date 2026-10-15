
---

# § Technical Reference: Entorno Animador Matemático (Manim Engine)

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
* **`animar_integral(funcion: Callable, x_min: float, x_max: float, dx: float | None = None, color: str = "#00FFFF", opacidad: float = 0.5, id_area: str | None = None, tiempo_animacion: float = 1.0, tiempo_espera: float = 0.5) -> self`**
Subsistema de cálculo integral y aproximación por Sumas de Riemann. Si `dx` está definido, renderiza rectángulos de partición de Riemann (`get_riemann_rectangles`) con grosor de contorno unitario y opacidad controlada. Si `dx=None`, renderiza el área continua bajo la curva (`get_area`). Se ubica automáticamente con $z\text{-index}=1$ por debajo de las curvas principales.

### 2.2. Métodos de Cinemática y Acotación Espacial (Dynamic Geometry)

* **`animar_punto_sobre_curva(x_inicio: float, x_fin: float, funcion: Callable | None = None, color: str = YELLOW, tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0, id: str | None = None) -> self`**
Ejecuta una interpolación posicional acoplada a la trayectoria de $f(x)$ mediante un carril invisible parametrizado con `ParametricFunction` y la animación nativa `MoveAlongPath`. Elimina por completo `ValueTracker` y dependencias de updaters frame-a-frame, garantizando sincronización exacta en milisegundos cuando se despacha dentro de bloques de concurrencia paralela (`bloque_paralelo`). Si se provee `id` y el punto ya existe en la memoria de la escena (`self.objetos`), se reutiliza el mobject existente sin `FadeIn` duplicado.
* **`animar_convergencia_parametrica(funcion: Callable, x_fijo: float, x_movil_ini: float, x_movil_fin: float, id_secante: str, id_punto_curva: str, id_punto_raiz: str, tiempo_animacion: float = 2.0, tiempo_espera: float = 1.0) -> self`**
**Paradigma Paramétrico Maestro.** Sincronización absoluta de convergencia numérica. Vincula la recta secante (`id_secante`), el extremo móvil de la curva (`id_punto_curva`) y el punto raíz sobre el eje X (`id_punto_raiz`) a un único parámetro maestro $\alpha \in [0, 1]$ (`ValueTracker`). En cada fotograma, el motor evalúa simultáneamente la posición exacta del punto sobre $f(x)$, computa la pendiente analítica de la secante que pasa por el punto fijo $(x_{fijo}, f(x_{fijo}))$, extiende la recta infinita a los límites del plano y calcula en tiempo real el corte exacto con el eje $Y=0$. Al estar gobernadas por la misma variable escalar, es físicamente imposible que ocurra desincronización por curvas de aceleración (easing) dispares.
* **`animar_secante(x1_ini: float, x1_fin: float, x2_ini: float, x2_fin: float, funcion: Callable | None = None, color: str = YELLOW, tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0) -> self`**
Genera un segmento lineal dinámico. Si $\vert{}x_2 - x_1\vert{} < 10^{-4}$, computa automáticamente la derivada numérica simétrica para transicionar a una tangente.
* **`animar_linea_punteada(x1_ini: float, x1_fin: float, x2_ini: float, x2_fin: float, y1_ini: float | Callable, y2_ini: float | Callable, y1_fin: float | None = None, y2_fin: float | None = None, color: str = WHITE, tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0) -> self`**
Proyecta un vector discontinuo (`DashedLine`) entre dos coordenadas.
*Polimorfismo:* Los parámetros `y1_ini` y `y2_ini` admiten funciones matemáticas (`Callable`). Si se provee una función, la coordenada transversal se acopla dinámicamente a la curva en tiempo de renderizado.
* **`animar_llave(x1_ini: float, x1_fin: float, x2_ini: float, x2_fin: float, y1_ini: float | Callable, y2_ini: float | Callable, y1_fin: float | None = None, y2_fin: float | None = None, texto: str = "", direccion: Vector | None = None, color: str = WHITE, tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0) -> self`**
Instancia una llave isométrica (`BraceBetweenPoints`) acoplada a dos nodos iterativos por `ValueTracker`. Soporta inyección de texto LaTeX mediante `texto` y control de vector normal mediante `direccion` (ej. `UP`, `DOWN`).

### 2.3. Métodos de Transición de Estado Visual (Geometry $\leftrightarrow$ Algebra)

* **`transformar_objeto(origen: str | None = None, tipo_destino: str | None = None, funcion: Callable | None = None, x: float | None = None, y: float | None = None, texto: str | None = None, x_min: float | None = None, x_max: float | None = None, color: str | None = None, label: bool = False, posicion: str | tuple = "center", id_destino: str | None = None, animacion: str = "ReplacementTransform", tiempo_animacion: float = 1.5, tiempo_espera: float = 1.0) -> self`**
  **ReplacementTransform Universal Multidireccional.** Permite transicionar morfológicamente cualquier entidad de la escena (función, punto o label) hacia cualquier otra entidad (función, punto o label).
  * *Entidad de origen (`origen`):* Identificador (`id`) del mobject previamente registrado (`"mi_curva"`, `"mi_punto"`, `"hud_limite"`), o `None` para aplicar sobre el último objeto creado en la escena. También acepta los alias de sistema `"principal"`, `"grafica"`, `"plano"` y `"texto_central"`.
  * *Entidad de destino (`tipo_destino`):*
    * `"funcion"`: Genera una curva matemática continua trazada por $f(x)$ sobre el plano cartesiano (`funcion=callable`, `x_min`, `x_max`, `color`).
    * `"integral"`: Genera rectángulos de Riemann (`dx` especificado) o área continua (`dx=None`) acoplados a la curva (`funcion=callable`, `x_min`, `x_max`, `dx`, `opacidad`, `color`).
    * `"punto"`: Colapsa o transmuta la entidad en un punto coordinado $\mathbb{R}^2$ (`x`, `y`, `color`, `label=True/False`).
    * `"label"` / `"texto"`: Transforma la entidad en un tensor tipográfico o ecuación LaTeX (`texto=r"..."`, `posicion="center" | "UL" | "UR" | "DL" | "DR" | (x, y)`).
  * *Deducción automática:* Si `tipo_destino` es omitido, el motor infiere automáticamente el tipo destino según los parámetros provistos (`funcion` $\to$ función, `texto` $\to$ label, `x`/`y` $\to$ punto).
  * *Aliases:* `replacement_transform`, `transformar`, `transformacion_universal`.

* **`transformar_a_texto(texto_latex: str, tiempo_animacion: float = 1.5, tiempo_espera: float = 1.0) -> self`**
Compresión topológica mediante `ReplacementTransform` global hacia un tensor lógico escalar (`MathTex`).
* **`transformar_a_plano(tiempo_animacion: float = 1.5, tiempo_espera: float = 1.0) -> self`**
Descompresión del estado escalar y retorno a geometría $\mathbb{R}^2$.
* **`insertar_algebra(fuente_o_texto: str, tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0) -> self`**
Suspende la topología gráfica activa e invoca el pipeline simbólico. Acepta `.txt` o raw strings.
* **`agregar_algebra_flotante(fuente_o_texto: str, posicion: str = "UL", remover_al_final: bool = False, tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0, id: str | None = None) -> self`**
Inyecta un HUD vectorial superpuesto (`aligned_edge` routing).

### 2.4. Métodos de Purga y Ciclo de Vida (Lifecycle & Deletion)

* **`eliminar_objeto(id: str | None = None, animacion: str = "FadeOut", tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0) -> self`**
Elimina un objeto del plano por su identificador asignado (`id`) o el último elemento generado si `id=None`. Si `id="todos"`, elimina todos los objetos visibles de la escena.
*Tipos de animación admitidos:* `"FadeOut"`, `"Uncreate"` (des-traza curvas/líneas de forma inversa), `"Shrink"` / `"ShrinkToCenter"`.
* **`remover_objeto(id: str | None = None, animacion: str = "FadeOut", tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0) -> self`**
Alias sintáctico de `eliminar_objeto`.
* **`desvanecer_todo(animacion: str = "FadeOut", tiempo_animacion: float = 1.5, tiempo_espera: float = 1.0) -> self`**
Provoca la finalización suave de la escena disolviendo todos los mobjects a negro (*muerte* de la animación).

### 2.5. Métodos de Ejecución Paralela y Concurrencia (Simultaneous Animations)

Permite orquestar múltiples animaciones, mutaciones morfológicas y purgas en un único fotograma temporal simultáneo (`self.play(*anims, run_time=t_anim)`), eliminando esperas y desfaces secuenciales.

* **`iniciar_bloque_paralelo() -> self`**
  Abre un contexto recolector de ejecución concurrente. Las instrucciones añadidas subsecuentemente a la cola (`transformar_objeto`, `agregar_punto`, `agregar_funcion`, `eliminar_objeto`, etc.) no se reproducen de manera aislada, sino que sus instancias `Animation` de Manim se acumulan en un buffer sincrónico.
  * *Alias:* `iniciar_paralelo()`.

* **`cerrar_bloque_paralelo(tiempo_animacion: float = 1.5, tiempo_espera: float = 1.0) -> self`**
  Cierra el contexto recolector y dispara todas las animaciones acumuladas al unísono en `self.play(*anims_paralelas, run_time=tiempo_animacion)`. Tras concluir la interpolación, ejecuta los finalizadores topológicos (actualización de identificadores `id` y registros de objetos) y aplica un tiempo de reposo (`tiempo_espera`).
  * *Alias:* `cerrar_paralelo()`.

* **`bloque_paralelo(tiempo_animacion: float = 1.5, tiempo_espera: float = 1.0) -> ContextManager`**
  Context manager Pythonic para agrupar bloques concurrentes de forma concisa:
  ```python
  with escena.bloque_paralelo(tiempo_animacion=2.0, tiempo_espera=1.0):
      escena.transformar_objeto(origen="secante", tipo_destino="funcion", funcion=f_nueva, id_destino="secante")
      escena.transformar_objeto(origen="nodo_B", tipo_destino="punto", x=c, y=fc, id_destino="nodo_B")
  ```

* **Directiva de Identificadores en Paralelo:**
  Cuando se ejecutan múltiples `transformar_objeto()` o `eliminar_objeto()` en paralelo, se deben declarar identificadores explícitos (`id="nombre"`) en el origen para garantizar que cada animación capture su tensor correspondiente sin colisiones de cursor.

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
* **v8.0 - Ciclo de Vida y Purga de Entidades:** Implementación del subsistema de registro de mobjects por identificador (`id`), métodos de eliminación atómica (`eliminar_objeto`, `remover_objeto`, `desvanecer_todo`) con efectos 'Uncreate', 'FadeOut' y 'Shrink', y soporte nativo para inicialización de escena desde etiquetas LaTeX (`iniciar_con_texto`).
* **v9.0 - Universal Replacement Transform Engine:** Implementación del método de metamorfosis universal `transformar_objeto` (con alias `replacement_transform`), capaz de mutar cualquier mobject registrado de tipo función, punto o label hacia cualquier otro tipo con preservación de tablas de identificadores, resolución de dominio perimetral y adaptabilidad de coordenadas.
* **v10.0 - Pipeline de Ejecución Concurrente / Paralela (Parallel Animation Engine):** Implementación del subsistema de concurrencia gráfica basado en `iniciar_bloque_paralelo()`, `cerrar_bloque_paralelo()` y el context manager `bloque_paralelo()`. Permite el empaquetado y detonación sincrónica de múltiples transformaciones morfológicas (`ReplacementTransform`), creaciones geométricas y purgas atómicas en un único ciclo `self.play(*anims)`, sincronizando transiciones multidimensionales coordinadas sin retardos secuenciales intermedios.

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