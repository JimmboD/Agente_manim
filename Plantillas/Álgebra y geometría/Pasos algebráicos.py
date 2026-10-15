from Planos.generar_plano import AnimadorGrafico

if __name__ == "__main__":
    escena = AnimadorGrafico()
    
    # Inyecta el archivo de pasos algebraicos en LaTeX
    escena.insertar_algebra("pasos_algebraicos.txt", tiempo_animacion=1.5, tiempo_espera=2.0)
    
    escena.desvanecer_todo(tiempo_animacion=1.5)
    escena.render(previsualizar=True)
