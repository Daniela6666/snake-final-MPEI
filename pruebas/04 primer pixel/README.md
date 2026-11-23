# Prueba 04: el primer píxel del panel

**Qué hace en la placa:** enciende **un solo píxel verde** del panel P10, en la columna 7 y la fila 0 (arriba a la izquierda, a 7 columnas del borde). El resto del panel queda apagado.

**Para qué sirve:** es la primera prueba con el panel. Comprueba a la vez tres cosas: que los 11 pines del panel están bien conectados y configurados, que el **protocolo HUB75** (desplazar bits con CLK, copiarlos con LAT, elegir la fase con A y B, encender con OE) está bien implementado a mano, y que la **fórmula de mapeo** medida (`docs/mapeo_pixeles.md`) es correcta: el bit 0 de la fase 0 debe aparecer en (x = 7, y = 0).

**Qué se agrega respecto a la prueba 03:** el módulo `panel` (`inc/panel.h`, `src/panel.c`) y dos cambios pequeños en `gpio_config`.

**Qué NO cambia:** `Makefile`, `linker_script.ld`, `crt0.S` y `system_config` (ver los README de las pruebas 01 y 02).

### Cómo funciona un panel HUB75 (resumen)

El panel P10 tiene **registros de desplazamiento** (como una fila de casillas). No se escribe un píxel directamente; se meten **bits** uno por uno y luego se "congelan":

| Señal | Pin | Qué hace |
|---|---|---|
| R1, G1, B1 | PC0, PC1, PC2 | Color (1 bit por canal) de un píxel de la **mitad de arriba** |
| R2, G2, B2 | PC3, PC4, PC5 | Color de un píxel de la **mitad de abajo** |
| CLK | PC8 | Cada **flanco de subida** mete en el registro los 6 bits de color que hay en los pines |
| LAT | PC7 | Un pulso **copia** lo desplazado a las salidas (el *latch*) |
| OE | PC6 | *Output Enable*: habilita las salidas. Es **activo en bajo** (0 = encendido) |
| A, B | PC10, PC11 | Eligen cuál de las **4 fases** se muestra (fase = 2·B + A) |

El panel es de **escaneo 1/4**: nunca enciende todas las filas a la vez; muestra 4 filas por fase y rota entre las 4 fases. Para dibujar una fase: (1) desplazar todos los bits de esa fase; (2) apagar OE; (3) pulso de LAT; (4) poner A y B; (5) encender OE.

### 1. `inc/gpio_config.h`: lo que cambia

El resto es igual que en la prueba 03.

**Líneas 21 a 22**

```c
// Velocidad alta: OSPEEDR = 11. Fuente: RM0390, sección 7.4, registro GPIOx_OSPEEDR (código por verificar en el PDF).
#define VELOCIDAD_ALTA 3U
```

- Se agrega `VELOCIDAD_ALTA 3U` (OSPEEDR = `11`): los pines del panel (sobre todo CLK y LAT) necesitan **flancos rápidos**. El comentario deja constancia de que el código del campo estaba por verificar en el manual.

**Línea 32**

```c
    // Velocidad del pin: VELOCIDAD_BAJA o VELOCIDAD_ALTA.
```

- El comentario del campo `velocidad` ahora dice «BAJA o ALTA».

**Línea 39**

```c
// Enciende el reloj del puerto indicado (puerto A, B o C).
```

- El comentario de `habilitar_reloj_puerto` ahora dice que acepta los puertos A, B o C (en la prueba 03 se agregó B).

### 2. `src/gpio_config.c`: lo que cambia

Aparte de lo siguiente, el archivo incluye la rama del puerto B de la prueba 03 (líneas 9-11) y es igual a la prueba 03 en lo demás.

**Líneas 66 a 80**

