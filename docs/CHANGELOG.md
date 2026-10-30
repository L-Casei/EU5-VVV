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
