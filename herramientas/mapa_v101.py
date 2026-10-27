# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) v1.0.1: mapa del tesoro treasure_map3_unite_l (texto en pergamino). Las versiones por programa
partían mal los renglones y dejaban el último diminuto. A mano: se borra el texto del original (tinta oscura sobre el
pergamino) y se escriben los 6 párrafos en una letra con serifa como la original, mismo color, mismo margen y alto."""
import os, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import atlas_es, paginas_v101 as PV, paginas_es as P
r = 'pausepar_pause_en/item/treasure_map3_unite_l'
o = np.array(Image.open(PV.origen(r + '.dds')).convert('RGBA')); a = o.copy()
x0, y0, x1, y1 = 12, 100, 506, 412
z = a[y0:y1, x0:x1, :3].astype(int); papel = cv2.medianBlur(np.ascontiguousarray(a[..., :3]), 21)
m = np.zeros(a.shape[:2], np.uint8); m[y0:y1, x0:x1] = (z.sum(2) < np.median(z.sum(2)) - 90)
m = cv2.dilate(m * 255, np.ones((3, 3), np.uint8), iterations=2)
a[..., :3] = cv2.inpaint(np.ascontiguousarray(a[..., :3]), m, 4, cv2.INPAINT_TELEA)
tinta = (25, 18, 10, 255)
PARR = ['Cuando volví en mí, estaba en una ciudad donde nevaba.',
        'Me quedé parado en medio de un cruce un momento y decidí caminar por el centro de la calle, como si me empujaran los bocinazos de los carros.',
        'En el siguiente cruce, giré a la izquierda. Me llevó a una calle amplia. La crucé y seguí mi camino un rato.',
        'Por suerte, encontré una calle protegida del mal tiempo. Mi cuerpo congelado decidió por mí y fui en esa dirección.',
        'Cuando se acabó el camino, seguí andando con el tráfico a mi izquierda. Al llegar al final de la calle, lo vi.',
        '«Felicidades», me dijo. Entonces supe que había llegado al final de mi viaje.']
img = Image.fromarray(a); d = ImageDraw.Draw(img)
for tam in range(16, 9, -1):
    f = ImageFont.truetype('C:/Windows/Fonts/times.ttf', tam); paso = 17; hueco = 15
    bloques = [P.partir(t, f, 476) for t in PARR]
    alto = sum(len(b) for b in bloques) * paso + (len(bloques) - 1) * hueco
    if alto <= 412 - 104: break
y = 104 + paso * 0.8
for b in bloques:
    for t in b: d.text((17, y), t, font=f, fill=tinta, anchor='ls'); y += paso
    y += hueco
atlas_es.TEX = os.path.join(PV.T, 'extraido'); atlas_es.SAL = PV.SAL; atlas_es.guardar_dds(r, img)
v = Image.new('RGBA', (1036, o.shape[0])); v.paste(Image.fromarray(o), (0, 0)); v.paste(img, (524, 0)); v.crop((0, 90, 1036, 420)).save(os.path.join(PV.REV, 'F_mapa.png'))
print('tam', tam)
