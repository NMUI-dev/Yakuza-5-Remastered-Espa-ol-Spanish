# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) rule_h_dance_battle3: rótulos del medidor «Power / Low» y «Power / High» -> «Potencia / Baja»,
«Potencia / Alta», blanco con borde oscuro como el original. Se aplica DESPUÉS de paginas_v101.py (parte de su salida)."""
import os, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import atlas_es, paginas_v101 as PV
r = 'pausepar_pause_en/picture/rule_h_dance_battle3'
o = np.array(Image.open(PV.origen(r + '.dds')).convert('RGBA')); a = np.array(Image.open(os.path.join(PV.SAL, r + '.dds')).convert('RGBA'))
F = 'C:/Windows/Fonts/arialbd.ttf'
img = None
for (x0, y0, x1, y1), arriba, abajo in (((602, 278, 682, 338), 'Potencia', 'Baja'), ((932, 278, 1012, 338), 'Potencia', 'Alta')):
    z = o[y0:y1, x0:x1, :3].max(2); m = np.zeros(a.shape[:2], np.uint8); m[y0:y1, x0:x1] = (z > 200)
    m = cv2.dilate(m * 255, np.ones((5, 5), np.uint8), iterations=2)
    a[..., :3] = cv2.inpaint(np.ascontiguousarray(a[..., :3]), m, 4, cv2.INPAINT_TELEA)
img = Image.fromarray(a); d = ImageDraw.Draw(img)
for cx, arriba, abajo in ((642, 'Potencia', 'Baja'), (972, 'Potencia', 'Alta')):
    d.text((cx, 290), arriba, font=ImageFont.truetype(F, 15), fill=(255, 255, 255, 255), anchor='mm', stroke_width=2, stroke_fill=(30, 30, 40, 255))
    d.text((cx, 318), abajo, font=ImageFont.truetype(F, 24), fill=(255, 255, 255, 255), anchor='mm', stroke_width=2, stroke_fill=(30, 30, 40, 255))
atlas_es.TEX = os.path.join(PV.T, 'extraido'); atlas_es.SAL = PV.SAL; atlas_es.guardar_dds(r, img)
img.crop((560, 230, 1024, 360)).resize((928, 260)).save(os.path.join(PV.REV, 'F_medidor.png'))
