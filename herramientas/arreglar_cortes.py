# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Arreglo AUTOMÁTICO de los rótulos que chequeo_cortes.py marcó como BORDE o CAJA: baja el
«alto» (tamaño de letra) un 6 % cada vez, hasta un 30 % como mucho, hasta que la tinta nueva quepa en su casilla con
2 px de aire y sin tocar el borde de la textura. Si ni así cabe, lo apunta en arreglar_cortes_mano.txt (acortar texto).
Guarda copia del .json antes de tocarlo en atlas_hechos_antes/.   python herramientas/arreglar_cortes.py [TIPO ...]
"""
import json, os, shutil, sys
import numpy as np
tipos = sys.argv[1:] or ['BORDE', 'CAJA']; sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_probar as A
from chequeo_cortes import tinta
T = A.S.T; ANT = os.path.join(T, 'atlas_hechos_antes'); os.makedirs(ANT, exist_ok=True)
L = [l.split(' | ') for l in open(os.path.join(T, 'chequeo_cortes.txt'), encoding='utf-8').read().splitlines()]
casos = {}
for ident, es, av in L:
    if av.split()[0] in tipos: casos.setdefault(ident, set()).add(es[1:-1])
mano = []; bien = 0


def medir(spec, it):
    o, nv, items = A.dibujar(spec); a, b = np.asarray(o), np.asarray(nv); H, W = a.shape[:2]
    cambio = np.abs(a.astype(int) - b.astype(int)).max(2) > 40
    x0, y0, x1, y1 = it['caja']; propio = np.zeros_like(cambio)
    g = [max(0, x0 - 6), max(0, y0 - 6), min(W, x1 + 6), min(H, y1 + 6)]
    propio[g[1]:g[3], g[0]:g[2]] = cambio[g[1]:g[3], g[0]:g[2]]
    for ot in spec['items']:
        if ot is not it: q0, q1, q2, q3 = ot['caja']; propio[q1:q3, q0:q2] = False
    propio[y0:y1, x0:x1] = cambio[y0:y1, x0:x1]
    te = tinta(b, g, propio)
    ok = te is not None and te[0] >= max(1, x0 - 1) and te[2] <= min(W - 1, x1 + 1) and te[1] >= max(1, y0 - 1) and te[3] <= min(H - 1, y1 + 1)
    return ok, te


for ident, textos in casos.items():
    p = os.path.join(A.HECHOS, ident + '.json'); spec = json.load(open(p, encoding='utf-8'))
    if not os.path.exists(os.path.join(ANT, ident + '.json')): shutil.copy(p, ANT)
    for it in spec['items']:
        if it.get('es') not in textos: continue
        ok, te = medir(spec, it)
        if ok: bien += 1; continue
        antes = it.get('alto'); base = int(antes or (te[3] - te[1] if te else 20)); paso = 0
        while not ok and paso < 6:
            paso += 1; it['alto'] = max(6, int(int(base) * (1 - 0.06 * paso))); ok, te = medir(spec, it)
        if ok: bien += 1
        else:   # (21-10) si se rinde, el rótulo vuelve EXACTO a como estaba (antes ponía el alto de la tinta medida)
            if antes is None or it.get('tam'): it.pop('alto', None)
            else: it['alto'] = antes
            mano.append(f"{ident} | «{it['es']}» | no cabe ni al 70 %: ACORTAR")
    json.dump(spec, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
open(os.path.join(T, 'arreglar_cortes_mano.txt'), 'w', encoding='utf-8').write('\n'.join(mano))
print('arreglados', bien, '| a mano', len(mano))
