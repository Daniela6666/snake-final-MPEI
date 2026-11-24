# Prueba 03: los seis botones del shield

**Qué hace en la placa:** el LED de la placa (PA5) se enciende si **cualquiera de los seis botones del shield (A a F) está presionado** y se apaga si ninguno lo está.

**Para qué sirve:** comprobar el cableado de los seis botones **antes** de usarlos en el juego. Si al presionar cada uno el LED enciende, el botón está bien conectado y el pin está bien configurado.

**Qué se agrega respecto a la prueba 02:**
- Soporte para el **puerto B** (cuatro de los seis botones están en PB3, PB4, PB5 y PB10).
- Seis entradas con **pull-up**.

**Qué NO cambia:** `Makefile`, `linker_script.ld`, `crt0.S` y `system_config` son los de la prueba 02 (ver [`../02_led_parpadeo/README.md`](../02_led_parpadeo/README.md) y [`../01_led_con_boton/README.md`](../01_led_con_boton/README.md)).

**Los botones del shield** son activos en bajo (presionado = 0) y están en:

| Botón | Pin | Puerto |
|---|---|---|
| A | PA10 | A |
| B | PB3 | B |
| C | PB5 | B |
| D | PB4 | B |
| E | PB10 | B |
| F | PA8 | A |

### 1. `inc/registros_f446.h`: lo que se agrega

Solo cambian estas líneas respecto a la prueba 02 (el resto se explica en los README de las pruebas 01 y 02).

**Líneas 18 a 19**

```c
// Puerto B de GPIO (0x40020400). Fuente: RM0390, sección 2.2.2, tabla 1.
#define GPIOB_BASE (AHB1_BASE + 0x400U)
```

- `GPIOB_BASE = AHB1_BASE + 0x400` → `0x40020400`: el puerto B está 0x400 bytes después del A (cada puerto ocupa 1 KB del mapa de memoria).

**Línea 80**

```c
    // Desplazamiento 0x30. Habilita el reloj de cada puerto GPIO (bit 0 = puerto A, bit 1 = puerto B, bit 2 = puerto C).
```

- El comentario de `AHB1ENR` ahora dice que el **bit 1** es el puerto B (junto al bit 0 = A y el bit 2 = C).

**Líneas 108 a 109**

```c
// Puntero al puerto B de GPIO (botones B, C, D y E del shield).
#define GPIOB ((RegistrosGPIO *)GPIOB_BASE)
```

- `GPIOB` es el puntero al puerto B, igual que `GPIOA` y `GPIOC`.

**Líneas 121 a 122**

```c
// Bit 1 de RCC_AHB1ENR: 1 enciende el reloj del puerto B. Fuente: RM0390, sección 6.3.10.
#define RCC_AHB1ENR_GPIOBEN (1U << 1)
```

- `RCC_AHB1ENR_GPIOBEN (1U << 1)`: el bit que enciende el reloj del puerto B.

### 2. `src/gpio_config.c`: lo que se agrega

El resto del archivo es idéntico a la prueba 01.

**Líneas 11 a 14**

```c
    // Si el puerto es B, se pone en 1 el bit 1 de RCC->AHB1ENR (|= no cambia los demás bits).
    } else if (puerto == GPIOB) {
        // Se enciende el reloj del puerto GPIOB.
        RCC->AHB1ENR |= RCC_AHB1ENR_GPIOBEN;
```

- Se agrega una rama a `habilitar_reloj_puerto`: `else if (puerto == GPIOB) { RCC->AHB1ENR |= RCC_AHB1ENR_GPIOBEN; }`. Sin esto, al configurar un pin del puerto B **no se encendería su reloj** y la configuración no tendría efecto (el pin seguiría como entrada flotante en reset).

### 3. `main.c`: el programa

**Líneas 1 a 6**