```c
// Pone un pin de salida en 1 o en 0 usando BSRR.
// BSRR: los bits 0 a 15 ponen en 1 el pin correspondiente; los bits 16 a 31 lo ponen en 0.
// Los bits escritos con 0 no cambian nada. No se lee el registro, así que no hay lectura-modificación-escritura.
void escribir_pin(RegistrosGPIO *puerto, uint32_t pin, uint32_t estado)
{
    // Si estado es distinto de 0, se escribe 1 en el bit "pin" (0 a 15) de BSRR: el pin queda en 1.
    if (estado != 0U) {
        // Escribir 1 en la mitad baja de BSRR pone el pin en alto, en una sola escritura.
        puerto->BSRR = (1U << pin);
    // Si estado es 0, se escribe 1 en el bit "pin + 16" de BSRR (16 a 31): el pin queda en 0.
    } else {
        // Escribir 1 en la mitad alta de BSRR (pin + 16) pone el pin en bajo, en una sola escritura.
        puerto->BSRR = (1U << (pin + 16U));
    }
}
```

`escribir_pin` ahora usa **`BSRR`** en vez de `ODR`:
- `puerto->BSRR = (1U << pin);` escribe 1 en el bit `pin` (0 a 15) de `BSRR`: el pin pasa a **1**.
- `puerto->BSRR = (1U << (pin + 16U));` escribe 1 en el bit `pin + 16` (16 a 31): el pin pasa a **0**.
- Los bits de `BSRR` que se escriben con **0 no hacen nada**: no se cambia ningún otro pin. Además, **no hay que leer `ODR` antes**, así que no hay *lectura-modificación-escritura*.
- **Por qué importa:** con `ODR |= ...` la CPU hace tres pasos (leer, modificar, escribir). Si una interrupción escribe otro pin del mismo puerto entre esos pasos, el cambio se pierde. Con `BSRR` es **una sola escritura**, atómica. Esto cobra importancia desde la prueba 05, donde la interrupción de TIM3 escribe pines del puerto C mientras `main` también podría hacerlo.
- Además, cada cambio de pin es una sola escritura en vez de leer + escribir, que es menos trabajo al desplazar muchos bits seguidos.

### 3. `inc/panel.h`: interfaz del módulo del panel

**Líneas 1 a 7**

```c
// Guarda de inclusión: si este archivo ya se incluyó, se salta todo hasta #endif (evita definiciones repetidas).
#ifndef PANEL_H
// Marca el archivo como ya incluido.
#define PANEL_H

// Este módulo usa gpio_config.h, por eso se incluye aquí.
#include "gpio_config.h"
```

- Guarda de inclusión (`PANEL_H`) y `#include "gpio_config.h"` (que ya trae los registros): el panel usa `ConfiguracionPin`, `escribir_pin`, etc.

**Líneas 9 a 30**

```c
// Pin R1 del panel (HUB75 pin 1), conectado a PC0. Fuente: docs/conexiones.md.
#define PIN_PANEL_R1 0U
// Pin G1 del panel (HUB75 pin 2), conectado a PC1. Fuente: docs/conexiones.md.
#define PIN_PANEL_G1 1U
// Pin B1 del panel (HUB75 pin 3), conectado a PC2. Fuente: docs/conexiones.md.
#define PIN_PANEL_B1 2U
// Pin R2 del panel (HUB75 pin 5), conectado a PC3. Fuente: docs/conexiones.md.
#define PIN_PANEL_R2 3U
// Pin G2 del panel (HUB75 pin 6), conectado a PC4. Fuente: docs/conexiones.md.
#define PIN_PANEL_G2 4U
// Pin B2 del panel (HUB75 pin 7), conectado a PC5. Fuente: docs/conexiones.md.
#define PIN_PANEL_B2 5U
// Pin OE del panel (HUB75 pin 15), conectado a PC6. Fuente: docs/conexiones.md.
#define PIN_PANEL_OE 6U
// Pin LAT del panel (HUB75 pin 14), conectado a PC7. Fuente: docs/conexiones.md.
#define PIN_PANEL_LAT 7U
// Pin CLK del panel (HUB75 pin 13), conectado a PC8. Fuente: docs/conexiones.md.
#define PIN_PANEL_CLK 8U
// Pin A del panel (HUB75 pin 9), conectado a PC10. Fuente: docs/conexiones.md.
#define PIN_PANEL_A 10U
// Pin B de selección de fase del panel (HUB75 pin 10), conectado a PC11. Fuente: docs/conexiones.md.
#define PIN_PANEL_B 11U
```

