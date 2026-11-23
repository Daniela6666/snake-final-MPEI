# Prueba 08: orden serial de los dos paneles (diagnóstico)

**Qué hace en la placa:** es una **prueba de diagnóstico** del orden en que los bits recorren los **dos paneles encadenados**. Enciende **un solo bit** de la cadena de 128 y deja ver en qué píxel aparece. Con los botones se mueve ese bit:
- **A** / **B**: el bit avanza / retrocede **1** posición (0 a 127, da la vuelta).
- **E** / **F**: el bit avanza / retrocede **un bloque de 16**.
- **C** / **D**: cambia la **fase** que se muestra (0 a 3), hacia adelante / hacia atrás.

El bit encendido pone en 1 a la vez **G1** (verde, mitad de arriba) y **R2** (rojo, mitad de abajo), así en el panel se ve **un píxel verde y uno rojo** a 8 filas de distancia.

**Para qué sirve:** con dos paneles en cadena (128 bits por fase) hay que saber **qué bit va a qué píxel**: en qué panel cae, en qué columna y en qué fila. Se prueba bit por bit en la placa y se anota dónde aparece. Esa tabla es la que da las fórmulas de la prueba 09 (`modulo = bit / 64`, panel lejano girado 180°, etc.).

**Qué se agrega respecto a la prueba 07:**
- `dibujar_fase_de_prueba` y `PANEL_BITS_POR_CADENA` en `panel`: desplaza 128 bits con un solo bit encendido.
- `obtener_milisegundos` en `system_config`: milisegundos desde el arranque.
- `dibujar_numero` en `graficos`: dibuja un número de 4 dígitos.
- El módulo `aleatorio`: generador de números pseudoaleatorios (LFSR).
- Los archivos `snake.h` y `snake.c` (el juego): **se compilan pero esta prueba no los usa**.
- Un `main.c` nuevo.

**Qué NO cambia:** `botones`, `gpio_config`, `registros_f446.h`, `Makefile`, `linker_script.ld`, `crt0.S`. Lo demás de `panel.c`, `graficos.c` y `system_config.c` es igual que en la 07.

**Importante:** en esta prueba **no se inicia TIM3**. No hay refresco por interrupción: `main` llama a `dibujar_fase_de_prueba` **en cada vuelta** del bucle. Solo se ve **una fase** (4 filas de las 16 por panel, en las filas `fase`, `fase + 4`, `fase + 8` y `fase + 12`), pero como el bit encendido es uno solo, basta para ver dónde cae.

### Detalle del orden de la cadena
Los datos se desplazan de un panel al siguiente: el **primer bit** que se envía es el que queda **más lejos** (en el último panel) y el **último bit** queda en el panel más cercano a la placa. Por eso, en la prueba 09, `bit / 64` da el panel: bits 0–63 → panel lejano y bits 64–127 → panel cercano.

### 1. `src/system_config.c`: lo nuevo

**Líneas 122 a 127**

```c
// Devuelve los milisegundos transcurridos desde que se inició SysTick.
uint32_t obtener_milisegundos(void)
{
    // El contador es un entero de 32 bits y se lee de una sola vez: la lectura no se parte aunque la interrupción lo cambie.
    return contador_milisegundos;
}
```

`obtener_milisegundos()`: devuelve cuántos milisegundos pasaron desde el arranque (el valor de `contador_milisegundos`, que SysTick suma cada 1 ms).
- **Para qué:** el juego lo usa como **semilla** del generador aleatorio: el momento en que el jugador presiona su primer botón es distinto cada vez, así cada partida empieza con números distintos.
- **Por qué es seguro leerlo:** el contador es un entero de **32 bits** y el procesador de 32 bits lo lee **de una sola instrucción**; la interrupción no puede cambiarlo a la mitad de la lectura.
- Es una función porque `contador_milisegundos` es `static`: otros archivos no pueden verla, pero sí llamar a esta función. La declaración está en `system_config.h` (líneas 18-19).

### 2. `inc/panel.h`: lo nuevo

**Líneas 81 a 85**

