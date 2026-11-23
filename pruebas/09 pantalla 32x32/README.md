# Prueba 09: pantalla completa de 32×32 (dos paneles)

**Qué hace en la placa:** muestra una imagen fija en la **pantalla completa de 32×32** (dos paneles P10 de 32×16 apilados):
- un **marco verde** alrededor de toda la pantalla,
- un **dígito blanco en cada esquina** (1 arriba a la izquierda, 2 arriba a la derecha, 3 abajo a la izquierda, 4 abajo a la derecha), a 2 píxeles del borde,
- **dos filas con los 7 colores** (rojo, verde, azul, amarillo, magenta, cian, blanco) justo **en la unión de los dos paneles** (filas 15 y 16).

**Para qué sirve:** comprobar que **los dos paneles quedan bien ordenados como una sola pantalla**. Si el panel de abajo estuviera al revés o desordenado, los dígitos saldrían girados o en otra esquina y el marco quedaría cortado. Los dígitos distintos en cada esquina y la fila de colores en la unión permiten ver el error al primer vistazo.

**Qué se agrega respecto a la prueba 08:**
- `panel`: la pantalla pasa de 32×16 a **32×32**; `dibujar_fase` ahora envía **128 bits por fase** (2 paneles) y aplica el **giro de 180°** del panel lejano. Se quita `dibujar_fase_de_prueba` (ya cumplió su objetivo en la 08).
- `botones`: el sexto botón (`BOTON_F`, PA8) se reemplaza por **`BOTON_REINICIO`**, el **botón azul de la placa (PC13)**.
- Un `main.c` nuevo.

**Qué NO cambia:** `graficos`, `aleatorio`, `system_config`, `gpio_config`, `registros_f446.h`, `Makefile`, `linker_script.ld` y `crt0.S` son los de la 08. `snake.h` y `snake.c` siguen **sin usarse** en esta prueba; solo cambian en que la asignación de botones a direcciones se hizo según la posición física de los botones del shield (A = izquierda, B = abajo, C = derecha, D = arriba).

**Importante:**
- Aquí **sí se usa TIM3**: la interrupción refresca los paneles y `main` termina en un `while (1)` vacío.
- Ya **no se llama a `iniciar_systick()`**: esta prueba no usa esperas ni temporizadores.

### Cómo están conectados los dos paneles

Los paneles se conectan **en cadena**: la salida de datos del panel 1 (el que está pegado a la placa) entra al panel 2. Los 128 bits que se desplazan en cada fase recorren primero el panel 1 y terminan en el panel 2: el **primer bit** que se envía acaba en el panel **más lejano** (panel 2, el de abajo) y el **último** en el panel 1.

```
  placa ──► [ panel 1 ] ──► [ panel 2 ]     bits 64–127 → panel 1
             (arriba)         (abajo)        bits  0–63  → panel 2
                          (girado 180°)
```

- Panel 1 ocupa las filas **0 a 15** de la pantalla, panel 2 las filas **16 a 31**.
- El panel 2 está **montado girado 180°**: lo que para él es la esquina superior izquierda, en la pantalla es la inferior derecha. Por eso se invierten columnas y filas: `columna = 31 − x` y `fila = 31 − y`.

### 1. `inc/panel.h`: lo que cambia

**Líneas 32 a 35**

```c
// Bits que se desplazan por fase con los dos paneles encadenados: 64 por panel. Fuente: medición del Paso 11 (docs/mapeo_pixeles.md para el mapeo de un panel).
#define PANEL_BITS_POR_FASE 128U
// Bits que se desplazan por fase en un solo panel: 4 bloques de 16. Fuente: docs/mapeo_pixeles.md.
#define PANEL_BITS_POR_MODULO 64U
```

- `PANEL_BITS_POR_FASE 128U` (antes 64): ahora se desplazan **128 bits por fase** (2 paneles × 64).
- `PANEL_BITS_POR_MODULO 64U` (nuevo): bits de **un** panel por fase (4 bloques de 16). Un «módulo» es un panel.

