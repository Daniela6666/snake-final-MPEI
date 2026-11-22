# Conexiones

## Panel P10 (conector HUB75 IN del panel 1)
| Pin HUB75 | Señal | Pin de la Nucleo |
|---|---|---|
| 1 | R1 | PC0 |
| 2 | G1 | PC1 |
| 3 | B1 | PC2 |
| 5 | R2 | PC3 |
| 6 | G2 | PC4 |
| 7 | B2 | PC5 |
| 9 | A | PC10 |
| 10 | B | PC11 |
| 13 | CLK | PC8 |
| 14 | LAT | PC7 |
| 15 | OE | PC6 |
| 16 | GND | GND |

Los pines 4, 8, 11 y 12 quedan sin conectar. El OUT del panel 1 va al IN del panel 2 con otro cable plano.

Antes de energizar, con el cable enchufado y el panel apagado, ningún cable de señal debe dar continuidad con GND, salvo el del pin 16.

## Botones del Joystick Shield V1.A
Activos en bajo, con pull-up interno. El shield va conectado con jumpers (G a GND de la Nucleo); no se usan la V, los ejes X e Y ni el botón K.

| Botón | Pin | Pin Arduino |
|---|---|---|
| A | PA10 | D2 |
| B | PB3 | D3 |
| C | PB5 | D4 |
| D | PB4 | D5 |
| E | PB10 | D6 |

El botón F (PA8) no se usa. El reinicio es el botón azul de la placa (PC13).

## Alimentación
- 5 V externos a los cables rojo (+5 V) y negro (GND) de cada panel, con el GND de la fuente unido al de la Nucleo.
- No alimentar los paneles desde el pin 5 V de la Nucleo.
- Con la fuente usada solo se midió el consumo en rojo: 0,65 A a 4,94 V. No se probó pantalla blanca completa.

## Otros pines
LED LD2: PA5. Botón azul: PC13.
