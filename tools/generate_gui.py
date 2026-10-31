"""Generate a bounded, scroll-free field from the shared layout specification."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_layout(root: Path = ROOT) -> dict:
    return json.loads((root / 'design/battlefield.json').read_text())


def role_position(layout: dict, role: dict, friendly: bool,
                  formation: str = 'line') -> tuple[int, int]:
    if friendly and layout.get('formations'):
        preset = next(f for f in layout['formations'] if f['key'] == formation)
        return tuple(preset['friendly'][role['key']])
    x, y = role['enemy']
    if friendly:
        y = 2 * layout['enemy_mirror_line'] - y - layout['token'][1]
    return x, y


def formation_slots(layout: dict, friendly: bool, formation: str = 'line') -> str:
    result = []
    for role in layout['roles']:
        x, y = role_position(layout, role, friendly, formation)
        result.append(f'''
        widget = {{
            name = "vvv_slot_{'friendly' if friendly else 'enemy'}_{role['key']}"
            position = {{ {x} {y} }}
            size = {{ 112 80 }}
            alwaystransparent = yes
            datamodel = "[CombatSide.GetSubUnitCounts]"
            item = {{
                vvv_formation_token = {{
                    visible = "[And(ObjectsEqual(SubUnitCombatCounts.GetCategory.Self, GetSubUnitCategory('{role['category']}').Self), GreaterThan_int32(SubUnitCombatCounts.GetCount, '(int32)0'))]"
                    blockoverride "vvv_formation_symbol" {{ texture = "gfx/interface/vvv/symbol_{role['icon']}.dds" }}
                    blockoverride "vvv_formation_label" {{ text = "{role['label']}" }}
                }}
            }}
        }}''')
    return '\n'.join(result)


def friendly_formation_types(layout: dict) -> str:
    w, h = layout['canvas']
    return '\n'.join(f'''    type vvv_friendly_formation_{f['key']} = widget {{
        size = {{ {w} {h} }}
        alwaystransparent = yes
{formation_slots(layout, True, f['key'])}
    }}''' for f in layout['formations'])


def friendly_formation_instances(layout: dict) -> str:
    result = []
    for f in layout['formations']:
        chosen = f"GetVariableSystem.HasValue('vvv_field_layout', '{f['key']}')"
        if f['key'] == 'line':
            alternatives = [f"GetVariableSystem.HasValue('vvv_field_layout', '{x['key']}')"
                            for x in layout['formations'] if x['key'] != 'line']
            chosen = f"Not(Or({', '.join(alternatives)}))"
        for own_attacker in (True, False):
            side = 'Attacker' if own_attacker else 'Defender'
            own = 'Combat.GetAttacker.IsPlayerInCombat' if own_attacker else 'Not(Combat.GetAttacker.IsPlayerInCombat)'
            result.append(f'''        vvv_friendly_formation_{f['key']} = {{
            visible = "[And({own}, {chosen})]"
            datacontext = "[Combat.Get{side}]"
        }}''')
    return '\n'.join(result)


def formation_controls(layout: dict) -> str:
    return '\n'.join(f'''        button = {{
            using = button_regular_texture
            using = button_common_template
            position = {{ {368 + i * 78} 81 }} size = {{ 74 22 }}
            text = "{f['label']}"
            onclick = "[GetVariableSystem.Set('vvv_field_layout', '{f['key']}')]"
            tooltip = "VVV_LAYOUT_TT"
            tooltipwidget = {{ BasicFunctionalTooltip = {{}} }}
        }}''' for i, f in enumerate(layout['formations']))


def generate(root: Path = ROOT) -> str:
    layout = load_layout(root)
    w, h = layout['canvas']
    field = layout['field']
    enemy = formation_slots(layout, False)
    # Explicit geometry avoids depending on a fixedgrid/vbox interpretation.
    gui = f'''types VVVTacticalBoardTypes
{{
    type vvv_formation_token = widget {{
        size = {{ 112 80 }}
        scissor = no
        button = {{
            using = button_common_template
            size = {{ 112 80 }}
            enabled = "[And(CombatSide.IsPlayerInCombat, GetScriptedGui('vvv_select_formation').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).AddScope('vvv_battle', Combat.MakeScope).AddScope('vvv_category', SubUnitCombatCounts.GetCategory.MakeScope).End))]"
            onclick = "[GetScriptedGui('vvv_select_formation').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).AddScope('vvv_battle', Combat.MakeScope).AddScope('vvv_category', SubUnitCombatCounts.GetCategory.MakeScope).End)]"
            tooltip = "[SubUnitCombatCounts.GetTooltip]"
            tooltipwidget = {{ BasicFunctionalTooltip = {{}} }}
        }}
        icon = {{
            position = {{ 32 0 }}
            size = {{ 48 48 }}
            alwaystransparent = yes
            texture = "[Select_CString(CombatSide.IsPlayerInCombat, 'gfx/interface/vvv/token_blue.dds', 'gfx/interface/vvv/token_red.dds')]"
        }}
        icon = {{
            position = {{ 28 -4 }}
            size = {{ 56 56 }}
            alwaystransparent = yes
            visible = "[And(CombatSide.IsPlayerInCombat, ObjectsEqual(SubUnitCombatCounts.GetCategory.Self, GetPlayer.MakeScope.GetVariable('vvv_selected_regiment').GetSubUnit.GetDefinition.GetCategory.Self))]"
            texture = "gfx/interface/vvv/token_selected.dds"
        }}
        icon = {{
            position = {{ 42 10 }}
            size = {{ 28 28 }}
            alwaystransparent = yes
            block "vvv_formation_symbol" {{ texture = "gfx/interface/vvv/symbol_pikes.dds" }}
        }}
        icon = {{
            position = {{ 0 46 }}
            size = {{ 112 34 }}
            alwaystransparent = yes
            texture = "gfx/interface/vvv/token_plaque.dds"
        }}
        text_single = {{
            position = {{ 0 49 }}
            size = {{ 112 20 }}
            layoutpolicy_horizontal = fixed
            layoutpolicy_vertical = fixed
            autoresize = no
            align = center|nobaseline
            fontsize = 18
            alwaystransparent = yes
            text = "[SubUnitCombatCounts.GetTotal]"
        }}
        text_single = {{
            position = {{ 0 69 }}
            size = {{ 112 11 }}
            layoutpolicy_horizontal = fixed
            layoutpolicy_vertical = fixed
            autoresize = no
            align = center|nobaseline
            fontsize = 10
            alwaystransparent = yes
            block "vvv_formation_label" {{ text = "VVV_HEAVY_INFANTRY" }}
        }}
    }}

    type vvv_enemy_formation = widget {{
        size = {{ {w} {h} }}
        alwaystransparent = yes
{enemy}
    }}
{friendly_formation_types(layout)}

    type vvv_matchup_side = widget {{
        size = {{ 310 40 }}
        scissor = yes
        country_flag_small_plus = {{
            datacontext = "[CombatSide.GetCountry]"
            position = {{ 0 0 }}
        }}
        text_single = {{
            position = {{ 66 0 }} size = {{ 244 22 }}
            autoresize = no fontsize = 16
            text = "[CombatSide.GetCountry.GetName]"
        }}
        text_single = {{
            position = {{ 66 23 }} size = {{ 244 17 }}
            autoresize = no fontsize = 13
            text = "[CombatSide.GetVisualStrength]"
        }}
    }}

    type vvv_battle_content = widget {{
        size = {{ {w} {h} }}
        alwaystransparent = yes
        visible = "[And3(Combat.IsActive, GetVariableSystem.HasValue('vvv_open_battle', Combat.GetKey), Or(Combat.GetAttacker.IsPlayerInCombat, Combat.GetDefender.IsPlayerInCombat))]"
        icon = {{
            position = {{ {field[0]} {field[1]} }}
            size = {{ {field[2]} {field[3]} }}
            alwaystransparent = yes
            texture = "[Concatenate('gfx/interface/vvv/terrain_', Concatenate(GetPlayer.MakeScope.GetVariable('vvv_terrain_style').GetFlagName, '.dds'))]"
        }}
        text_single = {{
            position = {{ 160 10 }} size = {{ 640 28 }}
            autoresize = no align = center|nobaseline fontsize = 22
            text = "[Combat.GetLocation.GetName]"
        }}
        text_single = {{
            position = {{ 355 37 }} size = {{ 250 19 }}
            autoresize = no align = center|nobaseline fontsize = 12
            text = "[Combat.GetLocation.GetTopography.GetNameWithNoTooltip] · [Combat.GetLocation.GetVegetation.GetNameWithNoTooltip]"
        }}
        vvv_matchup_side = {{
            position = {{ 46 54 }}
            visible = "[Combat.GetAttacker.IsPlayerInCombat]"
            datacontext = "[Combat.GetAttacker]"
        }}
        vvv_matchup_side = {{
            position = {{ 46 54 }}
            visible = "[Not(Combat.GetAttacker.IsPlayerInCombat)]"
            datacontext = "[Combat.GetDefender]"
        }}
        vvv_matchup_side = {{
            position = {{ 608 54 }}
            visible = "[Combat.GetAttacker.IsPlayerInCombat]"
            datacontext = "[Combat.GetDefender]"
        }}
        vvv_matchup_side = {{
            position = {{ 608 54 }}
            visible = "[Not(Combat.GetAttacker.IsPlayerInCombat)]"
            datacontext = "[Combat.GetAttacker]"
        }}
        text_single = {{
            position = {{ 440 57 }} size = {{ 80 22 }}
            autoresize = no align = center|nobaseline fontsize = 16
            text = "VVV_VERSUS"
        }}
        vvv_enemy_formation = {{
            visible = "[Combat.GetAttacker.IsPlayerInCombat]"
            datacontext = "[Combat.GetDefender]"
        }}
        vvv_enemy_formation = {{
            visible = "[Not(Combat.GetAttacker.IsPlayerInCombat)]"
            datacontext = "[Combat.GetAttacker]"
        }}
{friendly_formation_instances(layout)}
{formation_controls(layout)}

        widget = {{
            name = "vvv_order_strip"
            position = {{ 16 516 }} size = {{ 928 88 }}
            scissor = yes
            text_single = {{
                position = {{ 14 12 }} size = {{ 860 22 }}
                autoresize = no fontsize = 14
                visible = "[Not(GetScriptedGui('vvv_select_regiment').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).AddScope('vvv_battle', Combat.MakeScope).AddScope('vvv_regiment', GetPlayer.MakeScope.GetVariable('vvv_selected_regiment').GetSubUnit.MakeScope).End))]"
                text = "VVV_FORMATION_HINT"
            }}
            text_single = {{
                position = {{ 14 43 }} size = {{ 860 18 }}
                autoresize = no fontsize = 12
                visible = "[Not(GetScriptedGui('vvv_select_regiment').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).AddScope('vvv_battle', Combat.MakeScope).AddScope('vvv_regiment', GetPlayer.MakeScope.GetVariable('vvv_selected_regiment').GetSubUnit.MakeScope).End))]"
                text = "VVV_FORMATION_LEGEND"
            }}
            widget = {{
                size = {{ 928 88 }}
                alwaystransparent = yes
                visible = "[GetScriptedGui('vvv_select_regiment').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).AddScope('vvv_battle', Combat.MakeScope).AddScope('vvv_regiment', GetPlayer.MakeScope.GetVariable('vvv_selected_regiment').GetSubUnit.MakeScope).End)]"
                datacontext = "[GetPlayer.MakeScope.GetVariable('vvv_selected_regiment').GetSubUnit]"
                text_single = {{
                    position = {{ 14 9 }} size = {{ 372 22 }}
                    autoresize = no fontsize = 15
                    text = "[SubUnit.GetNameWithNoTooltip]"
                    tooltip = "[SubUnit.GetUITooltip]"
                    tooltipwidget = {{ BasicFunctionalTooltip = {{}} }}
                }}
                text_single = {{
                    position = {{ 14 35 }} size = {{ 372 19 }}
                    autoresize = no fontsize = 12
                    text = "[SubUnit.GetStrength|0] · [SubUnit.GetTypeName]"
                }}
                text_single = {{
                    position = {{ 14 58 }} size = {{ 372 17 }}
                    autoresize = no fontsize = 11
                    text = "[SubUnit.GetMoraleLabel]"
                }}
                button = {{
                    using = button_regular_texture
                    using = button_common_template
                    position = {{ 406 22 }} size = {{ 154 38 }}
                    text = "VVV_RALLY"
                    enabled = "[GetScriptedGui('vvv_rally_regiment').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).AddScope('vvv_battle', Combat.MakeScope).AddScope('vvv_regiment', SubUnit.MakeScope).End)]"
                    onclick = "[GetScriptedGui('vvv_rally_regiment').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).AddScope('vvv_battle', Combat.MakeScope).AddScope('vvv_regiment', SubUnit.MakeScope).End)]"
                    tooltip = "VVV_RALLY_TT"
                    tooltipwidget = {{ BasicFunctionalTooltip = {{}} }}
                }}
                text_single = {{
                    position = {{ 584 13 }} size = {{ 326 20 }}
                    autoresize = no fontsize = 13
                    text = "VVV_RALLY_SHORT"
                }}
                text_single = {{
                    position = {{ 584 43 }} size = {{ 326 19 }}
                    autoresize = no fontsize = 12
                    visible = "[GetPlayer.MakeScope.GetVariableFromVariableMap('vvv_rally_cooldowns', SubUnit.MakeScope).IsSet]"
                    text = "VVV_RALLY_RECOVERING"
                }}
            }}
        }}
    }}
}}

window = {{
    name = "vvv_tactical_board"
    layer = top
    parentanchor = center
    widgetanchor = center
    size = {{ {w} {h} }}
    movable = yes
    resizable = no
    allow_outside = no
    scissor = yes
    filter_mouse = all
    visible = "[GetVariableSystem.Exists('vvv_open_battle')]"
    icon = {{
        size = {{ {w} {h} }}
        alwaystransparent = yes
        texture = "gfx/interface/vvv/battle_frame.dds"
    }}
    widget = {{
        name = "vvv_live_battle_model"
        size = {{ {w} {h} }}
        alwaystransparent = yes
        datamodel = "[GetPlayer.MakeScope.GetList('vvv_board_battles')]"
        item = {{ vvv_battle_content = {{ datacontext = "[Scope.GetCombat]" }} }}
    }}
    widget = {{
        name = "vvv_battle_handoff_status"
        position = {{ 64 170 }} size = {{ 832 160 }}
        scissor = yes
        visible = "[Not(And3(GetPlayer.MakeScope.GetVariable('vvv_current_battle').GetCombat.IsActive, GetVariableSystem.HasValue('vvv_open_battle', GetPlayer.MakeScope.GetVariable('vvv_current_battle').GetCombat.GetKey), Or(GetPlayer.MakeScope.GetVariable('vvv_current_battle').GetCombat.GetAttacker.IsPlayerInCombat, GetPlayer.MakeScope.GetVariable('vvv_current_battle').GetCombat.GetDefender.IsPlayerInCombat)))]"
        text_multi = {{
            size = {{ 820 140 }} autoresize = no fontsize = 16
            text = "VVV_WAITING_BATTLE"
        }}
    }}
    button = {{
        using = button_regular_texture
        using = button_common_template
        position = {{ 860 12 }} size = {{ 76 28 }}
        text = "VVV_CLOSE"
        onclick = "[GetVariableSystem.Clear('vvv_open_battle')]"
    }}
}}
'''
    path = root / 'in_game/gui/vvv_tactical_board.gui'
    path.write_text(gui, encoding='utf-8-sig')
    return gui


if __name__ == '__main__':
    generate()
