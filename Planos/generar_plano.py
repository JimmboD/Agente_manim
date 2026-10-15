import os
from manim import *
import numpy as np
import math
import scipy.optimize as opt  # <--- NUEVA IMPORTACIÓN PARA PRECISIÓN MATEMÁTICA
from Algebra.algebra import procesar_pasos_algebraicos, procesar_algebra_flotante, procesar_algebra, _obtener_codigos_latex
from Algebra.ExtraerLATEX import extraer_texto_colores
from Planos.rutinas_parametricas import render_convergencia_secante
from contextlib import contextmanager

class AnimadorGrafico:
    def __init__(self, funcion=None, x_min=-5.0, x_max=5.0, dibujar_grafica_inicial=True, iniciar_con_texto=None, dibujar_plano_inicial=True):
        self.funcion = funcion if funcion is not None else (lambda x: 0.0)
        self.funcion_es_dummy = (funcion is None)
        self.x_min = x_min
        self.x_max = x_max
        self.dibujar_grafica_inicial = dibujar_grafica_inicial and (funcion is not None)
        self.iniciar_con_texto = iniciar_con_texto
        self.dibujar_plano_inicial = dibujar_plano_inicial
        self.cola_animaciones = []
        self.objetos = {}
        self.tiempo_espera_actual = 0.0

    def agregar_punto(self, x, y, color=WHITE, label=False, tiempo_animacion=1.0, tiempo_espera=1.0, id=None):
        self.cola_animaciones.append({
            "tipo": "punto", "x": x, "y": y, "color": color, "label": label,
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera, "id": id
        })
        return self 

    def agregar_funcion(self, funcion, x_min=None, x_max=None, color=GREEN, tiempo_animacion=1.0, tiempo_espera=1.0, id=None):
        self.cola_animaciones.append({
            "tipo": "funcion", "funcion": funcion, "x_min": x_min, "x_max": x_max, "color": color,
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera, "id": id
        })
        return self

    def eliminar_objeto(self, id=None, animacion="FadeOut", tiempo_animacion=1.0, tiempo_espera=1.0):
        """
        Elimina un objeto del plano por su identificador (id) o el último agregado si no se especifica.
        Si id='todos', 'all' o '*', desvanece todos los elementos visibles de la escena.
        
        animacion: 'FadeOut', 'Uncreate', 'Shrink' / 'ShrinkToCenter'.
        """
        self.cola_animaciones.append({
            "tipo": "eliminar_objeto", "id": id, "animacion": animacion,
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera
        })
        return self

    def remover_objeto(self, id=None, animacion="FadeOut", tiempo_animacion=1.0, tiempo_espera=1.0):
        """Alias para eliminar_objeto."""
        return self.eliminar_objeto(id=id, animacion=animacion, tiempo_animacion=tiempo_animacion, tiempo_espera=tiempo_espera)

    def desvanecer_todo(self, animacion="FadeOut", tiempo_animacion=1.5, tiempo_espera=1.0):
        """Desvanece todos los elementos visibles de la escena (hace que la animación muera limpiamente)."""
        return self.eliminar_objeto(id="todos", animacion=animacion, tiempo_animacion=tiempo_animacion, tiempo_espera=tiempo_espera)

    def fade_out_plano(self, animacion="FadeOut", tiempo_animacion=1.5, tiempo_espera=1.0):
        """Desvanece el plano cartesiano activo de la escena."""
        return self.eliminar_objeto(id="plano", animacion=animacion, tiempo_animacion=tiempo_animacion, tiempo_espera=tiempo_espera)

    desvanecer_plano = fade_out_plano

    def fade_in_plano(
        self,
        funcion=None,
        x_min=None,
        x_max=None,
        y_min=None,
        y_max=None,
        color=BLUE,
        stroke_opacity=0.4,
        incluir_coordenadas=True,
        dibujar_grafica=False,
        color_grafica=RED,
        desvanecer_anterior=False,
        ajustar_camara=True,
        animacion="FadeIn",
        tiempo_animacion=1.5,
        tiempo_espera=1.0,
        id="plano"
    ):
        """
        Crea e introduce un nuevo plano cartesiano a la escena mediante FadeIn (o Create).
        
        Permite configurar un nuevo rango [x_min, x_max, y_min, y_max], una función opcional,
        ajuste dinámico de la cámara y re-ancla automáticamente cualquier animación posterior
        (puntos, funciones, rectas, áreas, etc.) a este nuevo sistema de coordenadas.

        Parámetros:
        - funcion: (opcional) función f(x) matemática base para auto-ajustar los rangos del nuevo plano.
        - x_min, x_max: rango horizontal deseado (o None para conservar el anterior).
        - y_min, y_max: rango vertical deseado (o None para auto-calcular con f(x) o conservar).
        - color: color de las líneas de la cuadrícula (por defecto BLUE).
        - stroke_opacity: opacidad de las líneas de la cuadrícula (por defecto 0.4).
        - incluir_coordenadas: si True, añade la numeración en los ejes cartesianos.
        - dibujar_grafica: si True y se proporciona una función, dibuja su curva junto con el nuevo plano.
        - color_grafica: color de la curva si dibujar_grafica=True (por defecto RED).
        - desvanecer_anterior: si True y existe un plano previo en escena, le aplica FadeOut simultáneamente.
        - ajustar_camara: si True, reposiciona y redimensiona la cámara suavemente al centro y escala del nuevo plano.
        - animacion: 'FadeIn' (por defecto) o 'Create'.
        - tiempo_animacion: duración de la animación en segundos.
        - tiempo_espera: tiempo de pausa posterior en segundos.
        - id: identificador para registrar el nuevo plano (por defecto 'plano').
        """
        self.cola_animaciones.append({
            "tipo": "fade_in_plano",
            "funcion": funcion,
            "x_min": x_min,
            "x_max": x_max,
            "y_min": y_min,
            "y_max": y_max,
            "color": color,
            "stroke_opacity": stroke_opacity,
            "incluir_coordenadas": incluir_coordenadas,
            "dibujar_grafica": dibujar_grafica,
            "color_grafica": color_grafica,
            "desvanecer_anterior": desvanecer_anterior,
            "ajustar_camara": ajustar_camara,
            "animacion": animacion,
            "t_anim": tiempo_animacion,
            "t_wait": tiempo_espera,
            "id": id,
        })
        return self

    animar_nuevo_plano = fade_in_plano
    nuevo_plano = fade_in_plano
    agregar_nuevo_plano = fade_in_plano
    aparecer_plano = fade_in_plano

    def animar_punto_sobre_curva(self, x_inicio, x_fin, funcion=None, color=YELLOW, tiempo_animacion=1.0, tiempo_espera=1.0, id=None):
        self.cola_animaciones.append({
            "tipo": "movimiento_punto", "x_ini": x_inicio, "x_fin": x_fin,
            "funcion": funcion if funcion else self.funcion, "color": color, 
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera, "id": id
        })
        return self

    def animar_secante(self, x1_ini, x1_fin, x2_ini, x2_fin, funcion=None, color=YELLOW, tiempo_animacion=1.0, tiempo_espera=1.0, id=None):
        self.cola_animaciones.append({
            "tipo": "movimiento_secante",
            "x1_ini": x1_ini, "x1_fin": x1_fin,
            "x2_ini": x2_ini, "x2_fin": x2_fin,
            "funcion": funcion if funcion else self.funcion,
            "color": color, 
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera, "id": id
        })
        return self

    def transformar_a_texto(self, texto_latex, tiempo_animacion=1.5, tiempo_espera=1.0, id=None):
        self.cola_animaciones.append({
            "tipo": "a_texto", "texto": texto_latex,
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera, "id": id
        })
        return self

    def transformar_a_plano(self, tiempo_animacion=1.5, tiempo_espera=1.0):
        self.cola_animaciones.append({
            "tipo": "a_plano",
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera
        })
        return self

    def insertar_algebra(
        self,
        fuente_o_texto,
        tiempo_animacion=1.0,
        tiempo_espera=1.0,
        tiempo_transformacion=None,
        tiempos_transformacion=None,
        tiempos_espera=None,
        tiempo_escritura=None,
        tiempo_replacement_transform=None,
        tiempo_pantalla=None,
        tiempo_entre_pasos=None
    ):
        t_trans = tiempo_replacement_transform if tiempo_replacement_transform is not None else (tiempo_transformacion if tiempo_transformacion is not None else tiempo_animacion)
        t_wait = tiempo_pantalla if tiempo_pantalla is not None else (tiempo_entre_pasos if tiempo_entre_pasos is not None else tiempo_espera)
        self.cola_animaciones.append({
            "tipo": "algebra",
            "fuente": fuente_o_texto,
            "t_anim": t_trans,
            "t_wait": t_wait,
            "t_trans": t_trans,
            "t_wait_step": t_wait,
            "ts_trans": tiempos_transformacion,
            "ts_wait": tiempos_espera,
            "t_write": tiempo_escritura
        })
        return self

    def animar_linea_punteada(self, x1_ini, x1_fin, x2_ini, x2_fin, y1_ini, y2_ini, y1_fin=None, y2_fin=None, color=WHITE, tiempo_animacion=1.0, tiempo_espera=1.0, id=None):
        """
        Dibuja y mueve una línea punteada. 
        Nota: 'y_ini' y 'y_fin' pueden ser números fijos o tu función matemática.
        """
        self.cola_animaciones.append({
            "tipo": "linea_punteada",
            "x1_ini": x1_ini, "x1_fin": x1_fin,
            "x2_ini": x2_ini, "x2_fin": x2_fin,
            "y1_ini": y1_ini, "y1_fin": y1_fin if y1_fin is not None else y1_ini,
            "y2_ini": y2_ini, "y2_fin": y2_fin if y2_fin is not None else y2_ini,
            "color": color, 
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera, "id": id
        })
        return self

    def animar_llave(self, x1_ini, x1_fin, x2_ini, x2_fin, y1_ini, y2_ini, y1_fin=None, y2_fin=None, texto="", direccion=None, color=WHITE, tiempo_animacion=1.0, tiempo_espera=1.0, id=None):
        """
        Dibuja y mueve una llave de acotación entre dos puntos.
        'direccion' puede ser UP, DOWN, LEFT, RIGHT. Si es None, Manim la calcula perpendicular.
        """
        self.cola_animaciones.append({
            "tipo": "llave",
            "x1_ini": x1_ini, "x1_fin": x1_fin,
            "x2_ini": x2_ini, "x2_fin": x2_fin,
            "y1_ini": y1_ini, "y1_fin": y1_fin if y1_fin is not None else y1_ini,
            "y2_ini": y2_ini, "y2_fin": y2_fin if y2_fin is not None else y2_ini,
            "texto": texto, "direccion": direccion,
            "color": color, 
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera, "id": id
        })
        return self

    def agregar_algebra_flotante(
        self,
        fuente_o_texto,
        posicion="UL",
        remover_al_final=False,
        tiempo_animacion=1.0,
        tiempo_espera=1.0,
        id=None,
        tiempo_transformacion=None,
        tiempos_transformacion=None,
        tiempos_espera=None,
        tiempo_escritura=None,
        tiempo_replacement_transform=None,
        tiempo_pantalla=None,
        tiempo_entre_pasos=None
    ):
        t_trans = tiempo_replacement_transform if tiempo_replacement_transform is not None else (tiempo_transformacion if tiempo_transformacion is not None else tiempo_animacion)
        t_wait = tiempo_pantalla if tiempo_pantalla is not None else (tiempo_entre_pasos if tiempo_entre_pasos is not None else tiempo_espera)
        self.cola_animaciones.append({
            "tipo": "algebra_flotante",
            "fuente": fuente_o_texto,
            "posicion": posicion,
            "remover": remover_al_final,
            "t_anim": t_trans,
            "t_wait": t_wait,
            "t_trans": t_trans,
            "t_wait_step": t_wait,
            "ts_trans": tiempos_transformacion,
            "ts_wait": tiempos_espera,
            "t_write": tiempo_escritura,
            "id": id
        })
        return self

    def animar_algebra(
        self,
        fuente_o_texto,
        posicion=None,
        remover_al_final=False,
        tiempo_transformacion=1.0,
        tiempo_espera=1.0,
        tiempos_transformacion=None,
        tiempos_espera=None,
        tiempo_escritura=None,
        tiempo_animacion=None,
        tiempo_replacement_transform=None,
        tiempo_pantalla=None,
        tiempo_entre_pasos=None,
        id=None
    ):
        """
        Función unificada para animar álgebra tanto en pantalla completa ("desde la normalidad", posicion=None o "center")
        como anclada en esquinas ("desde los labels en las gráficas", posicion="UL", "UR", "DL", "DR").
        
        Permite controlar con precisión:
        - Lo que se tarda en hacer cada replacement transform (tiempo_transformacion / tiempos_transformacion / tiempo_replacement_transform).
        - Los tiempos de espera en pantalla entre cada paso (tiempo_espera / tiempos_espera / tiempo_pantalla / tiempo_entre_pasos).
        - El tiempo del primer paso de escritura (tiempo_escritura).
        """
        t_trans = tiempo_replacement_transform if tiempo_replacement_transform is not None else (tiempo_animacion if tiempo_animacion is not None else tiempo_transformacion)
        t_wait = tiempo_pantalla if tiempo_pantalla is not None else (tiempo_entre_pasos if tiempo_entre_pasos is not None else tiempo_espera)

        es_flotante = (
            posicion is not None and 
            str(posicion).upper() not in ["CENTER", "CENTRO", "NORMAL", "FULLSCREEN", "NONE", ""]
        )

        if es_flotante:
            return self.agregar_algebra_flotante(
                fuente_o_texto=fuente_o_texto,
                posicion=posicion,
                remover_al_final=remover_al_final,
                tiempo_animacion=t_trans,
                tiempo_espera=t_wait,
                id=id,
                tiempo_transformacion=t_trans,
                tiempos_transformacion=tiempos_transformacion,
                tiempos_espera=tiempos_espera,
                tiempo_escritura=tiempo_escritura
            )
        else:
            return self.insertar_algebra(
                fuente_o_texto=fuente_o_texto,
                tiempo_animacion=t_trans,
                tiempo_espera=t_wait,
                tiempo_transformacion=t_trans,
                tiempos_transformacion=tiempos_transformacion,
                tiempos_espera=tiempos_espera,
                tiempo_escritura=tiempo_escritura
            )

    procesar_algebra = animar_algebra
    reproducir_algebra = animar_algebra
    mostrar_algebra = animar_algebra
    algebra = animar_algebra

    def transformar_algebra_flotante(
        self, 
        id_origen: str, 
        nuevo_texto: str, 
        posicion: str = "UL", 
        id_destino: str | None = None, 
        tiempo_animacion: float = 1.5, 
        tiempo_espera: float = 0.0,
        animacion: str = "TransformMatchingShapes"
    ) -> "AnimadorGrafico":
        """
        Muta un HUD existente hacia una nueva ecuación de forma limpia y paralela, 
        sin ciclos secuenciales de escritura.
        """
        id_dest = id_destino if id_destino else id_origen
        
        self.cola_animaciones.append({
            "tipo": "transformar_algebra_flotante",
            "id_origen": id_origen,
            "nuevo_texto": nuevo_texto,
            "posicion": posicion,
            "id_destino": id_dest,
            "t_anim": tiempo_animacion,
            "t_wait": tiempo_espera,
            "animacion": animacion
        })
        if hasattr(self, "objetos"):
            self.objetos[id_dest] = True
        self.tiempo_espera_actual = tiempo_espera
        
        return self

    mutar_algebra_flotante = transformar_algebra_flotante
    actualizar_algebra_flotante = transformar_algebra_flotante

    def animar_convergencia_parametrica(self, funcion, x_fijo, x_movil_ini, x_movil_fin, id_secante, id_punto_curva, id_punto_raiz, tiempo_animacion=2.0, tiempo_espera=1.0):
        self.cola_animaciones.append({
            "tipo": "convergencia_parametrica",
            "funcion": funcion,
            "x_fijo": x_fijo,
            "x_movil_ini": x_movil_ini,
            "x_movil_fin": x_movil_fin,
            "id_secante": id_secante,
            "id_punto_curva": id_punto_curva,
            "id_punto_raiz": id_punto_raiz,
            "t_anim": tiempo_animacion,
            "t_wait": tiempo_espera
        })
        return self

    def animar_integral(self, funcion, x_min: float, x_max: float, dx: float | None = None, color: str = "#00FFFF", opacidad: float = 0.5, id_area: str | None = None, tiempo_animacion: float = 1.0, tiempo_espera: float = 0.5):
        """Genera rectángulos de Riemann (si dx está definido) o un área sólida (si dx es None)."""
        self.cola_animaciones.append({
            "tipo": "integral",
            "funcion": funcion,
            "x_min": x_min,
            "x_max": x_max,
            "dx": dx,
            "color": color,
            "opacidad": opacidad,
            "id": id_area,
            "t_anim": tiempo_animacion,
            "t_wait": tiempo_espera
        })
        return self

    def transformar_objeto(
        self,
        origen=None,
        tipo_destino=None,
        funcion=None,
        x=None,
        y=None,
        texto=None,
        x_min=None,
        x_max=None,
        dx=None,
        opacidad=0.5,
        color=None,
        label=False,
        posicion="center",
        id_destino=None,
        animacion="ReplacementTransform",
        tiempo_animacion=1.5,
        tiempo_espera=1.0,
    ):
        """
        ReplacementTransform universal: transforma cualquier entidad (función, punto o label)
        hacia cualquier otra entidad (función, punto o label).
        
        Parámetros:
        - origen: ID del objeto existente (o None para el último objeto creado).
        - tipo_destino: "funcion", "punto", "label" (o "texto"). Si es None, se deduce automáticamente.
        - funcion: callable f(x) si el destino es una función.
        - x, y: coordenadas (float) si el destino es un punto.
        - texto: string o fórmula LaTeX si el destino es un label.
        - x_min, x_max: rango de graficación si el destino es una función.
        - color: color Manim (WHITE, GREEN, RED, hex string, etc.).
        - label: bool si el punto destino incluye etiqueta de coordenadas.
        - posicion: "center", "UL", "UR", "DL", "DR", "UP", o tupla (x, y) para posicionar labels.
        - id_destino: ID para registrar el objeto resultante. Si es None, hereda el ID de origen.
        - animacion: 'ReplacementTransform' (por defecto) o 'Transform'.
        - tiempo_animacion: duración en segundos.
        - tiempo_espera: pausa en segundos tras la transformación.
        """
        if tipo_destino is None:
            if funcion is not None:
                tipo_destino = "funcion"
            elif texto is not None:
                tipo_destino = "label"
            elif x is not None or y is not None:
                tipo_destino = "punto"
            else:
                tipo_destino = "label"

        self.cola_animaciones.append({
            "tipo": "transformar_objeto",
            "origen": origen,
            "tipo_destino": tipo_destino.lower(),
            "funcion": funcion,
            "x": x,
            "y": y,
            "texto": texto,
            "x_min": x_min,
            "x_max": x_max,
            "dx": dx,
            "opacidad": opacidad,
            "color": color,
            "label": label,
            "posicion": posicion,
            "id_destino": id_destino,
            "animacion": animacion,
            "t_anim": tiempo_animacion,
            "t_wait": tiempo_espera,
        })
        return self

    replacement_transform = transformar_objeto
    transformar = transformar_objeto
    transformacion_universal = transformar_objeto

    def iniciar_bloque_paralelo(self):
        """Abre un contexto de ejecución simultánea. Las acciones no se renderizan, se acumulan."""
        self.cola_animaciones.append({"tipo": "iniciar_paralelo"})
        return self

    def cerrar_bloque_paralelo(self, tiempo_animacion=1.5, tiempo_espera=1.0):
        """Cierra el contexto y detona TODAS las animaciones acumuladas al mismo tiempo."""
        self.cola_animaciones.append({
            "tipo": "cerrar_paralelo",
            "t_anim": tiempo_animacion,
            "t_wait": tiempo_espera
        })
        return self

    iniciar_paralelo = iniciar_bloque_paralelo
    cerrar_paralelo = cerrar_bloque_paralelo

    @contextmanager
    def bloque_paralelo(self, tiempo_animacion=1.5, tiempo_espera=1.0):
        """Context manager Pythonic para agrupar animaciones concurrentes con 'with escena.bloque_paralelo():'."""
        self.iniciar_bloque_paralelo()
        try:
            yield self
        finally:
            self.cerrar_bloque_paralelo(tiempo_animacion=tiempo_animacion, tiempo_espera=tiempo_espera)

    def render(self, previsualizar=True):
        f = self.funcion
        a, b = self.x_min, self.x_max
        acciones = self.cola_animaciones
        iniciar_con_texto = self.iniciar_con_texto
        dibujar_plano_inicial = self.dibujar_plano_inicial
        dibujar_grafica_inicial = self.dibujar_grafica_inicial
        funcion_es_dummy = self.funcion_es_dummy

        if os.environ.get("MANIM_STUDIO_HEADLESS") == "1":
            previsualizar = False

        calidad = os.environ.get("MANIM_QUALITY", "low_quality")
        
        with tempconfig({"quality": calidad, "preview": previsualizar}):
            
            class EscenaAutomatica(MovingCameraScene):
                def construct(self):
                    nonlocal f, funcion_es_dummy, a, b
                    # --- 1. NUEVO CÁLCULO ESTRICTO DE EXTREMOS Y PADDING ---
                    
                    # A. Muestreo ultra-denso inicial (10,000 puntos) para buscar picos escurridizos
                    x_vals = np.linspace(a, b, 10000)
                    y_vals = []
                    for x in x_vals:
                        try:
                            val = f(x)
                            if not isinstance(val, complex) and not math.isnan(val) and not math.isinf(val):
                                y_vals.append(val)
                        except: pass
                        
                    if not y_vals: y_vals = [-1, 1] # Fallback de seguridad
                    y_vals = np.array(y_vals)
                    
                    vmin_aprox, vmax_aprox = np.min(y_vals), np.max(y_vals)
                    x_min_aprox = x_vals[np.argmin(y_vals)]
                    x_max_aprox = x_vals[np.argmax(y_vals)]

                    # B. Refinamiento matemático exacto usando SciPy Optimize
                    try:
                        res_min = opt.minimize(f, x0=x_min_aprox, bounds=[(a, b)])
                        vmin = res_min.fun if res_min.success else vmin_aprox
                        
                        # Invertimos la función para hallar el máximo
                        res_max = opt.minimize(lambda x: -f(x), x0=x_max_aprox, bounds=[(a, b)])
                        vmax = -res_max.fun if res_max.success else vmax_aprox
                    except:
                        vmin, vmax = vmin_aprox, vmax_aprox

                    # C. Aplicación del "Padding" (10% extra) para que el grosor no muerda los bordes
                    dist_x_real = max(abs(b - a), 1)
                    dist_y_real = max(abs(vmax - vmin), 1)
                    
                    dist_x = dist_x_real * 1.10
                    dist_y = dist_y_real * 1.10

                    # El centro matemático siempre debe ser el real, independientemente del padding
                    c_x = a + (dist_x_real / 2)
                    c_y = vmin + (dist_y_real / 2)

                    ancho_camara = max(dist_x, dist_y * (16/9))
                    alto_camara = ancho_camara / (16/9)

                    x_vis_min = c_x - ancho_camara / 2
                    x_vis_max = c_x + ancho_camara / 2
                    y_vis_min = c_y - alto_camara / 2
                    y_vis_max = c_y + alto_camara / 2

                    # --- FIN DE LA ACTUALIZACIÓN DE CÁMARA ---

                    def calcular_paso(distancia):
                        paso_ideal = distancia / 12.0
                        magnitud = 10 ** math.floor(math.log10(paso_ideal))
                        fraccion = paso_ideal / magnitud
                        if fraccion < 1.5: multiplo = 1
                        elif fraccion < 3.5: multiplo = 2
                        elif fraccion < 7.5: multiplo = 5
                        else: multiplo = 10
                        return magnitud * multiplo

                    self.objetos_registrados = {}
                    self.objetos = self.objetos_registrados
                    self.ultimos_objetos = []
                    self.recolectando_paralelo = False

                    paso_unico = calcular_paso(max(ancho_camara, alto_camara))

                    plano = NumberPlane(
                        x_range=[x_vis_min, x_vis_max, paso_unico], 
                        y_range=[y_vis_min, y_vis_max, paso_unico],
                        x_length=ancho_camara, y_length=alto_camara,
                        background_line_style={"stroke_opacity": 0.4, "stroke_color": BLUE}
                    ).add_coordinates()

                    self.camera.frame.move_to(plano.c2p(c_x, c_y)).set_width(ancho_camara)
                    self.objetos_registrados["plano"] = plano

                    # --- INICIO CON LABEL O PLANO DIRECTO ---
                    if iniciar_con_texto:
                        txt_init = iniciar_con_texto.strip()
                        if txt_init.startswith("$$") and txt_init.endswith("$$"):
                            txt_init = txt_init[2:-2].strip()
                        label_inicial = MathTex(txt_init).set_z_index(20)
                        label_inicial.scale(ancho_camara / 10)
                        label_inicial.move_to(self.camera.frame.get_center())
                        self.objetos_registrados["label_inicial"] = label_inicial
                        self.ultimos_objetos.append(label_inicial)
                        
                        self.play(Write(label_inicial), run_time=1.5)
                        self.wait(1.0)
                        self.play(ReplacementTransform(label_inicial, plano), run_time=1.5)
                        if "label_inicial" in self.objetos_registrados:
                            del self.objetos_registrados["label_inicial"]
                        if label_inicial in self.ultimos_objetos:
                            self.ultimos_objetos.remove(label_inicial)
                        self.wait(0.5)
                    else:
                        if dibujar_plano_inicial:
                            self.play(Create(plano), run_time=1.5)

                    # --- DIBUJO DE FUNCIÓN PRINCIPAL SI ESTÁ HABILITADA ---
                    if dibujar_grafica_inicial and not funcion_es_dummy:
                        test_xs = np.linspace(x_vis_min, x_vis_max, 2000)
                        valid_xs = [tx for tx in test_xs if y_vis_min <= (f(tx) if not isinstance(f(tx), complex) else 0) <= y_vis_max]
                                
                        if valid_xs:
                            dx = (x_vis_max - x_vis_min) / 2000
                            x_graf_min = max(x_vis_min, valid_xs[0] - 5 * dx)
                            x_graf_max = min(x_vis_max, valid_xs[-1] + 5 * dx)
                        else:
                            x_graf_min, x_graf_max = a, b

                        grafica = plano.plot(f, x_range=[x_graf_min, x_graf_max], color=RED, stroke_opacity=0.8).set_z_index(1)
                        self.play(Create(grafica), run_time=1)
                        self.objetos_registrados["principal"] = grafica
                        self.objetos_registrados["grafica_principal"] = grafica
                        self.ultimos_objetos.append(grafica)

                    radio_punto = ancho_camara * 0.004
                    alto_texto = ancho_camara * 0.025
                    
                    # --- PIPELINE DE CONCURRENCIA Y EJECUCIÓN PARALELA ---
                    modo_paralelo = False
                    anims_paralelas = []
                    callbacks_paralelos = []

                    def despachar_animacion(anims, callback=None, t_anim=1.0, t_wait=1.0):
                        nonlocal anims_paralelas, callbacks_paralelos
                        if not isinstance(anims, (list, tuple)):
                            anims = [anims] if anims is not None else []
                        
                        if modo_paralelo:
                            anims_paralelas.extend(anims)
                            if callback:
                                callbacks_paralelos.append(callback)
                        else:
                            if anims:
                                self.play(*anims, run_time=t_anim)
                            if callback:
                                callback()
                            if t_wait > 0:
                                self.wait(t_wait)

                    # --- PROCESAMIENTO DE ACCIONES ---
                    for accion in acciones:
                        t_anim = accion.get("t_anim", 1.0)
                        t_wait = accion.get("t_wait", 1.0)

                        if accion["tipo"] == "iniciar_paralelo":
                            modo_paralelo = True
                            self.recolectando_paralelo = True
                            anims_paralelas = []
                            callbacks_paralelos = []
                            continue

                        elif accion["tipo"] == "cerrar_paralelo":
                            t_anim_paralelo = accion.get("t_anim", 1.5)
                            t_wait_paralelo = accion.get("t_wait", 1.0)

                            if anims_paralelas:
                                self.play(*anims_paralelas, run_time=t_anim_paralelo)

                            for cb in callbacks_paralelos:
                                try:
                                    cb()
                                except Exception as e:
                                    print(f"Advertencia en callback paralelo: {e}")

                            if t_wait_paralelo > 0:
                                self.wait(t_wait_paralelo)

                            modo_paralelo = False
                            self.recolectando_paralelo = False
                            anims_paralelas = []
                            callbacks_paralelos = []
                            continue

                        elif accion["tipo"] == "punto":
                            px, py = accion["x"], accion["y"]
                            punto = Dot(point=plano.c2p(px, py), color=accion["color"], radius=radio_punto).set_z_index(5)
                            obj_final = punto
                            anims_pto = []
                            if accion["label"]:
                                etiqueta = MathTex(rf"({px:.2f}, {py:.2f})")
                                etiqueta.next_to(punto, UP, buff=radio_punto * 1.5).set_height(alto_texto).set_z_index(5)
                                obj_final = VGroup(punto, etiqueta)
                                anims_pto = [FadeIn(punto), Write(etiqueta)]
                            else:
                                anims_pto = [FadeIn(punto)]

                            def post_punto(of=obj_final, oid=accion.get("id")):
                                if oid:
                                    self.objetos_registrados[oid] = of
                                self.ultimos_objetos.append(of)

                            despachar_animacion(anims_pto, post_punto, t_anim, t_wait)

                        elif accion["tipo"] == "funcion":
                            f_sec = accion["funcion"]
                            xmin_sec = accion["x_min"] if accion["x_min"] is not None else x_vis_min
                            xmax_sec = accion["x_max"] if accion["x_max"] is not None else x_vis_max

                            test_xs_sec = np.linspace(xmin_sec, xmax_sec, 2000)
                            valid_xs_sec = [tx for tx in test_xs_sec if y_vis_min <= (f_sec(tx) if not isinstance(f_sec(tx), complex) else 0) <= y_vis_max]

                            if valid_xs_sec:
                                dx_sec = (xmax_sec - xmin_sec) / 2000
                                xg_min = max(xmin_sec, valid_xs_sec[0] - 5 * dx_sec)
                                xg_max = min(xmax_sec, valid_xs_sec[-1] + 5 * dx_sec)
                            else:
                                xg_min, xg_max = xmin_sec, xmax_sec

                            grafica_sec = plano.plot(f_sec, x_range=[xg_min, xg_max], color=accion["color"], stroke_opacity=0.8).set_z_index(1)

                            def post_func(gs=grafica_sec, oid=accion.get("id")):
                                if oid:
                                    self.objetos_registrados[oid] = gs
                                self.ultimos_objetos.append(gs)

                            despachar_animacion([Create(grafica_sec)], post_func, t_anim, t_wait)

                        elif accion["tipo"] == "eliminar_objeto":
                            obj_id = accion.get("id")
                            anim_tipo = str(accion.get("animacion", "FadeOut")).lower()

                            mobjects_a_remover = []
                            if obj_id in ["todo", "todos", "all", "*"]:
                                mobjects_a_remover = [m for m in self.mobjects if m is not self.camera.frame]
                            elif obj_id is not None:
                                if obj_id in self.objetos_registrados:
                                    mobjects_a_remover = [self.objetos_registrados[obj_id]]
                                elif obj_id == "texto_central" and hasattr(self, "texto_central") and self.texto_central:
                                    mobjects_a_remover = [self.texto_central]
                                elif obj_id in ["grafica", "principal"] and "principal" in self.objetos_registrados:
                                    mobjects_a_remover = [self.objetos_registrados["principal"]]
                                elif obj_id == "plano" and "plano" in self.objetos_registrados:
                                    mobjects_a_remover = [self.objetos_registrados["plano"]]
                            elif self.ultimos_objetos:
                                mobjects_a_remover = [self.ultimos_objetos[-1]]
                            elif hasattr(self, "texto_central") and self.texto_central:
                                mobjects_a_remover = [self.texto_central]

                            anims_elim = []
                            for mob in mobjects_a_remover:
                                if anim_tipo == "uncreate":
                                    anims_elim.append(Uncreate(mob))
                                elif anim_tipo in ["shrink", "shrinktocenter"]:
                                    anims_elim.append(ShrinkToCenter(mob))
                                else:
                                    anims_elim.append(FadeOut(mob))

                            def post_eliminar(mobs=list(mobjects_a_remover), oid=obj_id):
                                for mob in mobs:
                                    self.remove(mob)
                                    if mob in self.ultimos_objetos:
                                        self.ultimos_objetos.remove(mob)
                                    claves = [k for k, v in self.objetos_registrados.items() if v == mob]
                                    for k in claves:
                                        del self.objetos_registrados[k]
                                    if hasattr(self, "elementos_graficos") and mob in self.elementos_graficos:
                                        self.elementos_graficos.remove(mob)
                                    if hasattr(self, "texto_central") and mob == self.texto_central:
                                        self.texto_central = None

                                if oid in ["todo", "todos", "all", "*"]:
                                    self.objetos_registrados.clear()
                                    self.ultimos_objetos.clear()
                                    if hasattr(self, "elementos_graficos"):
                                        self.elementos_graficos.clear()
                                    self.texto_central = None

                            despachar_animacion(anims_elim, post_eliminar, t_anim, t_wait)

                        elif accion["tipo"] == "integral":
                            temp_graph = plano.plot(accion["funcion"], x_range=[accion["x_min"], accion["x_max"]])
                            
                            if accion["dx"] is not None:
                                area = plano.get_riemann_rectangles(
                                    temp_graph, x_range=[accion["x_min"], accion["x_max"]], 
                                    dx=accion["dx"], color=accion["color"], fill_opacity=accion["opacidad"], stroke_width=1
                                )
                            else:
                                area = plano.get_area(
                                    temp_graph, x_range=[accion["x_min"], accion["x_max"]], 
                                    color=accion["color"], opacity=accion["opacidad"]
                                )
                                
                            area.set_z_index(1)  # Por debajo de las curvas principales
                            
                            if "id" in accion and accion["id"] and hasattr(self, "objetos"):
                                self.objetos[accion["id"]] = area
                            if hasattr(self, "ultimos_objetos"):
                                self.ultimos_objetos.append(area)
                                
                            # Si son rectángulos, los construimos de abajo hacia arriba
                            if accion.get("dx") is not None:
                                self.play(Create(area), run_time=t_anim)
                            # Si es un área sólida, la difuminamos suavemente para no trazar al revés
                            else:
                                self.play(FadeIn(area), run_time=t_anim)
                            self.wait(t_wait)

                        elif accion["tipo"] in ["fade_in_plano", "nuevo_plano"]:
                            f_nueva = accion.get("funcion")
                            if f_nueva is not None and callable(f_nueva):
                                f = f_nueva
                                funcion_es_dummy = False

                            a_new = accion.get("x_min")
                            b_new = accion.get("x_max")
                            if a_new is not None:
                                a = float(a_new)
                            if b_new is not None:
                                b = float(b_new)

                            y_min_req = accion.get("y_min")
                            y_max_req = accion.get("y_max")

                            # Determinar extremos verticales
                            if y_min_req is not None and y_max_req is not None:
                                vmin_new, vmax_new = float(y_min_req), float(y_max_req)
                            elif f is not None and callable(f) and not funcion_es_dummy:
                                x_vals_new = np.linspace(a, b, 2000)
                                y_vals_new = []
                                for xv in x_vals_new:
                                    try:
                                        val = f(xv)
                                        if not isinstance(val, complex) and not math.isnan(val) and not math.isinf(val):
                                            y_vals_new.append(val)
                                    except:
                                        pass
                                if not y_vals_new:
                                    y_vals_new = [-1, 1]
                                y_vals_new = np.array(y_vals_new)
                                vmin_aprox, vmax_aprox = float(np.min(y_vals_new)), float(np.max(y_vals_new))
                                x_min_aprox = x_vals_new[np.argmin(y_vals_new)]
                                x_max_aprox = x_vals_new[np.argmax(y_vals_new)]

                                try:
                                    res_min = opt.minimize(f, x0=x_min_aprox, bounds=[(a, b)])
                                    vmin_calc = res_min.fun if res_min.success else vmin_aprox
                                    res_max = opt.minimize(lambda x: -f(x), x0=x_max_aprox, bounds=[(a, b)])
                                    vmax_calc = -res_max.fun if res_max.success else vmax_aprox
                                except:
                                    vmin_calc, vmax_calc = vmin_aprox, vmax_aprox

                                vmin_new = float(y_min_req) if y_min_req is not None else float(vmin_calc)
                                vmax_new = float(y_max_req) if y_max_req is not None else float(vmax_calc)
                            else:
                                vmin_new = float(y_min_req) if y_min_req is not None else y_vis_min
                                vmax_new = float(y_max_req) if y_max_req is not None else y_vis_max

                            # Cálculo de encuadre y cámara con 10% de padding
                            dist_x_real = max(abs(b - a), 1.0)
                            dist_y_real = max(abs(vmax_new - vmin_new), 1.0)

                            dist_x = dist_x_real * 1.10
                            dist_y = dist_y_real * 1.10

                            c_x_new = a + (dist_x_real / 2.0)
                            c_y_new = vmin_new + (dist_y_real / 2.0)

                            ancho_camara = max(dist_x, dist_y * (16.0 / 9.0))
                            alto_camara = ancho_camara / (16.0 / 9.0)

                            x_vis_min = c_x_new - ancho_camara / 2.0
                            x_vis_max = c_x_new + ancho_camara / 2.0
                            y_vis_min = c_y_new - alto_camara / 2.0
                            y_vis_max = c_y_new + alto_camara / 2.0

                            radio_punto = ancho_camara * 0.004
                            alto_texto = ancho_camara * 0.025

                            paso_nuevo = calcular_paso(max(ancho_camara, alto_camara))

                            color_plano = accion.get("color", BLUE)
                            opac_plano = accion.get("stroke_opacity", 0.4)
                            incluir_coords = accion.get("incluir_coordenadas", True)

                            nuevo_plano = NumberPlane(
                                x_range=[x_vis_min, x_vis_max, paso_nuevo],
                                y_range=[y_vis_min, y_vis_max, paso_nuevo],
                                x_length=ancho_camara,
                                y_length=alto_camara,
                                background_line_style={"stroke_opacity": opac_plano, "stroke_color": color_plano}
                            )
                            if incluir_coords:
                                nuevo_plano.add_coordinates()

                            anims_fade_in = []

                            # Si se solicita desvanecer el plano anterior de forma explícita
                            if accion.get("desvanecer_anterior"):
                                plano_prev = self.objetos_registrados.get("plano")
                                if plano_prev and plano_prev in self.mobjects:
                                    anims_fade_in.append(FadeOut(plano_prev))

                            anim_tipo = str(accion.get("animacion", "FadeIn")).lower()
                            if anim_tipo == "create":
                                anims_fade_in.append(Create(nuevo_plano))
                            else:
                                anims_fade_in.append(FadeIn(nuevo_plano))

                            if accion.get("ajustar_camara", True):
                                p_cam_dest = nuevo_plano.c2p(c_x_new, c_y_new)
                                curr_cam_center = self.camera.frame.get_center()
                                curr_cam_width = self.camera.frame.get_width()
                                if np.linalg.norm(p_cam_dest - curr_cam_center) > 1e-3 or abs(curr_cam_width - ancho_camara) > 1e-3:
                                    anims_fade_in.append(self.camera.frame.animate.move_to(p_cam_dest).set_width(ancho_camara))

                            grafica_nueva = None
                            if accion.get("dibujar_grafica") and f is not None and callable(f) and not funcion_es_dummy:
                                test_xs_new = np.linspace(x_vis_min, x_vis_max, 2000)
                                valid_xs_new = [tx for tx in test_xs_new if y_vis_min <= (f(tx) if not isinstance(f(tx), complex) else 0) <= y_vis_max]
                                if valid_xs_new:
                                    dx_n = (x_vis_max - x_vis_min) / 2000
                                    xg_min = max(x_vis_min, valid_xs_new[0] - 5 * dx_n)
                                    xg_max = min(x_vis_max, valid_xs_new[-1] + 5 * dx_n)
                                else:
                                    xg_min, xg_max = a, b
                                grafica_nueva = nuevo_plano.plot(
                                    f, x_range=[xg_min, xg_max],
                                    color=accion.get("color_grafica", RED),
                                    stroke_opacity=0.8
                                ).set_z_index(1)
                                anims_fade_in.append(Create(grafica_nueva))

                            plano = nuevo_plano

                            def post_fade_in(np_obj=nuevo_plano, gn_obj=grafica_nueva, oid=accion.get("id", "plano")):
                                if oid:
                                    self.objetos_registrados[oid] = np_obj
                                self.objetos_registrados["plano"] = np_obj
                                self.ultimos_objetos.append(np_obj)
                                if gn_obj is not None:
                                    self.objetos_registrados["principal"] = gn_obj
                                    self.objetos_registrados["grafica_principal"] = gn_obj
                                    self.ultimos_objetos.append(gn_obj)

                            despachar_animacion(anims_fade_in, post_fade_in, t_anim, t_wait)

                        elif accion["tipo"] == "movimiento_punto":
                            f_anim = accion["funcion"]
                            x_ini, x_fin = accion["x_ini"], accion["x_fin"]
                            
                            # 1. Gestión de ID (Prevención de Memory Leak)
                            es_nuevo = True
                            if "id" in accion and hasattr(self, "objetos") and accion["id"] in self.objetos:
                                punto = self.objetos[accion["id"]]
                                es_nuevo = False
                            else:
                                punto = Dot(color=accion["color"], radius=radio_punto).set_z_index(5)
                                if "id" in accion and hasattr(self, "objetos"):
                                    self.objetos[accion["id"]] = punto
                                    if hasattr(self, "objetos_registrados"):
                                        self.objetos_registrados[accion["id"]] = punto

                            if punto in self.ultimos_objetos:
                                self.ultimos_objetos.remove(punto)
                            self.ultimos_objetos.append(punto)

                            # 2. Generación de Vector de Interpolación (Elimina ValueTracker)
                            rango_t = [x_ini, x_fin] if x_ini < x_fin else [x_fin, x_ini]
                            if abs(rango_t[1] - rango_t[0]) < 1e-6:
                                rango_t[1] = rango_t[0] + 1e-6
                            trayectoria = ParametricFunction(
                                lambda t: plano.c2p(t, f_anim(t)),
                                t_range=rango_t
                            )
                            # Inversión vectorial si el movimiento es hacia la izquierda
                            if x_ini > x_fin:
                                trayectoria.reverse_direction()

                            # 3. Ejecución Estándar / Concurrente
                            if es_nuevo:
                                if modo_paralelo:
                                    anims_paralelas.append(FadeIn(punto))
                                else:
                                    self.play(FadeIn(punto), run_time=0.5)
                                
                            despachar_animacion([MoveAlongPath(punto, trayectoria)], None, t_anim, t_wait)

                        elif accion["tipo"] == "convergencia_parametrica":
                            render_convergencia_secante(self, plano, accion)

                        elif accion["tipo"] == "movimiento_secante":
                            f_anim = accion["funcion"]
                            tracker1 = ValueTracker(accion["x1_ini"])
                            tracker2 = ValueTracker(accion["x2_ini"])

                            def crear_recta_extendida():
                                x1 = tracker1.get_value()
                                x2 = tracker2.get_value()
                                if abs(x2 - x1) < 1e-4:
                                    dx = 1e-5
                                    m = (f_anim(x1 + dx) - f_anim(x1 - dx)) / (2 * dx)
                                    y1_val = f_anim(x1)
                                else:
                                    m = (f_anim(x2) - f_anim(x1)) / (x2 - x1)
                                    y1_val = f_anim(x1)
                                y_left = m * (x_vis_min - x1) + y1_val
                                y_right = m * (x_vis_max - x1) + y1_val
                                return Line(plano.c2p(x_vis_min, y_left), plano.c2p(x_vis_max, y_right), color=accion["color"]).set_z_index(3)

                            secante = always_redraw(crear_recta_extendida)
                            punto1 = always_redraw(lambda: Dot(point=plano.c2p(tracker1.get_value(), f_anim(tracker1.get_value())), color=accion["color"], radius=radio_punto).set_z_index(5))
                            punto2 = always_redraw(lambda: Dot(point=plano.c2p(tracker2.get_value(), f_anim(tracker2.get_value())), color=accion["color"], radius=radio_punto).set_z_index(5))

                            self.play(FadeIn(punto1), FadeIn(punto2), Create(secante), run_time=0.5)
                            self.play(tracker1.animate.set_value(accion["x1_fin"]), tracker2.animate.set_value(accion["x2_fin"]), run_time=t_anim)
                            secante.clear_updaters()
                            punto1.clear_updaters()
                            punto2.clear_updaters()

                            grp_sec = VGroup(secante, punto1, punto2)
                            obj_id = accion.get("id")
                            if obj_id:
                                self.objetos_registrados[obj_id] = grp_sec
                            self.ultimos_objetos.append(grp_sec)
                            self.wait(t_wait)

                        elif accion["tipo"] == "a_texto":
                            self.elementos_graficos = [m for m in self.mobjects if isinstance(m, VMobject) and m is not self.camera.frame]
                            self.grupo_graficos = VGroup(*self.elementos_graficos)

                            txt_a_texto = accion["texto"].strip()
                            if txt_a_texto.startswith("$$") and txt_a_texto.endswith("$$"):
                                txt_a_texto = txt_a_texto[2:-2].strip()
                            self.texto_central = MathTex(txt_a_texto).set_z_index(20)
                            self.texto_central.scale(ancho_camara / 10) 
                            self.texto_central.move_to(self.camera.frame.get_center())

                            grupo_copia = self.grupo_graficos.copy()
                            self.remove(*self.elementos_graficos)
                            self.add(grupo_copia)

                            def post_texto(tc=self.texto_central, oid=accion.get("id")):
                                if oid:
                                    self.objetos_registrados[oid] = tc
                                self.objetos_registrados["texto_central"] = tc
                                self.ultimos_objetos.append(tc)

                            despachar_animacion([ReplacementTransform(grupo_copia, self.texto_central)], post_texto, t_anim, t_wait)

                        elif accion["tipo"] == "a_plano":
                            if hasattr(self, "texto_central") and self.texto_central and hasattr(self, "grupo_graficos"):
                                grupo_copia = self.grupo_graficos.copy()

                                def post_plano(gc=grupo_copia, tc=self.texto_central, eg=list(self.elementos_graficos)):
                                    self.remove(gc)
                                    self.add(*eg)
                                    if tc in self.ultimos_objetos:
                                        self.ultimos_objetos.remove(tc)
                                    if "texto_central" in self.objetos_registrados:
                                        del self.objetos_registrados["texto_central"]
                                    self.texto_central = None

                                despachar_animacion([ReplacementTransform(self.texto_central, grupo_copia)], post_plano, t_anim, t_wait)
                            else:
                                if not modo_paralelo and t_wait > 0:
                                    self.wait(t_wait)

                        elif accion["tipo"] == "algebra":
                            if not hasattr(self, "elementos_graficos") or not self.elementos_graficos:
                                self.elementos_graficos = [m for m in self.mobjects if isinstance(m, VMobject) and m is not self.camera.frame]
                                self.play(*[FadeOut(m) for m in self.elementos_graficos], run_time=0.5)

                            procesar_pasos_algebraicos(
                                escena=self, fuente=accion["fuente"], 
                                ancho_camara=ancho_camara, runtime=t_anim, waittime=t_wait,
                                tiempo_transformacion=accion.get("t_trans"),
                                tiempo_espera=accion.get("t_wait_step"),
                                tiempos_transformacion=accion.get("ts_trans"),
                                tiempos_espera=accion.get("ts_wait"),
                                tiempo_escritura=accion.get("t_write")
                            )

                            if self.elementos_graficos:
                                self.play(*[FadeIn(m) for m in self.elementos_graficos], run_time=0.5)
                                self.elementos_graficos = []

                        elif accion["tipo"] == "algebra_flotante":
                            label_flotante = procesar_algebra_flotante(
                                escena=self, fuente=accion["fuente"],
                                ancho_camara=ancho_camara, posicion=accion["posicion"],
                                remover=accion["remover"], runtime=t_anim, waittime=t_wait,
                                tiempo_transformacion=accion.get("t_trans"),
                                tiempo_espera=accion.get("t_wait_step"),
                                tiempos_transformacion=accion.get("ts_trans"),
                                tiempos_espera=accion.get("ts_wait"),
                                tiempo_escritura=accion.get("t_write")
                            )
                            obj_id = accion.get("id")
                            if obj_id and label_flotante:
                                self.objetos_registrados[obj_id] = label_flotante
                            if label_flotante:
                                self.ultimos_objetos.append(label_flotante)

                        elif accion["tipo"] == "transformar_algebra_flotante":
                            id_origen = accion["id_origen"]
                            id_dest = accion.get("id_destino") or id_origen
                            nuevo_texto = accion["nuevo_texto"]
                            posicion = accion.get("posicion", "UL")
                            anim_tipo = accion.get("animacion", "TransformMatchingShapes")

                            # 1. Recuperamos el mobject origen existente en la escena
                            if id_origen not in self.objetos_registrados:
                                raise ValueError(f"El HUD origen '{id_origen}' no existe en la escena.")
                            mob_origen = self.objetos_registrados[id_origen]

                            # 2. Compilar nuevo_texto respetando colores LaTeX y múltiples líneas
                            latex_codes = _obtener_codigos_latex(nuevo_texto)
                            sub_mobs = []
                            for code in latex_codes:
                                fragmentos = extraer_texto_colores(code)
                                textos_limpios = [frag[0] for frag in fragmentos]
                                m_tex = MathTex(*textos_limpios).set_z_index(30)
                                for i, frag in enumerate(fragmentos):
                                    if frag[1].lower() != "white":
                                        m_tex[i].set_color(frag[1])
                                sub_mobs.append(m_tex)

                            if len(sub_mobs) == 1:
                                mob_destino = sub_mobs[0]
                            elif len(sub_mobs) > 1:
                                mob_destino = VGroup(*sub_mobs).arrange(DOWN, aligned_edge=LEFT, buff=0.15).set_z_index(30)
                            else:
                                texto_limpio = nuevo_texto.replace("$$", "").strip()
                                mob_destino = MathTex(texto_limpio).set_z_index(30)

                            # 3. Alineación y escalado acoplado al frame de la cámara
                            pos_map = {"UL": UL, "UR": UR, "DL": DL, "DR": DR}
                            vector_pos = pos_map.get(str(posicion).upper(), UL)

                            max_width = ancho_camara * 0.25
                            if mob_destino.width > max_width:
                                mob_destino.scale_to_fit_width(max_width)
                            else:
                                mob_destino.scale(ancho_camara / 20)

                            buff_x = ancho_camara * 0.03
                            buff_y = ancho_camara * 0.03 * (9 / 16)
                            offset = -vector_pos[0] * RIGHT * buff_x + -vector_pos[1] * UP * buff_y

                            esquina_camara = self.camera.frame.get_corner(vector_pos)
                            mob_destino.move_to(esquina_camara + offset, aligned_edge=vector_pos)

                            # 4. Generación estricta de la transformación sin Writes previos
                            if str(anim_tipo).lower() == "replacementtransform":
                                animacion = ReplacementTransform(mob_origen, mob_destino)
                            else:
                                animacion = TransformMatchingShapes(mob_origen, mob_destino)

                            # 5. Encolado y actualización en el pipeline del motor
                            def post_mutar(mo=mob_origen, md=mob_destino, id_d=id_dest, id_o=id_origen):
                                if mo in self.ultimos_objetos:
                                    self.ultimos_objetos.remove(mo)
                                self.ultimos_objetos.append(md)
                                self.objetos_registrados[id_d] = md
                                if hasattr(self, "objetos"):
                                    self.objetos[id_d] = md
                                if id_d != id_o and id_o in self.objetos_registrados:
                                    del self.objetos_registrados[id_o]
                                    if hasattr(self, "objetos") and id_o in self.objetos:
                                        del self.objetos[id_o]

                            despachar_animacion([animacion], post_mutar, t_anim, t_wait)

                        elif accion["tipo"] == "linea_punteada":
                            if modo_paralelo:
                                x1_f, x2_f = accion["x1_fin"], accion["x2_fin"]
                                if callable(accion["y1_ini"]): y1_f = accion["y1_ini"](x1_f)
                                else: y1_f = accion["y1_fin"]
                                if callable(accion["y2_ini"]): y2_f = accion["y2_ini"](x2_f)
                                else: y2_f = accion["y2_fin"]

                                p1 = plano.c2p(x1_f, y1_f)
                                p2 = plano.c2p(x2_f, y2_f)
                                if np.linalg.norm(p2 - p1) < 1e-4:
                                    p2 = p1 + np.array([1e-4, 0, 0])
                                linea_est = DashedLine(p1, p2, color=accion["color"]).set_z_index(2)
                                def post_linea(lin=linea_est, oid=accion.get("id")):
                                    if oid: self.objetos_registrados[oid] = lin
                                    self.ultimos_objetos.append(lin)
                                despachar_animacion([Create(linea_est)], post_linea, t_anim, t_wait)
                            else:
                                t_alpha = ValueTracker(0.0)

                                def crear_linea():
                                    a = t_alpha.get_value()
                                    x1 = accion["x1_ini"] * (1 - a) + accion["x1_fin"] * a
                                    x2 = accion["x2_ini"] * (1 - a) + accion["x2_fin"] * a
                                    if callable(accion["y1_ini"]): y1 = accion["y1_ini"](x1)
                                    else: y1 = accion["y1_ini"] * (1 - a) + accion["y1_fin"] * a
                                    if callable(accion["y2_ini"]): y2 = accion["y2_ini"](x2)
                                    else: y2 = accion["y2_ini"] * (1 - a) + accion["y2_fin"] * a

                                    p1 = plano.c2p(x1, y1)
                                    p2 = plano.c2p(x2, y2)
                                    if np.linalg.norm(p2 - p1) < 1e-4:
                                        p2 = p1 + np.array([1e-4, 0, 0])

                                    return DashedLine(p1, p2, color=accion["color"]).set_z_index(2)

                                linea = always_redraw(crear_linea)
                                self.play(Create(linea), run_time=0.5)
                                self.play(t_alpha.animate.set_value(1.0), run_time=t_anim)
                                linea.clear_updaters()

                                obj_id = accion.get("id")
                                if obj_id:
                                    self.objetos_registrados[obj_id] = linea
                                self.ultimos_objetos.append(linea)
                                self.wait(t_wait)

                        elif accion["tipo"] == "llave":
                            if modo_paralelo:
                                x1_f, x2_f = accion["x1_fin"], accion["x2_fin"]
                                if callable(accion["y1_ini"]): y1_f = accion["y1_ini"](x1_f)
                                else: y1_f = accion["y1_fin"]
                                if callable(accion["y2_ini"]): y2_f = accion["y2_ini"](x2_f)
                                else: y2_f = accion["y2_fin"]
                                p1 = plano.c2p(x1_f, y1_f)
                                p2 = plano.c2p(x2_f, y2_f)
                                if np.linalg.norm(p2 - p1) < 1e-4:
                                    p2 = p1 + np.array([1e-4, 0, 0])
                                if accion["direccion"] is not None:
                                    llave_est = BraceBetweenPoints(p1, p2, direction=accion["direccion"], color=accion["color"]).set_z_index(4)
                                else:
                                    llave_est = BraceBetweenPoints(p1, p2, color=accion["color"]).set_z_index(4)

                                texto_str = accion["texto"]
                                if texto_str:
                                    etiqueta_est = MathTex(texto_str).set_color(accion["color"]).scale(ancho_camara / 20).next_to(llave_est, llave_est.get_direction(), buff=ancho_camara*0.01).set_z_index(4)
                                    obj_final = VGroup(llave_est, etiqueta_est)
                                    anims_llave = [FadeIn(llave_est), FadeIn(etiqueta_est)]
                                else:
                                    obj_final = llave_est
                                    anims_llave = [FadeIn(llave_est)]

                                def post_llave(of=obj_final, oid=accion.get("id")):
                                    if oid: self.objetos_registrados[oid] = of
                                    self.ultimos_objetos.append(of)
                                despachar_animacion(anims_llave, post_llave, t_anim, t_wait)
                            else:
                                t_alpha = ValueTracker(0.0)

                                def get_p1():
                                    a = t_alpha.get_value()
                                    x1 = accion["x1_ini"] * (1 - a) + accion["x1_fin"] * a
                                    if callable(accion["y1_ini"]): y1 = accion["y1_ini"](x1)
                                    else: y1 = accion["y1_ini"] * (1 - a) + accion["y1_fin"] * a
                                    return plano.c2p(x1, y1)

                                def get_p2():
                                    a = t_alpha.get_value()
                                    x2 = accion["x2_ini"] * (1 - a) + accion["x2_fin"] * a
                                    if callable(accion["y2_ini"]): y2 = accion["y2_ini"](x2)
                                    else: y2 = accion["y2_ini"] * (1 - a) + accion["y2_fin"] * a
                                    return plano.c2p(x2, y2)

                                def crear_llave():
                                    p1 = get_p1()
                                    p2 = get_p2()
                                    if np.linalg.norm(p2 - p1) < 1e-4:
                                        p2 = p1 + np.array([1e-4, 0, 0])

                                    if accion["direccion"] is not None:
                                        return BraceBetweenPoints(p1, p2, direction=accion["direccion"], color=accion["color"]).set_z_index(4)
                                    else:
                                        return BraceBetweenPoints(p1, p2, color=accion["color"]).set_z_index(4)

                                llave = always_redraw(crear_llave)

                                texto_str = accion["texto"]
                                if texto_str:
                                    etiqueta = always_redraw(lambda: MathTex(texto_str).set_color(accion["color"]).scale(ancho_camara / 20).next_to(llave, llave.get_direction(), buff=ancho_camara*0.01).set_z_index(4))
                                else:
                                    etiqueta = None

                                if etiqueta:
                                    self.play(FadeIn(llave), FadeIn(etiqueta), run_time=0.5)
                                else:
                                    self.play(FadeIn(llave), run_time=0.5)

                                self.play(t_alpha.animate.set_value(1.0), run_time=t_anim)

                                llave.clear_updaters()
                                if etiqueta:
                                    etiqueta.clear_updaters()
                                obj_final = VGroup(llave, etiqueta) if etiqueta else llave
                                obj_id = accion.get("id")
                                if obj_id:
                                    self.objetos_registrados[obj_id] = obj_final
                                self.ultimos_objetos.append(obj_final)
                                self.wait(t_wait)

                        elif accion["tipo"] == "transformar_objeto":
                            origen_id = accion.get("origen")
                            origen_mob = None

                            if origen_id is not None:
                                if origen_id in self.objetos_registrados:
                                    origen_mob = self.objetos_registrados[origen_id]
                                elif origen_id == "plano" and "plano" in self.objetos_registrados:
                                    origen_mob = self.objetos_registrados["plano"]
                                elif origen_id in ["grafica", "principal", "grafica_principal"] and "principal" in self.objetos_registrados:
                                    origen_mob = self.objetos_registrados["principal"]
                                elif origen_id == "texto_central" and hasattr(self, "texto_central") and self.texto_central:
                                    origen_mob = self.texto_central

                            if origen_mob is None:
                                if self.ultimos_objetos:
                                    origen_mob = self.ultimos_objetos[-1]
                                elif hasattr(self, "texto_central") and self.texto_central:
                                    origen_mob = self.texto_central
                                elif "principal" in self.objetos_registrados:
                                    origen_mob = self.objetos_registrados["principal"]
                                elif hasattr(self, "plano"):
                                    origen_mob = self.plano

                            if origen_mob is not None:
                                tipo_dest = str(accion.get("tipo_destino", "label")).lower()
                                color_dest = accion.get("color")

                                if tipo_dest in ["funcion", "curva", "grafica"]:
                                    f_dest = accion.get("funcion")
                                    if f_dest is None:
                                        f_dest = lambda x: 0.0

                                    xmin_sec = accion.get("x_min") if accion.get("x_min") is not None else x_vis_min
                                    xmax_sec = accion.get("x_max") if accion.get("x_max") is not None else x_vis_max

                                    test_xs_sec = np.linspace(xmin_sec, xmax_sec, 2000)
                                    valid_xs_sec = [tx for tx in test_xs_sec if y_vis_min <= (f_dest(tx) if not isinstance(f_dest(tx), complex) else 0) <= y_vis_max]
                                    if valid_xs_sec:
                                        dx_sec = (xmax_sec - xmin_sec) / 2000
                                        xg_min = max(xmin_sec, valid_xs_sec[0] - 5 * dx_sec)
                                        xg_max = min(xmax_sec, valid_xs_sec[-1] + 5 * dx_sec)
                                    else:
                                        xg_min, xg_max = xmin_sec, xmax_sec

                                    c_line = color_dest if color_dest is not None else GREEN
                                    destino_mob = plano.plot(f_dest, x_range=[xg_min, xg_max], color=c_line, stroke_opacity=0.85).set_z_index(2)

                                elif tipo_dest in ["integral", "area", "riemann"]:
                                    temp_graph = plano.plot(accion["funcion"], x_range=[accion["x_min"], accion["x_max"]])
                                    c_area = color_dest if color_dest is not None else accion.get("color", "#00FFFF")
                                    opac = accion.get("opacidad", 0.5)
                                    if accion.get("dx") is not None:
                                        destino = plano.get_riemann_rectangles(
                                            temp_graph, x_range=[accion["x_min"], accion["x_max"]], 
                                            dx=accion["dx"], color=c_area, fill_opacity=opac, stroke_width=1
                                        )
                                    else:
                                        destino = plano.get_area(
                                            temp_graph, x_range=[accion["x_min"], accion["x_max"]], 
                                            color=c_area, opacity=opac
                                        )
                                    destino.set_z_index(1)
                                    destino_mob = destino

                                elif tipo_dest in ["punto", "dot"]:
                                    px = accion.get("x")
                                    py = accion.get("y")
                                    if px is None: px = 0.0
                                    if py is None:
                                        f_ref = accion.get("funcion")
                                        if callable(f_ref):
                                            py = f_ref(px)
                                        elif callable(f):
                                            py = f(px)
                                        else:
                                            py = 0.0
                                    c_dot = color_dest if color_dest is not None else WHITE
                                    punto_dest = Dot(point=plano.c2p(px, py), color=c_dot, radius=radio_punto).set_z_index(5)
                                    if accion.get("label"):
                                        etiqueta_dest = MathTex(rf"({px:.2f}, {py:.2f})")
                                        etiqueta_dest.next_to(punto_dest, UP, buff=radio_punto * 1.5).set_height(alto_texto).set_z_index(5)
                                        destino_mob = VGroup(punto_dest, etiqueta_dest)
                                    else:
                                        destino_mob = punto_dest

                                else: # "label", "texto", "formula"
                                    txt_val = str(accion.get("texto", "")).strip()
                                    if txt_val.startswith("$$") and txt_val.endswith("$$"):
                                        txt_val = txt_val[2:-2].strip()

                                    try:
                                        destino_mob = MathTex(txt_val).set_z_index(20)
                                    except Exception:
                                        destino_mob = Text(txt_val).set_z_index(20)

                                    if color_dest is not None:
                                        destino_mob.set_color(color_dest)

                                    pos = accion.get("posicion", "center")
                                    if isinstance(pos, str):
                                        pos_upper = pos.upper()
                                        if pos_upper in ["CENTER", "CENTRO"]:
                                            destino_mob.scale(ancho_camara / 10)
                                            destino_mob.move_to(self.camera.frame.get_center())
                                        elif pos_upper == "UL":
                                            destino_mob.scale(ancho_camara / 14)
                                            destino_mob.to_corner(UL, buff=0.5)
                                        elif pos_upper == "UR":
                                            destino_mob.scale(ancho_camara / 14)
                                            destino_mob.to_corner(UR, buff=0.5)
                                        elif pos_upper == "DL":
                                            destino_mob.scale(ancho_camara / 14)
                                            destino_mob.to_corner(DL, buff=0.5)
                                        elif pos_upper == "DR":
                                            destino_mob.scale(ancho_camara / 14)
                                            destino_mob.to_corner(DR, buff=0.5)
                                        elif pos_upper == "UP":
                                            destino_mob.scale(ancho_camara / 12)
                                            destino_mob.to_edge(UP, buff=0.5)
                                        else:
                                            destino_mob.scale(ancho_camara / 10)
                                            destino_mob.move_to(self.camera.frame.get_center())
                                    elif isinstance(pos, (tuple, list)) and len(pos) >= 2:
                                        destino_mob.scale(ancho_camara / 14)
                                        destino_mob.move_to(plano.c2p(pos[0], pos[1]))

                                anim_name = str(accion.get("animacion", "ReplacementTransform")).lower()
                                if anim_name == "transform":
                                    anim_trans = Transform(origen_mob, destino_mob)
                                    obj_activo = origen_mob
                                else:
                                    anim_trans = ReplacementTransform(origen_mob, destino_mob)
                                    obj_activo = destino_mob

                                def post_trans(omob=origen_mob, destmob=obj_activo, oid=origen_id, id_d=accion.get("id_destino"), tdest=tipo_dest, pos_act=accion.get("posicion", "")):
                                    if omob in self.ultimos_objetos:
                                        self.ultimos_objetos.remove(omob)
                                    self.ultimos_objetos.append(destmob)

                                    if id_d:
                                        self.objetos_registrados[id_d] = destmob
                                    elif oid:
                                        self.objetos_registrados[oid] = destmob

                                    claves_antiguas = [k for k, v in self.objetos_registrados.items() if v == omob and k != id_d and k != oid]
                                    for k in claves_antiguas:
                                        del self.objetos_registrados[k]

                                    if hasattr(self, "texto_central"):
                                        if omob == self.texto_central:
                                            self.texto_central = None
                                        if tdest in ["label", "texto"] and str(pos_act).upper() in ["CENTER", "CENTRO"]:
                                            self.texto_central = destmob

                                despachar_animacion([anim_trans], post_trans, t_anim, t_wait)

                    # Salvaguarda: si quedó un bloque paralelo sin cerrar, detonarlo
                    if anims_paralelas:
                        self.play(*anims_paralelas, run_time=1.5)
                        for cb in callbacks_paralelos:
                            try:
                                cb()
                            except Exception:
                                pass
                        modo_paralelo = False
                        anims_paralelas = []
                        callbacks_paralelos = []

                    self.wait(2)
            
            EscenaAutomatica().render()