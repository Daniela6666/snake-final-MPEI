"""Herramientas comunes para analizar los CSV del osciloscopio (Hantek 6022BE).

No se ejecuta solo: lo importan los programas de las carpetas 01 a 07.
Lee el CSV de la carpeta de cada captura, detecta flancos y ráfagas, y guarda
la gráfica PNG en esa misma carpeta. Requiere numpy y matplotlib.
"""

import os
# numpy: operaciones sobre miles de muestras a la vez, sin bucles.
import numpy as np
# matplotlib: librería de gráficas.
import matplotlib

# Modo «Agg»: dibuja directo a archivo sin abrir ventana (sirve en un servidor o Codespace). Debe ir antes de importar pyplot.
matplotlib.use("Agg")  # dibuja sin abrir ventana: solo se guardan PNG
# pyplot: la interfaz para crear figuras.
import matplotlib.pyplot as plt

# Cada programa le pasa a estas funciones su propia carpeta (donde están su CSV y su gráfica).
# UMBRAL: nivel (V) que separa «alto» de «bajo»: la mitad de 3,3 V.
UMBRAL = 1.65  # V, mitad de 3,3 V
# US: factor para pasar segundos a microsegundos (1 s = 1 000 000 µs).
US = 1e6  # segundos a microsegundos


# Lee un CSV del osciloscopio y devuelve tres arreglos: tiempo (s), canal 1 (V) y canal 2 (V).
def leer_csv(nombre, carpeta):
    """Lee un CSV con separador ';' y coma decimal. Devuelve t, canal 1, canal 2."""
    # Ruta completa: la carpeta de la captura más el nombre del archivo.
    ruta = os.path.join(carpeta, nombre)
    # Aquí se acumularán las filas numéricas.
    datos = []
    # utf-8-sig descarta el BOM (marca invisible al inicio del archivo que ponen Excel y otros programas).
    with open(ruta, encoding="utf-8-sig") as archivo:
        # Salta la primera línea: es el encabezado, no son números.
        next(archivo)  # encabezado
        # Para cada línea de datos:
        for linea in archivo:
            # quita el salto de línea, cambia la coma decimal por punto (Python solo entiende 0.36) y separa las 3 columnas por «;».
            partes = linea.strip().replace(",", ".").split(";")
            # Convierte cada texto en número y guarda la fila.
            datos.append([float(parte) for parte in partes])
    # Matriz de N filas × 3 columnas.
    matriz = np.array(datos)
    # Devuelve la columna 0 (tiempo), la 1 (canal 1) y la 2 (canal 2).
    return matriz[:, 0], matriz[:, 1], matriz[:, 2]


# Instantes (interpolados) en que la señal v cruza el umbral. subida=True: flancos de subida; False: de bajada.
def cruces(t, v, subida, umbral=UMBRAL):
    """Instantes (interpolados) en que v cruza el umbral. subida=True: flancos de subida."""
    # Flancos de subida:
    if subida:
        # Índices donde una muestra está por debajo del umbral y la siguiente en o por encima (v[:-1] y v[1:] forman parejas consecutivas).
        indices = np.where((v[:-1] < umbral) & (v[1:] >= umbral))[0]
    # Flancos de bajada:
    else:
        # Índices donde una muestra está en o por encima del umbral y la siguiente por debajo.
        indices = np.where((v[:-1] >= umbral) & (v[1:] < umbral))[0]
    # Interpolación lineal: qué fracción del camino entre las dos muestras se recorrió al cruzar el umbral.
    fraccion = (umbral - v[indices]) / (v[indices + 1] - v[indices])
    # Instante real del cruce: tiempo de la muestra anterior + fracción × intervalo entre muestras.
    return t[indices] + fraccion * (t[indices + 1] - t[indices])


