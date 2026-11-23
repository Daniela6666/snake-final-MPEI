# Análisis 3: CLK y R1 (el dato es estable en el flanco)

**Qué mide:** la señal **CLK** (PC8, canal 1) y **R1** (el dato rojo de la mitad superior, pin **PC0**, canal 2). Lee **los 128 bits** que viajan por R1 en una ráfaga y mide **cuánto después de cada flanco de CLK cambia el dato**.

**Por qué se mide:** el panel lee el dato **en el flanco de subida de CLK**. Para que lea bien, el dato **tiene que estar estable justo en ese instante**; si cambiara a la vez que CLK, el panel podría leer el bit viejo o el nuevo. Esta captura lo comprueba y, de paso, deja ver **el patrón de bits** que el juego estaba enviando.

**Cómo se conectó la sonda:** CH1 en PC8 (CLK) y CH2 en PC0 (R1). Ventana de 1,33 ms, 20 000 muestras (una cada 66,7 ns).

**Qué se concluye:**
- R1 vale **lo mismo antes y después del flanco** en los **128 de 128 pulsos**: el dato es estable cuando el panel lo lee.
- R1 cambia **~3 µs después** de la subida anterior de CLK (de 2,92 a 3,08 µs): a mitad del periodo, lejos del flanco que lo lee.
- R1 está en alto en **32 de los 128 bits**. El patrón `1010101001010101` se repite 4 veces y luego hay 64 ceros: se interpreta como un dibujo con rojo solo en el panel 2 en esa fase (**no verificado**).
- El periodo entre pulsos es de 6,34 µs, mayor que los 6,1 µs de la captura 1. Con más bits en 1 el periodo sube (no se verificó la causa).

**Cómo se ejecuta** (desde cualquier carpeta; solo necesita `numpy` y `matplotlib`):

```bash
python3 analizar.py
```

**Esta carpeta es independiente:** el CSV de la captura, la gráfica que se genera y el código están **juntos aquí**. Usa las herramientas de [`../comun/`](../comun/README.md) para leer el CSV, detectar flancos y guardar la gráfica. Los números que imprime son los que aparecen en el [README de las mediciones](../README.md).

**Salida real del programa** (así se ve al ejecutarlo):

```text
=== captura3-CLK-R1: CLK (PC8) y R1 (PC0) ===
Intervalo: 66.7 ns, ventana: 1.33 ms
Ráfagas: [128, 55] pulsos
Periodo entre pulsos en la ráfaga completa: mediana 6.34 µs, min 6.26, max 6.41
Pulsos con periodo entre 6,1 y 6,4 µs: 127 de 127
R1 en alto en 32 de 128 pulsos (medido 3 muestras antes del flanco)
R1 igual antes y después del flanco en 128 de 128 pulsos
Cambios de R1 entre pulsos consecutivos: 57
Bits de R1 (primer pulso a la izquierda):
    0 a  15: 1010101001010101
   16 a  31: 1010101001010101
   32 a  47: 1010101001010101
   48 a  63: 1010101001010101
   64 a  79: 0000000000000000
   80 a  95: 0000000000000000
   96 a 111: 0000000000000000
  112 a 127: 0000000000000000
R1 cambia 2.92 a 3.08 µs después del flanco de subida anterior del CLK (mediana 3.01, 57 cambios)
captura3: CLK min -0.93 V, max 5.01 V; R1 min -1.25 V, max 5.13 V
```

### El código, trozo por trozo

**Líneas 1 a 6**

```python
#!/usr/bin/env python3
"""Captura 3: CLK (PC8) y R1 (PC0). Lee los 128 bits que viajan por R1 y mide cuándo cambia el dato.

Uso, desde cualquier carpeta:  python3 analizar.py
Lee captura3-CLK-R1.csv (de esta carpeta) y guarda captura3-CLK-R1.png y captura3-CLK-R1-acercamiento.png aquí mismo.
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
from medicion import US, UMBRAL, cruces, rafagas, ultimo_antes, mostrar, guardar, niveles, leer_csv, plt

# CARPETA: la carpeta de este archivo; ahí están el CSV y se guarda la gráfica.
CARPETA = os.path.dirname(os.path.abspath(__file__))
```

