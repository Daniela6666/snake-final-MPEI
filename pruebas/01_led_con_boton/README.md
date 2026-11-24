# Prueba 01: LED con el botón azul

**Qué hace en la placa:** el LED de la placa (PA5) se enciende mientras mantienes presionado el botón azul (PC13) y se apaga al soltarlo.

**Para qué sirve esta prueba:** es el programa más pequeño que comprueba que *toda la cadena funciona*: el compilador, el linker, el arranque (`crt0.S`), los registros escritos a mano y la grabación con OpenOCD. Si el LED responde al botón, el chip arranca, el reloj de los puertos se enciende y la configuración de pines funciona.

**Cómo compilar y grabar** (desde esta carpeta):

```bash
make          # compila y muestra cuánta FLASH y RAM usa
make flash    # graba la placa por el ST-LINK con OpenOCD
make clean    # borra los archivos generados
```

**Cómo leer este documento:** cada bloque muestra el código real del archivo, con sus números de línea, y debajo explica qué hace, por qué se hace así y qué significa. Los archivos van en el orden en que trabaja el programa: primero lo que construye el programa (`Makefile`, `linker_script.ld`), luego lo que corre primero al encender (`crt0.S`), luego los registros y el módulo de pines, y al final `main.c`.

> El `Makefile`, el `linker_script.ld` y el `crt0.S` son **idénticos en las 9 pruebas**. Se explican aquí una sola vez; los README de las otras carpetas solo explican lo que cambia.

**Cómo se conectan los archivos:**

```
main.c  ──usa──▶  gpio_config.h/.c  ──usa──▶  registros_f446.h
   │                                              (direcciones de los registros)
   └─ arranca desde ─▶ crt0.S (Reset_Handler) ─▶ llama a main()
```

### 1. `Makefile`: cómo se compila

**Líneas 1 a 2**

```make
# Nombre del programa: se genera snake.elf.
APPNAME = snake
```

- `APPNAME = snake` crea una variable de make con el nombre del programa. El archivo final se llama `snake.elf`. Tener el nombre en una variable permite cambiarlo en un solo lugar (se usa en las reglas `$(APPNAME).elf` y `flash`).

**Líneas 4 a 5**

```make
# Compilador cruzado: corre en el PC pero genera código para el Cortex-M4 (arm-none-eabi = ARM sin sistema operativo).
CC = arm-none-eabi-gcc
```

- `CC = arm-none-eabi-gcc` es el compilador. Es un *compilador cruzado*: corre en tu PC pero genera instrucciones para el procesador ARM Cortex-M4 de la placa. `arm-none-eabi` significa "ARM, sin sistema operativo (none), formato EABI para sistemas embebidos".

**Líneas 7 a 16**

```make
# Opciones de compilación (CFLAGS). -Wall -Wextra: muestra todas las advertencias útiles.
# -ffreestanding: no hay sistema operativo ni biblioteca estándar completa (el programa es «independiente»).
CFLAGS = -Wall -Wextra -ffreestanding
# -mcpu=cortex-m4 -mthumb: genera instrucciones del Cortex-M4 en modo Thumb (el único que ejecutan los Cortex-M).
# -mfloat-abi=soft: los decimales se calculan por software (no se usa la unidad de punto flotante).
CFLAGS += -mcpu=cortex-m4 -mthumb -mfloat-abi=soft
# -O0: sin optimización, para que el código ejecutado se parezca al escrito. -g: guarda información para depurar.
CFLAGS += -O0 -g
# -Iinc: busca los archivos .h en la carpeta inc/.
CFLAGS += -Iinc
```

- Línea 9, `CFLAGS = -Wall -Wextra -ffreestanding`:
  - `-Wall -Wextra` activan casi todas las advertencias del compilador (variables sin usar, comparaciones raras, etc.). Ayudan a detectar errores antes de grabar.
  - `-ffreestanding` le dice a GCC que el programa **no corre sobre un sistema operativo ni usa la librería estándar de C**. Sin esto, GCC asume cosas que aquí no existen (por ejemplo, que `main` es llamada por el sistema o que existen `memcpy` y `printf`).
- Línea 12, `CFLAGS += ...`: `+=` agrega a la variable sin borrar lo anterior.
  - `-mcpu=cortex-m4` genera código para el núcleo del STM32F446.
  - `-mthumb` usa el conjunto de instrucciones Thumb (los Cortex-M **solo** ejecutan Thumb; sin esto no correría).
  - `-mfloat-abi=soft` hace que los cálculos con decimales (si los hubiera) se hagan por software y no con la unidad de punto flotante. El proyecto no usa decimales, y esto coincide con `.fpu softvfp` de `crt0.S`.
- Línea 14, `-O0 -g`: `-O0` desactiva las optimizaciones (el código ejecutado es el que escribiste, línea por línea), y `-g` incluye información de depuración. La consecuencia es que el programa es más lento que uno optimizado.
- Línea 16, `-Iinc` le dice al compilador que busque los archivos `.h` en la carpeta `inc/`, para escribir `#include "gpio_config.h"` sin ruta.

**Líneas 18 a 19**

```make
# Opciones del linker: -Tlinker_script.ld usa nuestro mapa de memoria; -nostdlib no enlaza las bibliotecas estándar.
LDFLAGS = -Tlinker_script.ld -nostdlib
```

- `LDFLAGS = -Tlinker_script.ld -nostdlib` son las opciones del *linker* (el programa que une los `.o`). `-T` indica qué linker script usar (el mapa de memoria propio). `-nostdlib` evita enlazar la librería estándar y el arranque que trae el compilador, porque el arranque lo escribimos nosotros en `crt0.S`.

**Líneas 21 a 26**

```make
# Archivos C: main.c y todos los .c de la carpeta src/ ($(wildcard ...) expande el patrón).
C_SRC = main.c $(wildcard src/*.c)
# Archivo en ensamblador: el arranque.
ASM_SRC = crt0.S
# Archivos objeto (.o): cada .c y cada .S cambiando su extensión por .o.
OBJS = $(C_SRC:.c=.o) $(ASM_SRC:.S=.o)
```

- Línea 22: `main.c` más todos los `.c` que haya en `src/` (`$(wildcard src/*.c)` expande a la lista de archivos). Por eso, al agregar un `.c` a `src/`, se compila solo.
- Línea 24: `crt0.S` es el único archivo en ensamblador.
- Línea 26: `OBJS` es la lista de archivos objeto. `$(C_SRC:.c=.o)` cambia la terminación `.c` por `.o` en cada nombre; `$(ASM_SRC:.S=.o)` hace lo mismo con `.S`. Así `main.c` pasa a `main.o`, `src/gpio_config.c` a `src/gpio_config.o` y `crt0.S` a `crt0.o`.

**Líneas 28 a 29**

```make
# Objetivo por defecto («make» solo): construir snake.elf.
all: $(APPNAME).elf
```

- `all: $(APPNAME).elf` es el objetivo por defecto: al escribir solo `make`, se construye `snake.elf`.

**Líneas 31 a 35**

```make
# Regla del ejecutable. Línea 1 de la receta: el linker une todos los .o en un solo .elf ($@ = el nombre del objetivo).
# Línea 2: arm-none-eabi-size muestra cuánta FLASH (text, data) y RAM (bss) ocupa el programa.
$(APPNAME).elf: $(OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS) $(OBJS) -o $@
	arm-none-eabi-size $@
```

- Línea 33: `snake.elf` depende de todos los `.o`; si alguno cambia, se vuelve a enlazar.
- Línea 34 (la línea de la receta empieza con un **tabulador**, no con espacios; make lo exige): une todos los `.o` en `snake.elf`. `$@` significa "el objetivo de esta regla" (`snake.elf`).
- Línea 35: `arm-none-eabi-size` imprime cuánta memoria usa el programa (texto/FLASH, datos y `.bss`), útil para comprobar que cabe en los 512 KB de FLASH y los 128 KB de RAM.

**Líneas 37 a 43**

```make
# Regla patrón: cada .o de ensamblador se construye a partir de su .S ($< = el archivo de entrada; -c = solo compilar, sin enlazar).
%.o: %.S
	$(CC) $(CFLAGS) -c $< -o $@

# Regla patrón: cada .o de C se construye a partir de su .c.
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@
```

- Líneas 38-39: regla genérica "para hacer cualquier `X.o` a partir de `X.S`": `$(CC) $(CFLAGS) -c $< -o $@`. `-c` compila **sin enlazar**; `$<` es el primer requisito (el `.S`) y `$@` el resultado (el `.o`).
- Líneas 42-43: lo mismo para los `.c`.
- Importante: las reglas dependen solo del `.c`/`.S`, **no de los `.h`**. Si cambias un `.h` y haces `make`, puede que no recompile los `.c` que lo usan; en ese caso haz `make clean` primero.

**Líneas 45 a 48**

```make
# «clean» no es un archivo sino una acción (.PHONY): «make clean» borra los objetos y el .elf para empezar de cero.
.PHONY: clean
clean:
	rm -f *.o src/*.o *.elf
```

- `.PHONY: clean` marca `clean` como un objetivo que no es un archivo (para que funcione aunque exista un archivo llamado `clean`).
- `rm -f *.o src/*.o *.elf` borra los objetos y el `.elf`. `-f` evita error si no existen.

**Líneas 50 a 54**

```make
# «flash» también es una acción: construye el .elf si hace falta y lo graba en la placa con OpenOCD por el ST-LINK
# (program = grabar, verify = comprobar lo grabado, reset = reiniciar el microcontrolador, exit = cerrar OpenOCD).
.PHONY: flash
flash: $(APPNAME).elf
	openocd -f interface/stlink.cfg -f target/stm32f4x.cfg -c "program $(APPNAME).elf verify reset exit"
```

- `flash` primero construye el `.elf` (por la dependencia) y luego llama a OpenOCD, el programa que habla con el ST-LINK de la placa.
  - `-f interface/stlink.cfg`: usa el programador ST-LINK.
  - `-f target/stm32f4x.cfg`: el chip es de la familia STM32F4.
  - `-c "program snake.elf verify reset exit"`: graba el archivo (`program`), comprueba que quedó igual (`verify`), reinicia el chip para que arranque (`reset`) y cierra OpenOCD (`exit`).

### 2. `linker_script.ld`: el mapa de memoria

**Líneas 1 a 2**

```text
/* Primera instruccion que ejecuta el programa: el manejador de reset (definido en crt0.S) */
ENTRY(Reset_Handler)
```

