# Análisis 6: botón A (duración y rebote)

**Qué mide:** el voltaje del **botón A (pin PA10)** durante **una pulsación completa** (1 s de ventana): cuánto tiempo estuvo presionado y **cuánto rebotó al soltarlo**.

**Por qué se mide:** los botones son contactos mecánicos: al cerrarse o abrirse **rebotan**, es decir, el voltaje sube y baja varias veces durante unos milisegundos antes de quedar estable. Si el programa cuenta cada flanco como una pulsación, **una sola pulsación se contaría varias veces**. Esta captura **mide la duración del rebote** para decidir cuánto debe esperar el programa (el antirrebote de **30 ms** de la prueba 08).

**Cómo se conectó la sonda:** CH1 en PA10 (botón A). El botón tiene pull-up: en reposo está en **alto** (~3 V) y al presionar baja a **~0,4 V**. Ventana de 1 s, una muestra cada 50 µs.

**Qué se concluye:**
- **Al presionar:** un solo flanco de bajada limpio (a 219,3 ms).
- **Estuvo presionado:** 146,3 ms.
- **Al soltar:** sube (365,57 ms), **vuelve a bajar** (366,13 ms) y sube **definitivamente** (369,38 ms): **rebote de 3,81 ms**.
- Los 30 ms de antirrebote de la prueba 08 son **unas 8 veces el rebote medido**. Pero hay **una sola pulsación medida**; para un valor más fiable hay que repetirla varias veces.

**Cómo se ejecuta** (desde cualquier carpeta; solo necesita `numpy` y `matplotlib`):

```bash
python3 analizar.py
```

**Esta carpeta es independiente:** el CSV de la captura, la gráfica que se genera y el código están **juntos aquí**. Usa las herramientas de [`../comun/`](../comun/README.md) para leer el CSV, detectar flancos y guardar la gráfica. Los números que imprime son los que aparecen en el [README de las mediciones](../README.md).

**Salida real del programa** (así se ve al ejecutarlo):

```text
=== captura6-boton-presionar-soltar.csv: botón A (PA10) ===
Intervalo: 50.0 µs, ventana: 1.000 s
Reposo (primeros 100 ms): mediana 3.03 V
Flancos de bajada (ms): ['219.285', '366.134']
Flancos de subida (ms): ['365.570', '369.378']
Nivel bajo mediano mientras está presionado: 0.36 V
Presionado desde el primer flanco de bajada hasta la primera subida: 146.3 ms
Último flanco de subida menos primera bajada: 150.1 ms
Rebote al soltar: de la primera subida a la última subida: 3.81 ms
Voltaje mínimo 0.34 V, máximo 3.07 V
```

### El código, trozo por trozo

**Líneas 1 a 6**

```python
#!/usr/bin/env python3
"""Captura 6: botón A (PA10) al presionar y soltar. Mide cuánto dura la pulsación y el rebote al soltar.

Uso, desde cualquier carpeta:  python3 analizar.py
Lee captura6-boton-presionar-soltar.csv (de esta carpeta) y guarda captura6-boton-presionar-soltar.png aquí mismo.
"""
```

Línea de ejecución y *docstring*.

**Líneas 8 a 21**

```python
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
```

Igual que en los otros análisis: `comun/` se agrega a la ruta de módulos (línea 14), `numpy` (línea 16) y las herramientas de [`../comun/README.md`](../comun/README.md) (línea 18). Aquí ya no se importa `CARPETA_CSV`: el CSV se lee de la carpeta de este archivo.
- **Línea nueva `CARPETA = os.path.dirname(os.path.abspath(__file__))`:** la carpeta **de este archivo**. Es donde están el CSV y donde se guardará la gráfica. Se pasa a `leer_csv(..., CARPETA)` y a `guardar(..., CARPETA)`; así **la carpeta es independiente**: funciona sin importar desde dónde se ejecute y sin tocar las carpetas de las demás capturas.

**Líneas 24 a 29**

```python
# Analiza la captura del botón A. Los parámetros tienen valor por defecto: el archivo de esta carpeta, y graficar=True.
def analizar_captura6(nombre="captura6-boton-presionar-soltar.csv", carpeta=CARPETA, graficar=True):
    # Encabezado de esta captura en la salida.
    mostrar(nombre + ": botón A (PA10)")
    # Lee el CSV; el segundo canal no se usa (por eso se llama _).
    t, boton, _ = leer_csv(nombre, carpeta)
```

- Línea 25: la función recibe el **nombre del CSV** (por defecto el de esta captura), la **carpeta** y si se debe **dibujar** la gráfica. Esos parámetros permiten reutilizarla con otra captura del botón sin cambiar el código.
- Línea 27: encabezado.
- Línea 29: lee el CSV. `t, boton, _`: el canal 2 no se usa y se descarta con el nombre `_`.

**Líneas 30 a 33**

