# -*- coding: utf-8 -*-
"""(claude1, 21-10-2026) Atlas del kit SIN verificar que YA tienen versión en trabajo/imagenes/es (programa de claude2):
hoja por cada 5: original | programa (es/) | kit (atlas_hechos redibujado) -> trabajo/imagenes/comparar/cmp_NN.png
  python herramientas/comparar_versiones.py
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_semi as S, atlas_probar as P
from atlas_borrador import HECHOS
T = S.T; O = os.path.join(T, 'comparar'); os.makedirs(O, exist_ok=True)
v = P.verificados(); filas = []
for f in sorted(os.listdir(HECHOS)):
    i = f[:-5]
    if i in v: continue
    spec = json.load(open(os.path.join(HECHOS, f), encoding='utf-8')); n = spec['textura']
    pe = os.path.join(T, 'es', n + '.dds')
    if not os.path.exists(pe): continue
    a = Image.open(os.path.join(S.tex_dir(n), n + '.dds')).convert('RGBA')
    kit = P.dibujar(spec)[1]; kit = kit if isinstance(kit, Image.Image) else Image.fromarray(np.asarray(kit))
    fila = []
    for im in (a, Image.open(pe).convert('RGBA'), kit.convert('RGBA')):
        b = Image.new('RGBA', im.size, (40, 40, 40, 255)); b.alpha_composite(im); b = b.convert('RGB')
        k = 480 / b.width; fila.append(b.resize((480, max(1, int(b.height * k)))))
    filas.append((i, fila))
for h in range(0, len(filas), 5):
    tr = filas[h:h + 5]; H = sum(max(x.height for x in f) + 16 for _, f in tr)
    o = Image.new('RGB', (1460, H), (15, 15, 15)); d = ImageDraw.Draw(o); y = 0
    for i, f in tr:
        d.text((4, y + 2), f'[{h + tr.index((i, f))}] {i}   original | programa | kit', fill=(255, 255, 0)); y += 16
        for k, x in enumerate(f): o.paste(x, (k * 490, y))
        y += max(x.height for x in f)
    o.save(os.path.join(O, f'cmp_{h // 5:02d}.png'))
    print(f'cmp_{h // 5:02d}', ' '.join(i for i, _ in tr))
