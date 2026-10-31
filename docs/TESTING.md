# Prueba en EU5 1.4

El jugador ha confirmado botón, apertura y datos reales en el diseño anterior.
La nueva interfaz 0.2 y la orden necesitan pruebas. Los 27 tests locales no
ejecutan el motor de EU5.

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
   El marco debe abrirse incluso si la captura de datos aún no ha llegado.
   Si ves un aviso de datos pendientes, cierra el panel y vuelve a abrirlo.
   Si el aviso permanece, comparte los errores de VVV del registro del juego.
3. Comprueba que tu bando está abajo y el enemigo arriba.
4. Comprueba que el título solo muestra el lugar y que los dos países tienen
   sus banderas. Compara los totales por categoría con la interfaz normal y
   con el tooltip de cada ficha. Las categorías vacías deben desaparecer.
5. Prueba más de seis regimientos y más de un ejército: debe seguir habiendo
   como máximo seis fichas por bando, sin scroll ni solapamientos. Comprueba
   Línea, Cuña e Izquierda; solo debe cambiar la distribución propia visible.
6. Repite actuando como defensor y con un aliado en tu bando.
7. Comprueba vegetación/topografía y fondo en localidades distintas. La prioridad
   visual es montaña, colinas/meseta, humedal, bosque, seco y llanura. El dibujo
   es esquemático; no añade reglas de terreno.
8. A la escala habitual de interfaz, verifica que cabecera, botones de formación,
   fichas, orden y Cerrar caben completos. Prueba también una escala mayor.
   La ventana mide 960×620 unidades de GUI; las pruebas geométricas no garantizan
   su encaje con cualquier escala o resolución del juego.

## Orden real

1. Pausa una batalla y anota la moral de un regimiento propio que no esté al máximo.
2. Pulsa la ficha de su categoría y comprueba el nombre del regimiento elegido
   abajo. Se prioriza uno propio con moral incompleta y sin recuperación activa.
   Anota los datos de ese regimiento y ejecuta Reagrupar una vez.
3. Sin avanzar el tiempo, comprueba el cambio en su ficha y en los datos nativos.
4. Verifica que el botón se desactiva y aparece el aviso de recuperación.
5. El enemigo, otro regimiento propio y otro ejército en otra batalla deben
   mantener sus valores mientras el juego siga pausado.
6. Pulsa otra categoría y vuelve a la anterior: la recuperación del primer
   regimiento debe persistir. Si hay otro disponible, la selección puede elegirlo;
   comprueba siempre el nombre antes de emitir una orden.
7. Tras siete días, comprueba que vuelve a estar disponible si aún puede recibirla.
8. Un regimiento con moral completa, retirado, capturado o ajeno no debe recibirla.

## Ciclo de vida

- Cierra el tablero con su botón Cerrar; no debe reaparecer solo.
- Cambia de batalla: el tablero sigue vinculado a su batalla original hasta
  cerrarlo o abrirlo desde otra batalla. Nunca debe redirigir órdenes por un
  cambio de selección externa. Al abrirlo desde la nueva batalla, la selección
  anterior debe limpiarse.
- Comprueba refuerzos, retirada de un ejército, fin de batalla y destrucción del
  seleccionado. Al terminar el combate se ocultan sus datos y aparece el aviso;
  cierra el marco explícitamente. Los datos ausentes no deben crear errores repetidos.
- Guarda y carga con una selección y una recuperación activas.
- En multijugador el tablero puede observarse, pero las órdenes están desactivadas.

## Qué enviar si falla

- Captura con la ventana completa, versión y escala de interfaz.
- Resultado del instalador.
- Fragmento de `error.log` relacionado con `vvv`, `SubUnit`, `GuiScope` o `Combat`.
  Si usas `-debug_mode`, los registros están en la carpeta de usuario de EU5.

La primera revisión visual y de comportamiento se hará con estas pruebas.
