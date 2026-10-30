# Architecture and current boundaries

## Entry point and UI state

`tools.gui_patch` tokenizes the installed `battle_lateralview.gui`, locates the
named lateralview, its `panel_content` override, and its direct combat-context
container. It inserts only `vvv_battle_entry = {}`. Comments, strings containing
braces, CRLF and whitespace are handled without rewriting vanilla types.
An unfamiliar layout fails with a clear error instead of guessing a hook point.

The entry point receives `BattleView.GetCombat` inside the native lateralview.
`BattleView` is not assumed to be globally accessible from a separate window.
Opening the board validates participation, stores the combat handle on the
issuing country as `vvv_current_battle`, and stores its key in the client-only
`GetVariableSystem`. The independent central window downcasts that saved scope
with `Scope.GetCombat`. Its visibility requires an active land battle, player
participation and a matching open key. The native entry's hide animation and
the board's hide animation clear the local key; no persistent HUD button exists.

Switching the native view must never redirect an already captured combat
handle. Reopening from a different battle explicitly replaces the handle and
clears selection. Exact close/switch animation timing needs an in-game test.

The two sides are rendered through `CombatSide.GetUnits`, then `Unit.GetSubUnits`.
These are real game handles. Cards are grouped by owning army and do not attempt
to change the native flank assignment. Vertical scroll areas retain access to
large armies and reinforcements. Displaying every regiment may need pagination
or aggregation after performance is measured inside EU5.

## Selection and order validation

Selection passes the current battle and clicked regiment to a country-scoped
scripted GUI. The selected subunit handle is stored on the issuing country.
It is revalidated against the currently open combat before showing command
controls, so a selection from a different battle cannot receive an order there.

Both `is_valid` and the effect itself call the validation trigger:

1. A human country in singleplayer issues the action.
2. Both argument handles still exist.
3. The regiment is owned and controlled by the issuer and has positive strength.
4. Its owning army is a land army in this exact combat.
5. The regiment belongs to a fighting section or reserve on one side; a
   retreated/captured regiment must not pass merely because its army is present.

Reagrupar additionally requires missing morale and no cooldown variable. The
effect adds `0.10` morale directly to that one regiment and sets a seven-day
variable on it. The effect is instantaneous, so no temporary discipline/tactics
modifier can leak into a subsequent march or unrelated battle. Repeated clicks
must be rejected by the game-state check after the first successful execution.

The magnitude and clamping behavior of `add_subunit_morale` still require an
in-game check. Do not interpret the order as balanced gameplay yet.

## Authority and future tactical simulation

EU5 owns casualties, reinforcement, retreat and native combat resolution.
VVV currently owns a captured combat handle, selection and a morale order. The board does not yet have
persistent coordinates, pathfinding, arcs, ranges, terrain cells or tactical AI.

Future board positions need an explicit, tested mapping to combat effects.
Moving an icon must never be presented as a native regiment moving freely
through EU5's combat engine. A later custom damage calculation would require a
separate investigation of native damage suppression/reconciliation before use.

Save/load, destroyed handles, changing owners/controllers, battle closure and
the GUI-to-script handle round trip all require runtime validation. No saved
selection should be trusted without the server-side membership checks.

## Version and packaging

The target is EU5 1.4.x. Published export dumps used for API research are a
moving snapshot and do not prove the same behavior in every 1.4 hotfix.
No vanilla file or export dump is included in the repository or distribution.
The generated local override is excluded from git and package creation.
