# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) v1.0.1: barras de botones del purikura (puri_button, puri_button_bb) y la frase «Elige la foto...»
del menú de notas (ui puri_text). La v1.0.1 anterior dejaba cajas oscuras detrás y la letra gris y fina.
Se parte del ORIGINAL: cada caja de texto se repinta fila a fila con la recta RGBA que une sus dos bordes (la barra es un
degradado suave) y se escribe en Segoe UI Semibold blanco, como el original. Los iconos ◀ ▶ ○ ✕ y «OK» se quedan.
puri_text de la interfaz es la MISMA imagen que la de pausepar: se copia la de pausepar (una sola letra en las dos).
  python herramientas/botones_puri_v101.py   (va después de atlas_v101.py en regenerar_v101.sh)
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
import paginas_v101 as PV
SB = 'C:/Windows/Fonts/seguisb.ttf'
PIC = 'pausepar_pause_en/picture/'
# caja de borrado (x0, x1) en las filas 16-49 ; textos: (texto, x, alineación)
BARRAS = {
    PIC + 'puri_button': ([(289, 426), (549, 732)], [('Anterior', 293, 'izq'), ('Cerrar', 553, 'izq'), ('Siguiente', 729, 'der')]),
    PIC + 'puri_button_bb': ([(289, 426), (549, 732)], [('Anterior', 293, 'izq'), ('Cerrar', 553, 'izq'), ('Siguiente', 729, 'der')]),
}


def recta(a, x0, x1, y0, y1):
    k = np.linspace(0, 1, x1 - x0)[:, None]
    for y in range(y0, y1):
        iz = a[y, x0 - 2:x0, :].astype(float).mean(0); de = a[y, x1:x1 + 2, :].astype(float).mean(0)
        a[y, x0:x1, :] = np.clip(iz + (de - iz) * k, 0, 255).astype(np.uint8)


def barra(r, cajas, textos):
    o = Image.open(PV.origen(r + '.dds')).convert('RGBA'); a = np.array(o)
    for x0, x1 in cajas: recta(a, x0, x1, 14, 52)
    img = Image.fromarray(a); d = ImageDraw.Draw(img)
    for t, x, al in textos:   # «Cerrar» más grande, como «Close» en el original
        f = ImageFont.truetype(SB, 24 if t == 'Cerrar' else 21)
        d.text((x, 33), t, font=f, fill=(255, 255, 255, 255), anchor='lm' if al == 'izq' else 'rm')
    atlas_es.TEX = os.path.join(PV.T, 'extraido'); atlas_es.SAL = PV.SAL; atlas_es.guardar_dds(r, img)
    return o, img


def main():
    vs = []
    for r, (c, t) in BARRAS.items(): vs.append(barra(r, c, t)); print('ok', r, flush=True)
    # puri_text de la interfaz = la de pausepar (ya hecha por atlas_v101.puri_text_pausa)
    src = Image.open(os.path.join(PV.SAL, PIC + 'puri_text.dds')).convert('RGBA')
    r = 'ui_en/surfboard/pjd_mg_purikura_note.par/2d_mg_purikura_note_texlist/puri_text'
    atlas_es.TEX = os.path.join(PV.T, 'extraido_r'); atlas_es.SAL = PV.SAL; atlas_es.guardar_dds(r, src); print('ok', r)
    vs.append((Image.open(PV.origen(r + '.dds')).convert('RGBA'), src))
    W = max(o.width for o, _ in vs); H = sum(o.height * 2 + 10 for o, _ in vs); v = Image.new('RGBA', (W, H), (90, 90, 150, 255)); y = 0
    for o, n in vs: v.alpha_composite(o, (0, y)); v.alpha_composite(n, (0, y + o.height + 2)); y += o.height * 2 + 10
    v.convert('RGB').save(os.path.join(PV.REV, 'F_botones_puri.png'))


if __name__ == '__main__':
    main()
