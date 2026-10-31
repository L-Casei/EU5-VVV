# Architecture and current boundaries

## Entry point and UI state

`tools.gui_patch` tokenizes the installed `battle_lateralview.gui`, locates the
named lateralview, its `panel_content` override, and its direct combat-context
container. It inserts only `vvv_battle_entry = {}`. Comments, strings containing
braces, CRLF and whitespace are handled without rewriting vanilla types.
An unfamiliar layout fails with a clear error instead of guessing a hook point.

The entry point receives `BattleView.GetCombat` inside the native lateralview.
`BattleView` is not assumed to be globally accessible from a separate window.
The first click action stores the battle key in the client-only
`GetVariableSystem`. The independent shell's visibility depends only on this
UI flag, so it can open while the game-state handoff is still absent. Neither
the shell nor the entry clears that flag from a hide animation. The close
button clears it explicitly; no permanent HUD button exists.

The second click action validates country participation, stores the combat
handle on the country as `vvv_current_battle`, and replaces `vvv_board_battles`
with a one-item variable list. A widget datamodel creates the typed content
from that list using `Scope.GetCombat`. The shell itself never caches an empty
combat data context at startup. Live content requires an active matching combat
and player participation; a separate status message covers missing/stale data.

Switching the native view must never redirect an already captured combat
handle. Reopening from a different battle explicitly replaces the handle and
clears selection. Until lifecycle behavior is verified, closing is explicit.
If the captured battle ends, live data is hidden and the status message appears.

The standalone window is registered in `gui/scripted_widgets`. Saved regiment
arguments to `GuiScope.AddScope` terminate with `GetSubUnit.MakeScope`; a bare
`Scope.GetVariable` is a context promote and was rejected by the engine.

The 960×620 canvas has a fixed 928×392 field and a clipped bottom order strip.
Both sides use native `CombatSide.GetSubUnitCounts` aggregates, with one visible
token for each of the six vanilla land categories. `GetTotal` supplies the troop
total as native text, `GetCount` controls empty-category visibility and the
native tooltip provides composition details. Counts include allied troops;
order selection considers only regiments owned and controlled by the player.
There are no scroll areas or per-regiment grids. Category glyphs distinguish
roles, not every individual regiment definition within a category.

`design/battlefield.json` supplies bounded positions for Line, Wedge and Left
layouts. `tools.generate_gui` generates the GUI and the offline preview uses
the same coordinates. The choice is client UI state, shared across opened
boards during that session. These layouts rearrange friendly tokens only;
there are no saved regiment coordinates and no native flank reassignment.

Opening captures a terrain-style flag on the country from the combat location:
mountains, hills/plateau, wetlands, woods/forest/jungle, dry or plains, in that
priority order. The field texture is an original schematic backdrop. It does
not claim to reproduce local terrain geometry or add terrain combat rules.
Native country-flag widgets render the leading countries' flags. The header
shows location, countries, strengths, topography and vegetation.

## Selection and order validation

Selection passes the current battle and clicked category to a country-scoped
scripted GUI. It scans active sections on both sides for an owned, controlled,
positive-strength regiment of that category. It prefers missing morale without
a rally cooldown, then any missing-morale regiment, then any active regiment.
The selected subunit handle is stored on the issuing country. The order strip
names that individual target; clicking the category does not issue a group order.
It is revalidated against the currently open combat before showing command
controls, so a selection from a different battle cannot receive an order there.

Both `is_valid` and the effect itself call the validation trigger:

1. A human country in singleplayer issues the action.
2. Both argument handles still exist.
3. The regiment is owned and controlled by the issuer and has positive strength.
4. Its owning army is a land army in this exact combat.
5. The regiment belongs to a fighting section or reserve on one side; a
   retreated/captured regiment must not pass merely because its army is present.

Reagrupar additionally requires missing morale and no active entry for the
regiment in the issuing country's `vvv_rally_cooldowns` map. The effect adds
`0.10` morale directly to that regiment and adds a seven-day map entry keyed by
its scope. Exported EU5 scope capabilities mark `sub_unit` as unable to store
variables; all persistent state therefore stays on the country. The effect is
instantaneous, so no temporary discipline/tactics
modifier can leak into a subsequent march or unrelated battle. Repeated clicks
must be rejected by the game-state check after the first successful execution.

The magnitude and clamping behavior of `add_subunit_morale` still require an
in-game check. Do not interpret the order as balanced gameplay yet.

## Authority and future tactical simulation

EU5 owns casualties, reinforcement, retreat and native combat resolution.
VVV currently owns a captured combat handle, selection and a morale order.
The board does not yet have persistent regiment coordinates, free placement,
pathfinding, arcs, ranges, terrain cells or tactical AI.

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
