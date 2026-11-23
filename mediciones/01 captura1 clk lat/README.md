# Análisis 1: CLK y LAT (ráfagas de 128 pulsos)

**Qué mide:** la señal **CLK** (reloj de desplazamiento, pin **PC8**, canal 1) y **LAT** (latch, pin **PC7**, canal 2) mientras el juego dibuja. Cuenta cuántos pulsos de CLK hay en cada ráfaga y mide su periodo, su ancho y cada cuánto da LAT un pulso.

**Por qué se mide:** el firmware dice que cada fase envía **128 bits** (dos paneles × 64) y luego da un pulso de LAT. Esta captura **comprueba con el osciloscopio** que eso es lo que realmente sale por los pines, y dice cuánto tarda cada parte, que es lo que limita el brillo y el parpadeo del panel.

**Cómo se conectó la sonda:** CH1 en PC8 (CLK) y CH2 en PC7 (LAT). Ventana de 2 ms, 20 000 muestras (una cada 100 ns).

**Qué se concluye** (ver las explicaciones de cada línea abajo):
- Cada fase es una ráfaga de **128 pulsos** de CLK: **coincide con el código** (`PANEL_BITS_POR_FASE = 128`).
- Cada pulso dura ~0,5 µs y se repite cada **~6,1 µs** (~164 kHz).
- La ráfaga completa dura **772 µs** y hay una pausa de **208 µs** hasta la siguiente. El pulso de LAT ocurre en esa pausa.
- LAT se repite cada **980 µs**: es lo que dura una **fase**. El diseño es 1000 µs (TIM3 interrumpe cada 1 ms); sale ~2 % menos, probablemente porque el oscilador interno (HSI) no es exacto (no se verificó).
- Las ráfagas ocupan ~79 % de cada fase (772 de 980 µs).

**Cómo se ejecuta** (desde cualquier carpeta; solo necesita `numpy` y `matplotlib`):

```bash
python3 analizar.py
```

**Esta carpeta es independiente:** el CSV de la captura, la gráfica que se genera y el código están **juntos aquí**. Usa las herramientas de [`../comun/`](../comun/README.md) para leer el CSV, detectar flancos y guardar la gráfica. Los números que imprime son los que aparecen en el [README de las mediciones](../README.md).

**Salida real del programa** (así se ve al ejecutarlo):

```text
=== captura1-CLK-LAT: CLK (PC8) y LAT (PC7) ===
Muestras: 20000, intervalo: 100.0 ns, ventana: 2.00 ms
Ráfagas detectadas: 3, con pulsos: [68, 128, 66]
Ráfagas completas de 128 pulsos: 1
  ráfaga completa 0: periodo mediano 6.095 µs (min 5.99, max 6.21), primera subida 618.6 µs, última 1390.7 µs
    duración (primera a última subida): 772.1 µs; duración con un periodo más: 778.2 µs
Ancho del pulso en alto de CLK: mediana 0.53 µs, min 0.51, max 0.62
Pausa entre última subida de una ráfaga y la primera de la siguiente: ['208.2', '208.2'] µs
Pulsos de LAT: 2, subidas en µs: ['412.2', '1392.5']
Periodo de LAT: ['980.3'] µs
Ancho del pulso de LAT: ['0.61', '0.52'] µs
captura1: CLK min -0.81 V, max 5.09 V; LAT min -0.77 V, max 4.65 V
```

### El código, trozo por trozo

**Líneas 1 a 6**

```python
#!/usr/bin/env python3
"""Captura 1: CLK (PC8) y LAT (PC7). Cuenta los pulsos por ráfaga y mide periodos y anchos.

Uso, desde cualquier carpeta:  python3 analizar.py
Lee captura1-CLK-LAT.csv (de esta carpeta) y guarda captura1-CLK-LAT.png aquí mismo.
"""
```

Primera línea `#!/usr/bin/env python3`: permite ejecutar el archivo como programa en Linux/Mac. Luego el *docstring*: qué hace el programa y cómo se usa.

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
from medicion import US, UMBRAL, cruces, rafagas, primero_despues, mostrar, guardar, niveles, leer_csv, plt

