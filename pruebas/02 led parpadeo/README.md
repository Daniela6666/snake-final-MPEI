# Prueba 02: reloj a 84 MHz, SysTick y parpadeo a 1 Hz

**Qué hace en la placa:** el LED de la placa (PA5) parpadea a 1 Hz: 500 ms encendido y 500 ms apagado.

**Qué se agrega respecto a la prueba 01:**
- El módulo `system_config` (`inc/system_config.h` y `src/system_config.c`): sube el reloj del chip de 16 MHz a **84 MHz** con el PLL, y enciende **SysTick**, un contador del núcleo que interrumpe cada **1 ms**.
- Más registros en `registros_f446.h`: FLASH, SysTick y los campos del RCC para el reloj.
- `main.c` ahora usa `esperar_milisegundos` para marcar el tiempo.

**Qué NO cambia:** `Makefile`, `linker_script.ld`, `crt0.S` y `gpio_config.c/.h` son los de la prueba 01 (ver [`../01_led_con_boton/README.md`](../01_led_con_boton/README.md)).

**Cómo se comprueba que el reloj está bien:** si el LED parpadea a 1 Hz *reales* (mide con un cronómetro), el PLL y SysTick están bien configurados. Si el PLL estuviera mal, el parpadeo sería más lento o más rápido de lo esperado.

### 1. `inc/system_config.h`: la interfaz del módulo de reloj

**Líneas 1 a 7**

```c
// Guarda de inclusión: si este archivo ya se incluyó, se salta todo hasta #endif (evita definiciones repetidas).
#ifndef SYSTEM_CONFIG_H
// Marca el archivo como ya incluido.
#define SYSTEM_CONFIG_H

// Este módulo usa registros_f446.h, por eso se incluye aquí.
#include "registros_f446.h"
```

- Guarda de inclusión (`SYSTEM_CONFIG_H`) y se incluyen los registros, porque este módulo usa `uint32_t` y los punteros del RCC y SysTick.

**Líneas 9 a 12**

```c
// Frecuencia del reloj del sistema (SYSCLK y HCLK) después de configurar_reloj: 84 MHz.
#define FRECUENCIA_RELOJ_HZ 84000000U
// Interrupciones de SysTick por segundo: 1000 = una interrupción por milisegundo (base de tiempo de 1 ms).
#define INTERRUPCIONES_SYSTICK_POR_SEGUNDO 1000U
```

- `FRECUENCIA_RELOJ_HZ 84000000U`: la frecuencia a la que queda el reloj del sistema tras `configurar_reloj` (84 MHz). Se usa para calcular el valor de SysTick.
- `INTERRUPCIONES_SYSTICK_POR_SEGUNDO 1000U`: se quiere una interrupción por milisegundo, o sea 1000 por segundo.
- Los dos valores van como constantes con nombre, no como números sueltos, para que el cálculo de `LOAD` se lea como una fórmula.

**Líneas 14 a 19**

```c
// Configura el PLL a 84 MHz, la latencia de la FLASH y los divisores de los buses. Se llama antes que cualquier periférico.
void configurar_reloj(void);
// Enciende SysTick para que interrumpa cada 1 ms (base de tiempo).
void iniciar_systick(void);
// Espera la cantidad de milisegundos indicada. Mientras espera, la interrupción de SysTick sigue contando.
void esperar_milisegundos(uint32_t milisegundos);
```

Prototipos de las tres funciones públicas:
- `configurar_reloj()`: sube el reloj a 84 MHz. **Se llama antes que cualquier periférico.**
- `iniciar_systick()`: enciende la interrupción de 1 ms.
- `esperar_milisegundos(n)`: espera `n` ms. Mientras espera, la interrupción de SysTick sigue contando.

**Línea 21**

```c
#endif
```

- `#endif` cierra la guarda.

### 2. `src/system_config.c`: reloj a 84 MHz, SysTick y espera

**Líneas 1 a 2**

```c
// Se incluye su propia interfaz (system_config.h) para que el compilador compruebe que las funciones coinciden con sus prototipos.
#include "system_config.h"
```

- Incluye su propio `.h`.

**Líneas 4 a 5**

```c
// Estados de espera de la FLASH (LATENCY = 2). Con VDD de 2.7 a 3.6 V, 2 estados de espera son necesarios para 60 < HCLK ≤ 90 MHz. Fuente: RM0390, sección 3.4.1, tabla 5 «Number of wait states according to CPU clock (HCLK) frequency».
#define FLASH_ESTADOS_DE_ESPERA 2U
```

