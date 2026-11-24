# Prueba 07: botones y temporizador (punto que se mueve)

**Qué hace en la placa:** un **punto verde** nace en el centro del panel, quieto. Los botones lo controlan:
- **A** = arriba, **B** = derecha, **C** = abajo, **D** = izquierda: eligen la dirección. El punto avanza **1 píxel cada 200 ms** en esa dirección y **sigue avanzando solo** aunque se suelte el botón.
- **E** = pausa: mientras se mantiene presionado, el punto no avanza.
- **F** = reinicio: vuelve al centro y se queda quieto.
- En el borde del panel el punto se detiene (no sale ni da la vuelta).

**Para qué sirve:** es el **esqueleto del juego**. Aquí se prueban juntas las dos piezas que necesita la serpiente: **leer botones** y **mover algo a un ritmo fijo** (sin usar `esperar_milisegundos`, para que el programa siga leyendo botones mientras tanto).

**Qué se agrega respecto a la prueba 06:**
- El módulo **`botones`** (`inc/botones.h`, `src/botones.c`): configura los 6 botones y los lee como un solo número con un bit por botón.
- Un **temporizador de software** dentro de `system_config.c`: SysTick lo actualiza cada 1 ms y avisa con una bandera cuando pasan 200 ms.
- Un `main.c` nuevo con la lógica del punto.

**Qué NO cambia:** `panel`, `graficos`, `gpio_config`, `registros_f446.h`, `Makefile`, `linker_script.ld` y `crt0.S` son los de la prueba 06. Todo lo que ya estaba en `system_config.c` (reloj, SysTick, `esperar_milisegundos`) tampoco cambia: ver el README de la prueba 02.

### Idea clave: dos formas de «esperar»
- `esperar_milisegundos(200)` **bloquea**: el programa se queda quieto 200 ms y no lee botones.
- El **temporizador de software** no bloquea: `main` da vueltas a toda velocidad leyendo botones, y solo cuando la bandera dice «pasaron 200 ms» mueve el punto.

### Cómo se leen los botones
Los botones del shield están conectados entre el pin y GND. Con la resistencia **pull-up** interna, el pin lee **1** si el botón está suelto y **0** si está presionado (**activo en bajo**). `leer_botones()` invierte esa lógica y devuelve un número donde **1 = presionado**, con un bit por botón:

| Botón | Pin | Bit | Valor |
|---|---|---|---|
| A | PA10 | 0 | `1` |
| B | PB3 | 1 | `2` |
| C | PB5 | 2 | `4` |
| D | PB4 | 3 | `8` |
| E | PB10 | 4 | `16` |
| F | PA8 | 5 | `32` |

Así se pueden presionar varios a la vez: el resultado es la suma (por ejemplo A + B = `3`) y se pregunta por cada uno con `botones & BOTON_X`.

### 1. `src/system_config.c`: el temporizador de software (solo lo nuevo)

**Líneas 25 a 38**

```c
// Temporizador de software que SysTick_Handler actualiza cada milisegundo.
typedef struct {
    // Milisegundos desde el último vencimiento. SysTick_Handler lo suma cada 1 ms y lo pone en 0 al vencer.
    uint32_t contador;
    // Milisegundos entre un vencimiento y el siguiente. Si vale 0, el temporizador está detenido.
    uint32_t periodo;
    // Vale 1 cuando el temporizador venció y todavía no se consultó. main la lee y la baja a 0.
    uint32_t bandera;
// Fin de la estructura: desde aquí se puede usar el tipo TemporizadorSoftware.
} TemporizadorSoftware;

// Temporizador de movimiento: una sola instancia, arranca detenido (periodo 0).
// Es volatile porque SysTick_Handler la cambia sin que main lo sepa.
static volatile TemporizadorSoftware temporizador_movimiento = { 0U, 0U, 0U };
```