```c
// Solo para la prueba del orden serial: bits de la cadena de los dos paneles encadenados.
#define PANEL_BITS_POR_CADENA 128U

// Solo para la prueba del orden serial: desplaza la cadena con un solo bit encendido (G1 y R2) en la fase indicada.
void dibujar_fase_de_prueba(uint32_t bit_encendido, uint32_t fase);
```

- `PANEL_BITS_POR_CADENA 128U`: bits de la cadena completa de 2 paneles por fase (2 × 64). En esta prueba aún se trabaja con el framebuffer de un panel, pero la cadena física tiene 128 bits.
- Prototipo de `dibujar_fase_de_prueba(bit_encendido, fase)`: solo se usa en esta prueba. Deja un solo bit en 1.

### 3. `src/panel.c`: `dibujar_fase_de_prueba`

**Líneas 192 a 194**

```c
// Desplaza PANEL_BITS_POR_CADENA bits. Solo el bit bit_encendido sale en 1 (G1 y R2), así se ve en qué píxel aparece.
void dibujar_fase_de_prueba(uint32_t bit_encendido, uint32_t fase)
{
```

`dibujar_fase_de_prueba(bit_encendido, fase)`: hace lo mismo que `dibujar_fase` (desplazar, latch, elegir fila), pero en vez de leer el framebuffer **envía ceros y un solo 1**.

**Líneas 195 a 201**

```c
    // Se desplazan los 128 bits de la cadena, uno por uno, con CLK.
    for (uint32_t bit = 0U; bit < PANEL_BITS_POR_CADENA; bit++) {
        // Si este es el bit encendido, G1 (mitad de arriba) y R2 (mitad de abajo) salen en 1; si no, todo en 0.
        uint32_t datos = ((bit == bit_encendido) ? ((1U << PIN_PANEL_G1) | (1U << PIN_PANEL_R2)) : 0U);
        // Se desplazan los 6 bits de color de este bit.
        desplazar_bit(datos);
    }
```

- Línea 196: `for (bit = 0; bit < 128; bit++)`: se envían los **128 bits** de la cadena, uno por uno.
- Línea 198: `datos = (bit == bit_encendido) ? ((1U << PIN_PANEL_G1) | (1U << PIN_PANEL_R2)) : 0U;`
  - Si este es el bit elegido, `datos` vale `0b001010` (= 10): bits 1 (G1) y 3 (R2) en 1. Los otros colores quedan en 0.
  - Si no es el bit elegido, `datos` vale 0: todos los colores apagados.
  - **Por qué G1 y R2 juntos:** G1 enciende la mitad superior del panel y R2 la inferior, así se ven **dos puntos de colores distintos** (verde y rojo) y se distingue cuál es cuál.
- Línea 200: `desplazar_bit(datos)`: saca los 6 bits por los pines R1…B2 y da un pulso de CLK (ver README de la prueba 04).

**Líneas 202 a 213**

```c
    // OE apagado mientras cambian LAT y la fase: así no se ve basura durante el cambio.
    escribir_pin(GPIOC, PIN_PANEL_OE, NIVEL_OE_APAGADO);
    // LAT en 1: el latch pasa los bits desplazados a la salida. Va después de desplazar todos los bits.
    escribir_pin(GPIOC, PIN_PANEL_LAT, 1U);
    // LAT en 0: termina el pulso de latch.
    escribir_pin(GPIOC, PIN_PANEL_LAT, 0U);
    // A toma el bit 0 de la fase (selección de fila dentro del escaneo 1/4).
    escribir_pin(GPIOC, PIN_PANEL_A, fase & 1U);
    // B toma el bit 1 de la fase.
    escribir_pin(GPIOC, PIN_PANEL_B, (fase >> 1U) & 1U);
    // OE encendido: el panel muestra la fase recién cargada.
    escribir_pin(GPIOC, PIN_PANEL_OE, NIVEL_OE_ENCENDIDO);
```

Termina igual que `dibujar_fase` (secuencia de la prueba 04):
- `OE = NIVEL_OE_APAGADO`: se apaga el panel mientras se cambia de fase.
- `LAT = 1` y luego `LAT = 0`: pulso de latch; los bits desplazados pasan a las salidas.
- `A = fase & 1` y `B = (fase >> 1) & 1`: la fase (0 a 3) en 2 bits elige qué grupo de filas se enciende (escaneo 1/4).
- `OE = NIVEL_OE_ENCENDIDO`: se enciende el panel con lo recién cargado.

