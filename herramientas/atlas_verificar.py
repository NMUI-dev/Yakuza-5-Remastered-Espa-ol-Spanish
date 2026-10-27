# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Hojas de VERIFICACIÓN para claude2: redibuja cada atlas aceptado (atlas_hechos, sin gemma4) y
pone cada rótulo de cerca, original | español, varios atlas por hoja -> trabajo/imagenes/atlas_verif/hoja_NN.png
  python herramientas/atlas_verificar.py hojas          (los hechos sin verificar)
  python herramientas/atlas_verificar.py ok <id> [...]  (los apunta en atlas_verificados.txt)
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from atlas_probar import HECHOS, VERIF, verificados, dibujar
import atlas_semi as S
OUT = os.path.join(S.T, 'atlas_verif'); ANCHO = 1500; ALTO_MAX = 1900


def filas(i):
    spec = json.load(open(os.path.join(HECHOS, i + '.json'), encoding='utf-8'))
    o, nv, items = dibujar(spec); a, b = np.asarray(o), np.asarray(nv); W, H = o.size; out = []
    for it in items:
        x0, y0, x1, y1 = it['caja']; p = 3; c = [max(0, x0 - p), max(0, y0 - p), min(W, x1 + p), min(H, y1 + p)]
        ca, cb = Image.fromarray(a[c[1]:c[3], c[0]:c[2]]), Image.fromarray(b[c[1]:c[3], c[0]:c[2]])
        z = max(1, min(3, 40 // max(1, ca.height)))
        ca, cb = ca.resize((ca.width * z, ca.height * z)), cb.resize((cb.width * z, cb.height * z))
        if ca.width * 2 + 10 > ANCHO: k = (ANCHO - 10) / (2 * ca.width); ca, cb = ca.resize((int(ca.width * k), max(1, int(ca.height * k)))), cb.resize((int(cb.width * k), max(1, int(cb.height * k))))
        f = Image.new('RGBA', (ANCHO, ca.height + 2), (40, 90, 40, 255)); f.alpha_composite(ca, (0, 2)); f.alpha_composite(cb, (ca.width + 10, 2))
        out.append(f)
    return out, len(spec['items']) - len(items)


def hojas():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT): os.remove(os.path.join(OUT, f))
    pend = sorted(f[:-5] for f in os.listdir(HECHOS) if f[:-5] not in verificados())
    hoja, y, n, indice = Image.new('RGB', (ANCHO, ALTO_MAX), (15, 15, 15)), 0, 0, []
    def guardar():
        nonlocal hoja, y, n
        hoja.crop((0, 0, ANCHO, max(y, 1))).save(os.path.join(OUT, f'hoja_{n:02d}.png')); n += 1
        hoja, y = Image.new('RGB', (ANCHO, ALTO_MAX), (15, 15, 15)), 0
    for i in pend:
        fs, dejados = filas(i); alto = 22 + sum(f.height for f in fs)
        if y and y + alto > ALTO_MAX: guardar()
        ImageDraw.Draw(hoja).text((4, y + 4), f'[{len(indice)}] {i.split("__")[-1]}  ({len(fs)} rótulos, {dejados} dejados)', fill=(255, 255, 0))
        indice.append((n, i)); y += 22
        for f in fs:
            if y + f.height > ALTO_MAX: guardar()
            hoja.paste(f.convert('RGB'), (0, y)); y += f.height
    if y: guardar()
    json.dump(indice, open(os.path.join(OUT, 'indice.json'), 'w'), indent=0)
    for k, (h, i) in enumerate(indice): print(k, f'hoja_{h:02d}', i)


def ok(ids):
    open(VERIF, 'a', encoding='utf-8').write(''.join(i + '\n' for i in ids)); print('verificados', len(ids))


if __name__ == '__main__':
    hojas() if sys.argv[1] == 'hojas' else ok(sys.argv[2:])