**La estructura del temporizador.**
- `typedef struct { ... } TemporizadorSoftware;`: agrupa tres números en un solo tipo.
  - `contador`: cuántos milisegundos pasaron desde el último vencimiento. Lo suma SysTick cada 1 ms.
  - `periodo`: cada cuántos milisegundos debe vencer. **Si vale 0, el temporizador está detenido.**
  - `bandera`: vale 1 cuando venció y nadie lo ha consultado todavía. Es el «aviso» de SysTick a `main`.
- `static volatile TemporizadorSoftware temporizador_movimiento = { 0U, 0U, 0U };`: la única instancia, con los tres campos en 0 (arranca detenida porque `periodo` = 0).
  - **`static`**: solo se ve dentro de este archivo; los demás archivos usan las funciones.
  - **`volatile`**: `SysTick_Handler` la cambia **sin que `main` lo sepa**. Sin `volatile`, el compilador podría guardar la bandera en un registro y `main` nunca vería el cambio.

**Líneas 95 a 111**

```c
// El nombre es el de la tabla de vectores de crt0.S (posición 0x3C). Al definirla aquí reemplaza al alias débil que apunta a Default_Handler.
// Se ejecuta cada 1 ms.
void SysTick_Handler(void)
{
    // Suma 1 milisegundo al contador.
    contador_milisegundos++;
    // Suma 1 milisegundo al contador del temporizador de movimiento.
    temporizador_movimiento.contador++;
    // Si el periodo es 0, el temporizador está detenido y no vence. Si no, se compara con >= y no con ==:
    // así, aunque el contador haya pasado del periodo (por ejemplo, al cambiar el periodo), igual vence.
    if (temporizador_movimiento.periodo != 0U && temporizador_movimiento.contador >= temporizador_movimiento.periodo) {
        // Se reinicia el contador para contar otra vez desde 0 hasta el periodo.
        temporizador_movimiento.contador = 0U;
        // Se avisa a main que el temporizador venció: la bandera queda en 1 hasta que main la consulte.
        temporizador_movimiento.bandera = 1U;
    }
}
```

**`SysTick_Handler`**: la interrupción que se ejecuta **cada 1 ms**.
- Línea 100: `contador_milisegundos++;` (ya existía; es el reloj de `esperar_milisegundos`).
- Línea 102: `temporizador_movimiento.contador++;`: el temporizador de movimiento también suma 1 ms.
- Línea 105: `if (periodo != 0U && contador >= periodo)`: ¿venció?
  - `periodo != 0U`: si está detenido (0), nunca vence.
  - **`>=` y no `==`**: si por algún motivo el contador ya pasó del periodo (por ejemplo, si se cambió el periodo a uno menor), con `==` nunca más vencería. Con `>=` vence igual.
- Línea 107: `contador = 0U;`: reinicia la cuenta para el siguiente periodo.
- Línea 109: `bandera = 1U;`: avisa a `main`. La bandera **se queda en 1** hasta que `main` la consulte.
- Es corto a propósito: una interrupción debe hacer lo mínimo (solo sumar y levantar una bandera).

**Líneas 122 a 131**

```c
// Arranca el temporizador de movimiento con el periodo dado en milisegundos.
void iniciar_temporizador_movimiento(uint32_t periodo_ms)
{
    // Primero se pone el contador en 0 para que la cuenta empiece desde el principio.
    temporizador_movimiento.contador = 0U;
    // Se baja la bandera para que no quede un vencimiento viejo pendiente.
    temporizador_movimiento.bandera = 0U;
    // Se guarda el periodo nuevo. Va al final porque, al escribirlo, el temporizador empieza a poder vencer.
    temporizador_movimiento.periodo = periodo_ms;
}
```

**`iniciar_temporizador_movimiento(periodo_ms)`**: arranca el temporizador.
- `contador = 0U;` la cuenta empieza desde cero.
- `bandera = 0U;` borra cualquier vencimiento viejo pendiente.
- `periodo = periodo_ms;` **se escribe al final**: mientras `periodo` valía 0 el temporizador estaba detenido, y solo al escribirlo empieza a poder vencer. Así nunca vence con valores a medias.

**Líneas 133 a 147**

