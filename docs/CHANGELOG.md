# 0.2.0-alpha (2026-10-31)

- Replace the left-stacked scroll roster with a 960×620 battlefield and bounded
  bottom order strip. Show only the location as title, native country flags,
  country names and strengths.
- Render up to six live category totals on each side with original circular
  tokens and distinct light/heavy infantry, cavalry, artillery and support glyphs.
- Add six original terrain backdrops selected from the combat location.
- Add Line, Wedge and Left visual layouts. These do not change native combat
  positions or mechanics; free regiment placement remains a later milestone.
- Category selection resolves an own active regiment, preferring one eligible
  for rally. The order strip names the individual target; rally remains a
  single-regiment effect with its existing ownership and membership checks.
- Generate GUI and artwork from a shared layout file. Add bounds and overlap
  regressions for all layouts. Validation and 27 local tests pass.
- Player confirmed the preceding board opens and shows real troops. This new
  rendering, category selection and rally behavior await an EU5 runtime check.

## Preserved board registration fix

- Register `vvv_tactical_board` in `gui/scripted_widgets`. The standalone
  definition was parsed but never registered for creation in the in-game UI.
- Validate the registration, target file and window name, and verify that
  installation includes the registration. The previous expression fix alone
  did not resolve the missing window. Player subsequently confirmed opening.

## Preserved board load fix

- Fix the two selection visibility expressions that EU5 rejected as malformed
  tokens in `error.log` at 21:46:07 on 2026-10-30. `Scope.GetVariable` is a
  context promote, not a terminal data function: resolve `GetSubUnit.MakeScope`
  before passing the saved regiment to `GuiScope.AddScope`.
- Add validation and regression coverage for the rejected argument form.
- Static validation only; the game was not started for this fix.

# 0.1.1-alpha

- Make the board shell open from client UI state before the scripted combat
  handoff completes. Remove hide-state callbacks that could clear its request.
- Build live combat content from a typed variable-list item. Show a visible
  status message if data is missing or no longer matches the requested battle.
- Validate board access against participating countries; keep order ownership
  and active-regiment checks separate.
- Move rally cooldowns to a country map keyed by regiment. EU5 subunit scopes
  do not support storing variables.
- Add regression checks for shell/game-state coupling, self-clearing visibility
  and writes to unsupported scopes. Read installed version from mod metadata.

Local result: 19 checks/tests pass. In-game opening, data handoff and rally
behavior are still pending validation. Free movement is not part of this patch.