**Líneas 36 a 39**

```c
// Ancho del tablero en píxeles (columnas x): un panel de 32 columnas.
#define PANEL_ANCHO 32U
// Alto del tablero en píxeles (filas y): dos paneles de 16 filas apilados.
#define PANEL_ALTO 32U
```

- `PANEL_ANCHO 32U`: las columnas siguen siendo 32.
- `PANEL_ALTO 32U` (antes 16): **dos paneles de 16 filas apilados**. Este cambio hace que el framebuffer pase a 32×32 bytes y que `dibujar_rectangulo`, `borrar_pantalla` y todo el módulo gráfico trabajen con la pantalla completa **sin cambiar una sola línea**: usan `PANEL_ALTO`, no un número fijo.

### 2. `src/panel.c`: `dibujar_fase` con dos paneles

**Líneas 91 a 98**

```c
// Dibuja una fase completa con los colores del framebuffer. Los 128 bits de la fase son 2 módulos de 64 bits:
//   modulo = bit / 64: 0 = panel 2 (abajo, el más lejano, girado 180 grados), 1 = panel 1 (arriba, conectado a la placa).
//   bit_en_modulo = bit % 64; bloque = bit_en_modulo / 16, j = bit_en_modulo % 16.
// Posición dentro del panel, según docs/mapeo_pixeles.md:
//   si j < 8:  x = 8 * bloque + (7 - j), y = fase        (de derecha a izquierda)
//   si j >= 8: x = 8 * bloque + (j - 8), y = fase + 4    (de izquierda a derecha)
// R2, G2 y B2 usan la fila y + 8 dentro del panel.
// Panel 2 girado 180 grados: columna = 31 - x, fila = 31 - y (y 31 - (y + 8) para R2, G2 y B2).
```

El comentario resume la regla nueva:
- `modulo = bit / 64`: de qué panel es el bit. **0 = panel 2** (abajo, el más lejano, girado 180°) y **1 = panel 1** (arriba, el conectado a la placa).
- `bit_en_modulo = bit % 64`: posición del bit dentro de su panel; de ahí salen `bloque = bit_en_modulo / 16` y `j = bit_en_modulo % 16`, **igual que en la prueba 04** (con un solo panel).
- Para el panel 2 se invierte todo: `columna = 31 − x`, `fila = 31 − y` (y `31 − (y + 8)` para R2, G2 y B2).

**Líneas 99 a 102**

```c
static void dibujar_fase(uint32_t fase)
{
    // Se desplazan los 128 bits de la fase, uno por uno, con CLK.
    for (uint32_t bit = 0U; bit < PANEL_BITS_POR_FASE; bit++) {
```

- `static void dibujar_fase(fase)`: envía una fase completa. **`static`** = solo la usa `TIM3_IRQHandler`, que está en este archivo.
- Línea 102: `for (bit = 0; bit < PANEL_BITS_POR_FASE; bit++)`: **128 vueltas**, una por cada bit de la cadena (antes eran 64).

**Líneas 103 a 110**

```c
        // Módulo al que pertenece el bit: 0 = panel 2 (abajo), 1 = panel 1 (arriba).
        uint32_t modulo = bit / PANEL_BITS_POR_MODULO;
        // Posición del bit dentro de su módulo (0 a 63).
        uint32_t bit_en_modulo = bit % PANEL_BITS_POR_MODULO;
        // Bloque de 16 bits al que pertenece el bit dentro del módulo (0 a 3).
        uint32_t bloque = bit_en_modulo / PANEL_BITS_POR_BLOQUE;
        // Posición del bit dentro de su bloque (0 a 15).
        uint32_t j = bit_en_modulo % PANEL_BITS_POR_BLOQUE;
```

