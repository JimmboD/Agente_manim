
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
* **`insertar_algebra(fuente_o_texto: str, tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0, tiempo_transformacion: float | None = None, tiempos_transformacion: list[float] | None = None, tiempos_espera: list[float] | None = None, tiempo_escritura: float | None = None) -> self`**
Suspende la topología gráfica activa e invoca el pipeline simbólico en pantalla completa (modo central). Acepta rutas a archivos `.txt`, listas de fórmulas o cadenas multilínea con delimitadores `$$`.

* **`agregar_algebra_flotante(fuente_o_texto: str, posicion: str = "UL", remover_al_final: bool = False, tiempo_animacion: float = 1.0, tiempo_espera: float = 1.0, id: str | None = None, tiempo_transformacion: float | None = None, tiempos_transformacion: list[float] | None = None, tiempos_espera: list[float] | None = None, tiempo_escritura: float | None = None, tiempo_replacement_transform: float | None = None, tiempo_pantalla: float | None = None, tiempo_entre_pasos: float | None = None) -> self`**
Inyecta un HUD analítico vectorial superpuesto anclado a las esquinas del viewport (`UL`, `UR`, `DL`, `DR`) mediante enrutamiento acoplado a la cámara (`aligned_edge` routing).
  * **Control Temporal Escalar y Vectorial:**
    * `tiempo_escritura (float)`: Duración específica para el `Write` inicial de la primera ecuación o encabezado.
    * `tiempo_transformacion` / `tiempo_replacement_transform` (float) o `tiempos_transformacion` (list[float]): Duración de las interpolaciones algebraicas (`ReplacementTransform` o `TransformMatchingShapes`). Permite asignar duraciones heterogéneas paso a paso (`[t_1, t_2, ...]`).
    * `tiempo_espera` / `tiempo_pantalla` / `tiempo_entre_pasos` (float) o `tiempos_espera` (list[float]): Tiempo de permanencia y lectura en pantalla tras cada paso (`[w_1, w_2, ...]`).
    * *Regla de auto-extensión:* Si la lista provista en `tiempos_transformacion` o `tiempos_espera` contiene menos elementos que pasos a ejecutar, el motor replica automáticamente el último valor hasta cubrir la totalidad de la secuencia.
    * `remover_al_final (bool)`: Si es `True`, desvanece el HUD al concluir el último paso con `FadeOut`. Si es `False`, el HUD permanece visible en la escena.

* **`animar_algebra(fuente_o_texto: str, posicion: str | None = None, remover_al_final: bool = False, tiempo_transformacion: float = 1.0, tiempo_espera: float = 1.0, tiempos_transformacion: list[float] | None = None, tiempos_espera: list[float] | None = None, tiempo_escritura: float | None = None, id: str | None = None) -> self`**
Método unificado polimórfico del lector de álgebra. Detecta automáticamente si la posición es de esquina (`"UL"`, `"UR"`, `"DL"`, `"DR"`) para derivar a `agregar_algebra_flotante`, o si es central / pantalla completa (`None`, `"center"`, `"fullscreen"`) para derivar a `insertar_algebra`.
  * *Aliases:* `procesar_algebra`, `reproducir_algebra`, `mostrar_algebra`.

* **`transformar_algebra_flotante(id_origen: str, nuevo_texto: str, posicion: str = "UL", id_destino: str | None = None, tiempo_animacion: float = 1.5, tiempo_espera: float = 0.0, animacion: str = "TransformMatchingShapes") -> self`**
Mutación directa in-place de un HUD registrado previamente en la escena por su `id`. Transforma directamente el mobject origen hacia una nueva tarjeta LaTeX sin requerir ciclos secuenciales de escritura (`Write`) ni parpadeos.
  * *Aliases:* `mutar_algebra_flotante`, `actualizar_algebra_flotante`.

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

---

## 5. Control de Tiempos y Ritmo en Plantillas Numéricas (Pacing por Pasos)