- `FLASH_ESTADOS_DE_ESPERA 2U`: la FLASH tarda en entregar datos y a 84 MHz la CPU necesita esperar **2 ciclos** por lectura (RM0390, tabla 5: 2 estados de espera para 60 MHz < HCLK ≤ 90 MHz con VDD entre 2,7 y 3,6 V).

**Líneas 6 a 11**

```c
// Divisor M del PLL: 16 MHz de la HSI / 16 = 1 MHz, que es la entrada del VCO. Fuente: RM0390, sección 6.3.2 (RCC_PLLCFGR).
#define PLL_DIVISOR_ENTRADA_M 16U
// Multiplicador N del PLL: 1 MHz × 336 = 336 MHz en el VCO. Fuente: RM0390, sección 6.3.2 (RCC_PLLCFGR).
#define PLL_MULTIPLICADOR_N 336U
// Código del divisor P del PLL: 01 = dividir entre 4, 336 MHz / 4 = 84 MHz. Fuente: RM0390, sección 6.3.2 (00 = /2, 01 = /4, 10 = /6, 11 = /8).
#define PLL_CODIGO_DIVISOR_SALIDA_P 1U
```

La cuenta del PLL, con los números del código:

```
HSI 16 MHz ÷ M(16) = 1 MHz   ×  N(336) = 336 MHz (VCO)   ÷  P(4) = 84 MHz
```

- `PLL_DIVISOR_ENTRADA_M 16U`: divide la entrada del PLL (los 16 MHz del oscilador interno HSI) para dejar 1 MHz.
- `PLL_MULTIPLICADOR_N 336U`: el VCO (oscilador controlado por voltaje) multiplica por 336 y queda en 336 MHz.
- `PLL_CODIGO_DIVISOR_SALIDA_P 1U`: el campo P no guarda el divisor sino un **código** de 2 bits: `00` = ÷2, `01` = ÷4, `10` = ÷6, `11` = ÷8. Con `01` se divide entre 4: 336 / 4 = 84 MHz.

**Líneas 12 a 19**

```c
// Código HPRE = 0xxx: el AHB no se divide, HCLK = SYSCLK = 84 MHz. Fuente: RM0390, sección 6.3.3 (RCC_CFGR, HPRE).
#define AHB_SIN_DIVISION 0U
// Código PPRE1 = 100: el APB1 se divide entre 2, APB1 = 42 MHz (el máximo permitido es 45 MHz). Fuente: máximo de 45 MHz en RM0390, sección 6.2 «Clocks»; código del campo en la sección 6.3.3 (RCC_CFGR, PPRE1).
#define APB1_DIVIDIR_ENTRE_2 4U
// Código PPRE2 = 0xx: el APB2 no se divide, APB2 = 84 MHz (el máximo permitido es 90 MHz). Fuente: máximo de 90 MHz en RM0390, sección 6.2 «Clocks»; código del campo en la sección 6.3.3 (RCC_CFGR, PPRE2).
#define APB2_SIN_DIVISION 0U
// Código SW y SWS = 10: el PLL es la fuente del reloj del sistema. Fuente: RM0390, sección 6.3.3 (RCC_CFGR, SW y SWS).
#define RELOJ_SISTEMA_PLL 2U
```

Códigos de los divisores de los buses y de la fuente del reloj (también son códigos de campo, no divisores):
- `AHB_SIN_DIVISION 0U`: HPRE = `0xxx`: el bus AHB no se divide, HCLK = SYSCLK = 84 MHz.
- `APB1_DIVIDIR_ENTRE_2 4U`: PPRE1 = `100`: el bus APB1 se divide entre 2 → **42 MHz** (su máximo permitido es 45 MHz; por eso hay que dividirlo, a 84 MHz se pasaría).
- `APB2_SIN_DIVISION 0U`: PPRE2 = `0xx`: sin división → 84 MHz (máximo permitido 90 MHz).
- `RELOJ_SISTEMA_PLL 2U`: SW/SWS = `10`: el reloj del sistema sale del PLL (`00` = HSI, `01` = HSE).

**Líneas 21 a 23**

```c
// Cuenta milisegundos desde el arranque. Es volatile porque la interrupción la cambia sin que main lo sepa.
// Es static porque solo este archivo la usa.
static volatile uint32_t contador_milisegundos = 0U;
```

