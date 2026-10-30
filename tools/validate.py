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


def validate(root: Path = ROOT) -> list[str]:
    errors = []
    contract = json.loads((root / "docs/api-scope-storage.json").read_text(encoding="utf-8"))
    metadata = json.loads((root / ".metadata/metadata.json").read_text(encoding="utf-8-sig"))
    if metadata["game_id"] != "eu5" or metadata["supported_game_version"] != "1.4.*":
        errors.append("Unexpected game target")
    gui = ""
    for directory in ("in_game/gui", "in_game/common/scripted_guis", "in_game/common/scripted_triggers"):
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