- `ENTRY(Reset_Handler)` marca el punto de entrada del programa: la etiqueta `Reset_Handler` (definida en `crt0.S`). Es lo primero que se ejecuta tras un reset.

**Líneas 4 a 11**

```text
/* Mapa de memoria del STM32F446RE (RM0390) */
MEMORY
{
    /* Memoria flash: aqui se guarda el programa. Se lee y se ejecuta, no se escribe en ejecucion */
    FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 512K
    /* SRAM1 (112 KB) + SRAM2 (16 KB), contiguas: variables y pila */
    RAM (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}
```

- `MEMORY { ... }` declara las dos regiones físicas del chip (STM32F446RE, RM0390):
  - `FLASH (rx)`: empieza en `0x08000000`, mide 512 KB. `rx` = se puede leer y ejecutar (no escribir en ejecución). Aquí se guarda el programa.
  - `RAM (rwx)`: empieza en `0x20000000`, mide 128 KB (SRAM1 de 112 KB + SRAM2 de 16 KB, contiguas). `rwx` = leer, escribir, ejecutar. Aquí van variables y pila.

**Líneas 13 a 14**

```text
/* Valor inicial del puntero de pila: el final de la RAM (0x20020000). La pila crece hacia abajo */
_estack = ORIGIN(RAM) + LENGTH(RAM);
```

- `_estack = ORIGIN(RAM) + LENGTH(RAM);` define un símbolo con el valor `0x20020000` (final de la RAM). Es el valor inicial del puntero de pila: la pila crece **hacia abajo**, así que arranca en el extremo alto. `crt0.S` y la tabla de vectores usan `_estack`.

**Líneas 16 a 17**

```text
SECTIONS   /* aquí empieza la lista de secciones: dónde se coloca cada parte del programa */
{
```

- `SECTIONS { ... }` indica en qué región va cada tipo de contenido del programa.

**Líneas 18 a 23**

```text
    /* Codigo: primero la tabla de vectores (queda en 0x08000000) y despues las funciones */
    .text :
    {
        *(.isr_vector)
        *(.text*)
    } > FLASH   /* esta sección se guarda en la FLASH */
```

- `.text` contiene el código. `*(.isr_vector)` va **primero**: la tabla de vectores tiene que quedar en `0x08000000`, porque el procesador la lee de ahí al reiniciar (el primer dato es el valor inicial del SP y el segundo, la dirección de `Reset_Handler`). Después `*(.text*)` pone todas las funciones. `> FLASH` lo ubica en la FLASH.

**Líneas 25 a 31**

```text
    /* Constantes (const, textos): solo lectura, en flash */
    .rodata :
    {
        *(.rodata*)
        /* Alinear a 4 bytes para que el valor inicial de .data (en flash) empiece en direccion multiplo de 4 */
        . = ALIGN(4);
    } > FLASH   /* también en la FLASH */
```

- `.rodata` guarda constantes (variables `const`, textos). Quedan en la FLASH: no gastan RAM. (La fuente de dígitos de la prueba 06 es un caso.)
- `. = ALIGN(4);` ajusta la posición actual a un múltiplo de 4. Es necesario porque lo que sigue (el valor inicial de `.data`) se copia de 4 en 4 bytes.

**Líneas 33 a 34**

```text
    /* Direccion en flash donde esta guardado el valor inicial de .data */
    _sidata = LOADADDR(.data);
```

- `_sidata = LOADADDR(.data);` crea el símbolo `_sidata` con la dirección **en FLASH** donde está guardado el valor inicial de `.data`. `crt0.S` copia desde ahí.

**Líneas 36 a 44**

```text
    /* Variables globales con valor inicial: viven en RAM, pero su valor inicial se guarda en flash */
    .data :
    {
        _sdata = .;   /* _sdata: dirección en RAM donde empieza .data (el contador de posición «.» es la dirección actual) */
        *(.data*)
        /* Alinear a 4 bytes: crt0.S copia de 4 en 4 bytes hasta _edata */
        . = ALIGN(4);
        _edata = .;   /* _edata: dirección en RAM donde termina .data */
    } > RAM AT> FLASH   /* vive en RAM (> RAM) pero su valor inicial se guarda en FLASH (AT> FLASH) */
```

- `.data` son las variables globales **con valor inicial** (por ejemplo `int x = 5;`).
- `_sdata` y `_edata` marcan dónde empiezan y terminan en RAM.
- `> RAM AT> FLASH` dice algo importante: la sección **vive en RAM** (donde se lee y escribe en ejecución) pero su **contenido inicial se guarda en FLASH**, porque la RAM se borra al apagar. Al arrancar, `crt0.S` copia de FLASH a RAM.
- `ALIGN(4)` por la misma razón que antes: `crt0.S` copia de 4 en 4.

**Líneas 46 a 55**

```text
    /* Variables globales sin valor inicial (valen 0): viven en RAM y no ocupan flash */
    .bss (NOLOAD) :
    {
        _sbss = .;   /* _sbss: dirección donde empieza .bss */
        *(.bss*)
        /* Alinear a 4 bytes: crt0.S borra de 4 en 4 bytes hasta _ebss */
        . = ALIGN(4);
        _ebss = .;   /* _ebss: dirección donde termina .bss */
    } > RAM   /* solo ocupa RAM */
}
```

- `.bss` son las globales **sin valor inicial** (valen 0 en C). `(NOLOAD)` indica que no ocupan espacio en la FLASH: no hay nada que guardar, solo reservar RAM y ponerla en 0 (lo hace `crt0.S` entre `_sbss` y `_ebss`).
- En pruebas posteriores, el `framebuffer` del panel vive aquí.

### 3. `crt0.S`: lo primero que se ejecuta

**Líneas 1 a 27**

```asm
/* adaptado de startup_stm32f401xe.s (ST) y del ejemplo 24-ADC-1 del profesor */
/**
  ******************************************************************************
  * @file      startup_stm32f401xe.s
  * @author    MCD Application Team
  * @brief     STM32F401xExx Devices vector table for GCC based toolchains. 
  *            This module performs:
  *                - Set the initial SP
  *                - Set the initial PC == Reset_Handler,
  *                - Set the vector table entries with the exceptions ISR address
  *                - Branches to main in the C library (which eventually
  *                  calls main()).
  *            After Reset the Cortex-M4 processor is in Thread mode,
  *            priority is Privileged, and the Stack is set to Main.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2017 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */

```

- Comentarios: el archivo está adaptado del arranque que da ST (`startup_stm32f401xe.s`) y del ejemplo 24 del profesor. El bloque `@file ... @attention` es el encabezado original de ST, con su licencia.

**Líneas 28 a 31**

```asm
  .syntax unified   /* sintaxis unificada de ARM (la misma para ARM y Thumb) */
  .cpu cortex-m4    /* instrucciones del Cortex-M4 */
  .fpu softvfp      /* sin FPU: coincide con -mfloat-abi=soft del Makefile */
  .thumb            /* el codigo es Thumb (los Cortex-M solo ejecutan Thumb) */
```

- `.syntax unified`: usa la sintaxis unificada de ARM (la misma para instrucciones ARM y Thumb).
- `.cpu cortex-m4`: genera instrucciones válidas para el Cortex-M4.
- `.fpu softvfp`: sin unidad de punto flotante; coincide con `-mfloat-abi=soft` del Makefile.
- `.thumb`: todo el código siguiente es Thumb (el único que ejecuta un Cortex-M).

**Líneas 32 a 35**

```asm

.global  g_pfnVectors    /* la tabla de vectores es visible para el linker */
.global  Default_Handler /* manejador por defecto */
.global  Reset_Handler   /* manejador de reset: ENTRY del linker script */
```

- `.global` hace visible un símbolo para el linker y otros archivos. `g_pfnVectors` (la tabla de vectores), `Default_Handler` y `Reset_Handler` (el `ENTRY` del linker script) deben ser globales.

**Líneas 36 a 44**

```asm

/**
 * Reset_Handler: es lo primero que se ejecuta despues de un reset.
 * Prepara la pila, copia .data de FLASH a RAM, pone .bss en cero
 * y llama a main().
*/
    .section  .text.Reset_Handler
  .type  Reset_Handler, %function
Reset_Handler:
```

- El comentario resume lo que hace `Reset_Handler`: prepara la pila, copia `.data`, pone `.bss` en cero y llama a `main()`.
- `.section .text.Reset_Handler` pone el código en su propia sección dentro de `.text`.
- `.type Reset_Handler, %function` le dice al ensamblador que es una función (necesario para que la dirección guardada en la tabla de vectores sea correcta en Thumb).
- `Reset_Handler:` es la etiqueta: la dirección a la que salta el procesador tras un reset.

**Líneas 45 a 46**

```asm
  /* Pila: SP = _estack (final de la RAM, 0x20020000; la pila crece hacia abajo) */
  ldr   sp, =_estack
```

- `ldr sp, =_estack` carga el valor de `_estack` (`0x20020000`) en el registro `sp` (puntero de pila). **Hay que hacerlo antes que cualquier otra cosa**, porque las llamadas a funciones guardan datos en la pila. El procesador ya carga el SP solo desde la entrada `0x00` de la tabla de vectores; repetirlo es la costumbre de los archivos de arranque de ST y del ejemplo del profesor.

**Líneas 47 a 53**

```asm

  /* Copiar el valor inicial de .data desde la FLASH (_sidata) hasta la RAM (_sdata a _edata) */
  ldr r0, =_sdata               /* r0 = direccion de inicio de .data en RAM */
  ldr r1, =_edata               /* r1 = direccion de fin de .data en RAM */
  ldr r2, =_sidata              /* r2 = direccion del valor inicial en FLASH */
  movs r3, #0                   /* r3 = desplazamiento en bytes, empieza en 0 */
  b LoopCopyDataInit            /* saltar a la condicion del bucle */
```

Copia del valor inicial de `.data` (de FLASH a RAM). Se usan registros como variables:
- `ldr r0, =_sdata`: r0 = dirección donde empieza `.data` en RAM (destino).
- `ldr r1, =_edata`: r1 = dirección donde termina `.data` en RAM (límite).
- `ldr r2, =_sidata`: r2 = dirección en FLASH del valor inicial (origen).
- `movs r3, #0`: r3 = cuántos bytes se han copiado (desplazamiento).
- `b LoopCopyDataInit`: salta directamente a **comprobar la condición**, para que, si `.data` está vacía, no se copie nada.

**Líneas 54 a 58**

