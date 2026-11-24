#!/usr/bin/env python3
"""Captura 5: LAT (PC7) y A (PC10). Mide cuánto después del pulso de LAT cambia la dirección de fila.

Uso, desde cualquier carpeta:  python3 analizar.py
Lee captura5-LAT-A.csv (de esta carpeta) y guarda captura5-LAT-A.png aquí mismo.
"""

# Para armar rutas de archivos y carpetas.
import os
# Para modificar la lista de carpetas donde Python busca módulos.
import sys

# Agrega la carpeta comun/ (la hermana de esta) a la lista donde Python busca módulos; así «import medicion» funciona se ejecute desde donde se ejecute.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "comun"))
# numpy: operaciones sobre miles de muestras a la vez, sin bucles.
import numpy as np
# Herramientas de comun/medicion.py (explicadas en ../comun/README.md).
from medicion import US, cruces, primero_despues, mostrar, niveles, grafica_dos_canales, leer_csv

# CARPETA: la carpeta de este archivo; ahí están el CSV y se guarda la gráfica.
CARPETA = os.path.dirname(os.path.abspath(__file__))


# Hace todo el análisis de la captura 5 (LAT y A) y guarda la gráfica.
def analizar_captura5():
    # Encabezado de esta captura en la salida.
    mostrar("captura5-LAT-A: LAT (PC7) y A (PC10)")
    # Lee el CSV (CH1 = LAT, CH2 = A).
    t, lat, a = leer_csv("captura5-LAT-A.csv", CARPETA)
    # Instantes en que LAT sube...
    lat_subidas = cruces(t, lat, True)
    # ...y en que baja.
    lat_bajadas = cruces(t, lat, False)
    # Todos los instantes en que A cambia (subidas y bajadas juntas, ordenados).
    cambios_a = np.sort(np.concatenate([cruces(t, a, True), cruces(t, a, False)]))
    # Imprime cuándo sube LAT.
    print("LAT sube en (µs): %s" % ["%.2f" % (x * US) for x in lat_subidas])
    # Imprime cuándo cambia A.
    print("A cambia en (µs): %s" % ["%.2f" % (x * US) for x in cambios_a])
    # Para cada subida de LAT:
    for subida in lat_subidas:
        # Cambios de A que ocurren después de esa subida.
        despues = cambios_a[cambios_a > subida]
        # Si hay alguno...
        if len(despues) > 0:
            # ...imprime cuánto después de que LAT sube cambia A el primero, y cuánto después de que LAT baja.
            print("  A cambia %.2f µs después de que LAT sube (%.2f µs después de que LAT baja)"
                  % ((despues[0] - subida) * US, (despues[0] - primero_despues(lat_bajadas, subida)) * US))
    # Con dos o más pulsos de LAT se mide su periodo.
    if len(lat_subidas) >= 2:
        # Periodo de LAT = diferencia entre subidas consecutivas.
        print("Periodo de LAT: %s µs" % ["%.1f" % (d * US) for d in np.diff(lat_subidas)])
    # Ancho de cada pulso de LAT: de su subida a la primera bajada posterior.
    anchos = [primero_despues(lat_bajadas, s) - s for s in lat_subidas if np.any(lat_bajadas >= s)]
    # Imprime los anchos.
    print("Ancho del pulso de LAT: %s µs" % ["%.2f" % (x * US) for x in anchos])
    # Voltaje mínimo y máximo de cada canal.
    niveles("captura5", t, lat, a, "LAT", "A")
    # Gráfica estándar de dos paneles (LAT arriba, A abajo); la guarda en esta carpeta.
    grafica_dos_canales(CARPETA, "captura5-LAT-A.csv", "LAT y A: A cambia poco después del pulso de LAT", "LAT, PC7", "A, PC10")


# Solo se ejecuta si el archivo se corre directamente (no cuando otro programa lo importa).
if __name__ == "__main__":
    analizar_captura5()
