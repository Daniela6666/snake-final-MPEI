# Análisis 4: dirección de fila (A y B)

**Qué mide:** las señales de **dirección de fila A (pin PC10) y B (pin PC11)**. A y B forman un número de 2 bits, la **fase** (0 a 3), que le dice al panel qué grupo de filas encender (escaneo 1/4). El programa reconstruye la **cuenta de fases** a partir de los voltajes y mide cuánto dura cada una.

**Por qué se mide:** para comprobar que el firmware cambia de fase **en orden (0, 1, 2, 3, 0…)** y cuánto tiempo deja cada una. Si el orden fuera otro, se verían las filas mezcladas.

**Cómo se conectó la sonda:** CH1 y CH2 en PC10 y PC11. Hay **dos CSV**: `captura4-A-B.csv` (fases 0, 1, 2) y `captura4-A-B-anterior.csv` (fases 2, 3, 0). Al medir se anotó CH1 = A y CH2 = B, pero **los datos solo cuadran con el código si CH2 estaba en PC10 (A) y CH1 en PC11 (B)**. El programa lo prueba: con esa asignación las fases cuentan de 1 en 1; con la contraria no. Es una **deducción, no está verificado** qué sonda iba en cada pin.

**Cómo se calcula la fase:** `fase = A + 2·B` (A es el bit 0 y B el bit 1), igual que en `dibujar_fase`: `A = fase & 1` y `B = (fase >> 1) & 1`.

**Qué se concluye:**
- Las fases salen **0, 1, 2** y **2, 3, 0**: cada una es la anterior más 1 (módulo 4).
- Cada fase dura **~0,98 ms**.
- Cuando cambian los dos bits (fase 1 → 2, o 3 → 0), **B cambia ~0,6 µs después de A** y hay un estado intermedio de 0,6 µs. Es el tiempo entre las dos escrituras del código (A y luego B). Ocurre con OE en alto, así que el panel no lo muestra.

**Cómo se ejecuta** (desde cualquier carpeta; solo necesita `numpy` y `matplotlib`):

```bash
python3 analizar.py
```

**Esta carpeta es independiente:** el CSV de la captura, la gráfica que se genera y el código están **juntos aquí**. Usa las herramientas de [`../comun/`](../comun/README.md) para leer el CSV, detectar flancos y guardar la gráfica. Los números que imprime son los que aparecen en el [README de las mediciones](../README.md).

**Salida real del programa** (así se ve al ejecutarlo):

```text
=== captura4-A-B.csv: CH1 y CH2 (dirección de fila) ===
Intervalo: 83.3 ns, ventana: 1.67 ms
Estados (CH1, CH2) en orden, con su duración:
  CH1=0 CH2=0  desde 0.0 µs, duración 471.67 µs
  CH1=0 CH2=1  desde 471.7 µs, duración 981.92 µs
  CH1=0 CH2=0  desde 1453.6 µs, duración 0.58 µs
  CH1=1 CH2=0  desde 1454.2 µs, duración 212.49 µs
Estados que duran más de 50 µs, con CH2 = A (bit 0) y CH1 = B (bit 1): fase = [0, 1, 2]
¿Cada fase es la anterior más 1 (como cuenta fase_actual en panel.c)? [True, True]
Con la asignación contraria (CH1 = A, CH2 = B): fase = [0, 2, 1] (no cuenta de 1 en 1)
Instantes de cambio de CH1 (µs): ['1454.09']
Instantes de cambio de CH2 (µs): ['471.61', '1453.53']
  Cambian en la misma transición de fase: CH2 en 1453.53 µs, CH1 en 1454.09 µs (CH1 menos CH2 = +0.55 µs)
  dibujar_fase escribe A y después B, con ~0,5 µs entre escrituras (ancho de CLK y de LAT): CH2 = A y CH1 = B.
captura4-A-B.csv: CH1 min -0.32 V, max 3.84 V; CH2 min -1.25 V, max 5.09 V

=== captura4-A-B-anterior.csv: CH1 y CH2 (dirección de fila) ===
Intervalo: 66.7 ns, ventana: 1.33 ms
Estados (CH1, CH2) en orden, con su duración:
  CH1=1 CH2=0  desde 0.0 µs, duración 221.20 µs
  CH1=1 CH2=1  desde 221.2 µs, duración 981.07 µs
  CH1=1 CH2=0  desde 1202.3 µs, duración 0.60 µs
  CH1=0 CH2=0  desde 1202.9 µs, duración 130.47 µs
Estados que duran más de 50 µs, con CH2 = A (bit 0) y CH1 = B (bit 1): fase = [2, 3, 0]
¿Cada fase es la anterior más 1 (como cuenta fase_actual en panel.c)? [True, True]
Con la asignación contraria (CH1 = A, CH2 = B): fase = [1, 3, 0] (no cuenta de 1 en 1)
Instantes de cambio de CH1 (µs): ['1202.84']
Instantes de cambio de CH2 (µs): ['221.16', '1202.23']
  Cambian en la misma transición de fase: CH2 en 1202.23 µs, CH1 en 1202.84 µs (CH1 menos CH2 = +0.61 µs)
  dibujar_fase escribe A y después B, con ~0,5 µs entre escrituras (ancho de CLK y de LAT): CH2 = A y CH1 = B.
captura4-A-B-anterior.csv: CH1 min -0.04 V, max 4.24 V; CH2 min -1.25 V, max 4.48 V
```

