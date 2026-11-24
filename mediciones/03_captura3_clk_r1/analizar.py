#!/usr/bin/env python3
"""Captura 3: CLK (PC8) y R1 (PC0). Lee los 128 bits que viajan por R1 y mide cuándo cambia el dato.

Uso, desde cualquier carpeta:  python3 analizar.py
Lee captura3-CLK-R1.csv (de esta carpeta) y guarda captura3-CLK-R1.png y captura3-CLK-R1-acercamiento.png aquí mismo.
"""

# Para armar rutas de archivos y carpetas.
import os
# Para modificar la lista de carpetas donde Python busca módulos.
import sys

# Agrega la carpeta comun/ (la hermana de esta) a la lista donde Python busca módulos; así «import medicion» funciona se ejecute desde donde se ejecute.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "comun"))
# numpy: operaciones sobre miles de muestras a la vez, sin bucles.
import numpy as np
# Herramientas de comun/medicion.py (explicadas en ../comun/README.md); plt es matplotlib.pyplot ya configurado para guardar sin abrir ventana.
from medicion import US, UMBRAL, cruces, rafagas, ultimo_antes, mostrar, guardar, niveles, leer_csv, plt

# CARPETA: la carpeta de este archivo; ahí están el CSV y se guarda la gráfica.
CARPETA = os.path.dirname(os.path.abspath(__file__))


