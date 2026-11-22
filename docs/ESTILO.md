# «Pizarra Analítica» — Sistema visual del Animador Matemático

> Guía abstracta extraída de `src/manim_studio/motor/plantillas/` y `src/manim_studio/motor/planos/generar_plano.py`.
> No describe una plantilla concreta: describe **las reglas que hacen que todas se vean como el mismo canal**.
> Sirve como referencia humana y como base del prompt de sistema (`docs/PROMPT_SISTEMA_MANIM.md`).

---

## 0. Principios

1. **Una idea por plano.** La curva (o la fórmula) es la protagonista; todo lo demás la señala.
2. **Jerarquía por contraste, no por cantidad.** Fondo casi negro, rejilla tenue, curva saturada, anotación blanca, resultado verde.
3. **Anotación quirúrgica.** Solo se marca lo que la narración está diciendo: un punto, una proyección, una llave, un corchete.
4. **Ritmo respiratorio.** Toda animación va seguida de una pausa. Nunca dos transformaciones encadenadas sin un beat.
5. **La cámara encuadra, no tiembla.** Encuadre automático con 10 % de margen; movimientos lentos y pocos.
6. **El HUD es papel de calco.** Paneles translúcidos, esquinas redondeadas, borde de 1,5 px. Nunca tapan la zona de interés.
7. **El color significa.** Un color = un rol matemático. No se usa color para decorar.

---

## 1. Paleta semántica

| Rol | Valor | Dónde se usa |
|---|---|---|
| Fondo | `#0B0B10` (o negro Manim) | lienzo completo |
| Panel HUD | `#181825` @ `0.85` | fondo de paneles de enunciado |
| Borde de panel | `#45475a` @ `1.5 px` | separación sutil del panel |
| Banner de cierre | `#11111b` @ `0.90` | conclusión / resultado |
| Rejilla | `BLUE` @ `0.4` | `NumberPlane` |
| Ejes y números | `GREY_A` | `Axes`, `add_coordinates()` |
| Curva principal `f(x)` | `RED` @ `0.8` (o `#89b4fa`) | protagonista |
| Punto ancla / entrada | `YELLOW` / `#f9e2af` | `x₀`, `a`, `b` |
| Punto móvil | `#00FFCC` | barridos, secantes, Riemann |
| Raíz / óptimo | `GREEN_A` / `GREEN_B` / `GREEN_C` | solución, anillo, banner |
| Error / divergencia | `#f38ba8` | lo que falla o se descarta |
| Auxiliar / proyección | `GREY_B` / `#6c7086` | líneas punteadas, fantasmas |
| Texto de cuerpo | `WHITE` / `#cdd6f4` | HUD, etiquetas |
| Acento LaTeX | `YELLOW` | símbolo que se está despejando |
| Región factible | relleno `#89b4fa` @ `0.35`, borde `#b4befe` @ `1.5` | área sombreada |

**Regla de acento:** en una fórmula solo se colorea **el símbolo que cambia** (`\textcolor{yellow}{b}`). Nunca la fórmula entera.

---

## 2. Tipografía matemática

- Toda fórmula va en `MathTex`. `Text` se reserva para palabras sueltas dentro de un panel (`\text{Sujeto a:}`).
- Títulos de panel: `\mathbf{}` + `\text{}` para palabras, `font_size=23`.
- Ecuación principal: `font_size=21`. Línea secundaria: `19`. Restricciones: `18`.
- Resultado final: `font_size=24`, color `GREEN_B`.
- Formato numérico: `:g` para coeficientes (evita `5.0x`), `:.2f` para el resultado final.
- Etiquetas de punto: `MathTex` con altura `0.025 × ancho_camara`.
- Fórmula flotante: escala `ancho_camara / 20`; si excede `0.25 × ancho_camara`, `scale_to_fit_width`.
- Fórmula central (protagonista): escala `ancho_camara / 10`.
- Etiqueta de llave: escala `ancho_camara / 20`.

**Símbolos canónicos**

| Concepto | LaTeX |
|---|---|
| Función | `f(x) = ...` |
| Iteración | `x_{n+1} = ...` |
| Intervalo | `[a,\,b]` |
| Error | `|x_n - x^*|` |
| Límite | `\lim_{h \to 0}` |
| Integral | `\int_{a}^{b} f(x)\,dx` |
| Serie | `\sum_{n=0}^{\infty}` |
| Óptimo | `x^* = (x_1, x_2)` |

