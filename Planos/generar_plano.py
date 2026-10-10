from manim import *
import numpy as np
import math
import scipy.optimize as opt  # <--- NUEVA IMPORTACIÓN PARA PRECISIÓN MATEMÁTICA
from Algebra.algebra import procesar_pasos_algebraicos, procesar_algebra_flotante

class AnimadorGrafico:
    def __init__(self, funcion, x_min, x_max):
        self.funcion = funcion
        self.x_min = x_min
        self.x_max = x_max
        self.cola_animaciones = []

    def agregar_punto(self, x, y, color=WHITE, label=False, tiempo_animacion=1.0, tiempo_espera=1.0):
        self.cola_animaciones.append({
            "tipo": "punto", "x": x, "y": y, "color": color, "label": label,
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera
        })
        return self 

    def agregar_funcion(self, funcion, x_min=None, x_max=None, color=GREEN, tiempo_animacion=1.0, tiempo_espera=1.0):
        self.cola_animaciones.append({
            "tipo": "funcion", "funcion": funcion, "x_min": x_min, "x_max": x_max, "color": color,
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera
        })
        return self

    def animar_punto_sobre_curva(self, x_inicio, x_fin, funcion=None, color=YELLOW, tiempo_animacion=1.0, tiempo_espera=1.0):
        self.cola_animaciones.append({
            "tipo": "movimiento_punto", "x_ini": x_inicio, "x_fin": x_fin,
            "funcion": funcion if funcion else self.funcion, "color": color, 
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera
        })
        return self

    def animar_secante(self, x1_ini, x1_fin, x2_ini, x2_fin, funcion=None, color=YELLOW, tiempo_animacion=1.0, tiempo_espera=1.0):
        self.cola_animaciones.append({
            "tipo": "movimiento_secante",
            "x1_ini": x1_ini, "x1_fin": x1_fin,
            "x2_ini": x2_ini, "x2_fin": x2_fin,
            "funcion": funcion if funcion else self.funcion,
            "color": color, 
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera
        })
        return self

    def transformar_a_texto(self, texto_latex, tiempo_animacion=1.5, tiempo_espera=1.0):
        self.cola_animaciones.append({
            "tipo": "a_texto", "texto": texto_latex,
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera
        })
        return self

    def transformar_a_plano(self, tiempo_animacion=1.5, tiempo_espera=1.0):
        self.cola_animaciones.append({
            "tipo": "a_plano",
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera
        })
        return self

    def insertar_algebra(self, fuente_o_texto, tiempo_animacion=1.0, tiempo_espera=1.0):
        self.cola_animaciones.append({
            "tipo": "algebra", "fuente": fuente_o_texto,
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera
        })
        return self

    def animar_linea_punteada(self, x1_ini, x1_fin, x2_ini, x2_fin, y1_ini, y2_ini, y1_fin=None, y2_fin=None, color=WHITE, tiempo_animacion=1.0, tiempo_espera=1.0):
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
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera
        })
        return self

    def animar_llave(self, x1_ini, x1_fin, x2_ini, x2_fin, y1_ini, y2_ini, y1_fin=None, y2_fin=None, texto="", direccion=None, color=WHITE, tiempo_animacion=1.0, tiempo_espera=1.0):
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
            "t_anim": tiempo_animacion, "t_wait": tiempo_espera
        })
        return self

    def agregar_algebra_flotante(self, fuente_o_texto, posicion="UL", remover_al_final=False, tiempo_animacion=1.0, tiempo_espera=1.0):
        self.cola_animaciones.append({
            "tipo": "algebra_flotante", "fuente": fuente_o_texto, "posicion": posicion,
            "remover": remover_al_final, "t_anim": tiempo_animacion, "t_wait": tiempo_espera
        })
        return self

    def render(self, previsualizar=True):
        f = self.funcion
        a, b = self.x_min, self.x_max
        acciones = self.cola_animaciones

        calidad = "low_quality" if previsualizar else "high_quality"
        
        with tempconfig({"quality": calidad, "preview": previsualizar}):
            
            class EscenaAutomatica(MovingCameraScene):
                def construct(self):
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

                    paso_unico = calcular_paso(max(ancho_camara, alto_camara))

                    plano = NumberPlane(
                        x_range=[x_vis_min, x_vis_max, paso_unico], 
                        y_range=[y_vis_min, y_vis_max, paso_unico],
                        x_length=ancho_camara, y_length=alto_camara,
                        background_line_style={"stroke_opacity": 0.4, "stroke_color": BLUE}
                    ).add_coordinates()

                    self.camera.frame.move_to(plano.c2p(c_x, c_y)).set_width(ancho_camara)

                    # --- DIBUJO DE FUNCIÓN PRINCIPAL CON OVERSCAN ---
                    test_xs = np.linspace(x_vis_min, x_vis_max, 2000)
                    valid_xs = [tx for tx in test_xs if y_vis_min <= (f(tx) if not isinstance(f(tx), complex) else 0) <= y_vis_max]
                            
                    if valid_xs:
                        # dx es el tamaño de un "pasito" en nuestra muestra
                        dx = (x_vis_max - x_vis_min) / 2000
                        # Sumamos 5 pasitos hacia afuera para cruzar el borde y que la cámara recorte limpio
                        x_graf_min = max(x_vis_min, valid_xs[0] - 5 * dx)
                        x_graf_max = min(x_vis_max, valid_xs[-1] + 5 * dx)
                    else:
                        x_graf_min, x_graf_max = a, b

                    grafica = plano.plot(f, x_range=[x_graf_min, x_graf_max], color=RED, stroke_opacity=0.8).set_z_index(1)
                    
                    self.play(Create(plano), run_time=1.5)
                    self.play(Create(grafica), run_time=1)

                    radio_punto = ancho_camara * 0.004
                    alto_texto = ancho_camara * 0.025
                    
                    # --- PROCESAMIENTO DE ACCIONES ---
                    for accion in acciones:
                        t_anim = accion.get("t_anim", 1.0)
                        t_wait = accion.get("t_wait", 1.0)

                        if accion["tipo"] == "punto":
                            px, py = accion["x"], accion["y"]
                            punto = Dot(point=plano.c2p(px, py), color=accion["color"], radius=radio_punto).set_z_index(5)
                            if accion["label"]:
                                etiqueta = MathTex(rf"({px:.2f}, {py:.2f})")
                                etiqueta.next_to(punto, UP, buff=radio_punto * 1.5).set_height(alto_texto).set_z_index(5)
                                self.play(FadeIn(punto), Write(etiqueta), run_time=t_anim)
                            else:
                                self.play(FadeIn(punto), run_time=t_anim)
                            self.wait(t_wait)
                                
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
                            self.play(Create(grafica_sec), run_time=t_anim)
                            self.wait(t_wait)

                        elif accion["tipo"] == "movimiento_punto":
                            f_anim = accion["funcion"]
                            tracker = ValueTracker(accion["x_ini"])
                            punto = Dot(color=accion["color"], radius=radio_punto).set_z_index(5)
                            punto.add_updater(lambda m: m.move_to(plano.c2p(tracker.get_value(), f_anim(tracker.get_value()))))
                            
                            self.play(FadeIn(punto), run_time=0.5)
                            self.play(tracker.animate.set_value(accion["x_fin"]), run_time=t_anim)
                            punto.clear_updaters()
                            self.wait(t_wait)

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
                            self.wait(t_wait)

                        elif accion["tipo"] == "a_texto":
                            self.elementos_graficos = [m for m in self.mobjects if isinstance(m, VMobject) and m is not self.camera.frame]
                            self.grupo_graficos = VGroup(*self.elementos_graficos)
                            
                            self.texto_central = MathTex(accion["texto"]).set_z_index(20)
                            self.texto_central.scale(ancho_camara / 10) 
                            self.texto_central.move_to(self.camera.frame.get_center())
                            
                            # --- MAGIA: TÉCNICA DE LA COPIA SACRIFICABLE ---
                            grupo_copia = self.grupo_graficos.copy()
                            
                            self.remove(*self.elementos_graficos) # Escondemos la matemática real intacta
                            self.add(grupo_copia) # Ponemos el doble de riesgo en escena
                            
                            self.play(ReplacementTransform(grupo_copia, self.texto_central), run_time=t_anim)
                            self.wait(t_wait)

                        elif accion["tipo"] == "a_plano":
                            if hasattr(self, "texto_central") and hasattr(self, "grupo_graficos"):
                                # Hacemos una copia sacrificable de cómo debe verse el final
                                grupo_copia = self.grupo_graficos.copy()
                                
                                self.play(ReplacementTransform(self.texto_central, grupo_copia), run_time=t_anim)
                                
                                # El texto ya es historia. Ahora quitamos la copia...
                                self.remove(grupo_copia)
                                # ... y devolvemos los objetos reales con sus coordenadas perfectas
                                self.add(*self.elementos_graficos)
                                
                                self.texto_central = None
                            self.wait(t_wait)
                                
                        elif accion["tipo"] == "algebra":
                            if not hasattr(self, "elementos_graficos") or not self.elementos_graficos:
                                # CORRECCIÓN: Filtro VMobject aplicado también aquí para el FadeOut
                                self.elementos_graficos = [m for m in self.mobjects if isinstance(m, VMobject) and m is not self.camera.frame]
                                self.play(*[FadeOut(m) for m in self.elementos_graficos], run_time=0.5)
                            
                            procesar_pasos_algebraicos(
                                escena=self, fuente=accion["fuente"], 
                                ancho_camara=ancho_camara, runtime=t_anim, waittime=t_wait
                            )
                            
                            if self.elementos_graficos:
                                self.play(*[FadeIn(m) for m in self.elementos_graficos], run_time=0.5)
                                self.elementos_graficos = []

                        elif accion["tipo"] == "algebra_flotante":
                            procesar_algebra_flotante(
                                escena=self, fuente=accion["fuente"],
                                ancho_camara=ancho_camara, posicion=accion["posicion"],
                                remover=accion["remover"], runtime=t_anim, waittime=t_wait
                            )

                        elif accion["tipo"] == "linea_punteada":
                            t_alpha = ValueTracker(0.0)

                            def crear_linea():
                                a = t_alpha.get_value() # a va de 0.0 a 1.0
                                
                                # Interpolación de X
                                x1 = accion["x1_ini"] * (1 - a) + accion["x1_fin"] * a
                                x2 = accion["x2_ini"] * (1 - a) + accion["x2_fin"] * a
                                
                                # Las Y pueden ser números interpolados o evaluados en la función dinámica
                                if callable(accion["y1_ini"]): y1 = accion["y1_ini"](x1)
                                else: y1 = accion["y1_ini"] * (1 - a) + accion["y1_fin"] * a
                                
                                if callable(accion["y2_ini"]): y2 = accion["y2_ini"](x2)
                                else: y2 = accion["y2_ini"] * (1 - a) + accion["y2_fin"] * a
                                
                                p1 = plano.c2p(x1, y1)
                                p2 = plano.c2p(x2, y2)
                                
                                # Prevenir colapso matemático si los puntos son idénticos
                                if np.linalg.norm(p2 - p1) < 1e-4:
                                    p2 = p1 + np.array([1e-4, 0, 0])
                                    
                                return DashedLine(p1, p2, color=accion["color"]).set_z_index(2)

                            linea = always_redraw(crear_linea)
                            
                            self.play(Create(linea), run_time=0.5)
                            self.play(t_alpha.animate.set_value(1.0), run_time=t_anim)
                            linea.clear_updaters()
                            self.wait(t_wait)

                        elif accion["tipo"] == "llave":
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
                            self.wait(t_wait)

                    self.wait(2)
            
            EscenaAutomatica().render()