Igual que en los otros análisis: `comun/` se agrega a la ruta de módulos (línea 14), `numpy` (línea 16) y las herramientas de [`../comun/README.md`](../comun/README.md) (línea 18).
- **Línea nueva `CARPETA = os.path.dirname(os.path.abspath(__file__))`:** la carpeta **de este archivo**. Es donde están el CSV y donde se guardará la gráfica. Se pasa a `leer_csv(..., CARPETA)` y a `guardar(..., CARPETA)`; así **la carpeta es independiente**: funciona sin importar desde dónde se ejecute y sin tocar las carpetas de las demás capturas.

**Líneas 24 a 37**

```python
# Hace todo el análisis de la captura 3 (CLK y R1) y guarda dos gráficas.
def analizar_captura3():
    # Encabezado de esta captura en la salida.
    mostrar("captura3-CLK-R1: CLK (PC8) y R1 (PC0)")
    # Lee el CSV (CH1 = CLK, CH2 = R1, el dato rojo del panel superior).
    t, clk, r1 = leer_csv("captura3-CLK-R1.csv", CARPETA)
    # Intervalo entre muestras (ns) y duración total (ms).
    print("Intervalo: %.1f ns, ventana: %.2f ms" % ((t[1] - t[0]) * 1e9, t[-1] * 1e3))
    # Instantes en que CLK sube.
    subidas = cruces(t, clk, True)
    # Agrupa las subidas en ráfagas.
    grupos = rafagas(subidas, 20e-6)
    # Imprime los pulsos de cada ráfaga.
    print("Ráfagas: %s pulsos" % [len(g) for g in grupos])
```

- Líneas 27-29: encabezado y lectura: `t`, `clk` y `r1`.
- Línea 31: intervalo entre muestras (66,7 ns) y duración de la ventana (1,33 ms).
- Líneas 33-37: flancos de subida de CLK, agrupados en ráfagas (`[128, 55]`: una completa y una cortada por el final de la ventana).

**Líneas 38 a 47**

```python
    # Ráfagas completas: las de 128 pulsos.
    completas = [g for g in grupos if len(g) == 128]
    # Si no hay ninguna...
    if len(completas) == 0:
        # ...se avisa...
        print("No hay ráfaga completa de 128 pulsos.")
        # ...y se termina (no se puede analizar).
        return
    # Se usa la primera ráfaga completa.
    grupo = completas[0]
```

- Línea 39: `completas` = ráfagas con exactamente 128 pulsos.
- Líneas 41-45: **si no hay ninguna**, avisa y termina la función con `return` (los pasos siguientes necesitan una ráfaga completa).
- Línea 47: `grupo` = la primera ráfaga completa, que se analiza.

**Líneas 48 a 53**

```python
    # Tiempo entre pulsos consecutivos.
    periodos = np.diff(grupo)
    # Imprime el periodo típico (mediana), el menor y el mayor.
    print("Periodo entre pulsos en la ráfaga completa: mediana %.2f µs, min %.2f, max %.2f" % (np.median(periodos) * US, periodos.min() * US, periodos.max() * US))
    # Cuenta los periodos entre 6,05 y 6,45 µs.
    print("Pulsos con periodo entre 6,1 y 6,4 µs: %d de %d" % (np.sum((periodos >= 6.05e-6) & (periodos <= 6.45e-6)), len(periodos)))
```

- Línea 49: periodos entre pulsos consecutivos (`np.diff`).
- Línea 51: mediana, mínimo y máximo: **6,34 µs** (6,26 a 6,41).
- Línea 53: cuenta cuántos periodos están entre 6,05 y 6,45 µs: **127 de 127**. Es una comprobación de que el ritmo del reloj es regular, sin pulsos atrasados.

**Líneas 54 a 67**

```python
    # Listas donde se guardará el nivel de R1 justo antes y justo después de cada flanco de CLK.
    antes = []
    despues = []
    # Para cada pulso de CLK de la ráfaga:
    for subida in grupo:
        # Posición (índice) de la muestra más cercana al flanco; searchsorted busca en el arreglo ordenado de tiempos.
        indice = int(np.searchsorted(t, subida))
        # Nivel de R1 3 muestras antes del flanco (max evita salirse del arreglo por el inicio).
        antes.append(r1[max(indice - 3, 0)] > UMBRAL)
        # Nivel de R1 3 muestras después (min evita salirse por el final).
        despues.append(r1[min(indice + 3, len(r1) - 1)] > UMBRAL)
    # Se pasan las listas a arreglos de numpy para poder compararlas.
    antes = np.array(antes)
    despues = np.array(despues)
```

