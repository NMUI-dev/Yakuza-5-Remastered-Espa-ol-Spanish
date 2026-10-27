# -*- coding: utf-8 -*-
"""(Claude Code, 20-10-2026) Avisos de acción de Yakuza 5 (2dpar/sprite_en.par: 2d_cf_action_asc_*.dds, 128x64):
texto blanco con brillo naranja. Se rehacen en español con el mismo tamaño de letra, color y brillo (medidos del
original). Si la palabra no cabe en 128 px se estrecha. Salida: trabajo/imagenes/es/sprite_en/<nombre>.dds
  python herramientas/acciones_es.py
"""
import os, io
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
ORIG = os.path.join(T, 'extraido', '2dpar_sprite_en'); SAL = os.path.join(T, 'imagenes', 'es', 'sprite_en')
FUENTE = 'C:/Windows/Fonts/georgia.ttf'
ES = {'akeru': ('Open', 'Abrir'), 'chumoku': ('Focus', 'Fijar'), 'deru': ('Leave', 'Salir'), 'gezan': ('Descend', 'Bajar'),
      'hairu': ('Enter', 'Entrar'), 'hanasu': ('Talk', 'Hablar'), 'hirou': ('Pick Up', 'Recoger'), 'kaeru': ('Trade', 'Canjear'),
      'kaisyuu': ('Collect', 'Recolectar'), 'kau': ('Buy', 'Comprar'), 'kiku': ('Listen', 'Escuchar'), 'kimeru': ('OK', 'Aceptar'),
      'kudaru': ('Go Down', 'Bajar'), 'kuzusu': ('Break', 'Romper'), 'miru': ('Look', 'Mirar'), 'modoru': ('Back', 'Volver'),
      'nageru': ('Throw', 'Lanzar'), 'noboru': ('Go Up', 'Subir'), 'noru': ('Get On', 'Subirse'), 'orosu': ('Put Down', 'Dejar'),
      'owaru': ('End', 'Terminar'), 'siraberu': ('Examine', 'Examinar'), 'syukaku': ('Check', 'Revisar'), 'tobu': ('Jump', 'Saltar'),
      'tojiru': ('Close', 'Cerrar'), 'toru': ('Photograph', 'Fotografiar'), 'tsukamu': ('Grab', 'Agarrar'), 'tsukau': ('Use', 'Usar'),
      'utsu': ('Hit', 'Golpear'), 'yameru': ('Stop', 'Detener')}


def hacer(nombre, en, es, tam_fijo=None):
    p = os.path.join(ORIG, f'2d_cf_action_asc_{nombre}.dds'); o = open(p, 'rb').read()
    a = np.asarray(Image.open(p).convert('RGBA')).astype(np.float32); H, W = a.shape[:2]
    nucleo = (a[..., 3] > 230) & (a[..., :3].min(2) > 200)
    filas = np.where(nucleo.any(1))[0]; cols = np.where(nucleo.any(0))[0]
    halo = (a[..., 3] > 20) & ~nucleo
    color_halo = np.median(a[..., :3][halo & (a[..., 3] > 60)], axis=0) if (halo & (a[..., 3] > 60)).sum() > 10 else np.array([230, 110, 40])
    # tamaño: calibrar con la altura de mayúscula del inglés (primera letra mayúscula)
    alto = int(filas[-1] - filas[0] + 1) if len(filas) else 24
    tam = 40
    for _ in range(6):
        f = ImageFont.truetype(FUENTE, tam); bb = f.getbbox(en, anchor='ls'); tam = max(8, int(round(tam * alto / max(1, bb[3] - bb[1]))))
    if tam_fijo is None and not any(c in en for c in 'gjpqy'): return tam
    if tam_fijo is None: return None
    if tam_fijo is None: return tam
    tam = tam_fijo
    f = ImageFont.truetype(FUENTE, tam); bb = f.getbbox(es, anchor='ls'); bben = f.getbbox(en, anchor='ls')
    lienzo = Image.new('L', (bb[2] - bb[0] + 8, H), 0)
    base = int(filas[0]) - f.getbbox('H', anchor='ls')[1] if len(filas) else H * 3 // 4
    ImageDraw.Draw(lienzo).text((4 - bb[0], base), es, font=f, fill=255, anchor='ls')
    x0 = int(cols[0]) if len(cols) else 6; maxw = W - x0 - 4
    if lienzo.width - 8 > maxw: lienzo = lienzo.resize((maxw + 8, H), Image.LANCZOS)
    m = Image.new('L', (W, H), 0); m.paste(lienzo, (x0 - 4, 0))
    mk = np.asarray(m, np.float32) / 255
    glow = np.asarray(m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(3.0)), np.float32) / 255
    glow = np.clip(glow * 1.6, 0, 1)
    rgb = np.zeros((H, W, 3), np.float32); alfa = np.maximum(mk, glow * 0.9)
    rgb[:] = color_halo; rgb = rgb * (1 - mk[..., None]) + 255 * mk[..., None]
    img = Image.fromarray(np.dstack([rgb, alfa * 255]).clip(0, 255).astype(np.uint8))
    b = io.BytesIO(); img.save(b, format='DDS', pixel_format='DXT5'); d = b.getvalue()
    mips = max(1, int.from_bytes(o[28:32], 'little'))
    assert mips <= 1 and len(d) == len(o), (nombre, mips, len(d), len(o))
    os.makedirs(SAL, exist_ok=True); open(os.path.join(SAL, f'2d_cf_action_asc_{nombre}.dds'), 'wb').write(o[:128] + d[128:])
    return img


if __name__ == '__main__':
    tams = [t for t in (hacer(n, en, es) for n, (en, es) in ES.items()) if t]
    tam = int(np.median(tams)); print('tamaño de letra', tam, sorted(tams))
    ims = [hacer(n, en, es, tam) for n, (en, es) in ES.items()]
    s = Image.new('RGB', (128 * 4, 64 * ((len(ims) + 3) // 4)), (40, 90, 40))
    for k, im in enumerate(ims): s.paste(im, ((k % 4) * 128, (k // 4) * 64), im)
    s.save(os.path.join(T, 'imagenes', 'acciones_es.png')); print('hechas', len(ims))
