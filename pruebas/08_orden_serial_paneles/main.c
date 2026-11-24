// Prueba del orden serial de los dos paneles encadenados: enciende un solo bit de la cadena de 128 para ver en qué píxel aparece.
#include "system_config.h"
// Se incluye el módulo del panel LED (framebuffer y refresco).
#include "panel.h"
// Se incluye el módulo de lectura de los botones.
#include "botones.h"

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

    // Bit de la cadena que se enciende (0 a 127).
    uint32_t bit_encendido = 0U;
    // Fase que se muestra (0 a 3).
    uint32_t fase = 0U;
    // Botones presionados en la vuelta anterior, para detectar solo el flanco de pulsación.
    uint32_t botones_anteriores = 0U;

    // Bucle infinito: un microcontrolador no termina, repite esto mientras tenga energía.
    while (1) {
        // Botones presionados en esta vuelta.
        uint32_t botones = leer_botones();
        // Flancos de pulsación: bits que están presionados ahora y no lo estaban antes. Así cada pulsación actúa una vez.
        uint32_t nuevos = botones & ~botones_anteriores;
        // Se guarda el estado actual para comparar en la siguiente vuelta.
        botones_anteriores = botones;

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

        // Si hubo alguna pulsación nueva, se espera 30 ms para que el rebote del botón no cuente como otra pulsación.
        if (nuevos != 0U) {
            // Se espera 30 ms (más largo que el rebote del botón, que dura unos 4 ms).
            esperar_milisegundos(30U);
        }

        // Se dibuja la fase con el bit encendido. Se llama en cada vuelta porque no hay refresco por interrupción.
        dibujar_fase_de_prueba(bit_encendido, fase);
    }
}
