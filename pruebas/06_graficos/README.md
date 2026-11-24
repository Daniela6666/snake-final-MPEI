# Prueba 06: biblioteca gráfica (marco, dígitos y barras de colores)

**Qué hace en la placa:** alterna dos pantallas, **3 segundos** cada una:
1. Un marco blanco alrededor del panel, los dígitos **0 a 4 en verde** en la fila de arriba y los dígitos **5 a 9 en amarillo** en la de abajo.
2. **Siete barras** (solo contorno) de izquierda a derecha en **rojo, verde, azul, amarillo, magenta, cian y blanco**.

**Para qué sirve:** comprobar visualmente que los **7 colores** salen bien (cada color es una combinación de los bits R, G y B) y que la **fuente de 3×5** dibuja bien los 10 dígitos. Esa fuente se usará para mostrar el puntaje del juego.

**Qué se agrega respecto a la prueba 05:**
- El módulo **`graficos`** (`inc/graficos.h`, `src/graficos.c`): borrar la pantalla, dibujar rectángulos y dibujar dígitos.
- Cuatro colores nuevos en `panel.h` (amarillo, magenta, cian, blanco).

**Qué NO cambia:** `panel.c`, `system_config`, `gpio_config`, `registros_f446.h`, `Makefile`, `linker_script.ld` y `crt0.S` son los de la prueba 05 (ver sus README). En `panel.h` solo cambian las constantes de color y un comentario.

### Cómo se combinan los colores

Cada canal es de 1 bit. Con R = bit 0, G = bit 1 y B = bit 2, un color es la **suma** de los canales encendidos:

| Color | Canales | Valor |
|---|---|---|
| Negro | ninguno | 0 |
| Rojo | R | 1 |
| Verde | G | 2 |
| Amarillo | R + G | 3 |
| Azul | B | 4 |
| Magenta | R + B | 5 |
| Cian | G + B | 6 |
| Blanco | R + G + B | 7 |

### 1. `inc/panel.h`: lo que cambia

**Líneas 59 a 66**

```c
// Color amarillo: bits R (bit 0) y G (bit 1) en 1, es decir, rojo + verde.
#define COLOR_AMARILLO 3U
// Color magenta: bits R (bit 0) y B (bit 2) en 1, es decir, rojo + azul.
#define COLOR_MAGENTA 5U
// Color cian: bits G (bit 1) y B (bit 2) en 1, es decir, verde + azul.
#define COLOR_CIAN 6U
// Color blanco: los tres bits R, G y B en 1.
#define COLOR_BLANCO 7U
```

- `COLOR_AMARILLO 3U` (`011`: R y G), `COLOR_MAGENTA 5U` (`101`: R y B), `COLOR_CIAN 6U` (`110`: G y B) y `COLOR_BLANCO 7U` (`111`: R, G y B). No hay que cambiar nada más: `dibujar_fase` ya copia los 3 bits de color del framebuffer, así que cualquier valor de 0 a 7 funciona.

**Líneas 78 a 79**

```c
// Guarda el color (uno de los COLOR_*) del píxel (x, y) en el framebuffer.
void encender_pixel(uint32_t x, uint32_t y, uint32_t color);
```

- Solo cambia el comentario del prototipo de `encender_pixel`: ahora dice «uno de los `COLOR_*`».

### 2. `inc/graficos.h`: interfaz del módulo gráfico

**Líneas 1 a 7**

```c
// Guarda de inclusión: si este archivo ya se incluyó, se salta todo hasta #endif (evita definiciones repetidas).
#ifndef GRAFICOS_H
// Marca el archivo como ya incluido.
#define GRAFICOS_H

// Este módulo usa panel.h, por eso se incluye aquí.
#include "panel.h"
```

- Guarda de inclusión (`GRAFICOS_H`) y `#include "panel.h"` (necesita `encender_pixel`, los colores y el tamaño del tablero).

**Líneas 9 a 14**

