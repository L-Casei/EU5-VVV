"""Original top-down map illustrations and vector-style unit symbols.

Only asset regeneration needs Pillow. Coordinates are shared with the GUI;
the labelled preview is not an in-game screenshot.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .generate_gui import load_layout, role_position

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'in_game/gfx/interface/vvv'


def frame() -> Image.Image:
    image = Image.new('RGB', (960, 620), '#202b2b')
    d = ImageDraw.Draw(image)
    d.rectangle((3, 3, 956, 616), outline='#b09b70', width=2)
    d.rectangle((8, 8, 951, 611), outline='#4f5e56')
    d.line((24, 45, 936, 45), fill='#756b52')
    d.rounded_rectangle((39, 51, 364, 99), 4, fill='#263e47')
    d.rounded_rectangle((598, 51, 923, 99), 4, fill='#4b302e')
    d.rectangle((15, 111, 944, 504), outline='#baa77a', width=2)
    d.rectangle((16, 516, 943, 603), fill='#2c3835', outline='#6b7561')
    d.line((412, 528, 412, 589), fill='#586451')
    return image


def terrain(style: str) -> Image.Image:
    colors = {'plains': '#89916b', 'hills': '#838865', 'mountains': '#858774',
              'woods': '#66795b', 'dry': '#b19c70', 'wetlands': '#748b78'}
    rng = random.Random(731 + sum(map(ord, style)))
    image = Image.new('RGB', (928, 392), colors[style])
    d = ImageDraw.Draw(image)
    # Broad colour washes and fine cartographic grain, not a square grid.
    palette = [tuple(max(0, min(255, c + n)) for c in image.getpixel((0, 0)))
               for n in (-5, -3, 3, 5)]
    for _ in range(10000):
        x, y = rng.randrange(928), rng.randrange(392)
        d.line((x, y, x + rng.randrange(1, 5), y), fill=rng.choice(palette))

    if style in {'plains', 'hills', 'dry'}:
        for y in (34, 352):
            points = [(x, y + int(9 * math.sin(x / 83))) for x in range(0, 929, 8)]
            d.line(points, fill='#a2a485' if style != 'dry' else '#c7b58b', width=2)
        for x, y in ((15, 83), (770, 290), (20, 300), (805, 15)):
            for i in range(5):
                d.line((x, y + i * 5, x + 110, y + 12 + i * 5), fill='#929b76' if style != 'dry' else '#baab80')

    if style in {'hills', 'mountains', 'dry'}:
        for cx, cy, rx, ry in ((80, 25, 155, 74), (833, 365, 170, 65),
                               (875, 65, 125, 70), (60, 363, 140, 64)):
            for ring in range(7):
                points = []
                for angle in range(0, 361, 5):
                    a = math.radians(angle)
                    wobble = 1 + .06 * math.sin(a * 5 + cx)
                    points.append((cx + (rx - ring * 13) * math.cos(a) * wobble,
                                   cy + (ry - ring * 7) * math.sin(a) * wobble))
                d.line(points, fill='#666f51' if style != 'dry' else '#9b8458', width=1)
        if style == 'mountains':
            for cx, cy in ((30, 45), (150, 25), (810, 355), (890, 325)):
                rock = [(cx-65, cy+30), (cx-36, cy-18), (cx-9, cy-39),
                        (cx+17, cy-14), (cx+64, cy+28), (cx+8, cy+45)]
                d.polygon(rock, fill='#9b9b88', outline='#616a5c')
                d.line((cx-36, cy-18, cx-9, cy-39, cx+8, cy+3, cx+64, cy+28), fill='#d0cbb1', width=3)
                d.line((cx-9, cy-39, cx-18, cy+14, cx+8, cy+45), fill='#737a68', width=2)

    if style == 'wetlands':
        for offset in (-12, 8, 27):
            points = [(x, 40 + offset + int(15 * math.sin(x / 69))) for x in range(0, 929, 4)]
            d.line(points, fill='#557875', width=5)
            d.line(points, fill='#91aaa0', width=2)
        for x, y in ((15, 310), (760, 330), (840, 105)):
            d.ellipse((x, y, x+120, y+22), fill='#5b807b', outline='#94a99b')
        for _ in range(160):
            x, y = rng.randrange(928), rng.choice([rng.randrange(5, 85), rng.randrange(315, 391)])
            d.line((x, y+6, x+2, y-2), fill='#526e55')

    if style in {'woods', 'hills', 'plains'}:
        count = 330 if style == 'woods' else 30
        for _ in range(count):
            x = rng.randrange(928)
            y = rng.choice([rng.randrange(2, 72), rng.randrange(323, 391)])
            if style == 'woods' and rng.random() < .35:
                x = rng.choice([rng.randrange(0, 65), rng.randrange(864, 927)])
                y = rng.randrange(392)
            r = rng.randrange(4, 10)
            d.ellipse((x-r, y-r, x+r, y+r), fill=rng.choice(['#435f49', '#506b4f', '#5b7352']), outline='#3d5845')
            d.arc((x-r+2, y-r+1, x+r-1, y+r-1), 180, 300, fill='#7f9269', width=1)
    # A quiet dotted meeting line, never three native flank columns.
    for x in range(12, 920, 18):
        d.line((x, 198, x+5, 198), fill='#b8b795')
    d.line((0, 0, 927, 0), fill='#c0b58e')
    d.line((0, 391, 927, 391), fill='#c0b58e')
    return image


def token(color: str, selected: bool = False) -> Image.Image:
    s = 4
    image = Image.new('RGBA', (64*s, 64*s), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    def box(values): return tuple(int(v*s) for v in values)
    if selected:
        d.ellipse(box((3, 3, 60, 60)), outline='#f1d38a', width=2*s)
        d.ellipse(box((0, 0, 63, 63)), outline='#c0a56a', width=s)
    else:
        d.ellipse(box((4, 6, 61, 63)), fill=(18, 28, 22, 120))
        d.ellipse(box((2, 2, 60, 60)), fill=color, outline='#c5b992', width=2*s)
        d.ellipse(box((7, 7, 55, 55)), outline='#a8a584', width=s)
    return image.resize((64, 64), Image.Resampling.LANCZOS)


def symbol(kind: str) -> Image.Image:
    s = 4
    image = Image.new('RGBA', (64*s, 64*s), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    ivory, gold = '#f1ead4', '#d2bd83'
    def pts(points): return [(int(x*s), int(y*s)) for x,y in points]
    def line(points, fill=ivory, width=3): d.line(pts(points), fill=fill, width=width*s, joint='curve')
    def poly(points, fill=ivory): d.polygon(pts(points), fill=fill)
    def ellipse(box, fill=None, outline=ivory, width=3):
        d.ellipse(tuple(int(v*s) for v in box), fill=fill, outline=outline, width=width*s)
    if kind == 'pikes':
        for x in (14, 30, 46):
            line([(x-5, 57), (x+8, 15)], width=3)
            poly([(x+8, 4), (x+2, 17), (x+12, 19)], gold)
            line([(x, 42), (x+11, 46)], gold, 2)
    elif kind == 'bow':
        d.arc((13*s, 6*s, 49*s, 58*s), 95, 265, fill=ivory, width=4*s)
        line([(29, 7), (29, 57)], gold, 2)
        line([(9, 32), (56, 32)])
        poly([(57, 32), (46, 26), (46, 38)])
        line([(12, 25), (19, 32), (12, 39)], gold, 2)
    elif kind in {'light_horse', 'heavy_horse'}:
        poly([(15, 57), (19, 42), (10, 35), (18, 24), (24, 20), (22, 7),
              (34, 13), (43, 12), (50, 21), (49, 37), (44, 47), (45, 57)])
        poly([(14, 33), (22, 31), (21, 37)], '#243638')
        ellipse((35, 20, 39, 24), fill='#243638', outline='#243638', width=1)
        line([(24, 17), (30, 26), (27, 35), (32, 45)], gold, 2)
        if kind == 'heavy_horse':
            poly([(30, 36), (48, 36), (47, 49), (39, 57), (31, 49)], '#7e8b85')
            line([(39, 39), (39, 51)], gold, 2)
        else:
            line([(7, 49), (19, 49)], gold, 3)
            line([(5, 55), (16, 55)], gold, 2)
    elif kind == 'cannon':
        poly([(11, 23), (51, 17), (55, 28), (15, 35)])
        line([(16, 36), (46, 42)], gold, 4)
        ellipse((13, 37, 33, 57), fill='#243638', width=3)
        ellipse((36, 38, 55, 57), fill='#243638', width=3)
        line([(23, 40), (23, 54)], gold, 2)
        line([(45, 41), (45, 54)], gold, 2)
    else:
        line([(19, 7), (19, 58)], gold, 4)
        poly([(22, 10), (53, 10), (47, 22), (53, 35), (22, 35)])
        line([(29, 17), (42, 17)], gold, 2)
        line([(29, 25), (41, 25)], gold, 2)
        line([(11, 58), (30, 58)], gold, 3)
    return image.resize((64,64), Image.Resampling.LANCZOS)


def font(size: int, bold: bool = False):
    try:
        return ImageFont.truetype('DejaVuSerif-Bold.ttf' if bold else 'DejaVuSans.ttf', size)
    except OSError:
        return ImageFont.load_default(size=size)


def preview(style: str = 'hills') -> Image.Image:
    layout = load_layout()
    image = frame().convert('RGBA')
    image.alpha_composite(terrain(style).convert('RGBA'), tuple(layout['field'][:2]))
    d = ImageDraw.Draw(image)
    def text(x, y, value, size=13, color='#eee8d5', center=False, bold=False):
        d.text((x,y), value, font=font(size,bold), fill=color, anchor='mt' if center else None)
    text(480, 14, 'Tlemcen', 22, center=True, bold=True)
    text(880, 18, 'Cerrar', 12)
    text(480, 61, 'VS', 15, center=True)
    text(480, 38, 'Llanura · Bosque' if style == 'woods' else 'Colinas · Praderas', 11, center=True)
    for x, label in ((368,'Línea'),(446,'Cuña'),(524,'Izquierda')):
        d.rounded_rectangle((x,81,x+74,103),2,fill='#486967' if x==368 else '#2b3c3b',outline='#a29571')
        text(x+37,86,label,11,center=True)
    # Illustrative faction flags in the offline preview; the game uses native flags.
    d.rectangle((46,56,99,90), fill='#a52626', outline='#b7a679')
    star=[]
    for i in range(10):
        a=-math.pi/2+i*math.pi/5;r=12 if i%2==0 else 5
        star.append((73+r*math.cos(a),73+r*math.sin(a)))
    d.polygon(star, outline='#539061')
    d.rectangle((608,56,661,90), fill='#eee9ce', outline='#b7a679')
    d.ellipse((626,61,649,84), fill='#364e6f')
    d.ellipse((633,57,653,79), fill='#eee9ce')
    text(112,56,'Marruecos',16);text(112,79,'8.460',12)
    text(674,56,'Tlemcen',16);text(674,79,'6.866',12)
    names={'light_infantry':'Inf. ligera','heavy_infantry':'Inf. pesada','light_cavalry':'Cab. ligera',
           'heavy_cavalry':'Cab. pesada','artillery':'Artillería','auxiliary':'Apoyo'}
    counts=[[900,2800,1000,1300,266,600],[1200,3100,1100,1800,400,860]]
    for friendly in (False,True):
        for index,role in enumerate(layout['roles']):
            x,y=role_position(layout,role,friendly)
            image.alpha_composite(token('#30576e' if friendly else '#7d413b').resize((48,48)),(x+32,y))
            if friendly and role['key']=='heavy_cavalry':
                image.alpha_composite(token('',True).resize((56,56)),(x+28,y-4))
            image.alpha_composite(symbol(role['icon']).resize((28,28)),(x+42,y+10))
            d=ImageDraw.Draw(image)
            d.rounded_rectangle((x+4,y+49,x+108,y+79),3,fill=(25,36,31,220))
            text(x+56,y+49,f'{counts[int(friendly)][index]:,}'.replace(',','.'),17,center=True)
            text(x+56,y+69,names[role['key']],10,center=True)
    text(30,527,'Caballeros acorazados',15)
    text(30,553,'200 · Caballería pesada',12)
    text(30,577,'Moral: 84 / 100',11)
    d.rounded_rectangle((422,538,576,576),3,fill='#486967',outline='#b9a879')
    text(499,548,'Reagrupar',14,center=True)
    text(600,532,'+0,10 de moral · 7 días',13)
    text(600,560,'Orden al regimiento seleccionado',11)
    result=Image.new('RGB',(960,654),'#182321')
    result.paste(image.convert('RGB'),(0,0))
    ImageDraw.Draw(result).text((18,632),'MAQUETA OFFLINE · Datos de ejemplo · Distribución esquemática',font=font(12),fill='#cbbd97')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview',action='store_true')
    args=parser.parse_args()
    ART.mkdir(parents=True,exist_ok=True)
    frame().save(ART/'battle_frame.dds',pixel_format='DXT1')
    for style in load_layout()['terrain_styles']:
        terrain(style).save(ART/f'terrain_{style}.dds',pixel_format='DXT1')
    for name,color in [('blue','#30576e'),('red','#7d413b')]:
        token(color).save(ART/f'token_{name}.dds',pixel_format='DXT5')
    token('',True).save(ART/'token_selected.dds',pixel_format='DXT5')
    for role in load_layout()['roles']:
        symbol(role['icon']).save(ART/f"symbol_{role['icon']}.dds",pixel_format='DXT5')
    plaque=Image.new('RGBA',(112,36),(0,0,0,0))
    ImageDraw.Draw(plaque).rounded_rectangle((4,1,108,35),3,fill=(25,36,31,225))
    plaque.save(ART/'token_plaque.dds',pixel_format='DXT5')
    if args.preview:
        preview().save(ROOT/'docs/board-preview.png')
        preview('woods').save(ROOT/'docs/board-preview-woods.png')
        print(ROOT/'docs/board-preview.png')


if __name__=='__main__':
    main()
