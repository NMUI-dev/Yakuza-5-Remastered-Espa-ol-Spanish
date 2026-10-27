# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) v1.0.1: rule_01_0 (dardos 01): restos del inglés pegados a la 1.ª viñeta («●Reducir»). Se rehace
ese renglón: fondo de la fila (zona vacía de la derecha), viñeta copiada de la 2.ª y el texto en Segoe UI, con el tamaño
calibrado con el 2.º renglón («Si bajas de cero, te pasas.»)."""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
import atlas_es, paginas_v101 as PV
r = 'pausepar_pause_en/picture/rule_01_0'
e = np.array(Image.open(os.path.join(PV.SAL, r + '.dds')).convert('RGBA'))
bala = e[392:416, 154:180].copy()
fila = lambda y0, y1: np.where((e[y0:y1, 182:1000, :3].min(2) > 150).any(0))[0]
x_fin2 = 182 + fila(394, 416).max()
f = 'C:/Windows/Fonts/segoeui.ttf'; t2 = 'Si bajas de cero, te pasas.'
tam = 10
while ImageFont.truetype(f, tam + 1).getlength(t2) <= x_fin2 - 182: tam += 1
for y in range(361, 391): e[y, 150:1000] = np.median(e[y, 760:1000], 0).astype(np.uint8)
blanco = bala[..., :3].min(2) > 120
zona = e[359:383, 154:180]; zona[blanco] = bala[blanco]
img = Image.fromarray(e); d = ImageDraw.Draw(img)
# línea base: la del 2.º renglón menos el paso entre viñetas (394 - 361 = 33)
mk = (e[394:420, 182:400, :3].min(2) > 150).any(1); base2 = 394 + np.where(mk)[0].max()
d.text((182, base2 - 33), 'Reducir la puntuación a cero.', font=ImageFont.truetype(f, tam), fill=(255, 255, 255, 255), anchor='ls')
atlas_es.TEX = os.path.join(PV.T, 'extraido'); atlas_es.SAL = PV.SAL; atlas_es.guardar_dds(r, img)
img.crop((100, 330, 700, 470)).resize((1200, 280)).save(os.path.join(PV.REV, 'F_rule_01_0.png'))
print('tam', tam)