```asm

CopyDataInit:
  ldr r4, [r2, r3]              /* leer una palabra (4 bytes) de la FLASH */
  str r4, [r0, r3]              /* escribirla en la RAM */
  adds r3, r3, #4               /* avanzar 4 bytes */
```

Cuerpo del bucle de copia:
- `ldr r4, [r2, r3]` lee una palabra de 4 bytes de la FLASH en la dirección `r2 + r3`.
- `str r4, [r0, r3]` la escribe en la RAM en la dirección `r0 + r3`.
- `adds r3, r3, #4` avanza 4 bytes.

**Líneas 59 a 63**

```asm

LoopCopyDataInit:
  adds r4, r0, r3               /* r4 = direccion actual en RAM */
  cmp r4, r1                    /* comparar con el fin de .data */
  bcc CopyDataInit              /* si todavia es menor, seguir copiando */
```

Condición del bucle:
- `adds r4, r0, r3`: r4 = dirección actual en RAM (inicio + copiados).
- `cmp r4, r1`: la compara con el final de `.data`.
- `bcc CopyDataInit`: *branch if carry clear*, es decir, "si r4 es menor que r1 (sin signo), vuelve a copiar". Cuando r4 llega a `_edata`, el bucle termina.

**Líneas 64 a 69**

```asm

  /* Poner en cero .bss (de _sbss a _ebss), porque en C las globales sin valor inicial valen 0 */
  ldr r2, =_sbss                /* r2 = direccion de inicio de .bss */
  ldr r4, =_ebss                /* r4 = direccion de fin de .bss */
  movs r3, #0                   /* r3 = valor cero */
  b LoopFillZerobss             /* saltar a la condicion del bucle */
```

Preparación para poner en cero `.bss` (en C las globales sin valor inicial valen 0, y la RAM al encender trae basura):
- r2 = `_sbss` (inicio), r4 = `_ebss` (fin), r3 = 0 (el valor que se escribirá).
- `b LoopFillZerobss` salta a la condición, de nuevo para el caso de `.bss` vacía.

**Líneas 70 a 73**

```asm

FillZerobss:
  str  r3, [r2]                 /* escribir un cero (4 bytes) */
  adds r2, r2, #4               /* avanzar 4 bytes */
```

- `str r3, [r2]` escribe un cero de 4 bytes en la dirección r2.
- `adds r2, r2, #4` avanza a la siguiente palabra.

**Líneas 74 a 77**

```asm

LoopFillZerobss:
  cmp r2, r4                    /* comparar con el fin de .bss */
  bcc FillZerobss               /* si todavia es menor, seguir borrando */
```

- `cmp r2, r4` compara la dirección actual con el fin de `.bss` y `bcc FillZerobss` repite mientras sea menor.

**Líneas 78 a 80**

```asm

  /* Llamar a main() */
  bl  main
```

- `bl main` es *branch with link*: salta a `main()` y guarda en `lr` la dirección de retorno. Ya están listas la pila, las variables con valor inicial y las variables en cero, así que el código en C puede ejecutarse con normalidad.

**Líneas 81 a 84**

```asm

  /* Si main retorna, quedarse en un bucle infinito */
  b .
  .size  Reset_Handler, .-Reset_Handler
```

- `b .` salta a sí misma: un bucle infinito. Solo se llegaría ahí si `main` retornara; así el procesador no ejecuta basura.
- `.size Reset_Handler, .-Reset_Handler` le informa al ensamblador/depurador el tamaño de la función (la posición actual menos el inicio).

**Líneas 85 a 94**

```asm

/**
 * Default_Handler: se ejecuta si llega una interrupcion que no tiene manejador.
 * Entra en un bucle infinito para poder examinar el sistema con el depurador.
*/
    .section  .text.Default_Handler,"ax",%progbits
Default_Handler:
Infinite_Loop:
  b  Infinite_Loop
  .size  Default_Handler, .-Default_Handler
```

- `Default_Handler` es el manejador de cualquier interrupción que no tenga uno propio. `Infinite_Loop: b Infinite_Loop` se queda en un bucle: si ocurre una interrupción que no esperabas, el programa se detiene ahí y con el depurador puedes ver que algo pasó (en vez de que el procesador siga ejecutando cosas al azar).
- `.section .text.Default_Handler,"ax",%progbits`: sección con permiso de ejecución (`a` asignable, `x` ejecutable) y con contenido real.

**Líneas 95 a 104**

```asm

/**
 * Tabla de vectores del STM32F446 (RM0390, seccion 10.1.3, tabla 38).
 * El linker la deja al inicio de la FLASH (0x08000000), que es donde el procesador la busca.
 * Cada entrada es una palabra de 4 bytes con la direccion del manejador (0 = reservado).
*/
   .section  .isr_vector,"a",%progbits
  .type  g_pfnVectors, %object

g_pfnVectors:
```

- El comentario explica la tabla: está en la sección `.isr_vector`, que el linker script coloca **al inicio de la FLASH** (`0x08000000`). El procesador la consulta cada vez que ocurre una excepción o interrupción: la entrada número *n* contiene la dirección de la función que debe ejecutar. `0` significa "reservado".
- `.section .isr_vector,"a",%progbits`: sección de solo lectura (`a`), con datos (`%progbits`).
- `.type g_pfnVectors, %object` la marca como dato (no función) y `g_pfnVectors:` es su etiqueta.

**Líneas 105 a 120**

```asm
  .word  _estack                          /* 0x00: valor inicial del puntero de pila (SP) */
  .word  Reset_Handler                    /* 0x04: Reset */
  .word  NMI_Handler                      /* 0x08: NMI (interrupcion no enmascarable) */
  .word  HardFault_Handler                /* 0x0C: HardFault (todas las clases de falla) */
  .word  MemManage_Handler                /* 0x10: MemManage (gestion de memoria) */
  .word  BusFault_Handler                 /* 0x14: BusFault (falla de bus) */
  .word  UsageFault_Handler               /* 0x18: UsageFault (instruccion indefinida o estado ilegal) */
  .word  0                                /* 0x1C: reservado */
  .word  0                                /* 0x20: reservado */
  .word  0                                /* 0x24: reservado */
  .word  0                                /* 0x28: reservado */
  .word  SVC_Handler                      /* 0x2C: SVCall (llamada al sistema) */
  .word  DebugMon_Handler                 /* 0x30: Debug Monitor */
  .word  0                                /* 0x34: reservado */
  .word  PendSV_Handler                   /* 0x38: PendSV */
  .word  SysTick_Handler                  /* 0x3C: SysTick (temporizador del sistema) */
```

Las 16 primeras entradas (excepciones del **núcleo**). Cada `.word` ocupa 4 bytes, por eso la posición de la entrada *n* es `4 × n`:
- `0x00 _estack`: **no es una dirección de función**, es el valor inicial del puntero de pila que el procesador carga solo al reiniciar.
- `0x04 Reset_Handler`: a dónde salta el procesador al reiniciar.
- `0x08 NMI`, `0x0C HardFault`, `0x10 MemManage`, `0x14 BusFault`, `0x18 UsageFault`: excepciones de error (interrupción no enmascarable y diferentes fallas). Si ocurre una falla (por ejemplo, acceder a una dirección inválida), el procesador salta aquí.
- `0x1C` a `0x28`: reservadas (`0`).
- `0x2C SVC`, `0x30 DebugMon`, `0x38 PendSV`: llamadas al sistema, monitor de depuración y servicio pendiente (no se usan aquí). `0x34` reservada.
- **`0x3C SysTick_Handler`**: la excepción del temporizador del sistema. Es la que usa la prueba 02 en adelante para contar milisegundos.

**Líneas 121 a 152**

```asm

  /* Interrupciones externas: IRQ 0 a 96 (la direccion en la tabla es 0x40 + 4 * numero de IRQ) */
  .word  WWDG_IRQHandler                  /* IRQ 0: Window Watchdog */
  .word  PVD_IRQHandler                   /* IRQ 1: PVD por la linea EXTI */
  .word  TAMP_STAMP_IRQHandler            /* IRQ 2: Tamper y TimeStamp por la linea EXTI */
  .word  RTC_WKUP_IRQHandler              /* IRQ 3: RTC Wakeup por la linea EXTI */
  .word  FLASH_IRQHandler                 /* IRQ 4: FLASH */
  .word  RCC_IRQHandler                   /* IRQ 5: RCC */
  .word  EXTI0_IRQHandler                 /* IRQ 6: EXTI linea 0 */
  .word  EXTI1_IRQHandler                 /* IRQ 7: EXTI linea 1 */
  .word  EXTI2_IRQHandler                 /* IRQ 8: EXTI linea 2 */
  .word  EXTI3_IRQHandler                 /* IRQ 9: EXTI linea 3 */
  .word  EXTI4_IRQHandler                 /* IRQ 10: EXTI linea 4 */
  .word  DMA1_Stream0_IRQHandler          /* IRQ 11: DMA1 stream 0 */
  .word  DMA1_Stream1_IRQHandler          /* IRQ 12: DMA1 stream 1 */
  .word  DMA1_Stream2_IRQHandler          /* IRQ 13: DMA1 stream 2 */
  .word  DMA1_Stream3_IRQHandler          /* IRQ 14: DMA1 stream 3 */
  .word  DMA1_Stream4_IRQHandler          /* IRQ 15: DMA1 stream 4 */
  .word  DMA1_Stream5_IRQHandler          /* IRQ 16: DMA1 stream 5 */
  .word  DMA1_Stream6_IRQHandler          /* IRQ 17: DMA1 stream 6 */
  .word  ADC_IRQHandler                   /* IRQ 18: ADC1, ADC2 y ADC3 */
  .word  CAN1_TX_IRQHandler               /* IRQ 19: CAN1 TX */
  .word  CAN1_RX0_IRQHandler              /* IRQ 20: CAN1 RX0 */
  .word  CAN1_RX1_IRQHandler              /* IRQ 21: CAN1 RX1 */
  .word  CAN1_SCE_IRQHandler              /* IRQ 22: CAN1 SCE */
  .word  EXTI9_5_IRQHandler               /* IRQ 23: EXTI lineas 9 a 5 */
  .word  TIM1_BRK_TIM9_IRQHandler         /* IRQ 24: TIM1 Break y TIM9 */
  .word  TIM1_UP_TIM10_IRQHandler         /* IRQ 25: TIM1 Update y TIM10 */
  .word  TIM1_TRG_COM_TIM11_IRQHandler    /* IRQ 26: TIM1 Trigger/Commutation y TIM11 */
  .word  TIM1_CC_IRQHandler               /* IRQ 27: TIM1 Capture Compare */
  .word  TIM2_IRQHandler                  /* IRQ 28: TIM2 */
  .word  TIM3_IRQHandler                  /* IRQ 29: TIM3 */
```