Se descompone el número de bit en dos paneles y los bloques de cada uno:
- Línea 104: `modulo = bit / PANEL_BITS_POR_MODULO;`: división entera. Bits 0 a 63 → módulo 0; bits 64 a 127 → módulo 1.
- Línea 106: `bit_en_modulo = bit % PANEL_BITS_POR_MODULO;`: el resto, de 0 a 63. **Dentro de cada panel el orden es el mismo**, por eso se vuelve a empezar en 0.
- Línea 108: `bloque = bit_en_modulo / 16;` (0 a 3): bloque de 8 columnas del panel.
- Línea 110: `j = bit_en_modulo % 16;` (0 a 15): posición dentro del bloque.

**Líneas 111 a 127**

```c
        // Columna del píxel de la mitad de arriba dentro del panel.
        uint32_t x;
        // Fila del píxel de la mitad de arriba dentro del panel.
        uint32_t y;
        // Mitad j < 8: las columnas van de derecha a izquierda y la fila es la de la fase.
        if (j < PANEL_COLUMNAS_POR_BLOQUE) {
            // Columna x: inicio del bloque más la posición contada de derecha a izquierda.
            x = PANEL_COLUMNAS_POR_BLOQUE * bloque + (PANEL_COLUMNAS_POR_BLOQUE - 1U - j);
            // La fila es la de la fase.
            y = fase;
        // Mitad j >= 8: las columnas van de izquierda a derecha y la fila es la de la fase + 4.
        } else {
            // Columna x: inicio del bloque más la posición contada de izquierda a derecha.
            x = PANEL_COLUMNAS_POR_BLOQUE * bloque + (j - PANEL_COLUMNAS_POR_BLOQUE);
            // La fila es la de la fase más 4.
            y = fase + PANEL_SEPARACION_FILAS;
        }
```

Esta parte **no cambia**: calcula `(x, y)` dentro del panel (ver README de la prueba 04):
- `j < 8`: `x = 8 * bloque + (7 − j)` (de derecha a izquierda) y `y = fase`.
- `j ≥ 8`: `x = 8 * bloque + (j − 8)` (de izquierda a derecha) y `y = fase + 4`.
Es la posición **dentro del panel**, sin importar si es el 1 o el 2.

**Líneas 128 a 150**

```c
        // Columna y filas en el tablero completo de 32x32.
        uint32_t columna;
        // Fila de la mitad superior del panel (la de los bits R1, G1, B1).
        uint32_t fila_superior;
        // Fila de la mitad inferior del panel (la de los bits R2, G2, B2).
        uint32_t fila_inferior;
        // Panel 1 (arriba): sin giro, la fila de abajo es la fila de arriba + 8.
        if (modulo == 1U) {
            // Sin giro: la columna es la x.
            columna = x;
            // La fila superior es la y.
            fila_superior = y;
            // La fila inferior está 8 filas más abajo.
            fila_inferior = y + PANEL_FILAS_MITAD_SUPERIOR;
        // Panel 2 (abajo, girado 180 grados): la columna y las filas se cuentan desde el otro lado.
        } else {
            // Girado 180°: la columna se cuenta desde el borde contrario.
            columna = (PANEL_ANCHO - 1U) - x;
            // La fila superior se cuenta desde abajo.
            fila_superior = (PANEL_ALTO - 1U) - y;
            // La fila inferior también se cuenta desde abajo.
            fila_inferior = (PANEL_ALTO - 1U) - (y + PANEL_FILAS_MITAD_SUPERIOR);
        }
```

Nuevo: pasar de «posición en el panel» a «posición en la pantalla de 32×32».
- Líneas 129-133: tres variables: `columna`, `fila_superior` y `fila_inferior` (la fila de R1 G1 B1 y la de R2 G2 B2).
- Líneas 135-141, **panel 1** (`modulo == 1`): sin giro. `columna = x`, `fila_superior = y` y `fila_inferior = y + 8` (la mitad de abajo del panel está 8 filas más abajo). Ocupa las filas 0 a 15.
- Líneas 143-149, **panel 2** (el resto, `modulo == 0`): **girado 180°**.
  - `columna = 31 − x`: la columna 0 del panel es la 31 de la pantalla, la 1 la 30, etc.
  - `fila_superior = 31 − y` y `fila_inferior = 31 − (y + 8)`: lo mismo con las filas. Por ejemplo, `y = 0` → fila 31 (la última de la pantalla) e `y + 8 = 8` → fila 23.
  - Así las filas del panel 2 caen en la zona 16 a 31 de la pantalla.
