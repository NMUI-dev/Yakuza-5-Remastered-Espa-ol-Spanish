# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Hueco tras la «í» en el juego («paí s»): el juego reserva para cada casilla de la letra
(gothic_en/sd_hankaku.dds) un ANCHO FIJO de su tabla, y el de «í» es el de la í original (dibujada a la derecha), mucho
más que el de la «i». Se dibuja la «í» en la casilla del acento grave «`» (estrecha, casi sin uso) y aplicar.py/devil.py
escriben «`» en vez de «í» (aplicar.LETRAS), como ya se hizo con «¡» -> «~».
Rehace trabajo/fuente/font_hd_en.par a partir del original (trabajo/originales) + trabajo/fuente/add.
  python herramientas/letra_i.py
"""
import os, shutil, subprocess, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); F = os.path.join(R, 'trabajo', 'fuente')
HOJA = os.path.join(F, 'add', 'font_hd_en', 'gothic_en', 'sd_hankaku.dds')


def celda(c): o = ord(c); return ((o - 0x20) % 16) * 16, ((o - 0x20) // 16) * 32


im = Image.open(os.path.join(F, 'sd_hankaku_antes_i.dds')).convert('RGBA'); a = np.asarray(im).copy()
ORIG = np.asarray(Image.open(os.path.join(R, 'trabajo', 'extraido', 'font_font_hd_en', 'font_hd_en', 'gothic_en', 'sd_hankaku.dds')).convert('RGBA'))
# (21-10) letra -> casilla estrecha casi sin uso cuyo ancho de la tabla del juego le va bien (prueba en el lab):
#   í -> «`» (tinta 2-6), Í -> «|» (7-9; «¶» dejaba hueco), ¡ -> «½» (2-6). aplicar.LETRAS y devil.py hacen el mismo cambio.
CAMBIOS = {'í': '`', 'Í': '|', '¡': '½'}
for letra, casilla in CAMBIOS.items():
    xi, yi = celda('~' if letra == '¡' else letra); xg, yg = celda(casilla)   # la «¡» buena estaba en «~»
    z = a[yi:yi + 32, xi:xi + 16].copy(); cols = np.where(z[..., 3].max(0) > 20)[0]
    oc = np.where(ORIG[yg:yg + 32, xg:xg + 16, 3].max(0) > 20)[0]
    z = np.roll(z, int(oc.min()) - int(cols.min()), axis=1)   # la tinta empieza donde empezaba la de esa casilla
    a[yg:yg + 32, xg:xg + 16] = z
# guardar con el mismo formato (DXT5) usando la rutina del kit
atlas_es.TEX = os.path.join(F, 'add'); atlas_es.SAL = os.path.join(F, 'tmp_dds')
ruta = atlas_es.guardar_dds('font_hd_en/gothic_en/sd_hankaku', Image.fromarray(a))
shutil.copy(ruta, HOJA); shutil.rmtree(atlas_es.SAL, ignore_errors=True)
orig = os.path.join(R, 'trabajo', 'originales', 'fontpar', 'font_hd_en.par')
out = os.path.join(F, 'font_hd_en.par')
subprocess.run([os.path.join(R, 'herramientas', 'partool', 'ParTool.exe'), 'add', orig, os.path.join(F, 'add'), out], check=True, stdin=subprocess.DEVNULL)
print('ok', out)
