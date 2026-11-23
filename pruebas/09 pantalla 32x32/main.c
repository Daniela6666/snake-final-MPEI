// Prueba de la pantalla de 32x32 (dos paneles): marco, un dígito en cada esquina y los 7 colores en la unión de los paneles.
#include "system_config.h"
// Se incluye el módulo del panel LED (framebuffer y refresco).
#include "panel.h"
// Se incluye el módulo gráfico (rectángulos y dígitos).
#include "graficos.h"

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
    // Primero el reloj, antes de usar cualquier periférico: deja el sistema a 84 MHz.
    configurar_reloj();
    // Se configuran los pines del panel como salidas.
    configurar_panel();
    // Se enciende TIM3: desde aquí la interrupción refresca el panel cada 1 ms, sin necesidad de llamarla desde main.
    iniciar_refresco_panel();

    // Marco verde alrededor de todo el tablero: la esquina superior izquierda en (0, 0) y el tamaño del tablero.
    dibujar_rectangulo(0U, 0U, PANEL_ANCHO, PANEL_ALTO, COLOR_VERDE);
    // Dígito 1 blanco en la esquina superior izquierda, a 2 píxeles del borde.
    dibujar_digito(2U, 2U, 1U, COLOR_BLANCO);
    // Dígito 2 blanco en la esquina superior derecha, a 2 píxeles del borde.
    dibujar_digito(PANEL_ANCHO - 2U - FUENTE_ANCHO, 2U, 2U, COLOR_BLANCO);
    // Dígito 3 blanco en la esquina inferior izquierda, a 2 píxeles del borde.
    dibujar_digito(2U, PANEL_ALTO - 2U - FUENTE_ALTO, 3U, COLOR_BLANCO);
    // Dígito 4 blanco en la esquina inferior derecha, a 2 píxeles del borde.
    dibujar_digito(PANEL_ANCHO - 2U - FUENTE_ANCHO, PANEL_ALTO - 2U - FUENTE_ALTO, 4U, COLOR_BLANCO);

    // Dos filas de colores en x = 12 a 18: la fila 15 es la última del panel 1 y la 16 es la primera del panel 2.
    for (uint32_t i = 0U; i < 7U; i++) {
        // Píxel de la fila 15 con el color i.
        encender_pixel(12U + i, 15U, COLORES_DE_PRUEBA[i]);
        // Píxel de la fila 16 con el mismo color i.
        encender_pixel(12U + i, 16U, COLORES_DE_PRUEBA[i]);
    }

    // El refresco sigue por la interrupción de TIM3; main no hace nada más.
    while (1) {
    }
}
