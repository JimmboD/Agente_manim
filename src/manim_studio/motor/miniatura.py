from manim import *
import numpy as np

# Configuración global de resolución y relación de aspecto exacta 4:1
config.pixel_width = 1584
config.pixel_height = 396
config.frame_height = 4.0
config.frame_width = 16.0  # Límites de X: [-8.0, 8.0], Límites de Y: [-2.0, 2.0]
config.background_color = "#121212"


class ECGFourierBanner(ThreeDScene):

    def construct(self):
        # ---------------------------------------------------------
        # 1. CUADRÍCULA DE FONDO (El Lienzo Espacial)
        # ---------------------------------------------------------
        grid = NumberPlane(
            x_range=[-14, 14, 0.5],
            y_range=[-6, 6, 0.5],
            background_line_style={
                "stroke_color": "#2A2A2A",
                "stroke_width": 1.2,
                "stroke_opacity": 0.6,
            },
            axis_config={"stroke_opacity": 0},
        )
        self.add(grid)

        # ---------------------------------------------------------
        # 2. LA SEÑAL CLÍNICA (Centro-Izquierda: x de -1.6 a 0.8)
        # ---------------------------------------------------------
        def ecg_morphology(x):
            t = (x - (-0.4)) * 2.2
            p_wave = 0.18 * np.exp(-((t + 0.7) ** 2) / 0.03)
            q_wave = -0.22 * np.exp(-((t + 0.18) ** 2) / 0.005)
            r_wave = 1.15 * np.exp(-(t**2) / 0.008)
            s_wave = -0.32 * np.exp(-((t - 0.18) ** 2) / 0.006)
            t_wave = 0.28 * np.exp(-((t - 0.85) ** 2) / 0.05)

            noise = (
                0.04 * np.sin(28 * x)
                + 0.025 * np.cos(45 * x)
                + 0.03 * np.sin(4 * x)
            )
            return p_wave + q_wave + r_wave + s_wave + t_wave + noise

        x_Prism = 0.8

        ecg_curve = ParametricFunction(
            lambda t: np.array([t, ecg_morphology(t), 0]),
            t_range=[-1.6, x_Prism, 0.01],
            color="#00FFCC",
            stroke_width=3.5,
        )
        ecg_glow = ecg_curve.copy().set_stroke(
            color="#00FFCC", width=9, opacity=0.25
        )

        # ---------------------------------------------------------
        # 3. EL PRISMA MATEMÁTICO (Umbral Tiempo -> Frecuencia)
        # ---------------------------------------------------------
        prism_plane = Surface(
            lambda u, v: np.array([x_Prism, u, v]),
            u_range=[-1.6, 1.6],
            v_range=[-1.8, 1.8],
            resolution=(2, 2),
        )
        prism_plane.set_style(
            fill_color="#FFFFFF",
            fill_opacity=0.07,
            stroke_color="#00FFCC",
            stroke_width=0.8,
            stroke_opacity=0.3,
        )

        prism_line = DashedLine(
            start=[x_Prism, -1.75, 0],
            end=[x_Prism, 1.75, 0],
            color=WHITE,
            dash_length=0.12,
            stroke_width=2.5,
        )

        # ---------------------------------------------------------
        # 4. LA DESCOMPOSICIÓN ESPECTRAL (Centro-Derecha: x de 0.8 a 7.3)
        # ---------------------------------------------------------
        def envelope(x):
            fade_in = np.clip((x - x_Prism) / 0.35, 0, 1)
            fade_out = np.clip((7.3 - x) / 1.4, 0, 1)
            return fade_in * (fade_out**1.5)

        wave_low = ParametricFunction(
            lambda t: np.array(
                [t, 0.70 * np.sin(1.8 * (t - x_Prism)) * envelope(t), -1.3]
            ),
            t_range=[x_Prism, 7.3, 0.02],
            color="#FF00FF",
            stroke_width=3.2,
        )

        wave_mid = ParametricFunction(
            lambda t: np.array(
                [t, 0.42 * np.sin(5.0 * (t - x_Prism)) * envelope(t), 0.0]
            ),
            t_range=[x_Prism, 7.3, 0.02],
            color="#FFFF00",
            stroke_width=2.6,
        )

        wave_high = ParametricFunction(
            lambda t: np.array(
                [t, 0.20 * np.sin(18.0 * (t - x_Prism)) * envelope(t), 1.3]
            ),
            t_range=[x_Prism, 7.3, 0.01],
            color="#0088FF",
            stroke_width=2.0,
        )

        connectors = VGroup(
            DashedLine(
                [x_Prism, ecg_morphology(x_Prism), 0],
                [x_Prism, 0, -1.3],
                color="#FF00FF",
                stroke_opacity=0.6,
            ),
            DashedLine(
                [x_Prism, ecg_morphology(x_Prism), 0],
                [x_Prism, 0, 0.0],
                color="#FFFF00",
                stroke_opacity=0.6,
            ),
            DashedLine(
                [x_Prism, ecg_morphology(x_Prism), 0],
                [x_Prism, 0, 1.3],
                color="#0088FF",
                stroke_opacity=0.6,
            ),
        )

        # ---------------------------------------------------------
        # 5. LA FIRMA DE INGENIERÍA (Esquina Superior Derecha)
        # ---------------------------------------------------------
        fourier_eq = MathTex(
            r"\mathcal{F}(\omega) = \int_{-\infty}^{\infty} f(t) e^{-j\omega t} \, dt",
            color="#FFFFFF",
            font_size=30,
        )
        fourier_eq.move_to([4.8, 1.35, 0])
        self.add_fixed_in_frame_mobjects(fourier_eq)
        fourier_eq.set_opacity(0)

        # ---------------------------------------------------------
        # 6. SECUENCIA DE ANIMACIÓN
        # ---------------------------------------------------------
        self.set_camera_orientation(phi=0 * DEGREES, theta=-90 * DEGREES)

        # Paso 1: Avance de la señal de ECG
        self.play(
            Create(ecg_curve),
            Create(ecg_glow),
            run_time=2.0,
            rate_func=rate_functions.ease_in_out_sine,
        )

        # Paso 2: Aparición del Prisma y giro de cámara 3D compatible con ThreeDCamera
        self.move_camera(
            phi=20 * DEGREES,
            theta=-76 * DEGREES,
            gamma=4 * DEGREES,
            added_anims=[
                FadeIn(prism_line),
                FadeIn(prism_plane),
            ],
            run_time=1.6,
        )

        # Paso 3: Explosión espectral en el eje Z y aparición de la ecuación de Fourier
        self.play(
            FadeIn(connectors, run_time=0.4),
            Create(wave_low),
            Create(wave_mid),
            Create(wave_high),
            fourier_eq.animate.set_opacity(1.0),
            run_time=2.5,
            rate_func=linear,
        )

        self.wait(2)