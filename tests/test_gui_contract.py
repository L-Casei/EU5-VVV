"""Regression checks for the click/handoff failure; these do not run EU5."""
import json
from pathlib import Path
import unittest

from tools.validate import scope_storage_errors, shell_opening_errors

ROOT = Path(__file__).resolve().parents[1]


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
