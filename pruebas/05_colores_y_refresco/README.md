# Prueba 05: colores y refresco por interrupción (framebuffer + TIM3)

**Qué hace en la placa:** muestra cinco dibujos, cada uno **2 segundos**, en bucle: (1) 1 de cada 4 píxeles en rojo, (2) en verde, (3) en azul, (4) un marco rojo alrededor del panel y (5) dos diagonales verdes de esquina a esquina.

**Para qué sirve:** es el salto de "enviar una fase a mano" (prueba 04) a **tener una imagen en memoria que se refresca sola**. Ahora `main` solo escribe píxeles en un arreglo (el *framebuffer*) y una **interrupción de TIM3 cada 1 ms** se encarga de dibujar el panel. `main` ya **no toca los pines del panel**.

**Por qué los dibujos son "parciales" (1 de cada 4 píxeles):** se enciende solo 1 de cada 4 píxeles para limitar la corriente que pide el panel a la fuente de 3 A. (La corriente medida está en `docs/mediciones/alimentacion.md`.)

**Qué se agrega respecto a la prueba 04:**
- Un **framebuffer** en `panel.c` y la función `encender_pixel` para escribir en él.
- **TIM3** configurado para interrumpir cada 1 ms, y su manejador `TIM3_IRQHandler`.
- La función interna `dibujar_fase`, que reemplaza a `enviar_fase_con_un_bit`: lee el framebuffer y calcula, para cada bit, a qué píxel corresponde.
- Colores y tamaño del tablero en `panel.h`; registros de TIM3 y del NVIC en `registros_f446.h`.

**Qué NO cambia:** `Makefile`, `linker_script.ld`, `crt0.S`, `system_config` y `gpio_config` (ver los README de las pruebas 01 a 04).

### Cómo se reparte el trabajo

```
main (bucle)                     TIM3 (cada 1 ms, interrupción)
  encender_pixel(x,y,color)  ─▶   framebuffer  ◀─ dibujar_fase(fase_actual)
  esperar_milisegundos(2000)                       fase_actual = (fase_actual+1) % 4
```

Cada fase (0, 1, 2, 3) se dibuja una vez cada 4 ms, o sea **250 veces por segundo**. Como el ojo no percibe parpadeo a esa frecuencia, la imagen se ve estable.

### 1. `inc/registros_f446.h`: lo que se agrega

Solo se explican las líneas nuevas; el resto es igual a la prueba 03.

**Líneas 14 a 15**

```c
// Bus APB1: aquí está TIM3. Fuente: RM0390, sección 2.2.2, tabla 1 (el APB1 empieza en 0x40000000).
#define APB1_BASE (PERIFERICOS_BASE)
```

- `APB1_BASE = PERIFERICOS_BASE` (`0x40000000`): el bus APB1 empieza al comienzo de la zona de periféricos. Ahí está TIM3.

**Líneas 28 a 29**

```c
// Timer de propósito general TIM3 (0x40000400). Fuente: RM0390, sección 2.2.2, tabla 1 (APB1_BASE + 0x400).
#define TIM3_BASE (APB1_BASE + 0x400U)
```

- `TIM3_BASE = APB1_BASE + 0x400` → `0x40000400`: dirección del timer TIM3.

**Líneas 32 a 33**

```c
// Registros del NVIC (controlador de interrupciones) del núcleo Cortex-M4 (0xE000E100). Fuente: PM0214, sección NVIC (por verificar por Daniela); coincide con core_cm4.h de CMSIS de ARM.
#define NVIC_BASE (0xE000E100U)
```

- `NVIC_BASE = 0xE000E100`: el NVIC (controlador de interrupciones) es del **núcleo ARM**, como SysTick, con dirección fija.

**Líneas 94 a 95**

```c
    // Desplazamiento 0x40. Habilita el reloj de los periféricos del bus APB1; se usa para TIM3 (bit 1).
    volatile uint32_t APB1ENR;
```

- `APB1ENR` (0x40) se agrega al final de `RegistrosRCC`: habilita el reloj de los periféricos del bus APB1. Se usa para TIM3 (bit 1). Para que caiga en 0x40 se declararon también `AHB2ENR`, `AHB3ENR` y `RESERVADO_2` (líneas 88-93).

**Líneas 119 a 147**