# CARPETA: la carpeta de este archivo; ahí están el CSV y se guarda la gráfica.
CARPETA = os.path.dirname(os.path.abspath(__file__))
```

- `import os` e `import sys`: para armar una ruta y para modificar dónde busca Python los módulos.
- Línea 14: `sys.path.insert(0, ".../comun")` **agrega la carpeta `comun/` al principio de la lista de lugares donde Python busca módulos**. `__file__` es este archivo; `abspath` lo vuelve absoluto; el primer `dirname` da esta carpeta y el segundo sube a `mediciones/`; `join(..., "comun")` apunta a `mediciones/comun/`. **Por qué:** cada carpeta es un programa independiente que se puede ejecutar desde cualquier lugar, sin instalar nada: así `import medicion` encuentra `comun/medicion.py`.
- Línea 16: `numpy` para los cálculos sobre arreglos.
- Línea 18: se importan **solo** las herramientas que se usan, todas explicadas en [`../comun/README.md`](../comun/README.md). `plt` es `matplotlib.pyplot` ya configurado para guardar sin abrir ventana.
- **Línea nueva `CARPETA = os.path.dirname(os.path.abspath(__file__))`:** la carpeta **de este archivo**. Es donde están el CSV y donde se guardará la gráfica. Se pasa a `leer_csv(..., CARPETA)` y a `guardar(..., CARPETA)`; así **la carpeta es independiente**: funciona sin importar desde dónde se ejecute y sin tocar las carpetas de las demás capturas.

**Líneas 24 a 31**

```python
# Hace todo el análisis de la captura 1 (CLK y LAT) y guarda la gráfica.
def analizar_captura1():
    # Encabezado de esta captura en la salida.
    mostrar("captura1-CLK-LAT: CLK (PC8) y LAT (PC7)")
    # Lee el CSV: tiempos y los dos canales (CH1 = CLK, CH2 = LAT).
    t, clk, lat = leer_csv("captura1-CLK-LAT.csv", CARPETA)
    # Datos generales: cantidad de muestras, intervalo entre muestras (ns) y duración total (ms).
    print("Muestras: %d, intervalo: %.1f ns, ventana: %.2f ms" % (len(t), (t[1] - t[0]) * 1e9, t[-1] * 1e3))
```

- Línea 25: toda la medición está en una función, para poder reutilizarla o llamarla desde otro programa sin que se ejecute sola al importarla.
- Línea 27: `mostrar(...)` imprime el encabezado de la captura.
- Línea 29: `leer_csv` devuelve tiempo, canal 1 (CLK) y canal 2 (LAT).
- Línea 31: imprime cuántas muestras hay (20 000), cada cuánto se tomó una (`t[1] - t[0]` = 100 ns, por `1e9` para pasar a ns) y la duración total (`t[-1]`, el último instante, ×1e3 para ms). Sirve para confirmar que se cargó la captura correcta.

**Líneas 32 a 37**

```python
    # Instantes en que CLK sube...
    subidas = cruces(t, clk, True)
    # ...y en que baja (con interpolación).
    bajadas = cruces(t, clk, False)
    # Agrupa las subidas en ráfagas: una pausa de más de 20 µs abre una ráfaga nueva.
    grupos = rafagas(subidas, 20e-6)
```

- Línea 33: `subidas` = instantes de **todos los flancos de subida de CLK**; línea 35: `bajadas` = los de bajada. Cada pulso de CLK tiene una subida y una bajada.
- Línea 37: `rafagas(subidas, 20e-6)` los **agrupa en ráfagas**: una pausa de más de 20 µs entre dos subidas abre una ráfaga nueva (dentro de una ráfaga hay ~6 µs entre pulsos; entre ráfagas, ~208 µs).

**Líneas 38 a 43**

```python
    # Cuántas ráfagas hay y cuántos pulsos tiene cada una (la ventana corta las de los extremos).
    print("Ráfagas detectadas: %d, con pulsos: %s" % (len(grupos), [len(g) for g in grupos]))
    # Se queda solo con las ráfagas completas: las de exactamente 128 pulsos.
    completas = [g for g in grupos if len(g) == 128]
    # Cuántas ráfagas completas hay.
    print("Ráfagas completas de 128 pulsos: %d" % len(completas))