**Línea 214**

```c
}
```

- Llave que cierra la función.

### 4. `inc/graficos.h`: lo nuevo

**Líneas 15 a 20**

```c
// Columnas vacías entre dos dígitos al dibujar un número.
#define FUENTE_SEPARACION 1U
// Cantidad de dígitos que dibuja dibujar_numero: siempre 4, con ceros a la izquierda.
#define NUMERO_CANTIDAD_DIGITOS 4U
// Ancho total en columnas de un número de NUMERO_CANTIDAD_DIGITOS dígitos: los dígitos más las separaciones entre ellos.
#define NUMERO_ANCHO (NUMERO_CANTIDAD_DIGITOS * FUENTE_ANCHO + (NUMERO_CANTIDAD_DIGITOS - 1U) * FUENTE_SEPARACION)
```

- `FUENTE_SEPARACION 1U`: una columna vacía entre dígitos.
- `NUMERO_CANTIDAD_DIGITOS 4U`: los números siempre se dibujan con **4 dígitos**, con ceros a la izquierda (7 se ve `0007`).
- `NUMERO_ANCHO`: ancho total en columnas = 4 dígitos × 3 + 3 separaciones × 1 = **15 columnas**. Los paréntesis protegen la macro.

**Líneas 28 a 29**

```c
// Dibuja el número con la esquina superior izquierda en (x, y), con NUMERO_CANTIDAD_DIGITOS dígitos y ceros a la izquierda. Si valor es mayor que 9999, muestra solo sus últimos 4 dígitos. No borra lo que haya debajo.
void dibujar_numero(uint32_t x, uint32_t y, uint32_t valor, uint32_t color);
```

- Prototipo de `dibujar_numero(x, y, valor, color)`: dibuja el número con la esquina superior izquierda en `(x, y)`. Si `valor` pasa de 9999 muestra solo sus últimos 4 dígitos. No borra lo que haya debajo.

### 5. `src/graficos.c`: `dibujar_numero`

**Líneas 90 a 102**

```c
// Dibuja un número con NUMERO_CANTIDAD_DIGITOS dígitos, con la esquina superior izquierda en (x, y). Los ceros a la izquierda se dibujan.
void dibujar_numero(uint32_t x, uint32_t y, uint32_t valor, uint32_t color)
{
    // Recorre las posiciones de los dígitos de derecha a izquierda: la posición 4 es la de unidades y la posición 1 la de millares.
    for (uint32_t posicion = NUMERO_CANTIDAD_DIGITOS; posicion > 0U; posicion--) {
        // Dígito de esta posición: el resto de dividir el valor entre 10 (el último dígito que queda).
        uint32_t digito = valor % 10U;
        // Quita el último dígito del valor para que el siguiente paso tome el anterior.
        valor = valor / 10U;
        // Dibuja el dígito en su columna: el desplazamiento es (posicion - 1) veces el ancho de un dígito más la separación. Las unidades (posicion 4) quedan a la derecha, con desplazamiento 3 * 4 = 12.
        dibujar_digito(x + (posicion - 1U) * (FUENTE_ANCHO + FUENTE_SEPARACION), y, digito, color);
    }
}
```

`dibujar_numero(x, y, valor, color)`: separa el número en dígitos y dibuja cada uno con `dibujar_digito`.
- Línea 94: `for (posicion = 4; posicion > 0; posicion--)`: recorre de **derecha a izquierda**: posición 4 = unidades, 3 = decenas, 2 = centenas, 1 = millares. Se va de derecha a izquierda porque **el último dígito de un número es el más fácil de sacar**.
- Línea 96: `digito = valor % 10U;` el resto de dividir entre 10 es el **último dígito** (por ejemplo, 1234 % 10 = 4).
- Línea 98: `valor = valor / 10U;` quita ese dígito (1234 → 123) para que en la siguiente vuelta se tome el anterior.
- Línea 100: `dibujar_digito(x + (posicion - 1) * (3 + 1), y, digito, color)`: la columna de cada dígito es `x` más `(posicion - 1)` veces **4** (ancho 3 + separación 1). Las unidades (posición 4) quedan en `x + 12`; los millares (posición 1) en `x`.
- **Por qué sale «los últimos 4 dígitos»:** el bucle solo da 4 vueltas; si el valor tiene más dígitos, los de la izquierda nunca se dibujan (12345 → `2345`).
- **Los ceros a la izquierda se dibujan** porque el bucle siempre hace las 4 vueltas: 7 → `0007`.

