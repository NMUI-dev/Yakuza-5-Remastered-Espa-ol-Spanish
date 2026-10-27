# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Hoja original | español de las páginas de reglas/tesoros/correos que hace el programa
(las 35 con «dejar» en el kit), por tandas.  python herramientas/hoja_paginas.py [desde=0] [n=4]"""
import json, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocr_imagenes import origen
T = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'trabajo', 'imagenes'); H = os.path.join(T, 'atlas_hechos')
desde = int(sys.argv[1]) if len(sys.argv) > 1 else 0; n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
rutas = []
for f in sorted(os.listdir(H)):
    if not any(s in f for s in ('__rule_', '__takara__', '__mail__')): continue
    s = json.load(open(os.path.join(H, f), encoding='utf-8'))
    if not any(i.get('es') and i.get('es') != i.get('en') and not i.get('dejar') for i in s['items']): rutas.append(s['textura'].replace(os.sep, '/') + '.dds')
filas = []
for r in rutas[desde:desde + n]:
    a = Image.open(origen(r)).convert('RGBA'); b = Image.open(os.path.join(T, 'es', r)).convert('RGBA'); W = 700; h = int(a.height * W / a.width)
    f = Image.new('RGB', (2 * W + 10, h + 14), (20, 20, 20))
    for k, im in enumerate((a, b)):
        bg = Image.new('RGBA', im.size, (0, 0, 0, 255)); bg.alpha_composite(im); f.paste(bg.convert('RGB').resize((W, h)), (k * (W + 10), 14))
    ImageDraw.Draw(f).text((3, 1), f'{desde + len(filas)}: {r}', fill=(255, 255, 0)); filas.append(f)
hoja = Image.new('RGB', (1410, sum(x.height for x in filas)), (0, 0, 0)); y = 0
for x in filas: hoja.paste(x, (0, y)); y += x.height
sal = os.path.join(T, 'tandas', f'paginas_{desde:03d}.png'); hoja.save(sal); print(sal, len(filas), 'de', len(rutas))
