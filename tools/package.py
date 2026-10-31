"""Build a source/install bundle; the local vanilla override is never included."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def package(root: Path = ROOT, output: Path | None = None) -> Path:
    version = json.loads((root / ".metadata/metadata.json").read_text(encoding="utf-8-sig"))["version"]
    output = output or root / "dist" / f"EU5-VVV-{version}.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    files = []
    for directory in (".metadata", "in_game", "tools", "docs", "design"):
        files.extend(p for p in (root / directory).rglob("*") if p.is_file())
    files.extend(root / name for name in ("README.md", "Install-VVV.cmd"))
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            rel = path.relative_to(root)
            if "__pycache__" in rel.parts or path.suffix == ".pyc":
                continue
            if rel.as_posix() == "in_game/gui/battle_lateralview.gui":
                continue
            archive.write(path, Path("EU5-VVV") / rel)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    print(package(output=parser.parse_args().output))


if __name__ == "__main__":
    main()