---

## 3. Composición y HUD

- Lienzo **16:9**. Todo se calcula en función de `ancho_camara`, nunca en unidades absolutas.
- Cuatro anclajes:
  - `UL` → definición / función del problema.
  - `UR` → enunciado, restricciones, datos.
  - `DL` → bitácora de pasos o eje cartesiano.
  - `DR` → resultado parcial o fórmula actual.
- Separación al borde: `0.03 × ancho_camara` horizontal y `0.03 × ancho_camara × 9/16` vertical.
- Panel: `RoundedRectangle(corner_radius=0.15)`, padding `0.35`, fill `#181825` @ `0.85`, stroke `#45475a` @ `1.5`.
- Banner: `corner_radius=0.1`, padding `0.5 / 0.3`, fill `#11111b` @ `0.9`, stroke verde, `to_edge(UP, buff=0.45)`.
- El HUD nunca ocupa más del **25 %** del ancho de cámara. Si no cabe, se pagina o se reduce.
- Zona prohibida: el HUD no puede cubrir el punto de interés ni el extremo de la curva que se está explicando.

**Mapa mental del frame**

```
┌──────────────────────────────────────────────┐
│  [UL] definición        [UR] enunciado       │
│                                              │
│            curva / figura central            │
│                                              │
│  [DL] bitácora / ejes   [DR] resultado       │
└──────────────────────────────────────────────┘
```

---

## 4. Cámara y plano

- `MovingCameraScene` con encuadre automático:
  - `ancho_camara = max(dist_x, dist_y × 16/9)`
  - `alto_camara = ancho_camara / (16/9)`
  - padding del **10 %** en ambos ejes.
  - centro en el centro matemático real, no en el centro con padding.
- Movimiento: `self.camera.frame.animate.move_to(...).set_width(...)`, `run_time=1.5`.
- Máximo **2 reencuadres** por escena. Solo cuando cambia el dominio, no en cada paso.
- Zoom máximo entre pasos: **2×**. Si hace falta más, se divide en dos beats.
- `NumberPlane` con `stroke_opacity=0.4` y `stroke_color=BLUE`; paso calculado con la serie 1-2-5-10 para ~12 divisiones.
- `Axes` de `6.8 × 6.8` cuando el HUD ocupa una esquina; `to_corner(DL, buff=0.45)`.
- Puntos: `Dot(radius = 0.004 × ancho_camara)`.
- Proyecciones: `DashedLine` gris, `z_index=2`.
- Llaves: `BraceBetweenPoints`, `z_index=4`, etiqueta `next_to(..., buff=0.01 × ancho_camara)`.

**Z-index canónico**

| Capa | z |
|---|---|
| Rejilla / área | 1 |
| Curva | 1–2 |
| Auxiliares (proyecciones, secantes) | 2–3 |
| Llaves / anotaciones | 4–5 |
| Puntos | 5 |
| HUD / fórmula central | 20–30 |

---

## 5. Ritmo y tiempos

Toda plantilla declara `TIEMPOS_BASE` y lo escala con `ESCALA_TIEMPO`:

```python
ESCALA_TIEMPO = 1.0
TIEMPOS_BASE = { ... }
T = {k: v * ESCALA_TIEMPO for k, v in TIEMPOS_BASE.items()}
```

| Tipo de beat | `t_anim` | `t_wait` |
|---|---|---|
| Micro (etiqueta, punto) | 0.5–0.8 s | 0.1–0.3 s |
| Construcción (plano, curva) | 1.0–1.5 s | 0.3–0.5 s |
| Transformación algebraica | 1.0–1.5 s | 0.5–1.0 s |
| Barrido paramétrico | 2.0–3.5 s | 0.5–1.0 s |
| Reencuadre de cámara | 1.5–2.0 s | 0.3–0.5 s |
| Conclusión / resultado | 1.5–2.0 s | 2.0–2.5 s |
| Cierre | 1.5–2.0 s | 0.5 s (negro) |

**Reglas**

- `t_wait ≥ 0.5 × t_anim` en pasos conceptuales; `0.2` en pasos mecánicos.
- Un Short de 60 s tiene **6–9 beats**. Un vídeo de 8–12 min tiene **40–60 beats**.
- El presupuesto se reparte: setup 15 %, desarrollo 65 %, conclusión 20 %.
- Si el factor de escala sale fuera de `[0.5, 3.0]`, no se estira: se recorta el número de iteraciones o de pasos.

