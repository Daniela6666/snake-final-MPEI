#!/usr/bin/env python3
"""Ejecuta los siete análisis en orden, igual que el script único original.

Uso, desde cualquier carpeta:  python3 analizar_todo.py
Cada análisis también se puede ejecutar solo: python3 01_captura1_clk_lat/analizar.py
"""

import os
import runpy

CARPETA = os.path.dirname(os.path.abspath(__file__))
ANALISIS = [
    "01_captura1_clk_lat",
    "02_captura2_clk_oe",
    "03_captura3_clk_r1",
    "04_captura4_direccion_fila",
    "05_captura5_lat_a",
    "06_captura6_boton",
    "07_secuencia_de_una_fase",
]

for carpeta in ANALISIS:
    runpy.run_path(os.path.join(CARPETA, carpeta, "analizar.py"), run_name="__main__")

print("\nGráficas guardadas en la carpeta de cada captura, dentro de: " + CARPETA)
