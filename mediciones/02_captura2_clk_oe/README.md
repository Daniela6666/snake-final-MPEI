# Análisis 2: CLK y OE (el panel casi siempre encendido)

**Qué mide:** la señal **CLK** (PC8, canal 1) y **OE** (*output enable*, pin **PC6**, canal 2). Mide **cuándo sube y baja OE** respecto al último pulso de CLK y qué fracción del tiempo está en alto.

**Por qué se mide:** OE es **activo en bajo**: con OE en bajo el panel **está encendido** y con OE en alto **está apagado**. El código apaga el panel (OE alto) solo mientras cambia el latch y la fila (`dibujar_fase`). Si OE estuviera en alto mucho tiempo, el panel se vería **tenue**; esta captura mide cuánto está realmente apagado.

**Cómo se conectó la sonda:** CH1 en PC8 (CLK) y CH2 en PC6 (OE).

**Qué se concluye:**
- OE solo sube **~2,5 µs por fase** y está en alto el **0,26 %** de la ventana: el panel está **encendido ~99,7 % del tiempo**.
- OE sube **~1,3 µs después del último pulso de CLK** y baja **3,9 µs** después: es justo la secuencia de `dibujar_fase` (desplazar los bits → apagar OE → pulso de LAT → cambiar A y B → encender OE).

**Cómo se ejecuta** (desde cualquier carpeta; solo necesita `numpy` y `matplotlib`):

```bash
python3 analizar.py
```

**Esta carpeta es independiente:** el CSV de la captura, la gráfica que se genera y el código están **juntos aquí**. Usa las herramientas de [`../comun/`](../comun/README.md) para leer el CSV, detectar flancos y guardar la gráfica. Los números que imprime son los que aparecen en el [README de las mediciones](../README.md).

**Salida real del programa** (así se ve al ejecutarlo):

```text
=== captura2-CLK-OE: CLK (PC8) y OE (PC6) ===
Flancos de subida de OE: 2, de bajada: 2
Ráfagas: [128, 128] pulsos
  OE sube 1.38 µs después del último CLK; OE baja 3.92 µs después del último CLK (OE alto 2.54 µs)
  OE sube 1.29 µs después del último CLK; OE baja 3.92 µs después del último CLK (OE alto 2.63 µs)
Fracción de la ventana con OE en alto: 0.26 %
captura2: CLK min -0.77 V, max 5.13 V; OE min -0.44 V, max 4.89 V
```

### El código, trozo por trozo

**Líneas 1 a 6**

```python
#!/usr/bin/env python3
"""Captura 2: CLK (PC8) y OE (PC6). Mide cuándo sube y baja OE respecto al último pulso de CLK.

Uso, desde cualquier carpeta:  python3 analizar.py
Lee captura2-CLK-OE.csv (de esta carpeta) y guarda captura2-CLK-OE.png aquí mismo.
"""
```

Línea de ejecución y *docstring* (qué hace y cómo se usa).

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
from medicion import US, UMBRAL, cruces, rafagas, ultimo_antes, primero_despues, mostrar, niveles, grafica_dos_canales, leer_csv

# CARPETA: la carpeta de este archivo; ahí están el CSV y se guarda la gráfica.
CARPETA = os.path.dirname(os.path.abspath(__file__))
```

Igual que en el análisis 01: se agrega `comun/` a la ruta de módulos (línea 14), se importa `numpy` (línea 16) y se importan las herramientas de [`../comun/README.md`](../comun/README.md). Aquí además se usan `ultimo_antes`, `primero_despues` y `grafica_dos_canales`.
- **Línea nueva `CARPETA = os.path.dirname(os.path.abspath(__file__))`:** la carpeta **de este archivo**. Es donde están el CSV y donde se guardará la gráfica. Se pasa a `leer_csv(..., CARPETA)` y a `guardar(..., CARPETA)`; así **la carpeta es independiente**: funciona sin importar desde dónde se ejecute y sin tocar las carpetas de las demás capturas.

**Líneas 24 a 29**

```python
# Hace todo el análisis de la captura 2 (CLK y OE) y guarda la gráfica.
def analizar_captura2():
    # Encabezado de esta captura en la salida.
    mostrar("captura2-CLK-OE: CLK (PC8) y OE (PC6)")
    # Lee el CSV (CH1 = CLK, CH2 = OE).
    t, clk, oe = leer_csv("captura2-CLK-OE.csv", CARPETA)
```

Encabezado y lectura del CSV: `t`, `clk` (canal 1) y `oe` (canal 2).

**Líneas 30 a 41**

```python
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
```

- Línea 31: flancos de subida de CLK. Líneas 33-35: flancos de subida y de bajada de OE (OE sube = el panel **se apaga**; OE baja = **se enciende**).
- Línea 37: imprime cuántos flancos tiene OE (2 y 2: dos fases en la ventana).
- Líneas 39-41: agrupa los pulsos de CLK en ráfagas e imprime sus tamaños: `[128, 128]`, dos ráfagas completas.

**Líneas 42 a 55**

```python
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
```

Para cada vez que OE sube:
- Línea 45: `ultimo_antes(subidas, subida)` busca **el último pulso de CLK anterior a ese flanco de OE**.
- Línea 47: busca el flanco de bajada de OE posterior (el panel se vuelve a encender). `... if np.any(oe_bajadas >= subida) else None` evita un error si la captura termina antes de que OE baje.
- Línea 49: `texto` = cuánto **después del último CLK** sube OE (1,38 µs y 1,29 µs).
- Líneas 51-53: si hay bajada, agrega cuándo baja (3,92 µs después del último CLK) y cuánto estuvo OE en alto (2,5 µs).
- Línea 55: imprime la línea.

**Líneas 56 a 59**

```python
    # Máscara verdadero/falso: una muestra de OE es «alto» si pasa de 1,65 V.
    nivel_alto = oe > UMBRAL
    # Porcentaje de la ventana con OE en alto (el promedio de la máscara): el tiempo con el panel apagado.
    print("Fracción de la ventana con OE en alto: %.2f %%" % (100.0 * nivel_alto.mean()))
```

- Línea 57: `oe > UMBRAL` da un arreglo de verdadero/falso, una entrada por muestra: verdadero si OE está en alto.
- Línea 59: `.mean()` calcula la **fracción de verdaderos** (verdadero cuenta 1, falso 0). Multiplicada por 100 da el porcentaje: **0,26 %**. El resto del tiempo (99,74 %) OE está en bajo = panel encendido.

**Líneas 60 a 63**

```python
    # Voltaje mínimo y máximo de cada canal.
    niveles("captura2", t, clk, oe, "CLK", "OE")
    # Gráfica estándar de dos paneles (CLK arriba, OE abajo); la guarda en esta carpeta.
    grafica_dos_canales(CARPETA, "captura2-CLK-OE.csv", "CLK y OE: OE solo sube alrededor del latch", "CLK, PC8", "OE, PC6")
```

- Línea 61: imprime los niveles mínimo y máximo de cada canal.
- Línea 63: `grafica_dos_canales` (de `comun`) dibuja los dos canales y guarda `captura2-CLK-OE.png` en esta carpeta.

**Líneas 66 a 68**

```python
# Solo se ejecuta si el archivo se corre directamente (no cuando otro programa lo importa).
if __name__ == "__main__":
    analizar_captura2()
```

Se ejecuta `analizar_captura2()` solo cuando el archivo se corre directamente.