```

- Línea 39: imprime cuántas ráfagas se detectaron y **cuántos pulsos tiene cada una**: `[68, 128, 66]`. La ventana de 2 ms **corta** la primera y la última ráfaga (por eso tienen menos pulsos) y deja **una completa en el medio**.
- Línea 41: `completas` = las ráfagas con **exactamente 128 pulsos**: dos paneles × 64 bits, lo que dice el código.
- Línea 43: imprime cuántas hay (1).

**Líneas 44 a 54**

```python
    # Para cada ráfaga completa:
    for numero, grupo in enumerate(completas):
        # Tiempo entre pulsos consecutivos (np.diff resta cada instante con el anterior).
        periodos = np.diff(grupo)
        # Estadísticas del periodo (mediana, mínimo, máximo) y de cuándo empieza y termina la ráfaga.
        print("  ráfaga completa %d: periodo mediano %.3f µs (min %.2f, max %.2f), primera subida %.1f µs, última %.1f µs"
              % (numero, np.median(periodos) * US, periodos.min() * US, periodos.max() * US,
                 grupo[0] * US, grupo[-1] * US))
        # Duración de la ráfaga: de la primera a la última subida, y con un periodo más (hasta el final del último pulso).
        print("    duración (primera a última subida): %.1f µs; duración con un periodo más: %.1f µs"
              % ((grupo[-1] - grupo[0]) * US, (grupo[-1] - grupo[0] + np.median(periodos)) * US))
```

Para cada ráfaga completa:
- Línea 47: `np.diff(grupo)` calcula la **diferencia entre flancos consecutivos**: son los **periodos** entre pulsos (127 valores para 128 pulsos).
- Líneas 49-51: imprime el periodo **mediano** (6,095 µs; la mediana no se deja influir por un valor raro), el mínimo y el máximo, y el instante del primer y del último flanco de subida.
- Líneas 53-54: **duración de la ráfaga**: de la primera a la última subida son 127 periodos = **772,1 µs**. Sumando un periodo más (porque el último pulso también ocupa su tiempo) son **778,2 µs**, que es 128 × 6,1 µs.

**Líneas 55 a 68**

```python
    # Ancho de cada pulso de CLK en alto: de cada subida a la siguiente bajada.
    anchos = []
    # Para cada subida...
    for subida in subidas:
        # ...las bajadas que ocurren después de ella...
        despues = bajadas[bajadas > subida]
        # ...y si hay alguna, la primera es el final de ese pulso.
        if len(despues) > 0:
            # Se guarda el ancho (bajada − subida).
            anchos.append(despues[0] - subida)
    # Se convierte la lista en arreglo de numpy para calcular mediana, mínimo y máximo.
    anchos = np.array(anchos)
    # Imprime el ancho típico del pulso en alto de CLK.
    print("Ancho del pulso en alto de CLK: mediana %.2f µs, min %.2f, max %.2f" % (np.median(anchos) * US, anchos.min() * US, anchos.max() * US))
```

**Ancho de cada pulso de CLK en alto:**
- Líneas 56-64: para cada subida, `bajadas[bajadas > subida]` deja las bajadas **posteriores** y `[0]` toma la **primera**; la resta es cuánto tardó en bajar = el ancho del pulso. `if len(despues) > 0` evita un error en la última subida si la captura termina antes de su bajada.
- Línea 66: pasa la lista a arreglo de numpy.
- Línea 68: imprime mediana (0,53 µs), mínimo y máximo. Es el tiempo que el procesador mantiene CLK en alto: lo que tardan las instrucciones entre subirlo y bajarlo.

**Líneas 69 a 74**

```python
    # Si hay una ráfaga completa y otra después, mide la pausa entre ráfagas:
    if len(completas) >= 1 and len(grupos) >= 2:
        # Pausa = primera subida de la ráfaga siguiente − última subida de la anterior.
        pausas = [grupos[i + 1][0] - grupos[i][-1] for i in range(len(grupos) - 1)]
        # Imprime las pausas (µs).
        print("Pausa entre última subida de una ráfaga y la primera de la siguiente: %s µs" % ["%.1f" % (p * US) for p in pausas])