### 6. `inc/aleatorio.h`: interfaz del generador aleatorio

**Líneas 1 a 7**

```c
// Guarda de inclusión: si este archivo ya se incluyó, se salta todo hasta #endif (evita definiciones repetidas).
#ifndef ALEATORIO_H
// Marca el archivo como ya incluido.
#define ALEATORIO_H

// Tipos de entero de tamaño fijo (uint32_t, uint16_t, uint8_t...).
#include <stdint.h>
```

- Guarda de inclusión (`ALEATORIO_H`) e `#include <stdint.h>` (para `uint32_t`; no necesita nada más).

**Líneas 9 a 12**

```c
// Pone la semilla del generador. Si la semilla queda en 0, se usa 1 en su lugar.
void sembrar_aleatorio(uint32_t semilla);
// Devuelve el siguiente número pseudoaleatorio de 16 bits (LFSR de Fibonacci).
uint32_t siguiente_aleatorio(void);
```

- `sembrar_aleatorio(semilla)`: da el valor inicial del generador. Si la semilla da 0 se usa 1.
- `siguiente_aleatorio()`: devuelve el siguiente número pseudoaleatorio de 16 bits.
- **Pseudoaleatorio**: sale de una fórmula, no del azar. Misma semilla → misma secuencia. Por eso se siembra con `obtener_milisegundos()`: así cada partida es distinta.

**Línea 14**

```c
#endif
```

- `#endif`.

### 7. `src/aleatorio.c`: el generador (LFSR)

**Líneas 1 a 2**

```c
// Se incluye su propia interfaz (aleatorio.h) para que el compilador compruebe que las funciones coinciden con sus prototipos.
#include "aleatorio.h"
```

- Incluye `aleatorio.h`.

**Líneas 4 a 7**

```c
// Cantidad de desplazamientos del LFSR que se hacen en cada llamada a siguiente_aleatorio.
#define DESPLAZAMIENTOS_POR_LLAMADA 16U
// Semilla de reemplazo: si la semilla pedida da 0, el LFSR usa 1 en su lugar.
#define SEMILLA_DE_REEMPLAZO 1U
```

- `DESPLAZAMIENTOS_POR_LLAMADA 16U`: cuántos pasos del LFSR se dan en cada número pedido (explicado abajo).
- `SEMILLA_DE_REEMPLAZO 1U`: semilla que se usa si la pedida da 0.

**Líneas 9 a 11**

```c
// Estado del LFSR de 16 bits. Nunca puede valer 0: un LFSR en 0 se queda en 0 para siempre.
// Empieza en 1 para que el generador funcione aunque nunca se haya sembrado.
static uint16_t estado_lfsr = 1U;
```

**El estado del generador.** `static uint16_t estado_lfsr = 1U;`: un número de **16 bits** que cambia en cada paso.
- **`static`**: privado de este archivo y **persiste entre llamadas** (se guarda en `.data`).
- **Nunca puede valer 0**: un LFSR que llega a 0 se queda en 0 para siempre (todo XOR de ceros da 0).
- Empieza en **1** para que funcione aunque nadie lo haya sembrado.

**Qué es un LFSR** (*Linear Feedback Shift Register*): un registro de bits que se **desplaza** y por un extremo recibe un bit nuevo calculado con **XOR** de algunos bits del propio registro (los *taps*). Con los taps correctos recorre **65 535 valores distintos** (todos menos el 0) antes de repetir. Es muy barato: solo desplazamientos y XOR, sin multiplicar ni dividir.

**Líneas 13 a 23**