```c
// Mapa de los registros de TIM3, en el orden del manual hasta ARR. Cada campo está en su desplazamiento.
// Fuente: RM0390, capítulo de los timers de propósito general TIM2 a TIM5, mapa de registros (número de capítulo y sección por verificar por Daniela).
typedef struct {
    // Desplazamiento 0x00. Control 1: bit 0 CEN enciende el contador. Se usa para encender TIM3.
    volatile uint32_t CR1;
    // Desplazamiento 0x04. Control 2. No se usa.
    volatile uint32_t CR2;
    // Desplazamiento 0x08. Control del modo esclavo. No se usa.
    volatile uint32_t SMCR;
    // Desplazamiento 0x0C. Habilitación de interrupciones y DMA: bit 0 UIE habilita la interrupción de actualización. Se usa.
    volatile uint32_t DIER;
    // Desplazamiento 0x10. Estado: bit 0 UIF indica que hubo una actualización (se limpia escribiendo 0). Se usa.
    volatile uint32_t SR;
    // Desplazamiento 0x14. Generación de eventos: bit 0 UG carga PSC y ARR de inmediato. Se usa.
    volatile uint32_t EGR;
    // Desplazamiento 0x18. Modo de captura/comparación 1. No se usa.
    volatile uint32_t CCMR1;
    // Desplazamiento 0x1C. Modo de captura/comparación 2. No se usa.
    volatile uint32_t CCMR2;
    // Desplazamiento 0x20. Habilitación de captura/comparación. No se usa.
    volatile uint32_t CCER;
    // Desplazamiento 0x24. Valor actual del contador. No se usa.
    volatile uint32_t CNT;
    // Desplazamiento 0x28. Divisor del reloj del timer: el contador avanza cada PSC + 1 ciclos. Se usa.
    volatile uint32_t PSC;
    // Desplazamiento 0x2C. Valor de recarga: el contador va de 0 a ARR. Se usa.
    volatile uint32_t ARR;
// Fin de la estructura: desde aquí se puede usar el tipo RegistrosTIM3.
} RegistrosTIM3;
```

`RegistrosTIM3`: los registros de TIM3 en el orden del manual, **hasta `ARR`** (los posteriores no se usan). Los que se usan:
- `CR1` (0x00): bit 0 `CEN` enciende el contador.
- `DIER` (0x0C): bit 0 `UIE` habilita la interrupción de actualización (cuando el contador desborda).
- `SR` (0x10): bit 0 `UIF` indica que hubo una actualización.
- `EGR` (0x14): bit 0 `UG` genera una actualización a la fuerza (carga `PSC` y `ARR` en el acto).
- `PSC` (0x28): **divisor** del reloj del timer: el contador avanza cada `PSC + 1` ciclos.
- `ARR` (0x2C): **valor de recarga**: el contador cuenta de 0 a `ARR` y se reinicia.
- Los demás (`CR2`, `SMCR`, `CCMR1/2`, `CCER`, `CNT`) están solo para mantener los desplazamientos.

**Líneas 149 a 154**

```c
// Mapa de los registros del NVIC. Fuente: PM0214, sección NVIC (por verificar por Daniela).
typedef struct {
    // Desplazamiento 0x00. Habilita las interrupciones 0 a 31: escribir 1 en el bit n habilita la interrupción n; escribir 0 no hace nada.
    volatile uint32_t ISER0;
// Fin de la estructura: desde aquí se puede usar el tipo RegistrosNVIC.
} RegistrosNVIC;
```

- `RegistrosNVIC` solo declara `ISER0` (desplazamiento 0): habilita las interrupciones 0 a 31. **Escribir 1** en el bit *n* habilita la interrupción *n*; escribir 0 no cambia nada (por eso no hay que leer antes).

**Líneas 169 a 172**

```c
// Puntero a los registros de TIM3 (se usa para TIM3->PSC, ARR, CR1, DIER, SR y EGR).
#define TIM3 ((RegistrosTIM3 *)TIM3_BASE)
// Puntero a los registros del NVIC (se usa para NVIC->ISER0).
#define NVIC ((RegistrosNVIC *)NVIC_BASE)
```

- Punteros `TIM3` y `NVIC` a esos bloques de registros.

**Líneas 232 a 243**

```c
// Bit 1 de RCC_APB1ENR: 1 enciende el reloj de TIM3. Fuente: RM0390, capítulo 6 (RCC), registro RCC_APB1ENR (sección por verificar por Daniela).
#define RCC_APB1ENR_TIM3EN (1U << 1)
// Bit 0 de TIM3 CR1 (CEN): 1 enciende el contador del timer. Fuente: RM0390, capítulo de TIM2 a TIM5, registro TIM_CR1 (sección por verificar por Daniela).
#define TIM_CR1_CEN (1U << 0)
// Bit 0 de TIM3 DIER (UIE): 1 habilita la interrupción de actualización. Fuente: RM0390, capítulo de TIM2 a TIM5, registro TIM_DIER (sección por verificar por Daniela).
#define TIM_DIER_UIE (1U << 0)
// Bit 0 de TIM3 SR (UIF): 1 indica que hubo una actualización. Es rc_w0: se limpia escribiendo 0 en este bit; escribir 1 no cambia nada. Fuente: RM0390, capítulo de TIM2 a TIM5, registro TIM_SR (sección por verificar por Daniela).
#define TIM_SR_UIF (1U << 0)
// Bit 0 de TIM3 EGR (UG): al escribir 1 se genera una actualización que carga PSC y ARR. Fuente: RM0390, capítulo de TIM2 a TIM5, registro TIM_EGR (sección por verificar por Daniela).
#define TIM_EGR_UG (1U << 0)
// Número de la interrupción de TIM3 (IRQ 29), que es la posición 16 + 29 = 45 de la tabla de vectores. Fuente: RM0390, sección 10.1.3, tabla 38.
#define NUMERO_INTERRUPCION_TIM3 29U
```