Las plantillas de algoritmos numéricos ubicadas en `Plantillas/Análisis numérico/` (`Bisección.py`, `Regla falsa.py` y `Newton-Raphson.py`) cuentan con un bloque de constantes explícitas para controlar de forma granular la duración de animación (`anim`) y el tiempo de reposo (`espera`) de cada fase del algoritmo.

> [!IMPORTANT]
> **Directiva de Ritmo Predefinido (Agent & User Rule):**
> Todos los valores de tiempo declarados en la cabecera de las plantillas representan el **ritmo estándar predefinido** de la animación (equivalente a los tiempos base del motor). **NO deben modificarse por iniciativa propia.** Únicamente deben alterarse cuando el usuario o la especificación del requerimiento incluya una indicación explícita (por ejemplo: *"haz el paso del cálculo más lento"*, *"acelera las transiciones"*, *"dale 3 segundos al HUD para leerlo con calma"*, etc.).

---

### 5.1. Plantilla: Método de Bisección (`Bisección.py`)

Esta plantilla divide iterativamente el intervalo $[a, b]$ a la mitad y traslada el extremo respectivo sobre la curva.

| Paso | Constante de Animación | Constante de Espera | Valor Predefinido (`anim` / `espera`) | Descripción Técnica |
| :--- | :--- | :--- | :--- | :--- |
| **Paso 0: Puntos iniciales** | `T_PUNTOS_INI_ANIM` | `T_PUNTOS_INI_ESPERA` | `0.5s` / `0.1s` | Creación de los puntos ancla $A(a, f(a))$ y $B(b, f(b))$. |
| **Paso 1: HUD Algebraico** | `T_HUD_ANIM` | `T_HUD_ESPERA` | `1.0s` / `1.0s` | Despliegue de la tarjeta LaTeX superior izquierda con la iteración, fórmula de $c_i$, $f(c_i)$ y el error relativo. |
| **Paso 2: Proyección punto $c$** | `T_PROY_PUNTO_ANIM`<br>`T_PROY_LINEA_ANIM` | `T_PROY_PUNTO_ESPERA`<br>`T_PROY_LINEA_ESPERA` | `0.5s` / `1.0s`<br>`0.8s` / `1.0s` | Marca del punto medio $c$ sobre el eje X y trazado de la línea discontinua hacia la curva $f(c)$. |
| **Paso 3: Limpieza de guías** | `T_LIMPIEZA_LINEA_ANIM`<br>`T_LIMPIEZA_PUNTO_ANIM` | `T_LIMPIEZA_LINEA_ESPERA`<br>`T_LIMPIEZA_PUNTO_ESPERA` | `0.5s` / `0.1s`<br>`0.5s` / `0.2s` | `Uncreate` de la línea vertical y `FadeOut` del punto blanco antes del movimiento de la cota. |
| **Paso 4: Movimiento sobre curva** | `T_MOVIMIENTO_CURVA_ANIM` | `T_MOVIMIENTO_CURVA_ESPERA` | `1.5s` / `1.0s` | Desplazamiento cinemático (`animar_punto_sobre_curva`) del extremo descartado hacia la nueva posición $c$. |
| **Paso 5: Cierre de escena** | `T_FINAL_ANIM` | `T_FINAL_ESPERA` | `2.0s` / `1.0s` | Disolución general suave (`desvanecer_todo`) al término de las iteraciones. |

---

### 5.2. Plantilla: Método de Regla Falsa (`Regla falsa.py`)

Esta plantilla traza una recta secante entre los extremos y resuelve la raíz analítica por interpolación lineal.

