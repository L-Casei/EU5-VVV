"""Geometry regressions for the clipped command panel and overlapping troops."""
from pathlib import Path
import unittest

from tools.generate_gui import load_layout, role_position

ROOT = Path(__file__).resolve().parents[1]


class BattlefieldGeometryTests(unittest.TestCase):
    def setUp(self):
        self.layout = load_layout()

    def test_field_orders_and_tokens_fit_the_compact_canvas(self):
        width, height = self.layout['canvas']
        self.assertLessEqual(width, 960)
        self.assertLessEqual(height, 620)
        for name in ('field', 'orders'):
            x,y,w,h = self.layout[name]
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(x+w, width)
            self.assertLessEqual(y+h, height)
        fx,fy,fw,fh = self.layout['field']
        tw,th = self.layout['token']
        for formation in self.layout['formations']:
            for friendly in (False,True):
                for role in self.layout['roles']:
                    with self.subTest(formation=formation['key'],friendly=friendly,role=role['key']):
                        x,y = role_position(self.layout,role,friendly,formation['key'])
                        self.assertGreaterEqual(x,fx)
                        self.assertGreaterEqual(y-4,fy)  # selected-ring glow
                        self.assertLessEqual(x+tw,fx+fw)
                        self.assertLessEqual(y+th,fy+fh)

    def test_formation_tokens_never_overlap(self):
        tw,th = self.layout['token']
        for formation in self.layout['formations']:
            positions=[(friendly,role['key'],*role_position(self.layout,role,friendly,formation['key']))
                       for friendly in (False,True) for role in self.layout['roles']]
            for i,a in enumerate(positions):
                for b in positions[i+1:]:
                    _,_,ax,ay=a
                    _,_,bx,by=b
                    separated=ax+tw<=bx or bx+tw<=ax or ay+th<=by or by+th<=ay
                    self.assertTrue(separated,f"{formation['key']}: {a[:2]} overlaps {b[:2]}")

    def test_all_six_vanilla_land_categories_have_distinct_roles(self):
        categories=[role['category'] for role in self.layout['roles']]
        self.assertEqual(set(categories),{
            'army_light_infantry','army_heavy_infantry','army_light_cavalry',
            'army_heavy_cavalry','army_artillery','army_auxiliary'})
        self.assertEqual(len(categories),len(set(categories)))
        self.assertEqual(len({r['icon'] for r in self.layout['roles']}),6)

    def test_scroll_roster_and_unbounded_regiment_grid_are_absent(self):
        gui=(ROOT/'in_game/gui/vvv_tactical_board.gui').read_text(encoding='utf-8-sig')
        self.assertNotIn('scrollarea',gui)
        self.assertNotIn('scrollwidget',gui)
        self.assertNotIn('fixedgridbox',gui)
        self.assertNotIn('[Unit.GetSubUnits]',gui)
        self.assertNotIn('VVV_BOARD_TITLE',gui)
        self.assertIn('[CombatSide.GetSubUnitCounts]',gui)
        self.assertIn('[SubUnitCombatCounts.GetTotal]',gui)


if __name__=='__main__':
    unittest.main()
