# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) v1.0.1: carta de técnica s_sa_001 (ALMA). La v1.0 pegó un recorte de otra carta detrás del rótulo
(parche de otro color sobre el abrigo). Se parte del original: se borra «SOUL» (tinta roja) y se pega solo la tinta del
rótulo «ALMA» de la v1.0."""
import os, numpy as np, cv2
from PIL import Image
import atlas_es, paginas_v101 as PV
r = 'pausepar_pause_en/ability/s_sa_001'
o = np.array(Image.open(PV.origen(r + '.dds')).convert('RGBA')); e = np.array(Image.open(os.path.join(PV.T, 'imagenes', 'es', r + '.dds')).convert('RGBA'))
def rojo(a):
    R, G, B = [a[..., k].astype(int) for k in range(3)]
    m = (R > 140) & (R - G > 60) & (R - B > 60); m[:140] = False; m[:, :140] = False; return m
ms = cv2.dilate(rojo(o).astype(np.uint8) * 255, np.ones((5, 5), np.uint8), iterations=2)
a = o.copy(); a[..., :3] = cv2.inpaint(np.ascontiguousarray(o[..., :3]), ms, 5, cv2.INPAINT_TELEA)
ma = cv2.dilate(rojo(e).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
linea = np.zeros_like(ma); linea[188:] = True
ma &= ~(linea & (np.abs(e.astype(int) - o.astype(int)).max(2) < 40))   # la raya naranja de abajo se queda la original
a[ma] = e[ma]
img = Image.fromarray(a); atlas_es.TEX = os.path.join(PV.T, 'extraido'); atlas_es.SAL = PV.SAL; atlas_es.guardar_dds(r, img)
v = Image.new('RGBA', (524, 256)); v.paste(Image.fromarray(o), (0, 0)); v.paste(img, (268, 0)); v.resize((1048, 512)).save(os.path.join(PV.REV, 'F_s_sa_001.png'))
