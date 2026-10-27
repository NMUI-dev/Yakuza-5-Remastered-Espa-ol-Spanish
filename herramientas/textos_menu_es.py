# -*- coding: utf-8 -*-
"""(Claude Code, 20-10-2026) Carteles de menú de Yakuza 5 con efectos (objeto obtenido, habilidad aprendida, subir de
nivel). Cada entrada: textura (ruta en trabajo/extraido_r sin .dds), rectángulo (del .sbb), texto, fuente, estilo:
  plano   = texto del color medido;      brillo = texto + halo del mismo color;
  hueco   = solo el contorno con halo;   barrido = desenfoque vertical (efecto de movimiento);
  neon    = relleno de color con halo claro (subir de nivel).
El rectángulo se borra entero y el texto se escribe centrado, a la altura del original (o «alto»), estrechado si no cabe.
  python herramientas/textos_menu_es.py
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
W_FONTS = 'C:/Windows/Fonts/'
LV = 'ui_en/surfboard/pjd_levelup.par/Texlist_0001/2d_jm_levelup'
GI = 'ui_en/surfboard/pjd_get_item.par/texlist/2d_cf_get_item'
GA = 'ui_en/surfboard/pjd_get_ability.par/texlist/2d_cf_get_ability'
SERIF = 'timesbd.ttf'; SANS = 'segoeuib.ttf'
TRABAJOS = {
    GI: [((0, 168, 256, 212), 'Objeto obtenido', SERIF, 'plano', None), ((0, 212, 256, 256), 'Objeto obtenido', SERIF, 'brillo', None)],
    LV: [((0, 0, 204, 40), 'SUBES DE NIVEL', SANS, 'neon', None), ((0, 256, 256, 290), 'Vida máxima aumentada', SANS, 'neon', 15),
         ((0, 290, 256, 324), 'Orbes de alma obtenidos', SANS, 'neon', 15)],
    GA: [((14, 320, 98, 384), 'HABI', SERIF, 'plano', 26), ((121, 320, 231, 384), 'LIDAD', SERIF, 'plano', 26),
         ((252, 320, 350, 384), 'APREN', SERIF, 'plano', 26), ((370, 320, 500, 384), 'DIDA', SERIF, 'plano', 26),
         ((14, 384, 98, 448), 'HABI', SERIF, 'hueco', 26), ((121, 384, 231, 448), 'LIDAD', SERIF, 'hueco', 26),
         ((252, 384, 350, 448), 'APREN', SERIF, 'hueco', 26), ((370, 384, 500, 448), 'DIDA', SERIF, 'hueco', 26),
         ((0, 448, 512, 512), 'HABILIDAD APRENDIDA', SERIF, 'barrido', 30)],
}


def mascara(texto, fuente, alto, ancho):
    f = ImageFont.truetype(W_FONTS + fuente, 100); bb = f.getbbox(texto, anchor='ls'); hcap = -f.getbbox('H', anchor='ls')[1]
    img = Image.new('L', (bb[2] - bb[0] + 20, bb[3] - bb[1] + 20), 0)
    ImageDraw.Draw(img).text((10 - bb[0], 10 - bb[1]), texto, font=f, fill=255, anchor='ls')
    img = img.crop(img.getbbox()); k = alto / hcap
    w, h = max(1, int(img.width * k)), max(1, int(img.height * k))
    if w > ancho: w = ancho
    return img.resize((w, h), Image.LANCZOS), int(round((-bb[1] - hcap) * k))   # desplazamiento de tildes por encima


def dibujar(nombre, trabajos):
    orig = Image.open(os.path.join(atlas_es.TEX, nombre + '.dds')).convert('RGBA'); a = np.asarray(orig).copy()
    for (x0, y0, x1, y1), texto, fuente, estilo, alto in trabajos:
        z = a[y0:y1, x0:x1].astype(np.float32); op = z[..., 3] > 200
        color = np.median(z[..., :3][op], axis=0) if op.sum() > 10 else np.array([255, 255, 255.])
        filas = np.where((z[..., 3] > 200).any(1))[0]
        alto = alto or (int(filas[-1] - filas[0] + 1) if len(filas) else int((y1 - y0) * 0.6))
        a[y0:y1, x0:x1] = 0
        m, sube = mascara(texto, fuente, alto, x1 - x0 - 8)
        capa = Image.new('L', (x1 - x0, y1 - y0), 0)
        capa.paste(m, ((x1 - x0 - m.width) // 2, (y1 - y0 - alto) // 2 - max(0, m.height - alto - 2) + (2 if sube < 0 else 0)))
        c = np.asarray(capa, np.float32) / 255
        if estilo == 'brillo':
            c = np.maximum(c, np.asarray(capa.filter(ImageFilter.GaussianBlur(3)), np.float32) / 255 * 1.5)
        elif estilo == 'hueco':
            borde = np.asarray(capa.filter(ImageFilter.MaxFilter(3)), np.float32) / 255 - np.asarray(capa.filter(ImageFilter.MinFilter(3)), np.float32) / 255
            halo = np.asarray(capa.filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
            c = np.clip(np.maximum(borde, halo * 0.8), 0, 1)
        elif estilo == 'barrido':
            v = Image.fromarray((c * 255).astype(np.uint8)).resize((x1 - x0, 1 + (y1 - y0) // 10), Image.BOX).resize((x1 - x0, y1 - y0), Image.BICUBIC)
            c = np.clip(np.asarray(v, np.float32) / 255 * 0.9 + c * 0.25, 0, 1)
        elif estilo == 'neon':
            halo = np.asarray(capa.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(2)), np.float32) / 255
            rgb = np.zeros(c.shape + (3,), np.float32); rgb[:] = color
            rgb = rgb * c[..., None] + np.array([230, 245, 255.]) * (1 - c[..., None])
            a[y0:y1, x0:x1, :3] = rgb.clip(0, 255); a[y0:y1, x0:x1, 3] = (np.clip(np.maximum(c, halo * 0.9), 0, 1) * 255)
            continue
        a[y0:y1, x0:x1, :3] = color; a[y0:y1, x0:x1, 3] = (np.clip(c, 0, 1) * 255)
    nuevo = Image.fromarray(a.astype(np.uint8)); atlas_es.guardar_dds(nombre, nuevo)
    W, H = orig.size; v = Image.new('RGBA', (W * 2, H), (40, 90, 40, 255)); v.alpha_composite(orig); v.alpha_composite(nuevo, (W, 0))
    v.convert('RGB').save(os.path.join(atlas_es.SAL, nombre + '.png'))


if __name__ == '__main__':
    for n, t in TRABAJOS.items(): dibujar(n, t); print('ok', n)
