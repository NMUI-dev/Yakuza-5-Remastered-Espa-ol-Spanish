# -*- coding: utf-8 -*-
"""(01-11-2026, claude1) Los 9 rótulos de escena de auth_telop_en.par («A year and a half earlier / Morning Glory
Orphanage, Okinawa»): el OCR los leyó a palabras sueltas, así que se REHACEN enteros con la frase completa del lote 368.
Textura 1024x128 transparente: renglones blancos en cursiva con sombra gris oscura, alineados a la izquierda, con el
renglón más largo terminando en x≈944 (como el original). Letra: Candara negrita cursiva (Windows) con aire entre letras.
Salida: trabajo/imagenes/es_extra/<ruta>.dds + revision_extra/*.png     python herramientas/telops_es.py [--ingles]
  --ingles: dibuja el inglés con el mismo método (para comparar con el original)."""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
CARP = 'barrido_3110/x/auth_telop/auth_telop_en.par_par/'
FUENTE = 'C:/Windows/Fonts/candaraz.ttf'
CIFRAS = 'C:/Windows/Fonts/calibriz.ttf'
TAM, LETRA, PALABRA = 48, 2.0, 10       # cuerpo, aire entre letras y entre palabras: ajustados al ancho del inglés original
FIN_X, Y = 944, (14, 74)                  # fin del renglón más largo; arriba de cada renglón (mayúsculas)
TEXTOS = {   # textura: id del lote 368
    '2d30': 80632, 'c3010_telop': 80632, '2d31': 80633, '2dabashiri': 80634, '2dkamuro': 80635,
    '2dkamuro02': 80636, '2dnagasu': 80637, '2dyoku': 80638, '2dyokuasa': 80639}


def cifras(tam):
    """Las cifras de Candara son «antiguas» (2011 en minúscula) y el original las lleva altas: van con Calibri negrita
    cursiva, del alto de una mayúscula de Candara."""
    f = ImageFont.truetype(FUENTE, tam); h = f.getbbox('H')[3] - f.getbbox('H')[1]
    g = ImageFont.truetype(CIFRAS, tam); return ImageFont.truetype(CIFRAS, round(tam * h / (g.getbbox('2')[3] - g.getbbox('2')[1])))


def fuente_de(c, f, fd):
    return fd if c.isdigit() else f


def largo(r, f, fd):
    return sum(fuente_de(c, f, fd).getlength(c) for c in r) + LETRA * (len(r) - 1) + PALABRA * r.count(' ')


def dibujar(renglones):
    tam = TAM
    while True:
        f, fd = ImageFont.truetype(FUENTE, tam), cifras(tam)
        x0 = FIN_X - max(largo(r, f, fd) for r in renglones)
        if x0 >= 24 or tam < 20: break
        tam -= 1
    capa = Image.new('L', (1024, 128), 0); d = ImageDraw.Draw(capa)
    for i, r in enumerate(renglones):
        x = x0 - 3 * i
        base = Y[i] + f.getbbox('H')[3] - f.getbbox('H')[1]          # línea de base: bajo la mayúscula
        for c in r:
            g = fuente_de(c, f, fd)
            d.text((x, base - g.getbbox('H' if g is f else '2')[3]), c, font=g, fill=255)
            x += g.getlength(c) + LETRA + (PALABRA if c == ' ' else 0)
    sombra = capa.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    sombra = Image.fromarray((np.asarray(sombra, float) * 1.0).clip(0, 255).astype(np.uint8))
    img = Image.new('RGBA', (1024, 128), (0, 0, 0, 0))
    img.paste(Image.new('RGBA', (1024, 128), (40, 40, 40, 255)), (2, 2), sombra)
    img.alpha_composite(Image.merge('RGBA', [Image.new('L', (1024, 128), 255)] * 3 + [capa]))
    return img


def main():
    ingles = '--ingles' in sys.argv
    L = os.path.join(T, 'lotes')
    tx = {x['id']: x['en'] for x in json.load(open(os.path.join(L, 'lote_368.json'), encoding='utf-8'))}
    es = json.load(open(os.path.join(L, 'lote_368_es.json'), encoding='utf-8'))
    atlas_es.TEX, atlas_es.SAL = T, os.path.join(T, 'imagenes', 'es_extra')
    rev = os.path.join(T, 'imagenes', 'revision_extra'); os.makedirs(rev, exist_ok=True)
    for n, i in TEXTOS.items():
        texto = tx[i] if ingles else es[str(i)]
        img = dibujar([r.strip() for r in texto.split(' / ')])
        o = Image.open(os.path.join(T, CARP + n + '.dds')).convert('RGBA')
        if not ingles: atlas_es.guardar_dds(CARP + n, img)
        v = Image.new('RGBA', (1024, 256), (40, 60, 90, 255)); v.alpha_composite(o); v.alpha_composite(img, (0, 128))
        v.convert('RGB').save(os.path.join(rev, ('EN_' if ingles else '') + 'telop__' + n + '.png'))
        print(n, texto)


if __name__ == '__main__': main()
