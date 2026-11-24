# Pruebas

Programas de prueba que se grabaron en la placa durante el desarrollo, uno por carpeta. Cada carpeta es un proyecto completo y compila sola. **Cada archivo de código tiene comentarios línea por línea** (qué hace y por qué), y el `README.md` de cada carpeta explica lo mismo con más detalle, citando el código con sus números de línea.

```bash
cd 01_led_con_boton
make          # compila
make flash    # graba la placa
```

| Carpeta | Qué hace | Paneles |
|---|---|---|
| [`01_led_con_boton`](01_led_con_boton/README.md) | El LED de la placa (PA5) se enciende mientras se presiona el botón azul (PC13) | ninguno |
| [`02_led_parpadeo`](02_led_parpadeo/README.md) | Reloj a 84 MHz y SysTick: el LED parpadea a 1 Hz | ninguno |
| [`03_botones`](03_botones/README.md) | Los seis botones del shield (A a F) como entrada con pull-up, probados con el LED | ninguno |
| [`04_primer_pixel`](04_primer_pixel/README.md) | Primer píxel del panel con GPIO: un píxel verde en x = 7, y = 0 | 1 |
| [`05_colores_y_refresco`](05_colores_y_refresco/README.md) | Framebuffer y refresco con la interrupción de TIM3: 1 de cada 4 píxeles en rojo, verde y azul, un marco y dos diagonales, de 2 s cada uno | 1 |
| [`06_graficos`](06_graficos/README.md) | Biblioteca gráfica: marco, dígitos 0 a 9 y siete barras de colores | 1 |
| [`07_punto_con_botones`](07_punto_con_botones/README.md) | Un punto verde que se mueve con los botones (A arriba, B derecha, C abajo, D izquierda, E pausa, F reinicia) | 1 |
| [`08_orden_serial_paneles`](08_orden_serial_paneles/README.md) | Enciende un solo bit de la cadena de 128 para medir en qué píxel aparece (A y B cambian el bit en 1, E y F en 16, C y D cambian la fase) | 2 |
| [`09_pantalla_32x32`](09_pantalla_32x32/README.md) | Marco verde de 32×32, un dígito en cada esquina y los 7 colores en la unión de los dos paneles | 2 |

## De dónde sale cada una
- **01 a 07:** son el código tal como quedó en el commit de cada paso del desarrollo (pasos 1 a 7), sin cambios. Por eso usan las versiones de entonces de los módulos: un solo panel de 32×16 y los botones con las direcciones de esa época. El juego definitivo, con dos paneles, está en `juego/`.
- **08 y 09:** los archivos originales no se guardaron. Se reconstruyeron a partir del código que aparece en el paso 11 de `docs/GUIA_DE_ESTUDIO.md`: `09` con los módulos del juego definitivo y `08` con los del paso 10 más la función `dibujar_fase_de_prueba` y la constante `PANEL_BITS_POR_CADENA`. Solo se cambió el primer comentario de cada `main.c`.
- La sintaxis de las 9 carpetas se revisó con el compilador del PC (`gcc -fsyntax-only -Wall -Wextra`, 0 avisos). No se compilaron con `arm-none-eabi-gcc` al escribir estas explicaciones. 08 y 09 no se volvieron a grabar en la placa con esta reconstrucción.

## Explicación del código, línea por línea

Cada carpeta tiene su propio `README.md` que recorre **todos** los archivos de esa prueba **por trozos de código**: se muestra el código real, y debajo qué hace, **por qué se hace así** y qué significa. Los programas se acumulan (cada uno parte del anterior), así que cada README explica con detalle **lo que se agrega** y avisa qué archivos no cambian.

| README | Qué explica |
|---|---|
| [01 LED con botón](01_led_con_boton/README.md) | **Todo el arranque:** `Makefile`, `linker_script.ld`, `crt0.S` (tabla de vectores), `registros_f446.h`, `gpio_config` y `main.c` |
| [02 Parpadeo](02_led_parpadeo/README.md) | Reloj a 84 MHz (PLL), SysTick y `esperar_milisegundos` |
| [03 Botones](03_botones/README.md) | Los seis botones como entradas con pull-up, puerto B y los pines de depuración PB3 y PB4 |
| [04 Primer píxel](04_primer_pixel/README.md) | Señales del panel HUB75, `desplazar_bit`, enviar una fase, BSRR |
| [05 Colores y refresco](05_colores_y_refresco/README.md) | Framebuffer, `encender_pixel`, TIM3 y su interrupción |
| [06 Gráficos](06_graficos/README.md) | Colores, fuente 3×5, `borrar_pantalla`, rectángulos y dígitos |
| [07 Punto con botones](07_punto_con_botones/README.md) | Módulo `botones`, temporizador de software con SysTick, lógica del punto |
| [08 Orden serial](08_orden_serial_paneles/README.md) | Cadena de 128 bits, detección de flancos, antirrebote, `dibujar_numero` y el generador aleatorio (LFSR) |
| [09 Pantalla 32×32](09_pantalla_32x32/README.md) | Dos paneles como una sola pantalla: `modulo`, giro de 180° y botón de reinicio |