```

**Pausa entre ráfagas:** si hay al menos una ráfaga completa y dos ráfagas en total, `pausas` es el tiempo entre el **último pulso de una ráfaga y el primero de la siguiente** (208,2 µs). En esa pausa el panel recibe el pulso de LAT, cambia la fase y se vuelve a empezar.

**Líneas 75 a 84**

```python
    # Instantes en que LAT sube...
    lat_subidas = cruces(t, lat, True)
    # ...y en que baja.
    lat_bajadas = cruces(t, lat, False)
    # Imprime cuántos pulsos de LAT hay y cuándo suben.
    print("Pulsos de LAT: %d, subidas en µs: %s" % (len(lat_subidas), ["%.1f" % (x * US) for x in lat_subidas]))
    # Con dos o más pulsos de LAT se puede medir cada cuánto se repite:
    if len(lat_subidas) >= 2:
        # Periodo de LAT = diferencia entre subidas consecutivas.
        print("Periodo de LAT: %s µs" % ["%.1f" % (d * US) for d in np.diff(lat_subidas)])
```

**Pulsos de LAT:**
- Líneas 76-78: flancos de subida y de bajada de LAT.
- Línea 80: imprime cuántos pulsos hay y en qué instante sube cada uno (412,2 µs y 1392,5 µs).
- Líneas 82-84: **periodo de LAT** = diferencia entre subidas consecutivas = **980,3 µs**. Es lo que dura una fase.

**Líneas 85 a 90**

```python
    # Ancho de cada pulso de LAT: de su subida a la primera bajada posterior.
    anchos_lat = [primero_despues(lat_bajadas, s) - s for s in lat_subidas if np.any(lat_bajadas >= s)]
    # Imprime los anchos de LAT.
    print("Ancho del pulso de LAT: %s µs" % ["%.2f" % (a * US) for a in anchos_lat])
    # Voltaje mínimo y máximo de cada canal (para ver los niveles reales).
    niveles("captura1", t, clk, lat, "CLK", "LAT")
```

- Líneas 86-88: **ancho de cada pulso de LAT**: para cada subida, la primera bajada posterior menos la subida (≈0,5 a 0,6 µs). `np.any(lat_bajadas >= s)` comprueba que **exista** una bajada después, para no fallar con un pulso cortado por el final de la captura.
- Línea 90: imprime los voltajes mínimo y máximo de cada canal.

**Líneas 92 a 113**

```python
    # Gráfica: 2 paneles apilados que comparten el eje del tiempo (CLK arriba, LAT abajo).
    figura, ejes = plt.subplots(2, 1, sharex=True, figsize=(10, 4.5))
    # Panel de arriba: CLK en azul (tiempo pasado a µs con US).
    ejes[0].plot(t * US, clk, color="#1f77b4", linewidth=0.6)
    # Nombre del eje vertical del panel de arriba.
    ejes[0].set_ylabel("CLK, PC8 (V)")
    # Panel de abajo: LAT en rojo.
    ejes[1].plot(t * US, lat, color="#d62728", linewidth=0.8)
    # Nombre del eje vertical del panel de abajo.
    ejes[1].set_ylabel("LAT, PC7 (V)")
    # Nombre del eje del tiempo (solo el panel de abajo).
    ejes[1].set_xlabel("Tiempo (µs)")
    # En cada panel:
    for eje in ejes:
        # una línea punteada gris en el umbral de 1,65 V (separa alto de bajo)
        eje.axhline(UMBRAL, color="gray", linestyle=":", linewidth=0.8)
        # y una cuadrícula suave.
        eje.grid(alpha=0.3)
    # Título de la gráfica.
    ejes[0].set_title("CLK y LAT: ráfagas de 128 pulsos y un pulso de LAT por fase")
    # Se guarda el PNG en esta carpeta y se libera la figura.
    guardar(figura, "captura1-CLK-LAT.png", CARPETA)
```

**La gráfica** `captura1-CLK-LAT.png` (en esta carpeta):
- Línea 93: dos paneles apilados que comparten el eje del tiempo.
- Líneas 95-103: arriba CLK (azul, línea más fina porque son muchos pulsos) y abajo LAT (rojo); etiquetas de los ejes.
- Líneas 105-109: en cada panel, línea punteada en el umbral de 1,65 V y cuadrícula.
- Línea 111: título.
- Línea 113: `guardar` la escribe como PNG y libera la memoria.

**Líneas 116 a 118**

```python
# Solo se ejecuta si el archivo se corre directamente (no cuando otro programa lo importa).
if __name__ == "__main__":
    analizar_captura1()
```

`if __name__ == "__main__":` significa «solo si este archivo se **ejecuta directamente**» (no si lo importa otro programa). Entonces corre `analizar_captura1()`. Así el mismo archivo sirve como programa y como módulo.

