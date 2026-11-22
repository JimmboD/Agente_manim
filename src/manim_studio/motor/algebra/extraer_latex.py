def extraer_texto_colores(texto_latex):
    resultados = []
    indice_limpio_actual = 0
    ultimo_indice_original = 0
    
    while True:
        # 1. Buscar el inicio del siguiente comando \textcolor
        inicio_cmd = texto_latex.find(r"\textcolor{", ultimo_indice_original)
        
        if inicio_cmd == -1:
            # Si no hay más comandos, guardamos el resto del texto como blanco
            texto_restante = texto_latex[ultimo_indice_original:]
            if texto_restante:
                fin_restante = indice_limpio_actual + len(texto_restante)
                resultados.append([texto_restante, "white", indice_limpio_actual, fin_restante])
            break
            
        # 2. Extraer el texto "blanco" que haya antes del comando
        texto_blanco = texto_latex[ultimo_indice_original:inicio_cmd]
        if texto_blanco:
            fin_blanco = indice_limpio_actual + len(texto_blanco)
            resultados.append([texto_blanco, "white", indice_limpio_actual, fin_blanco])
            indice_limpio_actual = fin_blanco
            
        # 3. Extraer el Color
        inicio_color = inicio_cmd + 11  # Longitud de "\textcolor{"
        fin_color = texto_latex.find("}", inicio_color)
        color = texto_latex[inicio_color:fin_color]
        
        # 4. Extraer el texto coloreado (usando conteo de llaves)
        # Asegurarnos de encontrar la llave de apertura del texto
        inicio_texto = texto_latex.find("{", fin_color) 
        
        contador_llaves = 1
        idx_actual = inicio_texto + 1
        
        # Recorremos el texto sumando y restando llaves hasta llegar a 0
        while contador_llaves > 0 and idx_actual < len(texto_latex):
            if texto_latex[idx_actual] == "{":
                contador_llaves += 1
            elif texto_latex[idx_actual] == "}":
                contador_llaves -= 1
            idx_actual += 1
            
        # Al salir del bucle, idx_actual está un índice por delante de la llave de cierre final
        fin_texto = idx_actual - 1
        texto_color = texto_latex[inicio_texto+1:fin_texto]
        
        # 5. Guardar los resultados y avanzar los índices
        fin_color_idx = indice_limpio_actual + len(texto_color)
        resultados.append([texto_color, color, indice_limpio_actual, fin_color_idx])
        
        indice_limpio_actual = fin_color_idx
        ultimo_indice_original = idx_actual
        
    return resultados