Bits y números nuevos:
- `RCC_APB1ENR_TIM3EN (1U << 1)`: enciende el reloj de TIM3.
- `TIM_CR1_CEN (1U << 0)`: enciende el contador.
- `TIM_DIER_UIE (1U << 0)`: habilita la interrupción de actualización.
- `TIM_SR_UIF (1U << 0)`: bandera de actualización. Es del tipo **rc_w0**: se **borra escribiendo 0** en ese bit; escribir 1 no cambia nada.
- `TIM_EGR_UG (1U << 0)`: al escribir 1 se genera una actualización que carga `PSC` y `ARR`.
- `NUMERO_INTERRUPCION_TIM3 29U`: TIM3 es la **IRQ 29** (posición 16 + 29 = 45 de la tabla de vectores).

### 2. `inc/panel.h`: lo que se agrega

**Líneas 34 a 39**

```c
// Ancho del tablero en píxeles (columnas x). Etapa 1: un solo panel de 32 columnas. En la etapa 2 cambia aquí.
#define PANEL_ANCHO 32U
// Alto del tablero en píxeles (filas y). Etapa 1: un solo panel de 16 filas. En la etapa 2 cambia aquí.
#define PANEL_ALTO 16U
// Número de fases del escaneo 1/4: cada fase enciende 4 filas (0, 1, 2, 3). Fuente: docs/mapeo_pixeles.md.
#define PANEL_FASES 4U
```

- `PANEL_ANCHO 32U` y `PANEL_ALTO 16U`: tamaño del tablero en esta etapa: **un solo panel** de 32 columnas por 16 filas. Los comentarios dicen que en la etapa 2 (dos paneles) estos valores cambian aquí (así ocurre en la prueba 09: `PANEL_ALTO` pasa a 32).
- `PANEL_FASES 4U`: el escaneo 1/4 tiene **4 fases**.

**Líneas 40 a 49**

```c
// Bits que se desplazan en cada bloque de 16 bits. Fuente: docs/mapeo_pixeles.md (bloque = bit / 16).
#define PANEL_BITS_POR_BLOQUE 16U
// Columnas que ocupa cada mitad de un bloque (8 para la mitad j < 8 y 8 para la mitad j >= 8). Fuente: docs/mapeo_pixeles.md.
#define PANEL_COLUMNAS_POR_BLOQUE 8U
// Separación en filas entre la mitad j < 8 y la mitad j >= 8 de un bloque: y = fase + 4. Fuente: docs/mapeo_pixeles.md.
#define PANEL_SEPARACION_FILAS 4U
// Filas que hay entre la mitad de arriba y la de abajo del panel: R2, G2 y B2 suman 8 a y. Fuente: docs/mapeo_pixeles.md.
#define PANEL_FILAS_MITAD_SUPERIOR 8U
// Posición del bit de los colores de abajo (R2, G2, B2) dentro de datos: R2 es el bit 3. Fuente: desplazar_bit en src/panel.c.
#define PANEL_DESPLAZAMIENTO_MITAD_INFERIOR 3U
```

Constantes de la **fórmula de mapeo** (de `docs/mapeo_pixeles.md`) que usa `dibujar_fase`:
- `PANEL_BITS_POR_BLOQUE 16U`: los 64 bits de una fase se agrupan en 4 bloques de 16.
- `PANEL_COLUMNAS_POR_BLOQUE 8U`: cada bloque cubre 8 columnas (cada mitad de 8 bits va a 8 columnas).
- `PANEL_SEPARACION_FILAS 4U`: la segunda mitad de un bloque está 4 filas más abajo (`y = fase + 4`).
- `PANEL_FILAS_MITAD_SUPERIOR 8U`: los colores R2, G2, B2 corresponden a la fila `y + 8` (la mitad de abajo del panel, 16 filas / 2).
- `PANEL_DESPLAZAMIENTO_MITAD_INFERIOR 3U`: en la variable `datos`, el color de abajo (R2) empieza en el **bit 3**.

**Líneas 51 a 58**