- `static volatile uint32_t contador_milisegundos = 0U;` es una variable global que cuenta los milisegundos desde el arranque.
  - `volatile`: la **interrupción** la cambia sin que `main` lo "vea" en el flujo normal del programa; sin `volatile`, el compilador podría leerla una sola vez dentro de un bucle de espera y quedarse esperando para siempre.
  - `static`: solo este archivo puede usarla (es privada del módulo); los demás usan funciones.
  - Tiene valor inicial `0U`, pero como el valor es cero, va a `.bss` y `crt0.S` la pone en 0.

**Líneas 25 a 27**

```c
// Pone el reloj del sistema en 84 MHz usando el PLL (el HSI de 16 MHz es la entrada).
void configurar_reloj(void)
{
```

- `void configurar_reloj(void) {` empieza la función que cambia el reloj. **El orden de los pasos importa**; cada paso tiene su razón.

**Líneas 28 a 32**

```c
    // Se escribe solo el campo LATENCY: la máscara va entre paréntesis en su definición para que ~ afecte solo a esos bits, y no se sobrescribe FLASH->ACR completo.
    // Primero la latencia de la FLASH, porque la FLASH es más lenta que 84 MHz y debe esperar más ciclos antes de subir la frecuencia.
    FLASH->ACR = (FLASH->ACR & ~FLASH_ACR_LATENCY_MASCARA) | (FLASH_ESTADOS_DE_ESPERA << FLASH_ACR_LATENCY_POSICION);
    // El manual (RM0390, sección 3.4.1) recomienda releer LATENCY y esperar a que quede escrito antes de cambiar el reloj.
    while (((FLASH->ACR & FLASH_ACR_LATENCY_MASCARA) >> FLASH_ACR_LATENCY_POSICION) != FLASH_ESTADOS_DE_ESPERA) { }
```

**Paso 1: latencia de la FLASH.**
- Línea 30: `FLASH->ACR = (FLASH->ACR & ~FLASH_ACR_LATENCY_MASCARA) | (FLASH_ESTADOS_DE_ESPERA << FLASH_ACR_LATENCY_POSICION);` es el mismo patrón "borrar el campo y escribir el valor" de `configurar_pin`, ahora sobre el campo `LATENCY` (bits 3:0 de `FLASH_ACR`). Solo se modifica ese campo, no el registro entero.
- **Por qué va primero:** la FLASH es más lenta que 84 MHz. Si se subiera la frecuencia antes de añadir los estados de espera, la CPU leería instrucciones antes de que la FLASH las entregue y el programa fallaría.
- Línea 32: `while (...) { }` es una espera activa: relee `LATENCY` hasta que el valor escrito se refleje. El manual recomienda comprobarlo antes de cambiar el reloj. `{ }` vacío = no hace nada mientras espera.

**Líneas 33 a 41**

```c

    // PLLSRC queda en 0 (HSI de 16 MHz, valor tras el reset). PLLQ y PLLR no se tocan y conservan su valor de reset.
    // El PLL está apagado, por eso se puede escribir PLLCFGR. Solo se escriben los campos PLLM, PLLN y PLLP, no el registro completo.
    // Campo PLLM: divisor de entrada del PLL.
    RCC->PLLCFGR = (RCC->PLLCFGR & ~RCC_PLLCFGR_PLLM_MASCARA) | (PLL_DIVISOR_ENTRADA_M << RCC_PLLCFGR_PLLM_POSICION);
    // Campo PLLN: multiplicador del VCO.
    RCC->PLLCFGR = (RCC->PLLCFGR & ~RCC_PLLCFGR_PLLN_MASCARA) | (PLL_MULTIPLICADOR_N << RCC_PLLCFGR_PLLN_POSICION);
    // Campo PLLP: divisor de salida del PLL que da el reloj del sistema.
    RCC->PLLCFGR = (RCC->PLLCFGR & ~RCC_PLLCFGR_PLLP_MASCARA) | (PLL_CODIGO_DIVISOR_SALIDA_P << RCC_PLLCFGR_PLLP_POSICION);
```