```c
// Devuelve 1 si el temporizador venció desde la última consulta, y 0 si no.
uint32_t temporizador_movimiento_vencio(void)
{
    // Si la bandera está en 1, el temporizador venció desde la última consulta.
    if (temporizador_movimiento.bandera != 0U) {
        // Se baja la bandera para consumir el aviso: la siguiente consulta devuelve 0 si no vuelve a vencer.
        // La interrupción podría poner la bandera en 1 justo entre el if y esta línea, y ese vencimiento se perdería.
        // Con un periodo de cientos de ms no importa: el siguiente vencimiento se detecta igual.
        temporizador_movimiento.bandera = 0U;
        // Devuelve 1: sí venció.
        return 1U;
    }
    // La bandera está en 0: no venció desde la última consulta.
    return 0U;
}
```

**`temporizador_movimiento_vencio()`**: pregunta «¿venció desde la última vez que pregunté?».
- Línea 137: `if (bandera != 0U)`: ¿SysTick la levantó?
- Línea 141: `bandera = 0U;` **se consume el aviso**: la próxima consulta devolverá 0 hasta que vuelva a vencer.
- Línea 143: `return 1U;` sí venció. Línea 146: `return 0U;` no venció.
- **Limitación conocida** (comentada en el código): si la interrupción levanta la bandera justo entre el `if` y `bandera = 0U`, ese vencimiento se pierde. Con un periodo de 200 ms no importa: el siguiente se detecta igual.

### 2. `inc/botones.h`: interfaz del módulo de botones

**Líneas 1 a 7**

```c
// Guarda de inclusión: si este archivo ya se incluyó, se salta todo hasta #endif (evita definiciones repetidas).
#ifndef BOTONES_H
// Marca el archivo como ya incluido.
#define BOTONES_H

// Este módulo usa gpio_config.h, por eso se incluye aquí.
#include "gpio_config.h"
```

- Guarda de inclusión (`BOTONES_H`) y `#include "gpio_config.h"` (necesita `RegistrosGPIO`, `configurar_pin` y `leer_pin`).

**Líneas 9 a 20**

```c
// Bit del botón A en el valor que devuelve leer_botones (1 = presionado).
#define BOTON_A (1U << 0)
// Bit del botón B en el valor que devuelve leer_botones (1 = presionado).
#define BOTON_B (1U << 1)
// Bit del botón C en el valor que devuelve leer_botones (1 = presionado).
#define BOTON_C (1U << 2)
// Bit del botón D en el valor que devuelve leer_botones (1 = presionado).
#define BOTON_D (1U << 3)
// Bit del botón E en el valor que devuelve leer_botones (1 = presionado).
#define BOTON_E (1U << 4)
// Bit del botón F en el valor que devuelve leer_botones (1 = presionado).
#define BOTON_F (1U << 5)
```

Una máscara por botón: `BOTON_A (1U << 0)` = `0b000001`, `BOTON_B (1U << 1)` = `0b000010`, y así hasta `BOTON_F (1U << 5)` = `0b100000`. Cada botón es **un bit distinto**, por eso se pueden combinar con `|` y consultar con `&`. Los paréntesis protegen la macro de la precedencia de operadores.

**Líneas 22 a 25**

```c
// Configura los seis botones del shield como entradas con pull-up interno.
void configurar_botones(void);
// Devuelve un valor con un bit por cada botón presionado (BOTON_A a BOTON_F). Un bit en 1 = botón presionado.
uint32_t leer_botones(void);
```

- `configurar_botones()`: deja los 6 pines como entradas con pull-up.
- `leer_botones()`: devuelve un número con **1 en cada bit de un botón presionado**.

**Línea 27**

```c
#endif
```

- `#endif`.

### 3. `src/botones.c`: configurar y leer los botones

**Líneas 1 a 2**

```c
// Se incluye su propia interfaz (botones.h) para que el compilador compruebe que las funciones coinciden con sus prototipos.
#include "botones.h"
```

- Incluye `botones.h`.