```c
// Color negro: los tres bits de color en 0 (el pixel está apagado).
#define COLOR_NEGRO 0U
// Color rojo: solo el bit R (bit 0) en 1.
#define COLOR_ROJO 1U
// Color verde: solo el bit G (bit 1) en 1.
#define COLOR_VERDE 2U
// Color azul: solo el bit B (bit 2) en 1.
#define COLOR_AZUL 4U
```

Colores. Cada color es un número de 3 bits **R = bit 0, G = bit 1, B = bit 2**:
- `COLOR_NEGRO 0` (apagado), `COLOR_ROJO 1` (`001`), `COLOR_VERDE 2` (`010`), `COLOR_AZUL 4` (`100`).
- Como cada canal es de 1 bit (encendido o apagado), el panel solo hace 8 colores; los demás (amarillo, magenta, cian, blanco) se agregan en la prueba 06 como combinaciones.

**Líneas 68 a 71**

```c
// Enciende TIM3 para que interrumpa cada 1 ms y el panel se refresque solo.
void iniciar_refresco_panel(void);
// Guarda el color (COLOR_NEGRO, COLOR_ROJO, COLOR_VERDE o COLOR_AZUL) del píxel (x, y) en el framebuffer.
void encender_pixel(uint32_t x, uint32_t y, uint32_t color);
```

Prototipos nuevos:
- `iniciar_refresco_panel()`: enciende TIM3 para refrescar el panel solo.
- `encender_pixel(x, y, color)`: guarda el color del píxel (x, y) en el framebuffer.
- (`enviar_fase_con_un_bit` desaparece del `.h`: ya no es necesaria; `dibujar_fase` es privada y solo la llama la interrupción.)

### 3. `src/panel.c`: framebuffer, mapeo y TIM3

El resto de `panel.c` (`configurar_salida_del_panel`, `desplazar_bit` y `configurar_panel`) es igual al de la prueba 04 (ver su README). `enviar_fase_con_un_bit` desaparece y su lugar lo toma `dibujar_fase`.

**Líneas 4 a 7**

```c
// Divisor de TIM3: 84 MHz / (83 + 1) = 1 MHz, es decir, el contador avanza una cuenta cada 1 µs.
#define TIM3_PRESCALER 83U
// Valor de recarga de TIM3: 1 MHz / (999 + 1) = 1 kHz, es decir, una interrupción cada 1 ms.
#define TIM3_AUTORRECARGA 999U
```

- `TIM3_PRESCALER 83U`: TIM3 recibe **84 MHz**. Con `PSC = 83` el contador avanza cada 83 + 1 = 84 ciclos: 84 MHz / 84 = **1 MHz**, o sea una cuenta por microsegundo.
- `TIM3_AUTORRECARGA 999U`: el contador cuenta de 0 a 999 (1000 cuentas) → 1000 µs = **1 ms**. Al desbordar, genera la interrupción.
- (¿Por qué TIM3 recibe 84 MHz si el APB1 está a 42 MHz? Porque cuando el divisor del bus APB1 no es 1, el reloj de sus timers es el **doble**, ver prueba 02.)

**Líneas 9 a 12**

```c
// Imagen del tablero: un color por píxel, indexado [y][x]. Los bits 0 a 2 son R, G y B.
// volatile porque la interrupción de TIM3 lee este arreglo mientras main lo escribe.
// Está en .bss, así que empieza en 0 (COLOR_NEGRO).
static volatile uint8_t framebuffer[PANEL_ALTO][PANEL_ANCHO];
```

- `static volatile uint8_t framebuffer[PANEL_ALTO][PANEL_ANCHO];` es la **imagen del tablero**: un byte por píxel, indexado `[fila y][columna x]`. Solo se usan los 3 bits bajos (R, G, B).
  - `volatile`: `main` lo escribe y la interrupción de TIM3 lo lee; el compilador no debe asumir que no cambia.
  - `static`: privado de este archivo.
  - Está en `.bss`, así que empieza en **0** (negro) sin escribir nada; ocupa 16 × 32 = 512 bytes de RAM.

**Líneas 13 a 14**

```c
// Fase que se dibuja en la siguiente interrupción de TIM3. Solo la usa la interrupción, por eso no necesita volatile.
static uint32_t fase_actual = 0U;
```

- `static uint32_t fase_actual = 0U;` es la fase que se dibujará en la **próxima** interrupción. Solo la usa la interrupción, por eso no necesita `volatile`.

**Líneas 91 a 138**