| Paso | Constante de Animación | Constante de Espera | Valor Predefinido (`anim` / `espera`) | Descripción Técnica |
| :--- | :--- | :--- | :--- | :--- |
| **Paso 0: Puntos iniciales** | `T_PUNTOS_INI_ANIM` | `T_PUNTOS_INI_ESPERA` | `0.5s` / `0.1s` | Creación de los puntos extremos iniciales $A$ y $B$. |
| **Paso 1: Secante inicial** | `T_SECANTE_INI_ANIM` | `T_SECANTE_INI_ESPERA` | `1.0s` / `1.0s` | Trazado de la recta secante $y - y_0 = m(x - x_0)$ (sólo en la primera iteración). |
| **Paso 2: HUD Algebraico** | `T_HUD_ANIM` | `T_HUD_ESPERA` | `1.0s` / `1.0s` | Despliegue de la iteración, cálculo analítico de $x_i$, valor funcional y error relativo. |
| **Paso 3: Proyección punto raíz** | `T_PROY_PUNTO_ANIM`<br>`T_PROY_LINEA_ANIM` | `T_PROY_PUNTO_ESPERA`<br>`T_PROY_LINEA_ESPERA` | `0.5s` / `1.0s`<br>`0.8s` / `1.0s` | Marca del corte de la secante con el eje X y proyección vertical hacia $f(c)$. |
| **Paso 4: Limpieza de guías** | `T_LIMPIEZA_LINEA_ANIM`<br>`T_LIMPIEZA_PUNTO_ANIM` | `T_LIMPIEZA_LINEA_ESPERA`<br>`T_LIMPIEZA_PUNTO_ESPERA` | `0.5s` / `0.1s`<br>`0.5s` / `0.2s` | Purga atómica de la línea vertical y el marcador de raíz temporal. |
| **Paso 5: Convergencia paramétrica**| `T_CONVERGENCIA_ANIM` | `T_CONVERGENCIA_ESPERA` | `2.0s` / `1.0s` | Vinculación del extremo móvil, la secante infinita y el punto raíz mediante `animar_convergencia_parametrica`. |
| **Paso 6: Cierre de escena** | `T_FINAL_ANIM` | `T_FINAL_ESPERA` | `2.0s` / `1.0s` | `desvanecer_todo` final a negro. |

---

### 5.3. Plantilla: Método de Newton-Raphson (`Newton-Raphson.py`)

Esta plantilla computa derivadas analíticas y utiliza rectas tangentes que pivotan sincrónicamente sobre la curva.