Número de pin de cada señal del panel (todas en el puerto C). Los comentarios indican a qué pin del conector **HUB75** va cada una y que la fuente es `docs/conexiones.md`:
- `PIN_PANEL_R1 0U`, `G1 1U`, `B1 2U` → PC0, PC1, PC2 (HUB75 pines 1, 2, 3).
- `PIN_PANEL_R2 3U`, `G2 4U`, `B2 5U` → PC3, PC4, PC5 (HUB75 pines 5, 6, 7).
- `PIN_PANEL_OE 6U` → PC6 (HUB75 pin 15). `PIN_PANEL_LAT 7U` → PC7 (pin 14). `PIN_PANEL_CLK 8U` → PC8 (pin 13).
- `PIN_PANEL_A 10U` → PC10 (pin 9). `PIN_PANEL_B 11U` → PC11 (pin 10). (PC9 no se usa.)
- **Detalle clave:** los seis pines de color son PC0 a PC5, o sea que el **número del pin coincide con la posición del bit** en la variable `datos` (R1 = bit 0, G1 = bit 1, ..., B2 = bit 5). `desplazar_bit` lo aprovecha.

**Líneas 32 a 33**

```c
// Bits que se desplazan por fase y por módulo: 4 bloques de 16. Fuente: docs/mapeo_pixeles.md.
#define PANEL_BITS_POR_FASE 64U
```

- `PANEL_BITS_POR_FASE 64U`: en cada fase hay que desplazar **64 bits** (cada bit lleva dos píxeles: uno de arriba y uno de abajo). Son 4 bloques de 16 bits. La fuente es la medición documentada en `docs/mapeo_pixeles.md`.

**Líneas 35 a 39**

```c
// Nivel de OE que enciende el panel: 0 (OE activo en bajo). Confirmado en la placa (2026-11-09).
// Si otro panel no enciende, se intercambian este valor y NIVEL_OE_APAGADO.
#define NIVEL_OE_ENCENDIDO 0U
// Nivel de OE que apaga el panel: 1, el opuesto de NIVEL_OE_ENCENDIDO. Confirmado en la placa (2026-11-09).
#define NIVEL_OE_APAGADO 1U
```

- `NIVEL_OE_ENCENDIDO 0U` y `NIVEL_OE_APAGADO 1U`: OE es **activo en bajo**: con 0 el panel muestra la imagen, con 1 se apaga. Los comentarios dicen que se confirmó en la placa (2026-11-09) y que, si otro panel no enciende, basta intercambiar los dos valores.

**Líneas 41 a 44**

```c
// Configura los pines del panel como salidas y los deja en un estado seguro.
void configurar_panel(void);
// Envía una fase completa: 64 bits, de los cuales solo el bit bit_encendido lleva datos; el resto va en 0.
void enviar_fase_con_un_bit(uint32_t fase, uint32_t bit_encendido, uint32_t datos);
```

Prototipos:
- `configurar_panel()`: pone los pines como salidas en un estado seguro.
- `enviar_fase_con_un_bit(fase, bit_encendido, datos)`: desplaza los 64 bits de una fase, de los cuales **solo uno lleva datos**; los otros van en 0 (negro).

**Línea 46**

```c
#endif
```

- `#endif`.

### 4. `src/panel.c`: el protocolo HUB75 a mano

**Líneas 1 a 2**

