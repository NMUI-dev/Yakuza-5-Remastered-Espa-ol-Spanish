# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Aviso de ficción al arrancar (firstload_fiction), hecho a mano: el texto va en blanco sobre
negro, así que se borra todo el bloque y se escriben los 5 renglones en español con el MISMO alto de letra, el mismo
centro y las mismas líneas que el inglés; ningún renglón pasa del ancho del renglón inglés más largo.
Está en trabajo/imagenes/manuales.txt (imagenes_es.py no la toca).
  python herramientas/ficcion_es.py
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = 'pausepar_pause_en/picture/firstload/firstload_fiction'
atlas_es.TEX = os.path.join(R, 'trabajo', 'extraido')
LINEAS = [(307, 348, 'Esta es una obra de ficción. Todo parecido con personas reales,'),
          (378, 422, 'vivas o muertas, o con hechos reales, es pura coincidencia.'),
          (522, 563, 'Además, esta obra transcurre en el año 2012.'),
          (597, 634, 'Las leyes u opiniones que aquí se mencionan corresponden'),
          (667, 708, 'a esa época.')]
X0, X1 = 431, 1637                       # ancho del renglón inglés más largo
o = Image.open(os.path.join(atlas_es.TEX, RUTA + '.dds')).convert('RGBA')
a = np.asarray(o).copy(); a[280:740, 380:1690, :3] = 0          # fondo negro liso: se borra el bloque entero
img = Image.fromarray(a); d = ImageDraw.Draw(img)
F = 'C:/Windows/Fonts/seguisb.ttf'   # seminegrita, como el original
alto_h = 26                               # alto de mayúscula del original (tinta 311-345 con colas: ~26 px)
tam = 100
while True:                               # mismo cuerpo para todos los renglones: el que cabe en el más largo
    f = ImageFont.truetype(F, tam); hcap = -f.getbbox('H', anchor='ls')[1]
    if hcap <= alto_h and max(f.getlength(t) for _, _, t in LINEAS) <= X1 - X0: break
    tam -= 1
cx = (X0 + X1) / 2
for y0, y1, t in LINEAS:
    d.text((cx, y1 - 9), t, font=f, fill=(255, 255, 255, 255), anchor='ms')
atlas_es.guardar_dds(RUTA, img)
print('ok', RUTA, 'cuerpo', tam)