### El código, trozo por trozo

**Líneas 1 a 6**

```python
#!/usr/bin/env python3
"""Captura 4: dirección de fila (A en PC10 y B en PC11). Reconstruye la cuenta de fases 0, 1, 2, 3.

Uso, desde cualquier carpeta:  python3 analizar.py
Lee captura4-A-B.csv y captura4-A-B-anterior.csv (de esta carpeta) y guarda sus gráficas aquí mismo.
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
from medicion import US, UMBRAL, cruces, mostrar, guardar, niveles, leer_csv, plt

# CARPETA: la carpeta de este archivo; ahí están el CSV y se guarda la gráfica.
CARPETA = os.path.dirname(os.path.abspath(__file__))
```

Igual que en los otros análisis: `comun/` se agrega a la ruta de módulos (línea 14), `numpy` (línea 16) y las herramientas de [`../comun/README.md`](../comun/README.md) (línea 18).
- **Línea nueva `CARPETA = os.path.dirname(os.path.abspath(__file__))`:** la carpeta **de este archivo**. Es donde están el CSV y donde se guardará la gráfica. Se pasa a `leer_csv(..., CARPETA)` y a `guardar(..., CARPETA)`; así **la carpeta es independiente**: funciona sin importar desde dónde se ejecute y sin tocar las carpetas de las demás capturas.

**Líneas 24 a 47**

```python
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
```

`estados_ab(nombre)`: convierte las dos señales analógicas en una **lista de estados** con su duración.
- Línea 27: lee `t`, `a` (canal 1) y `b` (canal 2). *(Los nombres `a` y `b` son solo los dos canales, en el orden del CSV: CH1, CH2.)*
- Líneas 29-31: `(a > UMBRAL).astype(int)` pone **1** donde la señal pasa de 1,65 V y **0** donde no: así cada muestra queda como un bit.
- Línea 33: `estados` empieza vacía. Cada elemento será `[(bit CH1, bit CH2), instante de inicio, instante de fin]`.
- Líneas 35-37: recorre las muestras; `estado` es la pareja de bits de esa muestra.
- Líneas 39-41: si **no hay estados todavía** o el estado **cambió** respecto al último, **abre uno nuevo** con inicio y fin en este instante.
- Líneas 43-45: si es **el mismo estado**, solo **extiende el fin** del último.
- Línea 47: devuelve los tiempos, los voltajes y la lista de estados.
- **Por qué así:** da una tabla corta («durante 981 µs estuvo en 01, luego 0,6 µs en 00…») en lugar de miles de muestras.

**Líneas 50 a 61**

```python
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
```

