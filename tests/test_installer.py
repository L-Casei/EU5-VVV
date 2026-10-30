import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.gui_patch import BEGIN, PatchError, blocks, patch_battle_gui
from tools.install import GUI_REL, MANIFEST, ROOT, install
from tools.package import package


# Independently authored structural fixture, not a copied game file.
FIXTURE = '''types SyntheticTypes {
    type sample = widget { tooltip = "a { brace } inside a string" }
}
lateralview = {
    name = "battle_lateralview"
    blockoverride "panel_header" { widget = { text = "Heading" } }
    blockoverride "panel_content" {
        vbox = {
            datacontext = "[BattleView.GetCombat]" # keep this comment
            widget = { size = { 100 100 } }
        }
    }
}
'''


class PatcherTests(unittest.TestCase):
    def test_patch_preserves_source_around_insertion(self):
        result = patch_battle_gui(FIXTURE)
        self.assertEqual(result.count(BEGIN), 1)
        self.assertIn('# keep this comment', result)
        self.assertIn('tooltip = "a { brace } inside a string"', result)
        blocks(result)

    def test_reapplying_is_idempotent(self):
        result = patch_battle_gui(FIXTURE)
        self.assertEqual(patch_battle_gui(result), result)

    def test_crlf_is_preserved(self):
        result = patch_battle_gui(FIXTURE.replace('\n', '\r\n'))
        self.assertNotIn('\n', result.replace('\r\n', ''))

    def test_minified_source(self):
        source = FIXTURE.replace('# keep this comment', '').replace('\n', ' ')
        result = patch_battle_gui(source)
        blocks(result)
        self.assertIn('vvv_battle_entry = {}', result)

    def test_comments_do_not_supply_an_anchor(self):
        source = FIXTURE.replace('datacontext = "[BattleView.GetCombat]"',
                                 '# datacontext = "[BattleView.GetCombat]"')
        with self.assertRaises(PatchError):
            patch_battle_gui(source)

    def test_changed_layout_and_duplicate_roots_fail(self):
        for source in (FIXTURE.replace('panel_content', 'renamed_content'), FIXTURE + FIXTURE):
            with self.subTest(source=source[-60:]), self.assertRaises(PatchError):
                patch_battle_gui(source)

    def test_unbalanced_source_is_rejected(self):
        with self.assertRaises(PatchError):
            patch_battle_gui(FIXTURE[:-3])


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / 'Steam/Europa Universalis V'
        self.source = self.game / 'game' / GUI_REL
        self.source.parent.mkdir(parents=True)
        self.source.write_bytes(b'\xef\xbb\xbf' + FIXTURE.encode())
        self.target = self.root / 'Documents/EU5/mod/EU5-VVV'

    def test_install_reads_game_and_writes_only_destination(self):
        before = self.source.read_bytes()
        result = install(self.game, self.target)
        self.assertEqual(result['status'], 'installed')
        self.assertEqual(self.source.read_bytes(), before)
        self.assertIn(BEGIN, (self.target / GUI_REL).read_text(encoding='utf-8-sig'))
        self.assertTrue((self.target / '.metadata/metadata.json').is_file())
        self.assertEqual(install(self.game, self.target)['status'], 'unchanged')

    def test_unknown_existing_destination_is_preserved(self):
        self.target.mkdir(parents=True)
        marker = self.target / 'personal.txt'
        marker.write_text('keep')
        with self.assertRaises(ValueError):
            install(self.game, self.target)
        self.assertEqual(marker.read_text(), 'keep')

    def test_edited_managed_file_and_unmanaged_file_are_preserved(self):
        install(self.game, self.target)
        gui = self.target / GUI_REL
        original = gui.read_bytes()
        gui.write_bytes(original + b'\n# personal change')
        with self.assertRaises(ValueError):
            install(self.game, self.target)
        self.assertTrue(gui.read_bytes().endswith(b'# personal change'))
        gui.write_bytes(original)
        (self.target / 'personal.txt').write_text('keep')
        with self.assertRaises(ValueError):
            install(self.game, self.target)

    def test_update_refreshes_source_and_keeps_backup(self):
        install(self.game, self.target)
        before = (self.target / GUI_REL).read_bytes()
        self.source.write_bytes(self.source.read_bytes() + b'\n# new hotfix')
        self.assertEqual(install(self.game, self.target)['status'], 'installed')
        self.assertIn(b'new hotfix', (self.target / GUI_REL).read_bytes())
        backups = list((self.target.parent.parent / 'vvv-backups').glob('*.zip'))
        self.assertEqual(len(backups), 1)
        with zipfile.ZipFile(backups[0]) as archive:
            self.assertEqual(archive.read(GUI_REL.as_posix()), before)

    def test_destinations_overlapping_source_are_rejected(self):
        for destination in (self.game, self.game / 'game/new-mod', self.root / 'Steam', ROOT):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                install(self.game, destination)

    def test_manifest_path_escape_is_rejected(self):
        install(self.game, self.target)
        manifest_path = self.target / MANIFEST
        manifest = json.loads(manifest_path.read_text())
        manifest['files']['../../outside.txt'] = 'irrelevant'
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            install(self.game, self.target)

    def test_package_excludes_generated_gui_and_reference_files(self):
        output = package(output=self.root / 'bundle.zip')
        with zipfile.ZipFile(output) as archive:
            names = archive.namelist()
        self.assertIn('EU5-VVV/.metadata/metadata.json', names)
        self.assertIn('EU5-VVV/Install-VVV.cmd', names)
        self.assertNotIn('EU5-VVV/in_game/gui/battle_lateralview.gui', names)
        self.assertFalse(any('local-reference' in n or '__pycache__' in n for n in names))


if __name__ == '__main__':
    unittest.main()