```c
// Ancho de un dígito de la fuente en columnas (3 bits por fila).
#define FUENTE_ANCHO 3U
// Alto de un dígito de la fuente en filas (5 filas por dígito).
#define FUENTE_ALTO 5U
// Cantidad de dígitos de la fuente (los dígitos 0 a 9).
#define FUENTE_CANTIDAD_DIGITOS 10U
```

- `FUENTE_ANCHO 3U` y `FUENTE_ALTO 5U`: cada dígito mide **3 columnas por 5 filas**.
- `FUENTE_CANTIDAD_DIGITOS 10U`: los dígitos de 0 a 9.

**Líneas 16 a 21**

```c
// Pone en negro todos los píxeles del tablero.
void borrar_pantalla(void);
// Dibuja solo el contorno de un rectángulo de ancho por alto píxeles. (x, y) es la esquina superior izquierda.
void dibujar_rectangulo(uint32_t x, uint32_t y, uint32_t ancho, uint32_t alto, uint32_t color);
// Dibuja el dígito (0 a 9) de 3x5 con la esquina superior izquierda en (x, y). Solo enciende los píxeles del dígito; los demás no se tocan.
void dibujar_digito(uint32_t x, uint32_t y, uint32_t digito, uint32_t color);
```

Tres funciones:
- `borrar_pantalla()`: pone todo el tablero en negro.
- `dibujar_rectangulo(x, y, ancho, alto, color)`: dibuja **solo el contorno** de un rectángulo; `(x, y)` es la esquina superior izquierda.
- `dibujar_digito(x, y, digito, color)`: dibuja un dígito de 3×5 con su esquina superior izquierda en `(x, y)`. Solo enciende los píxeles del dígito; **no borra** lo demás.

**Línea 23**

```c
#endif
```

- `#endif`.

### 3. `src/graficos.c`: la fuente, el borrado y las formas

**Líneas 1 a 2**

```c
// Se incluye su propia interfaz (graficos.h) para que el compilador compruebe que las funciones coinciden con sus prototipos.
#include "graficos.h"
```

- Incluye `graficos.h`.

**Líneas 4 a 29**

```c
// Fuente propia de 3x5 para los dígitos 0 a 9. Cada dígito son 5 bytes, uno por fila, de arriba abajo.
// Solo se usan los bits 0 a 2 de cada byte: el bit 2 es la columna izquierda y el bit 0 la columna derecha.
// Se escribe en binario con literales 0b... (extensión de GCC, que acepta arm-none-eabi-gcc).
// Es const, así que el arreglo va en FLASH (.rodata) y no ocupa RAM.
static const uint8_t fuente_digitos[FUENTE_CANTIDAD_DIGITOS][FUENTE_ALTO] = {
    // Dígito 0: 111 101 101 101 111.
    { 0b111, 0b101, 0b101, 0b101, 0b111 },
    // Dígito 1: 010 110 010 010 111.
    { 0b010, 0b110, 0b010, 0b010, 0b111 },
    // Dígito 2: 111 001 111 100 111.
    { 0b111, 0b001, 0b111, 0b100, 0b111 },
    // Dígito 3: 111 001 111 001 111.
    { 0b111, 0b001, 0b111, 0b001, 0b111 },
    // Dígito 4: 101 101 111 001 001.
    { 0b101, 0b101, 0b111, 0b001, 0b001 },
    // Dígito 5: 111 100 111 001 111.
    { 0b111, 0b100, 0b111, 0b001, 0b111 },
    // Dígito 6: 111 100 111 101 111.
    { 0b111, 0b100, 0b111, 0b101, 0b111 },
    // Dígito 7: 111 001 001 001 001.
    { 0b111, 0b001, 0b001, 0b001, 0b001 },
    // Dígito 8: 111 101 111 101 111.
    { 0b111, 0b101, 0b111, 0b101, 0b111 },
    // Dígito 9: 111 101 111 001 111.
    { 0b111, 0b101, 0b111, 0b001, 0b111 },
};
```