- **Por qué se invierte con `(PANEL_ANCHO − 1U) − x`:** girar 180° equivale a espejar columnas **y** filas a la vez; el `− 1` es porque el último índice de 32 columnas es 31, no 32.

**Líneas 151 a 155**

```c
        // datos: bits 0 a 2 = R1, G1, B1 (fila superior); bits 3 a 5 = R2, G2, B2 (fila inferior), desplazados 3 posiciones.
        uint32_t datos = framebuffer[fila_superior][columna] | (framebuffer[fila_inferior][columna] << PANEL_DESPLAZAMIENTO_MITAD_INFERIOR);
        // Se desplazan los 6 bits de color de este píxel.
        desplazar_bit(datos);
    }
```

- Línea 152: `datos = framebuffer[fila_superior][columna] | (framebuffer[fila_inferior][columna] << 3);`: los 3 bits de color de la fila superior (R1 G1 B1, bits 0 a 2) más los de la inferior desplazados 3 posiciones (R2 G2 B2, bits 3 a 5). Igual que en la 04, pero leyendo las filas y la columna ya calculadas.
- Línea 154: `desplazar_bit(datos)` saca los 6 bits y da un pulso de CLK.
- Línea 155: cierra el `for`.

**Líneas 156 a 168**

```c
    // OE apagado mientras cambian LAT y la fase: así no se ve basura durante el cambio.
    escribir_pin(GPIOC, PIN_PANEL_OE, NIVEL_OE_APAGADO);
    // LAT en 1: el latch pasa los 128 bits desplazados a la salida. Va después de desplazar todos los bits.
    escribir_pin(GPIOC, PIN_PANEL_LAT, 1U);
    // LAT en 0: termina el pulso de latch.
    escribir_pin(GPIOC, PIN_PANEL_LAT, 0U);
    // A toma el bit 0 de la fase (selección de fila dentro del escaneo 1/4).
    escribir_pin(GPIOC, PIN_PANEL_A, fase & 1U);
    // B toma el bit 1 de la fase.
    escribir_pin(GPIOC, PIN_PANEL_B, (fase >> 1U) & 1U);
    // OE encendido: el panel muestra la fase recién cargada.
    escribir_pin(GPIOC, PIN_PANEL_OE, NIVEL_OE_ENCENDIDO);
}
```

Igual que en la 04: **OE apagado, pulso de LAT, fase en A y B, OE encendido**. Solo cambia el comentario de LAT: ahora el latch captura **128 bits** (los dos paneles) en lugar de 64.

### 3. `inc/botones.h`: lo que cambia

**Líneas 19 a 25**

```c
// Bit del botón de reinicio en el valor que devuelve leer_botones (1 = presionado): el botón azul de la placa, PC13.
#define BOTON_REINICIO (1U << 5)

// Configura los cinco botones del shield y el botón azul de la placa como entradas con pull-up interno.
void configurar_botones(void);
// Devuelve un valor con un bit por cada botón presionado (BOTON_A a BOTON_E y BOTON_REINICIO). Un bit en 1 = botón presionado.
uint32_t leer_botones(void);
```

- `BOTON_REINICIO (1U << 5)` reemplaza a `BOTON_F`: sigue siendo el **bit 5**, pero ahora es el **botón azul de la placa (PC13)**, no un botón del shield. Los otros cinco no cambian.
- Los comentarios de `configurar_botones` y `leer_botones` pasan de «seis botones» a «cinco botones del shield y el botón azul de la placa».

### 4. `src/botones.c`: lo que cambia

**Líneas 14 a 15**

```c
// Número del pin del botón azul de la placa: PC13, activo en bajo (presionado = 0).
#define PIN_BOTON_REINICIO 13U
```

