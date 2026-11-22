# Registro de uso de IA

Requisito 10 del curso: todo uso de IA debe quedar documentado (herramienta, propósito y qué código se generó). Cada entrada se agrega en el mismo commit en que entra el código o documento.

## Declaración general
- **Chat y Cowork (entradas 1 y 2):** elegir la conexión del panel, diagnosticar por qué no encendía y medir su mapeo en un repositorio anterior (su código no se reutiliza), y analizar los ejemplos del profesor y armar el plan.
- **Agente principal (Claude Code, Sonnet 5.5):** coordinó el trabajo, nos hizo las preguntas de diseño, escribió directamente el `Makefile`, el `linker_script.ld`, el `crt0.S` y la guía de estudio, y en cada paso recompiló, grabó la placa (`make flash`) y aplicó correcciones menores por decisión nuestra.
- **Subagente `programador` (Haiku):** escribió el código del firmware desde la pieza 4 del paso 1 hasta el paso 11 (entradas 6 a 16).
- **Subagente `revisor` (Sonnet):** revisó y verificó ese código (compiló, comprobó pines y offsets, lo simuló en programas de PC). Solo cambió comentarios, en las entradas 7 y 14.
- **Lo que decidimos y hicimos nosotros:** el diseño (pines, reglas del juego, tiempos, nombres y estructura), las respuestas a las preguntas de Claude Code, el cableado, la medición del mapeo de los dos paneles (entrada 16) y la prueba de cada paso en la placa.
- Las mediciones con osciloscopio y la carpeta de pruebas se publican aparte, con sus propias entradas.
- Los commits no llevan firma de la herramienta: el uso de IA se declara solo aquí.

La columna "Revisión propia" la completan los integrantes del equipo.

