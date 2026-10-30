"""Insert a battle-content button without redistributing a vanilla GUI file."""
from __future__ import annotations

from dataclasses import dataclass
import re


class PatchError(ValueError):
    pass


@dataclass(frozen=True)
class Token:
    value: str
    start: int
    end: int


@dataclass
class Block:
    key: str
    label: str | None
    opening: int
    closing: int
    parent: int | None


def tokens(text: str) -> list[Token]:
    pattern = r'"(?:\\.|[^"\\])*"|#[^\r\n]*|[{}=]|[^\s{}=#"\ufeff]+'
    result = []
    for match in re.finditer(pattern, text):
        if not match.group().startswith("#"):
            result.append(Token(match.group(), match.start(), match.end()))
    return result


def blocks(text: str) -> tuple[list[Token], list[Block]]:
    ts = tokens(text)
    result: list[Block] = []
    stack: list[int] = []
    for i, token in enumerate(ts):
        if token.value == "{":
            if i >= 2 and ts[i - 1].value == "=":
                key, label = ts[i - 2].value, None
            elif i >= 2 and ts[i - 2].value in {"block", "blockoverride", "types"}:
                key, label = ts[i - 2].value, ts[i - 1].value.strip('"')
            else:
                key, label = ts[i - 1].value if i else "", None
            result.append(Block(key, label, i, -1, stack[-1] if stack else None))
            stack.append(len(result) - 1)
        elif token.value == "}":
            if not stack:
                raise PatchError(f"Unexpected closing brace at character {token.start}")
            result[stack.pop()].closing = i
    if stack:
        raise PatchError("Unclosed GUI/script block")
    return ts, result


def direct_fields(ts: list[Token], block: Block) -> dict[str, list[Token]]:
    fields: dict[str, list[Token]] = {}
    depth = 0
    for i in range(block.opening + 1, block.closing):
        if ts[i].value == "{":
            depth += 1
        elif ts[i].value == "}":
            depth -= 1
        elif depth == 0 and i + 2 < block.closing and ts[i + 1].value == "=":
            if ts[i + 2].value != "{":
                fields.setdefault(ts[i].value, []).append(ts[i + 2])
    return fields


BEGIN = "# VVV-BEGIN battle-entry v1"
END = "# VVV-END battle-entry v1"


def patch_battle_gui(text: str) -> str:
    if BEGIN in text:
        if text.count(BEGIN) == text.count(END) == 1 and text.count("vvv_battle_entry = {") == 1:
            return text
        raise PatchError("Incomplete or duplicate VVV injection; use an unmodified source GUI")
    if "vvv_battle_entry" in text:
        raise PatchError("Unknown VVV hook in source GUI")
    ts, bs = blocks(text)
    roots = [i for i, b in enumerate(bs) if b.key == "lateralview" and any(
        t.value.strip('"') == "battle_lateralview"
        for t in direct_fields(ts, b).get("name", [])
    )]
    if len(roots) != 1:
        raise PatchError("Expected one lateralview named battle_lateralview")
    content = [i for i, b in enumerate(bs) if b.parent == roots[0]
               and b.key == "blockoverride" and b.label == "panel_content"]
    if len(content) != 1:
        raise PatchError("Expected one panel_content override in the battle view")
    candidates: list[tuple[int, Token]] = []
    for i, b in enumerate(bs):
        if b.parent != content[0] or b.key not in {"vbox", "widget", "container"}:
            continue
        for field in direct_fields(ts, b).get("datacontext", []):
            if field.value == '"[BattleView.GetCombat]"':
                candidates.append((i, field))
    if len(candidates) != 1:
        raise PatchError("Expected one direct battle-context container in panel_content; layout changed")
    _, field = candidates[0]
    line_start = text.rfind("\n", 0, field.start) + 1
    indent = re.match(r"[ \t]*", text[line_start:]).group()
    newline = "\r\n" if "\r\n" in text else "\n"
    # Insert at the end of the assignment itself, not after an arbitrary next
    # newline: minified files and trailing comments both remain valid.
    injection = newline + newline.join(indent + line for line in (
        BEGIN,
        "vvv_battle_entry = {}",
        END,
    )) + newline + indent
    patched = text[:field.end] + injection + text[field.end:]
    blocks(patched)
    return patched
