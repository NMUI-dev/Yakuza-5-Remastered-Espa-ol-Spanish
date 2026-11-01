# -*- coding: utf-8 -*-
"""(01-11-2026, claude1) Dibuja en español las imágenes de imagenes_extra.py (rótulos de escena, karaoke, dardos), como
imagenes_es.py pero con los bloques de trabajo/telop/bloques_extra.json, las texturas de trabajo/barrido_3110/x (la ruta
del bloque ya empieza por barrido_3110/) y las traducciones de los lotes (368-369 y las frases que ya estaban en otros).
Salida: trabajo/imagenes/es_extra/<ruta>.dds + trabajo/imagenes/revision_extra/*.png (arriba original, abajo español)
  python herramientas/imagenes_extra_es.py [filtro]"""
import os, sys, json
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv, _argv = sys.argv[:1], sys.argv
import aplicar_extra as AX
sys.argv = _argv
import paginas_es as P, atlas_es, rotulos
from imagenes_lotes import validas
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
# (01-11) dardos: nombres de modo apilados en dos palabras y rótulos diminutos: traducidos quedaban partidos y pisados
# («Estándar» sobre «CRICKET»): se dejan como el original, y «BULL» (término de dardos; «DIANA» salía rosa). Solo va
# «GAME PREDICTION», corto para no pisar la cifra de al lado
SIN_TOCAR = {'COUNT-UP', 'ROUND', 'SCORE', 'STANDARD', 'CRICKET', 'HIDDEN', 'RANDOM', 'DART&RESULT', 'DART & RESULT', 'BULL'}
FIJOS = {'GAME PREDICTION': 'PREDICCIÓN'}
SAL = os.path.join(T, 'imagenes', 'es_extra'); REV = os.path.join(T, 'imagenes', 'revision_extra')


def barra_negra(o, img, caja=(196, 176, 300, 192)):
    """Barra negra de «GAME PREDICTION»: el borrado dejaba restos del inglés. Se rehace: la barra original con su texto
    tapado y «PREDICCIÓN» escrito aquí, blanco, centrado donde iba el inglés (x 202..288, 11 px)."""
    import numpy as np
    from PIL import ImageDraw, ImageFont
    x0, y0, x1, y1 = caja
    a = np.asarray(o).copy(); z = a[y0:y1, x0:x1]
    from scipy import ndimage
    letra = ndimage.binary_dilation(z[..., :3].max(-1) > 45, iterations=1)
    letra[:, :3] = letra[:, -3:] = False             # (los bordes de la caja no: ahí no hay letra)
    for r in range(z.shape[0]):                      # letra -> el gris de la barra en ese renglón
        t = letra[r]
        if t.any() and (~t).any(): z[r, t, :3] = np.median(z[r, ~t, :3], axis=0)
    n = a.copy(); n[y0:y1, x0:x1] = z                 # (solo lleva este rótulo: se parte del original)
    img = Image.fromarray(n); d = ImageDraw.Draw(img)
    f = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 12); t = FIJOS['GAME PREDICTION']
    b = f.getbbox(t); x = (202 + 288) / 2 - (b[2] - b[0]) / 2
    d.text((x - b[0], 189 - b[3]), t, font=f, fill=(235, 235, 235, 255))
    return img


def main(filtro=''):
    bloques = json.load(open(os.path.join(T, 'telop', 'bloques_extra.json'), encoding='utf-8'))
    ocr = json.load(open(os.path.join(T, 'telop', 'ocr_nuevas.json'), encoding='utf-8'))
    gen = AX.traducciones(); gen_l = {k.lower(): v for k, v in gen.items()}
    P._BLOQUES = bloques
    P.origen = lambda r: os.path.join(T, r)
    atlas_es.TEX, atlas_es.SAL = T, SAL
    es, falta = {}, []
    for k, b in bloques.items():
        if filtro not in k or k.split('/')[-1].startswith('artwork_back_'): continue      # portadas: como el original
        if '/darts' in k and b['en'].strip().upper() in SIN_TOCAR: continue
        t = FIJOS.get(b['en'].strip()) or gen.get(AX.norm(b['en'])) or gen_l.get(AX.norm(b['en']).lower())
        if t is None: falta.append(k); continue
        es[k] = t.replace('\r\n', ' ').replace('\n', ' ').translate(AX.LETRAS)
    os.makedirs(REV, exist_ok=True); avisos = []; n = 0
    for ruta in sorted({k.split('#')[0] for k in es}):
        o = Image.open(P.origen(ruta)).convert('RGBA')
        try:
            if f'{ruta}#pincel' in es:
                img, av = rotulos.dibujar(o, [x.strip() for x in es[f'{ruta}#pincel'].split(' / ')], semilla=len(ruta)), []
            else: img, av = P.traducir_textura(ruta, validas(ocr[ruta]), es)
        except Exception as e: avisos.append(f'{ruta}: ERROR {e!r}'); continue
        if img is None: continue
        if '/darts_countup_' in ruta: img = barra_negra(o, img)
        try: atlas_es.guardar_dds(ruta[:-4], img)
        except Exception as e: avisos.append(f'{ruta}: PENDIENTE {e!r}'); continue
        W, H = o.size
        v = Image.new('RGBA', (W, H * 2), (40, 90, 40, 255)); v.alpha_composite(o); v.alpha_composite(img, (0, H))
        v.convert('RGB').save(os.path.join(REV, ruta.replace('/', '__')[:-4] + '.png')); n += 1
        avisos += [f'{ruta}: {a}' for a in av]
    open(os.path.join(T, 'imagenes', 'avisos_extra.txt'), 'w', encoding='utf-8').write('\n'.join(avisos + ['SIN TRADUCCIÓN: ' + k for k in falta]))
    print('texturas', n, 'bloques traducidos', len(es), 'sin traducción', len(falta), 'avisos', len(avisos))


if __name__ == '__main__': main(next((a for a in sys.argv[1:] if not a.startswith('--')), ''))
