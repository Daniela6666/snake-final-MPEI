# Herramientas comunes de análisis (`comun/medicion.py`)

**Qué es:** la «caja de herramientas» que comparten los siete análisis. **No se ejecuta sola**: cada análisis la importa con `from medicion import ...`.

**Por qué existe:** todos los análisis hacen lo mismo al principio: leer el CSV, decidir dónde la señal sube y baja, agrupar los pulsos en ráfagas y guardar una gráfica. Si cada programa tuviera su propia copia, un error corregido en uno quedaría sin corregir en los demás. Con un solo archivo, **se arregla en un lugar y los siete análisis lo reciben**.

### Ideas que hay que entender antes de leer el código

- **El CSV del osciloscopio** es una tabla de tres columnas: tiempo (s), canal 1 (V) y canal 2 (V). Cada fila es una **muestra** (por ejemplo, una cada 100 ns). Está en formato español: separador `;` y **coma decimal** (`0,363636`).
- **Nivel alto y bajo:** las señales digitales de la placa son de 3,3 V. Se decide que una muestra está en **alto** si pasa de **1,65 V** (la mitad, `UMBRAL`) y en **bajo** si no. Es un umbral simple: los picos de 5 V o de −1 V que se ven en las gráficas no cambian la decisión.
- **Flanco:** el instante en que la señal **cruza** el umbral. **Flanco de subida** = pasa de bajo a alto; **flanco de bajada** = de alto a bajo. Casi todas las medidas son «tiempo entre un flanco y otro».
- **Ráfaga:** un grupo de pulsos de CLK seguidos (los 128 bits de una fase), separado del siguiente grupo por una pausa larga.

### El código, trozo por trozo

**Líneas 1 a 6**

```python
"""Herramientas comunes para analizar los CSV del osciloscopio (Hantek 6022BE).

No se ejecuta solo: lo importan los programas de las carpetas 01 a 07.
Lee el CSV de la carpeta de cada captura, detecta flancos y ráfagas, y guarda
la gráfica PNG en esa misma carpeta. Requiere numpy y matplotlib.
"""
```

Texto de ayuda del archivo (*docstring*): para qué sirve. No se ejecuta; sirve como documentación (`help(medicion)` lo muestra).

**Líneas 8 a 17**

```python
import os
# numpy: operaciones sobre miles de muestras a la vez, sin bucles.
import numpy as np
# matplotlib: librería de gráficas.
import matplotlib

# Modo «Agg»: dibuja directo a archivo sin abrir ventana (sirve en un servidor o Codespace). Debe ir antes de importar pyplot.
matplotlib.use("Agg")  # dibuja sin abrir ventana: solo se guardan PNG
# pyplot: la interfaz para crear figuras.
import matplotlib.pyplot as plt
```

- `import os`: para armar rutas de archivos.
- `import numpy as np`: **arreglos** y operaciones sobre miles de muestras de una vez (restar, comparar, buscar) sin escribir bucles. Es mucho más rápido y corto que con listas.
- `matplotlib.use("Agg")`: elige el modo de dibujo **«Agg»**, que dibuja directamente a un archivo y **no abre ninguna ventana**. Así el programa funciona en un servidor o en un Codespace, donde no hay pantalla. **Debe ir antes de `import matplotlib.pyplot`**; por eso está entre los dos `import`.
- `import matplotlib.pyplot as plt`: la interfaz para crear figuras.

**Líneas 19 a 23**

```python
# Cada programa le pasa a estas funciones su propia carpeta (donde están su CSV y su gráfica).
# UMBRAL: nivel (V) que separa «alto» de «bajo»: la mitad de 3,3 V.
UMBRAL = 1.65  # V, mitad de 3,3 V
# US: factor para pasar segundos a microsegundos (1 s = 1 000 000 µs).
US = 1e6  # segundos a microsegundos
```