`analizar_captura4(nombre)`: analiza un CSV.
- Líneas 52-53: texto de ayuda: explica que las etiquetas originales de las sondas contradecían al código y que aquí se prueba la asignación contraria.
- Línea 55: encabezado. Línea 57: `estados_ab` da los canales y los estados. Línea 59: `paso` = intervalo entre muestras.
- Línea 61: imprime ese intervalo (83,3 ns o 66,7 ns según la captura) y la duración de la ventana.

**Líneas 62 a 67**

```python
    # Encabezado de la lista de estados.
    print("Estados (CH1, CH2) en orden, con su duración:")
    # Para cada estado: su valor, cuándo empieza y cuándo termina.
    for estado, inicio, fin in estados:
        # Imprime el estado y su duración (la última muestra dura un intervalo más).
        print("  CH1=%d CH2=%d  desde %.1f µs, duración %.2f µs" % (estado[0], estado[1], inicio * US, (fin - inicio + paso) * US))
```

Imprime **cada estado en orden con su duración**: `CH1=0 CH2=1 desde 471.7 µs, duración 981.92 µs`. `fin - inicio + paso` suma una muestra porque el estado ocupa también la última muestra donde se mantuvo.

**Líneas 68 a 75**

```python
    # Estados «permanentes»: los que duran más de 50 µs (los demás son transiciones entre fases).
    permanentes = [e for e in estados if (e[2] - e[1]) > 50e-6]
    # Deducción: CH2 = A (bit 0 de la fase) y CH1 = B (bit 1 de la fase).
    # Deducción: CH2 = A (bit 0 de la fase) y CH1 = B (bit 1 de la fase).
    # Número de fase de cada estado permanente: A + 2·B.
    valores_fase = [int(e[0][1] + 2 * e[0][0]) for e in permanentes]
    # Imprime las fases en orden.
    print("Estados que duran más de 50 µs, con CH2 = A (bit 0) y CH1 = B (bit 1): fase = %s" % valores_fase)
```

- Línea 69: `permanentes` = estados que duran **más de 50 µs**. Descarta los estados intermedios de ~0,6 µs que aparecen cuando A y B no cambian exactamente al mismo tiempo. `e[2] - e[1]` es fin menos inicio.
- Líneas 70-73: **la deducción.** Se supone CH2 = A (bit 0) y CH1 = B (bit 1); `e[0]` es la pareja `(CH1, CH2)`, así que `fase = CH2 + 2·CH1` = `e[0][1] + 2 * e[0][0]`. `int(...)` lo deja como número normal de Python.
- Línea 75: imprime las fases en orden (`[0, 1, 2]`).

**Líneas 76 a 83**

```python
    # Comprueba que cada fase es la anterior más 1 (módulo 4: después de la 3 viene la 0).
    siguiente = [(valores_fase[i] + 1) % 4 == valores_fase[i + 1] for i in range(len(valores_fase) - 1)]
    # Imprime esa comprobación (True/False por cada paso).
    print("¿Cada fase es la anterior más 1 (como cuenta fase_actual en panel.c)? %s" % siguiente)
    # Lo mismo con la asignación contraria (CH1 = A, CH2 = B), para comparar.
    valores_inversos = [int(e[0][0] + 2 * e[0][1]) for e in permanentes]
    # Imprime la cuenta contraria: si no cuenta de 1 en 1, esa asignación no es la correcta.
    print("Con la asignación contraria (CH1 = A, CH2 = B): fase = %s (no cuenta de 1 en 1)" % valores_inversos)
```

- Línea 77: `siguiente` es una lista de verdadero/falso: para cada fase, ¿**la siguiente es ella más 1** (módulo 4, para que 3 → 0 cuente)? `% 4` da la vuelta.
- Línea 79: imprime el resultado (`[True, True]`): **sí cuenta de 1 en 1**, como `fase_actual` en `panel.c`.
- Líneas 81-83: la **prueba con la asignación contraria** (CH1 = A, CH2 = B): `fase = CH1 + 2·CH2`. Salen `[0, 2, 1]` y `[1, 3, 0]`: **no cuentan de 1 en 1**, así que esa asignación queda descartada.