Entradas de las interrupciones de los **periféricos** (IRQ 0 a 29). La primera IRQ está en la posición `0x40`, así que la IRQ *n* está en `0x40 + 4n`. Cada una apunta a un manejador con nombre fijo (`WWDG_IRQHandler`, `EXTI0_IRQHandler`, `DMA1_Stream0_IRQHandler`, ...).
- La línea 152, **`TIM3_IRQHandler` (IRQ 29)**, es la que se usa desde la prueba 05 para refrescar el panel cada milisegundo. Su posición en la tabla es 16 + 29 = 45 (por eso `NUMERO_INTERRUPCION_TIM3` vale 29 en `registros_f446.h`).

**Líneas 153 a 183**

```asm
  .word  TIM4_IRQHandler                  /* IRQ 30: TIM4 */
  .word  I2C1_EV_IRQHandler               /* IRQ 31: I2C1 evento */
  .word  I2C1_ER_IRQHandler               /* IRQ 32: I2C1 error */
  .word  I2C2_EV_IRQHandler               /* IRQ 33: I2C2 evento */
  .word  I2C2_ER_IRQHandler               /* IRQ 34: I2C2 error */
  .word  SPI1_IRQHandler                  /* IRQ 35: SPI1 */
  .word  SPI2_IRQHandler                  /* IRQ 36: SPI2 */
  .word  USART1_IRQHandler                /* IRQ 37: USART1 */
  .word  USART2_IRQHandler                /* IRQ 38: USART2 */
  .word  USART3_IRQHandler                /* IRQ 39: USART3 */
  .word  EXTI15_10_IRQHandler             /* IRQ 40: EXTI lineas 15 a 10 */
  .word  RTC_Alarm_IRQHandler             /* IRQ 41: Alarmas A y B del RTC por la linea EXTI */
  .word  OTG_FS_WKUP_IRQHandler           /* IRQ 42: USB OTG FS Wakeup por la linea EXTI */
  .word  TIM8_BRK_TIM12_IRQHandler        /* IRQ 43: TIM8 Break y TIM12 */
  .word  TIM8_UP_TIM13_IRQHandler         /* IRQ 44: TIM8 Update y TIM13 */
  .word  TIM8_TRG_COM_TIM14_IRQHandler    /* IRQ 45: TIM8 Trigger/Commutation y TIM14 */
  .word  TIM8_CC_IRQHandler               /* IRQ 46: TIM8 Capture Compare */
  .word  DMA1_Stream7_IRQHandler          /* IRQ 47: DMA1 stream 7 */
  .word  FMC_IRQHandler                   /* IRQ 48: FMC */
  .word  SDIO_IRQHandler                  /* IRQ 49: SDIO */
  .word  TIM5_IRQHandler                  /* IRQ 50: TIM5 */
  .word  SPI3_IRQHandler                  /* IRQ 51: SPI3 */
  .word  UART4_IRQHandler                 /* IRQ 52: UART4 */
  .word  UART5_IRQHandler                 /* IRQ 53: UART5 */
  .word  TIM6_DAC_IRQHandler              /* IRQ 54: TIM6 y errores de underrun de DAC1 y DAC2 */
  .word  TIM7_IRQHandler                  /* IRQ 55: TIM7 */
  .word  DMA2_Stream0_IRQHandler          /* IRQ 56: DMA2 stream 0 */
  .word  DMA2_Stream1_IRQHandler          /* IRQ 57: DMA2 stream 1 */
  .word  DMA2_Stream2_IRQHandler          /* IRQ 58: DMA2 stream 2 */
  .word  DMA2_Stream3_IRQHandler          /* IRQ 59: DMA2 stream 3 */
  .word  DMA2_Stream4_IRQHandler          /* IRQ 60: DMA2 stream 4 */
```

IRQ 30 a 60: `TIM4`, I2C1 e I2C2, SPI1 y SPI2, `USART1` a `USART3`, EXTI15_10, alarmas del RTC, USB OTG, `TIM8`, `DMA1_Stream7`, `FMC`, `SDIO`, `TIM5`, `SPI3`, `UART4/5`, `TIM6_DAC`, `TIM7`, `DMA2_Stream0` a `4`. Ninguna se usa en este proyecto, pero deben estar en la tabla para que el orden sea el del manual.

**Líneas 184 a 219**

```asm
  .word  0                                /* IRQ 61: reservado */
  .word  0                                /* IRQ 62: reservado */
  .word  CAN2_TX_IRQHandler               /* IRQ 63: CAN2 TX */
  .word  CAN2_RX0_IRQHandler              /* IRQ 64: CAN2 RX0 */
  .word  CAN2_RX1_IRQHandler              /* IRQ 65: CAN2 RX1 */
  .word  CAN2_SCE_IRQHandler              /* IRQ 66: CAN2 SCE */
  .word  OTG_FS_IRQHandler                /* IRQ 67: USB OTG FS */
  .word  DMA2_Stream5_IRQHandler          /* IRQ 68: DMA2 stream 5 */
  .word  DMA2_Stream6_IRQHandler          /* IRQ 69: DMA2 stream 6 */
  .word  DMA2_Stream7_IRQHandler          /* IRQ 70: DMA2 stream 7 */
  .word  USART6_IRQHandler                /* IRQ 71: USART6 */
  .word  I2C3_EV_IRQHandler               /* IRQ 72: I2C3 evento */
  .word  I2C3_ER_IRQHandler               /* IRQ 73: I2C3 error */
  .word  OTG_HS_EP1_OUT_IRQHandler        /* IRQ 74: USB OTG HS endpoint 1 OUT */
  .word  OTG_HS_EP1_IN_IRQHandler         /* IRQ 75: USB OTG HS endpoint 1 IN */
  .word  OTG_HS_WKUP_IRQHandler           /* IRQ 76: USB OTG HS Wakeup por la linea EXTI */
  .word  OTG_HS_IRQHandler                /* IRQ 77: USB OTG HS */
  .word  DCMI_IRQHandler                  /* IRQ 78: DCMI */
  .word  0                                /* IRQ 79: reservado */
  .word  0                                /* IRQ 80: reservado */
  .word  FPU_IRQHandler                   /* IRQ 81: FPU */
  .word  0                                /* IRQ 82: reservado */
  .word  0                                /* IRQ 83: reservado */
  .word  SPI4_IRQHandler                  /* IRQ 84: SPI4 */
  .word  0                                /* IRQ 85: reservado */
  .word  0                                /* IRQ 86: reservado */
  .word  SAI1_IRQHandler                  /* IRQ 87: SAI1 */
  .word  0                                /* IRQ 88: reservado */
  .word  0                                /* IRQ 89: reservado */
  .word  0                                /* IRQ 90: reservado */
  .word  SAI2_IRQHandler                  /* IRQ 91: SAI2 */
  .word  QUADSPI_IRQHandler               /* IRQ 92: QuadSPI */
  .word  CEC_IRQHandler                   /* IRQ 93: HDMI-CEC */
  .word  SPDIFRX_IRQHandler               /* IRQ 94: SPDIF-Rx */
  .word  FMPI2C1_EV_IRQHandler            /* IRQ 95: FMPI2C1 evento */
  .word  FMPI2C1_ER_IRQHandler            /* IRQ 96: FMPI2C1 error */
```

IRQ 61 a 96: las IRQ 61 y 62 están reservadas (`.word 0`); después CAN2, USB OTG FS, `DMA2_Stream5` a `7`, `USART6`, I2C3, USB OTG HS, DCMI, FPU, SPI4, SAI1, SAI2, QuadSPI, HDMI-CEC, SPDIF-Rx y FMPI2C1. Los huecos con `.word 0` son IRQ que el chip no tiene. Las posiciones deben coincidir exactamente con la tabla 38 del RM0390; si se omitiera una entrada, todas las siguientes quedarían corridas y las interrupciones llamarían a la función equivocada.

**Líneas 220 a 221**

```asm

  .size  g_pfnVectors, .-g_pfnVectors
```

- `.size g_pfnVectors, .-g_pfnVectors` fija el tamaño de la tabla (97 + 16 palabras).

**Líneas 222 a 226**

```asm

/**
 * Alias debiles: cada manejador apunta a Default_Handler. Si en C se define una
 * funcion con el mismo nombre (por ejemplo TIM3_IRQHandler), esa funcion reemplaza al alias.
*/
```

- Comentario: cada manejador tiene un **alias débil** que apunta a `Default_Handler`. Si en C se define una función con el mismo nombre (por ejemplo `TIM3_IRQHandler`), esa función **reemplaza** al alias.

**Líneas 227 a 369**

