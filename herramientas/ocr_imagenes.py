# -*- coding: utf-8 -*-
"""(Claude Code, 20-10-2026) Lee con OCR (RapidOCR, sin conexión) el texto inglés de las texturas distintas de la versión
japonesa (trabajo/imagenes_distintas.txt), salvo las tarjetas de habilidad (habilidades_es.py) y los avisos de acción
(acciones_es.py). Las texturas con transparencia se leen sobre negro y sobre blanco (se queda la lectura más segura).
Salida: trabajo/imagenes/ocr.json  {ruta: [[x0, y0, x1, y1, texto, confianza], ...]}. Retoma si se corta.
  python -u herramientas/ocr_imagenes.py
"""
import os, json, time
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
SAL = os.path.join(T, 'imagenes', 'ocr.json')


def origen(ruta):
    """Las rutas 'ui_en/...' (texturas dentro de .par anidados) están en trabajo/extraido_r; el resto en trabajo/extraido."""
    return os.path.join(T, 'extraido_r' if ruta.startswith('ui_en/') else 'extraido', ruta)


def leer(ocr, ruta):
    im = Image.open(origen(ruta)).convert('RGBA')
    mejor = []
    for fondo in ((0, 0, 0, 255), (255, 255, 255, 255)):
        b = Image.new('RGBA', im.size, fondo); b.alpha_composite(im)
        r, _ = ocr(np.asarray(b.convert('RGB')))
        lineas = [[int(min(p[0] for p in c)), int(min(p[1] for p in c)), int(max(p[0] for p in c)), int(max(p[1] for p in c)), t, round(float(s), 3)]
                  for c, t, s in (r or [])]
        if sum(len(l[4]) * l[5] for l in lineas) > sum(len(l[4]) * l[5] for l in mejor): mejor = lineas
        if im.getextrema()[3][0] == 255: break           # opaca: con una lectura basta
    return mejor


def main():
    hecho = json.load(open(SAL, encoding='utf-8')) if os.path.exists(SAL) else {}
    lista = [l.strip() for l in open(os.path.join(T, 'imagenes_distintas.txt'), encoding='utf-8')
             if l.strip() and '/ability/' not in l and '2d_cf_action_asc_' not in l]
    lista += ['ui_en/' + l.strip() for l in open(os.path.join(T, 'ui_en_distintas.txt'), encoding='utf-8')
              if l.strip() and '2d_cf_action_asc_' not in l]
    ocr = RapidOCR(); t0 = time.time()
    for i, ruta in enumerate(lista):
        if ruta in hecho: continue
        try: hecho[ruta] = leer(ocr, ruta)
        except Exception as e: hecho[ruta] = []; print('ERROR', ruta, e)
        if i % 20 == 0:
            json.dump(hecho, open(SAL, 'w', encoding='utf-8'), ensure_ascii=False)
            print(f'{len(hecho)}/{len(lista)}  {time.time() - t0:.0f} s', flush=True)
    json.dump(hecho, open(SAL, 'w', encoding='utf-8'), ensure_ascii=False)
    print('fin', len(hecho))


if __name__ == '__main__': main()


CJK = __import__('re').compile(r'[\u3040-\u30ff\u4e00-\u9fff]')
LAT = __import__('re').compile(r'[A-Za-z0-9][A-Za-z0-9 .,\'!?:/&-]*$')


def partir_mixtas():
    """(20-10) Renglones con japonés y luego inglés («第一章 CHAPTER 1»): se parte por el hueco de tinta más ancho y se
    queda solo la parte inglesa como renglón propio (la japonesa no se traduce). Modifica ocr.json; repetible."""
    import re
    hecho = json.load(open(SAL, encoding='utf-8')); n = 0
    for ruta, lineas in hecho.items():
        nuevas = []
        for l in lineas:
            t = l[4]; m = re.search(r'[A-Za-z0-9]', t)
            if not (CJK.search(t) and m and LAT.match(t[m.start():]) and not CJK.search(t[m.start():])): nuevas.append(l); continue
            a = np.asarray(Image.open(origen(ruta)).convert('RGBA'))
            x0, y0, x1, y1 = l[:4]; z = a[y0:y1, x0:x1]
            v = z[..., :3].mean(2) * (z[..., 3] / 255.0)
            cols = (v > 100).any(0)
            # huecos (rachas de columnas vacías) entre tinta; el más ancho separa japonés e inglés
            mejor, ini, run = None, None, 0
            for x, c in enumerate(cols):
                if not c:
                    if ini is None: ini = x
                elif ini is not None:
                    if ini > 0 and (mejor is None or x - ini > mejor[1] - mejor[0]): mejor = (ini, x)
                    ini = None
            if mejor is None: nuevas.append(l); continue
            nuevas.append([x0 + mejor[1], y0, x1, y1, t[m.start():].strip(), l[5]]); n += 1
        hecho[ruta] = nuevas
    json.dump(hecho, open(SAL, 'w', encoding='utf-8'), ensure_ascii=False)
    print('renglones mixtos partidos:', n)
