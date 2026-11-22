import unittest

import numpy as np

from manim_studio.motor.planos.generar_plano import muestrear_funcion


class MuestreoFuncionTests(unittest.TestCase):
    def test_descarta_muestras_invalidas_y_mantiene_x_alineada(self):
        def funcion(x):
            if 0.4 < x < 0.6:
                raise ValueError("fuera de dominio")
            return (x - 0.8) ** 2

        xs = np.linspace(0.0, 1.0, 11)
        xs_validas, ys = muestrear_funcion(funcion, xs)

        self.assertEqual(len(xs_validas), len(ys))
        minimo = xs_validas[int(np.argmin(ys))]
        self.assertAlmostEqual(float(minimo), 0.8, places=1)
        self.assertFalse(np.any((xs_validas > 0.4) & (xs_validas < 0.6)))

    def test_fallback_sin_muestras_validas(self):
        def funcion(x):
            return float("nan")

        xs = np.linspace(-1.0, 1.0, 5)
        xs_validas, ys = muestrear_funcion(funcion, xs)

        self.assertEqual(list(xs_validas), [-1.0, 1.0])
        self.assertEqual(list(ys), [-1.0, 1.0])


if __name__ == "__main__":
    unittest.main()