```asm
   .weak      NMI_Handler                 /* .weak: el símbolo es «débil»: puede ser reemplazado por una función C con el mismo nombre */
   .thumb_set NMI_Handler,Default_Handler  /* .thumb_set: NMI_Handler vale lo mismo que Default_Handler mientras nadie lo reemplace */

   .weak      HardFault_Handler
   .thumb_set HardFault_Handler,Default_Handler

   .weak      MemManage_Handler
   .thumb_set MemManage_Handler,Default_Handler

   .weak      BusFault_Handler
   .thumb_set BusFault_Handler,Default_Handler

   .weak      UsageFault_Handler
   .thumb_set UsageFault_Handler,Default_Handler

   .weak      SVC_Handler
   .thumb_set SVC_Handler,Default_Handler

   .weak      DebugMon_Handler
   .thumb_set DebugMon_Handler,Default_Handler

   .weak      PendSV_Handler
   .thumb_set PendSV_Handler,Default_Handler

   .weak      SysTick_Handler
   .thumb_set SysTick_Handler,Default_Handler

   .weak      WWDG_IRQHandler
   .thumb_set WWDG_IRQHandler,Default_Handler

   .weak      PVD_IRQHandler
   .thumb_set PVD_IRQHandler,Default_Handler

   .weak      TAMP_STAMP_IRQHandler
   .thumb_set TAMP_STAMP_IRQHandler,Default_Handler

   .weak      RTC_WKUP_IRQHandler
   .thumb_set RTC_WKUP_IRQHandler,Default_Handler

   .weak      FLASH_IRQHandler
   .thumb_set FLASH_IRQHandler,Default_Handler

   .weak      RCC_IRQHandler
   .thumb_set RCC_IRQHandler,Default_Handler

   .weak      EXTI0_IRQHandler
   .thumb_set EXTI0_IRQHandler,Default_Handler

   .weak      EXTI1_IRQHandler
   .thumb_set EXTI1_IRQHandler,Default_Handler

   .weak      EXTI2_IRQHandler
   .thumb_set EXTI2_IRQHandler,Default_Handler

   .weak      EXTI3_IRQHandler
   .thumb_set EXTI3_IRQHandler,Default_Handler

   .weak      EXTI4_IRQHandler
   .thumb_set EXTI4_IRQHandler,Default_Handler

   .weak      DMA1_Stream0_IRQHandler
   .thumb_set DMA1_Stream0_IRQHandler,Default_Handler

   .weak      DMA1_Stream1_IRQHandler
   .thumb_set DMA1_Stream1_IRQHandler,Default_Handler

   .weak      DMA1_Stream2_IRQHandler
   .thumb_set DMA1_Stream2_IRQHandler,Default_Handler

   .weak      DMA1_Stream3_IRQHandler
   .thumb_set DMA1_Stream3_IRQHandler,Default_Handler

   .weak      DMA1_Stream4_IRQHandler
   .thumb_set DMA1_Stream4_IRQHandler,Default_Handler

   .weak      DMA1_Stream5_IRQHandler
   .thumb_set DMA1_Stream5_IRQHandler,Default_Handler

   .weak      DMA1_Stream6_IRQHandler
   .thumb_set DMA1_Stream6_IRQHandler,Default_Handler

   .weak      ADC_IRQHandler
   .thumb_set ADC_IRQHandler,Default_Handler

   .weak      CAN1_TX_IRQHandler
   .thumb_set CAN1_TX_IRQHandler,Default_Handler

   .weak      CAN1_RX0_IRQHandler
   .thumb_set CAN1_RX0_IRQHandler,Default_Handler

   .weak      CAN1_RX1_IRQHandler
   .thumb_set CAN1_RX1_IRQHandler,Default_Handler

   .weak      CAN1_SCE_IRQHandler
   .thumb_set CAN1_SCE_IRQHandler,Default_Handler

   .weak      EXTI9_5_IRQHandler
   .thumb_set EXTI9_5_IRQHandler,Default_Handler

   .weak      TIM1_BRK_TIM9_IRQHandler
   .thumb_set TIM1_BRK_TIM9_IRQHandler,Default_Handler

   .weak      TIM1_UP_TIM10_IRQHandler
   .thumb_set TIM1_UP_TIM10_IRQHandler,Default_Handler

   .weak      TIM1_TRG_COM_TIM11_IRQHandler
   .thumb_set TIM1_TRG_COM_TIM11_IRQHandler,Default_Handler

   .weak      TIM1_CC_IRQHandler
   .thumb_set TIM1_CC_IRQHandler,Default_Handler

   .weak      TIM2_IRQHandler
   .thumb_set TIM2_IRQHandler,Default_Handler

   .weak      TIM3_IRQHandler
   .thumb_set TIM3_IRQHandler,Default_Handler

   .weak      TIM4_IRQHandler
   .thumb_set TIM4_IRQHandler,Default_Handler

   .weak      I2C1_EV_IRQHandler
   .thumb_set I2C1_EV_IRQHandler,Default_Handler

   .weak      I2C1_ER_IRQHandler
   .thumb_set I2C1_ER_IRQHandler,Default_Handler

   .weak      I2C2_EV_IRQHandler
   .thumb_set I2C2_EV_IRQHandler,Default_Handler

   .weak      I2C2_ER_IRQHandler
   .thumb_set I2C2_ER_IRQHandler,Default_Handler

   .weak      SPI1_IRQHandler
   .thumb_set SPI1_IRQHandler,Default_Handler

   .weak      SPI2_IRQHandler
   .thumb_set SPI2_IRQHandler,Default_Handler

   .weak      USART1_IRQHandler
   .thumb_set USART1_IRQHandler,Default_Handler

   .weak      USART2_IRQHandler
   .thumb_set USART2_IRQHandler,Default_Handler
```

Desde aquí hasta el final hay 95 pares de líneas con el mismo patrón, uno por cada nombre de la tabla:

```
   .weak      NMI_Handler
   .thumb_set NMI_Handler,Default_Handler
```

- `.weak NMI_Handler` declara el símbolo como **débil**: si en otro archivo hay una definición normal con ese nombre, el linker usa la normal y no se queja de duplicado.
- `.thumb_set NMI_Handler,Default_Handler` hace que `NMI_Handler` sea otro nombre de `Default_Handler` (con la marca de Thumb correcta).
- **Resultado:** si el programa no define `SysTick_Handler`, la entrada `0x3C` de la tabla apunta a `Default_Handler` (bucle infinito). Si el programa define `void SysTick_Handler(void)` en C, la tabla apunta a esa función. Por eso **el nombre de las funciones de interrupción es obligatorio**.

**Líneas 370 a 510**

```asm

   .weak      USART3_IRQHandler
   .thumb_set USART3_IRQHandler,Default_Handler

   .weak      EXTI15_10_IRQHandler
   .thumb_set EXTI15_10_IRQHandler,Default_Handler

   .weak      RTC_Alarm_IRQHandler
   .thumb_set RTC_Alarm_IRQHandler,Default_Handler

   .weak      OTG_FS_WKUP_IRQHandler
   .thumb_set OTG_FS_WKUP_IRQHandler,Default_Handler

   .weak      TIM8_BRK_TIM12_IRQHandler
   .thumb_set TIM8_BRK_TIM12_IRQHandler,Default_Handler

   .weak      TIM8_UP_TIM13_IRQHandler
   .thumb_set TIM8_UP_TIM13_IRQHandler,Default_Handler

   .weak      TIM8_TRG_COM_TIM14_IRQHandler
   .thumb_set TIM8_TRG_COM_TIM14_IRQHandler,Default_Handler

   .weak      TIM8_CC_IRQHandler
   .thumb_set TIM8_CC_IRQHandler,Default_Handler

   .weak      DMA1_Stream7_IRQHandler
   .thumb_set DMA1_Stream7_IRQHandler,Default_Handler

   .weak      FMC_IRQHandler
   .thumb_set FMC_IRQHandler,Default_Handler

   .weak      SDIO_IRQHandler
   .thumb_set SDIO_IRQHandler,Default_Handler

   .weak      TIM5_IRQHandler
   .thumb_set TIM5_IRQHandler,Default_Handler

   .weak      SPI3_IRQHandler
   .thumb_set SPI3_IRQHandler,Default_Handler

   .weak      UART4_IRQHandler
   .thumb_set UART4_IRQHandler,Default_Handler

   .weak      UART5_IRQHandler
   .thumb_set UART5_IRQHandler,Default_Handler

   .weak      TIM6_DAC_IRQHandler
   .thumb_set TIM6_DAC_IRQHandler,Default_Handler

   .weak      TIM7_IRQHandler
   .thumb_set TIM7_IRQHandler,Default_Handler

   .weak      DMA2_Stream0_IRQHandler
   .thumb_set DMA2_Stream0_IRQHandler,Default_Handler

   .weak      DMA2_Stream1_IRQHandler
   .thumb_set DMA2_Stream1_IRQHandler,Default_Handler

   .weak      DMA2_Stream2_IRQHandler
   .thumb_set DMA2_Stream2_IRQHandler,Default_Handler

   .weak      DMA2_Stream3_IRQHandler
   .thumb_set DMA2_Stream3_IRQHandler,Default_Handler

   .weak      DMA2_Stream4_IRQHandler
   .thumb_set DMA2_Stream4_IRQHandler,Default_Handler

   .weak      CAN2_TX_IRQHandler
   .thumb_set CAN2_TX_IRQHandler,Default_Handler

   .weak      CAN2_RX0_IRQHandler
   .thumb_set CAN2_RX0_IRQHandler,Default_Handler

   .weak      CAN2_RX1_IRQHandler
   .thumb_set CAN2_RX1_IRQHandler,Default_Handler

   .weak      CAN2_SCE_IRQHandler
   .thumb_set CAN2_SCE_IRQHandler,Default_Handler

   .weak      OTG_FS_IRQHandler
   .thumb_set OTG_FS_IRQHandler,Default_Handler

   .weak      DMA2_Stream5_IRQHandler
   .thumb_set DMA2_Stream5_IRQHandler,Default_Handler

   .weak      DMA2_Stream6_IRQHandler
   .thumb_set DMA2_Stream6_IRQHandler,Default_Handler

   .weak      DMA2_Stream7_IRQHandler
   .thumb_set DMA2_Stream7_IRQHandler,Default_Handler

   .weak      USART6_IRQHandler
   .thumb_set USART6_IRQHandler,Default_Handler

   .weak      I2C3_EV_IRQHandler
   .thumb_set I2C3_EV_IRQHandler,Default_Handler

   .weak      I2C3_ER_IRQHandler
   .thumb_set I2C3_ER_IRQHandler,Default_Handler

   .weak      OTG_HS_EP1_OUT_IRQHandler
   .thumb_set OTG_HS_EP1_OUT_IRQHandler,Default_Handler

   .weak      OTG_HS_EP1_IN_IRQHandler
   .thumb_set OTG_HS_EP1_IN_IRQHandler,Default_Handler

   .weak      OTG_HS_WKUP_IRQHandler
   .thumb_set OTG_HS_WKUP_IRQHandler,Default_Handler

   .weak      OTG_HS_IRQHandler
   .thumb_set OTG_HS_IRQHandler,Default_Handler

   .weak      DCMI_IRQHandler
   .thumb_set DCMI_IRQHandler,Default_Handler

   .weak      FPU_IRQHandler
   .thumb_set FPU_IRQHandler,Default_Handler

   .weak      SPI4_IRQHandler
   .thumb_set SPI4_IRQHandler,Default_Handler

   .weak      SAI1_IRQHandler
   .thumb_set SAI1_IRQHandler,Default_Handler

   .weak      SAI2_IRQHandler
   .thumb_set SAI2_IRQHandler,Default_Handler

   .weak      QUADSPI_IRQHandler
   .thumb_set QUADSPI_IRQHandler,Default_Handler

   .weak      CEC_IRQHandler
   .thumb_set CEC_IRQHandler,Default_Handler

   .weak      SPDIFRX_IRQHandler
   .thumb_set SPDIFRX_IRQHandler,Default_Handler

   .weak      FMPI2C1_EV_IRQHandler
   .thumb_set FMPI2C1_EV_IRQHandler,Default_Handler

   .weak      FMPI2C1_ER_IRQHandler
   .thumb_set FMPI2C1_ER_IRQHandler,Default_Handler
```