```c
// Dibuja una fase completa con los colores del framebuffer. Fórmula de docs/mapeo_pixeles.md:
//   bloque = bit / 16, j = bit % 16
//   si j < 8:  x = 8 * bloque + (7 - j), y = fase        (de derecha a izquierda)
//   si j >= 8: x = 8 * bloque + (j - 8), y = fase + 4    (de izquierda a derecha)
// R2, G2 y B2 usan la fila y + 8.
static void dibujar_fase(uint32_t fase)
{
    // Se desplazan los 64 bits de la fase, uno por uno, con CLK.
    for (uint32_t bit = 0U; bit < PANEL_BITS_POR_FASE; bit++) {
        // Bloque de 16 bits al que pertenece el bit (0 a 3).
        uint32_t bloque = bit / PANEL_BITS_POR_BLOQUE;
        // Posición del bit dentro de su bloque (0 a 15).
        uint32_t j = bit % PANEL_BITS_POR_BLOQUE;
        // Columna del píxel de la mitad de arriba que corresponde a este bit.
        uint32_t x;
        // Fila del píxel de la mitad de arriba que corresponde a este bit.
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
        // datos: bits 0 a 2 = R1, G1, B1 (fila y); bits 3 a 5 = R2, G2, B2 (fila y + 8), desplazados 3 posiciones.
        uint32_t datos = framebuffer[y][x] | (framebuffer[y + PANEL_FILAS_MITAD_SUPERIOR][x] << PANEL_DESPLAZAMIENTO_MITAD_INFERIOR);
        // Se desplazan los 6 bits de color de este píxel.
        desplazar_bit(datos);
    }
    // OE apagado mientras cambian LAT y la fase: así no se ve basura durante el cambio.
    escribir_pin(GPIOC, PIN_PANEL_OE, NIVEL_OE_APAGADO);
    // LAT en 1: el latch pasa los 64 bits desplazados a la salida. Va después de desplazar todos los bits.
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

`dibujar_fase(fase)` (es `static`) recorre los 64 bits de una fase y, para cada uno, busca en el framebuffer el color del píxel que le toca:
- Línea 99: `for (bit = 0; bit < PANEL_BITS_POR_FASE; bit++)`: los 64 bits que hay que desplazar.
- Líneas 101-103: `bloque = bit / 16` (a qué bloque de 16 bits pertenece, 0 a 3) y `j = bit % 16` (posición dentro del bloque, 0 a 15). `/` y `%` son división y resto enteros.
- Líneas 105-120: se calculan `x` e `y` del píxel de la mitad de arriba:
  - Si `j < 8`: `x = 8 * bloque + (7 - j)` (las columnas van de **derecha a izquierda** dentro del bloque) y `y = fase`.
  - Si `j >= 8`: `x = 8 * bloque + (j - 8)` (de **izquierda a derecha**) y `y = fase + 4`.
  - Esta es la fórmula **medida** en la placa (`docs/mapeo_pixeles.md`): el orden en que el panel recibe los bits no sigue el orden de las columnas.
  - Ejemplo (fase 0): bit 0 → bloque 0, j = 0 → x = 7, y = 0. Bit 7 → x = 0, y = 0. Bit 8 → x = 0, y = 4. Bit 15 → x = 7, y = 4. Bit 16 → bloque 1, j = 0 → x = 15, y = 0.
- Línea 122: `datos = framebuffer[y][x] | (framebuffer[y + 8][x] << 3);` arma los 6 bits: el color del píxel de arriba va en los bits 0 a 2 (R1, G1, B1) y el de abajo (fila `y + 8`) se **corre 3 posiciones** para quedar en los bits 3 a 5 (R2, G2, B2). Funciona porque cada color son 3 bits con R = 1, G = 2, B = 4.
- Línea 124: `desplazar_bit(datos)`: mete los 6 bits y da un pulso de CLK.
- Líneas 126-137: igual que `enviar_fase_con_un_bit` de la prueba 04: OE apagado, pulso de LAT, se escriben A y B según la fase y OE encendido.

**Líneas 140 a 149**

```c
// Guarda el color de un píxel en el framebuffer. Si x o y están fuera del tablero, no hace nada:
// escribir fuera del arreglo dañaría otra zona de la memoria.
void encender_pixel(uint32_t x, uint32_t y, uint32_t color)
{
    // Solo se escribe si x está dentro de las columnas y y dentro de las filas del tablero.
    if (x < PANEL_ANCHO && y < PANEL_ALTO) {
        // Se guarda el color en 3 bits (R = bit 0, G = bit 1, B = bit 2). Cabe en uint8_t sin perder datos.
        framebuffer[y][x] = (uint8_t)color;
    }
}
```

`encender_pixel(x, y, color)` guarda un color en el framebuffer:
- `if (x < PANEL_ANCHO && y < PANEL_ALTO)`: solo escribe si la posición está dentro del tablero. **Por qué:** escribir fuera del arreglo dañaría otra variable de la RAM, sin ningún aviso. Con esta comprobación, un dibujo que se salga del tablero simplemente se recorta.
- `framebuffer[y][x] = (uint8_t)color;`: el color cabe en 3 bits, así que el `uint8_t` no pierde datos.
- Solo se cambia la memoria: **no se toca ningún pin del panel**; eso lo hace la interrupción.

**Líneas 151 a 178**

```c
// Enciende TIM3 para que interrumpa cada 1 ms. Cada interrupción dibuja una fase del panel.
void iniciar_refresco_panel(void)
{
    // (a) Se enciende el reloj de TIM3 en el bus APB1. |= no cambia los demás bits de RCC->APB1ENR.
    RCC->APB1ENR |= RCC_APB1ENR_TIM3EN;
    // Variable que solo sirve para leer el registro; el valor leído no se usa.
    volatile uint32_t lectura_descartada;
    // Dos lecturas después de habilitar el reloj, como en habilitar_reloj_puerto: el periférico necesita unos ciclos antes de usarse.
    lectura_descartada = RCC->APB1ENR;
    // Lectura de espera: da unos ciclos para que el reloj de TIM3 se estabilice antes de usarlo.
    lectura_descartada = RCC->APB1ENR;
    // El valor leído no se usa: (void) le dice al compilador que se descarta a propósito (evita la advertencia).
    (void)lectura_descartada;
    // (b) Divisor y valor de recarga: el contador cuenta de 0 a 999 con un reloj de 1 MHz, es decir, 1 ms.
    TIM3->PSC = TIM3_PRESCALER;
    // Valor de recarga ARR: el contador cuenta de 0 a ARR y entonces genera la interrupción.
    TIM3->ARR = TIM3_AUTORRECARGA;
    // (c) UG carga PSC y ARR en el momento; sin esto, el divisor nuevo esperaría a la primera actualización.
    TIM3->EGR = TIM_EGR_UG;
    // (d) Se limpia el UIF que dejó UG: se escribe 0 en ese bit y 1 en los demás (rc_w0 no cambia con 1).
    TIM3->SR = ~TIM_SR_UIF;
    // (e) Se habilita la interrupción de actualización de TIM3 (UIE).
    TIM3->DIER |= TIM_DIER_UIE;
    // (f) Se habilita la IRQ 29 en el NVIC. Escribir 0 en los demás bits no cambia nada, por eso no hace falta leer ISER0.
    NVIC->ISER0 = (1U << NUMERO_INTERRUPCION_TIM3);
    // (g) Se enciende el contador de TIM3 (CEN). A partir de aquí llegan interrupciones cada 1 ms.
    TIM3->CR1 |= TIM_CR1_CEN;
}
```

`iniciar_refresco_panel()` configura TIM3 para que interrumpa cada 1 ms. **El orden de los 7 pasos importa**:
- **(a) Líneas 154-163:** `RCC->APB1ENR |= RCC_APB1ENR_TIM3EN;` enciende el reloj de TIM3 (sin esto, sus registros no responden). Se repiten las dos lecturas descartadas de la misma forma que en `habilitar_reloj_puerto`.
- **(b) Líneas 164-167:** `TIM3->PSC = 83;` y `TIM3->ARR = 999;` → 1 MHz y cuenta hasta 999 → **1 ms**.
- **(c) Líneas 168-169:** `TIM3->EGR = TIM_EGR_UG;` fuerza una actualización. Los registros `PSC` y `ARR` tienen una copia "sombra" que solo se actualiza al desbordar el contador; con `UG` se cargan **de inmediato** y no hay que esperar la primera vuelta.
- **(d) Líneas 170-171:** `TIM3->SR = ~TIM_SR_UIF;` el `UG` anterior dejó `UIF` en 1; si no se borrara, la interrupción dispararía en cuanto se habilite. `~TIM_SR_UIF` escribe **0 en el bit `UIF`** (lo borra) y 1 en los demás (como son *rc_w0*, escribir 1 no los cambia).
- **(e) Líneas 172-173:** `TIM3->DIER |= TIM_DIER_UIE;` el timer **avisará** cuando desborde.
- **(f) Líneas 174-175:** `NVIC->ISER0 = (1U << 29);` habilita la IRQ 29 en el NVIC (el controlador de interrupciones). Hay dos "permisos": el del periférico (`UIE`) y el del NVIC; ambos hacen falta. Escribir 0 en los demás bits no cambia nada, así que se escribe `=` directo.
- **(g) Líneas 176-177:** `TIM3->CR1 |= TIM_CR1_CEN;` **enciende el contador al final**, cuando todo está listo. Desde aquí hay una interrupción cada 1 ms.

**Líneas 180 a 190**

```c
// Manejador de la interrupción de TIM3. El nombre es el de la tabla de vectores de crt0.S, así que reemplaza al alias débil.
// Se ejecuta cada 1 ms y dibuja una fase (0, 1, 2, 3, 0...): cada fase se repite 250 veces por segundo.
void TIM3_IRQHandler(void)
{
    // Se limpia la causa de la interrupción (UIF) escribiendo 0 en ese bit; si no, la interrupción se repetiría sin fin.
    TIM3->SR = ~TIM_SR_UIF;
    // Se dibuja la fase actual con los colores que hay en el framebuffer.
    dibujar_fase(fase_actual);
    // Se pasa a la siguiente fase. % PANEL_FASES hace que después de la fase 3 vuelva a la 0.
    fase_actual = (fase_actual + 1U) % PANEL_FASES;
}
```

`TIM3_IRQHandler` es el manejador de la interrupción:
- Su nombre es el de la tabla de vectores de `crt0.S` (IRQ 29): reemplaza al alias débil.
- Línea 185: `TIM3->SR = ~TIM_SR_UIF;` **borra la causa** de la interrupción. Si no se borra `UIF`, el timer seguiría "pidiendo atención" y la interrupción se repetiría sin parar.
- Línea 187: `dibujar_fase(fase_actual);` dibuja una fase con lo que haya en el framebuffer.
- Línea 189: `fase_actual = (fase_actual + 1U) % PANEL_FASES;` pasa a la siguiente fase; el `% 4` hace que después de la 3 vuelva a la 0 (0, 1, 2, 3, 0, 1, ...).
- La interrupción corre cada 1 ms **sin que `main` haga nada**, aunque `main` esté en una espera.

### 4. `main.c`: el programa

**Líneas 1 a 4**

```c
// Se incluye la configuración del reloj y del temporizador SysTick.
#include "system_config.h"
// Se incluye el módulo del panel LED (framebuffer y refresco).
#include "panel.h"
```

- Incluye el módulo de reloj y el del panel.

**Líneas 6 a 17**

```c
// Pone en negro todos los píxeles del tablero.
static void limpiar_pantalla(void)
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