| # | Fecha | Herramienta | Para qué se usó | Código o documento generado | Revisión propia |
|---|---|---|---|---|---|
| 1 | 2026-10-19 a 2026-10-22 | Claude (chat) y Claude Code | Elegir la conexión del panel, diagnosticar por qué no encendía (filas del conector invertidas) y medir su mapeo, en un repositorio anterior | Programas de prueba de ese repositorio; no se reutilizan aquí | Pendiente de completar |
| 2 | 2026-11-08 | Claude (Cowork) | Analizar los ejemplos del profesor y armar el plan paso a paso | Plan y documentos iniciales; sin código de firmware | Pendiente de completar |
| 3 | 2026-11-08 | Claude Code (Sonnet 5.5) | Paso 1: probar el ejemplo `1-led-blink` del profesor y adaptar su Makefile a nuestro proyecto | `Makefile`. Lo escribió y revisó el agente principal (Sonnet 5.5), adaptando el del profesor, y luego nos lo explicó | Pendiente de completar |
| 4 | 2026-11-08 | Claude Code (Sonnet 5.5) | Paso 1: adaptar el linker script del ejemplo 24-ADC-1 (RAM de 128K) y verificar la RAM en el RM0390 | `linker_script.ld`. Lo escribió y revisó el agente principal | Pendiente de completar |
| 5 | 2026-11-08 | Claude Code (Sonnet 5.5) | Paso 1: adaptar el `crt0.S` a la F446, con la tabla de vectores completa del RM0390 | `crt0.S`. Lo escribió y revisó el agente principal; la tabla se generó con un script que no está en el repositorio | Pendiente de completar |
| 6 | 2026-11-08 | Claude Code: `programador` (Haiku) y `revisor` (Sonnet) | Paso 1: registros, GPIO y un LED que responde a un botón | `inc/registros_f446.h`, `gpio_config.*` y `main.c`. Los escribió `programador` (Haiku). `revisor` (Sonnet) ayudó a revisar los registros (comprobó los offsets) y no cambió nada; el agente principal hizo una corrección menor | Pendiente de completar |
| 7 | 2026-11-09 | Claude Code: `programador` (Haiku) y `revisor` (Sonnet) | Paso 2: reloj a 84 MHz con el PLL y base de tiempo SysTick de 1 ms | `system_config.*` y `main.c`. Los escribió `programador` (Haiku); `revisor` (Sonnet) los revisó y solo cambió comentarios | Pendiente de completar |
| 8 | 2026-11-09 | Claude Code: `programador` (Haiku) y `revisor` (Sonnet) | Paso 3: los seis botones del shield como entrada con pull-up | `gpio_config.*`, `registros_f446.h` y `main.c`. Los escribió `programador` (Haiku); `revisor` (Sonnet) los revisó sin cambios | Pendiente de completar |
| 9 | 2026-11-09 | Claude Code: `programador` (Haiku) y `revisor` (Sonnet) | Paso 4: primer píxel del panel con GPIO, para entender cómo se comporta la pantalla (datos, latch y filas) | `panel.*`. Los escribió `programador` (Haiku); `revisor` (Sonnet) los revisó sin cambios | Pendiente de completar |
| 10 | 2026-11-09 | Claude Code: `programador` (Haiku) y `revisor` (Sonnet) | Paso 5: framebuffer y refresco del panel con TIM3, con dibujos de prueba para ver cómo se comporta la pantalla | `panel.*` y `main.c`. Los escribió `programador` (Haiku); `revisor` (Sonnet) los revisó sin cambios | Pendiente de completar |
| 11 | 2026-11-09 | Claude Code: `programador` (Haiku) y `revisor` (Sonnet) | Paso 6: biblioteca gráfica mínima (rectángulo, dígitos 3x5 y colores) | `graficos.*`. Los escribió `programador` (Haiku); `revisor` (Sonnet) los revisó sin cambios | Pendiente de completar |
| 12 | 2026-11-09 | Claude Code: `programador` (Haiku) y `revisor` (Sonnet) | Paso 7: mover un punto con los botones y temporizador de software con SysTick | `botones.*` y `main.c`. Los escribió `programador` (Haiku); `revisor` (Sonnet) los revisó sin cambios | Pendiente de completar |
| 13 | 2026-11-10 | Claude Code: `programador` (Haiku) y `revisor` (Sonnet) | Paso 8: Snake básico (serpiente, manzana y fin del juego). Claude nos explicó cómo hacer el arreglo circular del cuerpo | `snake.*`. Los escribió `programador` (Haiku); `revisor` (Sonnet) los revisó sin cambios | Pendiente de completar |
| 14 | 2026-11-17 | Claude Code: `programador` (Haiku) y `revisor` (Sonnet) | Paso 9: generador de números aleatorios (LFSR) y veneno azul. Claude ayudó a explicar y a generar el código. La decisión de sembrar el generador con los milisegundos de la primera pulsación fue nuestra | `aleatorio.*` y `snake.*`. Los escribió `programador` (Haiku); `revisor` (Sonnet) los revisó y solo cambió comentarios | Pendiente de completar |
| 15 | 2026-11-19 | Claude Code: `programador` (Haiku) y `revisor` (Sonnet) | Paso 10: mostrar el puntaje al terminar. Claude ayudó a generar los números de forma más simple, con la fuente de dígitos 3x5 | `graficos.*` y `snake.*`. Los escribió `programador` (Haiku); `revisor` (Sonnet) los revisó sin cambios | Pendiente de completar |
| 16 | 2026-11-20 | Claude Code: `programador` (Haiku) y `revisor` (Sonnet) | Paso 11: segundo panel (32×32). Claude ayudó a mapear los dos paneles, con las mediciones que hicimos nosotros, y con eso supimos cómo expandir la pantalla | `panel.*`, `botones.*`, `snake.*` y `main.c`. Los escribió `programador` (Haiku); `revisor` (Sonnet) los revisó sin cambios | Pendiente de completar |
| 17 | 2026-11-20 | Claude Code (Sonnet 5.5) | Actualizar `docs/mapeo_pixeles.md` con el mapeo de los dos paneles que medimos | `docs/mapeo_pixeles.md`. Lo escribió y revisó el agente principal | Pendiente de completar |
| 18 | 2026-11-22 | Claude Code (Sonnet 5.5) | Ayudó a organizar el repositorio de entrega (carpetas, README y documentos, limpieza del historial de commits). La estructura fue decisión del grupo | Estructura del repositorio, `README.md`, `docs/conexiones.md` y `docs/mapeo_pixeles.md`; sin cambios en el código | Pendiente de completar |

Desde el paso 1 cada entrada indica además qué modelo escribió el código (`programador`), qué modelo lo revisó (`revisor`) y qué correcciones hizo.

## Cómo se completa "Revisión propia"
Por cada entrada, anotar qué se revisó, qué se entendió, qué se cambió y qué dudas quedaron. Es lo que el profesor va a preguntar en la sustentación.