Continúan los mismos pares de `.weak` / `.thumb_set` hasta el último manejador, `FMPI2C1_ER_IRQHandler` (línea 509-510).

### 4. `inc/registros_f446.h`: los registros del chip escritos a mano

**Líneas 1 a 4**

```c
// Guarda de inclusión: si este archivo ya se incluyó, se salta todo hasta #endif (evita definiciones repetidas).
#ifndef REGISTROS_F446_H
// Marca el archivo como ya incluido.
#define REGISTROS_F446_H
```

- `#ifndef REGISTROS_F446_H` / `#define ...` son la **guarda de inclusión** (include guard): si varios archivos incluyen este `.h`, su contenido se procesa una sola vez y no se redefinen tipos. Se cierra con `#endif` al final (línea 92).

**Líneas 6 a 7**

```c
// Tipos de entero de tamaño fijo (uint32_t, uint16_t, uint8_t...).
#include <stdint.h>
```

- `#include <stdint.h>` trae los tipos de ancho fijo (`uint32_t`, `uint8_t`...). Es una cabecera de tipos, no una librería con código, y funciona en `-ffreestanding`. Se usa `uint32_t` porque los registros del chip miden exactamente 32 bits.

**Líneas 9 a 11**

```c
// Direcciones base de los buses. Fuente: RM0390 (manual de referencia STM32F446),
// sección 2.2.2, tabla 1 «STM32F446xx register boundary addresses».
#define PERIFERICOS_BASE (0x40000000U)
```

- `PERIFERICOS_BASE = 0x40000000`: dirección donde empiezan los periféricos en el mapa de memoria (RM0390, tabla 1). Los periféricos están "mapeados en memoria": para configurarlos se **lee y escribe en direcciones concretas**, como si fueran variables.
- La `U` al final (`0x40000000U`) marca el número como *unsigned* (sin signo), para evitar sorpresas con signos en las operaciones.
- Los paréntesis alrededor protegen la macro si se usa dentro de una expresión.

**Líneas 12 a 13**

```c
// Bus AHB1: aquí están los puertos GPIO y el RCC.
#define AHB1_BASE (PERIFERICOS_BASE + 0x20000U)
```

- `AHB1_BASE = PERIFERICOS_BASE + 0x20000` = `0x40020000`. El bus AHB1 es donde están colgados los puertos GPIO y el controlador de reloj (RCC).

**Líneas 15 a 21**

```c
// Direcciones base de cada periférico. Fuente: RM0390, sección 2.2.2, tabla 1.
// Puerto A de GPIO (0x40020000).
#define GPIOA_BASE (AHB1_BASE)
// Puerto C de GPIO (0x40020800).
#define GPIOC_BASE (AHB1_BASE + 0x800U)
// Controlador de reloj RCC (0x40023800).
#define RCC_BASE (AHB1_BASE + 0x3800U)
```

Dirección base de cada periférico (suma de la base del bus y el desplazamiento de la tabla 1 del manual):
- `GPIOA_BASE = AHB1_BASE` → `0x40020000`.
- `GPIOC_BASE = AHB1_BASE + 0x800` → `0x40020800`. (El puerto B, `+0x400`, se agrega en la prueba 03.)
- `RCC_BASE = AHB1_BASE + 0x3800` → `0x40023800`.

**Líneas 23 a 24**

```c
// Mapa de los registros del puerto: cada campo está 4 bytes después del anterior,
// por eso el orden no se puede cambiar. Fuente: RM0390, capítulo 7, sección 7.4, tabla 26.
```

- El comentario dice lo esencial: los registros de un puerto están **uno tras otro, cada 4 bytes**, y por eso el **orden de los campos del `struct` no se puede cambiar**. El compilador pone cada campo justo después del anterior, así que el campo *n* queda en la dirección `base + 4n` (la que dice el manual).

**Líneas 25 a 47**

```c
typedef struct {
    // Desplazamiento 0x00. Modo de cada pin: 2 bits por pin (00 entrada, 01 salida, 10 alterna, 11 analógico).
    volatile uint32_t MODER;
    // Desplazamiento 0x04. Tipo de salida de cada pin: 1 bit por pin (0 push-pull, 1 open-drain).
    volatile uint32_t OTYPER;
    // Desplazamiento 0x08. Velocidad de cambio de cada pin: 2 bits por pin.
    volatile uint32_t OSPEEDR;
    // Desplazamiento 0x0C. Resistencia pull-up o pull-down de cada pin: 2 bits por pin.
    volatile uint32_t PUPDR;
    // Desplazamiento 0x10. Lectura del estado de los pines de entrada: 1 bit por pin.
    volatile uint32_t IDR;
    // Desplazamiento 0x14. Valor que se saca por cada pin de salida: 1 bit por pin.
    volatile uint32_t ODR;
    // Desplazamiento 0x18. Pone (bits 0 a 15) o borra (bits 16 a 31) bits de ODR de forma atómica.
    volatile uint32_t BSRR;
    // Desplazamiento 0x1C. Bloquea la configuración de los pines hasta el próximo reinicio.
    volatile uint32_t LCKR;
    // Desplazamiento 0x20. Función alterna de los pines 0 a 7: 4 bits por pin.
    volatile uint32_t AFRL;
    // Desplazamiento 0x24. Función alterna de los pines 8 a 15: 4 bits por pin.
    volatile uint32_t AFRH;
// Fin de la estructura: desde aquí se puede usar el tipo RegistrosGPIO.
} RegistrosGPIO;
```

`RegistrosGPIO` es un `struct` que **modela** los registros de un puerto GPIO. Cada campo es `volatile uint32_t`:
- `volatile` obliga al compilador a leer o escribir el registro **cada vez** que el código lo pide. Sin `volatile`, el compilador podría guardar el valor en un registro de la CPU y no volver a leerlo (creyendo que "no cambió"), o eliminar una escritura que "no sirve". En hardware el valor puede cambiar por sí solo (por ejemplo, un botón) y cada escritura tiene efecto.

Los campos, en orden (el comentario de cada uno dice su desplazamiento):
- `MODER` (0x00): modo de cada pin, **2 bits por pin**: `00` entrada, `01` salida, `10` función alterna, `11` analógico.
- `OTYPER` (0x04): tipo de salida, 1 bit por pin: `0` push-pull (el pin empuja a 1 y a 0), `1` open-drain (solo tira a 0).
- `OSPEEDR` (0x08): velocidad de cambio (cuán rápido puede cambiar el pin), 2 bits por pin.
- `PUPDR` (0x0C): resistencia interna, 2 bits por pin: `00` ninguna, `01` pull-up, `10` pull-down.
- `IDR` (0x10): **lectura** del nivel de los pines, 1 bit por pin.
- `ODR` (0x14): **escritura** del nivel de los pines de salida, 1 bit por pin.
- `BSRR` (0x18): poner (bits 0 a 15) o borrar (bits 16 a 31) bits de ODR de una sola escritura, sin leer antes.
- `LCKR` (0x1C): bloquea la configuración de pines hasta el siguiente reset (no se usa).
- `AFRL` (0x20) y `AFRH` (0x24): función alterna de los pines 0 a 7 y 8 a 15, 4 bits por pin.

**Líneas 49 a 77**

```c
// Mapa de los registros del RCC (reloj). Cada campo está en su desplazamiento del manual.
// Fuente: RM0390, capítulo 6, sección 6.3, «RCC registers», mapa de registros.
typedef struct {
    // Desplazamiento 0x00. Control del reloj (HSI, HSE, PLL). No se usa todavía (paso 2).
    volatile uint32_t CR;
    // Desplazamiento 0x04. Configuración del PLL. No se usa todavía (paso 2).
    volatile uint32_t PLLCFGR;
    // Desplazamiento 0x08. Configuración del reloj del sistema y de los buses. No se usa todavía (paso 2).
    volatile uint32_t CFGR;
    // Desplazamiento 0x0C. Interrupciones del reloj. No se usa todavía (paso 2).
    volatile uint32_t CIR;
    // Desplazamiento 0x10. Reinicia los puertos AHB1. No se usa todavía (paso 2).
    volatile uint32_t AHB1RSTR;
    // Desplazamiento 0x14. Reinicia los periféricos AHB2. No se usa todavía (paso 2).
    volatile uint32_t AHB2RSTR;
    // Desplazamiento 0x18. Reinicia los periféricos AHB3. No se usa todavía (paso 2).
    volatile uint32_t AHB3RSTR;
    // Desplazamiento 0x1C. Reservado por el fabricante, no se usa.
    uint32_t RESERVADO_0;
    // Desplazamiento 0x20. Reinicia los periféricos del bus APB1. No se usa todavía (paso 2).
    volatile uint32_t APB1RSTR;
    // Desplazamiento 0x24. Reinicia los periféricos del bus APB2. No se usa todavía (paso 2).
    volatile uint32_t APB2RSTR;
    // Desplazamientos 0x28 y 0x2C. Reservados por el fabricante, no se usan.
    uint32_t RESERVADO_1[2];
    // Desplazamiento 0x30. Habilita el reloj de cada puerto GPIO (bit 0 = puerto A, bit 2 = puerto C).
    volatile uint32_t AHB1ENR;
// Fin de la estructura: desde aquí se puede usar el tipo RegistrosRCC.
} RegistrosRCC;
```

`RegistrosRCC` modela el controlador de reloj. Solo se necesitan algunos registros, pero **hay que declarar todos los anteriores** para que el campo que sí se usa (`AHB1ENR`) caiga en el desplazamiento correcto:
- `CR`, `PLLCFGR`, `CFGR` (0x00, 0x04, 0x08): control del reloj, PLL y buses. Se usan desde la prueba 02 (configurar el reloj de 84 MHz).
- `CIR`, `AHB1RSTR`, `AHB2RSTR`, `AHB3RSTR`: interrupciones del reloj y reinicios de periféricos. No se usan.
- `RESERVADO_0` (0x1C) y `RESERVADO_1[2]` (0x28 y 0x2C): huecos del manual. Son `uint32_t` sin `volatile` porque nunca se tocan; sirven solo para mantener la distancia.
- `APB1RSTR`, `APB2RSTR`: reinicio de periféricos de los buses APB.
- `AHB1ENR` (0x30): **habilita el reloj de cada puerto GPIO**. Es el que usa esta prueba: bit 0 = puerto A, bit 2 = puerto C.

