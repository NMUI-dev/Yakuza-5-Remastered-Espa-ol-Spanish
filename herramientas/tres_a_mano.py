# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) Las 3 páginas que quedaron en inglés en la v1.0 (cricket 06/07 y ranking del Coliseo), rehechas a
mano: se borra la tinta inglesa (cv2.inpaint sobre su máscara) y se escribe el español centrado en su hueco.
RESERVA: el usuario las quiere guardadas y solo se añaden si alguien se queja. Salida: trabajo/imagenes/es_reserva/<ruta>.dds
y trabajo/imagenes/revision_reserva/<nombre>.png (arriba original, abajo español).
Uso: python herramientas/tres_a_mano.py"""
import os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import atlas_es

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
atlas_es.TEX = os.path.join(T, 'extraido')
atlas_es.SAL = os.path.join(T, 'imagenes', 'es_reserva')
REV = os.path.join(T, 'imagenes', 'revision_reserva'); os.makedirs(REV, exist_ok=True)
SEG, SEGB = 'C:/Windows/Fonts/seguisb.ttf', 'C:/Windows/Fonts/segoeuib.ttf'
GEO, GEOB = 'C:/Windows/Fonts/georgia.ttf', 'C:/Windows/Fonts/georgiab.ttf'

def abrir(n): return Image.open(os.path.join(T, 'extraido', n + '.dds')).convert('RGBA')

def borrar(img, caja, umbral=150, dil=3):
    """borra la tinta CLARA de la caja (x0, y0, x1, y1) rellenando con lo de alrededor"""
    a = np.array(img); x0, y0, x1, y1 = caja
    rgb = np.ascontiguousarray(a[..., :3]); m = np.zeros(a.shape[:2], np.uint8)
    m[y0:y1, x0:x1] = (rgb[y0:y1, x0:x1].max(axis=2) > umbral).astype(np.uint8) * 255
    m = cv2.dilate(m, np.ones((dil, dil), np.uint8))
    a[..., :3] = cv2.inpaint(rgb, m, 5, cv2.INPAINT_TELEA)
    return Image.fromarray(a)

def centrado(d, cx, y, s, f, fill, sombra=None):
    w = d.textlength(s, font=f)
    if sombra: d.text((cx - w / 2 + 2, y + 2), s, font=f, fill=sombra)
    d.text((cx - w / 2, y), s, font=f, fill=fill)

def ajustar(d, s, ruta, tam, ancho):
    while tam > 10 and d.textlength(s, font=ImageFont.truetype(ruta, tam)) > ancho: tam -= 1
    return ImageFont.truetype(ruta, tam)

def titulo_cricket(img):
    """el rótulo «REGLAS DEL CRICKET» ya hecho en la página 05 de la v1.0 (mismo rótulo, misma posición)"""
    hecho = Image.open(os.path.join(T, 'imagenes', 'es', 'pausepar_pause_en', 'picture', 'rule_darts_cricket_05.dds')).convert('RGBA')
    caja = (300, 4, 724, 62); img.paste(hecho.crop(caja), caja[:2]); return img

def etiqueta(img, caja, s):
    """recuadro blanco de la leyenda (1 Hit, Closed): se repinta con su propio degradado (columna del borde derecho)"""
    x0, y0, x1, y1 = caja; a = np.array(img)
    col = a[y0:y1, x1 - 4:x1 - 3].copy()
    a[y0:y1, x0 + 2:x1 - 3] = np.repeat(col, x1 - 3 - x0 - 2, axis=1)
    img = Image.fromarray(a); d = ImageDraw.Draw(img)
    f = ajustar(d, s, SEG, 20, x1 - x0 - 14)
    centrado(d, (x0 + x1) / 2, y0 + (y1 - y0 - 26) / 2, s, f, (40, 40, 44, 255))
    return img

def panel(img, lineas):
    """panel inferior: «Resumen del juego» + 2 renglones"""
    img = borrar(img, (142, 360, 884, 486), umbral=140)
    d = ImageDraw.Draw(img)
    centrado(d, 512, 366, '«Resumen del juego»', ImageFont.truetype(SEG, 24), (255, 255, 255, 255))
    for i, s in enumerate(lineas):
        centrado(d, 512, 408 + i * 32, s, ajustar(d, s, SEG, 21, 730), (255, 255, 255, 255))
    return img

def guardar(n, img):
    atlas_es.guardar_dds(n, img)
    o = abrir(n); W, H = o.size
    v = Image.new('RGBA', (W, H * 2), (40, 90, 40, 255)); v.alpha_composite(o); v.alpha_composite(img, (0, H))
    p = os.path.join(REV, n.split('/')[-1] + '.png'); v.convert('RGB').save(p); print('ok', p)

# 06: leyenda de aciertos
n = 'pausepar_pause_en/picture/rule_darts_cricket_06'
img = titulo_cricket(abrir(n))
for i, s in enumerate(['1 acierto', '2 aciertos', '3 aciertos']):
    img = etiqueta(img, (616, 121 + i * 28, 761, 145 + i * 28), s)
img = panel(img, ['Los jugadores intentan acertar tres veces en cada número para cerrarlo.',
                  'Un marcador muestra los aciertos de cada número.'])
guardar(n, img)

# 07: «Closed» (SINGLE/DOUBLE 11 es el marcador DARTSLIVE: se queda como en la 05, igual que TEMP POINTS)
n = 'pausepar_pause_en/picture/rule_darts_cricket_07'
img = titulo_cricket(abrir(n))
img = etiqueta(img, (616, 177, 761, 201), 'Cerrado')
img = panel(img, ['Los aciertos en un número cerrado suman puntos.',
                  'Un número deja de sumar cuando todos los jugadores lo han cerrado.'])
guardar(n, img)

# Ranking del Coliseo (título lila con brillo + 7 renglones; letra con serifa como el original)
n = 'pausepar_tougijyo_en/2d_jm_tougi_okite_ranking'
img = abrir(n)
img = borrar(img, (180, 40, 845, 90), umbral=110, dil=7)
img = borrar(img, (170, 140, 860, 430), umbral=75, dil=7)   # (25-10) 140 dejaba restos claros del inglés
d = ImageDraw.Draw(img)
t = 'Clasificación del Coliseo Subterráneo'
centrado(d, 512, 46, t, ajustar(d, t, GEOB, 30, 600), (226, 210, 250, 255), sombra=(60, 40, 90, 255))
texto = ['La Clasificación del Coliseo Subterráneo muestra el rango',
         'general de cada luchador según un sistema de puntos.',
         'Ganar torneos y exhibiciones aumenta tus puntos de',
         'clasificación, mientras que perder los reduce.',
         'Ganas más puntos de clasificación si derrotas',
         'a un rival de mayor rango.',
         '¡Sigue ganando y llega a lo más alto de la clasificación!']
f = min((ajustar(d, s, GEO, 26, 670) for s in texto), key=lambda x: x.size)   # mismo tamaño en todos los renglones
for i, s in enumerate(texto):
    d.text((180, 145 + i * 42), s, font=f, fill=(240, 240, 240, 255))
guardar(n, img)

# (25-10) Las cuatro leyes del Nuevo Coliseo (la v1.0 solo traducía el renglón 1)
n = 'pausepar_tougijyo_en/2d_jm_tougi_okite'
img = abrir(n)
img = borrar(img, (180, 40, 845, 90), umbral=110, dil=7)
img = borrar(img, (140, 140, 900, 425), umbral=80, dil=7)
d = ImageDraw.Draw(img)
t = 'Las cuatro leyes del Nuevo Coliseo'
centrado(d, 512, 46, t, ajustar(d, t, GEOB, 30, 600), (226, 210, 250, 255), sombra=(60, 40, 90, 255))
reglas = [('1.', 'En el formato de torneo, 8 hombres o 8 equipos', 'compiten por la victoria.'),
          ('2.', 'En el formato de exhibición, el último hombre en pie', 'se proclama vencedor.'),
          ('3.', 'Entre combates se recupera el 30 % de la vida máxima.', None),
          ('4.', 'El ganador recibe un premio en efectivo y', 'puntos del Coliseo.')]
f = min((ajustar(d, s, GEO, 26, 640) for _, s, _ in reglas), key=lambda x: x.size)
for (num, a1, a2), y in zip(reglas, (147, 225, 307, 354)):
    d.text((157, y), num, font=f, fill=(240, 240, 240, 255))
    d.text((197, y), a1, font=f, fill=(240, 240, 240, 255))
    if a2: d.text((197, y + 33), a2, font=f, fill=(240, 240, 240, 255))
guardar(n, img)