| Paso | Constante de Animación | Constante de Espera | Valor Predefinido (`anim` / `espera`) | Descripción Técnica |
| :--- | :--- | :--- | :--- | :--- |
| **Paso 0: Punto ancla inicial** | `T_PUNTO_INI_ANIM` | `T_PUNTO_INI_ESPERA` | `0.5s` / `0.1s` | Instanciación del punto semilla $x_0$ sobre la curva $f(x)$. |
| **Paso 1: Tangente inicial** | `T_TANGENTE_INI_ANIM` | `T_TANGENTE_INI_ESPERA` | `1.0s` / `1.0s` | Trazado de la recta tangente con pendiente $f'(x_0)$ (sólo en la primera iteración). |
| **Paso 2: HUD Algebraico** | `T_HUD_ANIM` | `T_HUD_ESPERA` | `1.0s` / `1.0s` | Despliegue de la fórmula de Newton-Raphson $x_{i+1} = x_i - \frac{f(x_i)}{f'(x_i)}$ y error. |
| **Paso 3: Proyección de corte** | `T_PROY_PUNTO_ANIM`<br>`T_PROY_LINEA_ANIM` | `T_PROY_PUNTO_ESPERA`<br>`T_PROY_LINEA_ESPERA` | `0.5s` / `1.0s`<br>`0.8s` / `1.0s` | Ubicación del corte con el eje X y proyección discontinua hacia la nueva evaluación en la curva. |
| **Paso 4: Transición en paralelo** | `T_TRANSICION_PARALELO_ANIM` | `T_TRANSICION_PARALELO_ESPERA` | `2.0s` / `1.0s` | Ejecución concurrente dentro de `bloque_paralelo`: rotación de la tangente a la nueva pendiente mientras el punto ancla viaja sobre la curva. |
| **Paso 5: Limpieza de guías** | `T_LIMPIEZA_LINEA_ANIM`<br>`T_LIMPIEZA_PUNTO_ANIM` | `T_LIMPIEZA_LINEA_ESPERA`<br>`T_LIMPIEZA_PUNTO_ESPERA` | `0.5s` / `0.1s`<br>`0.5s` / `0.2s` | `Uncreate` de la proyección y `FadeOut` del punto de corte temporal. |
| **Paso 6: Cierre de escena** | `T_FINAL_ANIM` | `T_FINAL_ESPERA` | `2.0s` / `1.0s` | Desvanecimiento final suave de la escena completa. |

---

### 5.4. Ejemplos de Ajuste de Ritmo bajo Demanda

Cuando el usuario requiera modificar el tiempo de algún paso específico, modifique **únicamente** la constante correspondiente en la cabecera:

```python
# Ejemplo 1: El usuario indica que las explicaciones matemáticas deben durar 3 segundos para leerse con calma
T_HUD_ESPERA = 3.0

# Ejemplo 2: El usuario indica que la convergencia de la secante debe ser lenta y detallada (4 segundos de animación)
T_CONVERGENCIA_ANIM = 4.0

# Ejemplo 3: El usuario solicita un render ultra rápido / express
T_HUD_ANIM = 0.5
T_HUD_ESPERA = 0.2
T_CONVERGENCIA_ANIM = 1.0
T_CONVERGENCIA_ESPERA = 0.2
```

---

### 5.5. Control de Ritmo y Escalado para Formato Corto (`Plantillas/Short/tiempo.py`)

Para producciones en formato de video vertical corto (**Shorts / Reels / TikTok**), el sistema dispone del módulo `tiempo.py` que calcula la duración máxima y es capaz de **escalar armónicamente la cadencia** de cada paso para encajar un número de iteraciones en un tiempo límite deseado (por ejemplo, exactamente $60.0\,\text{s}$):

```python
from Plantillas.Short.tiempo import (
    calcular_tiempo_maximo,
    desglosar_tiempo_maximo,
    verificar_duracion_short,
    calcular_vector_tiempos
)

# 1. Cálculo directo del tiempo total máximo (segundos)
t_max = calcular_tiempo_maximo("biseccion", max_iteraciones=3) # -> 55.5s

# 2. Vector de tiempos escalados para encajar 4 iteraciones en 60 segundos
vector_bis = calcular_vector_tiempos("biseccion", max_iteraciones=4, tiempo_deseado=60.0)
print(list(vector_bis))          # [0.42, 0.08, 0.84, 0.84, 0.42, 0.84, ...]
print(vector_bis.T_HUD_ANIM)     # 0.84s (acceso por clave)
print(vector_bis.tiempo_estimado) # 59.8s

# 3. Vector para todos los métodos a la vez
vectores = calcular_vector_tiempos("todos", max_iteraciones=4, tiempo_deseado=60.0)
v_rf = vectores["regla_falsa"]
v_nr = vectores["newton_raphson"]

# 4. Validación contra el límite de 60 segundos
resultado = verificar_duracion_short("newton_raphson", max_iteraciones=3, limite_segundos=60.0)
print(resultado["es_apto_short"])   # True (58.4s)
print(resultado["margen_restante"])  # 1.6s
```

---

### 5.6. Generador Automatizado de Código Manim para Shorts (`Plantillas/Short/generador_short.py`)

Ubicado en la carpeta `Plantillas/Short/`, este módulo construye dinámicamente scripts ejecutables de Manim listos para producción:
- **Derivación simbólica automática**: Para Newton-Raphson, calcula automáticamente $f'(x)$ usando SymPy y formatea el código en Python puro (`math.exp`, `math.cos`, etc.) y en LaTeX para el HUD visual.
- **Inyección de cadencia calculada**: Invoca `calcular_vector_tiempos()` para inyectar las constantes escaladas exactas en la cabecera del código.
- **Soporte CLI y API**: Puede ejecutarse desde la terminal o consumirse desde el servidor web:

```bash
# Ejecución vía línea de comandos
python Plantillas/Short/generador_short.py --metodo biseccion --tiempo 60 --iteraciones 4 --funcion "exp(x) - 3*(x**2)"
```

Uso desde Python:
```python
from Plantillas.Short import generar_codigo_short

res = generar_codigo_short(
    metodo="newton_raphson",
    funcion="x**3 - x - 2",
    tiempo_deseado=45.0,
    max_iteraciones=4,
    x0=1.5,
    save_to_main=True  # Escribe directamente en main.py
)

print(f"Duración estimada: {res['tiempo_estimado']}s | Factor: {res['factor_escalado']}x")
```

---

### 5.7. Creador Visual de Shorts en Manim Studio Web (`view-short`)

En la interfaz web de **Manim Studio**, dentro del **Panel de Control &rarr; Vistas de Trabajo**, se encuentra la subpágina **Creador de Shorts** (`#view-short`):

1. **Selección de Método Numérico**: Tarjetas visuales de alto contraste para elegir entre **Bisección**, **Regla Falsa** y **Newton-Raphson**, con insignias de convergencia y fórmulas matemáticas.
2. **Control de Tiempo y Cadencia**:
   - Chips rápidos de presets: `15s Micro`, `30s Reels`, `45s Fluido`, `60s Shorts Max`.
   - Control deslizante interactivo con indicador de rango de $10\,\text{s}$ a $120\,\text{s}$.
3. **Función Objetivo y Parámetros Contextuales**:
   - Entrada de fórmulas en sintaxis Python (`exp(x) - 3*x**2`, `x**3 - x - 2`, etc.).
   - Chips de plantillas clásicas para autocompletado en 1 clic.
   - Renderizado en vivo con KaTeX de $f(x)$ y de la derivada analítica $f'(x)$.
   - Campos dinámicos: Intervalo $[a, b]$ para Bisección/Regla Falsa o Punto Inicial $x_0$ para Newton-Raphson.
4. **Número de Iteraciones**: Selector deslizante de 1 a 8 iteraciones.
5. **Panel de Diagnóstico Temporal en Tiempo Real**:
   - Medidor heroico central de duración estimada.
   - Insignia de compatibilidad: `⚡ APTO SHORT (<= 60s)` o `⚠️ EXCEDE LÍMITE SHORT`.
   - Etiqueta de velocidad de cadencia (ej. `0.84x Ágil`).
   - Barra de distribución temporal visual (Setup, Puntos iniciales, Iteraciones, Cierre).
   - Nube de constantes de tiempo ($T$) escaladas.
6. **Acciones Integradas**:
   - **⚡ Cargar en Editor (main.py)**: Guarda el código en `main.py`, actualiza el editor Ace y cambia a la vista de animación manual.
   - **▶ Renderizar Short Directo**: Compila y transmite los logs en vivo vía SSE hacia la consola y el reproductor de video.
   - **📋 Copiar Código**: Copia el script completo al portapapeles.

---

### 5.8. Modulación Granular de Pasos y Visualización en el HUD de Plantillas (Análisis Numérico y Serie de Taylor)

El motor algebraico (`Algebra/algebra.py`) integra una función de resolución temporal (`_resolver_tiempos`) que es **totalmente extrapolable, compatible e intercambiable** con las llamadas del HUD superior izquierdo (`posicion="UL"`) implementadas en las plantillas de `Plantillas/Análisis numérico/` y `Plantillas/Cálculo diferencial/Serie de Taylor.py`.

Cada bloque multilínea de texto delimitado por `$$` pasado a `escena.agregar_algebra_flotante()` es descompuesto automáticamente por el lector en una secuencia de **pasos atómicos**:

#### A. Mapeo en Plantillas de Análisis Numérico (Bisección, Regla Falsa, Newton-Raphson)
En cada iteración del bucle numérico se genera un bloque LaTeX compuesto por 4 pasos secuenciales:
1. `Paso 0 (Inicial): $$\text{Iteración: } i$$` (Identificador de iteración, renderizado mediante `Write`)
2. `Paso 1: $$c_i = \dots$$` o `$$x_{i+1} = \dots$$` (Sustitución analítica)
3. `Paso 2: $$f(c_i) \approx \dots$$` o `$$x_i \approx \dots$$` (Evaluación numérica)
4. `Paso 3: $$\text{Error: } \dots$$` (Cálculo del error relativo)

Por defecto, las plantillas emplean las constantes globales escalares `T_HUD_ANIM` y `T_HUD_ESPERA`:
```python
escena.agregar_algebra_flotante(
    texto_hud, posicion="UL", remover_al_final=True, 
    tiempo_animacion=T_HUD_ANIM, tiempo_espera=T_HUD_ESPERA
)
```

**Extrapolación con tiempos diferenciados por paso:**
Para variar de manera precisa la velocidad de escritura del encabezado, el tiempo de transformación de cada línea matemática y el tiempo de permanencia/lectura en pantalla de cada resultado, basta sustituir las constantes por los parámetros vectoriales soportados nativamente por el motor:

```python
# Ejemplo: Control granular paso a paso en Bisección / Regla Falsa / Newton-Raphson
escena.agregar_algebra_flotante(
    texto_hud,
    posicion="UL",
    remover_al_final=True,
    tiempo_escritura=0.5,                       # Escritura rápida del título 'Iteración: i'
    tiempos_transformacion=[0.5, 1.2, 0.8, 0.5], # [Título, Sustitución analítica, Evaluación funcional, Error]
    tiempos_espera=[0.3, 1.5, 1.0, 2.5]         # Permite leer con calma la sustitución (1.5s) y el error final (2.5s)
)
```

#### B. Mapeo en la Plantilla de Cálculo Diferencial (Serie de Taylor)
En `Plantillas/Cálculo diferencial/Serie de Taylor.py`, cada ciclo de construcción del polinomio genera 2 pasos algebraicos:
1. `Paso 0 (Inicial): $$\text{Grado: } i$$`
2. `Paso 1: $$T_{i}(x) = \dots$$` (Polinomio de Taylor acumulado)

**Extrapolación en Serie de Taylor:**
```python
# Modulación temporal en Serie de Taylor:
escena.agregar_algebra_flotante(
    texto_hud,
    posicion="UL",
    remover_al_final=True,
    tiempo_escritura=0.4,                 # Escritura concisa del grado
    tiempos_transformacion=[0.4, 1.0],    # 1.0s para la metamorfosis del polinomio completo
    tiempos_espera=[0.2, 2.0]             # Deja visible el polinomio resultante durante 2.0s para apreciarlo
)
```

#### C. Mutación In-Place Persistente sin Re-escritura (Alternativa Avanzada)
Si se requiere que el HUD permanezca fijo en la esquina sin destruirse ni re-escribirse en cada ciclo del bucle, se puede registrar con un identificador persistente (`id="hud_metodo"`) y mutarlo dinámicamente mediante `transformar_algebra_flotante`:
```python
# Iteración 1: Creación del HUD persistente (remover_al_final=False)
if i == 1:
    escena.agregar_algebra_flotante(
        texto_hud, posicion="UL", remover_al_final=False, 
        id="hud_metodo", tiempo_animacion=1.0, tiempo_espera=1.0
    )
else:
    # Iteraciones subsiguientes: Metamorfosis directa de la tarjeta en pantalla
    escena.transformar_algebra_flotante(
        id_origen="hud_metodo",
        nuevo_texto=texto_hud,
        posicion="UL",
        tiempo_animacion=0.8,
        tiempo_espera=1.2,
        animacion="TransformMatchingShapes"
    )
```


