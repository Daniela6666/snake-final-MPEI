# Mapeo de píxeles

El panel P10 es de escaneo 1/4: en cada fase (0 a 3, elegida con A y B) se encienden las filas `fase`, `fase + 4`, `fase + 8` y `fase + 12`. Cada bit que se desplaza lleva 6 datos: R1 G1 B1 para la mitad de arriba del panel y R2 G2 B2 para la de abajo.

## Un panel (64 bits por fase)
```
bloque = bit / 16
j      = bit % 16

si j < 8:   x = 8 * bloque + (7 - j)    y = fase        (de derecha a izquierda)
si j >= 8:  x = 8 * bloque + (j - 8)    y = fase + 4    (de izquierda a derecha)

R2, G2 y B2 usan la fila y + 8.
```

## Dos paneles (128 bits por fase)
Los paneles van en serie, así que cada fase es un solo registro de 128 bits.
- Bits 0 a 63: panel 2 (el de abajo).
- Bits 64 a 127: panel 1 (el de arriba, conectado a la placa).
- Dentro de cada panel se usa la fórmula de arriba con `bit % 64`.

El panel 2 está debajo del panel 1 y **girado 180°**. Con `x` e `y` calculadas con la fórmula:

| Panel | Columna | Fila de R1 G1 B1 | Fila de R2 G2 B2 |
|---|---|---|---|
| 1 (arriba) | `x` | `y` | `y + 8` |
| 2 (abajo, girado) | `31 - x` | `31 - y` | `23 - y` |

## Puntos medidos (fase 0)
Un solo bit encendido con G1 (verde) y R2 (rojo) a la vez, en coordenadas (columna, fila):

| Bit | Verde | Rojo |
|---|---|---|
| 0 | (24, 31) | (24, 23) |
| 16 | (16, 31) | (16, 23) |

Los demás bits y fases se comprobaron juntos con una pantalla de prueba de 32×32 (marco, un dígito en cada esquina y los 7 colores en la unión de los paneles), que se vio correcta.
