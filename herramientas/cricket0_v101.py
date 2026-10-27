# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) rule_cricket_0: leyenda de marcas (SINGLE 1MARK... / 2MARKS...) y «CLOSE» a mano, con la letra
Times del original, sin aplastar. Se aplica DESPUÉS de atlas_v101 y dardos_v101 (parte de es_v101)."""
import os, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import atlas_es, paginas_v101 as PV
r = 'pausepar_pause_en/picture/rule_cricket_0'
o = np.array(Image.open(PV.origen(r + '.dds')).convert('RGBA'))
a = np.array(Image.open(os.path.join(PV.SAL, r + '.dds')).convert('RGBA'))
for x0, y0, x1, y1 in ((288, 32, 520, 98), (548, 2, 660, 100), (858, 52, 950, 82)):   # fondo negro del recuadro
    z = o[y0:y1, x0:x1, :3].max(2) > 70; linea = np.zeros_like(z)
    if x0 == 548: linea[z.mean(1) > 0.6, :] = True; cm = z.mean(0) > 0.6; cm[:88] = False; linea[:, cm] = True; linea &= z   # rayas y barra de la leyenda
    fondo = np.median(o[y0:y1, x0:x1, :3][~z], 0).astype(np.uint8)
    zona = a[y0:y1, x0:x1]; zona[..., :3] = fondo; zona[linea] = o[y0:y1, x0:x1][linea]
# las rayitas de las marcas (2/3/1) y la línea se devuelven del original: solo se borraron letras grandes
img = Image.fromarray(a); d = ImageDraw.Draw(img)
T, TB = 'C:/Windows/Fonts/times.ttf', 'C:/Windows/Fonts/timesbd.ttf'
B, R = (255, 255, 255, 255), (235, 110, 150, 255)
f = ImageFont.truetype(T, 21)
for y, (t1, t2, c) in zip((46, 66, 86), (('SIMPLE', '1 MARCA', B), ('DOBLE', '2 MARCAS', R), ('TRIPLE', '3 MARCAS', B))):
    d.text((292, y), t1, font=f, fill=c, anchor='lm'); d.text((385, y), t2, font=f, fill=c, anchor='lm')
for y, t, c in ((20, '2 MARCAS', B), (52, '3 MARCAS', R), (82, '1 MARCA', B)):
    d.text((551, y), t, font=ImageFont.truetype(TB, 19), fill=c, anchor='lm')
d.text((903, 66), 'CERRADO', font=ImageFont.truetype(TB, 20), fill=R, anchor='mm')
atlas_es.TEX = os.path.join(PV.T, 'extraido'); atlas_es.SAL = PV.SAL; atlas_es.guardar_dds(r, img)
v = Image.new('RGB', (1400, 130)); v.paste(Image.fromarray(o).convert('RGB').crop((270, 0, 970, 130)), (0, 0)); v.paste(img.convert('RGB').crop((270, 0, 970, 130)), (700, 0))
v.save(os.path.join(PV.REV, 'F_cricket0.png'))
