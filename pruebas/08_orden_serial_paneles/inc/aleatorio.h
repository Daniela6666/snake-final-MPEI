// Guarda de inclusión: si este archivo ya se incluyó, se salta todo hasta #endif (evita definiciones repetidas).
#ifndef ALEATORIO_H
// Marca el archivo como ya incluido.
#define ALEATORIO_H

// Tipos de entero de tamaño fijo (uint32_t, uint16_t, uint8_t...).
#include <stdint.h>

// Pone la semilla del generador. Si la semilla queda en 0, se usa 1 en su lugar.
void sembrar_aleatorio(uint32_t semilla);
// Devuelve el siguiente número pseudoaleatorio de 16 bits (LFSR de Fibonacci).
uint32_t siguiente_aleatorio(void);

#endif
