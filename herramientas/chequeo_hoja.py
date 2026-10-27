# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Hoja de cerca de los avisos de chequeo_cortes.py, por tandas pequeñas: cada fila = el
rótulo original | español con su casilla en rojo.  python herramientas/chequeo_hoja.py TIPO [desde=0] [n=12]
-> trabajo/imagenes/tandas/chequeo_TIPO_desde.png"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
tipo = sys.argv[1]; desde = int(sys.argv[2]) if len(sys.argv) > 2 else 0; n = int(sys.argv[3]) if len(sys.argv) > 3 else 12
sys.argv = sys.argv[:1]
import atlas_probar as A
L = [l for l in open(os.path.join(A.S.T, 'chequeo_cortes.txt'), encoding='utf-8').read().splitlines() if f'| {tipo}' in l]
filas = []; cache = {}
for l in L[desde:desde + n]:
    ident, es = l.split(' | ')[0], l.split(' | ')[1][1:-1]
    if ident not in cache:
        spec = json.load(open(os.path.join(A.HECHOS, ident + '.json'), encoding='utf-8')); cache[ident] = A.dibujar(spec)
    o, nv, items = cache[ident]
    it = next(i for i in items if i.get('es') == es)
    x0, y0, x1, y1 = it['caja']; W, H = o.size; p = 14
    c = (max(0, x0 - p), max(0, y0 - p), min(W, x1 + p), min(H, y1 + p))
    par = []
    for im in (o, nv):
        bg = Image.new('RGBA', im.size, (60, 60, 75, 255)); bg.alpha_composite(im); z = bg.crop(c).convert('RGB')
        ImageDraw.Draw(z).rectangle((x0 - c[0], y0 - c[1], x1 - c[0] - 1, y1 - c[1] - 1), outline=(255, 0, 0))
        k = min(4, 700 / z.width, 160 / z.height); par.append(z.resize((max(1, int(z.width * k)), max(1, int(z.height * k)))))
    f = Image.new('RGB', (1420, max(x.height for x in par) + 16), (30, 30, 30))
    f.paste(par[0], (0, 16)); f.paste(par[1], (720, 16))
    ImageDraw.Draw(f).text((3, 2), f'{desde + len(filas)}: {ident[-60:]} | {l.split(" | ")[2][:60]}', fill=(255, 255, 0)); filas.append(f)
hoja = Image.new('RGB', (1420, sum(x.height for x in filas)), (0, 0, 0)); y = 0
for x in filas: hoja.paste(x, (0, y)); y += x.height
sal = os.path.join(A.S.T, 'tandas', f'chequeo_{tipo}_{desde:03d}.png'); hoja.save(sal); print(sal, len(filas), 'de', len(L))