**Líneas 4 a 15**

```c
// Número del pin del botón A del shield: PA10, activo en bajo (presionado = 0).
#define PIN_BOTON_A 10U
// Número del pin del botón B del shield: PB3, activo en bajo (presionado = 0).
#define PIN_BOTON_B 3U
// Número del pin del botón C del shield: PB5, activo en bajo (presionado = 0).
#define PIN_BOTON_C 5U
// Número del pin del botón D del shield: PB4, activo en bajo (presionado = 0).
#define PIN_BOTON_D 4U
// Número del pin del botón E del shield: PB10, activo en bajo (presionado = 0).
#define PIN_BOTON_E 10U
// Número del pin del botón F del shield: PA8, activo en bajo (presionado = 0).
#define PIN_BOTON_F 8U
```

Números de pin de cada botón (con su puerto en los comentarios): A = PA10, B = PB3, C = PB5, D = PB4, E = PB10, F = PA8. Se escriben una sola vez como constantes con nombre: si el shield cambia de pines, solo se edita aquí.

**Líneas 17 a 34**

```c
// Configura un pin como entrada con pull-up interno. El pin queda en 1 mientras el botón no está presionado.
static void configurar_entrada_con_pull_up(RegistrosGPIO *puerto, uint32_t pin)
{
    // Datos de configuración del pin, que se escriben de una sola vez con configurar_pin.
    ConfiguracionPin configuracion;
    // El botón es una entrada.
    configuracion.modo = MODO_ENTRADA;
    // Número del pin dentro del puerto.
    configuracion.pin = pin;
    // Pull-up interno: el pin queda en 1 mientras el botón no está presionado.
    configuracion.resistencia = RESISTENCIA_PULL_UP;
    // Velocidad baja.
    configuracion.velocidad = VELOCIDAD_BAJA;
    // AF0: no se usa, el pin no es de función alterna.
    configuracion.funcion_alterna = 0U;
    // Se escribe la configuración en el puerto indicado.
    configurar_pin(puerto, configuracion);
}
```

`configurar_entrada_con_pull_up(puerto, pin)`: configura **un** pin como botón.
- **`static`**: función auxiliar privada, solo la usa este archivo.
- `ConfiguracionPin configuracion;`: la estructura que recibe `configurar_pin` (ver README de la prueba 01).
- `modo = MODO_ENTRADA`: el botón se **lee**, no se maneja.
- `pin = pin`: número del pin dentro del puerto.
- `resistencia = RESISTENCIA_PULL_UP`: conecta una resistencia interna a 3,3 V. **Por qué:** un pin de entrada sin nada conectado «flota» y lee valores al azar. Con el pull-up lee **1** en reposo y el botón, al cerrarse contra GND, lo baja a **0**.
- `velocidad = VELOCIDAD_BAJA`: no importa en una entrada; se pone el valor más tranquilo.
- `funcion_alterna = 0U`: no se usa (el pin no es de función alterna), AF0.
- `configurar_pin(puerto, configuracion)`: escribe los registros MODER, OSPEEDR, PUPDR (y AFR) del pin.

**Líneas 36 a 51**

```c
// Configura los seis pines de los botones como entradas con pull-up.
void configurar_botones(void)
{
    // Botón A (PA10) en el puerto A.
    configurar_entrada_con_pull_up(GPIOA, PIN_BOTON_A);
    // Botón B (PB3) en el puerto B. PB3 arranca en función alterna de depuración; por eso se configura explícitamente como entrada.
    configurar_entrada_con_pull_up(GPIOB, PIN_BOTON_B);
    // Botón C (PB5) en el puerto B.
    configurar_entrada_con_pull_up(GPIOB, PIN_BOTON_C);
    // Botón D (PB4) en el puerto B. PB4 arranca en función alterna de depuración; por eso se configura explícitamente como entrada.
    configurar_entrada_con_pull_up(GPIOB, PIN_BOTON_D);
    // Botón E (PB10) en el puerto B.
    configurar_entrada_con_pull_up(GPIOB, PIN_BOTON_E);
    // Botón F (PA8) en el puerto A.
    configurar_entrada_con_pull_up(GPIOA, PIN_BOTON_F);
}
```