```c
// Pone el estado inicial del generador.
void sembrar_aleatorio(uint32_t semilla)
{
    // Se guardan solo los 16 bits bajos de la semilla, que es el tamaño del estado.
    estado_lfsr = (uint16_t)(semilla & 0xFFFFU);
    // Si la semilla quedó en 0, el LFSR se quedaría en 0 para siempre: se usa la semilla de reemplazo.
    if (estado_lfsr == 0U) {
        // Se usa la semilla de reemplazo (1) para que el estado no quede en 0.
        estado_lfsr = SEMILLA_DE_REEMPLAZO;
    }
}
```

`sembrar_aleatorio(semilla)`:
- Línea 17: `estado_lfsr = (uint16_t)(semilla & 0xFFFFU);` se queda solo con los **16 bits bajos** de la semilla (el tamaño del estado). `& 0xFFFF` borra los bits altos; `(uint16_t)` hace explícita la conversión.
- Líneas 19-22: si quedó en 0, se pone 1 (el 0 es el único estado prohibido).

**Líneas 25 a 38**

```c
// Devuelve el siguiente número pseudoaleatorio.
uint32_t siguiente_aleatorio(void)
{
    // Se hacen varios desplazamientos por llamada: con uno solo, cada número sería el anterior corrido un bit
    // y las posiciones de la manzana y del veneno quedarían muy parecidas entre sí.
    for (uint32_t i = 0U; i < DESPLAZAMIENTOS_POR_LLAMADA; i++) {
        // Bit nuevo: XOR de los bits 0, 2, 3 y 5 del estado (taps 16, 14, 13 y 11 del polinomio x^16 + x^14 + x^13 + x^11 + 1).
        uint16_t bit = ((estado_lfsr >> 0) ^ (estado_lfsr >> 2) ^ (estado_lfsr >> 3) ^ (estado_lfsr >> 5)) & 1U;
        // El estado se desplaza una posición a la derecha y el bit nuevo entra por la posición 15.
        estado_lfsr = (estado_lfsr >> 1) | (bit << 15);
    }
    // Se devuelve el estado ya desplazado como número aleatorio.
    return estado_lfsr;
}
```

`siguiente_aleatorio()`:
- Líneas 28-30: **16 pasos por llamada.** Con un solo paso, cada número sería el anterior corrido 1 bit; dos números seguidos se parecerían mucho y la manzana y el veneno caerían en posiciones muy parecidas. Con 16 pasos se renueva **todo el estado** en cada llamada.
- Línea 32: `bit = ((estado >> 0) ^ (estado >> 2) ^ (estado >> 3) ^ (estado >> 5)) & 1U;`
  - `estado >> n` lleva el bit `n` a la posición 0; `^` es XOR; `& 1U` se queda con el resultado de 1 bit.
  - Bits 0, 2, 3 y 5 = los *taps* del polinomio `x^16 + x^14 + x^13 + x^11 + 1`, un polinomio de periodo máximo para 16 bits (comentado en el código).
- Línea 34: `estado = (estado >> 1) | (bit << 15);` todo el estado se desplaza **1 a la derecha** (el bit 0 sale) y el bit nuevo **entra por la izquierda** (posición 15).
- Línea 37: `return estado_lfsr;` el estado ya desplazado es el número aleatorio (0 a 65 535).
- Para obtener una posición del tablero se usa el resto: por ejemplo `siguiente_aleatorio() % 32` da una columna de 0 a 31.

### 8. `main.c`: la prueba del orden serial

**Líneas 1 a 6**

```c
// Prueba del orden serial de los dos paneles encadenados: enciende un solo bit de la cadena de 128 para ver en qué píxel aparece.
#include "system_config.h"
// Se incluye el módulo del panel LED (framebuffer y refresco).
#include "panel.h"
// Se incluye el módulo de lectura de los botones.
#include "botones.h"
```

- Comentario de qué hace la prueba e `#include` del reloj, el panel y los botones.

**Líneas 8 a 18**

```c
// Función principal: crt0.S la llama cuando termina de preparar la RAM.
int main(void)
{
    // Primero el reloj, antes de usar cualquier periférico: deja el sistema a 84 MHz.
    configurar_reloj();
    // Se enciende la base de tiempo de 1 ms (SysTick), que usa esperar_milisegundos.
    iniciar_systick();
    // Se configuran los pines del panel como salidas. TIM3 no se inicia en esta prueba.
    configurar_panel();
    // Se configuran los seis botones como entradas con pull-up.
    configurar_botones();
```