**Paso 2: configurar el PLL (mientras está apagado).**
- El PLL se puede configurar solo cuando está apagado, y lo está tras el reset. La fuente (`PLLSRC`) queda en HSI (valor de reset), y `PLLQ`/`PLLR` no se tocan.
- Líneas 37, 39 y 41: escriben, uno por uno, los campos `PLLM`, `PLLN` y `PLLP` de `RCC->PLLCFGR` con el mismo patrón de máscara. Se escriben campos separados para no sobrescribir los demás bits del registro.

**Líneas 42 a 49**

```c

    // Divisores de los buses, antes de subir la frecuencia para que ningún bus pase de su máximo.
    // Campo HPRE: divisor del AHB.
    RCC->CFGR = (RCC->CFGR & ~RCC_CFGR_HPRE_MASCARA) | (AHB_SIN_DIVISION << RCC_CFGR_HPRE_POSICION);
    // Campo PPRE1: divisor del APB1 (42 MHz; TIM3 recibirá 84 MHz).
    RCC->CFGR = (RCC->CFGR & ~RCC_CFGR_PPRE1_MASCARA) | (APB1_DIVIDIR_ENTRE_2 << RCC_CFGR_PPRE1_POSICION);
    // Campo PPRE2: divisor del APB2.
    RCC->CFGR = (RCC->CFGR & ~RCC_CFGR_PPRE2_MASCARA) | (APB2_SIN_DIVISION << RCC_CFGR_PPRE2_POSICION);
```

**Paso 3: divisores de los buses (antes de subir la frecuencia).**
- Se escriben `HPRE` (AHB), `PPRE1` (APB1) y `PPRE2` (APB2) en `RCC->CFGR`.
- **Por qué antes del cambio de reloj:** en el momento en que el reloj pasa a 84 MHz, ningún bus puede estar por encima de su máximo; si el APB1 se dejara sin dividir, trabajaría a 84 MHz, más de su límite de 45 MHz.
- El comentario de la línea 46 anticipa un dato que se usa en la prueba 05: aunque el APB1 trabaja a 42 MHz, los **timers** del APB1 (como TIM3) reciben el **doble** (84 MHz) cuando el divisor del bus no es 1.

**Líneas 50 a 54**

```c

    // Se enciende el PLL con |= para no cambiar los demás bits de CR.
    RCC->CR |= RCC_CR_PLLON;
    // Se espera a que el PLL enganche: PLLRDY = 1 indica que el PLL está listo.
    while ((RCC->CR & RCC_CR_PLLRDY) == 0U) { }
```

**Paso 4: encender el PLL y esperar.**
- `RCC->CR |= RCC_CR_PLLON;` pone en 1 el bit `PLLON` (con `|=`, sin tocar los demás bits de `CR`).
- `while ((RCC->CR & RCC_CR_PLLRDY) == 0U) { }` espera a que el bit `PLLRDY` sea 1: el PLL necesita un tiempo para "enganchar" (estabilizarse) y no se puede usar hasta entonces.

**Líneas 55 a 60**

```c

    // Campo SW: se elige el PLL como fuente del reloj del sistema.
    RCC->CFGR = (RCC->CFGR & ~RCC_CFGR_SW_MASCARA) | (RELOJ_SISTEMA_PLL << RCC_CFGR_SW_POSICION);
    // Se espera a que el hardware confirme el cambio: SWS muestra la fuente que está usando de verdad.
    while ((RCC->CFGR & RCC_CFGR_SWS_MASCARA) != (RELOJ_SISTEMA_PLL << RCC_CFGR_SWS_POSICION)) { }
}
```

**Paso 5: cambiar la fuente del reloj del sistema al PLL.**
- `SW` elige la fuente (`10` = PLL).
- `SWS` es el bit de **estado**: indica qué fuente está usando el hardware *de verdad*. El `while` espera a que `SWS` coincida con lo pedido, para no seguir ejecutando hasta que el cambio sea efectivo. Desde aquí el chip corre a **84 MHz**.

**Líneas 62 a 64**

```c
// Configura SysTick para que interrumpa cada 1 ms.
void iniciar_systick(void)
{
```

- `void iniciar_systick(void) {` configura el contador SysTick. Es parte del **núcleo** Cortex-M4 (no del fabricante), y por eso su dirección (`0xE000E010`) está fuera de los periféricos del STM32.

**Líneas 65 a 66**

```c
    // Se apaga el contador mientras se configura: ENABLE = 0 detiene la cuenta.
    SysTick->CTRL &= ~SYSTICK_CTRL_ENABLE;
```