`limpiar_pantalla()` pone todo el tablero en negro:
- Dos `for` anidados: el de afuera recorre las filas `y` (0 a 15) y el de adentro las columnas `x` (0 a 31). Para cada píxel llama a `encender_pixel(x, y, COLOR_NEGRO)`.
- Es `static` porque solo se usa en este archivo. (En la prueba 06 esta función pasa al módulo `graficos` con el nombre `borrar_pantalla`.)

**Líneas 19 a 33**

```c
// Pinta 1 de cada 4 píxeles (x e y pares) con el color dado. Es parcial para limitar la corriente de la fuente de 3 A.
static void rellenar_parcial(uint32_t color)
{
    // Recorre todas las filas del tablero.
    for (uint32_t y = 0U; y < PANEL_ALTO; y++) {
        // Recorre todas las columnas de la fila.
        for (uint32_t x = 0U; x < PANEL_ANCHO; x++) {
            // Solo se pintan los píxeles con x par e y par: queda 1 de cada 4 encendido.
            if ((x % 2U) == 0U && (y % 2U) == 0U) {
                // Pone el píxel (x, y) en el color pedido.
                encender_pixel(x, y, color);
            }
        }
    }
}
```

`rellenar_parcial(color)` pinta **1 de cada 4 píxeles**:
- Recorre todo el tablero igual que arriba, pero `if ((x % 2U) == 0U && (y % 2U) == 0U)` solo pinta si **x es par y y es par**. `%` es el resto: `x % 2 == 0` significa "x par". De cada 4 píxeles (2 × 2), solo 1 cumple ambas condiciones.
- Se hace para limitar la corriente de la fuente de 3 A.