`configurar_botones()`: llama a la función de arriba para cada botón y su puerto.
- A (PA10) y F (PA8) están en el **puerto A**; B, C, D y E en el **puerto B**.
- **PB3 (B) y PB4 (D) son pines especiales**: tras el reset están en función alterna de **depuración** (JTDO y NJTRST). Por eso se configuran **explícitamente** como entrada: `configurar_pin` los saca de ese modo (ver README de la prueba 03).

**Líneas 53 a 90**

```c
// Lee los seis botones y devuelve un número con un bit en 1 por cada botón presionado.
uint32_t leer_botones(void)
{
    // Valor que se va armando: cada botón presionado pone su bit en 1.
    uint32_t botones = 0U;
    // Los botones son activos en bajo: leer_pin devuelve 0 cuando el botón está presionado.
    if (leer_pin(GPIOA, PIN_BOTON_A) == 0U) {
        // Se pone en 1 el bit del botón A (|= no cambia los demás bits).
        botones |= BOTON_A;
    }
    // Botón B (PB3): presionado = 0.
    if (leer_pin(GPIOB, PIN_BOTON_B) == 0U) {
        // Se pone en 1 el bit del botón B.
        botones |= BOTON_B;
    }
    // Botón C (PB5): presionado = 0.
    if (leer_pin(GPIOB, PIN_BOTON_C) == 0U) {
        // Se pone en 1 el bit del botón C.
        botones |= BOTON_C;
    }
    // Botón D (PB4): presionado = 0.
    if (leer_pin(GPIOB, PIN_BOTON_D) == 0U) {
        // Se pone en 1 el bit del botón D.
        botones |= BOTON_D;
    }
    // Botón E (PB10): presionado = 0.
    if (leer_pin(GPIOB, PIN_BOTON_E) == 0U) {
        // Se pone en 1 el bit del botón E.
        botones |= BOTON_E;
    }
    // Botón F (PA8): presionado = 0.
    if (leer_pin(GPIOA, PIN_BOTON_F) == 0U) {
        // Se pone en 1 el bit del botón F.
        botones |= BOTON_F;
    }
    // Se devuelve el valor con un bit por cada botón presionado.
    return botones;
}
```

`leer_botones()`: arma el número con un bit por botón presionado.
- Línea 57: `uint32_t botones = 0U;` empieza sin ningún botón presionado.
- Cada bloque `if (leer_pin(puerto, pin) == 0U) { botones |= BOTON_X; }`:
  - `leer_pin` devuelve el nivel del pin: **0 = presionado** (activo en bajo, por el pull-up).
  - `botones |= BOTON_X` pone en 1 **solo** el bit de ese botón; el `|=` no toca los demás bits, así se acumulan varios botones.
- Línea 89: `return botones;`.
- Resultado: con A y C presionados, `botones` = `1 | 4` = `5`.

### 4. `main.c`: la lógica del punto

**Líneas 1 a 6**

```c
// Se incluye la configuración del reloj y del temporizador SysTick.
#include "system_config.h"
// Se incluye el módulo del panel LED (framebuffer y refresco).
#include "panel.h"
// Se incluye el módulo de lectura de los botones.
#include "botones.h"
```

- Incluye el reloj/temporizador (`system_config.h`), el panel y los botones. No usa `graficos.h` porque solo dibuja un píxel.

**Líneas 8 a 23**

