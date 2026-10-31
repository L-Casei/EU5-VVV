"""Regression checks for the click/handoff failure; these do not run EU5."""
import json
from pathlib import Path
import unittest
import tempfile

from tools.validate import scope_storage_errors, shell_opening_errors, gui_scope_argument_errors, board_registration_errors, validate

ROOT = Path(__file__).resolve().parents[1]


class BoardRegistrationTests(unittest.TestCase):
    def test_definition_alone_is_not_registered(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            gui = root / 'in_game/gui'
            gui.mkdir(parents=True)
            (gui / 'vvv_tactical_board.gui').write_text('window = { name = "vvv_tactical_board" }')
            self.assertTrue(board_registration_errors(root))
            registry = gui / 'scripted_widgets/vvv_scripted_widgets.txt'
            registry.parent.mkdir()
            registry.write_text('gui/vvv_tactical_board.gui = wrong_name\n')
            self.assertTrue(board_registration_errors(root))
            registry.write_text('gui/vvv_tactical_board.gui = vvv_tactical_board\n')
            self.assertEqual(board_registration_errors(root), [])
            (gui / 'vvv_tactical_board.gui').write_text('window = { name = "renamed_board" }')
            self.assertTrue(board_registration_errors(root))


class OpeningContractTests(unittest.TestCase):
    def test_shell_can_open_while_the_combat_handoff_is_missing(self):
        shell = '''window = {
            name = "vvv_tactical_board"
            visible = "[GetVariableSystem.Exists('vvv_open_battle')]"
            widget = {
                datacontext = "[Scope.GetCombat]"
                visible = "[Combat.IsActive]"
            }
        }'''
        self.assertEqual(shell_opening_errors(shell), [])

    def test_old_coupled_visibility_is_rejected(self):
        old = '''window = {
            name = "vvv_tactical_board"
            datacontext = "[GetPlayer.MakeScope.GetVariable('vvv_current_battle').GetCombat]"
            visible = "[And(Combat.IsActive, GetVariableSystem.Exists('vvv_open_battle'))]"
        }'''
        self.assertTrue(shell_opening_errors(old))

    def test_hide_animation_cannot_cancel_an_open_request(self):
        shell = '''window = {
            name = "vvv_tactical_board"
            visible = "[GetVariableSystem.Exists('vvv_open_battle')]"
            state = {
                name = _hide
                on_start = "[GetVariableSystem.Clear('vvv_open_battle')]"
            }
        }'''
        self.assertTrue(shell_opening_errors(shell))


class GuiScopeArgumentTests(unittest.TestCase):
    def test_log_reported_malformed_argument_is_rejected(self):
        old = '''widget = {
            visible = "[GetScriptedGui('vvv_select_regiment').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).AddScope('vvv_regiment', GetPlayer.MakeScope.GetVariable('vvv_selected_regiment')).End)]"
        }'''
        self.assertEqual(len(gui_scope_argument_errors(old)), 1)

    def test_typed_handle_round_trip_is_accepted(self):
        fixed = '''widget = {
            visible = "[GetScriptedGui('vvv_select_regiment').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).AddScope('vvv_regiment', GetPlayer.MakeScope.GetVariable('vvv_selected_regiment').GetSubUnit.MakeScope).End)]"
        }'''
        self.assertEqual(gui_scope_argument_errors(fixed), [])

    def test_shipped_assets_pass_validation(self):
        self.assertEqual(validate(ROOT), [])


class ScopeStorageContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((ROOT / 'docs/api-scope-storage.json').read_text())

    def test_exported_scope_capability_rejects_old_regiment_cooldown(self):
        old = '''rally = { effect = { scope:vvv_regiment = {
            add_subunit_morale = 0.10
            set_variable = { name = recovery value = yes days = 7 }
        } } }'''
        errors = scope_storage_errors(old, self.contract)
        self.assertEqual(len(errors), 1)
        self.assertIn('sub_unit', errors[0])

    def test_country_can_store_a_cooldown_keyed_by_regiment(self):
        fixed = '''rally = { scope = country effect = {
            scope:vvv_regiment = { add_subunit_morale = 0.10 }
            add_to_variable_map = {
                name = recovery key = scope:vvv_regiment value = yes days = 7
            }
        } }'''
        self.assertEqual(scope_storage_errors(fixed, self.contract), [])


if __name__ == '__main__':
    unittest.main()
