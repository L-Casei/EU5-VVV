"""Static asset/script checks. These are not a substitute for an EU5 runtime test."""
from __future__ import annotations

import json
from pathlib import Path
import re
import struct
from .gui_patch import blocks, direct_fields

ROOT = Path(__file__).resolve().parents[1]


def scope_storage_errors(text: str, contract: dict) -> list[str]:
    """Check writes against EU5's exported Stores Variables capability."""
    _, parsed = blocks(text)
    errors = []
    stores = contract["stores_variables"]
    arguments = contract["vvv_scope_arguments"]
    write_operations = {"set_variable", "add_to_variable_list", "add_to_variable_map"}
    for block in parsed:
        if block.key not in write_operations:
            continue
        parent = block.parent
        while parent is not None:
            ancestor = parsed[parent]
            if ancestor.key.startswith("scope:"):
                alias = ancestor.key.removeprefix("scope:")
                kind = arguments.get(alias)
                if kind in stores and not stores[kind]:
                    errors.append(f"{block.key} cannot store data on {alias} ({kind})")
                break
            parent = ancestor.parent
    return errors


def gui_scope_argument_errors(text: str) -> list[str]:
    """EU5 GetVariable is a promote; it cannot terminate an AddScope argument.

    This form produces a malformed token and prevents the board loading.
    Downcast the saved handle and use its MakeScope function instead.
    """
    expressions = [t.value for t in blocks(text)[0] if t.value.startswith('"[')]
    invalid = re.compile(
        r"\.AddScope\(\s*'[^']+'\s*,\s*[^\n]*?"
        r"\.GetVariable\(\s*'[^']+'\s*\)\s*\)"
    )
    return ["AddScope argument ends in GetVariable promote; use a typed MakeScope"
            for expression in expressions if invalid.search(expression)]


def shell_opening_errors(text: str) -> list[str]:
    """The board shell must be renderable before any game-state handoff."""
    ts, parsed = blocks(text)
    errors = []
    for index, block in enumerate(parsed):
        if block.key != "window" or block.parent is not None:
            continue
        fields = direct_fields(ts, block)
        if not any(t.value.strip('"') == "vvv_tactical_board" for t in fields.get("name", [])):
            continue
        visibility = " ".join(t.value for t in fields.get("visible", []))
        if not visibility or "GetVariableSystem.Exists" not in visibility:
            errors.append("Board shell must open from a client-only UI flag")
        if any(part in visibility for part in ("Combat.", "GetScriptedGui", "GetPlayer.", "GuiScope")):
            errors.append("Board shell visibility waits for a game-state handoff")
        if "datacontext" in fields:
            errors.append("Board shell must not capture an empty combat context at startup")
        for child in parsed:
            if child.parent != index or child.key != "state":
                continue
            state = direct_fields(ts, child)
            if any(t.value.strip('"') == "_hide" for t in state.get("name", [])):
                if any("vvv_open_battle" in t.value for t in state.get("on_start", [])):
                    errors.append("Board hide animation resets its own opening flag")
    return errors


def board_registration_errors(root: Path) -> list[str]:
    """A parsed standalone window still needs a scripted_widgets registration."""
    expected = ("gui/vvv_tactical_board.gui", "vvv_tactical_board")
    registrations = []
    for path in (root / "in_game/gui/scripted_widgets").glob("*.txt"):
        text = path.read_text(encoding="utf-8-sig")
        registrations.extend(re.findall(r"^\s*([^#\s=]+)\s*=\s*([^#\s]+)\s*(?:#.*)?$", text, re.M))
    if registrations.count(expected) != 1:
        return ["Tactical board needs exactly one scripted_widgets registration"]
    path = root / "in_game" / expected[0]
    if not path.is_file():
        return ["Registered tactical board GUI file is missing"]
    ts, parsed = blocks(path.read_text(encoding="utf-8-sig"))
    matches = [b for b in parsed if b.parent is None and b.key == "window"
               and any(t.value.strip('"') == expected[1]
                       for t in direct_fields(ts, b).get("name", []))]
    return [] if len(matches) == 1 else ["Registered tactical board window name does not match"]