`main`, preparación:
- `configurar_reloj()` y `iniciar_systick()`: 84 MHz y base de 1 ms (para `esperar_milisegundos` del antirrebote).
- `configurar_panel()`: pines del panel como salidas. **No se llama a `iniciar_refresco_panel()`: TIM3 queda apagado.**
- `configurar_botones()`: los 6 botones como entradas con pull-up.

**Líneas 20 a 25**

```c
    // Bit de la cadena que se enciende (0 a 127).
    uint32_t bit_encendido = 0U;
    // Fase que se muestra (0 a 3).
    uint32_t fase = 0U;
    // Botones presionados en la vuelta anterior, para detectar solo el flanco de pulsación.
    uint32_t botones_anteriores = 0U;
```

Tres variables locales:
- `bit_encendido` (0 a 127): qué bit de la cadena se enciende.
- `fase` (0 a 3): qué fase se muestra.
- `botones_anteriores`: los botones de la vuelta anterior, para detectar **el momento en que se presiona** (ver abajo).

**Líneas 27 a 34**

```c
    // Bucle infinito: un microcontrolador no termina, repite esto mientras tenga energía.
    while (1) {
        // Botones presionados en esta vuelta.
        uint32_t botones = leer_botones();
        // Flancos de pulsación: bits que están presionados ahora y no lo estaban antes. Así cada pulsación actúa una vez.
        uint32_t nuevos = botones & ~botones_anteriores;
        // Se guarda el estado actual para comparar en la siguiente vuelta.
        botones_anteriores = botones;
```

**Detección de flanco** (una acción por pulsación):
- `botones = leer_botones()`: botones presionados **ahora**.
- `nuevos = botones & ~botones_anteriores;`: bits que están en 1 **ahora y no estaban en 1 antes**. `~botones_anteriores` invierte todos los bits (1 donde el botón estaba suelto) y el `&` deja solo los que acaban de presionarse.
- `botones_anteriores = botones;`: se guarda el estado para la siguiente vuelta.
- **Por qué:** el bucle da miles de vueltas por segundo y un dedo tarda ~100 ms en soltar un botón. Sin esto, **una pulsación contaría miles de veces**; con esto, **una vez**.

**Líneas 36 a 55**

```c
        // A: el bit encendido avanza 1 y da la vuelta al llegar a 128.
        if ((nuevos & BOTON_A) != 0U) {
            // Suma 1; el % hace que después del bit 127 vuelva al 0.
            bit_encendido = (bit_encendido + 1U) % PANEL_BITS_POR_CADENA;
        }
        // B: el bit encendido retrocede 1; sumar PANEL_BITS_POR_CADENA evita un número negativo sin signo.
        if ((nuevos & BOTON_B) != 0U) {
            // Resta 1 sin pasar por un número negativo (que en uint32_t daría la vuelta a 4 294 967 295).
            bit_encendido = (bit_encendido + PANEL_BITS_POR_CADENA - 1U) % PANEL_BITS_POR_CADENA;
        }
        // E: el bit encendido avanza un bloque de PANEL_BITS_POR_BLOQUE (16) bits.
        if ((nuevos & BOTON_E) != 0U) {
            // Suma 16 con vuelta al llegar a 128.
            bit_encendido = (bit_encendido + PANEL_BITS_POR_BLOQUE) % PANEL_BITS_POR_CADENA;
        }
        // F: el bit encendido retrocede un bloque de PANEL_BITS_POR_BLOQUE (16) bits; sumar PANEL_BITS_POR_CADENA evita un número negativo sin signo.
        if ((nuevos & BOTON_F) != 0U) {
            // Resta 16 con vuelta, sin números negativos.
            bit_encendido = (bit_encendido + PANEL_BITS_POR_CADENA - PANEL_BITS_POR_BLOQUE) % PANEL_BITS_POR_CADENA;
        }
```

