# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Comprobador AUTOMÁTICO de los fallos que vio el usuario (para no repetirlos ni revisar a ojo):
por cada rótulo traducido de los atlas hechos (atlas_hechos) mide la tinta del español y avisa si
  BORDE  : la tinta toca el borde de la textura (x/y = 0 o el final): el juego pierde media letra («C» de COMBATE)
  CAJA   : la tinta toca el borde de su casilla: se corta en pantalla (el juego enseña solo ese hueco)
  ANCHO  : el español es >12 % más ancho que el inglés (sale apretado o se sale)
  VACIO  : el rótulo traducido no dibujó nada
Salida: trabajo/imagenes/chequeo_cortes.txt.  python herramientas/chequeo_cortes.py [filtro]
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = sys.argv[:2] if len(sys.argv) > 1 else sys.argv
import atlas_probar as A
filtro = sys.argv[1] if len(sys.argv) > 1 else ''


def tinta(a, c, cambio=None):
    x0, y0, x1, y1 = c; z = a[y0:y1, x0:x1]
    v = z[..., 3] > 90 if a[..., 3].min() < 250 else z[..., :3].max(2) > 150
    if cambio is not None: v &= cambio[y0:y1, x0:x1]          # solo la tinta NUEVA (no la del rótulo vecino)
    ys, xs = np.where(v)
    return None if len(xs) == 0 else (x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1)


avisos = []
for f in sorted(os.listdir(A.HECHOS)):
    if filtro not in f: continue
    spec = json.load(open(os.path.join(A.HECHOS, f), encoding='utf-8'))
    try: o, nv, items = A.dibujar(spec)
    except SystemExit as e: avisos.append(f'{f[:-5]} | ERROR {e}'); continue
    a, b = np.asarray(o), np.asarray(nv); H, W = a.shape[:2]
    cambio = np.abs(a.astype(int) - b.astype(int)).max(2) > 40
    for it in items:
        if it.get('dejar') or not it.get('es') or it['es'] == it.get('en'): continue
        x0, y0, x1, y1 = it['caja']; m = 6
        grande = [max(0, x0 - m), max(0, y0 - m), min(W, x1 + m), min(H, y1 + m)]
        propio = cambio.copy()                     # fuera de su casilla no cuenta lo que cae en la casilla de OTRO rótulo
        for ot in items:
            if ot is not it:
                q0, q1, q2, q3 = ot['caja']; propio[q1:q3, q0:q2] &= np.zeros((max(0, q3 - q1), max(0, q2 - q0)), bool)[:propio[q1:q3, q0:q2].shape[0], :propio[q1:q3, q0:q2].shape[1]]
        propio[y0:y1, x0:x1] = cambio[y0:y1, x0:x1]
        te, ti = tinta(b, grande, propio), tinta(a, it['caja'])
        nom = f"{f[:-5]} | «{it['es']}»"
        if te is None: avisos.append(f'{nom} | VACIO'); continue
        if te[0] <= 0 or te[1] <= 0 or te[2] >= W or te[3] >= H: avisos.append(f'{nom} | BORDE {te}')
        # (21-10) 1-2 px de roce no se notan: solo cuenta salirse 3 px o más
        elif te[0] < x0 - 2 or te[1] < y0 - 2 or te[2] > x1 + 2 or te[3] > y1 + 2: avisos.append(f'{nom} | CAJA tinta {te} casilla {it["caja"]}')
        if ti and (te[2] - te[0]) > 1.12 * (ti[2] - ti[0]) + 4: avisos.append(f'{nom} | ANCHO {te[2]-te[0]} px vs inglés {ti[2]-ti[0]}')
out = os.path.join(A.S.T, 'chequeo_cortes.txt')
open(out, 'w', encoding='utf-8').write('\n'.join(avisos))
from collections import Counter
print(Counter(x.split(' | ')[-1].split()[0] for x in avisos), '->', out)
