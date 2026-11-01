# -*- coding: utf-8 -*-
"""(01-11-2026, claude1) Las 189 líneas de LETRA del karaoke (minigame_en/karaoke_e.par, 2d_jm_ok_*.dds, 512x64): borrar
y escribir encima dejaba restos del inglés y cada línea con su tamaño. Se REHACEN enteras: textura vacía y la línea en
español en blanco con borde negro, a la izquierda (x 3) y a la misma altura que el original; si no cabe en 506 px se
estrecha. Traducción: la del lote (bloque del OCR); las 11 líneas que el OCR partió en trozos, enteras aquí (A_MANO).
Salida: trabajo/imagenes/es_extra/<ruta>.dds + revision_extra/letra__*.png
  python herramientas/karaoke_letras_es.py [--ingles]     (--ingles: dibuja el inglés, para comparar con el original)"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv, _argv = sys.argv[:1], sys.argv
import aplicar_extra as AX
sys.argv = _argv
import atlas_es
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
CARP = 'barrido_3110/x/minigame_en/karaoke_e.par_par/karaoke_e/'
FUENTE, TAM, LETRA, PALABRA, BORDE = 'C:/Windows/Fonts/arialbd.ttf', 23, -1.75, 2.5, 1   # ajustado al inglés original
X0, ANCHO, ARRIBA = 3, 506, 20                   # margen, ancho útil, arriba de la mayúscula (con borde) en el original
A_MANO = {   # textura: (inglés entero, español)
    'bakamitai05': ('"I love you" is', '"Te quiero" es'),
    'get_to_the_top21': ('We will reach a new peak', 'Alcanzaremos una nueva cima'),
    'kimi_ha_irukara11': ("I'm gonna make it", 'Lo voy a lograr'),
    'kimi_ha_irukara18': ("I don't know where you are, but I know you can see", 'No sé dónde estás, pero sé que puedes ver'),
    'loneliness_loop02': ("That's what your twisted love has turned me into", 'En eso me ha convertido tu amor retorcido'),
    'loneliness_loop16': ("That's what your twisted love has turned me into", 'En eso me ha convertido tu amor retorcido'),
    'loneliness_loop05': ('Your smile it cuts me in two, in its sorrow', 'Tu sonrisa me parte en dos con su tristeza'),
    'loneliness_loop19': ('Your smile it cuts me in two, in its sorrow', 'Tu sonrisa me parte en dos con su tristeza'),
    'rain_drops17': ('Coming like rain in the dead of night', 'Llegando como lluvia en plena noche'),
    'rain_drops22': ('Turning into drops of rain falling forever', 'Convirtiéndose en gotas de lluvia que caen sin fin'),
    'rouge_of_love06': ('I\'m so over, men and this "love" business', 'Estoy harta de los hombres y de este rollo del "amor"'),
    'rouge_of_love07': ("They don't mean a thing to me, throw it all away", 'No significan nada para mí, lo tiro todo por la borda')}


def dibujar(texto):
    f = ImageFont.truetype(FUENTE, TAM)
    w = int(sum(f.getlength(c) for c in texto) + LETRA * (len(texto) - 1) + PALABRA * texto.count(' ')) + 2 * BORDE + 4
    capa = Image.new('RGBA', (max(w, ANCHO), 64), (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
    x, y = BORDE, ARRIBA + BORDE - f.getbbox('H')[1]
    for c in texto:
        d.text((x, y), c, font=f, fill=(255, 255, 255, 255), stroke_width=BORDE, stroke_fill=(0, 0, 0, 255))
        x += f.getlength(c) + LETRA + (PALABRA if c == ' ' else 0)
    if capa.width > ANCHO: capa = capa.resize((ANCHO, 64), Image.LANCZOS)       # no cabe: más estrecha
    img = Image.new('RGBA', (512, 64), (0, 0, 0, 0)); img.alpha_composite(capa.crop((0, 0, ANCHO, 64)), (X0 - BORDE, 0))
    return img, w > ANCHO


def main():
    ingles = '--ingles' in sys.argv
    bloques = json.load(open(os.path.join(T, 'telop', 'bloques_extra.json'), encoding='utf-8'))
    gen = AX.traducciones(); gen_l = {k.lower(): v for k, v in gen.items()}
    atlas_es.TEX, atlas_es.SAL = T, os.path.join(T, 'imagenes', 'es_extra')
    rev = os.path.join(T, 'imagenes', 'revision_extra'); os.makedirs(rev, exist_ok=True)
    rutas = sorted({k.split('#')[0] for k in bloques if k.startswith(CARP + '2d_jm_ok_')})
    n = estrechas = 0; falta = []
    for ruta in rutas:
        nom = ruta[len(CARP) + len('2d_jm_ok_'):-4]
        if nom in A_MANO: en, es = A_MANO[nom]
        else:
            en = bloques[ruta + '#0']['en']
            es = gen.get(AX.norm(en)) or gen_l.get(AX.norm(en).lower())
        if es is None: falta.append(ruta); continue
        es = es.strip().replace('“', '"').replace('”', '"').replace('""', '"')
        if en[:1].isupper() and es[:1].islower(): es = es[0].upper() + es[1:]      # «vuela lejos» -> «Vuela lejos»
        img, estrecha = dibujar(en if ingles else es); estrechas += estrecha
        o = Image.open(os.path.join(T, ruta)).convert('RGBA')
        if not ingles: atlas_es.guardar_dds(ruta[:-4], img)
        v = Image.new('RGBA', (512, 128), (30, 30, 120, 255)); v.alpha_composite(o); v.alpha_composite(img, (0, 64))
        v.convert('RGB').save(os.path.join(rev, ('EN_' if ingles else '') + 'letra__' + nom + '.png')); n += 1
    print('líneas', n, 'estrechadas', estrechas, 'sin traducción', falta)


if __name__ == '__main__': main()
