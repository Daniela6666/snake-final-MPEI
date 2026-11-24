# Análisis 5: LAT y A (A cambia justo después del latch)

**Qué mide:** la señal **LAT** (pin **PC7**, canal 1) y **A** (pin **PC10**, canal 2). Mide **cuánto después del pulso de LAT cambia A**.

**Por qué se mide:** el código hace, en este orden: pulso de LAT → escribir A → escribir B. Esto comprueba que **A cambia justo después del latch** y cuánto tarda, es decir, que el orden de las instrucciones del firmware es el que se ve en las señales.

**Cómo se conectó la sonda:** CH1 en PC7 (LAT) y CH2 en PC10 (A).

**Qué se concluye:**
- A cambia **1,06 µs después de que LAT sube** y **0,52 µs después de que LAT baja**: una escritura de GPIO después del pulso (el pulso de LAT dura ~0,53 µs).

**Cómo se ejecuta** (desde cualquier carpeta; solo necesita `numpy` y `matplotlib`):

```bash
python3 analizar.py
```

**Esta carpeta es independiente:** el CSV de la captura, la gráfica que se genera y el código están **juntos aquí**. Usa las herramientas de [`../comun/`](../comun/README.md) para leer el CSV, detectar flancos y guardar la gráfica. Los números que imprime son los que aparecen en el [README de las mediciones](../README.md).

**Salida real del programa** (así se ve al ejecutarlo):

```text
=== captura5-LAT-A: LAT (PC7) y A (PC10) ===
LAT sube en (µs): ['712.30']
A cambia en (µs): ['713.35']
  A cambia 1.06 µs después de que LAT sube (0.52 µs después de que LAT baja)
Ancho del pulso de LAT: ['0.53'] µs
captura5: LAT min -0.93 V, max 3.72 V; A min 0.00 V, max 4.93 V
```

### El código, trozo por trozo

**Líneas 1 a 6**

```python
#!/usr/bin/env python3
"""Captura 5: LAT (PC7) y A (PC10). Mide cuánto después del pulso de LAT cambia la dirección de fila.

Uso, desde cualquier carpeta:  python3 analizar.py
Lee captura5-LAT-A.csv (de esta carpeta) y guarda captura5-LAT-A.png aquí mismo.
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
# Herramientas de comun/medicion.py (explicadas en ../comun/README.md).
from medicion import US, cruces, primero_despues, mostrar, niveles, grafica_dos_canales, leer_csv

# CARPETA: la carpeta de este archivo; ahí están el CSV y se guarda la gráfica.
CARPETA = os.path.dirname(os.path.abspath(__file__))
```

Igual que en los otros análisis: `comun/` se agrega a la ruta de módulos (línea 14), `numpy` (línea 16) y las herramientas de [`../comun/README.md`](../comun/README.md) (línea 18). Aquí se usan `cruces`, `primero_despues`, `niveles` y `grafica_dos_canales`.
- **Línea nueva `CARPETA = os.path.dirname(os.path.abspath(__file__))`:** la carpeta **de este archivo**. Es donde están el CSV y donde se guardará la gráfica. Se pasa a `leer_csv(..., CARPETA)` y a `guardar(..., CARPETA)`; así **la carpeta es independiente**: funciona sin importar desde dónde se ejecute y sin tocar las carpetas de las demás capturas.

**Líneas 24 a 29**

```python
# Hace todo el análisis de la captura 5 (LAT y A) y guarda la gráfica.
def analizar_captura5():
    # Encabezado de esta captura en la salida.
    mostrar("captura5-LAT-A: LAT (PC7) y A (PC10)")
    # Lee el CSV (CH1 = LAT, CH2 = A).
    t, lat, a = leer_csv("captura5-LAT-A.csv", CARPETA)
```

Encabezado y lectura del CSV: `t`, `lat` (canal 1) y `a` (canal 2).

**Líneas 30 a 35**

