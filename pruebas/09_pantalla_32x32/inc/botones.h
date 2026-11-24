// Guarda de inclusión: si este archivo ya se incluyó, se salta todo hasta #endif (evita definiciones repetidas).
#ifndef BOTONES_H
// Marca el archivo como ya incluido.
#define BOTONES_H

// Este módulo usa gpio_config.h, por eso se incluye aquí.
#include "gpio_config.h"

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
// Bit del botón de reinicio en el valor que devuelve leer_botones (1 = presionado): el botón azul de la placa, PC13.
#define BOTON_REINICIO (1U << 5)

// Configura los cinco botones del shield y el botón azul de la placa como entradas con pull-up interno.
void configurar_botones(void);
// Devuelve un valor con un bit por cada botón presionado (BOTON_A a BOTON_E y BOTON_REINICIO). Un bit en 1 = botón presionado.
uint32_t leer_botones(void);

#endif
