#!/usr/bin/env python3
"""Captura 6: botón A (PA10) al presionar y soltar. Mide cuánto dura la pulsación y el rebote al soltar.

Uso, desde cualquier carpeta:  python3 analizar.py
Lee captura6-boton-presionar-soltar.csv (de esta carpeta) y guarda captura6-boton-presionar-soltar.png aquí mismo.
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
from medicion import cruces, mostrar, guardar, leer_csv, plt

# CARPETA: la carpeta de este archivo; ahí están el CSV y se guarda la gráfica.
CARPETA = os.path.dirname(os.path.abspath(__file__))


# Analiza la captura del botón A. Los parámetros tienen valor por defecto: el archivo de esta carpeta, y graficar=True.
def analizar_captura6(nombre="captura6-boton-presionar-soltar.csv", carpeta=CARPETA, graficar=True):
    # Encabezado de esta captura en la salida.
    mostrar(nombre + ": botón A (PA10)")
    # Lee el CSV; el segundo canal no se usa (por eso se llama _).
    t, boton, _ = leer_csv(nombre, carpeta)
    # Intervalo entre muestras (µs) y duración total (s).
    print("Intervalo: %.1f µs, ventana: %.3f s" % ((t[1] - t[0]) * 1e6, t[-1]))
    # Nivel en reposo: la mediana de los primeros 100 ms (el botón suelto da ~3,3 V por el pull-up).
    print("Reposo (primeros 100 ms): mediana %.2f V" % np.median(boton[t < 0.1]))
    # Instantes en que el botón baja (se presiona)...
    bajadas = cruces(t, boton, False)
    # ...y en que sube (se suelta; con rebote puede haber varios).
    subidas = cruces(t, boton, True)
    # Imprime los flancos de bajada (ms).
    print("Flancos de bajada (ms): %s" % ["%.3f" % (x * 1e3) for x in bajadas])
    # Imprime los flancos de subida (ms).
    print("Flancos de subida (ms): %s" % ["%.3f" % (x * 1e3) for x in subidas])
    # Si hubo al menos una bajada y una subida...
    if len(bajadas) > 0 and len(subidas) > 0:
        # ...se toman las muestras entre ellas, con 10 ms de margen en cada lado para evitar los flancos.
        presionado = boton[(t > bajadas[0] + 0.01) & (t < subidas[0] - 0.01)]
        # Si hay muestras...
        if len(presionado) > 0:
            # ...se imprime el nivel bajo típico mientras está presionado.
            print("Nivel bajo mediano mientras está presionado: %.2f V" % np.median(presionado))
        # Si no...
        else:
            # ...se imprime una línea vacía.
            print("")
        # Duración de la pulsación: de la primera bajada a la primera subida.
        print("Presionado desde el primer flanco de bajada hasta la primera subida: %.1f ms" % ((subidas[0] - bajadas[0]) * 1e3))
        # Del primer flanco de bajada al último de subida (incluye el rebote).
        print("Último flanco de subida menos primera bajada: %.1f ms" % ((subidas[-1] - bajadas[0]) * 1e3))
        # Si hubo más de una subida, hubo rebote al soltar:
        if len(subidas) > 1:
            # Duración del rebote: de la primera a la última subida.
            print("Rebote al soltar: de la primera subida a la última subida: %.2f ms" % ((subidas[-1] - subidas[0]) * 1e3))
    # Voltaje mínimo y máximo.
    print("Voltaje mínimo %.2f V, máximo %.2f V" % (boton.min(), boton.max()))
    # Solo se dibuja si graficar es verdadero.
    if graficar:
        # Figura de 2 paneles: arriba la pulsación completa, abajo un acercamiento.
        figura, ejes = plt.subplots(2, 1, figsize=(10, 5))
        # Panel de arriba: la señal completa (tiempo en ms).
        ejes[0].plot(t * 1e3, boton, color="#1f77b4", linewidth=0.8)
        # Nombre del eje del tiempo.
        ejes[0].set_xlabel("Tiempo (ms)")
        # Nombre del eje de voltaje.
        ejes[0].set_ylabel("PA10 (V)")
        # Título.
        ejes[0].set_title("Botón A: pulsación completa")
        # Cuadrícula suave.
        ejes[0].grid(alpha=0.3)
        # Si hubo subida, se hace el acercamiento al soltar:
        if len(subidas) > 0:
            # Centro del acercamiento: la primera subida.
            centro = subidas[0]
            # Ventana: 3 ms antes y 8 ms después.
            mascara = (t > centro - 3e-3) & (t < centro + 8e-3)
            # Panel de abajo: solo esa ventana, con un punto por muestra para ver el rebote.
            ejes[1].plot(t[mascara] * 1e3, boton[mascara], color="#d62728", linewidth=0.9, marker=".", markersize=3)
            # Título del acercamiento.
            ejes[1].set_title("Acercamiento al soltar (rebote)")
        # Nombre del eje del tiempo.
        ejes[1].set_xlabel("Tiempo (ms)")
        # Nombre del eje de voltaje.
        ejes[1].set_ylabel("PA10 (V)")
        # Cuadrícula suave.
        ejes[1].grid(alpha=0.3)
        # Acomoda los paneles para que no se encimen los textos.
        figura.tight_layout()
        # Se guarda el PNG en esta carpeta.
        guardar(figura, "captura6-boton-presionar-soltar.png", CARPETA)


# Solo se ejecuta si el archivo se corre directamente (no cuando otro programa lo importa).
if __name__ == "__main__":
    analizar_captura6()