```c
// Tiempo entre un paso del punto y el siguiente, en milisegundos. El punto avanza un píxel cada 200 ms.
#define PERIODO_MOVIMIENTO_MS 200U
// Columna x donde nace el punto: el centro del panel.
#define POSICION_INICIAL_X (PANEL_ANCHO / 2U)
// Fila y donde nace el punto: el centro del panel.
#define POSICION_INICIAL_Y (PANEL_ALTO / 2U)
// Dirección sin movimiento: el punto está quieto hasta que se presiona A, B, C o D.
#define DIRECCION_QUIETO 0U
// Dirección arriba: y disminuye (el botón A).
#define DIRECCION_ARRIBA 1U
// Dirección derecha: x aumenta (el botón B).
#define DIRECCION_DERECHA 2U
// Dirección abajo: y aumenta (el botón C).
#define DIRECCION_ABAJO 3U
// Dirección izquierda: x disminuye (el botón D).
#define DIRECCION_IZQUIERDA 4U
```

Constantes con nombre:
- `PERIODO_MOVIMIENTO_MS 200U`: el punto avanza un píxel cada 200 ms (5 píxeles por segundo).
- `POSICION_INICIAL_X (PANEL_ANCHO / 2U)` y `POSICION_INICIAL_Y (PANEL_ALTO / 2U)`: el centro del panel (los paréntesis protegen la división).
- `DIRECCION_QUIETO 0U`, `ARRIBA 1U`, `DERECHA 2U`, `ABAJO 3U`, `IZQUIERDA 4U`: cada dirección es un número. Se usa 0 para «quieto» porque es el valor inicial de una variable `static`.

**Líneas 25 a 30**

```c
// Columna actual del punto verde.
static uint32_t punto_x;
// Fila actual del punto verde.
static uint32_t punto_y;
// Dirección en la que avanza el punto: uno de los DIRECCION_*.
static uint32_t direccion;
```

Tres variables globales `static` (solo este archivo las usa; viven en `.bss` y arrancan en 0):
- `punto_x`, `punto_y`: dónde está el punto ahora.
- `direccion`: hacia dónde va (uno de los `DIRECCION_*`).
No son `volatile` porque **ninguna interrupción las cambia**: solo `main`.

**Líneas 32 a 45**

```c
// Apaga el punto en su posición actual, lo pone en el centro, lo deja quieto y lo enciende en verde.
static void reiniciar_punto(void)
{
    // Se apaga el píxel de la posición actual para que no quede un punto viejo en el panel.
    encender_pixel(punto_x, punto_y, COLOR_NEGRO);
    // El punto vuelve a la posición inicial (el centro).
    punto_x = POSICION_INICIAL_X;
    // La fila inicial es la del centro.
    punto_y = POSICION_INICIAL_Y;
    // El punto queda quieto hasta que se presione una dirección.
    direccion = DIRECCION_QUIETO;
    // Se enciende el punto en su posición inicial, en verde.
    encender_pixel(punto_x, punto_y, COLOR_VERDE);
}
```

`reiniciar_punto()`: pone el punto en el centro, quieto.
- `encender_pixel(punto_x, punto_y, COLOR_NEGRO)`: **primero apaga el punto donde está**, para no dejar un punto viejo en el panel.
- `punto_x/punto_y = POSICION_INICIAL_*`: lo manda al centro.
- `direccion = DIRECCION_QUIETO`: queda quieto hasta que se presione A, B, C o D.
- `encender_pixel(..., COLOR_VERDE)`: lo dibuja en verde en el centro.
- Al inicio, `punto_x/y` valen 0, así que apaga el píxel (0, 0), que ya estaba negro: no hace daño.

**Líneas 47 a 71**

```c
// Cambia la dirección según los botones presionados. Si hay dos presionados, gana el último en este orden,
// porque el programa no sabe cuál se presionó primero.
static void actualizar_direccion(uint32_t botones)
{
    // Si el botón A está presionado, la dirección es arriba.
    if ((botones & BOTON_A) != 0U) {
        // Se guarda la dirección arriba.
        direccion = DIRECCION_ARRIBA;
    }
    // Si el botón B está presionado, la dirección es derecha.
    if ((botones & BOTON_B) != 0U) {
        // Se guarda la dirección derecha.
        direccion = DIRECCION_DERECHA;
    }
    // Si el botón C está presionado, la dirección es abajo.
    if ((botones & BOTON_C) != 0U) {
        // Se guarda la dirección abajo.
        direccion = DIRECCION_ABAJO;
    }
    // Si el botón D está presionado, la dirección es izquierda.
    if ((botones & BOTON_D) != 0U) {
        // Se guarda la dirección izquierda.
        direccion = DIRECCION_IZQUIERDA;
    }
}
```

