# -*- coding: utf-8 -*-
"""(31-10-2026, claude1) OCR (RapidOCR, sin conexión) de las texturas en inglés que la revisión de imágenes no miró
(trabajo/telop/sin_revisar.json: auth_telop_en sin versión japonesa, minigame_en, staffroll_en, parte de pause_en...).
Como ocr_imagenes.py: con transparencia se lee sobre negro y sobre blanco. Retoma si se corta.
Salida: trabajo/telop/ocr_nuevas.json  {ruta: [[x0, y0, x1, y1, texto, confianza], ...]}
  python -u herramientas/ocr_sin_revisar.py"""
import os, json
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
SAL = os.path.join(T, 'telop', 'ocr_nuevas.json')


def leer(ocr, ruta):
    im = Image.open(os.path.join(T, ruta)).convert('RGBA')
    if im.width < 32 or im.height < 16: return []
    mejor = []
    for fondo in ((0, 0, 0, 255), (255, 255, 255, 255)):
        b = Image.new('RGBA', im.size, fondo); b.alpha_composite(im)
        r, _ = ocr(np.asarray(b.convert('RGB')))
        lineas = [[int(min(p[0] for p in c)), int(min(p[1] for p in c)), int(max(p[0] for p in c)), int(max(p[1] for p in c)), t, round(float(s), 3)]
                  for c, t, s in (r or [])]
        if sum(len(l[4]) * l[5] for l in lineas) > sum(len(l[4]) * l[5] for l in mejor): mejor = lineas
        if im.getextrema()[3][0] == 255: break
    return mejor


def main():
    rutas = json.load(open(os.path.join(T, 'telop', 'sin_revisar.json')))
    hecho = json.load(open(SAL, encoding='utf-8')) if os.path.exists(SAL) else {}
    ocr = RapidOCR()
    for i, r in enumerate(rutas):
        if r in hecho: continue
        try: hecho[r] = leer(ocr, r)
        except Exception as e: hecho[r] = [[0, 0, 0, 0, 'ERROR ' + str(e)[:80], 0]]
        if i % 50 == 0:
            json.dump(hecho, open(SAL, 'w', encoding='utf-8'), ensure_ascii=False); print(i, len(rutas), flush=True)
    json.dump(hecho, open(SAL, 'w', encoding='utf-8'), ensure_ascii=False); print('fin', len(hecho))


if __name__ == '__main__': main()