```c
// Se incluyen las definiciones de los registros del microcontrolador.
#include "registros_f446.h"
// Se incluye el módulo de configuración de pines (GPIO).
#include "gpio_config.h"
// Se incluye la configuración del reloj y del temporizador SysTick.
#include "system_config.h"
```

- Incluye registros, módulo de pines y módulo de reloj.

**Líneas 8 a 21**

```c
// Número del pin del LED de la placa (PA5).
#define PIN_LED 5U
// Botón A del shield: pin PA10, activo en bajo (presionado = 0).
#define PIN_BOTON_A 10U
// Botón B del shield: pin PB3, activo en bajo (presionado = 0).
#define PIN_BOTON_B 3U
// Botón C del shield: pin PB5, activo en bajo (presionado = 0).
#define PIN_BOTON_C 5U
// Botón D del shield: pin PB4, activo en bajo (presionado = 0).
#define PIN_BOTON_D 4U
// Botón E del shield: pin PB10, activo en bajo (presionado = 0).
#define PIN_BOTON_E 10U
// Botón F del shield: pin PA8, activo en bajo (presionado = 0).
#define PIN_BOTON_F 8U
```

- `PIN_LED 5U`: el LED de la placa.
- `PIN_BOTON_A` a `PIN_BOTON_F`: el **número de pin** de cada botón dentro de su puerto (la tabla de arriba). Los comentarios dicen "activo en bajo (presionado = 0)": con el pull-up interno, el pin vale 1 en reposo y **baja a 0 al presionar**.

**Líneas 23 a 29**

```c
// Función principal: crt0.S la llama cuando termina de preparar la RAM.
int main(void)
{
    // Primero el reloj, antes de usar cualquier periférico: deja el sistema a 84 MHz.
    configurar_reloj();
    // Se enciende la base de tiempo de 1 ms (SysTick).
    iniciar_systick();
```

- `main` empieza igual que en la prueba 02: `configurar_reloj()` primero y después `iniciar_systick()`. (Esta prueba no usa la espera, pero deja el reloj en el mismo estado que las demás.)

**Líneas 31 a 44**

```c
    // Configuración del LED de la placa (PA5).
    ConfiguracionPin configuracion_led;
    // El LED es una salida.
    configuracion_led.modo = MODO_SALIDA;
    // Número del pin del LED.
    configuracion_led.pin = PIN_LED;
    // Sin pull-up ni pull-down en el LED.
    configuracion_led.resistencia = RESISTENCIA_NINGUNA;
    // Velocidad baja.
    configuracion_led.velocidad = VELOCIDAD_BAJA;
    // AF0: no se usa, el pin no es de función alterna.
    configuracion_led.funcion_alterna = 0U;
    // Se escribe la configuración del LED en el puerto A.
    configurar_pin(GPIOA, configuracion_led);
```

- Configura el LED de la placa igual que en las pruebas anteriores.

**Líneas 46 a 59**

```c
    // Configuración del botón A (PA10) como entrada.
    ConfiguracionPin configuracion_boton_A;
    // El botón es una entrada.
    configuracion_boton_A.modo = MODO_ENTRADA;
    // Número del pin del botón A.
    configuracion_boton_A.pin = PIN_BOTON_A;
    // Pull-up interno: el pin queda en 1 mientras el botón no está presionado.
    configuracion_boton_A.resistencia = RESISTENCIA_PULL_UP;
    // Velocidad baja.
    configuracion_boton_A.velocidad = VELOCIDAD_BAJA;
    // AF0: no se usa, el pin no es de función alterna.
    configuracion_boton_A.funcion_alterna = 0U;
    // Se escribe la configuración del botón A en el puerto A.
    configurar_pin(GPIOA, configuracion_boton_A);
```