```c
// Se incluye su propia interfaz (panel.h) para que el compilador compruebe que las funciones coinciden con sus prototipos.
#include "panel.h"
```

- Incluye `panel.h`.

**Líneas 4 a 21**

```c
// Configura un pin del panel (puerto C) como salida push-pull, sin resistencia, con velocidad alta.
static void configurar_salida_del_panel(uint32_t pin)
{
    // Datos de configuración del pin del panel.
    ConfiguracionPin configuracion;
    // Modo salida: el microcontrolador maneja el pin y saca el nivel que se le escriba.
    configuracion.modo = MODO_SALIDA;
    // Número del pin dentro del puerto C.
    configuracion.pin = pin;
    // Sin pull-up ni pull-down: el pin lo domina solo la salida.
    configuracion.resistencia = RESISTENCIA_NINGUNA;
    // Velocidad alta: los flancos de CLK y LAT tienen que ser rápidos.
    configuracion.velocidad = VELOCIDAD_ALTA;
    // AF0: no se usa, el pin no es de función alterna.
    configuracion.funcion_alterna = 0U;
    // Se escribe la configuración en el puerto C.
    configurar_pin(GPIOC, configuracion);
}
```

`configurar_salida_del_panel(pin)` es una función auxiliar (`static` = solo visible en este archivo) que configura **un pin del puerto C** para el panel:
- `ConfiguracionPin configuracion;` y se llenan los 5 campos.
- `modo = MODO_SALIDA`: el microcontrolador maneja el pin.
- `pin = pin`: el número recibido.
- `resistencia = RESISTENCIA_NINGUNA`: sin pull-up ni pull-down, el pin lo domina solo la salida.
- `velocidad = VELOCIDAD_ALTA`: CLK y LAT necesitan flancos rápidos.
- `funcion_alterna = 0U`: GPIO normal.
- `configurar_pin(GPIOC, configuracion)` escribe todo en el puerto C.
- Existe para no repetir 11 veces las mismas 5 líneas.

**Líneas 23 a 42**

```c
// Desplaza un bit por los seis colores. datos lleva en sus bits 0 a 5 los valores de R1, G1, B1, R2, G2 y B2.
static void desplazar_bit(uint32_t datos)
{
    // R1 sale por PC0: se toma el bit 0 de datos (el desplazamiento es el número del pin).
    escribir_pin(GPIOC, PIN_PANEL_R1, (datos >> PIN_PANEL_R1) & 1U);
    // G1 sale por PC1: se toma el bit 1 de datos.
    escribir_pin(GPIOC, PIN_PANEL_G1, (datos >> PIN_PANEL_G1) & 1U);
    // B1 sale por PC2: se toma el bit 2 de datos.
    escribir_pin(GPIOC, PIN_PANEL_B1, (datos >> PIN_PANEL_B1) & 1U);
    // R2 sale por PC3: se toma el bit 3 de datos.
    escribir_pin(GPIOC, PIN_PANEL_R2, (datos >> PIN_PANEL_R2) & 1U);
    // G2 sale por PC4: se toma el bit 4 de datos.
    escribir_pin(GPIOC, PIN_PANEL_G2, (datos >> PIN_PANEL_G2) & 1U);
    // B2 sale por PC5: se toma el bit 5 de datos.
    escribir_pin(GPIOC, PIN_PANEL_B2, (datos >> PIN_PANEL_B2) & 1U);
    // CLK en 1: el panel toma el bit de los pines de color en este flanco de subida.
    escribir_pin(GPIOC, PIN_PANEL_CLK, 1U);
    // CLK en 0: deja CLK listo para el siguiente bit.
    escribir_pin(GPIOC, PIN_PANEL_CLK, 0U);
}
```