---

## 6. Idioma de movimiento

| Intención | Animación |
|---|---|
| Primera aparición de una fórmula | `Write` |
| Evolución algebraica | `TransformMatchingShapes` si similitud ≥ 0.65; si no, `ReplacementTransform` |
| Construir geometría | `Create` |
| Entrar un panel | `FadeIn(shift=0.3 × dirección)` |
| Movimiento continuo | `always_redraw` + `ValueTracker` |
| Énfasis | `Indicate` / `Circumscribe` (1.0 s) |
| Salida por defecto | `FadeOut` |
| Salida de geometría dibujada | `Uncreate` |
| Salida de un punto | `ShrinkToCenter` |
| Cierre de escena | `FadeOut` de todos los mobjects, 1.5–2.0 s |

**Secuencia canónica de un paso**

```
Write/Transform  →  wait  →  anotación (punto, llave, proyección)  →  wait
```

Nunca más de **3 mobjects** animándose a la vez, salvo la revelación final.

---

## 7. Reglas por tipo de escena

| Escena | Protagonista | HUD | Cierre |
|---|---|---|---|
| Método numérico (bisección, Newton, secante) | curva + iteración | `UR` enunciado, `DR` tabla/fórmula | raíz en verde + banner |
| Cálculo (derivada, integral, Taylor) | curva + elemento móvil | `DL` fórmula, `DR` valor | resultado + fade |
| Álgebra | fórmula central | `UL/UR` contexto | fórmula final + fade |
| Optimización (Simplex) | región factible + camino | `UR` formulación, `DL` ejes | anillo verde + banner `Z_max` |
| Fourier / series | suma parcial que converge | `DR` fórmula | onda final + fade |
| Short vertical | una sola idea | mínimo, tipografía grande | resultado en < 2 s |

---

## 8. Anti-patrones

- ❌ `Text` para fórmulas.
- ❌ `self.play(...)` directo dentro de un builder: rompe la cola y los tiempos.
- ❌ HUD encima de la curva o del punto que se explica.
- ❌ Rejilla blanca a opacidad completa.
- ❌ Más de 3 animaciones simultáneas.
- ❌ Zoom mayor a 2× en un solo beat.
- ❌ Colores decorativos sin significado.
- ❌ Framing con unidades absolutas en vez de `ancho_camara`.
- ❌ Terminar sin fade: el corte a negro se siente amateur.
- ❌ Encadenar transformaciones sin `wait`.

---

## 9. Checklist de aceptación

- [ ] La curva es visible al menos el 80 % del tiempo.
- [ ] Cada fórmula se escribe una sola vez; después se transforma.
- [ ] Cada beat tiene su `t_wait`.
- [ ] El HUD no tapa la zona de interés.
- [ ] Los colores respetan los roles de la tabla.
- [ ] El resultado final es verde y tiene banner o énfasis.
- [ ] La cámara se mueve como máximo 2 veces.
- [ ] La duración total está dentro de ±5 % del objetivo.
- [ ] No hay `NaN`/`inf` en el muestreo de la función.
- [ ] Renderiza en `low_quality` sin errores.
- [ ] Cierre con fade y 0.5 s de negro.

---

## 10. Implementación de referencia

Este bloque puede convertirse en `src/manim_studio/motor/plantillas/estilo.py` para que todas las escenas compartan constantes y helpers.