**Líneas 35 a 52**

```c
// Dibuja un marco completo alrededor del tablero: la fila de arriba, la de abajo, la columna izquierda y la derecha.
static void dibujar_marco(uint32_t color)
{
    // Recorre las columnas para pintar la fila de arriba (y = 0) y la de abajo (y = PANEL_ALTO - 1).
    for (uint32_t x = 0U; x < PANEL_ANCHO; x++) {
        // Fila de arriba.
        encender_pixel(x, 0U, color);
        // Fila de abajo.
        encender_pixel(x, PANEL_ALTO - 1U, color);
    }
    // Recorre las filas para pintar la columna de la izquierda (x = 0) y la de la derecha (x = PANEL_ANCHO - 1).
    for (uint32_t y = 0U; y < PANEL_ALTO; y++) {
        // Columna de la izquierda.
        encender_pixel(0U, y, color);
        // Columna de la derecha.
        encender_pixel(PANEL_ANCHO - 1U, y, color);
    }
}
```

`dibujar_marco(color)` dibuja el contorno del tablero con dos `for`:
- Primer `for` (columnas): para cada `x`, pinta la **fila de arriba** `(x, 0)` y la **de abajo** `(x, PANEL_ALTO - 1)`.
- Segundo `for` (filas): para cada `y`, pinta la **columna izquierda** `(0, y)` y la **derecha** `(PANEL_ANCHO - 1, y)`.
- `PANEL_ALTO - 1` y `PANEL_ANCHO - 1` son el último índice (los índices van de 0 a tamaño − 1).