`desplazar_bit(datos)` mete **un bit de cada color** en el panel:
- `datos` es un número cuyos **bits 0 a 5** son R1, G1, B1, R2, G2, B2.
- Líneas 26-37: para cada color, `(datos >> PIN_PANEL_X) & 1U` **extrae un bit**. `>>` desplaza el número a la derecha para llevar el bit deseado a la posición 0 y `& 1U` descarta el resto. Ejemplo: R1 es `(datos >> 0) & 1`; G1 es `(datos >> 1) & 1`. Esto funciona **porque el número de pin coincide con la posición del bit**. `escribir_pin(GPIOC, PIN_PANEL_X, ese_bit)` lo saca por el pin.
- Líneas 38-39: `escribir_pin(GPIOC, PIN_PANEL_CLK, 1U)`: CLK sube. En ese **flanco de subida** el panel toma los 6 bits de color y los mete en su registro de desplazamiento.
- Líneas 40-41: CLK baja, listo para el siguiente bit.

**Líneas 44 a 77**

```c
// Configura los pines del panel. Primero se dejan en un nivel seguro y después pasan a salida.
void configurar_panel(void)
{
    // Se enciende el reloj del puerto C antes de escribir sus registros.
    habilitar_reloj_puerto(GPIOC);
    // OE apagado antes de ser salida: el panel no debe mostrar basura mientras se configura.
    escribir_pin(GPIOC, PIN_PANEL_OE, NIVEL_OE_APAGADO);
    // CLK en 0 antes de ser salida: el reset deja ODR en 0, pero se escribe por claridad.
    escribir_pin(GPIOC, PIN_PANEL_CLK, 0U);
    // LAT en 0 antes de ser salida: el panel no debe cargar datos mientras se configura.
    escribir_pin(GPIOC, PIN_PANEL_LAT, 0U);
    // R1 como salida.
    configurar_salida_del_panel(PIN_PANEL_R1);
    // G1 como salida.
    configurar_salida_del_panel(PIN_PANEL_G1);
    // B1 como salida.
    configurar_salida_del_panel(PIN_PANEL_B1);
    // R2 como salida.
    configurar_salida_del_panel(PIN_PANEL_R2);
    // G2 como salida.
    configurar_salida_del_panel(PIN_PANEL_G2);
    // B2 como salida.
    configurar_salida_del_panel(PIN_PANEL_B2);
    // OE como salida.
    configurar_salida_del_panel(PIN_PANEL_OE);
    // LAT como salida.
    configurar_salida_del_panel(PIN_PANEL_LAT);
    // CLK como salida.
    configurar_salida_del_panel(PIN_PANEL_CLK);
    // A como salida (selección de fase).
    configurar_salida_del_panel(PIN_PANEL_A);
    // B como salida (selección de fase).
    configurar_salida_del_panel(PIN_PANEL_B);
}
```

`configurar_panel()` deja los pines listos:
- Línea 48: `habilitar_reloj_puerto(GPIOC)`: el reloj del puerto C **antes** de escribir sus registros.
- Líneas 49-54: **primero** se escriben los niveles seguros (OE apagado = 1, CLK = 0, LAT = 0) y **después** los pines pasan a ser salidas. Así, en el instante en que cada pin se vuelve salida ya tiene el nivel correcto y el panel no recibe pulsos ni se enciende con basura. (El comentario de CLK explica que el reset deja `ODR` en 0 y que se escribe igual por claridad.)
- Líneas 55-76: `configurar_salida_del_panel` para los 11 pines: R1, G1, B1, R2, G2, B2, OE, LAT, CLK, A y B.

**Líneas 79 a 104**

