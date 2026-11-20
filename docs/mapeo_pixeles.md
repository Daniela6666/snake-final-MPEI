# Mapeo de píxeles del panel P10 RGB (un panel 32x16 y dos paneles 32x32)

Resumen del mapeo medido en el repositorio anterior (archivo `MAPEO.md` de la carpeta `PRUEBA PANTALLA`). Se comprobó en este repositorio con los dibujos de prueba del Paso 5 (un panel) y con la pantalla de prueba del Paso 11 (dos paneles). El fabricante puede cambiar el orden de los píxeles entre módulos, así que un panel de otra tanda debería medirse otra vez.

## Cómo se envía una fase
- El panel es de escaneo 1/4: en cada fase (0 a 3, escogida con A y B) se encienden las filas `fase`, `fase + 4`, `fase + 8` y `fase + 12`.
- Por cada fase se desplazan 64 bits (por módulo), en 4 bloques de 16.
- Cada bit lleva 6 datos a la vez: R1 G1 B1 para la mitad de arriba (filas 0 a 7) y R2 G2 B2 para la de abajo (filas 8 a 15).

## Fórmula medida (bit → x, y)
```
bloque = bit / 16
j      = bit % 16

si j < 8:   x = 8 * bloque + (7 - j)     y = fase          (de derecha a izquierda)
si j >= 8:  x = 8 * bloque + (j - 8)     y = fase + 4      (de izquierda a derecha)

Para R2, G2 y B2 se suma 8 a y.
```
La fórmula inversa (de x, y a fase y bit) se deduce de esta y se documenta en el paso 5.

## Dos paneles (tablero de 32x32, medido en el Paso 11)
Los dos paneles se encadenan en serie: el OUT del panel 1 va al IN del panel 2 (otro cable plano). Forman un solo registro de desplazamiento de 128 pasos por cada color, así que cada fase pasa a ser de 128 bits (`PANEL_BITS_POR_FASE`, con 64 por panel en `PANEL_BITS_POR_MODULO`).

- El primer bit que se envía (el bit 0) se va empujando hasta el panel más lejano; el último (el bit 127) queda en el panel conectado a la placa.
- **Los bits 0 a 63 son del panel 2** (el de abajo) y **los bits 64 a 127 son del panel 1** (el de arriba, conectado a la placa).
- Dentro de cada panel se usa la fórmula de arriba con `bit_en_modulo = bit % 64` (en lugar de `bit`).

### Disposición física
El panel 2 está **debajo** del panel 1 y **girado 180°** (de cabeza). Es físicamente igual al panel 1, así que su mapeo interno es el mismo y solo cambian las coordenadas vistas desde afuera. Con `x` e `y` las coordenadas dentro del panel, calculadas con la fórmula de arriba, el tablero de 32x32 se ve así (columna 0 a la izquierda, fila 0 arriba del panel 1):

| Panel | Bits de la fase | Columna | Fila de R1 G1 B1 | Fila de R2 G2 B2 |
|---|---|---|---|---|
| Panel 1 (arriba) | 64 a 127 | `x` | `y` | `y + 8` |
| Panel 2 (abajo, girado 180°) | 0 a 63 | `31 - x` | `31 - y` | `31 - (y + 8)` = `23 - y` |

### Puntos medidos (fase 0)
Se enciende un solo bit de la cadena con G1 (verde, mitad de arriba) y R2 (rojo, mitad de abajo) a la vez y se anota el píxel donde aparece (columna, fila):

| Bit | Verde medido | Rojo medido |
|---|---|---|
| 0 | (24, 31) | (24, 23) |
| 16 | (16, 31) | (16, 23) |

Esos dos puntos concuerdan con la tabla de arriba. No se midió el bit 8 (la otra mitad de un bloque), las fases 1 a 3 ni el panel 1 dentro de la cadena: se comprobaron todas juntas con una pantalla de prueba de 32x32 (marco, un dígito en cada esquina y dos filas con los 7 colores en la unión de los paneles), que se vio correcta y estable. Ver el Paso 11 de `docs/GUIA_DE_ESTUDIO.md`.
