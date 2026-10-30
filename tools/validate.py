"""Static asset/script checks. These are not a substitute for an EU5 runtime test."""
from __future__ import annotations

import json
from pathlib import Path
import re
import struct
from .gui_patch import blocks

ROOT = Path(__file__).resolve().parents[1]


def validate(root: Path = ROOT) -> list[str]:
    errors = []
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