> Orden recomendado: 01 → 09, en orden. Los programas de Python de las mediciones se explican aparte, en [`mediciones/`](../mediciones/README.md).

## Preguntas de sustentación (con respuesta)

**1. ¿Qué hace `crt0.S` antes de `main`?**  
Pone el SP en el final de la RAM, copia el valor inicial de `.data` de la FLASH a la RAM, llena `.bss` de ceros y llama a `main`. Además contiene la tabla de vectores.

**2. ¿Por qué `.data` está en la RAM pero también guardada en la FLASH?**  
La RAM se borra al apagar; el valor inicial tiene que estar en memoria permanente. El linker lo ubica con `> RAM AT> FLASH` y `crt0.S` lo copia.

**3. ¿Por qué el nombre `TIM3_IRQHandler` es obligatorio?**  
La tabla de vectores apunta a ese nombre con un alias débil a `Default_Handler`. Al definir una función con el mismo nombre, la tuya reemplaza al alias.

**4. ¿Para qué sirve `volatile`?**  
Obliga al compilador a leer/escribir realmente el registro o la variable cada vez. Se usa en los registros, en el contador de SysTick y en el framebuffer (lo escribe `main` y lo lee la interrupción).

**5. ¿Qué error tenía la macro del profesor y cómo se corrigió?**  
`~MASK` sin paréntesis: `~0x3U << n` se evalúa como `(~0x3U) << n` y borra la configuración de los pines de menor número. Se corrigió con `~(0x3U << n)`.

**6. ¿Por qué `escribir_pin` pasó de ODR a BSRR (de la prueba 04 en adelante)?**  
BSRR no lee el registro: poner o borrar un pin es una sola escritura atómica. Así la interrupción y `main` no se pisan al tocar pines del mismo puerto.

**7. ¿Cómo se llega a 84 MHz?**  
HSI 16 MHz ÷ 16 (M) × 336 (N) = 336 MHz ÷ 4 (P) = 84 MHz. Antes: 2 estados de espera en la FLASH y APB1 ÷ 2 (42 MHz).

**8. ¿Por qué TIM3 tiene 84 MHz si el APB1 está a 42 MHz?**  
Cuando el divisor del APB1 es distinto de 1, el reloj de los timers de ese bus es el doble.

**9. ¿Cómo se obtiene 1 ms con TIM3?**  
PSC = 83 → 84 MHz / 84 = 1 MHz; ARR = 999 → 1000 cuentas = 1 ms.

**10. ¿Qué es el escaneo 1/4 y cuántos bits se envían por fase?**  
En cada fase se encienden 4 filas (`fase`, +4, +8, +12), elegidas con A y B. Cada bit lleva dos píxeles (R1G1B1 arriba y R2G2B2 abajo), así que 2 filas × 32 columnas = 64 bits por panel (128 con dos).

**11. ¿Por qué se apaga OE antes de hacer LAT y cambiar A/B?**  
Para que no se vea basura mientras cambian el latch y la fila. Se vuelve a encender cuando la fase nueva ya está cargada.

**12. ¿Por qué el tiempo del juego está separado del refresco?**  
El refresco corre por interrupción de TIM3 (cada 1 ms) y no puede esperar. El juego usa un temporizador de software con SysTick y una bandera, así `main` nunca se bloquea.

**13. ¿Cómo se detecta una pulsación una sola vez (prueba 08)?**  
`nuevos = botones & ~botones_anteriores`: solo los bits que están en 1 ahora y estaban en 0 antes.

**14. ¿Por qué el panel 2 usa `31 - x` y `31 - y`?**  
Está montado girado 180°, así que sus columnas y filas se cuentan desde el otro lado. Se descubrió con la prueba 08.

## Lo que conviene revisar antes de sustentar

- **Referencias del manual marcadas "por verificar"** en `registros_f446.h`. Confírmalas en el RM0390 y en el PM0214 (el manual del núcleo).
- **Pruebas 08 y 09 reconstruidas** y no regrabadas en la placa con esa reconstrucción.
- **Sin `iniciar_systick()` en la prueba 09**: funciona porque no usa esperas, pero es una diferencia con las demás.
- Si cambias un `.h`, haz `make clean`: el Makefile no sigue las dependencias de los encabezados.

Las explicaciones se escribieron leyendo el código de cada carpeta. Las pruebas 01 a 07 son las que se grabaron en la placa en su momento; 08 y 09 se reconstruyeron y no se volvieron a grabar. Solo se revisó la sintaxis con el compilador del PC; no se compiló con `arm-none-eabi-gcc`.
