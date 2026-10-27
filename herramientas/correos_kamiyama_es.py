# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Correos publicitarios de Kamiyama Works (pausepar_pause_en/picture/mail/2d_yk_kamiyama_*):
4 renglones arriba (amarillo, contorno negro y sombra, letra gruesa estrecha) y «Super deals!» inclinado sobre la
estrella roja. Se borra el inglés (amarillo + contorno) con inpaint y se escribe el español con el mismo estilo, sin
pasar del ancho del cartel. El programa de páginas y el kit fallaban aquí. Está en trabajo/imagenes/manuales.txt.
  python herramientas/correos_kamiyama_es.py
"""
import os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); atlas_es.TEX = os.path.join(R, 'trabajo', 'extraido')
F = 'C:/Windows/Fonts/seguibl.ttf'; AMARILLO = (255, 236, 0)
SITIO = {'ac': 'en la calle Goshiki Este!', 'hk': 'en Tsukimino!', 'os': 'en Shofukucho!', 'tk': 'en Park Alley!'}
RENG = [(6, 32), (24, 58), (50, 85), (81, 112)]          # alto de cada renglón inglés (y0, y1)
XMAX = 240


def mascara(a, caja):
    x0, y0, x1, y1 = caja; z = a[y0:y1, x0:x1, :3].astype(int)
    amar = (z[..., 0] > 180) & (z[..., 1] > 160) & (z[..., 2] < 140); negro = z.max(2) < 45
    cerca = cv2.dilate(amar.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2).astype(bool)
    m = np.zeros(a.shape[:2], np.uint8); m[y0:y1, x0:x1] = (amar | (negro & cerca)).astype(np.uint8) * 255   # solo el contorno de la letra
    return m


def renglon(texto, alto, ancho_max):
    """Capa RGBA de un renglón con el estilo del cartel: amarillo, contorno negro, sombra; estrecho como el original."""
    tam = alto
    while True:
        f = ImageFont.truetype(F, tam); w = f.getlength(texto) * 0.84 + 8
        if w <= ancho_max or tam <= 12: break
        tam -= 1
    bb = f.getbbox(texto, anchor='ls', stroke_width=2)
    W, H = bb[2] - bb[0] + 6, bb[3] - bb[1] + 6
    capa = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
    d.text((2 - bb[0] + 2, 2 - bb[1] + 2), texto, font=f, fill=(0, 0, 0, 255), anchor='ls', stroke_width=2, stroke_fill=(0, 0, 0, 255))   # sombra
    d.text((2 - bb[0], 2 - bb[1]), texto, font=f, fill=AMARILLO + (255,), anchor='ls', stroke_width=2, stroke_fill=(0, 0, 0, 255))
    capa = capa.resize((max(1, int(W * 0.84)), H), Image.LANCZOS)
    return capa, -bb[1] + 2


for clave, sitio in SITIO.items():
    ruta = f'pausepar_pause_en/picture/mail/2d_yk_kamiyama_{clave}'
    o = Image.open(os.path.join(atlas_es.TEX, ruta + '.dds')).convert('RGBA'); a = np.asarray(o).copy()
    m = mascara(a, (10, 2, 246, 116)) | mascara(a, (128, 196, 250, 276))
    m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=1)
    a[..., :3] = cv2.inpaint(np.ascontiguousarray(a[..., :3]), m, 4, cv2.INPAINT_TELEA)
    # el MARCO amarillo del cartel no se toca: fuera del panel se vuelve al original (y donde había letra, amarillo marco)
    orig = np.asarray(o); yy, xx = np.mgrid[:a.shape[0], :a.shape[1]]
    marco = (xx < 16) | (xx >= 241) | (yy < 8) | (yy >= 270)
    a[marco] = orig[marco]; a[marco & (m > 0) & (yy < 120)] = (255, 222, 0, 255)
    img = Image.fromarray(a)
    for (y0, y1), t in zip(RENG, ['¡Ya abrimos', sitio, '¡Ven a echarle', 'un vistazo!']):
        capa, base = renglon(t, 27, XMAX - 14)
        img.alpha_composite(capa, (14, y1 - 6 - base))
    # «¡Súper ofertas!» inclinado sobre la estrella
    l1, _ = renglon('¡Súper', 26, 96); l2, _ = renglon('ofertas!', 26, 104)
    blo = Image.new('RGBA', (max(l1.width, l2.width + 14) + 4, l1.height + l2.height - 8), (0, 0, 0, 0))
    blo.alpha_composite(l1, (0, 0)); blo.alpha_composite(l2, (blo.width - l2.width, l1.height - 10))
    blo = blo.rotate(14, resample=Image.BICUBIC, expand=True)
    cx, cy = 192, 240
    img.alpha_composite(blo, (min(256 - blo.width - 2, cx - blo.width // 2), cy - blo.height // 2))
    atlas_es.guardar_dds(ruta, img); print('ok', ruta)