```python
    # Intervalo entre muestras (µs) y duración total (s).
    print("Intervalo: %.1f µs, ventana: %.3f s" % ((t[1] - t[0]) * 1e6, t[-1]))
    # Nivel en reposo: la mediana de los primeros 100 ms (el botón suelto da ~3,3 V por el pull-up).
    print("Reposo (primeros 100 ms): mediana %.2f V" % np.median(boton[t < 0.1]))
```

- Línea 31: intervalo entre muestras (50 µs; `t[1] - t[0]` × 1e6) y duración (1 s).
- Línea 33: `boton[t < 0.1]` selecciona solo las muestras de los **primeros 100 ms** (antes de presionar); la mediana es el **nivel de reposo**: 3,03 V (alto, por el pull-up).

**Líneas 34 a 41**

```python
    # Instantes en que el botón baja (se presiona)...
    bajadas = cruces(t, boton, False)
    # ...y en que sube (se suelta; con rebote puede haber varios).
    subidas = cruces(t, boton, True)
    # Imprime los flancos de bajada (ms).
    print("Flancos de bajada (ms): %s" % ["%.3f" % (x * 1e3) for x in bajadas])
    # Imprime los flancos de subida (ms).
    print("Flancos de subida (ms): %s" % ["%.3f" % (x * 1e3) for x in subidas])
```

- Líneas 35-37: flancos de **bajada** y de **subida** del botón. Cuando se presiona el voltaje **baja**; cuando se suelta, **sube**.
- Líneas 39-41: los imprime en milisegundos (`x * 1e3`): bajadas en 219,285 y 366,134 ms; subidas en 365,570 y 369,378 ms.

**Líneas 42 a 53**

```python
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
```

Solo si hubo al menos una bajada y una subida:
- Línea 45: `presionado` = voltajes desde **10 ms después** de la primera bajada hasta **10 ms antes** de la primera subida. Se dejan 10 ms de margen para no incluir los flancos.
- Líneas 47-49: si hay muestras, imprime la **mediana** de ese tramo: el **nivel bajo mientras está presionado** (0,36 V; no llega exactamente a 0).
- Líneas 51-53: si no hay muestras, imprime una línea en blanco.

**Líneas 54 a 61**

```python
        # Duración de la pulsación: de la primera bajada a la primera subida.
        print("Presionado desde el primer flanco de bajada hasta la primera subida: %.1f ms" % ((subidas[0] - bajadas[0]) * 1e3))
        # Del primer flanco de bajada al último de subida (incluye el rebote).
        print("Último flanco de subida menos primera bajada: %.1f ms" % ((subidas[-1] - bajadas[0]) * 1e3))
        # Si hubo más de una subida, hubo rebote al soltar:
        if len(subidas) > 1:
            # Duración del rebote: de la primera a la última subida.
            print("Rebote al soltar: de la primera subida a la última subida: %.2f ms" % ((subidas[-1] - subidas[0]) * 1e3))
```

- Línea 55: **tiempo presionado** = primera subida − primera bajada = **146,3 ms**.
- Línea 57: última subida − primera bajada = 150,1 ms (incluye el rebote).
- Líneas 59-61: si hay más de una subida, **el rebote al soltar** = última subida − primera subida = **3,81 ms**. Ese es el tiempo durante el cual el voltaje no se estabiliza.

**Líneas 62 a 63**

```python
    # Voltaje mínimo y máximo.
    print("Voltaje mínimo %.2f V, máximo %.2f V" % (boton.min(), boton.max()))
```

Imprime los voltajes mínimo y máximo de toda la captura.

**Líneas 64 a 77**

```python
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
```

Si se pidió graficar (`graficar=True`):
- Línea 67: dos paneles **independientes** (no comparten eje: arriba la pulsación completa y abajo el acercamiento).
- Líneas 69-77: **arriba**, todo el segundo en ms: nombre de ejes, título y cuadrícula.

**Líneas 78 a 87**

```python
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
```

**Abajo, el acercamiento al rebote:**
- Líneas 79-81: si hay una subida, se centra en la **primera** (`centro`).
- Línea 83: `mascara` = muestras de **3 ms antes a 8 ms después** de esa subida.
- Línea 85: dibuja solo esas muestras, con un **punto** en cada una (`marker=".", markersize=3`) para **ver cada muestra** y distinguir el rebote.
- Línea 87: título.

**Líneas 88 a 97**

```python
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
```

Ejes, cuadrícula, `tight_layout()` (acomoda los paneles para que no se encimen los textos) y guardado en `captura6-boton-presionar-soltar.png` (en esta carpeta).

**Líneas 100 a 102**

```python
# Solo se ejecuta si el archivo se corre directamente (no cuando otro programa lo importa).
if __name__ == "__main__":
    analizar_captura6()
```

Se ejecuta `analizar_captura6()` solo cuando el archivo se corre directamente.