```python
    # Instantes en que LAT sube...
    lat_subidas = cruces(t, lat, True)
    # ...y en que baja.
    lat_bajadas = cruces(t, lat, False)
    # Todos los instantes en que A cambia (subidas y bajadas juntas, ordenados).
    cambios_a = np.sort(np.concatenate([cruces(t, a, True), cruces(t, a, False)]))
```

- Líneas 31-33: flancos de subida y de bajada de LAT.
- Línea 35: **todos los cambios de A** (subidas y bajadas), juntados con `np.concatenate` y ordenados con `np.sort`. Se juntan porque A puede cambiar en cualquiera de los dos sentidos y se quiere el primer cambio sin importar cuál.

**Líneas 36 a 39**

```python
    # Imprime cuándo sube LAT.
    print("LAT sube en (µs): %s" % ["%.2f" % (x * US) for x in lat_subidas])
    # Imprime cuándo cambia A.
    print("A cambia en (µs): %s" % ["%.2f" % (x * US) for x in cambios_a])
```

Imprime los instantes en que LAT sube y en que A cambia, en µs.

**Líneas 40 a 48**

```python
    # Para cada subida de LAT:
    for subida in lat_subidas:
        # Cambios de A que ocurren después de esa subida.
        despues = cambios_a[cambios_a > subida]
        # Si hay alguno...
        if len(despues) > 0:
            # ...imprime cuánto después de que LAT sube cambia A el primero, y cuánto después de que LAT baja.
            print("  A cambia %.2f µs después de que LAT sube (%.2f µs después de que LAT baja)"
                  % ((despues[0] - subida) * US, (despues[0] - primero_despues(lat_bajadas, subida)) * US))
```

Para cada subida de LAT:
- Línea 43: `cambios_a[cambios_a > subida]` deja **los cambios de A posteriores** a esa subida.
- Línea 45: si hay alguno...
- Líneas 47-48: imprime cuánto tardó **el primero** (`despues[0]`) después de la subida de LAT (1,06 µs) y después de la **bajada** de LAT (0,52 µs; `primero_despues(lat_bajadas, subida)` es la bajada correspondiente).

**Líneas 49 a 52**

```python
    # Con dos o más pulsos de LAT se mide su periodo.
    if len(lat_subidas) >= 2:
        # Periodo de LAT = diferencia entre subidas consecutivas.
        print("Periodo de LAT: %s µs" % ["%.1f" % (d * US) for d in np.diff(lat_subidas)])
```

Si hay al menos dos pulsos de LAT, imprime el periodo entre ellos. En esta captura hay uno solo, así que no imprime nada.

**Líneas 53 a 56**

```python
    # Ancho de cada pulso de LAT: de su subida a la primera bajada posterior.
    anchos = [primero_despues(lat_bajadas, s) - s for s in lat_subidas if np.any(lat_bajadas >= s)]
    # Imprime los anchos.
    print("Ancho del pulso de LAT: %s µs" % ["%.2f" % (x * US) for x in anchos])
```

- Línea 54: ancho del pulso de LAT: para cada subida, la bajada posterior menos la subida (0,53 µs). `np.any(lat_bajadas >= s)` comprueba que exista esa bajada.
- Línea 56: imprime los anchos.

**Líneas 57 a 60**

```python
    # Voltaje mínimo y máximo de cada canal.
    niveles("captura5", t, lat, a, "LAT", "A")
    # Gráfica estándar de dos paneles (LAT arriba, A abajo); la guarda en esta carpeta.
    grafica_dos_canales(CARPETA, "captura5-LAT-A.csv", "LAT y A: A cambia poco después del pulso de LAT", "LAT, PC7", "A, PC10")
```

- Línea 58: imprime los voltajes mínimo y máximo.
- Línea 60: `grafica_dos_canales` dibuja los dos canales y guarda `captura5-LAT-A.png` en esta carpeta.

**Líneas 63 a 65**

```python
# Solo se ejecuta si el archivo se corre directamente (no cuando otro programa lo importa).
if __name__ == "__main__":
    analizar_captura5()
```

Se ejecuta `analizar_captura5()` solo cuando el archivo se corre directamente.