- `SysTick->CTRL &= ~SYSTICK_CTRL_ENABLE;` apaga el contador (`ENABLE` = 0) para configurarlo sin que cuente a medias.

**Líneas 67 a 69**

```c
    // 84 000 000 / 1000 = 84 000 ciclos por milisegundo. El contador cuenta desde LOAD hasta 0, o sea LOAD + 1 ciclos, por eso se resta 1.
    // LOAD = 83 999: cabe en los 24 bits (máximo 16 777 215).
    SysTick->LOAD = (FRECUENCIA_RELOJ_HZ / INTERRUPCIONES_SYSTICK_POR_SEGUNDO) - 1U;
```

- `SysTick->LOAD = (84000000 / 1000) - 1;` = 83 999.
  - 84 000 000 ciclos/s ÷ 1000 = 84 000 ciclos por milisegundo.
  - El contador baja desde `LOAD` hasta 0, y eso son `LOAD + 1` ciclos; por eso se resta 1: 83 999 → 84 000 ciclos = 1 ms exacto.
  - Cabe en los 24 bits del registro (máximo 16 777 215).

**Líneas 70 a 71**

```c
    // Se pone el contador en 0 para que empiece desde LOAD en la primera cuenta.
    SysTick->VAL = 0U;
```

- `SysTick->VAL = 0U;` pone el contador actual en 0 (escribir cualquier valor lo borra), para que empiece limpio.

**Líneas 72 a 73**

```c
    // CLKSOURCE = 1: el contador usa el reloj del procesador (84 MHz), no AHB/8.
    SysTick->CTRL |= SYSTICK_CTRL_CLKSOURCE;
```

- `CLKSOURCE = 1`: SysTick cuenta con el **reloj del procesador** (84 MHz). Con 0 usaría AHB/8 (10,5 MHz).

**Líneas 74 a 75**

```c
    // TICKINT = 1: al llegar a 0 se genera la interrupción. SysTick es una excepción del núcleo y no necesita habilitarse en el NVIC.
    SysTick->CTRL |= SYSTICK_CTRL_TICKINT;
```

- `TICKINT = 1`: al llegar el contador a 0 se genera una excepción (la interrupción de SysTick). Como es una excepción del núcleo, **no hay que habilitarla en el NVIC**.

**Líneas 76 a 78**

```c
    // ENABLE = 1: se enciende el contador al final, cuando ya está todo configurado.
    SysTick->CTRL |= SYSTICK_CTRL_ENABLE;
}
```

- `ENABLE = 1`: se enciende el contador **al final**, cuando todo lo demás ya está configurado. `}` cierra la función.

**Líneas 80 a 86**

```c
// El nombre es el de la tabla de vectores de crt0.S (posición 0x3C). Al definirla aquí reemplaza al alias débil que apunta a Default_Handler.
// Se ejecuta cada 1 ms.
void SysTick_Handler(void)
{
    // Suma 1 milisegundo al contador.
    contador_milisegundos++;
}
```

`SysTick_Handler` es el manejador de la interrupción de SysTick:
- Su **nombre es obligatorio**: coincide con el de la entrada `0x3C` de la tabla de vectores de `crt0.S`. Como allí es un alias débil de `Default_Handler`, al definir esta función aquí **la reemplaza**.
- Se ejecuta cada 1 ms. Hace una sola cosa: `contador_milisegundos++`. Debe ser **corta**: mientras se ejecuta, el programa principal está detenido.
- No necesita limpiar ninguna bandera: SysTick se rearma solo.

**Líneas 88 a 95**

```c
// Espera bloqueante: no sale hasta que pasen los milisegundos pedidos.
void esperar_milisegundos(uint32_t milisegundos)
{
    // Se guarda el instante en que empieza la espera.
    uint32_t instante_inicial = contador_milisegundos;
    // La resta funciona aunque el contador de 32 bits dé la vuelta. main espera aquí y la interrupción sigue contando.
    while ((contador_milisegundos - instante_inicial) < milisegundos) { }
}
```

`esperar_milisegundos(n)` es una espera **bloqueante**:
- `instante_inicial = contador_milisegundos;` guarda el "reloj" actual.
- `while ((contador_milisegundos - instante_inicial) < milisegundos) { }` repite hasta que hayan pasado `n` ms. Se usa la **diferencia** (no una comparación directa de instantes): con enteros sin signo de 32 bits, la resta da el resultado correcto aunque el contador dé la vuelta al llegar al máximo.
- Mientras `main` espera aquí, la interrupción de SysTick sigue actualizando `contador_milisegundos`; por eso el `while` termina.