(Por qué hay que habilitar el reloj: al arrancar, los periféricos tienen el reloj apagado para ahorrar energía; mientras esté apagado, sus registros no responden a lecturas ni escrituras.)

**Líneas 79 a 85**

```c
// Punteros a los periféricos: se usan como GPIOA->ODR, RCC->AHB1ENR, etc.
// Cada puntero apunta a la dirección base del periférico.
#define GPIOA ((RegistrosGPIO *)GPIOA_BASE)
// Puntero al puerto C de GPIO (botón azul PC13).
#define GPIOC ((RegistrosGPIO *)GPIOC_BASE)
// Puntero al controlador de reloj RCC.
#define RCC ((RegistrosRCC *)RCC_BASE)
```

Punteros a cada periférico. La macro convierte la dirección numérica en un puntero al `struct`:
- `#define GPIOA ((RegistrosGPIO *)GPIOA_BASE)` significa "trata la dirección `0x40020000` como si fuera un `RegistrosGPIO`". Así se puede escribir `GPIOA->ODR` y el compilador calcula `0x40020000 + 0x14`.
- Igual para `GPIOC` y `RCC`.

**Líneas 87 a 90**

```c
// Bit 0 de RCC_AHB1ENR: 1 enciende el reloj del puerto A. Fuente: RM0390, sección 6.3.10.
#define RCC_AHB1ENR_GPIOAEN (1U << 0)
// Bit 2 de RCC_AHB1ENR: 1 enciende el reloj del puerto C. Fuente: RM0390, sección 6.3.10.
#define RCC_AHB1ENR_GPIOCEN (1U << 2)
```

Máscaras de bit de `RCC_AHB1ENR`: `(1U << 0)` es el bit 0 (puerto A) y `(1U << 2)` el bit 2 (puerto C). Dar nombre al bit evita "números mágicos" en el código y deja claro qué se activa.

**Línea 92**

```c
#endif
```

- `#endif` cierra la guarda de inclusión de la línea 2.

### 5. `inc/gpio_config.h`: la interfaz del módulo de pines

**Líneas 1 a 7**

```c
// Guarda de inclusión: si este archivo ya se incluyó, se salta todo hasta #endif (evita definiciones repetidas).
#ifndef GPIO_CONFIG_H
// Marca el archivo como ya incluido.
#define GPIO_CONFIG_H

// Este módulo usa registros_f446.h, por eso se incluye aquí.
#include "registros_f446.h"
```

- Guarda de inclusión (`GPIO_CONFIG_H`) y `#include "registros_f446.h"`: este módulo necesita los tipos `RegistrosGPIO` y los punteros `GPIOA`, `GPIOC`. Las comillas `" "` buscan primero en `inc/` (por `-Iinc`).

**Líneas 9 a 20**

```c
// Valores para los campos de configuración de un pin.
// Fuente: RM0390, sección 7.4, descripción de los registros GPIOx_MODER, GPIOx_PUPDR y GPIOx_OSPEEDR.
// Modo entrada: MODER = 00.
#define MODO_ENTRADA 0U
// Modo salida: MODER = 01.
#define MODO_SALIDA 1U
// Sin pull-up ni pull-down: PUPDR = 00.
#define RESISTENCIA_NINGUNA 0U
// Pull-up interno: PUPDR = 01 (el pin queda en 1 si nadie lo baja).
#define RESISTENCIA_PULL_UP 1U
// Velocidad baja: OSPEEDR = 00.
#define VELOCIDAD_BAJA 0U
```

Valores simbólicos de los campos de configuración. Cada número es el **código de 2 bits** que hay que escribir en el registro del pin:
- `MODO_ENTRADA = 0` (MODER = `00`) y `MODO_SALIDA = 1` (MODER = `01`).
- `RESISTENCIA_NINGUNA = 0` (PUPDR = `00`) y `RESISTENCIA_PULL_UP = 1` (PUPDR = `01`): con pull-up, una resistencia interna tira el pin hacia 3,3 V, así que un pin sin nada conectado se lee **1**.
- `VELOCIDAD_BAJA = 0` (OSPEEDR = `00`).
Usar nombres en vez de `0`/`1` hace que `configuracion.modo = MODO_SALIDA;` se entienda sin mirar el manual.

**Líneas 22 a 35**

```c
// Datos para configurar un pin de una sola vez.
typedef struct {
    // Modo del pin: MODO_ENTRADA o MODO_SALIDA.
    uint32_t modo;
    // Número del pin dentro del puerto (0 a 15).
    uint32_t pin;
    // Resistencia interna: RESISTENCIA_NINGUNA o RESISTENCIA_PULL_UP.
    uint32_t resistencia;
    // Velocidad del pin: VELOCIDAD_BAJA.
    uint32_t velocidad;
    // Función alterna (AF0 a AF15). Usar 0U cuando el pin no es de función alterna.
    uint32_t funcion_alterna;
// Fin de la estructura: desde aquí se puede usar el tipo ConfiguracionPin.
} ConfiguracionPin;
```

`ConfiguracionPin` agrupa todo lo necesario para configurar **un pin** (`typedef struct`):
- `modo`: entrada o salida. `pin`: número 0 a 15 dentro del puerto. `resistencia`: ninguna o pull-up. `velocidad`: baja. `funcion_alterna`: AF0 a AF15 (se pone `0U` cuando no se usa).
- Pasar un `struct` completo a `configurar_pin` evita funciones con cinco parámetros sueltos fáciles de confundir.

**Líneas 37 a 46**

```c
// Enciende el reloj del puerto indicado (solo puerto A o C).
void habilitar_reloj_puerto(RegistrosGPIO *puerto);
// Escribe en los registros del puerto la configuración de un pin.
void configurar_pin(RegistrosGPIO *puerto, ConfiguracionPin configuracion);
// Devuelve 1 si el pin está en 1 y 0 si está en 0.
uint32_t leer_pin(RegistrosGPIO *puerto, uint32_t pin);
// Pone el pin en 1 si estado es distinto de 0, o en 0 si estado es 0.
void escribir_pin(RegistrosGPIO *puerto, uint32_t pin, uint32_t estado);
// Cambia el pin de 0 a 1 o de 1 a 0.
void invertir_pin(RegistrosGPIO *puerto, uint32_t pin);
```

Prototipos (declaraciones) de las cinco funciones del módulo. El `.c` las implementa; cualquier archivo que incluya este `.h` puede llamarlas:
- `habilitar_reloj_puerto`, `configurar_pin`, `leer_pin`, `escribir_pin`, `invertir_pin`.
- Reciben un `RegistrosGPIO *puerto` (por ejemplo `GPIOA`) y el número de pin, así sirven para cualquier puerto.

**Línea 48**

```c
#endif
```

- `#endif` cierra la guarda.

### 6. `src/gpio_config.c`: configurar y manejar pines

**Líneas 1 a 2**

```c
// Se incluye su propia interfaz (gpio_config.h) para que el compilador compruebe que las funciones coinciden con sus prototipos.
#include "gpio_config.h"
```

- Incluye su propio `.h` (que a su vez incluye `registros_f446.h`).

**Líneas 4 a 25**

```c
// Enciende el reloj del puerto. Sin reloj, los registros del puerto no responden.
void habilitar_reloj_puerto(RegistrosGPIO *puerto)
{
    // Si el puerto es A, se pone en 1 el bit 0 de RCC->AHB1ENR (|= no cambia los demás bits).
    if (puerto == GPIOA) {
        // Se enciende el reloj del puerto GPIOA (sin reloj el puerto no responde).
        RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;
    // Si el puerto es C, se pone en 1 el bit 2 de RCC->AHB1ENR.
    } else if (puerto == GPIOC) {
        // Se enciende el reloj del puerto GPIOC.
        RCC->AHB1ENR |= RCC_AHB1ENR_GPIOCEN;
    }
    // Variable que solo sirve para leer el registro; el valor leído no se usa.
    volatile uint32_t lectura_descartada;
    // Dos lecturas después de habilitar el reloj, como en el ejemplo del profesor, por una errata del chip:
    // el periférico necesita unos ciclos antes de poder usarse (no verificado en el RM0390).
    lectura_descartada = RCC->AHB1ENR;
    // Lectura de espera: da unos ciclos para que el reloj recién encendido se estabilice antes de usar el puerto.
    lectura_descartada = RCC->AHB1ENR;
    // El valor leído no se usa: (void) le dice al compilador que se descarta a propósito (evita la advertencia).
    (void)lectura_descartada;
}
```

`habilitar_reloj_puerto` enciende el reloj del puerto:
- Líneas 7-15: `if (puerto == GPIOA) {...} else if (puerto == GPIOC) {...}` compara el puntero recibido con las direcciones de cada puerto y activa el bit correspondiente. `RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;` usa `|=` (OR) para **poner en 1 solo ese bit y dejar los demás como estaban** (si usara `=`, apagaría los relojes de los otros puertos).
- Líneas 16-24: `volatile uint32_t lectura_descartada;` y dos lecturas de `RCC->AHB1ENR`. El código las deja "como en el ejemplo del profesor": el periférico necesita unos ciclos después de encender su reloj antes de poder usarse, y leer el registro da ese pequeño retraso. El comentario aclara que el motivo exacto no se verificó en el RM0390.
- `(void)lectura_descartada;` evita la advertencia de "variable asignada y no usada": le dice al compilador que se ignora a propósito.

**Líneas 27 a 52**