Constantes que usan todos los análisis:
- **Línea 19 (comentario):** `medicion.py` **no sabe de dónde leer ni dónde guardar**: cada programa le pasa **su propia carpeta** (donde están su CSV y su gráfica). **Por qué así:** cada captura vive en su carpeta, con todo junto; esta caja de herramientas sirve igual a las siete sin conocer ninguna ruta.
- `UMBRAL = 1.65`: el nivel (en voltios) que separa alto de bajo (la mitad de 3,3 V).
- `US = 1e6`: factor para pasar **segundos a microsegundos** (`1e6` = 1 000 000). Los tiempos medidos son de ~1 µs; se imprimen en µs para que sean legibles.

**Líneas 26 a 46**

```python
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
```

`leer_csv(nombre, carpeta)`: abre el CSV `nombre` que está en `carpeta` y devuelve tres arreglos: `t` (s), `canal 1` (V) y `canal 2` (V).
- Línea 30: `os.path.join(carpeta, nombre)` une la carpeta y el nombre en una ruta (con el separador correcto para el sistema operativo).
- Línea 34: `open(ruta, encoding="utf-8-sig")`: **`utf-8-sig` descarta el BOM**, una marca invisible que Excel y otros programas ponen al inicio del archivo; sin eso, el primer carácter del encabezado saldría raro.
- Línea 36: `next(archivo)`: **salta el encabezado** (`"t / s";"CH1 / V";"CH2 / V"`), que no son números.
- Línea 40: por cada línea: `strip()` quita el salto de línea (en estos CSV es CRLF), `replace(",", ".")` cambia la coma decimal por **punto**, porque Python solo entiende `0.36`, y `split(";")` separa las tres columnas.
- Línea 42: `float(parte)` convierte cada texto en número.
- Líneas 44-46: `np.array(datos)` forma una matriz de N filas × 3 columnas; `matriz[:, 0]` es **toda la columna 0** (el tiempo), `[:, 1]` el canal 1 y `[:, 2]` el canal 2.

**Líneas 49 a 63**

```python
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
```

`cruces(t, v, subida)`: encuentra los **instantes de los flancos**.
- Líneas 53-55 (subida): `v[:-1]` son todas las muestras **menos la última** y `v[1:]` todas **menos la primera**; comparadas posición por posición, forman **parejas de muestras consecutivas**. `(v[:-1] < umbral) & (v[1:] >= umbral)` es verdadero donde una muestra está por debajo del umbral y la siguiente en o por encima: ahí **hay un flanco de subida**. `np.where(...)[0]` devuelve los **índices** donde es verdadero.
- Líneas 57-59 (bajada): igual, con la condición contraria (de ≥ umbral a < umbral).
- Línea 61: **interpolación lineal.** El flanco ocurrió entre dos muestras; `fraccion` dice qué parte del camino entre ellas se recorrió cuando se cruzó el umbral: `(umbral − v_antes) / (v_después − v_antes)`.
- Línea 63: el instante real = tiempo de la muestra anterior + `fraccion` × (intervalo entre muestras).
- **Por qué interpolar:** las muestras están cada 66,7 ns a 100 ns y se miden retardos de ~0,5 µs a 3 µs. Sin interpolar, cada tiempo tendría un error de hasta una muestra completa; con ella, la resolución es mucho mejor que el intervalo.

**Líneas 66 a 82**

```python
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
```

`rafagas(subidas, separacion_minima)`: agrupa los flancos de subida de CLK en **ráfagas**.
- Línea 70: empieza con un primer grupo que contiene el primer flanco.
- Líneas 72-80: para cada flanco siguiente, si la distancia al **último flanco del último grupo** (`grupos[-1][-1]`) es **mayor** que `separacion_minima`, hay una pausa larga: se **abre un grupo nuevo**. Si no, el flanco **pertenece al grupo actual**.
- Línea 82: convierte cada grupo en un arreglo de numpy.
- Los análisis usan `20e-6` (20 µs): es **más que el periodo entre pulsos de una ráfaga (~6 µs)** y **menos que la pausa entre ráfagas (~208 µs)**, así que separa bien una ráfaga de la siguiente.