**Leer el valor de R1 en cada pulso:**
- Líneas 55-56: dos listas vacías: el valor de R1 **antes** y **después** del flanco.
- Línea 58: recorre cada flanco de subida de la ráfaga.
- Línea 60: `np.searchsorted(t, subida)` busca **en qué posición del arreglo de tiempos está ese instante** (la muestra que corresponde al flanco).
- Línea 62: `r1[indice - 3]` es el voltaje **3 muestras antes** del flanco (≈0,2 µs antes). `> UMBRAL` lo convierte a alto/bajo (verdadero/falso). `max(indice - 3, 0)` evita salirse del arreglo al principio.
- Línea 64: lo mismo **3 muestras después**; `min(..., len(r1) - 1)` evita salirse del arreglo al final.
- Líneas 66-67: pasan las listas a arreglos de numpy.
- **Por qué «antes»:** lo que el panel captura en el flanco es el valor **que había justo antes**, así que ese es el bit que se está enviando.

**Líneas 68 a 73**

```python
    # Cuántos pulsos tenían R1 en alto antes del flanco (es el bit que se estaba mandando).
    print("R1 en alto en %d de 128 pulsos (medido 3 muestras antes del flanco)" % antes.sum())
    # En cuántos pulsos R1 era igual antes y después: si es 128 de 128, el dato es estable alrededor del flanco.
    print("R1 igual antes y después del flanco en %d de 128 pulsos" % np.sum(antes == despues))
    # Cuántas veces R1 cambió de un pulso al siguiente (compara cada elemento con el anterior).
    print("Cambios de R1 entre pulsos consecutivos: %d" % np.sum(antes[1:] != antes[:-1]))
```

- Línea 69: cuántos bits valen 1 (`antes.sum()` suma los verdaderos): **32 de 128**.
- Línea 71: en cuántos pulsos el valor es **igual antes y después** del flanco: **128 de 128**. Es la comprobación de que **el dato no cambia en el flanco**.
- Línea 73: `antes[1:] != antes[:-1]` compara cada bit con el anterior y cuenta los cambios entre bits consecutivos (57).

**Líneas 74 a 81**

```python
    # Arma un texto de 128 caracteres, un «1» o un «0» por pulso.
    cadena = "".join("1" if bit else "0" for bit in antes)
    # Encabezado de la lista de bits.
    print("Bits de R1 (primer pulso a la izquierda):")
    # Imprime los 128 bits en 8 filas de 16...
    for inicio in range(0, 128, 16):
        # ...con el rango de pulsos al principio de cada fila.
        print("  %3d a %3d: %s" % (inicio, inicio + 15, cadena[inicio:inicio + 16]))
```

**Mostrar el patrón de bits:**
- Línea 75: arma un texto con un `"1"` o un `"0"` por pulso, en orden (el primer pulso a la izquierda).
- Líneas 77-81: lo imprime en 8 filas de 16 bits, con el rango de pulsos al principio de cada fila (`%3d` reserva 3 espacios para alinear). Se ve el patrón `1010101001010101` ×4 y 64 ceros.

**Líneas 82 a 97**

```python
    # Todos los instantes en que R1 cambia (subidas y bajadas juntas).
    cambios_r1 = np.concatenate([cruces(t, r1, True), cruces(t, r1, False)])
    # Aquí se guardará cuánto después del flanco de CLK cambia R1.
    retardos = []
    # Para cada cambio de R1...
    for cambio in cambios_r1:
        # ...dentro de la ráfaga (hasta 10 µs después del último pulso)...
        if grupo[0] <= cambio <= grupo[-1] + 10e-6:
            # ...se guarda la distancia al flanco de subida de CLK inmediatamente anterior.
            retardos.append(cambio - ultimo_antes(grupo, cambio))
    # Se pasa la lista a arreglo.
    retardos = np.array(retardos)
    # Si hubo cambios, se imprime el mínimo, el máximo y la mediana del retardo.
    if len(retardos) > 0:
        print("R1 cambia %.2f a %.2f µs después del flanco de subida anterior del CLK (mediana %.2f, %d cambios)"
              % (retardos.min() * US, retardos.max() * US, np.median(retardos) * US, len(retardos)))
```