# Agrupa flancos de subida en ráfagas: una pausa mayor que separacion_minima abre una ráfaga nueva.
def rafagas(subidas, separacion_minima):
    """Agrupa flancos de subida en ráfagas: una pausa mayor que separacion_minima abre otra."""
    # Empieza con un grupo que contiene el primer flanco.
    grupos = [[subidas[0]]]
    # Para cada flanco siguiente:
    for instante in subidas[1:]:
        # si la distancia al último flanco del último grupo es mayor que la separación mínima, hay una pausa larga...
        if instante - grupos[-1][-1] > separacion_minima:
            # ...y se abre un grupo nuevo.
            grupos.append([instante])
        # Si no...
        else:
            # ...el flanco pertenece al grupo actual.
            grupos[-1].append(instante)
    # Cada grupo se convierte en arreglo de numpy.
    return [np.array(grupo) for grupo in grupos]


# Último elemento de la lista ordenada que es menor o igual que la referencia (el flanco más cercano antes).
def ultimo_antes(instantes, referencia):
    """Último elemento de instantes que es menor o igual que referencia."""
    # La máscara deja solo los que cumplen y [-1] toma el último.
    return instantes[instantes <= referencia][-1]


# Primer elemento que es mayor o igual que la referencia (el flanco más cercano después).
def primero_despues(instantes, referencia):
    """Primer elemento de instantes que es mayor o igual que referencia."""
    # La máscara deja solo los que cumplen y [0] toma el primero.
    return instantes[instantes >= referencia][0]


# Imprime un encabezado «=== título ===» con una línea en blanco antes, para separar los resultados de cada captura.
def mostrar(titulo):
    print("\n=== " + titulo + " ===")


# Guarda la figura como PNG en la carpeta indicada (130 puntos por pulgada; bbox_inches recorta los márgenes blancos).
def guardar(figura, nombre, carpeta):
    figura.savefig(os.path.join(carpeta, nombre), dpi=130, bbox_inches="tight")
    # Libera la memoria de la figura.
    plt.close(figura)


# Imprime el mínimo y el máximo de voltaje de cada canal (los niveles reales de la señal).
def niveles(nombre, t, canal1, canal2, etiqueta1, etiqueta2):
    print("%s: %s min %.2f V, max %.2f V; %s min %.2f V, max %.2f V"
          % (nombre, etiqueta1, canal1.min(), canal1.max(), etiqueta2, canal2.min(), canal2.max()))


# Gráfica estándar: dos paneles apilados, uno por canal. Lee el CSV de la carpeta y guarda el PNG en la misma carpeta.
def grafica_dos_canales(carpeta, archivo, titulo, etiqueta1, etiqueta2, ventana_us=None, destino=None):
    # Lee el CSV.
    t, canal1, canal2 = leer_csv(archivo, carpeta)
    # 2 filas × 1 columna de ejes que comparten el eje del tiempo; figura de 10 × 4,5 pulgadas.
    figura, ejes = plt.subplots(2, 1, sharex=True, figsize=(10, 4.5))
    # Panel de arriba: canal 1 en azul (tiempo en µs).
    ejes[0].plot(t * US, canal1, color="#1f77b4", linewidth=0.8)
    # Nombre del eje vertical de arriba.
    ejes[0].set_ylabel(etiqueta1 + " (V)")
    # Panel de abajo: canal 2 en rojo.
    ejes[1].plot(t * US, canal2, color="#d62728", linewidth=0.8)
    # Nombre del eje vertical de abajo.
    ejes[1].set_ylabel(etiqueta2 + " (V)")
    # Nombre del eje del tiempo.
    ejes[1].set_xlabel("Tiempo (µs)")
    # En cada panel:
    for eje in ejes:
        # línea punteada gris en el umbral de 1,65 V
        eje.axhline(UMBRAL, color="gray", linestyle=":", linewidth=0.8)
        # y cuadrícula suave.
        eje.grid(alpha=0.3)
    # Si se pidió una ventana de tiempo...
    if ventana_us is not None:
        # ...se aplica (el * separa la pareja inicio, fin en dos argumentos).
        ejes[1].set_xlim(*ventana_us)
    # Título de la gráfica.
    ejes[0].set_title(titulo)
    # Guarda el PNG: con el nombre pedido o, si no se dio, el del CSV cambiando .csv por .png.
    guardar(figura, destino or (archivo.replace(".csv", ".png")), carpeta)