**Líneas 85 a 96**

```python
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
```

Dos funciones de búsqueda sobre listas de instantes ordenados:
- `ultimo_antes(instantes, referencia)`: `instantes <= referencia` crea una máscara de verdadero/falso; `instantes[máscara]` deja solo los elementos que cumplen y `[-1]` toma **el último**: el flanco más cercano **antes** de la referencia.
- `primero_despues(instantes, referencia)`: lo mismo con `>=` y `[0]`: el primer flanco **después**.
- Si no hay ningún elemento que cumpla, Python da error; por eso quien las llama primero comprueba con `np.any(...)`.

**Líneas 99 a 101**

```python
# Imprime un encabezado «=== título ===» con una línea en blanco antes, para separar los resultados de cada captura.
def mostrar(titulo):
    print("\n=== " + titulo + " ===")
```

`mostrar(titulo)`: imprime un encabezado `=== título ===` precedido de una línea en blanco, para separar los resultados de cada captura en la pantalla.

**Líneas 104 a 108**

```python
# Guarda la figura como PNG en la carpeta indicada (130 puntos por pulgada; bbox_inches recorta los márgenes blancos).
def guardar(figura, nombre, carpeta):
    figura.savefig(os.path.join(carpeta, nombre), dpi=130, bbox_inches="tight")
    # Libera la memoria de la figura.
    plt.close(figura)
```

`guardar(figura, nombre, carpeta)`: guarda la figura como PNG **en la carpeta que se le pasa** (la de la captura), uniendo `carpeta` y `nombre` con `os.path.join`.
- `savefig(..., dpi=130, bbox_inches="tight")`: 130 puntos por pulgada (nítida sin pesar demasiado) y recorta los márgenes blancos sobrantes.
- `plt.close(figura)`: libera la memoria de la figura (importante si se guardan varias seguidas).

**Líneas 111 a 114**

```python
# Imprime el mínimo y el máximo de voltaje de cada canal (los niveles reales de la señal).
def niveles(nombre, t, canal1, canal2, etiqueta1, etiqueta2):
    print("%s: %s min %.2f V, max %.2f V; %s min %.2f V, max %.2f V"
          % (nombre, etiqueta1, canal1.min(), canal1.max(), etiqueta2, canal2.min(), canal2.max()))
```

`niveles(...)`: imprime el **mínimo y máximo de voltaje de cada canal**. Sirve para ver los niveles reales de la señal (por ejemplo, picos de 5 V o de −1,25 V) aunque no se usen en el análisis.

**Líneas 117 a 146**

```python
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
```

`grafica_dos_canales(carpeta, archivo, ...)`: la gráfica estándar con **dos paneles apilados**, uno por canal. Lee `archivo` de `carpeta` y guarda el PNG en la misma carpeta.
- Línea 120: lee el CSV con `leer_csv(archivo, carpeta)`.
- Línea 122: `plt.subplots(2, 1, sharex=True, figsize=(10, 4.5))`: 2 filas y 1 columna de ejes que **comparten el eje del tiempo** (así los flancos de los dos canales quedan alineados verticalmente), en una figura de 10×4,5 pulgadas.
- Líneas 124-130: arriba el canal 1 (azul) y abajo el canal 2 (rojo). `t * US` pasa el tiempo a µs. `set_ylabel` pone el nombre de la señal.
- Líneas 132-138: etiqueta del eje de tiempo; en cada panel una **línea punteada gris en 1,65 V** (el umbral, para ver qué se cuenta como alto) y una cuadrícula suave (`alpha=0.3`).
- Líneas 140-142: si se pidió una ventana de tiempo, `set_xlim(*ventana_us)` la aplica (`*` desempaqueta la pareja `(inicio, fin)`).
- Línea 144: el título.
- Línea 146: `destino or (...)`: si no se dio nombre de archivo, usa el del CSV cambiando `.csv` por `.png`; guarda en la misma carpeta.