**Mover el bit encendido** (aritmética modular con 128 posiciones):
- **A**: `(bit_encendido + 1) % 128`: avanza 1; al llegar a 128 el resto da 0 (**da la vuelta**).
- **B**: `(bit_encendido + 128 - 1) % 128`: retrocede 1. **Se suma 128 antes de restar** porque `bit_encendido` es **sin signo**: `0 - 1` daría `0xFFFFFFFF`. Con `+128 - 1` el resultado nunca es negativo y el `%` lo devuelve a 0–127.
- **E**: `(bit_encendido + 16) % 128`: avanza un **bloque** de 16 bits (`PANEL_BITS_POR_BLOQUE`).
- **F**: `(bit_encendido + 128 - 16) % 128`: retrocede un bloque, con el mismo truco.
- Cada `if` usa `nuevos` (el flanco), no `botones`.

**Líneas 56 a 65**

```c
        // C: la fase avanza 1 y da la vuelta al llegar a 4.
        if ((nuevos & BOTON_C) != 0U) {
            // Suma 1; el % hace que después de la fase 3 vuelva a la 0.
            fase = (fase + 1U) % PANEL_FASES;
        }
        // D: la fase retrocede 1; sumar PANEL_FASES evita un número negativo sin signo.
        if ((nuevos & BOTON_D) != 0U) {
            // Resta 1 con vuelta, sin números negativos.
            fase = (fase + PANEL_FASES - 1U) % PANEL_FASES;
        }
```

**Cambiar la fase** (4 fases):
- **C**: `(fase + 1) % 4`; **D**: `(fase + 4 - 1) % 4` (mismo truco de sumar antes de restar).

**Líneas 67 a 71**

```c
        // Si hubo alguna pulsación nueva, se espera 30 ms para que el rebote del botón no cuente como otra pulsación.
        if (nuevos != 0U) {
            // Se espera 30 ms (más largo que el rebote del botón, que dura unos 4 ms).
            esperar_milisegundos(30U);
        }
```

**Antirrebote** (*debounce*): `if (nuevos != 0U) esperar_milisegundos(30U);`
- Al presionar un botón, el contacto mecánico **rebota**: durante unos milisegundos el pin pasa varias veces de 0 a 1. Eso se vería como varias pulsaciones.
- Si hubo una pulsación nueva, se espera **30 ms** para que el rebote termine antes de volver a leer. Mientras tanto no se lee ningún botón.

**Líneas 73 a 76**

```c
        // Se dibuja la fase con el bit encendido. Se llama en cada vuelta porque no hay refresco por interrupción.
        dibujar_fase_de_prueba(bit_encendido, fase);
    }
}
```

- `dibujar_fase_de_prueba(bit_encendido, fase);` se llama **en cada vuelta** porque no hay refresco por interrupción. Cada llamada desplaza los 128 bits y deja la fase encendida hasta la siguiente.
- Cierre del `while` y de `main`.

### 9. `inc/snake.h` y `src/snake.c`: el juego (no se usa en esta prueba)

Estos dos archivos son el **juego de la serpiente**. Están en la carpeta porque el `Makefile` compila todo lo que hay en `src/` (`$(wildcard src/*.c)`), pero **`main.c` de esta prueba no los llama**, así que no se ejecutan. Ocupan memoria (el arreglo `cuerpo` tiene `CAPACIDAD_CUERPO` = 32 × 16 = 512 posiciones de 2 bytes = 1 KB de RAM), pero no cambian lo que hace la prueba.

Lo que hace cada parte, a muy grandes rasgos:
- `Posicion`: estructura con `x` e `y` (1 byte cada uno).
- `cuerpo[]`, `cabeza`, `cola`, `longitud`: el cuerpo como **buffer circular**: la cabeza avanza, la cola se apaga; `% CAPACIDAD_CUERPO` hace la vuelta al principio del arreglo.
- `iniciar_juego`, `pedir_direccion`, `avanzar_serpiente`: la interfaz que usa el programa final.
- Manzana, veneno, puntaje y fin de partida: se usan `siguiente_aleatorio`, `obtener_milisegundos`, `dibujar_numero` y `celda_libre`.

Este código es de la parte del juego del proyecto (no de las pruebas); aquí solo se explica por qué está en la carpeta.

