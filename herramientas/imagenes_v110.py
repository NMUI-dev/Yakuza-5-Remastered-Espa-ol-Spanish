# -*- coding: utf-8 -*-
"""(07-11-2026, claude2) v1.0.10: en el menú Objetos, el rótulo «Pistola» (inglés «Gun») es más ancho que el hueco y el
número de «Hoja» le tapa la «P» (captura trabajo/capturas/obj1.png). Pasa a «Bala» (resistencia a balas), centrado en la
misma caja, con la misma fuente (Times) y del mismo alto que «Hoja». En TODAS las copias de la textura que lo llevan.
Usa borrar() de imagenes_v105.py (inpaint de la letra vieja) y guardar_dds() (mismo formato DDS).
  python imagenes_v110.py   -> trabajo/imagenes/es_v110/<ruta>.dds + hoja antes|después
"""
import os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import imagenes_v105 as v5
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(R, 'trabajo', 'img_final', 'es')
SAL = os.path.join(R, 'trabajo', 'imagenes', 'es_v110')
TIMES = 'C:/Windows/Fonts/times.ttf'
X = '2dpar/ui_en.par_x/'
TEX = [X + 'surfboard/pjd_omiyage.par/texlist/2d_yk_z_common_kiryu.dds'] + \
      [X + 'tex_common/common/2d_yk_z_common_%s.dds' % p for p in ('akiyama', 'haruka', 'kiryu', 'saejima', 'shinada', 'yukiyama')]
CAJA_GUN = (692, 664, 768, 684)       # atlas_es.json: «Gun» -> «Pistola»
CAJA_HOJA = (615, 664, 692, 684)      # «Blade» -> «Hoja»: su alto de letra marca el tamaño
NUEVO = 'Bala'


def alto_tinta(a, caja):
    x0, y0, x1, y1 = caja; c = a[y0:y1, x0:x1]
    borde = np.concatenate([c[0], c[-1], c[:, 0], c[:, -1]]); fondo = np.median(borde, axis=0)
    m = (np.abs(c[:, :, :3].astype(int) - fondo[:3]).sum(axis=2) > 70)
    ys = np.where(m.any(axis=1))[0]
    return (ys.max() - ys.min() + 1) if len(ys) else None


def main():
    os.makedirs(SAL, exist_ok=True); hojas = []
    for rel in TEX:
        ref = os.path.join(BASE, rel)
        img = Image.open(ref).convert('RGBA'); antes = img.copy(); a = np.array(img)
        # tamaño: el de Times con el que «Hoja» dibujada mide el mismo ANCHO de tinta que la «Hoja» de la textura
        x0, y0, x1, y1 = CAJA_HOJA; cc = a[y0:y1, x0:x1].astype(int)
        bd = np.concatenate([cc[0], cc[-1], cc[:, 0], cc[:, -1]]); fd = np.median(bd, axis=0)
        mm = np.abs(cc[:, :, :3] - fd[:3]).sum(axis=2) > 70
        xs = np.where(mm.any(axis=0))[0]; ancho_h = xs.max() - xs.min() + 1
        tam = 40
        while tam > 6 and (lambda bb: bb[2] - bb[0])(ImageFont.truetype(TIMES, tam).getbbox('Hoja')) > ancho_h: tam -= 1
        # línea de base: el pie de la «H» (primeras columnas de tinta; la «j» baja más)
        colH = mm[:, xs.min():xs.min() + 3]; pie_h = y0 + np.where(colH.any(axis=1))[0].max()
        # 1) borrar «Pistola» como en la v1.0.5 (se escribe algo y luego se repinta encima: aquí solo se aprovecha el borrado)
        borrado, info = v5.borrar_y_escribir(img, *CAJA_GUN, ' ', 0)
        # el color de la letra: el de «Hoja»
        x0, y0, x1, y1 = CAJA_HOJA; c = a[y0:y1, x0:x1].astype(int)
        borde = np.concatenate([c[0], c[-1], c[:, 0], c[:, -1]]); fondo = np.median(borde, axis=0)
        m = np.abs(c[:, :, :3] - fondo[:3]).sum(axis=2) > 70
        px = c[m]; letra = tuple(int(v) for v in np.median(px[np.argsort(px[:, :3].mean(axis=1))[int(len(px) * .75):]], axis=0)[:3])
        f = ImageFont.truetype(TIMES, tam); bb = f.getbbox(NUEVO)
        capa = Image.new('RGBA', borrado.size, (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
        gx0, gy0, gx1, gy1 = CAJA_GUN; cx = (gx0 + gx1) / 2
        # misma línea de base que «Hoja»: se alinea la parte de arriba de la B con la de la H
        hb = f.getbbox('B')                                  # «B» sin descendente: su pie = línea de base
        d.text((cx - (bb[0] + bb[2]) / 2, pie_h - hb[3] + 1), NUEVO, font=f, fill=letra + (255,))
        borrado.alpha_composite(capa)
        png = os.path.join(SAL, rel.replace('/', '_').replace('.dds', '.png')); borrado.save(png)
        v5.guardar_dds(png, ref, os.path.join(SAL, rel))
        caja = (590, 650, 790, 698)
        par = [Image.alpha_composite(Image.new('RGBA', x.size, (60, 60, 60, 255)), x).crop(caja).resize((600, 144)) for x in (antes, borrado)]
        h = Image.new('RGB', (600, 300), (255, 0, 0)); h.paste(par[0], (0, 0)); h.paste(par[1], (0, 156)); hojas.append(h)
        print(rel, 'tamaño', tam, 'color', letra, info)
    hoja = Image.new('RGB', (600, 300 * len(hojas)), (0, 0, 0))
    for i, h in enumerate(hojas): hoja.paste(h, (0, 300 * i))
    hoja.save(os.path.join(SAL, 'hoja.png')); print('listo', len(TEX))


if __name__ == '__main__':
    main()