**Cuánto después del flanco cambia el dato:**
- Línea 83: todos los instantes en que R1 cambia (de bajo a alto y de alto a bajo).
- Líneas 85-91: para cada cambio dentro de la ráfaga (hasta 10 µs después del último pulso), `ultimo_antes(grupo, cambio)` busca **la subida de CLK inmediatamente anterior** y la resta del cambio: es el **retardo**.
- Líneas 93-97: imprime el mínimo, el máximo y la mediana (2,92 a 3,08 µs; mediana 3,01 µs; 57 cambios). El dato cambia **a mitad del periodo de 6,3 µs**, lejos del flanco que lo lee.

**Líneas 98 a 99**

```python
    # Voltaje mínimo y máximo de cada canal.
    niveles("captura3", t, clk, r1, "CLK", "R1")
```

Imprime los niveles mínimo y máximo de cada canal.

**Líneas 101 a 114**

```python
    # Gráfica completa: 2 paneles apilados que comparten el eje del tiempo (CLK arriba, R1 abajo).
    figura, ejes = plt.subplots(2, 1, sharex=True, figsize=(10, 4.5))
    # Panel de arriba: CLK en azul (tiempo en µs).
    ejes[0].plot(t * US, clk, color="#1f77b4", linewidth=0.6)
    ejes[0].set_ylabel("CLK, PC8 (V)")
    # Panel de abajo: R1 en rojo.
    ejes[1].plot(t * US, r1, color="#d62728", linewidth=0.8)
    ejes[1].set_ylabel("R1, PC0 (V)")
    ejes[1].set_xlabel("Tiempo (µs)")
    for eje in ejes:
        eje.axhline(UMBRAL, color="gray", linestyle=":", linewidth=0.8)
        eje.grid(alpha=0.3)
    ejes[0].set_title("CLK y dato R1: R1 cambia entre flancos, no en el flanco")
    guardar(figura, "captura3-CLK-R1.png", CARPETA)
```

**Gráfica completa** (`captura3-CLK-R1.png`): CLK arriba, R1 abajo, línea punteada del umbral y cuadrícula, igual que en los otros análisis. El título resume la conclusión: «R1 cambia entre flancos, no en el flanco».

**Líneas 115 a 136**

```python
    # Segunda gráfica: acercamiento a 10 pulsos, porque con 128 juntos no se distinguen los flancos.
    # Acercamiento a 10 pulsos
    # Figura de 2 paneles.
    figura, ejes = plt.subplots(2, 1, sharex=True, figsize=(10, 4.5))
    # Inicio de la ventana: 3 µs antes del pulso 20.
    inicio = grupo[20] - 3e-6
    # Fin de la ventana: 3 µs después del pulso 30.
    fin = grupo[30] + 3e-6
    # Máscara: verdadero solo para las muestras dentro de la ventana.
    mascara = (t >= inicio) & (t <= fin)
    # CLK en azul, solo la ventana.
    ejes[0].plot(t[mascara] * US, clk[mascara], color="#1f77b4", linewidth=0.9)
    ejes[0].set_ylabel("CLK, PC8 (V)")
    # R1 en rojo, solo la ventana.
    ejes[1].plot(t[mascara] * US, r1[mascara], color="#d62728", linewidth=0.9)
    ejes[1].set_ylabel("R1, PC0 (V)")
    ejes[1].set_xlabel("Tiempo (µs)")
    for eje in ejes:
        eje.axhline(UMBRAL, color="gray", linestyle=":", linewidth=0.8)
        eje.grid(alpha=0.3)
    ejes[0].set_title("Acercamiento: 10 pulsos de CLK y el dato R1")
    guardar(figura, "captura3-CLK-R1-acercamiento.png", CARPETA)
```

**Gráfica de acercamiento** (`captura3-CLK-R1-acercamiento.png`): con 128 pulsos juntos no se distinguen los flancos, así que se hace zoom a **10 pulsos**.
- Líneas 120-122: el inicio es 3 µs antes del pulso 20 y el fin 3 µs después del pulso 30.
- Línea 124: `mascara` es verdadero solo en las muestras dentro de esa ventana.
- Líneas 126-130: se dibujan solo esas muestras (`t[mascara]`, `clk[mascara]`, `r1[mascara]`).
- Líneas 131-136: eje de tiempo, umbral, cuadrícula, título y guardado.

**Líneas 139 a 141**

```python
# Solo se ejecuta si el archivo se corre directamente (no cuando otro programa lo importa).
if __name__ == "__main__":
    analizar_captura3()
```

Se ejecuta `analizar_captura3()` solo cuando el archivo se corre directamente.

