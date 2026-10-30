# Veni, Vidi, Vici — EU5

**Target: Europa Universalis V 1.4.x · Version: 0.1.1-alpha**

VVV aims to add a 2D command board opened **from the active battle window**.
Orders on the board act on the regiments participating in that battle; EU5's
normal battle view and native combat continue to exist.

This is an integration alpha. **The battle button has been confirmed in EU5.**
The command board and rally order still need in-game validation. Static checks
and installer tests cannot establish rendering or combat behavior.

## Actualización 0.1.1: botón sin respuesta

La apertura del marco ya no depende de recibir antes los datos del combate.
El botón solicita primero la ventana y después captura la batalla. Si falla
esa captura, el panel muestra un mensaje en lugar de quedarse invisible.
Los datos se crean desde una lista de referencias de combate y la recuperación
de Reagrupar se guarda en el país, con una entrada por regimiento.

Para actualizar: cierra EU5, descarga el ZIP nuevo, extráelo y vuelve a ejecutar
`Install-VVV.cmd` desde esa copia. Después reinicia el juego. El siguiente paso
es comprobar que el clic abre el marco y que las tropas aparecen dentro.

## Qué incorpora esta primera versión

- Tipo de botón **Mando táctico** insertado en el contenido de la ventana de batalla.
- Panel 2D central, enemigo arriba y fuerzas propias abajo, leyendo los ejércitos
  y regimientos de `BattleView.GetCombat`, sin ejércitos de ejemplo en los archivos del juego.
- Fichas con tipo, fuerza y moral; selección de un regimiento propio.
- Orden experimental **Reagrupar**: `+0,10` de moral al regimiento seleccionado,
  con recuperación de siete días por regimiento y validación de dueño,
  controlador, batalla y participación activa.
- Instalador que genera el enganche desde la interfaz de tu instalación.
  Los archivos de EU5 se leen; el resultado se escribe en la carpeta del mod.
- Español e inglés. Sin dependencias de otros mods.

**Todavía no incluye movimiento, orientación, cargas, envolvimientos, terreno
táctico funcional, doctrinas, rasgos nuevos ni IA de órdenes.** La distribución
de fichas es una lista esquemática, no posiciones militares simuladas. La orden
de moral es una prueba del enlace con el combate, no el sistema táctico final.
Las órdenes de esta alpha se desactivan en multijugador.

## Instalar y probar en Windows

1. Descarga este repositorio: **Code → Download ZIP** y extrae la carpeta.
2. Ten instalado **Python 3.10 o posterior**. No hacen falta librerías adicionales
   para instalar. Si tienes el lanzador `py`, el instalador lo utilizará.
3. Cierra EU5 y ejecuta **`Install-VVV.cmd`**. Busca Steam y sus bibliotecas;
   si no encuentra EU5, permite seleccionar la carpeta de instalación.
4. Instala en `Documentos/Paradox Interactive/Europa Universalis V/mod/EU5-VVV`.
   El instalador consulta la ubicación real de Documentos en Windows, incluida
   su redirección a OneDrive.
5. Activa **Veni, Vidi, Vici — Tactical Command** en el gestor de mods y reinicia EU5.
6. En una partida de prueba individual, abre una batalla terrestre propia.
   Busca **Mando táctico** en la parte superior del contenido de su ventana.
7. Abre el tablero, selecciona una ficha propia con moral inferior al máximo
   y prueba **Reagrupar**. Comprueba el resultado siguiendo [esta guía](docs/TESTING.md).

Si el marco muestra un aviso de datos pendientes, ciérralo y vuelve a abrirlo.
Si continúa, comparte el fragmento de `error.log` relacionado con VVV. En esta
versión el cierre del tablero es explícito, mediante su botón Cerrar.

Si no detecta tu juego, abre una terminal en esta carpeta y ejecuta:

```powershell
py -3 -m tools.install --game-dir "D:/SteamLibrary/steamapps/common/Europa Universalis V"
```

Si utilizas otra carpeta de mods, añade `--mod-dir "ruta/completa/EU5-VVV"`.
El instalador rechaza destinos que se solapen con el juego o con el repositorio.
Al actualizar, conserva una copia de la instalación anterior y se detiene si
detecta archivos del mod editados por el usuario.

Vuelve a ejecutar el instalador después de actualizar EU5. El override generado
de `battle_lateralview.gui` es específico de tus archivos. Otros mods que cambien
esa misma interfaz necesitarán una integración conjunta.

## Vista previa del diseño

![Maqueta offline con datos ficticios; no es una captura de EU5](docs/board-preview.png)

La imagen muestra el diseño y las dimensiones previstos. Usa datos de ejemplo
y fuentes aproximadas. El render real, el tamaño de los widgets y su encaje
todavía deben verificarse en el juego.

## Desarrollo

```bash
python -m tools.validate
python -m unittest discover -s tests -v
python -m tools.package
```

Para regenerar las texturas originales y la maqueta:

```bash
python -m pip install "Pillow>=11.3"
python -m tools.build_assets --preview
```

Python es una herramienta de instalación y desarrollo; no se ejecuta dentro de
EU5. Los cambios de juego se implementan con GUI y scripts nativos de EU5.

Consulta [arquitectura y límites](docs/ARCHITECTURE.md), [pruebas en juego](docs/TESTING.md),
[siguientes hitos](docs/ROADMAP.md) y [referencias técnicas](docs/REFERENCES.md).
