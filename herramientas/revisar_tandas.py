# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Revisión de las imágenes traducidas POR TANDAS PEQUEÑAS (pedido del usuario): cada llamada
saca una hoja con N texturas (original | español, sobre gris) en trabajo/imagenes/tandas/tanda_NNN.png, por orden de
visibilidad, y apunta en tandas/progreso.txt cuáles ya salieron. Los arreglos se hacen aparte y luego se sigue.
  python herramientas/revisar_tandas.py [N=8]        siguiente tanda
  python herramientas/revisar_tandas.py --resto      cuántas quedan
"""
import os, sys
from PIL import Image, ImageDraw
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
ES = os.path.join(T, 'imagenes', 'es'); OUT = os.path.join(T, 'imagenes', 'tandas'); PROG = os.path.join(OUT, 'progreso.txt')
ORDEN = ['firstload', 'title', 'pause_en/picture/chapter', 'common', 'window', 'keitai', 'actbtn', 'result', 'mission',
         'tougi', 'taxi', 'picture/rule', 'picture/', '']          # lo que más se ve primero


def original(ruta):
    for d in ('extraido_r', 'extraido'):
        p = os.path.join(T, d, ruta)
        if os.path.exists(p): return p


def todas():
    rs = [os.path.relpath(os.path.join(dp, f), ES).replace(os.sep, '/') for dp, _, fs in os.walk(ES) for f in fs if f.endswith('.dds')]
    return sorted(rs, key=lambda r: (next(i for i, k in enumerate(ORDEN) if k in r), r))


hechas = set(open(PROG, encoding='utf-8').read().split()) if os.path.exists(PROG) else set()
# (21-10) los atlas ya verificados de cerca (rótulo a rótulo) van al final: primero lo que nadie miró de cerca
ver = set(open(os.path.join(T, 'imagenes', 'atlas_verificados.txt'), encoding='utf-8').read().split())
clave = lambda r: r[:-4].replace('/', '__')
quedan = [r for r in todas() if r not in hechas and original(r)]
quedan = [r for r in quedan if clave(r) not in ver] + [r for r in quedan if clave(r) in ver]
if '--resto' in sys.argv: print('quedan', len(quedan), 'de', len(quedan) + len(hechas)); sys.exit()
n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
tanda = quedan[:n]
W = 760; filas = []
for r in tanda:
    a = Image.open(original(r)).convert('RGBA'); b = Image.open(os.path.join(ES, r)).convert('RGBA')
    h = max(40, min(600, int(a.height * W / a.width)))
    f = Image.new('RGB', (2 * W + 10, h + 16), (60, 60, 75))
    for k, im in enumerate((a, b)):
        bg = Image.new('RGBA', im.size, (60, 60, 75, 255)); bg.alpha_composite(im)
        f.paste(bg.convert('RGB').resize((W, h)), (k * (W + 10), 16))
    ImageDraw.Draw(f).text((3, 2), r, fill=(255, 255, 0)); filas.append(f)
os.makedirs(OUT, exist_ok=True)
num = len([x for x in os.listdir(OUT) if x.startswith('tanda_')])
hoja = Image.new('RGB', (2 * W + 10, sum(x.height for x in filas)), (30, 30, 30)); y = 0
for x in filas: hoja.paste(x, (0, y)); y += x.height
sal = os.path.join(OUT, f'tanda_{num:03d}.png'); hoja.save(sal)
open(PROG, 'a', encoding='utf-8').write(''.join(r + '\n' for r in tanda))
print(sal, '|', len(tanda), 'texturas | quedan', len(quedan) - len(tanda)); print('\n'.join(tanda))