```python
# src/manim_studio/motor/plantillas/estilo.py — constantes y helpers del sistema «Pizarra Analítica»
from manim import *
import math

ESTILO = {
    "fondo": "#0B0B10",
    "panel_fill": "#181825",
    "panel_stroke": "#45475a",
    "banner_fill": "#11111b",
    "grid": BLUE,
    "grid_opacity": 0.4,
    "curva": RED,
    "curva_opacity": 0.8,
    "ancla": YELLOW,
    "movil": "#00FFCC",
    "exito": GREEN_B,
    "error": "#f38ba8",
    "auxiliar": GREY_B,
    "texto": WHITE,
    "acento": YELLOW,
    "region_fill": "#89b4fa",
    "region_stroke": "#b4befe",
}


def radio_punto(ancho_camara: float) -> float:
    return ancho_camara * 0.004


def alto_etiqueta(ancho_camara: float) -> float:
    return ancho_camara * 0.025


def paso_rejilla(distancia: float) -> float:
    """Serie 1-2-5-10 para ~12 divisiones visibles."""
    ideal = distancia / 12.0
    magnitud = 10 ** math.floor(math.log10(ideal))
    fraccion = ideal / magnitud
    if fraccion < 1.5:
        multiplo = 1
    elif fraccion < 3.5:
        multiplo = 2
    elif fraccion < 7.5:
        multiplo = 5
    else:
        multiplo = 10
    return magnitud * multiplo


def panel_hud(contenido: Mobject, esquina=UR, ancho_camara: float = 14.0) -> VGroup:
    max_width = ancho_camara * 0.25
    if contenido.width > max_width:
        contenido.scale_to_fit_width(max_width)
    fondo = RoundedRectangle(
        corner_radius=0.15,
        width=contenido.width + 0.35,
        height=contenido.height + 0.35,
        fill_color=ESTILO["panel_fill"],
        fill_opacity=0.85,
        stroke_color=ESTILO["panel_stroke"],
        stroke_width=1.5,
    ).move_to(contenido)
    buff = 0.03 * ancho_camara
    return VGroup(fondo, contenido).to_corner(esquina, buff=buff)


def banner_resultado(texto: Mobject) -> VGroup:
    fondo = RoundedRectangle(
        corner_radius=0.1,
        width=texto.width + 0.5,
        height=texto.height + 0.3,
        fill_color=ESTILO["banner_fill"],
        fill_opacity=0.9,
        stroke_color=GREEN_C,
        stroke_width=1.5,
    ).move_to(texto)
    return VGroup(fondo, texto).to_edge(UP, buff=0.45).set_z_index(20)


def etiqueta_punto(punto: Mobject, tex: str, ancho_camara: float) -> MathTex:
    return (
        MathTex(tex)
        .set_height(alto_etiqueta(ancho_camara))
        .next_to(punto, UP, buff=radio_punto(ancho_camara) * 1.5)
        .set_z_index(5)
    )
```

**Uso mínimo**

```python
from manim_studio.motor.plantillas.estilo import ESTILO, panel_hud, banner_resultado, etiqueta_punto

hud = panel_hud(MathTex(r"f(x) = x^2 - 2"), esquina=UR, ancho_camara=14.0)
banner = banner_resultado(MathTex(r"x^* = \sqrt{2}", color=ESTILO["exito"]))
```

---

## 11. Extensión a la interfaz

La misma jerarquía se aplica al editor web: superficies planas, una sola idea
por panel y color usado solo como señal.

| Elemento de UI | Regla |
|---|---|
| Fondo de app | `#0a0c0f`, sin gradientes ambientales ni resplandor |
| Paneles | `#111419`, borde `#252b34`, radio `10 px`, sin sombra |
| Texto principal | `#e7e9ec`; texto secundario `#8b939e` |
| Acento | Heredado del tema Manim activo (`--color-primary`) |
| Confirmación / error | `#8fd6a8` / `#e8a0a0`, siempre acompañados de texto |
| Tipografía de títulos | STIX Two Text, peso 500 |
| Tipografía de interfaz | IBM Plex Sans, 13–14 px, sentence case |
| Tipografía de código | JetBrains Mono, 11–12 px |
| Fórmulas vivas | KaTeX en cuanto se escribe; error en rojo, nunca silencioso |
| Iconos | SVG de trazo 1.5, 16–18 px, sin emoji decorativos |
| Editor de código | CodeMirror con línea activa, paréntesis pareados y Ctrl+S |
| Movimiento | transiciones ≤ 200 ms y respeto a `prefers-reduced-motion` |

Reglas adicionales:

- Proporción del preview: el marco adopta el `aspect-ratio` del formato activo.
- El asistente nunca aplica cambios por sorpresa: primero muestra resumen y
  diff; después el usuario elige **Aplicar**, **Descartar** o **Deshacer**.
- Un conflicto de revisión no se resuelve calladamente: se pide una nueva
  propuesta.
- Si un CDN falla, la interfaz degrada a textarea y texto plano sin perder la
  funcionalidad esencial.

---

*Extraído de: `src/manim_studio/motor/plantillas/investigacion_operaciones/Simplex.py`, `src/manim_studio/motor/plantillas/algebra_geometria/*`, `src/manim_studio/motor/plantillas/analisis_numerico/*`, `src/manim_studio/motor/plantillas/calculo_diferencial/*`, `src/manim_studio/motor/plantillas/ecuaciones_diferenciales/*` y `src/manim_studio/motor/planos/generar_plano.py`.*