### 3. `inc/registros_f446.h`: lo que se agrega respecto a la prueba 01

Solo se explican las líneas nuevas; el resto es idéntico a la prueba 01 (ver su README).

**Líneas 22 a 25**

```c
// Interfaz de la memoria FLASH (0x40023C00). Fuente: RM0390, sección 2.2.2, tabla 1, fila «Flash interface register».
#define FLASH_BASE (AHB1_BASE + 0x3C00U)
// Registros SysTick del núcleo Cortex-M4 (0xE000E010). Fuente: PM0214, sección «SysTick timer (STK)» (número de sección y tabla por verificar por Daniela); coincide con core_cm4.h de CMSIS de ARM.
#define SYSTICK_BASE (0xE000E010U)
```

- `FLASH_BASE = AHB1_BASE + 0x3C00` → `0x40023C00`: la interfaz de la FLASH (para configurar los estados de espera).
- `SYSTICK_BASE = 0xE000E010`: SysTick no es un periférico del STM32 sino del **núcleo ARM**, con dirección fija en la zona de periféricos del núcleo (manual PM0214). Los comentarios del archivo dejan constancia de que la sección exacta del manual quedó "por verificar".

**Líneas 83 a 88**

```c
// Solo se define ACR: los demás registros de la FLASH no se usan todavía.
typedef struct {
    // Desplazamiento 0x00. Control de acceso a la FLASH: estados de espera (LATENCY, bits 3:0). Fuente: RM0390, sección 3.8.1.
    volatile uint32_t ACR;
// Fin de la estructura: desde aquí se puede usar el tipo RegistrosFLASH.
} RegistrosFLASH;
```

- `RegistrosFLASH` solo declara `ACR`, porque es el único registro de la FLASH que se usa. Como `ACR` está en el desplazamiento 0x00, no hace falta rellenar nada antes. Su campo `LATENCY` (bits 3:0) son los estados de espera.

**Líneas 90 a 101**

```c
// Mapa de los registros de SysTick, mismo criterio que RegistrosGPIO.
typedef struct {
    // Desplazamiento 0x00. Control y estado: habilitar, interrupción y fuente de reloj (bits 0 a 2).
    volatile uint32_t CTRL;
    // Desplazamiento 0x04. Valor de recarga del contador, de 24 bits (bits 23:0).
    volatile uint32_t LOAD;
    // Desplazamiento 0x08. Valor actual del contador; escribir cualquier valor lo pone en 0.
    volatile uint32_t VAL;
    // Desplazamiento 0x0C. Calibración del contador. No se usa.
    volatile uint32_t CALIB;
// Fin de la estructura: desde aquí se puede usar el tipo RegistrosSysTick.
} RegistrosSysTick;
```

`RegistrosSysTick` tiene 4 registros de 32 bits:
- `CTRL` (0x00): bit 0 `ENABLE`, bit 1 `TICKINT`, bit 2 `CLKSOURCE`.
- `LOAD` (0x04): valor de recarga, de 24 bits.
- `VAL` (0x08): valor actual; escribirlo lo pone en 0.
- `CALIB` (0x0C): calibración (no se usa).

**Líneas 110 a 113**

```c
// Puntero a la interfaz de la FLASH (se usa para FLASH->ACR).
#define FLASH ((RegistrosFLASH *)FLASH_BASE)
// Puntero a los registros de SysTick (se usa para SysTick->CTRL, LOAD y VAL).
#define SysTick ((RegistrosSysTick *)SYSTICK_BASE)
```

- `FLASH` y `SysTick` son los punteros a esos dos bloques de registros, definidos igual que `GPIOA` y `RCC`. Así el código dice `FLASH->ACR` y `SysTick->CTRL`.

**Líneas 120 a 123**

```c
// Bit 24 de RCC_CR: 1 enciende el PLL. Fuente: RM0390, sección 6.3.1.
#define RCC_CR_PLLON (1U << 24)
// Bit 25 de RCC_CR: 1 indica que el PLL ya enganchó y está listo. Fuente: RM0390, sección 6.3.1.
#define RCC_CR_PLLRDY (1U << 25)
```

