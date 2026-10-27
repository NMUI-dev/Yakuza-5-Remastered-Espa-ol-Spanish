# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Hoja de cerca de los rótulos que arreglar_cortes.py ACHICÓ: original | antes | ahora,
por tandas.  python herramientas/chequeo_achicados.py [desde=0] [n=12] -> trabajo/imagenes/tandas/achicados_NNN.png"""
import json, os, sys
from PIL import Image, ImageDraw
desde = int(sys.argv[1]) if len(sys.argv) > 1 else 0; n = int(sys.argv[2]) if len(sys.argv) > 2 else 12; sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_probar as A
ANT = os.path.join(A.S.T, 'atlas_hechos_antes'); casos = []
for f in sorted(os.listdir(ANT)):
    a = json.load(open(os.path.join(ANT, f), encoding='utf-8')); d = json.load(open(os.path.join(A.HECHOS, f), encoding='utf-8'))
    for ia, idd in zip(a['items'], d['items']):
        if ia.get('es') == idd.get('es') and ia.get('alto') != idd.get('alto') and not idd.get('tam') and idd.get('alto'):
            casos.append((f, a, d, idd['es']))
filas = []
for f, a, d, es in casos[desde:desde + n]:
    ims = [A.dibujar(a)[0], A.dibujar(a)[1], A.dibujar(d)[1]]
    it = next(i for i in d['items'] if i.get('es') == es); x0, y0, x1, y1 = it['caja']; W, H = ims[0].size; p = 10
    c = (max(0, x0 - p), max(0, y0 - p), min(W, x1 + p), min(H, y1 + p)); par = []
    for im in ims:
        bg = Image.new('RGBA', im.size, (60, 60, 75, 255)); bg.alpha_composite(im); z = bg.crop(c).convert('RGB')
        k = min(3, 460 / z.width, 120 / z.height); par.append(z.resize((max(1, int(z.width * k)), max(1, int(z.height * k)))))
    fi = Image.new('RGB', (1410, max(x.height for x in par) + 14), (30, 30, 30))
    for j, z in enumerate(par): fi.paste(z, (j * 470, 14))
    ImageDraw.Draw(fi).text((3, 1), f'{desde + len(filas)}: {f[-55:-5]} «{es}»', fill=(255, 255, 0)); filas.append(fi)
hoja = Image.new('RGB', (1410, sum(x.height for x in filas)), (0, 0, 0)); y = 0
for x in filas: hoja.paste(x, (0, y)); y += x.height
sal = os.path.join(A.S.T, 'tandas', f'achicados_{desde:03d}.png'); hoja.save(sal); print(sal, len(filas), 'de', len(casos))
