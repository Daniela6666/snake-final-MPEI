#!/usr/bin/env python3
"""Captura 2: CLK (PC8) y OE (PC6). Mide cuándo sube y baja OE respecto al último pulso de CLK.

Uso, desde cualquier carpeta:  python3 analizar.py
Lee captura2-CLK-OE.csv (de esta carpeta) y guarda captura2-CLK-OE.png aquí mismo.
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
from medicion import US, UMBRAL, cruces, rafagas, ultimo_antes, primero_despues, mostrar, niveles, grafica_dos_canales, leer_csv

# CARPETA: la carpeta de este archivo; ahí están el CSV y se guarda la gráfica.
CARPETA = os.path.dirname(os.path.abspath(__file__))


# Hace todo el análisis de la captura 2 (CLK y OE) y guarda la gráfica.
def analizar_captura2():
    # Encabezado de esta captura en la salida.
    mostrar("captura2-CLK-OE: CLK (PC8) y OE (PC6)")
    # Lee el CSV (CH1 = CLK, CH2 = OE).
    t, clk, oe = leer_csv("captura2-CLK-OE.csv", CARPETA)
    # Instantes en que CLK sube.
    subidas = cruces(t, clk, True)
    # Instantes en que OE sube (el panel se apaga: OE es activo en bajo)...
    oe_subidas = cruces(t, oe, True)
    # ...y en que OE baja (el panel se enciende).
    oe_bajadas = cruces(t, oe, False)
    # Imprime cuántos flancos de OE hay.
    print("Flancos de subida de OE: %d, de bajada: %d" % (len(oe_subidas), len(oe_bajadas)))
    # Agrupa las subidas de CLK en ráfagas (pausa de más de 20 µs = ráfaga nueva).
    grupos = rafagas(subidas, 20e-6)
    # Imprime los pulsos de cada ráfaga.
    print("Ráfagas: %s pulsos" % [len(g) for g in grupos])
    # Para cada vez que OE sube:
    for subida in oe_subidas:
        # Último pulso de CLK antes de ese instante (el final de la ráfaga).
        ultimo = ultimo_antes(subidas, subida)
        # La bajada de OE que sigue (None si la ventana termina antes).
        bajada = primero_despues(oe_bajadas, subida) if np.any(oe_bajadas >= subida) else None
        # Texto: cuánto después del último CLK sube OE.
        texto = "OE sube %.2f µs después del último CLK" % ((subida - ultimo) * US)
        # Si se encontró la bajada...
        if bajada is not None:
            # ...se agrega cuándo baja OE y cuánto dura en alto.
            texto += "; OE baja %.2f µs después del último CLK (OE alto %.2f µs)" % ((bajada - ultimo) * US, (bajada - subida) * US)
        # Imprime el resultado de esta subida de OE.
        print("  " + texto)
    # Máscara verdadero/falso: una muestra de OE es «alto» si pasa de 1,65 V.
    nivel_alto = oe > UMBRAL
    # Porcentaje de la ventana con OE en alto (el promedio de la máscara): el tiempo con el panel apagado.
    print("Fracción de la ventana con OE en alto: %.2f %%" % (100.0 * nivel_alto.mean()))
    # Voltaje mínimo y máximo de cada canal.
    niveles("captura2", t, clk, oe, "CLK", "OE")
    # Gráfica estándar de dos paneles (CLK arriba, OE abajo); la guarda en esta carpeta.
    grafica_dos_canales(CARPETA, "captura2-CLK-OE.csv", "CLK y OE: OE solo sube alrededor del latch", "CLK, PC8", "OE, PC6")


# Solo se ejecuta si el archivo se corre directamente (no cuando otro programa lo importa).
if __name__ == "__main__":
    analizar_captura2()