- `RCC_CR_PLLON (1U << 24)` y `RCC_CR_PLLRDY (1U << 25)`: bits de `RCC_CR` para encender el PLL y para saber que ya está listo.

**Líneas 125 a 136**

```c
// Posición del campo PLLM (divisor de entrada del PLL) en RCC_PLLCFGR, bits 5:0. Fuente: RM0390, sección 6.3.2.
#define RCC_PLLCFGR_PLLM_POSICION 0U
// Máscara de los 6 bits de PLLM, ya desplazada a su posición. Fuente: RM0390, sección 6.3.2.
#define RCC_PLLCFGR_PLLM_MASCARA (0x3FU << RCC_PLLCFGR_PLLM_POSICION)
// Posición del campo PLLN (multiplicador del VCO) en RCC_PLLCFGR, bits 14:6. Fuente: RM0390, sección 6.3.2.
#define RCC_PLLCFGR_PLLN_POSICION 6U
// Máscara de los 9 bits de PLLN, ya desplazada a su posición. Fuente: RM0390, sección 6.3.2.
#define RCC_PLLCFGR_PLLN_MASCARA (0x1FFU << RCC_PLLCFGR_PLLN_POSICION)
// Posición del campo PLLP (divisor de salida del PLL) en RCC_PLLCFGR, bits 17:16. Fuente: RM0390, sección 6.3.2.
#define RCC_PLLCFGR_PLLP_POSICION 16U
// Máscara de los 2 bits de PLLP, ya desplazada a su posición. Fuente: RM0390, sección 6.3.2.
#define RCC_PLLCFGR_PLLP_MASCARA (0x3U << RCC_PLLCFGR_PLLP_POSICION)
```

Posición y máscara de los campos de `RCC_PLLCFGR`:
- `PLLM` en los bits 5:0 (6 bits → máscara `0x3F`), `PLLN` en los bits 14:6 (9 bits → máscara `0x1FF`) y `PLLP` en los bits 17:16 (2 bits → máscara `0x3`).
- Cada **máscara** ya viene desplazada a su posición (`0x3FU << 0`, `0x1FFU << 6`, `0x3U << 16`) y entre **paréntesis**, para que `~MASCARA` afecte a toda la expresión.

**Líneas 138 a 157**

```c
// Posición del campo SW (fuente del reloj del sistema) en RCC_CFGR, bits 1:0. Fuente: RM0390, sección 6.3.3.
#define RCC_CFGR_SW_POSICION 0U
// Máscara de los 2 bits de SW, ya desplazada a su posición. Fuente: RM0390, sección 6.3.3.
#define RCC_CFGR_SW_MASCARA (0x3U << RCC_CFGR_SW_POSICION)
// Posición del campo SWS (fuente que el hardware está usando de verdad) en RCC_CFGR, bits 3:2. Fuente: RM0390, sección 6.3.3.
#define RCC_CFGR_SWS_POSICION 2U
// Máscara de los 2 bits de SWS, ya desplazada a su posición. Fuente: RM0390, sección 6.3.3.
#define RCC_CFGR_SWS_MASCARA (0x3U << RCC_CFGR_SWS_POSICION)
// Posición del campo HPRE (divisor del AHB) en RCC_CFGR, bits 7:4. Fuente: RM0390, sección 6.3.3.
#define RCC_CFGR_HPRE_POSICION 4U
// Máscara de los 4 bits de HPRE, ya desplazada a su posición. Fuente: RM0390, sección 6.3.3.
#define RCC_CFGR_HPRE_MASCARA (0xFU << RCC_CFGR_HPRE_POSICION)
// Posición del campo PPRE1 (divisor del APB1) en RCC_CFGR, bits 12:10. Fuente: RM0390, sección 6.3.3.
#define RCC_CFGR_PPRE1_POSICION 10U
// Máscara de los 3 bits de PPRE1, ya desplazada a su posición. Fuente: RM0390, sección 6.3.3.
#define RCC_CFGR_PPRE1_MASCARA (0x7U << RCC_CFGR_PPRE1_POSICION)
// Posición del campo PPRE2 (divisor del APB2) en RCC_CFGR, bits 15:13. Fuente: RM0390, sección 6.3.3.
#define RCC_CFGR_PPRE2_POSICION 13U
// Máscara de los 3 bits de PPRE2, ya desplazada a su posición. Fuente: RM0390, sección 6.3.3.
#define RCC_CFGR_PPRE2_MASCARA (0x7U << RCC_CFGR_PPRE2_POSICION)
```