```c
// Envía una fase completa. Solo el bit bit_encendido lleva datos; los demás bits van en 0.
void enviar_fase_con_un_bit(uint32_t fase, uint32_t bit_encendido, uint32_t datos)
{
    // Se desplazan los 64 bits de la fase, uno por uno, con CLK.
    for (uint32_t bit = 0U; bit < PANEL_BITS_POR_FASE; bit++) {
        // Si es el bit elegido, se desplazan los datos.
        if (bit == bit_encendido) {
            desplazar_bit(datos);
        // Si no es el bit elegido, se desplaza 0 para que ese píxel quede apagado.
        } else {
            desplazar_bit(0U);
        }
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

`enviar_fase_con_un_bit(fase, bit_encendido, datos)` dibuja una fase siguiendo el protocolo:
- Líneas 83-91: `for (uint32_t bit = 0U; bit < 64; bit++)`: recorre los 64 bits de la fase. Si `bit == bit_encendido` desplaza `datos`; en los demás desplaza `0U` (negro). Cada llamada a `desplazar_bit` mete 6 bits y da un pulso de CLK.
- Líneas 92-93: **OE apagado** (`NIVEL_OE_APAGADO`) mientras se cambian el latch y la fila: así no se ve basura durante el cambio.
- Líneas 94-97: **LAT sube y baja**: un pulso que copia los 64 bits desplazados a las salidas del panel. Va **después de desplazar todos los bits**, no antes.
- Líneas 98-101: se ponen A y B según la `fase`: `A = fase & 1` (bit 0 de la fase) y `B = (fase >> 1) & 1` (bit 1). Con eso el panel elige cuál de sus 4 grupos de filas va a mostrar.
- Líneas 102-103: **OE encendido** (`NIVEL_OE_ENCENDIDO`): el panel muestra la fase recién cargada.

### 5. `main.c`: el programa

**Líneas 1 a 4**

```c
// Se incluye la configuración del reloj y del temporizador SysTick.
#include "system_config.h"
// Se incluye el módulo del panel LED (framebuffer y refresco).
#include "panel.h"
```

- Incluye el módulo de reloj y el del panel.

**Líneas 6 a 8**

```c
// Función principal: crt0.S la llama cuando termina de preparar la RAM.
int main(void)
{
```

- `int main(void) {`

**Líneas 9 a 12**

```c
    // Primero el reloj, antes de usar cualquier periférico: deja el sistema a 84 MHz.
    configurar_reloj();
    // Se enciende la base de tiempo de 1 ms (SysTick).
    iniciar_systick();
```

- `configurar_reloj()` (84 MHz) e `iniciar_systick()`, igual que en la prueba 02. Esta prueba no usa la espera, pero mantiene el mismo arranque.

**Líneas 14 a 15**

```c
    // Se configuran los pines del panel como salidas.
    configurar_panel();
```

- `configurar_panel()`: pone los 11 pines en salida con niveles seguros.

**Líneas 16 a 18**

```c
    // Según la fórmula de docs/mapeo_pixeles.md, el bit 0 de la fase 0 corresponde al píxel x = 7, y = 0.
    // Se envía fase 0, bit 0 con datos solo en G1 (verde): debe encenderse ese píxel en verde.
    enviar_fase_con_un_bit(0U, 0U, (1U << PIN_PANEL_G1));
```

- `enviar_fase_con_un_bit(0U, 0U, (1U << PIN_PANEL_G1));`: fase **0**, bit **0**, y `datos` con solo el bit de **G1** en 1 (`1U << 1` = `0b000010`): verde de la mitad de arriba.
- Según la fórmula de `docs/mapeo_pixeles.md`, el bit 0 de la fase 0 es el píxel **(x = 7, y = 0)**. Es decir, si el mapeo está bien, **se enciende ese píxel en verde**. Si apareciera otro, la fórmula estaría mal.

**Líneas 20 a 24**

```c
    // Bucle infinito: un microcontrolador no termina, repite esto mientras tenga energía.
    while (1) {
        // El panel conserva lo enviado mientras OE esté encendido; no hace falta repetir el envío.
    }
}
```

- `while (1) { }`: no hace nada más. El panel **conserva** lo enviado mientras OE esté encendido, así que no hace falta repetir el envío. (Esta prueba envía una sola fase. Para mostrar una imagen completa hay que repetir las 4 fases continuamente; eso llega en la prueba 05 con el framebuffer y la interrupción.)