`actualizar_direccion(botones)`: elige la dirección según los botones.
- Cada `if ((botones & BOTON_X) != 0U)` pregunta si ese bit está en 1 (botón presionado) y entonces cambia `direccion`.
- **A = arriba, B = derecha, C = abajo, D = izquierda.**
- Si hay dos botones a la vez, **gana el último `if`** (D sobre C sobre B sobre A): el programa no sabe cuál se presionó primero, así que se define un orden fijo.
- Si no hay ningún botón, **`direccion` no cambia**: el punto sigue en la dirección que ya llevaba. Por eso el punto sigue avanzando al soltar el botón.

**Líneas 73 a 111**

```c
// Avanza el punto un píxel en la dirección actual. En el borde se detiene y conserva la dirección.
static void mover_punto(void)
{
    // La posición nueva empieza igual a la actual; solo cambia si la dirección lo permite.
    uint32_t nueva_x = punto_x;
    // Lo mismo para la fila: empieza igual a la actual.
    uint32_t nueva_y = punto_y;
    // Arriba: se resta 1 a y solo si no está en la primera fila (0).
    if (direccion == DIRECCION_ARRIBA && punto_y > 0U) {
        // Sube una fila.
        nueva_y = punto_y - 1U;
    }
    // Abajo: se suma 1 a y solo si no está en la última fila.
    if (direccion == DIRECCION_ABAJO && punto_y < PANEL_ALTO - 1U) {
        // Baja una fila.
        nueva_y = punto_y + 1U;
    }
    // Izquierda: se resta 1 a x solo si no está en la primera columna (0).
    if (direccion == DIRECCION_IZQUIERDA && punto_x > 0U) {
        // Se mueve una columna a la izquierda.
        nueva_x = punto_x - 1U;
    }
    // Derecha: se suma 1 a x solo si no está en la última columna.
    if (direccion == DIRECCION_DERECHA && punto_x < PANEL_ANCHO - 1U) {
        // Se mueve una columna a la derecha.
        nueva_x = punto_x + 1U;
    }
    // Si la posición cambió, se mueve el punto. Si no cambió (borde o quieto), no se hace nada.
    if (nueva_x != punto_x || nueva_y != punto_y) {
        // Primero se enciende el píxel nuevo en verde.
        encender_pixel(nueva_x, nueva_y, COLOR_VERDE);
        // Después se apaga el píxel viejo, para no dejar dos puntos en el panel.
        encender_pixel(punto_x, punto_y, COLOR_NEGRO);
        // Se guarda la posición nueva como la actual.
        punto_x = nueva_x;
        // Lo mismo para la fila.
        punto_y = nueva_y;
    }
}
```

`mover_punto()`: avanza **un píxel** en la dirección actual.
- Líneas 77-79: `nueva_x` y `nueva_y` empiezan iguales a la posición actual; solo cambian si la dirección lo permite.
- Líneas 81-99: **una condición por dirección, con su límite**:
  - Arriba: `punto_y > 0U` → `nueva_y = punto_y - 1U`. **Por qué se pregunta antes de restar:** `punto_y` es sin signo; `0 - 1` daría `0xFFFFFFFF`.
  - Abajo: `punto_y < PANEL_ALTO - 1U` → `nueva_y = punto_y + 1U`.
  - Izquierda: `punto_x > 0U` → `nueva_x = punto_x - 1U`.
  - Derecha: `punto_x < PANEL_ANCHO - 1U` → `nueva_x = punto_x + 1U`.
  - En el borde la condición es falsa, `nueva_*` no cambia y el punto **se detiene conservando la dirección**.