**Líneas 54 a 68**

```c
// Dibuja dos diagonales de esquina a esquina con el color dado.
static void dibujar_diagonales(uint32_t color)
{
    // Recorre las filas: en cada una se pintan dos píxeles, uno de cada diagonal.
    for (uint32_t y = 0U; y < PANEL_ALTO; y++) {
        // x1 crece de 0 a PANEL_ANCHO - 1 a medida que y crece de 0 a PANEL_ALTO - 1: es la diagonal de arriba a la izquierda hacia abajo a la derecha.
        uint32_t x1 = (y * (PANEL_ANCHO - 1U)) / (PANEL_ALTO - 1U);
        // x2 es el espejo de x1: es la diagonal de arriba a la derecha hacia abajo a la izquierda.
        uint32_t x2 = (PANEL_ANCHO - 1U) - x1;
        // Pone el píxel de la primera diagonal en la fila y.
        encender_pixel(x1, y, color);
        // Pone el píxel de la segunda diagonal en la fila y.
        encender_pixel(x2, y, color);
    }
}
```

`dibujar_diagonales(color)` dibuja las dos diagonales:
- Para cada fila `y` calcula `x1 = (y * (PANEL_ANCHO - 1)) / (PANEL_ALTO - 1)`. Mientras `y` va de 0 a 15, `x1` va de 0 a 31 (31 columnas repartidas en 15 saltos; la división entera redondea hacia abajo, lo que da una línea escalonada).
- `x2 = (PANEL_ANCHO - 1) - x1` es el **espejo** de `x1`: la otra diagonal.
- Se pintan `(x1, y)` y `(x2, y)` en cada fila.

**Líneas 70 a 82**

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

```

`main`:
- `configurar_reloj()` (84 MHz) primero; `iniciar_systick()` para que funcione `esperar_milisegundos`.
- `configurar_panel()`: pines del panel como salidas.
- `iniciar_refresco_panel()`: **enciende TIM3**. Desde aquí, una interrupción cada 1 ms dibuja el framebuffer en el panel. Si se llamara antes de `configurar_panel()`, la interrupción escribiría pines que todavía no son salidas.

**Líneas 83 a 120**

```c
    // Bucle infinito: un microcontrolador no termina, repite esto mientras tenga energía.
    while (1) {
        // Dibujo 1: se debe ver 1 de cada 4 píxeles en rojo durante 2 s.
        limpiar_pantalla();
        // Se pinta 1 de cada 4 píxeles en rojo.
        rellenar_parcial(COLOR_ROJO);
        // Se espera 2 s con ese dibujo en el panel.
        esperar_milisegundos(2000U);

        // Dibujo 2: se debe ver 1 de cada 4 píxeles en verde durante 2 s.
        limpiar_pantalla();
        // Se pinta 1 de cada 4 píxeles en verde.
        rellenar_parcial(COLOR_VERDE);
        // Se espera 2 s con ese dibujo en el panel.
        esperar_milisegundos(2000U);

        // Dibujo 3: se debe ver 1 de cada 4 píxeles en azul durante 2 s.
        limpiar_pantalla();
        // Se pinta 1 de cada 4 píxeles en azul.
        rellenar_parcial(COLOR_AZUL);
        // Se espera 2 s con ese dibujo en el panel.
        esperar_milisegundos(2000U);

        // Dibujo 4: se debe ver un marco rojo completo alrededor del panel durante 2 s.
        limpiar_pantalla();
        // Se dibuja el marco rojo alrededor del panel.
        dibujar_marco(COLOR_ROJO);
        // Se espera 2 s con ese dibujo en el panel.
        esperar_milisegundos(2000U);

        // Dibujo 5: se deben ver dos diagonales verdes de esquina a esquina durante 2 s.
        limpiar_pantalla();
        // Se dibujan las dos diagonales verdes.
        dibujar_diagonales(COLOR_VERDE);
        // Se espera 2 s con ese dibujo en el panel.
        esperar_milisegundos(2000U);
    }
}
```

Bucle principal: los 5 dibujos, cada uno **limpia** (`limpiar_pantalla()`), **dibuja** y **espera 2000 ms**:
1. `rellenar_parcial(COLOR_ROJO)`.
2. `rellenar_parcial(COLOR_VERDE)`.
3. `rellenar_parcial(COLOR_AZUL)`.
4. `dibujar_marco(COLOR_ROJO)`.
5. `dibujar_diagonales(COLOR_VERDE)`.
- Mientras `main` espera, **la interrupción sigue refrescando el panel**: la imagen no parpadea ni se detiene. Esa es la ventaja de separar "dibujar en memoria" de "refrescar el panel".
- Los comentarios de `main` dicen qué se debe ver en cada paso: sirven como lista de comprobación al probar la placa.

