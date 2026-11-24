# Nombre del programa: se genera snake.elf.
APPNAME = snake

# Compilador cruzado: corre en el PC pero genera código para el Cortex-M4 (arm-none-eabi = ARM sin sistema operativo).
CC = arm-none-eabi-gcc

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

# Opciones del linker: -Tlinker_script.ld usa nuestro mapa de memoria; -nostdlib no enlaza las bibliotecas estándar.
LDFLAGS = -Tlinker_script.ld -nostdlib

# Archivos C: main.c y todos los .c de la carpeta src/ ($(wildcard ...) expande el patrón).
C_SRC = main.c $(wildcard src/*.c)
# Archivo en ensamblador: el arranque.
ASM_SRC = crt0.S
# Archivos objeto (.o): cada .c y cada .S cambiando su extensión por .o.
OBJS = $(C_SRC:.c=.o) $(ASM_SRC:.S=.o)

# Objetivo por defecto («make» solo): construir snake.elf.
all: $(APPNAME).elf

# Regla del ejecutable. Línea 1 de la receta: el linker une todos los .o en un solo .elf ($@ = el nombre del objetivo).
# Línea 2: arm-none-eabi-size muestra cuánta FLASH (text, data) y RAM (bss) ocupa el programa.
$(APPNAME).elf: $(OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS) $(OBJS) -o $@
	arm-none-eabi-size $@

# Regla patrón: cada .o de ensamblador se construye a partir de su .S ($< = el archivo de entrada; -c = solo compilar, sin enlazar).
%.o: %.S
	$(CC) $(CFLAGS) -c $< -o $@

# Regla patrón: cada .o de C se construye a partir de su .c.
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# «clean» no es un archivo sino una acción (.PHONY): «make clean» borra los objetos y el .elf para empezar de cero.
.PHONY: clean
clean:
	rm -f *.o src/*.o *.elf

# «flash» también es una acción: construye el .elf si hace falta y lo graba en la placa con OpenOCD por el ST-LINK
# (program = grabar, verify = comprobar lo grabado, reset = reiniciar el microcontrolador, exit = cerrar OpenOCD).
.PHONY: flash
flash: $(APPNAME).elf
	openocd -f interface/stlink.cfg -f target/stm32f4x.cfg -c "program $(APPNAME).elf verify reset exit"