```c
// Configura un pin: modo, velocidad, resistencia y función alterna.
void configurar_pin(RegistrosGPIO *puerto, ConfiguracionPin configuracion)
{
    // Primero se enciende el reloj del puerto para poder escribir sus registros.
    habilitar_reloj_puerto(puerto);

    // Los paréntesis en ~(...) son obligatorios. Sin ellos, ~0x3U << posición se evalúa como (~0x3U) << posición
    // y la máscara borra también la configuración de todos los pines con número menor.
    // Esta es la corrección al WRITE_REG_FIELD del profesor, que usaba ~MASK sin paréntesis.
    // MODER: borra los 2 bits del pin (máscara ~(0x3U << posición)) y pone el modo nuevo en esos bits.
    puerto->MODER = (puerto->MODER & ~(0x3U << (configuracion.pin * 2U))) | (configuracion.modo << (configuracion.pin * 2U));
    // OSPEEDR: borra los 2 bits de velocidad del pin y pone la velocidad nueva.
    puerto->OSPEEDR = (puerto->OSPEEDR & ~(0x3U << (configuracion.pin * 2U))) | (configuracion.velocidad << (configuracion.pin * 2U));
    // PUPDR: borra los 2 bits de resistencia del pin y pone la resistencia nueva.
    puerto->PUPDR = (puerto->PUPDR & ~(0x3U << (configuracion.pin * 2U))) | (configuracion.resistencia << (configuracion.pin * 2U));

    // Pines 0 a 7: la función alterna está en AFRL.
    if (configuracion.pin < 8U) {
        // AFRL: borra los 4 bits de función alterna del pin y pone la función nueva.
        puerto->AFRL = (puerto->AFRL & ~(0xFU << (configuracion.pin * 4U))) | (configuracion.funcion_alterna << (configuracion.pin * 4U));
    // Pines 8 a 15: la función alterna está en AFRH; la posición se calcula restando 8.
    } else {
        // AFRH: borra los 4 bits de función alterna del pin y pone la función nueva.
        puerto->AFRH = (puerto->AFRH & ~(0xFU << ((configuracion.pin - 8U) * 4U))) | (configuracion.funcion_alterna << ((configuracion.pin - 8U) * 4U));
    }
}
```

`configurar_pin` escribe la configuración de un pin en los registros del puerto:
- Línea 31: primero `habilitar_reloj_puerto(puerto)`, porque sin reloj los registros no responden.
- Líneas 33-35 (comentario): la **corrección al `WRITE_REG_FIELD` del profesor**. En C, `~0x3U << n` se evalúa como `(~0x3U) << n` (el `~` va primero), lo que da una máscara con ceros en *todos los bits de menor número* y **borra la configuración de los pines anteriores**. Con paréntesis, `~(0x3U << n)` pone en cero solo los 2 bits del pin `n`.
- Líneas 37, 39 y 41 siguen el mismo patrón de **leer-borrar-escribir un campo**:

```
registro = (registro & ~(MÁSCARA << posición)) | (valor << posición);
```

  1. `registro & ~(0x3U << (pin*2U))`: deja todos los bits como están **menos** los 2 del pin, que quedan en 0. El pin `n` ocupa los bits `2n` y `2n+1` (2 bits por pin).
  2. `| (valor << (pin*2U))`: pone el valor nuevo en esos 2 bits.
  - Ejemplo: pin 5, salida (`01`): máscara `0x3 << 10` = bits 11:10; se borran y se escribe `01` ahí → los otros 15 pines no cambian.
  - `MODER` (línea 37) = modo, `OSPEEDR` (35) = velocidad, `PUPDR` (37) = resistencia.
- Líneas 43-51 (función alterna): usa **4 bits por pin**. Los pines 0 a 7 están en `AFRL` (línea 45, máscara `0xFU`, posición `pin*4`); los pines 8 a 15 están en `AFRH` (línea 49), y se resta 8 al número de pin porque `AFRH` empieza en el pin 8.

**Líneas 54 a 60**

```c
// Lee el estado de un pin de entrada. Devuelve 1 si está en 1 y 0 si está en 0.
uint32_t leer_pin(RegistrosGPIO *puerto, uint32_t pin)
{
    // IDR tiene el estado real de cada pin. (1U << pin) crea una máscara con solo ese bit.
    // Si el bit del pin es 1, la expresión vale distinto de 0 y se devuelve 1U; si no, se devuelve 0U.
    return (puerto->IDR & (1U << pin)) ? 1U : 0U;
}
```

`leer_pin`:
- `puerto->IDR` es el nivel real de los 16 pines. `(1U << pin)` crea una **máscara** con un solo bit en 1 (el del pin). `&` deja solo ese bit.
- `? 1U : 0U` (operador ternario) devuelve 1 si ese bit no es cero y 0 si lo es. La función siempre devuelve 0 o 1.

**Líneas 62 a 74**

```c
// Pone un pin de salida en 1 o en 0.
void escribir_pin(RegistrosGPIO *puerto, uint32_t pin, uint32_t estado)
{
    // Si estado es distinto de 0, se pone en 1 el bit del pin en ODR (|= deja los demás bits igual).
    if (estado != 0U) {
        // Pone en 1 el bit del pin en ODR (salida en alto) sin cambiar los demás pines.
        puerto->ODR |= (1U << pin);
    // Si estado es 0, se pone en 0 el bit del pin en ODR (&= ~ deja los demás bits igual).
    } else {
        // Pone en 0 el bit del pin en ODR (salida en bajo) sin cambiar los demás pines.
        puerto->ODR &= ~(1U << pin);
    }
}
```

`escribir_pin` pone un pin de salida en 1 o en 0 modificando `ODR`:
- Si `estado != 0`: `puerto->ODR |= (1U << pin);` pone el bit en 1 sin tocar los otros.
- Si no: `puerto->ODR &= ~(1U << pin);` pone el bit en 0 sin tocar los otros (`~` invierte la máscara para que solo ese bit quede en 0).
- Esta forma es *leer-modificar-escribir*. Funciona aquí porque solo `main` escribe. (Desde la prueba 04 se cambia por `BSRR`, que no necesita leer.)

**Líneas 76 a 81**

```c
// Invierte un pin de salida: si estaba en 1 pasa a 0, y si estaba en 0 pasa a 1.
void invertir_pin(RegistrosGPIO *puerto, uint32_t pin)
{
    // ^= con la máscara del pin invierte solo ese bit de ODR y deja los demás igual.
    puerto->ODR ^= (1U << pin);
}
```

`invertir_pin`: `puerto->ODR ^= (1U << pin);` el XOR con la máscara **invierte solo ese bit** (1→0, 0→1). Es la forma más corta de hacer parpadear un LED (prueba 02).

### 7. `main.c`: el programa

**Líneas 1 a 4**

```c
// Se incluyen las definiciones de los registros del microcontrolador.
#include "registros_f446.h"
// Se incluye el módulo de configuración de pines (GPIO).
#include "gpio_config.h"
```

- Incluye los registros y el módulo de pines. `main.c` no necesita saber direcciones: usa `GPIOA`, `GPIOC` y las funciones.

**Líneas 6 a 9**

```c
// Número del pin del LED de la placa (PA5).
#define PIN_LED 5U
// Número del pin del botón azul de la placa (PC13). Es activo en bajo: leer 0 significa presionado.
#define PIN_BOTON_AZUL 13U
```

- `PIN_LED 5U`: el LED de usuario de la placa Nucleo está en **PA5** (pin 5 del puerto A).
- `PIN_BOTON_AZUL 13U`: el botón azul está en **PC13**. Es **activo en bajo**: con el botón suelto el pin está en 1 y al presionarlo baja a 0.

**Líneas 11 a 13**

```c
// Función principal: crt0.S la llama cuando termina de preparar la RAM.
int main(void)
{
```

- `int main(void)` es la función a la que salta `crt0.S` con `bl main`. No recibe ni devuelve nada útil porque no hay sistema operativo.

**Líneas 14 a 27**

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

Configuración del LED:
- Se crea una variable `ConfiguracionPin configuracion_led;` y se llenan sus 5 campos: `modo = MODO_SALIDA` (el microcontrolador maneja el pin), `pin = PIN_LED`, `resistencia = RESISTENCIA_NINGUNA` (no hace falta pull-up en una salida), `velocidad = VELOCIDAD_BAJA` (un LED no necesita cambios rápidos) y `funcion_alterna = 0U` (el pin es un GPIO normal, no una función especial).
- `configurar_pin(GPIOA, configuracion_led);` escribe todo en los registros del puerto A. Esa llamada también enciende el reloj del puerto A.

**Líneas 29 a 42**

```c
    // Configuración del botón azul (PC13).
    ConfiguracionPin configuracion_boton;
    // El botón es una entrada.
    configuracion_boton.modo = MODO_ENTRADA;
    // Número del pin del botón.
    configuracion_boton.pin = PIN_BOTON_AZUL;
    // Pull-up interno: el pin queda en 1 mientras el botón no está presionado.
    configuracion_boton.resistencia = RESISTENCIA_PULL_UP;
    // Velocidad baja.
    configuracion_boton.velocidad = VELOCIDAD_BAJA;
    // AF0: no se usa, el pin no es de función alterna.
    configuracion_boton.funcion_alterna = 0U;
    // Se escribe la configuración del botón en el puerto C.
    configurar_pin(GPIOC, configuracion_boton);
```

Configuración del botón:
- Igual que el LED, pero `modo = MODO_ENTRADA` y `resistencia = RESISTENCIA_PULL_UP`. El **pull-up** es necesario porque el botón conecta el pin a tierra al presionarse; sin resistencia, al soltarlo el pin quedaría "flotando" y leería valores al azar. Con el pull-up el pin vale 1 en reposo.
- `configurar_pin(GPIOC, configuracion_boton);` lo escribe en el puerto C (y enciende su reloj).

**Líneas 44 a 55**

```c
    // Bucle infinito: un microcontrolador no termina, repite esto mientras tenga energía.
    while (1) {
        // El botón es activo en bajo: leer 0 significa presionado; el LED se enciende mientras se mantiene presionado.
        if (leer_pin(GPIOC, PIN_BOTON_AZUL) == 0U) {
            // Botón presionado: se pone en 1 el pin PA5 y el LED enciende.
            escribir_pin(GPIOA, PIN_LED, 1U);
        } else {
            // Botón suelto: se pone en 0 el pin PA5 y el LED se apaga.
            escribir_pin(GPIOA, PIN_LED, 0U);
        }
    }
}
```

Bucle principal:
- `while (1)`: un programa de microcontrolador **nunca termina**; se repite siempre. Si `main` terminara, volvería a `crt0.S` y se quedaría en `b .`.
- `if (leer_pin(GPIOC, PIN_BOTON_AZUL) == 0U)`: leer 0 significa botón **presionado** (activo en bajo).
  - Presionado → `escribir_pin(GPIOA, PIN_LED, 1U)`: PA5 en 1, el LED enciende.
  - Suelto (`else`) → `escribir_pin(GPIOA, PIN_LED, 0U)`: PA5 en 0, el LED se apaga.
- Cada vuelta del bucle copia el estado del botón al LED: se llama *sondeo* o *polling* (preguntar una y otra vez). No hay retardo: el chip corre a 16 MHz (el reloj interno HSI, porque todavía no se configura el PLL) y la respuesta se percibe instantánea.