`PIN_BOTON_REINICIO 13U`: el botón azul de la placa NUCLEO está en el pin **PC13**. Es activo en bajo (presionado = 0), igual que los demás.

**Líneas 49 a 50**

```c
    // Botón azul de la placa (PC13) en el puerto C.
    configurar_entrada_con_pull_up(GPIOC, PIN_BOTON_REINICIO);
```

`configurar_entrada_con_pull_up(GPIOC, PIN_BOTON_REINICIO)`: se configura PC13 como entrada con pull-up, ahora en el **puerto C** (el mismo puerto de los pines del panel, y no el A como PA8).

**Líneas 83 a 87**

```c
    // Botón azul de la placa (PC13): presionado = 0.
    if (leer_pin(GPIOC, PIN_BOTON_REINICIO) == 0U) {
        // Se pone en 1 el bit del botón de reinicio.
        botones |= BOTON_REINICIO;
    }
```

`leer_botones` lee PC13 con `leer_pin(GPIOC, PIN_BOTON_REINICIO)` y, si vale 0 (presionado), pone en 1 el bit `BOTON_REINICIO`. Es el mismo patrón de los otros botones.

### 5. `main.c`: la imagen de prueba

**Líneas 1 a 6**

```c
// Prueba de la pantalla de 32x32 (dos paneles): marco, un dígito en cada esquina y los 7 colores en la unión de los paneles.
#include "system_config.h"
// Se incluye el módulo del panel LED (framebuffer y refresco).
#include "panel.h"
// Se incluye el módulo gráfico (rectángulos y dígitos).
#include "graficos.h"
```

- Comentario con lo que muestra la prueba e `#include` del reloj, el panel y los gráficos. No incluye `botones.h`: esta prueba **no usa botones**.

**Líneas 8 a 27**

```c
// Función principal: crt0.S la llama cuando termina de preparar la RAM.
int main(void)
{
    // Colores de la fila de prueba, de izquierda a derecha: rojo, verde, azul, amarillo, magenta, cian y blanco.
    const uint32_t COLORES_DE_PRUEBA[7] = {
        // Barra 1: rojo.
        COLOR_ROJO,
        // Barra 2: verde.
        COLOR_VERDE,
        // Barra 3: azul.
        COLOR_AZUL,
        // Barra 4: amarillo.
        COLOR_AMARILLO,
        // Barra 5: magenta.
        COLOR_MAGENTA,
        // Barra 6: cian.
        COLOR_CIAN,
        // Barra 7: blanco.
        COLOR_BLANCO
    };
```

`const uint32_t COLORES_DE_PRUEBA[7] = {...}`: los siete colores en el orden en que se dibujarán de izquierda a derecha: rojo, verde, azul, amarillo, magenta, cian y blanco. Es `const` porque no cambia (se guarda en FLASH).

**Líneas 28 a 33**

```c
    // Primero el reloj, antes de usar cualquier periférico: deja el sistema a 84 MHz.
    configurar_reloj();
    // Se configuran los pines del panel como salidas.
    configurar_panel();
    // Se enciende TIM3: desde aquí la interrupción refresca el panel cada 1 ms, sin necesidad de llamarla desde main.
    iniciar_refresco_panel();
```

Preparación:
- `configurar_reloj()`: sistema a 84 MHz (TIM3 recibe 84 MHz).
- `configurar_panel()`: los 11 pines del panel como salidas.
- `iniciar_refresco_panel()`: enciende TIM3. **Desde aquí una interrupción cada 1 ms refresca el panel** con el contenido del framebuffer; `main` no tiene que llamar a nada más.
- Lo que se dibuja a continuación solo escribe en el framebuffer; la interrupción lo va mostrando en el panel en cuanto cambia.

**Líneas 35 a 36**

```c
    // Marco verde alrededor de todo el tablero: la esquina superior izquierda en (0, 0) y el tamaño del tablero.
    dibujar_rectangulo(0U, 0U, PANEL_ANCHO, PANEL_ALTO, COLOR_VERDE);
```

