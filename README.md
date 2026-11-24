# Snake en paneles P10 RGB (NUCLEO-F446RE)

Proyecto final de Microprocesadores e Interfaces (Ingeniería Electrónica, MPEI 2026-2).
Juego Snake de 32×32 píxeles en dos paneles P10 RGB, programado sin librerías de ST (sin HAL ni CMSIS): todos los periféricos se manejan escribiendo sus registros.

**Integrantes:** Daniela Molina López y Daniel Martinez Fontecha.

## Cómo se juega
| Botón | Pin | Acción |
|---|---|---|
| A | PA10 | Izquierda |
| B | PB3 | Abajo |
| C | PB5 | Derecha |
| D | PB4 | Arriba |
| E | PB10 | Pausa (mientras se mantiene presionado) |
| Azul de la placa | PC13 | Reiniciar |

- Serpiente **verde**. Manzana **roja**: +1 punto y la serpiente crece 1 segmento.
- Veneno **azul**: −2 puntos y la serpiente pierde 2 segmentos. Aparece y desaparece solo.
- El juego termina al chocar con una pared o con el propio cuerpo, y el panel muestra el puntaje.

## Qué se necesita
- Placa NUCLEO-F446RE, 2 paneles P10 RGB 32×16 (HUB75), Joystick Shield V1.A y una fuente de 5 V para los paneles.
- `arm-none-eabi-gcc` 10.3.1, `make` 4.3 y `openocd` 0.11.0 (las versiones con las que se probó, en Linux sobre WSL2).

Las conexiones están en [`docs/conexiones.md`](docs/conexiones.md).

## Compilar y grabar
```bash
cd juego
make          # compila y genera snake.elf
make flash    # graba la placa con OpenOCD y el ST-LINK
```

## Carpetas
| Carpeta | Contenido |
|---|---|
| `juego/` | El juego definitivo, con el reloj, el GPIO y los demás módulos |
| `pruebas/` | Nueve programas de prueba que se grabaron durante el desarrollo, con su explicación línea por línea ([índice](pruebas/README.md)) |
| `mediciones/` | Mediciones con osciloscopio y multímetro, con los programas de Python que las analizan ([índice](mediciones/README.md)) |
| `entregables/` | [Video del juego funcionando](entregables/juego_funcionando.mp4) en los dos paneles, con el Joystick Shield |
| `docs/` | Conexiones, mapeo de píxeles y guía de estudio |
| `AI_USO.md` | Registro del uso de IA |
