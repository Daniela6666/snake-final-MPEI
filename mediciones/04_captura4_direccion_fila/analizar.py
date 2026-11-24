#!/usr/bin/env python3
"""Captura 4: dirección de fila (A en PC10 y B en PC11). Reconstruye la cuenta de fases 0, 1, 2, 3.

Uso, desde cualquier carpeta:  python3 analizar.py
Lee captura4-A-B.csv y captura4-A-B-anterior.csv (de esta carpeta) y guarda sus gráficas aquí mismo.
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
from medicion import US, UMBRAL, cruces, mostrar, guardar, niveles, leer_csv, plt

# CARPETA: la carpeta de este archivo; ahí están el CSV y se guarda la gráfica.
CARPETA = os.path.dirname(os.path.abspath(__file__))


# Convierte el CSV en una lista de «estados» (valor de los dos canales) con el tiempo en que empieza y termina cada uno.
def estados_ab(nombre):
    # Lee el CSV (CH1 y CH2).
    t, a, b = leer_csv(nombre, CARPETA)
    # Nivel digital de CH1: 1 si pasa de 1,65 V, 0 si no (astype(int) convierte verdadero/falso en 1/0)...
    nivel_a = (a > UMBRAL).astype(int)
    # ...y de CH2.
    nivel_b = (b > UMBRAL).astype(int)
    # Lista de estados; cada elemento es [estado, tiempo de inicio, tiempo de fin].
    estados = []
    # Se recorren todas las muestras.
    for indice in range(len(t)):
        # Estado de esta muestra: la pareja (nivel de CH1, nivel de CH2).
        estado = (nivel_a[indice], nivel_b[indice])
        # Si es la primera muestra o el estado cambió respecto al anterior...
        if len(estados) == 0 or estados[-1][0] != estado:
            # ...se abre un estado nuevo que empieza y termina en esta muestra.
            estados.append([estado, t[indice], t[indice]])
        # Si no cambió...
        else:
            # ...se extiende el fin del estado actual hasta esta muestra.
            estados[-1][2] = t[indice]
    # Devuelve los tiempos, los canales y la lista de estados.
    return t, a, b, estados


# Analiza un archivo de la captura 4 (dirección de fila A y B) y guarda su gráfica.
def analizar_captura4(nombre):
    """Analiza A y B. Las etiquetas del LEEME original (CH1 = A, CH2 = B) se contradicen con dibujar_fase;
    aquí se prueba la deducción contraria: CH1 en PC11 (B) y CH2 en PC10 (A)."""
    # Encabezado de esta captura en la salida.
    mostrar(nombre + ": CH1 y CH2 (dirección de fila)")
    # Lee el CSV y arma la lista de estados.
    t, canal1, canal2, estados = estados_ab(nombre)
    # Intervalo entre muestras (s).
    paso = t[1] - t[0]
    # Imprime el intervalo (ns) y la duración total (ms).
    print("Intervalo: %.1f ns, ventana: %.2f ms" % (paso * 1e9, t[-1] * 1e3))
    # Encabezado de la lista de estados.
    print("Estados (CH1, CH2) en orden, con su duración:")
    # Para cada estado: su valor, cuándo empieza y cuándo termina.
    for estado, inicio, fin in estados:
        # Imprime el estado y su duración (la última muestra dura un intervalo más).
        print("  CH1=%d CH2=%d  desde %.1f µs, duración %.2f µs" % (estado[0], estado[1], inicio * US, (fin - inicio + paso) * US))
    # Estados «permanentes»: los que duran más de 50 µs (los demás son transiciones entre fases).
    permanentes = [e for e in estados if (e[2] - e[1]) > 50e-6]
    # Deducción: CH2 = A (bit 0 de la fase) y CH1 = B (bit 1 de la fase).
    # Deducción: CH2 = A (bit 0 de la fase) y CH1 = B (bit 1 de la fase).
    # Número de fase de cada estado permanente: A + 2·B.
    valores_fase = [int(e[0][1] + 2 * e[0][0]) for e in permanentes]
    # Imprime las fases en orden.
    print("Estados que duran más de 50 µs, con CH2 = A (bit 0) y CH1 = B (bit 1): fase = %s" % valores_fase)
    # Comprueba que cada fase es la anterior más 1 (módulo 4: después de la 3 viene la 0).
    siguiente = [(valores_fase[i] + 1) % 4 == valores_fase[i + 1] for i in range(len(valores_fase) - 1)]
    # Imprime esa comprobación (True/False por cada paso).
    print("¿Cada fase es la anterior más 1 (como cuenta fase_actual en panel.c)? %s" % siguiente)
    # Lo mismo con la asignación contraria (CH1 = A, CH2 = B), para comparar.
    valores_inversos = [int(e[0][0] + 2 * e[0][1]) for e in permanentes]
    # Imprime la cuenta contraria: si no cuenta de 1 en 1, esa asignación no es la correcta.
    print("Con la asignación contraria (CH1 = A, CH2 = B): fase = %s (no cuenta de 1 en 1)" % valores_inversos)
    # Instantes en que cambia CH1 (subidas y bajadas, ordenados).
    cambios1 = np.sort(np.concatenate([cruces(t, canal1, True), cruces(t, canal1, False)]))
    # Instantes en que cambia CH2.
    cambios2 = np.sort(np.concatenate([cruces(t, canal2, True), cruces(t, canal2, False)]))
    # Imprime los instantes de cambio de CH1 (µs).
    print("Instantes de cambio de CH1 (µs): %s" % ["%.2f" % (x * US) for x in cambios1])
    # Imprime los de CH2.
    print("Instantes de cambio de CH2 (µs): %s" % ["%.2f" % (x * US) for x in cambios2])
    # Para cada cambio de CH1...
    for instante1 in cambios1:
        # ...busca los cambios de CH2 a menos de 5 µs (son de la misma transición de fase)...
        cercanos = cambios2[np.abs(cambios2 - instante1) < 5e-6]
        # ...y si hay,
        if len(cercanos) > 0:
            # imprime cuánto después o antes cambia CH1 respecto a CH2 (el signo + indica que CH1 cambia después).
            print("  Cambian en la misma transición de fase: CH2 en %.2f µs, CH1 en %.2f µs (CH1 menos CH2 = %+.2f µs)"
                  % (cercanos[0] * US, instante1 * US, (instante1 - cercanos[0]) * US))
    # Conclusión que sale del código del firmware: dibujar_fase escribe A y después B.
    print("  dibujar_fase escribe A y después B, con ~0,5 µs entre escrituras (ancho de CLK y de LAT): CH2 = A y CH1 = B.")
    # Voltaje mínimo y máximo de cada canal.
    niveles(nombre, t, canal1, canal2, "CH1", "CH2")

    # Gráfica: 2 paneles apilados que comparten el eje del tiempo.
    figura, ejes = plt.subplots(2, 1, sharex=True, figsize=(10, 4.5))
    # Panel de arriba: A (CH2, deducido) en azul.
    ejes[0].plot(t * US, canal2, color="#1f77b4", linewidth=0.8)
    ejes[0].set_ylabel("A, PC10 (V)\n(CH2, deducido)")
    # Panel de abajo: B (CH1, deducido) en rojo.
    ejes[1].plot(t * US, canal1, color="#d62728", linewidth=0.8)
    ejes[1].set_ylabel("B, PC11 (V)\n(CH1, deducido)")
    ejes[1].set_xlabel("Tiempo (µs)")
    for eje in ejes:
        eje.axhline(UMBRAL, color="gray", linestyle=":", linewidth=0.8)
        eje.grid(alpha=0.3)
    ejes[0].set_title("Dirección de fila (A y B): " + nombre.replace(".csv", ""))
    guardar(figura, nombre.replace(".csv", ".png"), CARPETA)


# Solo se ejecuta si el archivo se corre directamente (no cuando otro programa lo importa).
if __name__ == "__main__":
    analizar_captura4("captura4-A-B.csv")
    analizar_captura4("captura4-A-B-anterior.csv")