def validate(root: Path = ROOT) -> list[str]:
    errors = []
    errors.extend(board_registration_errors(root))
    contract = json.loads((root / "docs/api-scope-storage.json").read_text(encoding="utf-8"))
    metadata = json.loads((root / ".metadata/metadata.json").read_text(encoding="utf-8-sig"))
    if metadata["game_id"] != "eu5" or metadata["supported_game_version"] != "1.4.*":
        errors.append("Unexpected game target")
    gui = ""
    for directory in ("in_game/gui", "in_game/common/scripted_guis", "in_game/common/scripted_triggers", "in_game/common/scripted_effects"):
        for path in (root / directory).glob("*"):
            if path.suffix not in {".gui", ".txt"}:
                continue
            text = path.read_text(encoding="utf-8-sig")
            try:
                blocks(text)
                if path.suffix == ".txt":
                    errors.extend(f"{path}: {e}" for e in scope_storage_errors(text, contract))
                else:
                    errors.extend(f"{path}: {e}" for e in shell_opening_errors(text))
                    errors.extend(f"{path}: {e}" for e in gui_scope_argument_errors(text))
            except ValueError as exc:
                errors.append(f"{path}: {exc}")
            if path.suffix == ".gui":
                gui += text
    for path in (root / "in_game/localization").glob("*/*.yml"):
        if not path.read_bytes().startswith(b"\xef\xbb\xbf"):
            errors.append(f"Missing UTF-8 BOM: {path}")
        text = path.read_text(encoding="utf-8-sig")
        keys = re.findall(r'^\s+(VVV_\w+):', text, re.M)
        if len(keys) != len(set(keys)):
            errors.append(f"Duplicate localization key: {path}")
        missing = set(re.findall(r'"(VVV_[A-Z_]+)"', gui)) - set(keys)
        if missing:
            errors.append(f"Missing localization in {path}: {sorted(missing)}")
    for rel in set(re.findall(r"gfx/interface/vvv/[a-z_]+\.dds", gui)):
        path = root / "in_game" / rel
        if not path.is_file():
            errors.append(f"Missing texture: {rel}")
            continue
        header = path.read_bytes()[:128]
        if len(header) != 128 or header[:4] != b"DDS ":
            errors.append(f"Invalid DDS: {rel}")
            continue
        height, width = struct.unpack_from("<II", header, 12)
        if width % 4 or height % 4 or header[84:88] not in {b"DXT1", b"DXT5"}:
            errors.append(f"Unexpected DDS format/dimensions: {rel}")
    # Terrain textures are selected by a validated data key at runtime, so their
    # individual paths are not literal references in the generated GUI.
    layout_path = root / 'design/battlefield.json'
    if layout_path.is_file():
        layout = json.loads(layout_path.read_text())
        for style in layout['terrain_styles']:
            rel = f'in_game/gfx/interface/vvv/terrain_{style}.dds'
            path = root / rel
            if not path.is_file():
                errors.append(f'Missing terrain texture: {rel}')
            else:
                header = path.read_bytes()[:128]
                if header[:4] != b'DDS ' or header[84:88] != b'DXT1':
                    errors.append(f'Invalid terrain texture: {rel}')
    entry = (root / "in_game/gui/vvv_battle_button.gui").read_text(encoding="utf-8-sig")
    if re.search(r'^\s*(?:window|widget)\s*=\s*{', entry, re.M):
        errors.append("Battle entry must define a type, not a standalone HUD widget")
    return errors


def main():
    errors = validate()
    if errors:
        raise SystemExit("\n".join(errors))
    print("Metadata, balanced blocks, localizations and DDS references: OK")
    print("EU5 runtime behavior: pending in-game validation")


if __name__ == "__main__":
    main()