`dibujar_rectangulo(0, 0, PANEL_ANCHO, PANEL_ALTO, COLOR_VERDE)`: **marco verde** de toda la pantalla (32×32), desde la esquina (0, 0). Como `PANEL_ALTO` ahora es 32, el marco cubre los dos paneles.

**Líneas 37 a 44**

```c
    // Dígito 1 blanco en la esquina superior izquierda, a 2 píxeles del borde.
    dibujar_digito(2U, 2U, 1U, COLOR_BLANCO);
    // Dígito 2 blanco en la esquina superior derecha, a 2 píxeles del borde.
    dibujar_digito(PANEL_ANCHO - 2U - FUENTE_ANCHO, 2U, 2U, COLOR_BLANCO);
    // Dígito 3 blanco en la esquina inferior izquierda, a 2 píxeles del borde.
    dibujar_digito(2U, PANEL_ALTO - 2U - FUENTE_ALTO, 3U, COLOR_BLANCO);
    // Dígito 4 blanco en la esquina inferior derecha, a 2 píxeles del borde.
    dibujar_digito(PANEL_ANCHO - 2U - FUENTE_ANCHO, PANEL_ALTO - 2U - FUENTE_ALTO, 4U, COLOR_BLANCO);
```

Cuatro dígitos blancos, uno por esquina, **a 2 píxeles del borde** (cada dígito mide 3×5):
- Dígito **1**, arriba a la izquierda: `dibujar_digito(2, 2, 1, BLANCO)`.
- Dígito **2**, arriba a la derecha: `x = PANEL_ANCHO − 2 − FUENTE_ANCHO` = 32 − 2 − 3 = **27**, `y = 2`.
- Dígito **3**, abajo a la izquierda: `x = 2`, `y = PANEL_ALTO − 2 − FUENTE_ALTO` = 32 − 2 − 5 = **25**.
- Dígito **4**, abajo a la derecha: `x = 27`, `y = 25`.
- Se calculan con las constantes (no con 27 ni 25) para que, si cambia el tamaño de la pantalla, sigan en las esquinas.
- **Qué se debe ver:** los 4 dígitos **derechos** (no girados ni espejados) y cada uno en su esquina. Si el panel de abajo estuviera mal girado, el 3 y el 4 saldrían al revés o intercambiados.

**Líneas 46 a 52**

```c
    // Dos filas de colores en x = 12 a 18: la fila 15 es la última del panel 1 y la 16 es la primera del panel 2.
    for (uint32_t i = 0U; i < 7U; i++) {
        // Píxel de la fila 15 con el color i.
        encender_pixel(12U + i, 15U, COLORES_DE_PRUEBA[i]);
        // Píxel de la fila 16 con el mismo color i.
        encender_pixel(12U + i, 16U, COLORES_DE_PRUEBA[i]);
    }
```

La fila de colores en la **unión** de los paneles:
- `for (i = 0; i < 7; i++)`: una vuelta por color.
- `encender_pixel(12 + i, 15, COLORES_DE_PRUEBA[i])`: píxel de la **fila 15** (la última del panel 1) en la columna `12 + i` (de 12 a 18).
- `encender_pixel(12 + i, 16, COLORES_DE_PRUEBA[i])`: el mismo color en la **fila 16** (la primera del panel 2).
- Resultado: una barra de **2 filas de alto y 7 columnas**, mitad en cada panel. Si los paneles están bien alineados, se ve como **una sola barra continua** sin escalón; si el panel 2 estuviera desplazado, se vería partida.

**Líneas 54 a 57**

```c
    // El refresco sigue por la interrupción de TIM3; main no hace nada más.
    while (1) {
    }
}
```

`while (1) { }`: bucle infinito vacío. `main` **no puede terminar** (no hay a dónde volver en bare metal), y no necesita hacer nada: el refresco por interrupción de TIM3 sigue dibujando la imagen en los paneles.