Configura el botón A (PA10):
- `configuracion_boton_A.modo = MODO_ENTRADA;` el pin lee, no maneja.
- `.pin = PIN_BOTON_A;` el número de pin.
- `.resistencia = RESISTENCIA_PULL_UP;` **imprescindible**: el botón solo conecta el pin a tierra al presionarse; sin pull-up, al soltarlo el pin quedaría flotante y se leerían valores al azar.
- `.velocidad = VELOCIDAD_BAJA;` y `.funcion_alterna = 0U;` (no se usa; el pin es un GPIO normal).
- `configurar_pin(GPIOA, configuracion_boton_A);` lo escribe en el puerto **A**.

**Líneas 61 a 74**

```c
    // Configuración del botón B (PB3) como entrada.
    ConfiguracionPin configuracion_boton_B;
    // El botón es una entrada.
    configuracion_boton_B.modo = MODO_ENTRADA;
    // Número del pin del botón B.
    configuracion_boton_B.pin = PIN_BOTON_B;
    // Pull-up interno: el pin queda en 1 mientras el botón no está presionado.
    configuracion_boton_B.resistencia = RESISTENCIA_PULL_UP;
    // Velocidad baja.
    configuracion_boton_B.velocidad = VELOCIDAD_BAJA;
    // AF0: no se usa, el pin no es de función alterna.
    configuracion_boton_B.funcion_alterna = 0U;
    // PB3 arranca en función alterna de depuración; por eso se configura explícitamente como entrada.
    configurar_pin(GPIOB, configuracion_boton_B);
```

Botón B (PB3), mismo patrón, en el puerto **B**. El comentario de la línea 73 explica algo importante: **PB3 arranca con una función alterna de depuración** (JTAG/SWO). Por eso se configura *explícitamente*: `configurar_pin` escribe `MODER` = entrada y `AFRL` = 0 (AF0) para ese pin, dejándolo como un GPIO normal.

**Líneas 76 a 89**

```c
    // Configuración del botón C (PB5) como entrada.
    ConfiguracionPin configuracion_boton_C;
    // El botón es una entrada.
    configuracion_boton_C.modo = MODO_ENTRADA;
    // Número del pin del botón C.
    configuracion_boton_C.pin = PIN_BOTON_C;
    // Pull-up interno: el pin queda en 1 mientras el botón no está presionado.
    configuracion_boton_C.resistencia = RESISTENCIA_PULL_UP;
    // Velocidad baja.
    configuracion_boton_C.velocidad = VELOCIDAD_BAJA;
    // AF0: no se usa, el pin no es de función alterna.
    configuracion_boton_C.funcion_alterna = 0U;
    // Se escribe la configuración del botón C en el puerto B.
    configurar_pin(GPIOB, configuracion_boton_C);
```

Botón C (PB5), mismo patrón, puerto B.

**Líneas 91 a 104**

```c
    // Configuración del botón D (PB4) como entrada.
    ConfiguracionPin configuracion_boton_D;
    // El botón es una entrada.
    configuracion_boton_D.modo = MODO_ENTRADA;
    // Número del pin del botón D.
    configuracion_boton_D.pin = PIN_BOTON_D;
    // Pull-up interno: el pin queda en 1 mientras el botón no está presionado.
    configuracion_boton_D.resistencia = RESISTENCIA_PULL_UP;
    // Velocidad baja.
    configuracion_boton_D.velocidad = VELOCIDAD_BAJA;
    // AF0: no se usa, el pin no es de función alterna.
    configuracion_boton_D.funcion_alterna = 0U;
    // PB4 arranca en función alterna de depuración; por eso se configura explícitamente como entrada.
    configurar_pin(GPIOB, configuracion_boton_D);
```

Botón D (PB4), mismo patrón, puerto B. Igual que PB3, **PB4 arranca en función de depuración** (JTAG), por eso se configura explícitamente.

**Líneas 106 a 119**

