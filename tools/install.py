"""Install VVV using the battle GUI from the player's own EU5 installation."""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import zipfile

from .gui_patch import PatchError, patch_battle_gui

ROOT = Path(__file__).resolve().parents[1]
GUI_REL = Path("in_game/gui/battle_lateralview.gui")
MANIFEST = "vvv-install.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def documents_dir() -> Path:
    if sys.platform == "win32":
        buffer = ctypes.create_unicode_buffer(32768)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buffer) == 0:
            return Path(buffer.value)
    return Path.home() / "Documents"


def default_mod_dir() -> Path:
    return documents_dir() / "Paradox Interactive/Europa Universalis V/mod/EU5-VVV"


def game_root(path: Path) -> Path | None:
    path = path.expanduser().resolve()
    if (path / "game" / GUI_REL).is_file():
        return path
    if path.name == "game" and (path / GUI_REL).is_file():
        return path.parent
    return None


def steam_candidates() -> list[Path]:
    roots = []
    if sys.platform == "win32":
        import winreg
        for hive, key, field in (
            (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
        ):
            try:
                with winreg.OpenKey(hive, key) as handle:
                    roots.append(Path(winreg.QueryValueEx(handle, field)[0]))
            except OSError:
                pass
        roots.append(Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Steam")
    else:
        roots.extend([Path.home() / ".local/share/Steam", Path.home() / ".steam/steam"])
    libraries = list(roots)
    for root in roots:
        vdf = root / "steamapps/libraryfolders.vdf"
        if vdf.is_file():
            libraries.extend(Path(p.replace("\\\\", "\\")) for p in re.findall(
                r'"path"\s+"([^"\r\n]+)"', vdf.read_text(encoding="utf-8", errors="replace")
            ))
    return list(dict.fromkeys(p / "steamapps/common/Europa Universalis V" for p in libraries))


def locate_game(explicit: Path | None) -> Path:
    if explicit:
        found = game_root(explicit)
        if not found:
            raise ValueError(f"No game/{GUI_REL.as_posix()} in {explicit}")
        return found
    found = list(dict.fromkeys(r for p in steam_candidates() if (r := game_root(p))))
    if len(found) == 1:
        return found[0]
    if sys.platform == "win32":
        import tkinter
        from tkinter import filedialog
        root = tkinter.Tk()
        root.withdraw()
        chosen = filedialog.askdirectory(title="Selecciona la carpeta Europa Universalis V")
        root.destroy()
        if chosen and (result := game_root(Path(chosen))):
            return result
    raise ValueError('Specify --game-dir "D:/SteamLibrary/steamapps/common/Europa Universalis V"')


def installation_files(root: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for dirname in (".metadata", "in_game"):
        for path in sorted((root / dirname).rglob("*")):
            if path.is_file() and path.relative_to(root) != GUI_REL:
                files[path.relative_to(root).as_posix()] = path.read_bytes()
    return files


def install(game_dir: Path, mod_dir: Path, source_root: Path = ROOT) -> dict:
    game_dir = game_root(game_dir)
    if game_dir is None:
        raise ValueError("EU5 installation not found")
    target = mod_dir.expanduser().resolve()
    # Never allow the destination to overlap the source game/repository.
    for protected in (game_dir, source_root.resolve()):
        if target == protected or protected in target.parents or target in protected.parents:
            raise ValueError("The mod destination must be separate from the game and source repository")
    source = game_dir / "game" / GUI_REL
    source_bytes = source.read_bytes()
    patched = patch_battle_gui(source_bytes.decode("utf-8-sig"))
    desired = installation_files(source_root)
    desired[GUI_REL.as_posix()] = b"\xef\xbb\xbf" + patched.encode("utf-8")
    previous = None
    if target.exists():
        manifest_path = target / MANIFEST
        if not manifest_path.is_file():
            raise ValueError(f"Destination already exists without a VVV manifest: {target}")
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        if previous.get("mod_id") != "eu5_vvv":
            raise ValueError("Destination does not identify itself as a VVV installation")
        managed = previous.get("files", {})
        for rel, digest in managed.items():
            path = target / rel
            if Path(rel).is_absolute() or target not in path.resolve().parents:
                raise ValueError("Invalid path in installation manifest")
            if not path.is_file() or sha256(path.read_bytes()) != digest:
                raise ValueError(f"Installed file was edited or removed; preserving it: {path}")
        actual = {p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()}
        if actual - set(managed) - {MANIFEST}:
            raise ValueError("Destination contains unmanaged files; move them before updating")
        if previous.get("source_sha256") == sha256(source_bytes) and {
            rel: sha256(data) for rel, data in desired.items()
        } == managed:
            return {"status": "unchanged", "target": str(target)}
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="vvv-stage-", dir=target.parent))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    manifest = {
        "mod_id": "eu5_vvv",
        "version": json.loads(desired[".metadata/metadata.json"].decode("utf-8-sig"))["version"],
        "source_gui": str(source),
        "source_sha256": sha256(source_bytes),
        "installed_utc": stamp,
        "files": {rel: sha256(data) for rel, data in desired.items()},
    }
    old = None
    try:
        for rel, data in desired.items():
            dest = stage / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        (stage / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        if target.exists():
            # Keep update backups outside the mod scan directory.
            backups = target.parent.parent / "vvv-backups"
            backups.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(backups / f"EU5-VVV-{stamp}.zip", "w", zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(target.rglob("*")):
                    if path.is_file():
                        archive.write(path, path.relative_to(target))
            old = target.with_name(target.name + ".vvv-old-" + stamp)
            target.rename(old)
        try:
            stage.rename(target)
        except OSError:
            if old is not None:
                old.rename(target)
            raise
        if old is not None:
            shutil.rmtree(old)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return {"status": "installed", "target": str(target), "source_sha256": manifest["source_sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path)
    parser.add_argument("--mod-dir", type=Path, default=default_mod_dir())
    args = parser.parse_args()
    try:
        result = install(locate_game(args.game_dir), args.mod_dir)
    except (OSError, ValueError, PatchError) as exc:
        print(f"VVV: {exc}", file=sys.stderr)
        return 1
    print(f"VVV {result['status']}: {result['target']}")
    print("Activa Veni, Vidi, Vici en el gestor de mods y reinicia EU5.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