**La fuente de 3×5.** `fuente_digitos` es una tabla de 10 dígitos × 5 filas:
- `static const uint8_t fuente_digitos[10][5]`: 10 filas de la tabla (un dígito cada una) con 5 bytes (una fila de píxeles cada uno, de arriba hacia abajo).
- **Solo se usan los 3 bits bajos de cada byte**: el **bit 2 es la columna izquierda** y el **bit 0 la derecha**. Se escribe en binario con `0b...` (extensión de GCC, que acepta `arm-none-eabi-gcc`).
- Ejemplo, el dígito **0**: `0b111, 0b101, 0b101, 0b101, 0b111`:

```
111   ###
101   # #
101   # #
101   # #
111   ###
```

- Ejemplo, el **1**: `010 / 110 / 010 / 010 / 111`:

```
010    #
110   ##
010    #
010    #
111   ###
```

- **`const`**: la tabla nunca cambia, así que el linker la coloca en la FLASH (`.rodata`) y **no gasta RAM**. Cada dato de la tabla ocupa 1 byte (50 bytes en total).
- Los comentarios de cada dígito (por ejemplo, «Dígito 0: 111 101 101 101 111») muestran el dibujo en bits.

**Líneas 31 a 42**

```c
// Pone en negro todos los píxeles del tablero.
void borrar_pantalla(void)
{
    // Recorre todas las filas del tablero.
    for (uint32_t y = 0U; y < PANEL_ALTO; y++) {
        // Recorre todas las columnas de la fila.
        for (uint32_t x = 0U; x < PANEL_ANCHO; x++) {
            // Pone el píxel (x, y) en negro.
            encender_pixel(x, y, COLOR_NEGRO);
        }
    }
}
```

`borrar_pantalla()`: dos `for` anidados que recorren cada fila `y` y cada columna `x` y ponen `COLOR_NEGRO` con `encender_pixel`. Es la misma función `limpiar_pantalla` de la prueba 05, ahora como parte del módulo.

**Líneas 44 a 67**

```c
// Dibuja el contorno de un rectángulo: la fila de arriba, la de abajo, la columna izquierda y la derecha.
// Si el ancho o el alto son 0, no se dibuja nada: con alto = 0, alto - 1U daría una vuelta de uint32_t (0xFFFFFFFF).
void dibujar_rectangulo(uint32_t x, uint32_t y, uint32_t ancho, uint32_t alto, uint32_t color)
{
    // Ancho o alto en 0: no hay rectángulo que dibujar, se sale sin tocar el tablero.
    if (ancho == 0U || alto == 0U) {
        return;
    }
    // Recorre las columnas del rectángulo (de x hasta x + ancho - 1) para pintar la fila de arriba y la de abajo.
    for (uint32_t columna = x; columna < x + ancho; columna++) {
        // Fila de arriba del rectángulo.
        encender_pixel(columna, y, color);
        // Fila de abajo del rectángulo (y + alto - 1).
        encender_pixel(columna, y + alto - 1U, color);
    }
    // Recorre las filas del rectángulo (de y hasta y + alto - 1) para pintar la columna izquierda y la derecha.
    for (uint32_t fila = y; fila < y + alto; fila++) {
        // Columna izquierda del rectángulo.
        encender_pixel(x, fila, color);
        // Columna derecha del rectángulo (x + ancho - 1).
        encender_pixel(x + ancho - 1U, fila, color);
    }
    // Los píxeles que caen fuera del tablero los ignora encender_pixel, así que un rectángulo que se sale no escribe fuera del arreglo.
}
```