```c
    // Configuración del botón E (PB10) como entrada.
    ConfiguracionPin configuracion_boton_E;
    // El botón es una entrada.
    configuracion_boton_E.modo = MODO_ENTRADA;
    // Número del pin del botón E.
    configuracion_boton_E.pin = PIN_BOTON_E;
    // Pull-up interno: el pin queda en 1 mientras el botón no está presionado.
    configuracion_boton_E.resistencia = RESISTENCIA_PULL_UP;
    // Velocidad baja.
    configuracion_boton_E.velocidad = VELOCIDAD_BAJA;
    // AF0: no se usa, el pin no es de función alterna.
    configuracion_boton_E.funcion_alterna = 0U;
    // Se escribe la configuración del botón E en el puerto B.
    configurar_pin(GPIOB, configuracion_boton_E);
```

Botón E (PB10), mismo patrón, puerto B.

**Líneas 121 a 134**

```c
    // Configuración del botón F (PA8) como entrada.
    ConfiguracionPin configuracion_boton_F;
    // El botón es una entrada.
    configuracion_boton_F.modo = MODO_ENTRADA;
    // Número del pin del botón F.
    configuracion_boton_F.pin = PIN_BOTON_F;
    // Pull-up interno: el pin queda en 1 mientras el botón no está presionado.
    configuracion_boton_F.resistencia = RESISTENCIA_PULL_UP;
    // Velocidad baja.
    configuracion_boton_F.velocidad = VELOCIDAD_BAJA;
    // AF0: no se usa, el pin no es de función alterna.
    configuracion_boton_F.funcion_alterna = 0U;
    // Se escribe la configuración del botón F en el puerto A.
    configurar_pin(GPIOA, configuracion_boton_F);
```

Botón F (PA8), mismo patrón, puerto **A**.

**Líneas 136 a 157**

```c
    // Bucle infinito: un microcontrolador no termina, repite esto mientras tenga energía.
    while (1) {
        // Los botones son activos en bajo: presionado = pin en 0. El LED se enciende si CUALQUIERA de los seis está presionado, y se apaga si ninguno lo está.
        if (leer_pin(GPIOA, PIN_BOTON_A) == 0U ||
            // ... o el botón B está presionado (pin en 0) ...
            leer_pin(GPIOB, PIN_BOTON_B) == 0U ||
            // ... o el botón C está presionado ...
            leer_pin(GPIOB, PIN_BOTON_C) == 0U ||
            // ... o el botón D está presionado ...
            leer_pin(GPIOB, PIN_BOTON_D) == 0U ||
            // ... o el botón E está presionado ...
            leer_pin(GPIOB, PIN_BOTON_E) == 0U ||
            // ... o el botón F está presionado.
            leer_pin(GPIOA, PIN_BOTON_F) == 0U) {
            // Algún botón está presionado: el LED PA5 se enciende (es activo en alto).
            escribir_pin(GPIOA, PIN_LED, 1U);
        } else {
            // Ningún botón está presionado: el LED PA5 se apaga.
            escribir_pin(GPIOA, PIN_LED, 0U);
        }
    }
}
```

Bucle principal:
- Líneas 139-149: `if (leer_pin(GPIOA, PIN_BOTON_A) == 0U || leer_pin(GPIOB, PIN_BOTON_B) == 0U || ...)`. El operador `||` es "o": la condición es verdadera si **al menos uno** de los seis botones está en 0 (presionado). C evalúa de izquierda a derecha y se detiene en cuanto uno es verdadero.
- Línea 150-151: si algún botón está presionado, `escribir_pin(GPIOA, PIN_LED, 1U)` enciende el LED (el LED de la placa es activo en alto: 1 = encendido).
- Líneas 152-155: en caso contrario, `escribir_pin(GPIOA, PIN_LED, 0U)` lo apaga.
- Es *polling*: cada vuelta lee los seis pines y actualiza el LED.
- Esta forma repite seis veces el mismo bloque de configuración. En la prueba 07 eso se reemplaza por el módulo `botones` (una función `configurar_botones()` y otra `leer_botones()`).