Posición y máscara de los campos de `RCC_CFGR`:
- `SW` (bits 1:0) y `SWS` (bits 3:2): fuente de reloj pedida y fuente en uso.
- `HPRE` (bits 7:4, 4 bits → `0xF`): divisor del AHB.
- `PPRE1` (bits 12:10) y `PPRE2` (bits 15:13), 3 bits cada uno (`0x7`): divisores del APB1 y del APB2.

**Líneas 159 a 162**

```c
// Posición del campo LATENCY (estados de espera de la FLASH) en FLASH_ACR, bits 3:0. Fuente: RM0390, sección 3.8.1.
#define FLASH_ACR_LATENCY_POSICION 0U
// Máscara de los 4 bits de LATENCY, ya desplazada a su posición. Fuente: RM0390, sección 3.8.1.
#define FLASH_ACR_LATENCY_MASCARA (0xFU << FLASH_ACR_LATENCY_POSICION)
```

- `FLASH_ACR_LATENCY`: campo de 4 bits en la posición 0 de `FLASH_ACR` (máscara `0xF`).

**Líneas 164 a 169**

```c
// Bit 0 de SysTick CTRL: 1 enciende el contador. Fuente: PM0214, sección SysTick (por verificar por Daniela).
#define SYSTICK_CTRL_ENABLE (1U << 0)
// Bit 1 de SysTick CTRL: 1 genera la interrupción al llegar el contador a 0. Fuente: PM0214, sección SysTick (por verificar por Daniela).
#define SYSTICK_CTRL_TICKINT (1U << 1)
// Bit 2 de SysTick CTRL: 1 usa el reloj del procesador, 0 usa AHB/8. Fuente: PM0214, sección SysTick (por verificar por Daniela).
#define SYSTICK_CTRL_CLKSOURCE (1U << 2)
```

Bits de `SysTick->CTRL`: `ENABLE` (bit 0), `TICKINT` (bit 1) y `CLKSOURCE` (bit 2).

### 4. `main.c`: el programa

**Líneas 1 a 6**

```c
// Se incluyen las definiciones de los registros del microcontrolador.
#include "registros_f446.h"
// Se incluye el módulo de configuración de pines (GPIO).
#include "gpio_config.h"
// Se incluye la configuración del reloj y del temporizador SysTick.
#include "system_config.h"
```

- Incluye registros, módulo de pines y, nuevo, `system_config.h` para usar `configurar_reloj`, `iniciar_systick` y `esperar_milisegundos`.

**Líneas 8 a 9**

```c
// Número del pin del LED de la placa (PA5).
#define PIN_LED 5U
```

- `PIN_LED 5U`: el LED sigue en PA5. Ya no hay botón en esta prueba.

**Líneas 11 a 13**

```c
// Función principal: crt0.S la llama cuando termina de preparar la RAM.
int main(void)
{
```

- `int main(void)`: punto de entrada llamado desde `crt0.S`.

**Líneas 14 a 17**

```c
    // Primero el reloj, antes de usar cualquier periférico: deja el sistema a 84 MHz.
    configurar_reloj();
    // Se enciende la base de tiempo de 1 ms (SysTick).
    iniciar_systick();
```

- `configurar_reloj();` **va primero**, antes de usar cualquier periférico: deja el sistema a 84 MHz.
- `iniciar_systick();` enciende la base de tiempo de 1 ms que necesita `esperar_milisegundos`.

**Líneas 19 a 32**

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

- Configura el LED igual que en la prueba 01: salida, sin resistencia, velocidad baja, sin función alterna, en el puerto A.

**Líneas 34 a 41**

```c
    // Bucle infinito: un microcontrolador no termina, repite esto mientras tenga energía.
    while (1) {
        // Se invierte el LED y se espera 500 ms: 500 ms encendido y 500 ms apagado = 1 Hz.
        invertir_pin(GPIOA, PIN_LED);
        // Se espera 500 ms.
        esperar_milisegundos(500U);
    }
}
```

- `while (1)`: bucle infinito.
- `invertir_pin(GPIOA, PIN_LED);` cambia el LED (si estaba apagado, enciende; y al revés).
- `esperar_milisegundos(500U);` espera 500 ms.
- Un ciclo completo = 500 ms encendido + 500 ms apagado = **1 s** → frecuencia de **1 Hz**.