`dibujar_rectangulo(x, y, ancho, alto, color)` dibuja el **contorno**:
- Líneas 48-51: `if (ancho == 0U || alto == 0U) return;`. **Por qué:** con enteros **sin signo**, `alto - 1U` cuando `alto` es 0 daría `0xFFFFFFFF` (da la vuelta) y se dibujaría basura. Con ancho o alto en 0 no hay rectángulo, así que se sale sin hacer nada.
- Líneas 52-58: un `for` sobre las columnas del rectángulo (`columna` de `x` a `x + ancho - 1`). Para cada una pinta la **fila de arriba** `(columna, y)` y la **de abajo** `(columna, y + alto - 1)`.
- Líneas 59-65: un `for` sobre las filas (`fila` de `y` a `y + alto - 1`). Para cada una pinta la **columna izquierda** `(x, fila)` y la **derecha** `(x + ancho - 1, fila)`.
- Línea 66: si el rectángulo se sale del tablero, `encender_pixel` ignora los píxeles que caen fuera, así que no se escribe fuera del arreglo.

**Líneas 69 a 88**

```c
// Dibuja un dígito de 3x5 con la esquina superior izquierda en (x, y). Solo enciende los píxeles que valen 1 en la fuente.
void dibujar_digito(uint32_t x, uint32_t y, uint32_t digito, uint32_t color)
{
    // Si el número no es un dígito de la fuente (0 a 9), no se dibuja nada.
    if (digito >= FUENTE_CANTIDAD_DIGITOS) {
        return;
    }
    // Recorre las filas del dígito, de arriba abajo.
    for (uint32_t fila = 0U; fila < FUENTE_ALTO; fila++) {
        // Recorre las columnas del dígito, de izquierda a derecha.
        for (uint32_t columna = 0U; columna < FUENTE_ANCHO; columna++) {
            // El desplazamiento toma el bit de esta columna: la columna 0 (izquierda) es el bit 2 y la columna 2 (derecha) es el bit 0.
            // Se desplaza el byte de la fila y con & 1U se mira solo ese bit. Si vale 1, el píxel se enciende.
            if (((fuente_digitos[digito][fila] >> (FUENTE_ANCHO - 1U - columna)) & 1U) == 1U) {
                // Enciende el píxel del dígito en su posición dentro del tablero.
                encender_pixel(x + columna, y + fila, color);
            }
        }
    }
}
```

`dibujar_digito(x, y, digito, color)`:
- Líneas 72-75: si `digito >= 10` no es un dígito de la fuente y no se dibuja nada (evita leer fuera de la tabla).
- Línea 77: `for (fila = 0; fila < 5; ...)`: recorre las 5 filas del dígito, de arriba abajo.
- Línea 79: `for (columna = 0; columna < 3; ...)`: recorre las 3 columnas, de izquierda a derecha.
- Línea 82: `if (((fuente_digitos[digito][fila] >> (FUENTE_ANCHO - 1U - columna)) & 1U) == 1U)`: toma el **bit de esa columna**.
  - `fuente_digitos[digito][fila]` es el byte de esa fila.
  - `FUENTE_ANCHO - 1U - columna` = `2 - columna`: la columna 0 (izquierda) se corre 2 posiciones y queda en el bit 0, la columna 1 se corre 1 y la columna 2 (derecha) no se corre.
  - `>>` desplaza a la derecha y `& 1U` se queda solo con ese bit.
  - Si vale 1, ese píxel pertenece al dígito.
- Línea 84: `encender_pixel(x + columna, y + fila, color)`: lo enciende, desplazado a la posición `(x, y)` pedida.

### 4. `main.c`: el programa

**Líneas 1 a 6**

```c
// Se incluye la configuración del reloj y del temporizador SysTick.
#include "system_config.h"
// Se incluye el módulo del panel LED (framebuffer y refresco).
#include "panel.h"
// Se incluye el módulo gráfico (rectángulos y dígitos).
#include "graficos.h"
```

- Incluye el reloj, el panel y los gráficos.

**Líneas 8 a 31**