# Hace todo el análisis de la captura 3 (CLK y R1) y guarda dos gráficas.
def analizar_captura3():
    # Encabezado de esta captura en la salida.
    mostrar("captura3-CLK-R1: CLK (PC8) y R1 (PC0)")
    # Lee el CSV (CH1 = CLK, CH2 = R1, el dato rojo del panel superior).
    t, clk, r1 = leer_csv("captura3-CLK-R1.csv", CARPETA)
    # Intervalo entre muestras (ns) y duración total (ms).
    print("Intervalo: %.1f ns, ventana: %.2f ms" % ((t[1] - t[0]) * 1e9, t[-1] * 1e3))
    # Instantes en que CLK sube.
    subidas = cruces(t, clk, True)
    # Agrupa las subidas en ráfagas.
    grupos = rafagas(subidas, 20e-6)
    # Imprime los pulsos de cada ráfaga.
    print("Ráfagas: %s pulsos" % [len(g) for g in grupos])
    # Ráfagas completas: las de 128 pulsos.
    completas = [g for g in grupos if len(g) == 128]
    # Si no hay ninguna...
    if len(completas) == 0:
        # ...se avisa...
        print("No hay ráfaga completa de 128 pulsos.")
        # ...y se termina (no se puede analizar).
        return
    # Se usa la primera ráfaga completa.
    grupo = completas[0]
    # Tiempo entre pulsos consecutivos.
    periodos = np.diff(grupo)
    # Imprime el periodo típico (mediana), el menor y el mayor.
    print("Periodo entre pulsos en la ráfaga completa: mediana %.2f µs, min %.2f, max %.2f" % (np.median(periodos) * US, periodos.min() * US, periodos.max() * US))
    # Cuenta los periodos entre 6,05 y 6,45 µs.
    print("Pulsos con periodo entre 6,1 y 6,4 µs: %d de %d" % (np.sum((periodos >= 6.05e-6) & (periodos <= 6.45e-6)), len(periodos)))
    # Listas donde se guardará el nivel de R1 justo antes y justo después de cada flanco de CLK.
    antes = []
    despues = []
    # Para cada pulso de CLK de la ráfaga:
    for subida in grupo:
        # Posición (índice) de la muestra más cercana al flanco; searchsorted busca en el arreglo ordenado de tiempos.
        indice = int(np.searchsorted(t, subida))
        # Nivel de R1 3 muestras antes del flanco (max evita salirse del arreglo por el inicio).
        antes.append(r1[max(indice - 3, 0)] > UMBRAL)
        # Nivel de R1 3 muestras después (min evita salirse por el final).
        despues.append(r1[min(indice + 3, len(r1) - 1)] > UMBRAL)
    # Se pasan las listas a arreglos de numpy para poder compararlas.
    antes = np.array(antes)
    despues = np.array(despues)
    # Cuántos pulsos tenían R1 en alto antes del flanco (es el bit que se estaba mandando).
    print("R1 en alto en %d de 128 pulsos (medido 3 muestras antes del flanco)" % antes.sum())
    # En cuántos pulsos R1 era igual antes y después: si es 128 de 128, el dato es estable alrededor del flanco.
    print("R1 igual antes y después del flanco en %d de 128 pulsos" % np.sum(antes == despues))
    # Cuántas veces R1 cambió de un pulso al siguiente (compara cada elemento con el anterior).
    print("Cambios de R1 entre pulsos consecutivos: %d" % np.sum(antes[1:] != antes[:-1]))
    # Arma un texto de 128 caracteres, un «1» o un «0» por pulso.
    cadena = "".join("1" if bit else "0" for bit in antes)
    # Encabezado de la lista de bits.
    print("Bits de R1 (primer pulso a la izquierda):")
    # Imprime los 128 bits en 8 filas de 16...
    for inicio in range(0, 128, 16):
        # ...con el rango de pulsos al principio de cada fila.
        print("  %3d a %3d: %s" % (inicio, inicio + 15, cadena[inicio:inicio + 16]))
    # Todos los instantes en que R1 cambia (subidas y bajadas juntas).
    cambios_r1 = np.concatenate([cruces(t, r1, True), cruces(t, r1, False)])
    # Aquí se guardará cuánto después del flanco de CLK cambia R1.
    retardos = []
    # Para cada cambio de R1...
    for cambio in cambios_r1:
        # ...dentro de la ráfaga (hasta 10 µs después del último pulso)...
        if grupo[0] <= cambio <= grupo[-1] + 10e-6:
            # ...se guarda la distancia al flanco de subida de CLK inmediatamente anterior.
            retardos.append(cambio - ultimo_antes(grupo, cambio))
    # Se pasa la lista a arreglo.
    retardos = np.array(retardos)
    # Si hubo cambios, se imprime el mínimo, el máximo y la mediana del retardo.
    if len(retardos) > 0:
        print("R1 cambia %.2f a %.2f µs después del flanco de subida anterior del CLK (mediana %.2f, %d cambios)"
              % (retardos.min() * US, retardos.max() * US, np.median(retardos) * US, len(retardos)))
    # Voltaje mínimo y máximo de cada canal.
    niveles("captura3", t, clk, r1, "CLK", "R1")

    # Gráfica completa: 2 paneles apilados que comparten el eje del tiempo (CLK arriba, R1 abajo).
    figura, ejes = plt.subplots(2, 1, sharex=True, figsize=(10, 4.5))
    # Panel de arriba: CLK en azul (tiempo en µs).
    ejes[0].plot(t * US, clk, color="#1f77b4", linewidth=0.6)
    ejes[0].set_ylabel("CLK, PC8 (V)")
    # Panel de abajo: R1 en rojo.
    ejes[1].plot(t * US, r1, color="#d62728", linewidth=0.8)
    ejes[1].set_ylabel("R1, PC0 (V)")
    ejes[1].set_xlabel("Tiempo (µs)")
    for eje in ejes:
        eje.axhline(UMBRAL, color="gray", linestyle=":", linewidth=0.8)
        eje.grid(alpha=0.3)
    ejes[0].set_title("CLK y dato R1: R1 cambia entre flancos, no en el flanco")
    guardar(figura, "captura3-CLK-R1.png", CARPETA)
    # Segunda gráfica: acercamiento a 10 pulsos, porque con 128 juntos no se distinguen los flancos.
    # Acercamiento a 10 pulsos
    # Figura de 2 paneles.
    figura, ejes = plt.subplots(2, 1, sharex=True, figsize=(10, 4.5))
    # Inicio de la ventana: 3 µs antes del pulso 20.
    inicio = grupo[20] - 3e-6
    # Fin de la ventana: 3 µs después del pulso 30.
    fin = grupo[30] + 3e-6
    # Máscara: verdadero solo para las muestras dentro de la ventana.
    mascara = (t >= inicio) & (t <= fin)
    # CLK en azul, solo la ventana.
    ejes[0].plot(t[mascara] * US, clk[mascara], color="#1f77b4", linewidth=0.9)
    ejes[0].set_ylabel("CLK, PC8 (V)")
    # R1 en rojo, solo la ventana.
    ejes[1].plot(t[mascara] * US, r1[mascara], color="#d62728", linewidth=0.9)
    ejes[1].set_ylabel("R1, PC0 (V)")
    ejes[1].set_xlabel("Tiempo (µs)")
    for eje in ejes:
        eje.axhline(UMBRAL, color="gray", linestyle=":", linewidth=0.8)
        eje.grid(alpha=0.3)
    ejes[0].set_title("Acercamiento: 10 pulsos de CLK y el dato R1")
    guardar(figura, "captura3-CLK-R1-acercamiento.png", CARPETA)


# Solo se ejecuta si el archivo se corre directamente (no cuando otro programa lo importa).
if __name__ == "__main__":
    analizar_captura3()
