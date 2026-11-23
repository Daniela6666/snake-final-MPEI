# Análisis 7: secuencia completa de una fase

**Qué hace:** arma **una sola gráfica** con el final de una ráfaga: CLK, LAT, OE y A, **alineadas en el tiempo**, para ver el orden en que ocurre todo. No calcula ni imprime números; solo dibuja.

**Por qué:** cada medición del osciloscopio tiene **solo dos canales**, así que no se pudieron medir CLK, LAT, OE y A a la vez. Como el firmware repite **siempre la misma secuencia** en cada fase, se pueden **medir por pares** y luego **alinear todas con un mismo punto de referencia: el último pulso de CLK**.

**De dónde salen los datos:**
- CLK y LAT: captura 1.
- OE: captura 2 (CLK y OE).
- A: captura 5 (LAT y A). Esa captura **no tiene CLK**, así que se alinea con el **retardo medido entre el último CLK y el pulso de LAT en la captura 1**.

**Límite:** las señales no se midieron a la vez, así que el alineamiento supone que la secuencia es siempre igual. Es una **reconstrucción**, no una medición simultánea.

**Qué muestra** (tiempos desde el último pulso de CLK; vienen de los análisis 1, 2, 4 y 5):

| Instante | Evento |
|---|---|
| 0 | último pulso de CLK |
| +1,3 µs | OE sube (panel apagado) |
| +1,8 µs | LAT sube (dura ~0,5 µs) |
| +2,9 µs | cambia A |
| +3,5 µs | cambia B (si la fase cambia los dos) |
| +3,9 µs | OE baja (panel encendido) |
| +208 µs | empieza la ráfaga de la fase siguiente |

El orden coincide con `dibujar_fase`: desplazar los 128 bits, apagar OE, pulso de LAT, escribir A, escribir B y encender OE.

**Cómo se ejecuta** (desde cualquier carpeta; solo necesita `numpy` y `matplotlib`):

```bash
python3 analizar.py
```

**Esta carpeta guarda aquí su gráfica**, pero **los CSV no están aquí**: los lee de las carpetas hermanas `01_captura1_clk_lat`, `02_captura2_clk_oe` y `05_captura5_lat_a` (los mismos datos que usan esos análisis; por eso no se copian). Usa las herramientas de [`../comun/`](../comun/README.md) para leer el CSV, detectar flancos y guardar la gráfica. Los números que imprime son los que aparecen en el [README de las mediciones](../README.md).

**Salida real del programa** (así se ve al ejecutarlo):

```text
(Este programa no imprime nada: solo guarda secuencia-de-una-fase.png en esta carpeta)
```

### El código, trozo por trozo

**Líneas 1 a 7**

```python
#!/usr/bin/env python3
"""Secuencia de una fase: junta CLK, LAT, OE y A (capturas 1, 2 y 5) alineados con el último pulso de CLK.

Uso, desde cualquier carpeta:  python3 analizar.py
Lee los CSV de las carpetas 01, 02 y 05 y guarda secuencia-de-una-fase.png en esta carpeta.
No imprime números.
"""
```

Línea de ejecución y *docstring* (qué capturas usa y que no imprime números).

**Líneas 9 a 27**

```python
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
```

Igual que en los otros análisis: `comun/` se agrega a la ruta de módulos (línea 15) y se importan las herramientas de [`../comun/README.md`](../comun/README.md) (línea 17). Aquí no hace falta `numpy` porque no se calcula nada con arreglos aparte de las herramientas.
- **Líneas nuevas:** `CARPETA` es la carpeta de este archivo (donde se guarda la gráfica). `CAPTURA1`, `CAPTURA2` y `CAPTURA5` son las **carpetas hermanas** de las capturas 1, 2 y 5, que es donde están los CSV que usa esta gráfica (`os.path.dirname(CARPETA)` sube un nivel a `mediciones/`). Cada `leer_csv(..., CAPTURAn)` lee de la carpeta que le corresponde.

**Líneas 30 a 40**

```python
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
```

- Línea 31: toda la gráfica está en una función. Línea 32: su texto de ayuda.
- Líneas 34-38: lee las tres capturas: 1 (CLK y LAT), 2 (CLK y OE) y 5 (LAT y A). Cada una tiene su propio arreglo de tiempos (`t1`, `t2`, `t5`).
- Línea 40: una figura con **4 paneles apilados** (CLK, LAT, OE, A). `sharex=False` porque cada captura tiene su propia escala de tiempo; se alinean a mano restando una referencia.

**Líneas 41 a 57**

```python
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
```

**Paneles de CLK y LAT (captura 1):**
- Línea 41: comentario de cómo se alinea todo: con el último flanco de subida de CLK.
- Líneas 43-47: `subidas1` son las subidas de CLK, `grupos1` las ráfagas y `ultimo1` es **el último pulso de la primera ráfaga**: la referencia, tiempo 0.
- Línea 49: `mascara1` deja solo las muestras entre **12 µs antes y 12 µs después** de la referencia.
- Líneas 51-57: se dibujan CLK y LAT con el tiempo **restado de la referencia** (`t1[mascara1] - ultimo1`) y pasado a µs. Así el último pulso de CLK queda en 0.

**Líneas 58 a 69**

```python
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
```

**Panel de OE (captura 2):** el mismo procedimiento: `ultimo2` es el último pulso de CLK de la primera ráfaga de la captura 2 (tiempo 0), se recorta la ventana de ±12 µs y se dibuja OE (verde) con el tiempo restado de esa referencia.

**Líneas 70 a 82**

```python
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
```

**Panel de A (captura 5):**
- Líneas 71-73: `referencia5` = el instante en que **LAT sube** en la captura 5.
- Línea 75: ventana de ±12 µs alrededor.
- Línea 76: comentario: la captura 5 no tiene CLK, así que hay que **calcular cuándo, respecto al último CLK, sube LAT**.
- Línea 78: `retardo_lat` = (primera subida de LAT **después** del último CLK, en la captura 1) − (último CLK). Es el retardo entre el último pulso de CLK y LAT.
- Línea 80: se dibuja A con el tiempo `t5 − referencia5 + retardo_lat`: se pone el instante de LAT de la captura 5 **en el mismo lugar donde LAT sube en la captura 1**, y así A queda alineada con las otras señales.
- Línea 82: etiqueta.

**Líneas 83 a 98**

```python
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
```

- Línea 84: título general. Línea 86: quita la etiqueta del eje de tiempo del panel de arriba; línea 88 pone la etiqueta solo al panel de abajo: «Tiempo (µs) desde el último flanco de subida del CLK».
- Líneas 90-94: en cada panel, la línea del umbral y la cuadrícula.
- Línea 96: `tight_layout()` acomoda los paneles. Línea 98: guarda `secuencia-de-una-fase.png` en esta carpeta.

**Líneas 101 a 103**

```python
# Solo se ejecuta si el archivo se corre directamente (no cuando otro programa lo importa).
if __name__ == "__main__":
    grafica_secuencia_fase()
```

Se ejecuta `grafica_secuencia_fase()` solo cuando el archivo se corre directamente.

