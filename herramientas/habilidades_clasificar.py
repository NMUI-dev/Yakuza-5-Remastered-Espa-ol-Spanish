# -*- coding: utf-8 -*-
"""(Claude Code, 20-10-2026) Clasifica las 522 tarjetas de habilidad (pause_en/ability) por su etiqueta en inglés
(HEAT, TECH, SOUL, BODY u otra) comparando la máscara de la etiqueta con ejemplos. Salida: trabajo/habilidades_clases.json"""
import os, json, colorsys
import numpy as np
from PIL import Image
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
Z = (slice(128, 200), slice(136, 256))   # zona de la etiqueta (filas, columnas)

def mascara(p):
    en = np.asarray(Image.open(os.path.join(T, 'extraido', p)).convert('RGB'), np.float32)[Z]
    ja = np.asarray(Image.open(os.path.join(T, 'extraido_ja', p.replace('pause_en', 'pause_ja'))).convert('RGB'), np.float32)[Z]
    mx, mn = en.max(2), en.min(2)
    m = (np.abs(en - ja).sum(2) > 60) & (mx > 120) & ((mx - mn) / (mx + 1) > 0.35)
    return m, en

if __name__ == '__main__':
    L = [l.strip() for l in open(os.path.join(T, 'imagenes_distintas.txt')) if '/ability/' in l]
    datos = {p: mascara(p) for p in L}
    def tono(p):
        m, en = datos[p]
        if m.sum() < 30: return None
        r, g, b = np.median(en[m], 0) / 255; return colorsys.rgb_to_hsv(r, g, b)[0] * 360
    ej = {'TECH': 'pausepar_pause_en/ability/k_ba_001.dds'}
    res = {}
    for p in L:
        h = tono(p); res[p] = 'NADA' if h is None else ('ROJO' if (h < 20 or h > 330) else 'NARANJA' if h < 60 else 'AZUL' if 170 < h < 250 else f'otro{int(h)}')
    # los azules: TECH o HEAT según parecido con el ejemplo de TECH
    t = datos[ej['TECH']][0]
    for p in L:
        if res[p] == 'AZUL':
            m = datos[p][0]; iou = (m & t).sum() / max(1, (m | t).sum()); res[p] = 'TECH' if iou > 0.45 else 'HEAT'
            res[p + '#iou'] = round(float(iou), 2)
    json.dump(res, open(os.path.join(T, 'habilidades_clases.json'), 'w'), indent=0)
    import collections; print(collections.Counter(v for k, v in res.items() if '#' not in k))
    print(sorted(v for k, v in res.items() if '#' in k)[::10])