```c
// Columna donde empieza el primer dígito de cada fila.
#define COLUMNA_INICIAL_DIGITOS 6U
// Separación en columnas entre el inicio de un dígito y el siguiente: ancho 3 + 1 columna de separación.
#define SEPARACION_DIGITOS 4U
// Fila donde empieza la fila de dígitos de arriba.
#define FILA_DIGITOS_ARRIBA 3U
// Fila donde empieza la fila de dígitos de abajo.
#define FILA_DIGITOS_ABAJO 9U
// Cantidad de dígitos en cada fila: la fila de arriba muestra 0 a 4 y la de abajo 5 a 9.
#define DIGITOS_POR_FILA 5U
// Columna donde empieza la primera barra de colores.
#define COLUMNA_INICIAL_BARRAS 2U
// Separación en columnas entre el inicio de una barra y la siguiente: ancho 3 + 1 columna de separación.
#define SEPARACION_BARRAS 4U
// Ancho de cada barra en columnas.
#define ANCHO_BARRA 3U
// Alto de cada barra en filas.
#define ALTO_BARRA 12U
// Fila donde empiezan todas las barras.
#define FILA_BARRAS 2U
// Cantidad de barras: una por cada uno de los 7 colores de prueba.
#define CANTIDAD_BARRAS 7U
// Tiempo que se mantiene cada pantalla de prueba, en milisegundos.
#define TIEMPO_PANTALLA_MS 3000U
```

Constantes con nombre para **no escribir números sueltos** en el código:
- `COLUMNA_INICIAL_DIGITOS 6U`: columna donde empieza el primer dígito de cada fila.
- `SEPARACION_DIGITOS 4U`: de un dígito al siguiente hay 4 columnas (3 del dígito + 1 de espacio).
- `FILA_DIGITOS_ARRIBA 3U` y `FILA_DIGITOS_ABAJO 9U`: la fila donde empieza cada línea de dígitos (los dígitos miden 5 de alto: ocupan las filas 3 a 7 y 9 a 13).
- `DIGITOS_POR_FILA 5U`: 5 dígitos en cada línea (0 a 4 arriba y 5 a 9 abajo).
- `COLUMNA_INICIAL_BARRAS 2U`, `SEPARACION_BARRAS 4U`, `ANCHO_BARRA 3U`, `ALTO_BARRA 12U`, `FILA_BARRAS 2U`, `CANTIDAD_BARRAS 7U`: dónde y de qué tamaño son las 7 barras (una por color).
- `TIEMPO_PANTALLA_MS 3000U`: cada pantalla dura 3 s.

**Líneas 33 a 49**

```c
// Dibuja el marco blanco alrededor del tablero y los dígitos 0 a 9 en dos filas.
static void mostrar_marco_y_digitos(void)
{
    // Se borra el tablero antes de dibujar la nueva pantalla.
    borrar_pantalla();
    // Marco blanco: contorno del tablero completo, desde la esquina (0, 0) con el tamaño del panel.
    dibujar_rectangulo(0U, 0U, PANEL_ANCHO, PANEL_ALTO, COLOR_BLANCO);
    // Recorre las posiciones de los dígitos de una fila (0 a 4).
    for (uint32_t i = 0U; i < DIGITOS_POR_FILA; i++) {
        // Columna de este dígito: la columna inicial más la separación por cada dígito anterior.
        uint32_t posicion_x = COLUMNA_INICIAL_DIGITOS + SEPARACION_DIGITOS * i;
        // Fila de arriba: el dígito i (0 a 4) en verde.
        dibujar_digito(posicion_x, FILA_DIGITOS_ARRIBA, i, COLOR_VERDE);
        // Fila de abajo: el dígito i + 5 (5 a 9) en amarillo.
        dibujar_digito(posicion_x, FILA_DIGITOS_ABAJO, i + DIGITOS_POR_FILA, COLOR_AMARILLO);
    }
}
```

`mostrar_marco_y_digitos()`:
- `borrar_pantalla()`: empieza desde un tablero limpio.
- `dibujar_rectangulo(0, 0, PANEL_ANCHO, PANEL_ALTO, COLOR_BLANCO)`: el **marco blanco** de todo el tablero (esquina (0, 0) y el tamaño del panel).
- El `for i = 0 a 4`: `posicion_x = 6 + 4 * i` es la columna del dígito `i`. En esa columna dibuja el dígito `i` en **verde** en la fila de arriba (`dibujar_digito(posicion_x, 3, i, COLOR_VERDE)`) y el dígito `i + 5` en **amarillo** en la de abajo (`dibujar_digito(posicion_x, 9, i + 5, COLOR_AMARILLO)`).

