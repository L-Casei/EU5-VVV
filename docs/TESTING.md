# Prueba en EU5 1.4

Esta alpha necesita su primera prueba real en el juego. Los tests de Python
comprueban el instalador; no ejecutan el motor de EU5.

## Instalación

1. Anota la versión completa y la escala de interfaz.
2. Ejecuta `Install-VVV.cmd` y comprueba que termina sin error.
3. Activa VVV y abre una partida individual de prueba.
4. El mapa sin batalla abierta no debe mostrar botón ni tablero de VVV.

Si el instalador dice que cambió la estructura de la interfaz, conserva el
mensaje y comparte `game/in_game/gui/battle_lateralview.gui` para adaptar el
enganche. No añadas ese archivo generado al repositorio público.

## Ventana y datos

1. Abre una batalla terrestre en la que participes como atacante.
2. Pulsa Mando táctico desde su ventana.
3. Comprueba que tu bando está abajo y el enemigo arriba.
4. Compara los regimientos, cantidades y moral con la interfaz normal.
5. Prueba el scroll con más de seis regimientos y más de un ejército.
6. Repite actuando como defensor y con un aliado en tu bando.
7. Comprueba que la vegetación/topografía del título corresponden a la localidad.
   El fondo de esta alpha es esquemático y no cambia sus reglas según terreno.

## Orden real

1. Pausa una batalla y anota la moral de un regimiento propio que no esté al máximo.
2. Selecciónalo y ejecuta Reagrupar una vez.
3. Sin avanzar el tiempo, comprueba el cambio en su ficha y en los datos nativos.
4. Verifica que el botón se desactiva y aparece el aviso de recuperación.
5. El enemigo, otro regimiento propio y otro ejército en otra batalla deben
   mantener sus valores mientras el juego siga pausado.
6. Cambia de selección y vuelve al primero: la recuperación debe persistir.
7. Tras siete días, comprueba que vuelve a estar disponible si aún puede recibirla.
8. Un regimiento con moral completa, retirado, capturado o ajeno no debe recibirla.

## Ciclo de vida

- Cierra el tablero y la ventana de batalla; no debe reaparecer solo.
- Cambia de batalla: el tablero debe cerrarse al ocultarse su entrada. Si el
  juego reutiliza la ventana sin ocultarla, el tablero debe seguir vinculado a
  su batalla original; nunca debe redirigir órdenes. Al abrirlo desde la nueva
  batalla, la selección anterior debe limpiarse.
- Comprueba refuerzos, retirada de un ejército, fin de batalla y destrucción del
  seleccionado. Los datos ausentes no deben crear errores repetidos.
- Guarda y carga con una selección y una recuperación activas.
- En multijugador el tablero puede observarse, pero las órdenes están desactivadas.

## Qué enviar si falla

- Captura con la ventana completa, versión y escala de interfaz.
- Resultado del instalador.
- Fragmento de `error.log` relacionado con `vvv`, `SubUnit`, `GuiScope` o `Combat`.
  Si usas `-debug_mode`, los registros están en la carpeta de usuario de EU5.

La primera revisión visual y de comportamiento se hará con estas pruebas.
