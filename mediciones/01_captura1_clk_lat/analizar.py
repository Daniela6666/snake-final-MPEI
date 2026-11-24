#!/usr/bin/env python3
"""Captura 1: CLK (PC8) y LAT (PC7). Cuenta los pulsos por ráfaga y mide periodos y anchos.

Uso, desde cualquier carpeta:  python3 analizar.py
Lee captura1-CLK-LAT.csv (de esta carpeta) y guarda captura1-CLK-LAT.png aquí mismo.
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
from medicion import US, UMBRAL, cruces, rafagas, primero_despues, mostrar, guardar, niveles, leer_csv, plt

# CARPETA: la carpeta de este archivo; ahí están el CSV y se guarda la gráfica.
CARPETA = os.path.dirname(os.path.abspath(__file__))


# Hace todo el análisis de la captura 1 (CLK y LAT) y guarda la gráfica.
def analizar_captura1():
    # Encabezado de esta captura en la salida.
    mostrar("captura1-CLK-LAT: CLK (PC8) y LAT (PC7)")
    # Lee el CSV: tiempos y los dos canales (CH1 = CLK, CH2 = LAT).
    t, clk, lat = leer_csv("captura1-CLK-LAT.csv", CARPETA)
    # Datos generales: cantidad de muestras, intervalo entre muestras (ns) y duración total (ms).
    print("Muestras: %d, intervalo: %.1f ns, ventana: %.2f ms" % (len(t), (t[1] - t[0]) * 1e9, t[-1] * 1e3))
    # Instantes en que CLK sube...
    subidas = cruces(t, clk, True)
    # ...y en que baja (con interpolación).
    bajadas = cruces(t, clk, False)
    # Agrupa las subidas en ráfagas: una pausa de más de 20 µs abre una ráfaga nueva.
    grupos = rafagas(subidas, 20e-6)
    # Cuántas ráfagas hay y cuántos pulsos tiene cada una (la ventana corta las de los extremos).
    print("Ráfagas detectadas: %d, con pulsos: %s" % (len(grupos), [len(g) for g in grupos]))
    # Se queda solo con las ráfagas completas: las de exactamente 128 pulsos.
    completas = [g for g in grupos if len(g) == 128]
    # Cuántas ráfagas completas hay.
    print("Ráfagas completas de 128 pulsos: %d" % len(completas))
    # Para cada ráfaga completa:
    for numero, grupo in enumerate(completas):
        # Tiempo entre pulsos consecutivos (np.diff resta cada instante con el anterior).
        periodos = np.diff(grupo)
        # Estadísticas del periodo (mediana, mínimo, máximo) y de cuándo empieza y termina la ráfaga.
        print("  ráfaga completa %d: periodo mediano %.3f µs (min %.2f, max %.2f), primera subida %.1f µs, última %.1f µs"
              % (numero, np.median(periodos) * US, periodos.min() * US, periodos.max() * US,
                 grupo[0] * US, grupo[-1] * US))
        # Duración de la ráfaga: de la primera a la última subida, y con un periodo más (hasta el final del último pulso).
        print("    duración (primera a última subida): %.1f µs; duración con un periodo más: %.1f µs"
              % ((grupo[-1] - grupo[0]) * US, (grupo[-1] - grupo[0] + np.median(periodos)) * US))
    # Ancho de cada pulso de CLK en alto: de cada subida a la siguiente bajada.
    anchos = []
    # Para cada subida...
    for subida in subidas:
        # ...las bajadas que ocurren después de ella...
        despues = bajadas[bajadas > subida]
        # ...y si hay alguna, la primera es el final de ese pulso.
        if len(despues) > 0:
            # Se guarda el ancho (bajada − subida).
            anchos.append(despues[0] - subida)
    # Se convierte la lista en arreglo de numpy para calcular mediana, mínimo y máximo.
    anchos = np.array(anchos)
    # Imprime el ancho típico del pulso en alto de CLK.
    print("Ancho del pulso en alto de CLK: mediana %.2f µs, min %.2f, max %.2f" % (np.median(anchos) * US, anchos.min() * US, anchos.max() * US))
    # Si hay una ráfaga completa y otra después, mide la pausa entre ráfagas:
    if len(completas) >= 1 and len(grupos) >= 2:
        # Pausa = primera subida de la ráfaga siguiente − última subida de la anterior.
        pausas = [grupos[i + 1][0] - grupos[i][-1] for i in range(len(grupos) - 1)]
        # Imprime las pausas (µs).
        print("Pausa entre última subida de una ráfaga y la primera de la siguiente: %s µs" % ["%.1f" % (p * US) for p in pausas])
    # Instantes en que LAT sube...
    lat_subidas = cruces(t, lat, True)
    # ...y en que baja.
    lat_bajadas = cruces(t, lat, False)
    # Imprime cuántos pulsos de LAT hay y cuándo suben.
    print("Pulsos de LAT: %d, subidas en µs: %s" % (len(lat_subidas), ["%.1f" % (x * US) for x in lat_subidas]))
    # Con dos o más pulsos de LAT se puede medir cada cuánto se repite:
    if len(lat_subidas) >= 2:
        # Periodo de LAT = diferencia entre subidas consecutivas.
        print("Periodo de LAT: %s µs" % ["%.1f" % (d * US) for d in np.diff(lat_subidas)])
    # Ancho de cada pulso de LAT: de su subida a la primera bajada posterior.
    anchos_lat = [primero_despues(lat_bajadas, s) - s for s in lat_subidas if np.any(lat_bajadas >= s)]
    # Imprime los anchos de LAT.
    print("Ancho del pulso de LAT: %s µs" % ["%.2f" % (a * US) for a in anchos_lat])
    # Voltaje mínimo y máximo de cada canal (para ver los niveles reales).
    niveles("captura1", t, clk, lat, "CLK", "LAT")

    # Gráfica: 2 paneles apilados que comparten el eje del tiempo (CLK arriba, LAT abajo).
    figura, ejes = plt.subplots(2, 1, sharex=True, figsize=(10, 4.5))
    # Panel de arriba: CLK en azul (tiempo pasado a µs con US).
    ejes[0].plot(t * US, clk, color="#1f77b4", linewidth=0.6)
    # Nombre del eje vertical del panel de arriba.
    ejes[0].set_ylabel("CLK, PC8 (V)")
    # Panel de abajo: LAT en rojo.
    ejes[1].plot(t * US, lat, color="#d62728", linewidth=0.8)
    # Nombre del eje vertical del panel de abajo.
    ejes[1].set_ylabel("LAT, PC7 (V)")
    # Nombre del eje del tiempo (solo el panel de abajo).
    ejes[1].set_xlabel("Tiempo (µs)")
    # En cada panel:
    for eje in ejes:
        # una línea punteada gris en el umbral de 1,65 V (separa alto de bajo)
        eje.axhline(UMBRAL, color="gray", linestyle=":", linewidth=0.8)
        # y una cuadrícula suave.
        eje.grid(alpha=0.3)
    # Título de la gráfica.
    ejes[0].set_title("CLK y LAT: ráfagas de 128 pulsos y un pulso de LAT por fase")
    # Se guarda el PNG en esta carpeta y se libera la figura.
    guardar(figura, "captura1-CLK-LAT.png", CARPETA)


# Solo se ejecuta si el archivo se corre directamente (no cuando otro programa lo importa).
if __name__ == "__main__":
    analizar_captura1()