**Líneas 84 a 91**

```python
    # Instantes en que cambia CH1 (subidas y bajadas, ordenados).
    cambios1 = np.sort(np.concatenate([cruces(t, canal1, True), cruces(t, canal1, False)]))
    # Instantes en que cambia CH2.
    cambios2 = np.sort(np.concatenate([cruces(t, canal2, True), cruces(t, canal2, False)]))
    # Imprime los instantes de cambio de CH1 (µs).
    print("Instantes de cambio de CH1 (µs): %s" % ["%.2f" % (x * US) for x in cambios1])
    # Imprime los de CH2.
    print("Instantes de cambio de CH2 (µs): %s" % ["%.2f" % (x * US) for x in cambios2])
```

**Instantes de cada cambio:**
- Líneas 85-87: todos los flancos (de subida y de bajada) de cada canal, juntados con `np.concatenate` y ordenados con `np.sort`.
- Líneas 89-91: los imprime en µs.

**Líneas 92 a 100**

```python
    # Para cada cambio de CH1...
    for instante1 in cambios1:
        # ...busca los cambios de CH2 a menos de 5 µs (son de la misma transición de fase)...
        cercanos = cambios2[np.abs(cambios2 - instante1) < 5e-6]
        # ...y si hay,
        if len(cercanos) > 0:
            # imprime cuánto después o antes cambia CH1 respecto a CH2 (el signo + indica que CH1 cambia después).
            print("  Cambian en la misma transición de fase: CH2 en %.2f µs, CH1 en %.2f µs (CH1 menos CH2 = %+.2f µs)"
                  % (cercanos[0] * US, instante1 * US, (instante1 - cercanos[0]) * US))
```

**Qué cambia a la vez:**
- Línea 93: para cada cambio de CH1...
- Línea 95: ...busca los cambios de CH2 que ocurren **a menos de 5 µs** (`np.abs(cambios2 - instante1) < 5e-6`). Quedan los que pertenecen a **la misma transición de fase**.
- Líneas 97-100: si hay, imprime los dos instantes y su **diferencia**: CH1 cambia **+0,55 µs** (o +0,61 µs) **después** que CH2. O sea B cambia después de A: coincide con el código, que escribe A y luego B.

**Líneas 101 a 104**

```python
    # Conclusión que sale del código del firmware: dibujar_fase escribe A y después B.
    print("  dibujar_fase escribe A y después B, con ~0,5 µs entre escrituras (ancho de CLK y de LAT): CH2 = A y CH1 = B.")
    # Voltaje mínimo y máximo de cada canal.
    niveles(nombre, t, canal1, canal2, "CH1", "CH2")
```

- Línea 102: texto fijo con la explicación de la conclusión: `dibujar_fase` escribe A y después B, con ~0,5 µs entre las dos escrituras; por eso CH2 = A y CH1 = B.
- Línea 104: voltajes mínimo y máximo.

**Líneas 106 a 119**

```python
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
```

**La gráfica** (`captura4-A-B.png` o `captura4-A-B-anterior.png`):
- Línea 107: dos paneles que comparten el tiempo.
- Líneas 109-113: **arriba A** (se dibuja `canal2`) y **abajo B** (se dibuja `canal1`), con la etiqueta «deducido» para recordar que la asignación no está verificada.
- Líneas 114-117: eje de tiempo, umbral y cuadrícula.
- Línea 118: título con el nombre de la captura.
- Línea 119: el nombre del PNG es el del CSV cambiando `.csv` por `.png`.

**Líneas 122 a 125**

```python
# Solo se ejecuta si el archivo se corre directamente (no cuando otro programa lo importa).
if __name__ == "__main__":
    analizar_captura4("captura4-A-B.csv")
    analizar_captura4("captura4-A-B-anterior.csv")
```

Se analizan **los dos CSV**, uno tras otro, cuando el archivo se ejecuta directamente.

