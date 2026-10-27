# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) rule_blackjack0: «1 or 11» bajo el as -> «1 o 11» (solo cambia «or»). Después de paginas_v101.py."""
import os, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import atlas_es, paginas_v101 as PV
r = 'pausepar_pause_en/picture/rule_blackjack0'
a = np.array(Image.open(os.path.join(PV.SAL, r + '.dds')).convert('RGBA'))
x0, y0, x1, y1 = 60, 462, 92, 490
z = a[y0:y1, x0:x1, :3].max(2); m = np.zeros(a.shape[:2], np.uint8); m[y0:y1, x0:x1] = z < 150
m = cv2.dilate(m * 255, np.ones((3, 3), np.uint8), iterations=1)
a[..., :3] = cv2.inpaint(np.ascontiguousarray(a[..., :3]), m, 3, cv2.INPAINT_TELEA)
img = Image.fromarray(a); d = ImageDraw.Draw(img)
d.text((76, 485), 'o', font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 30), fill=(70, 70, 72, 255), anchor='ms')
atlas_es.TEX = os.path.join(PV.T, 'extraido'); atlas_es.SAL = PV.SAL; atlas_es.guardar_dds(r, img)
img.crop((20, 440, 200, 512)).resize((540, 216)).save(os.path.join(PV.REV, 'F_bj_or.png'))
