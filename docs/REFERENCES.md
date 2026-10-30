# Technical references

Research date: 2026-10-30. These are references, not VVV dependencies.

- [EU5 Modding Co-op: generated script/API documentation](https://github.com/Europa-Universalis-5-Modding-Co-op/modding-digests/tree/main/current_docs).
  Names checked: `BattleView.GetCombat`, `Combat.MakeScope`, `CombatSide.GetUnits`,
  `Unit.GetSubUnits`, `SubUnit.MakeScope`, `Scope.GetSubUnit`, `owning_unit`,
  `combat`, `any_center`, `any_left_flank`, `any_right_flank`, `any_reserves`,
  `subunit_morale_percentage`, `add_subunit_morale`, and timed `set_variable`.
  `event_scopes.log` marks `country` as able to store variables and `sub_unit`
  as unable to do so. The small capability snapshot used by validation is in
  [api-scope-storage.json](api-scope-storage.json). Rally now uses a country
  variable map keyed by the subunit, with timed entries.
- [Community Mod Framework](https://github.com/Europa-Universalis-5-Modding-Co-op/community-mod-framework).
  Working patterns for `GetVariableSystem`, `GuiScope.SetRoot/AddScope/End`,
  scripted GUI validation/execution, native buttons, scroll areas and grids.
  VVV does not require or bundle CMF.
- [CMF typed-handle datamodel example](https://github.com/Europa-Universalis-5-Modding-Co-op/community-mod-framework/blob/main/submods/cmf-engine-test/in_game/gui/et_bt_windows.gui).
  Reference pattern for a variable-list datamodel whose items downcast a saved
  scope into a typed widget context. VVV applies that shape to a combat handle;
  this still needs verification with EU5 combat scopes specifically.
- [Community Mod Toolkit](https://github.com/Europa-Universalis-5-Modding-Co-op/community-mod-toolkit).
  EU5 `.metadata/metadata.json` structure.
- [Glorp UI battle view](https://github.com/clickypoo/EU5.Glorp.UI/blob/master/in_game/gui/battle_lateralview.gui).
  Independently inspected layout precedent for a named `lateralview`, its
  `panel_content`, and `BattleView.GetCombat` data context. Used to exercise
  the patcher locally; the source file is not redistributed with VVV.

VVV contains original UI layout, artwork, scripts and tools. Its small synthetic
test fixtures describe layout structure and are not complete vanilla GUI files.

## Evidence limits

The published export snapshot may reflect a later 1.4 hotfix than the user's
installation. An identifier appearing in a dump establishes availability in that
snapshot; it does not establish lifecycle safety, scope round-trip behavior,
rendering, ordering, performance or semantics in a running game.

The generated board preview uses example values and a neutral schematic field.
It is not a screenshot and does not demonstrate game integration.