**Líneas 51 a 63**

```c
// Dibuja siete barras verticales, una de cada color de prueba: rojo, verde, azul, amarillo, magenta, cian y blanco.
static void mostrar_siete_colores(void)
{
    // Se borra el tablero antes de dibujar la nueva pantalla.
    borrar_pantalla();
    // Color de cada barra, de izquierda a derecha.
    const uint32_t colores_de_prueba[CANTIDAD_BARRAS] = { COLOR_ROJO, COLOR_VERDE, COLOR_AZUL, COLOR_AMARILLO, COLOR_MAGENTA, COLOR_CIAN, COLOR_BLANCO };
    // Recorre las siete barras.
    for (uint32_t i = 0U; i < CANTIDAD_BARRAS; i++) {
        // Dibuja el contorno de la barra i en su color, con la columna y fila de inicio de las barras.
        dibujar_rectangulo(COLUMNA_INICIAL_BARRAS + SEPARACION_BARRAS * i, FILA_BARRAS, ANCHO_BARRA, ALTO_BARRA, colores_de_prueba[i]);
    }
}
```

`mostrar_siete_colores()`:
- `borrar_pantalla()`.
- `const uint32_t colores_de_prueba[7] = { COLOR_ROJO, COLOR_VERDE, COLOR_AZUL, COLOR_AMARILLO, COLOR_MAGENTA, COLOR_CIAN, COLOR_BLANCO };` los 7 colores en orden, de izquierda a derecha.
- El `for i = 0 a 6`: `dibujar_rectangulo(2 + 4 * i, 2, 3, 12, colores_de_prueba[i])`: una barra (solo contorno) de 3 de ancho y 12 de alto, en la columna `2 + 4i`, con el color `i`.

**Líneas 65 a 90**

```c
// Función principal: crt0.S la llama cuando termina de preparar la RAM.
int main(void)
{
    // Primero el reloj, antes de usar cualquier periférico: deja el sistema a 84 MHz.
    configurar_reloj();
    // Se enciende la base de tiempo de 1 ms (SysTick), que usa esperar_milisegundos.
    iniciar_systick();

    // Se configuran los pines del panel como salidas.
    configurar_panel();
    // Se enciende TIM3: desde aquí, una interrupción cada 1 ms dibuja una fase del framebuffer en el panel.
    iniciar_refresco_panel();

    // Bucle infinito: un microcontrolador no termina, repite esto mientras tenga energía.
    while (1) {
        // Pantalla 1: se debe ver un marco blanco alrededor del panel, los dígitos 0 a 4 en verde en la fila de arriba y los dígitos 5 a 9 en amarillo en la fila de abajo, durante 3 s.
        mostrar_marco_y_digitos();
        // Se espera TIEMPO_PANTALLA_MS (3 s) con esa pantalla visible.
        esperar_milisegundos(TIEMPO_PANTALLA_MS);

        // Pantalla 2: se deben ver siete barras contorneadas, de izquierda a derecha en rojo, verde, azul, amarillo, magenta, cian y blanco, durante 3 s.
        mostrar_siete_colores();
        // Se espera TIEMPO_PANTALLA_MS (3 s) con esa pantalla visible.
        esperar_milisegundos(TIEMPO_PANTALLA_MS);
    }
}
```

`main`:
- Líneas 68-76: igual que en la prueba 05: `configurar_reloj()`, `iniciar_systick()`, `configurar_panel()` y `iniciar_refresco_panel()` (desde aquí la interrupción de TIM3 refresca el panel).
- Líneas 79-89: bucle infinito que alterna: `mostrar_marco_y_digitos();` + `esperar_milisegundos(3000)` y después `mostrar_siete_colores();` + `esperar_milisegundos(3000)`.
- Mientras `main` espera, el panel se sigue refrescando solo.

