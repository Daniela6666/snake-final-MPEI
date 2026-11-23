#!/usr/bin/env python3
"""Secuencia de una fase: junta CLK, LAT, OE y A (capturas 1, 2 y 5) alineados con el último pulso de CLK.

Uso, desde cualquier carpeta:  python3 analizar.py
Lee los CSV de las carpetas 01, 02 y 05 y guarda secuencia-de-una-fase.png en esta carpeta.
No imprime números.
"""

# Para armar rutas de archivos y carpetas.
import os
# Para modificar la lista de carpetas donde Python busca módulos.
import sys

# Agrega la carpeta comun/ (la hermana de esta) a la lista donde Python busca módulos; así «import medicion» funciona se ejecute desde donde se ejecute.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "comun"))
# Herramientas de comun/medicion.py (explicadas en ../comun/README.md); plt es matplotlib.pyplot ya configurado para guardar sin abrir ventana.
from medicion import US, UMBRAL, cruces, rafagas, primero_despues, guardar, leer_csv, plt

CARPETA = os.path.dirname(os.path.abspath(__file__))
# CARPETA: la carpeta de este archivo, donde se guarda la gráfica.
# Los CSV están en las carpetas de las capturas 1, 2 y 5, hermanas de esta.
# Carpeta de la captura 1 (CLK y LAT)...
CAPTURA1 = os.path.join(os.path.dirname(CARPETA), "01_captura1_clk_lat")
# ...de la captura 2 (CLK y OE)...
CAPTURA2 = os.path.join(os.path.dirname(CARPETA), "02_captura2_clk_oe")
# ...y de la captura 5 (LAT y A).
CAPTURA5 = os.path.join(os.path.dirname(CARPETA), "05_captura5_lat_a")


# Dibuja la secuencia completa al final de una ráfaga juntando tres capturas.
def grafica_secuencia_fase():
    """Una sola gráfica con la secuencia del final de la ráfaga, combinando CLK, OE, LAT y A (capturas 1, 2 y 5)."""
    # Captura 1: CLK y LAT.
    t1, clk1, lat1 = leer_csv("captura1-CLK-LAT.csv", CAPTURA1)
    # Captura 2: CLK y OE.
    t2, clk2, oe2 = leer_csv("captura2-CLK-OE.csv", CAPTURA2)
    # Captura 5: LAT y A.
    t5, lat5, a5 = leer_csv("captura5-LAT-A.csv", CAPTURA5)
    # Figura de 4 paneles apilados (CLK, LAT, OE, A). Cada captura tiene su propia escala de tiempo, por eso no comparten eje.
    figura, ejes = plt.subplots(4, 1, sharex=False, figsize=(10, 7))
    # Cada captura se alinea con su último flanco de subida de CLK (o con el flanco de LAT en la captura 5).
    # Subidas de CLK en la captura 1.
    subidas1 = cruces(t1, clk1, True)
    # Ráfagas de la captura 1.
    grupos1 = rafagas(subidas1, 20e-6)
    # Último pulso de CLK de la primera ráfaga: será el tiempo 0 de la gráfica.
    ultimo1 = grupos1[0][-1]
    # Máscara: solo las muestras entre 12 µs antes y 12 µs después de ese pulso.
    mascara1 = (t1 > ultimo1 - 12e-6) & (t1 < ultimo1 + 12e-6)
    # Panel 1: CLK con el tiempo medido desde el último pulso (en µs).
    ejes[0].plot((t1[mascara1] - ultimo1) * US, clk1[mascara1], color="#1f77b4", linewidth=0.9)
    # Nombre del eje.
    ejes[0].set_ylabel("CLK (V)")
    # Panel 2: LAT con el mismo tiempo 0.
    ejes[1].plot((t1[mascara1] - ultimo1) * US, lat1[mascara1], color="#d62728", linewidth=0.9)
    # Nombre del eje.
    ejes[1].set_ylabel("LAT (V)")
    # Lo mismo para la captura 2: subidas de CLK...
    subidas2 = cruces(t2, clk2, True)
    # ...ráfagas...
    grupos2 = rafagas(subidas2, 20e-6)
    # ...último pulso (tiempo 0)...
    ultimo2 = grupos2[0][-1]
    # ...ventana de ±12 µs...
    mascara2 = (t2 > ultimo2 - 12e-6) & (t2 < ultimo2 + 12e-6)
    # Panel 3: OE.
    ejes[2].plot((t2[mascara2] - ultimo2) * US, oe2[mascara2], color="#2ca02c", linewidth=0.9)
    # Nombre del eje.
    ejes[2].set_ylabel("OE (V)")
    # Captura 5: instantes en que LAT sube.
    lat_subidas5 = cruces(t5, lat5, True)
    # Referencia: la primera subida de LAT.
    referencia5 = lat_subidas5[0]
    # Ventana de ±12 µs alrededor de esa subida.
    mascara5 = (t5 > referencia5 - 12e-6) & (t5 < referencia5 + 12e-6)
    # La captura 5 no tiene CLK: se alinea con el instante en que LAT sube respecto al último CLK en la captura 1.
    # Retardo entre el último CLK y la subida de LAT, medido en la captura 1.
    retardo_lat = primero_despues(cruces(t1, lat1, True), ultimo1) - ultimo1
    # Panel 4: A, con el tiempo corrido para que la subida de LAT caiga donde cae en la captura 1.
    ejes[3].plot((t5[mascara5] - referencia5 + retardo_lat) * US, a5[mascara5], color="#9467bd", linewidth=0.9)
    # Nombre del eje.
    ejes[3].set_ylabel("A (V)")
    # Título general.
    ejes[0].set_title("Secuencia al final de una ráfaga (capturas 1, 2 y 5 alineadas con el último CLK en 1)")
    # Se quita el nombre del eje de tiempo del panel de arriba...
    ejes[0].set_xlabel("")
    # ...y se pone solo en el de abajo.
    ejes[3].set_xlabel("Tiempo (µs) desde el último flanco de subida del CLK")
    # En cada panel:
    for eje in ejes:
        # línea punteada gris en el umbral de 1,65 V
        eje.axhline(UMBRAL, color="gray", linestyle=":", linewidth=0.8)
        # y cuadrícula suave.
        eje.grid(alpha=0.3)
    # Acomoda los paneles.
    figura.tight_layout()
    # Se guarda el PNG en esta carpeta.
    guardar(figura, "secuencia-de-una-fase.png", CARPETA)


# Solo se ejecuta si el archivo se corre directamente (no cuando otro programa lo importa).
if __name__ == "__main__":
    grafica_secuencia_fase()
