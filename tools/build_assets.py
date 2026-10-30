"""Draw original UI textures and an explicitly labelled offline layout preview.

Pillow is needed only to regenerate artwork. It is not needed to install/play.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import random
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "in_game/gfx/interface/vvv"


def board() -> Image.Image:
    image = Image.new("RGB", (1104, 704), "#252c2b")
    d = ImageDraw.Draw(image)
    d.rectangle((5, 5, 1098, 698), outline="#ac9870", width=2)
    d.rectangle((11, 11, 1092, 692), outline="#53605a")
    d.line((25, 82, 1078, 82), fill="#857b5e", width=1)
    d.rectangle((20, 94, 804, 615), fill="#53674d", outline="#9f9b77", width=2)
    # A neutral schematic field; no invented river, trees, elevation or native
    # flank boundaries are presented as real combat geometry.
    rng = random.Random(1337)
    for _ in range(6500):
        x, y = rng.randrange(23, 801), rng.randrange(97, 612)
        shade = rng.choice(["#53674d", "#55694f", "#50644a", "#576b51"])
        d.line((x, y, x + 3, y + 1), fill=shade)
    for x in range(27, 804, 122):
        d.line((x, 120, x, 604), fill="#5c6e54")
    for y in (124, 210, 296, 394, 480, 566):
        d.line((30, y, 793, y), fill="#5c6e54")
    d.rectangle((23, 334, 801, 361), fill="#425442")
    d.line((34, 334, 789, 334), fill="#8a9676")
    d.line((34, 361, 789, 361), fill="#8a9676")
    d.rectangle((818, 94, 1081, 615), fill="#303a37", outline="#69776a")
    d.line((832, 130, 1067, 130), fill="#6b795f")
    d.line((28, 625, 1076, 625), fill="#646e60")
    return image


def card(color: str, border: str) -> Image.Image:
    image = Image.new("RGB", (112, 80), color)
    d = ImageDraw.Draw(image)
    d.rectangle((0, 0, 111, 79), outline=border, width=2)
    d.rectangle((4, 4, 107, 75), outline="#77877b")
    d.line((7, 54, 104, 54), fill="#79877b")
    return image


def font(size: int, serif: bool = False):
    name = "DejaVuSerif.ttf" if serif else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default(size=size)


def preview(image: Image.Image, cards: dict) -> Image.Image:
    image = image.copy()
    d = ImageDraw.Draw(image)
    white, gold = "#e9e7d4", "#cfbe91"
    def text(x, y, value, size=14, fill=white, serif=False):
        d.text((x, y), value, font=font(size, serif), fill=fill)
    text(28, 16, "VENI, VIDI, VICI", 25, gold, True)
    text(30, 51, "Batalla de ejemplo · Llanura · Pradera", 14)
    text(1030, 25, "Cerrar", 12)
    text(34, 101, "FUERZAS ENEMIGAS", 12, gold)
    text(34, 126, "Ejército enemigo — 1.050", 15)
    text(34, 153, "Ejército de campaña", 12)
    text(34, 341, "ORDEN DE BATALLA", 12, gold)
    text(34, 372, "NUESTRAS FUERZAS", 12, gold)
    text(34, 396, "Nuestro ejército — 1.500", 15)
    text(34, 423, "Ejército principal", 12)
    text(832, 101, "MANDO", 18, gold)
    for friendly, y, units in (
        (False, 177, [("Infantería", 600, .76), ("Arqueros", 150, .64), ("Caballería", 300, .88)]),
        (True, 447, [("Infantería", 1000, .62), ("Arqueros", 200, .81), ("Caballería", 300, .91)]),
    ):
        for i, (name, count, morale) in enumerate(units):
            x = 34 + i * 122
            image.paste(cards["blue" if friendly else "red"], (x, y))
            if friendly and i == 0:
                image.paste(cards["selected"], (x, y), cards["selected"])
            d = ImageDraw.Draw(image)
            # Exact, simple symbols, not fake screenshots or generated game art.
            d.line((x + 14, y + 12, x + 29, y + 29), fill=white, width=2)
            d.line((x + 29, y + 12, x + 14, y + 29), fill=white, width=2)
            text(x + 38, y + 9, str(count), 19)
            text(x + 8, y + 36, name, 12)
            d.rectangle((x + 10, y + 59, x + 102, y + 65), fill="#1b2625")
            d.rectangle((x + 10, y + 59, x + 10 + int(92 * morale), y + 65), fill="#a9bd79")
            text(x + 42, y + 66, f"{morale:.0%}", 10)
    text(832, 147, "Infantería", 18)
    text(832, 184, "1.000 soldados · 62%", 14)
    d.rectangle((832, 226, 1068, 269), fill="#526c64", outline=gold)
    text(875, 239, "Reagrupar", 16)
    text(832, 291, "+0,10 de moral", 14)
    text(832, 315, "Recuperación: 7 días", 14)
    text(32, 640, "Vista táctica inicial · Posiciones esquemáticas.", 13)
    text(32, 660, "Movimiento y maniobras: siguientes etapas del desarrollo.", 13)
    result = Image.new("RGB", (1104, 748), "#151c1b")
    result.paste(image, (0, 0))
    ImageDraw.Draw(result).text((22, 719), "MAQUETA OFFLINE · DATOS DE EJEMPLO · NO ES UNA CAPTURA DE EU5",
                               font=font(14), fill="#d7c69d")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    ART.mkdir(parents=True, exist_ok=True)
    image = board()
    image.save(ART / "command_board.dds", pixel_format="DXT1")
    cards = {"blue": card("#294c60", "#8da9ae"), "red": card("#633d38", "#bd8b7c")}
    for name, texture in cards.items():
        texture.save(ART / f"card_{name}.dds", pixel_format="DXT1")
    selected = Image.new("RGBA", (112, 80), (0, 0, 0, 0))
    ImageDraw.Draw(selected).rectangle((1, 1, 110, 78), outline="#ead393", width=3)
    selected.save(ART / "card_selected.dds", pixel_format="DXT5")
    cards["selected"] = selected
    if args.preview:
        out = ROOT / "docs/board-preview.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        preview(image, cards).save(out)
        print(out)


if __name__ == "__main__":
    main()