- Línea 101: `if (nueva_x != punto_x || nueva_y != punto_y)`: solo si la posición cambió.
  - Línea 103: **primero enciende el píxel nuevo en verde.**
  - Línea 105: después apaga el viejo. **Por qué en ese orden:** el panel se refresca por interrupción; si se apagara primero el viejo, por un instante no habría punto y se vería parpadear.
  - Líneas 107-109: guarda la posición nueva como la actual.

**Líneas 113 a 131**

```c
// Función principal: crt0.S la llama cuando termina de preparar la RAM.
int main(void)
{
    // Primero el reloj, antes de usar cualquier periférico: deja el sistema a 84 MHz.
    configurar_reloj();
    // Se enciende la base de tiempo de 1 ms (SysTick), que usa el temporizador de movimiento.
    iniciar_systick();

    // Se configuran los pines del panel como salidas.
    configurar_panel();
    // Se enciende TIM3: desde aquí, una interrupción cada 1 ms dibuja una fase del framebuffer en el panel.
    iniciar_refresco_panel();

    // Se configuran los seis botones como entradas con pull-up.
    configurar_botones();
    // El temporizador de movimiento cuenta desde 0 con un periodo de 200 ms.
    iniciar_temporizador_movimiento(PERIODO_MOVIMIENTO_MS);
    // El punto aparece en el centro, quieto y en verde.
    reiniciar_punto();
```

`main`, preparación (igual que en la 06, más tres líneas nuevas):
- `configurar_reloj()`: sistema a 84 MHz. `iniciar_systick()`: interrupción cada 1 ms (ahora también hace avanzar el temporizador de movimiento).
- `configurar_panel()` e `iniciar_refresco_panel()`: pines del panel y TIM3 (refresco automático).
- **Nuevo** `configurar_botones()`: los 6 pines como entradas con pull-up.
- **Nuevo** `iniciar_temporizador_movimiento(200)`: el temporizador empieza a contar 200 ms.
- **Nuevo** `reiniciar_punto()`: el punto aparece en el centro, quieto, en verde.

**Líneas 133 a 155**

```c
    // Bucle infinito: un microcontrolador no termina, repite esto mientras tenga energía.
    while (1) {
        // Los botones se leen en cada vuelta del bucle, no solo cuando vence el temporizador, para no perder pulsaciones cortas.
        uint32_t botones = leer_botones();
        // F reinicia el punto (mientras se mantiene presionada); si no, los botones A a D cambian la dirección.
        if ((botones & BOTON_F) != 0U) {
            // Se reinicia el punto al centro.
            reiniciar_punto();
        } else {
            // Se actualiza la dirección según los botones A a D.
            actualizar_direccion(botones);
        }

        // La bandera del temporizador se consume siempre, aunque haya pausa, para que no quede un vencimiento viejo pendiente.
        if (temporizador_movimiento_vencio() == 1U) {
            // E pausa el movimiento solo mientras se mantiene presionada: si no está presionada, el punto avanza.
            if ((botones & BOTON_E) == 0U) {
                // El punto avanza un paso en la dirección actual.
                mover_punto();
            }
        }
    }
}
```

El bucle principal da vueltas **muy rápido** (miles por segundo):
- Línea 136: `uint32_t botones = leer_botones();`: lee los botones **en cada vuelta**, no solo cada 200 ms, para **no perder pulsaciones cortas**.
- Líneas 138-144: si F está presionado → `reiniciar_punto()` (mientras se mantenga presionado, el punto se queda en el centro). Si no → `actualizar_direccion(botones)`.
- Línea 147: `if (temporizador_movimiento_vencio() == 1U)`: ¿pasaron 200 ms? **La bandera se consume siempre**, aunque haya pausa, para no acumular un vencimiento viejo.
- Línea 149: `if ((botones & BOTON_E) == 0U) { mover_punto(); }`: el punto avanza **solo si E NO está presionado**. Con E presionado, la pausa dura mientras se mantiene.
- Resumen: **leer botones** cada vuelta (rápido) y **mover el punto** solo cuando vence el temporizador (cada 200 ms). Separar las dos cosas es justo lo que necesitará el juego.

