import sympy as sp
import numpy as np
import random
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)

def generar_numero(permitir_cero=False):
    usar_fraccion = random.choice([True, False])
    numerador = random.randint(-50, 50)
    if not permitir_cero and numerador == 0:
        numerador = random.choice([-1, 1])
    if usar_fraccion:
        return sp.Rational(numerador, random.randint(1, 50))
    return numerador

def generar_termino(x, profundidad_actual=0, profundidad_max=1):
    catalogo = ['polinomio', 'trigonometrica', 'exponencial', 'raiz', 'logaritmica', 'cociente']
    if profundidad_actual >= profundidad_max:
        catalogo.remove('cociente')
        
    eleccion = random.choice(catalogo)
    a, w = generar_numero(), generar_numero()
    
    if eleccion == 'polinomio':
        return a * (x**random.randint(1, 5))
    elif eleccion == 'trigonometrica':
        return a * random.choice([sp.sin, sp.cos])(w * x)
    elif eleccion == 'exponencial':
        return a * sp.exp(w * x)
    elif eleccion == 'raiz':
        return a * sp.root((w**2 * x**2) + random.randint(1, 50), random.randint(2, 4))
    elif eleccion == 'logaritmica':
        return a * sp.log((w**2 * x**2) + random.randint(1, 50))
    elif eleccion == 'cociente':
        numerador = generar_termino(x, profundidad_actual + 1, profundidad_max)
        denominador = generar_termino(x, profundidad_actual + 1, profundidad_max)
        return (a * numerador) / (denominador**2 + random.randint(1, 50))

def cumple_restricciones_graficas(f_lambda, x_min_vis, x_max_vis, num_puntos=500):
    """
    Escáner estricto: Asegura continuidad y garantiza matemáticamente 
    que la función jamás rompa la escala 1:1 en el lienzo 9:16.
    """
    x_vals = np.linspace(x_min_vis, x_max_vis, num_puntos)
    try:
        y_vals = f_lambda(x_vals)
        
        if np.isnan(y_vals).any() or np.isinf(y_vals).any() or not np.isreal(y_vals).all():
            return False
            
        if np.max(np.abs(np.diff(y_vals))) > 50.0:
            return False
            
        # Candado estricto de proporción: La diferencia entre el máximo y mínimo
        # en la caja visible NUNCA debe superar 16 unidades de alto ni ser menor a 2.
        delta_y = np.max(y_vals) - np.min(y_vals)
        if delta_y > 14.0 or delta_y < 2.0:
            return False
            
        return True
    except Exception:
        return False

def generar_ejercicio(metodo=None):
    x = sp.Symbol('x')
    metodos_validos = ['Bisección', 'Regla Falsa', 'Newton-Raphson']
    metodo_seleccionado = metodo if metodo in metodos_validos else random.choice(metodos_validos)
    requiere_intervalo = metodo_seleccionado in ['Bisección', 'Regla Falsa']
    
    while True:
        try:
            # Límite drástico: Máximo 5 términos para mantener el bloque de texto manejable
            terminos = [generar_termino(x) for _ in range(random.randint(1, 5))]
            f_cruda = sum(terminos)
            
            r_exacta = round(random.uniform(-5.0, 5.0), 2)
            
            # Redondeo estricto a 2 decimales para la constante de ajuste
            y_en_r = float(f_cruda.subs(x, r_exacta).evalf())
            constante_ajuste = round(y_en_r, 2)
            f_final = f_cruda - constante_ajuste
            
            f_lambda = sp.lambdify(x, f_final, modules=['numpy', 'sympy'])
            
            if requiere_intervalo:
                a, b = sorted([
                    round(r_exacta - random.uniform(0.1, 1.0), 2),
                    round(r_exacta + random.uniform(1.5, 4.0), 2)
                ]) if random.choice([True, False]) else sorted([
                    round(r_exacta - random.uniform(1.5, 4.0), 2),
                    round(r_exacta + random.uniform(0.1, 1.0), 2)
                ])
                
                if f_lambda(a) * f_lambda(b) >= 0:
                    continue
                    
                # Pasar la caja visual completa de Manim al escáner estricto
                if not cumple_restricciones_graficas(f_lambda, a - 0.5, b + 0.5):
                    continue
                    
                return {
                    'metodo': metodo_seleccionado,
                    'ecuacion': f_final,
                    'latex': sp.latex(f_final),
                    'parametros': f"Intervalo: [{a}, {b}]",
                    'valores_iniciales': (a, b),
                    'raiz_objetiva': r_exacta
                }
            else:
                x0 = round(r_exacta + random.uniform(-1.5, 1.5), 2)
                x_min_vis, x_max_vis = min(x0, r_exacta) - 0.5, max(x0, r_exacta) + 0.5
                
                if not cumple_restricciones_graficas(f_lambda, x_min_vis, x_max_vis):
                    continue
                
                df_lambda = sp.lambdify(x, sp.diff(f_final, x), modules=['numpy', 'sympy'])
                if abs(df_lambda(x0)) < 1e-4:
                    continue
                    
                return {
                    'metodo': metodo_seleccionado,
                    'ecuacion': f_final,
                    'latex': sp.latex(f_final),
                    'parametros': f"Aproximación inicial x0: {x0}",
                    'valores_iniciales': x0,
                    'raiz_objetiva': r_exacta
                }
        except Exception:
            continue

# ==========================================
# PRUEBA DEL MOTOR DEPURADO
# ==========================================
if __name__ == "__main__":
    ejercicio_limpio = generar_ejercicio()
    print(f"Método:   {ejercicio_limpio['metodo']}")
    print(f"Ecuación: {ejercicio_limpio['ecuacion']}")
    print(f"LaTeX:    {ejercicio_limpio['latex']}")
    print(f"Datos:    {ejercicio_limpio['parametros']}")