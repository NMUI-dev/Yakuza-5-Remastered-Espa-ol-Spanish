# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) v1.0.1: las 3 páginas de introducción de los dardos (rule_01_0, rule_cricket_0, rule_countup_0)
rehechas DESDE EL ORIGINAL con cajas medidas a mano (la v1.0 y los parches sueltos dejaban «25 or 50POINTS», «CLOSE»,
pestañas «Introducción/Nota» desbordadas, rayas sueltas, ● pisando la letra y textos fuera del marco).
Cada caja: se borra el inglés (cada fila toma el color de fondo de su propia fila, o inpaint si el fondo es un dibujo) y se
escribe el español con la misma altura de mayúscula, color y alineación que el original, sin pasar de su ancho.
Lo que es del marcador DARTSLIVE (BULL, 15〜20+BULL, números) se queda como en el original, igual que en rule_darts_*.
  python herramientas/intro_dardos_v101.py   (va después de dardos_v101.py en regenerar_v101.sh)
"""
import os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
import paginas_v101 as PV
F = 'C:/Windows/Fonts/'
YU, YUB, TB = F + 'YuGothM.ttc', F + 'YuGothB.ttc', F + 'timesbd.ttf'
PIC = 'pausepar_pause_en/picture/'
BLANCO, ROSA = (255, 255, 255), (236, 112, 150)


def fondo_filas(a, c):
    """cada fila de la caja se pinta entera con su color de fondo (la mediana de su 15 % más oscuro: la letra es más clara)"""
    x0, y0, x1, y1 = c
    for y in range(y0, y1):
        f = a[y, x0:x1, :3]; l = f.astype(int).sum(1)
        f[:] = np.median(f[l <= np.percentile(l, 15)], 0).astype(np.uint8)


def fondo_recta(a, c):
    """pestañas en degradado: cada fila va de su color en el borde izquierdo al de la parte limpia de la derecha"""
    x0, y0, x1, y1 = c; k = np.linspace(0, 1, x1 - x0)[:, None]
    for y in range(y0, y1):
        iz = np.median(a[y, x0:x0 + 3, :3].astype(float), 0); de = np.median(a[y, x1 + 2:x1 + 8, :3].astype(float), 0)
        a[y, x0:x1, :3] = np.clip(iz + (de - iz) * k, 0, 255).astype(np.uint8)


def negro(a, c):
    x0, y0, x1, y1 = c; a[y0:y1, x0:x1, :3] = 0


def sello(a, c):
    """sello «CLOSE» sobre el icono del dardo: se quitan las letras (lo brillante y saturado) con inpaint"""
    x0, y0, x1, y1 = c; z = a[y0:y1, x0:x1, :3].astype(int)
    m = np.zeros(a.shape[:2], np.uint8); m[y0:y1, x0:x1] = ((z.max(2) > 150) & (z.max(2) - z.min(2) > 40) | (z.min(2) > 170)) * 255
    m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=1)
    a[..., :3] = cv2.inpaint(np.ascontiguousarray(a[..., :3]), m, 3, cv2.INPAINT_TELEA)


def inpaint(a, c, umbral=60):
    x0, y0, x1, y1 = c; z = a[y0:y1, x0:x1, :3].astype(int)
    m = np.zeros(a.shape[:2], np.uint8); m[y0:y1, x0:x1] = (z.min(2) > umbral) * 255
    m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=2)
    a[..., :3] = cv2.inpaint(np.ascontiguousarray(a[..., :3]), m, 4, cv2.INPAINT_TELEA)


def letra(ruta, cap):
    """fuente cuya mayúscula mide cap px"""
    bb = ImageFont.truetype(ruta, 100).getbbox('H', anchor='ls')
    return ImageFont.truetype(ruta, max(6, round(100 * cap / (bb[3] - bb[1]))))


def escribir(img, t, c, cap, col, ruta=YU, alin='izq', borde=None, estrechar=0.78):
    """texto con su línea base al pie de la caja; si no cabe se estrecha (hasta estrechar) y luego se achica"""
    x0, y0, x1, y1 = c; W = x1 - x0; f = letra(ruta, cap); sw = 2 if borde else 0
    capa = Image.new('RGBA', (int(f.getlength(t)) + 20, int(cap * 2.2) + 10), (0, 0, 0, 0))
    ImageDraw.Draw(capa).text((10, cap * 1.6 + 5), t, font=f, fill=col + (255,), anchor='ls', stroke_width=sw, stroke_fill=borde)
    caja = capa.getbbox(); capa = capa.crop((caja[0], 0, caja[2], capa.height)); base = int(cap * 1.6 + 5)
    cw = capa.width
    if cw > W:
        k = max(estrechar, W / cw); capa = capa.resize((max(1, int(cw * k)), capa.height), Image.LANCZOS)
        if capa.width > W: s = W / capa.width; capa = capa.resize((W, max(1, int(capa.height * s))), Image.LANCZOS); base = int(base * s)
    x = x0 if alin == 'izq' else (x0 + (W - capa.width) // 2 if alin == 'centro' else x1 - capa.width)
    img.alpha_composite(capa, (int(x), int(y1 - base)))


def pestana(a, c):
    """pestaña dorada/roja «Introduction»/«Note»: se repinta su degradado (la letra blanca fuera)"""
    fondo_recta(a, c)


def hacer(nombre, borrar, textos):
    r = PIC + nombre
    o = np.array(Image.open(PV.origen(r + '.dds')).convert('RGBA')); a = o.copy()
    for modo, c in borrar:
        {'filas': fondo_filas, 'recta': fondo_recta, 'inpaint': inpaint, 'negro': negro, 'sello': sello}[modo](a, c)
    img = Image.fromarray(a)
    for t in textos: escribir(img, *t[:4], **(t[4] if len(t) > 4 else {}))
    atlas_es.TEX = os.path.join(PV.T, 'extraido'); atlas_es.SAL = PV.SAL; atlas_es.guardar_dds(r, img)
    H, W = o.shape[:2]; v = Image.new('RGBA', (W, H * 2 + 8), (255, 0, 255, 255))
    v.alpha_composite(Image.fromarray(o)); v.alpha_composite(img, (0, H + 8))
    v.convert('RGB').save(os.path.join(PV.REV, 'I_' + nombre + '.png')); print('ok', nombre, flush=True)


# panel de abajo: renglones de 27 px; «<...>» en x=155, texto tras el ● en x=180
def abajo(lineas, y0=258, paso=27, x=155):
    """lineas: (n.º de renglón, sangría ('' / '●'), texto) -> cajas de borrado y textos"""
    b, t = [], []
    for n, s, txt in lineas:
        yy = y0 + n * paso; xx = 180 if s else x
        b.append(('filas', (xx - 2, yy, 990, yy + paso + 2)))
        t.append((txt, (xx, yy, 990, yy + 22), 19, BLANCO))
    return b, t


def countup():
    b, t = abajo([(0, '', '<Condiciones de victoria>'), (1, '', 'Consigue la puntuación total más alta.'),
                  (3, '', '<Resumen>'), (4, '●', 'Consigue la puntuación más alta.'),
                  (5, '●', 'Compite por el total más alto tras tres rondas.')])
    b += [('filas', (298, 44, 392, 74)), ('filas', (514, 44, 616, 74)), ('filas', (748, 44, 840, 74)),
          ('filas', (290, 104, 962, 137)),
          ('filas', (419, 150, 574, 176)), ('filas', (431, 179, 574, 204)),
          ('filas', (284, 214, 574, 243)), ('filas', (588, 214, 768, 243)), ('filas', (782, 214, 962, 243))]
    t += [('SIMPLE', (290, 46, 392, 70), 17, (225, 225, 225), dict(ruta=TB, alin='der')),
          ('DOBLE', (506, 46, 616, 70), 17, (225, 225, 225), dict(ruta=TB, alin='der')),
          ('TRIPLE', (740, 46, 840, 70), 17, (225, 225, 225), dict(ruta=TB, alin='der')),
          ('Área simple (x1)', (300, 106, 516, 131), 19, BLANCO, dict(alin='centro')),
          ('Área doble (x2)', (522, 106, 734, 131), 19, BLANCO, dict(alin='centro')),
          ('Área triple (x3)', (762, 106, 962, 131), 19, BLANCO, dict(alin='centro')),
          ('25 o 50 PUNTOS', (421, 152, 572, 172), 15, BLANCO, dict(ruta=TB, estrechar=0.62)),
          ('50 PUNTOS', (433, 180, 572, 200), 15, BLANCO, dict(ruta=TB, estrechar=0.62)),
          ('Diana: 25 o 50 pts.', (288, 218, 572, 239), 17, BLANCO, dict(alin='centro')),
          ('Máx.: triple 20.', (590, 218, 766, 239), 17, BLANCO, dict(alin='centro')),
          ('1 ronda = 3 tiros.', (784, 218, 960, 239), 17, BLANCO, dict(alin='centro'))]
    hacer('rule_countup_0', b, t)


def cricket():
    b, t = abajo([(0, '', '<Condiciones de victoria>'), (1, '', 'Consigue la mayor puntuación.'),
                  (2.2, '', '<Resumen>'), (3.2, '●', 'Objetivos válidos: números del 15 al 20 y la diana.'),
                  (4.2, '●', 'Simple: 1 acierto; doble: 2 aciertos; triple: 3 aciertos.'),
                  (5.2, '●', 'Tres aciertos cierran un número (pasa a ser tuyo)'),
                  (6.2, '●', 'y los aciertos siguientes suman puntos.'),
                  (7.2, '●', 'Un número cerrado por todos ya no suma puntos.'),
                  (8.2, '●', 'Gana quien, con más puntos, cierre todos los números.')], y0=258, paso=26.8)
    # (los renglones 6.2 y 8.2 son continuación: sin ● en el original; se escriben en x=180 igual)
    b = [(m, tuple(int(v) for v in c)) for m, c in b]; t = [(x[0], tuple(int(v) for v in x[1])) + x[2:] for x in t]
    b += [('negro', (76, 2, 254, 56)), ('sello', (374, 184, 450, 210)), ('sello', (640, 184, 714, 210)), ('sello', (723, 184, 797, 210)), ('recta', (284, 7, 452, 29)), ('recta', (284, 137, 362, 159)),
          ('filas', (292, 34, 545, 99)), ('filas', (552, 8, 652, 33)), ('filas', (552, 39, 652, 62)), ('filas', (552, 69, 652, 92)),
          ('filas', (848, 52, 960, 82)), ('filas', (290, 98, 960, 125)),
          ('filas', (826, 183, 960, 212)), ('filas', (300, 216, 610, 245)), ('filas', (632, 216, 962, 245))]
    t += [('CRICKET', (80, 6, 250, 27), 17, (232, 214, 150), dict(ruta=TB, alin='centro', borde=(60, 45, 10, 255))),
          ('ESTÁNDAR', (80, 30, 250, 51), 17, (232, 214, 150), dict(ruta=TB, alin='centro', borde=(60, 45, 10, 255))),
          ('Introducción', (288, 8, 450, 27), 14, BLANCO, dict(ruta=YUB)),
          ('Nota', (288, 138, 360, 157), 14, BLANCO, dict(ruta=YUB)),
          ('CERRADO', (376, 188, 448, 206), 14, (240, 110, 150), dict(ruta=TB, alin='centro', borde=(255, 255, 255, 255), estrechar=0.6)),
          ('CERRADO', (642, 188, 712, 206), 14, (240, 110, 150), dict(ruta=TB, alin='centro', borde=(255, 255, 255, 255), estrechar=0.6)),
          ('CERRADO', (725, 188, 795, 206), 14, (130, 110, 230), dict(ruta=TB, alin='centro', borde=(255, 255, 255, 255), estrechar=0.6)),
          ('SIMPLE   1 MARCA', (295, 36, 545, 55), 16, BLANCO, dict(ruta=TB)),
          ('DOBLE    2 MARCAS', (295, 57, 545, 76), 16, ROSA, dict(ruta=TB)),
          ('TRIPLE   3 MARCAS', (295, 78, 545, 97), 16, BLANCO, dict(ruta=TB)),
          ('2 MARCAS', (553, 9, 650, 30), 16, BLANCO, dict(ruta=TB, estrechar=0.6)),
          ('3 MARCAS', (553, 40, 650, 60), 16, ROSA, dict(ruta=TB, estrechar=0.6)),
          ('1 MARCA', (553, 70, 650, 90), 16, BLANCO, dict(ruta=TB, estrechar=0.6)),
          ('CERRADO', (850, 56, 958, 78), 16, ROSA, dict(ruta=TB, alin='centro')),
          ('Cierra un número acertándolo tres veces.', (296, 99, 960, 121), 19, BLANCO),
          ('SIN PUNTOS', (828, 186, 958, 208), 16, ROSA, dict(ruta=TB, alin='centro')),
          ('Acierta uno cerrado y suma pts.', (302, 220, 608, 241), 17, BLANCO, dict(alin='centro')),
          ('Sin pts si todos lo cerraron.', (634, 220, 960, 241), 17, BLANCO, dict(alin='centro'))]
    hacer('rule_cricket_0', b, t)


def juegos01():
    b, t = abajo([(0, '', '<Condiciones de victoria>'), (1, '', 'Sé el primero en reducir tu puntuación exactamente a cero.'),
                  (3, '', '<Resumen>'), (4, '●', 'Reduce tu puntuación a cero.'), (5, '●', 'Si bajas de cero, te pasas.'),
                  (6, '●', 'Al pasarte, el turno cambia de inmediato. Tu puntuación'),
                  (7, '●', 'vuelve a la que tenías al inicio de la ronda.')])
    b += [('filas', (86, 4, 246, 34)), ('recta', (284, 7, 452, 29)), ('recta', (284, 146, 384, 168)),
          ('filas', (292, 102, 960, 133)), ('filas', (528, 172, 660, 216)), ('filas', (292, 216, 666, 243))]
    t += [('JUEGOS 01', (86, 8, 246, 29), 17, (238, 225, 222), dict(ruta=TB, alin='centro', borde=(120, 30, 30, 255))),
          ('Introducción', (288, 8, 450, 27), 14, BLANCO, dict(ruta=YUB)),
          ('Nota', (288, 147, 380, 166), 14, BLANCO, dict(ruta=YUB)),
          ('Objetivo: reduce tu puntuación exactamente a cero.', (298, 104, 958, 127), 19, BLANCO),
          ('PASA', (532, 176, 656, 211), 30, (205, 150, 110), dict(ruta=TB, alin='centro', borde=(80, 40, 20, 255))),
          ('Si bajas de cero, te pasas.', (298, 218, 662, 239), 17, BLANCO)]
    hacer('rule_01_0', b, t)


if __name__ == '__main__':
    countup(); cricket(); juegos01()
