# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) v1.0.1: arreglos a mano de las páginas de DARDOS y sueltas (el fondo DARTSLIVE confunde al programa
de páginas). Se parte de la v1.0 (trabajo/imagenes/es) y solo se tocan las zonas con fallo, localizadas por el texto inglés
del ORIGINAL (OCR a doble tamaño de paginas_v101.ocr2x):
  bocadillo  texto oscuro en recuadro blanco (marcador, leyenda 1 Hit...): se repone el original y se escribe centrado
  panel      renglones blancos/de color del panel de abajo: se repone el original de todos y se escribe el párrafo centrado
  linea      un renglón suelto: se repone, se borra y se escribe en su sitio (alineado a la izquierda)
  orig       se deja como el original (BUST, nombres...)
  titulo     el rótulo de arriba se copia de otra página de la v1.0 que lo tiene bien
  -> trabajo/imagenes/es_v101/<ruta>.dds + revision_v101/rehechas/<nombre>.png
  python herramientas/dardos_v101.py
"""
import os, sys, re, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
import paginas_v101 as PV
import paginas_es as P
T = PV.T; ES = os.path.join(T, 'imagenes', 'es'); SAL = PV.SAL; REV = PV.REV
SEG, SEGB = 'C:/Windows/Fonts/seguisb.ttf', 'C:/Windows/Fonts/segoeuib.ttf'
PIC = 'pausepar_pause_en/picture/'
TIT_01 = (PIC + 'rule_darts_01_1.dds', '01 GAME RULE')
TIT_CU = (PIC + 'rule_darts_countup_0.dds', 'COUNT-UP RULE')
TIT_CR = (PIC + 'rule_darts_cricket_02.dds', 'CRICKET GAME RULE')
GANA = ('bocadillo', 'The higher score wins.', 'Gana la puntuación más alta.')
ESTANDAR = ('panel', ['STANDARD: Player with the highest score wins.'], 'ESTÁNDAR: gana el jugador con más puntos.')

TRABAJO = {
    PIC + 'rule_darts_01_3.dds': [('titulo', TIT_01), ('orig', 'BUST', 175)],
    PIC + 'rule_darts_countup_0.dds': [('panel', ['Starting from zero points, compete for the highest', 'point total in a predetermined number of rounds.'],
                                        'Empezando desde cero, compite por la puntuación total más alta en un número fijo de rondas.')],
    PIC + 'rule_darts_countup_1.dds': [GANA, ('orig', 'COUNT-UP')],
    PIC + 'rule_darts_cricket_01.dds': [GANA, ESTANDAR],
    PIC + 'rule_darts_cricket_02.dds': [('bocadillo', '1 Hit', '1 acierto'), ('bocadillo', '2@0+Hits@0', '2 aciertos'), ('bocadillo', '3@0+Hits@1', '3 aciertos'),
                                        ('panel', ['Players try to hit numbers three times to close them.', 'A scoreboard is used to show the number of hits for each number.'],
                                         'Los jugadores intentan acertar tres veces cada número para cerrarlo. Un marcador muestra los aciertos de cada número.')],
    PIC + 'rule_darts_cricket_03.dds': [('orig', 'SINGLE 18'), ('orig', 'DOURIE 18'), ('bocadillo', 'Closed', 'Cerrado'),
                                        ('panel', ['Hits on a closed number score points.', 'A number no longer yields points if all players have closed it.'],
                                         'Los aciertos en un número cerrado suman puntos. Un número deja de sumar si todos los jugadores lo han cerrado.')],
    PIC + 'rule_darts_cricket_05.dds': [GANA, ESTANDAR],
    PIC + 'rule_darts_cricket_09.dds': [GANA, ESTANDAR],
    PIC + 'rule_darts_cricket_10.dds': [('titulo', TIT_CR), ('orig', 'BULL', 60), ('bocadillo', '1 Hit', '1 acierto'), ('bocadillo', '2@0+Hits@0', '2 aciertos'),
                                        ('bocadillo', '3@0+Hits@1', '3 aciertos'), ('bocadillo', '1 Hit + Open Bonus', '1 acierto + bono')],
    PIC + 'rule_darts_cricket_11.dds': [('titulo', TIT_CR), ('orig', 'SINGLE@0+BULL', 40), ('orig', 'SINGLE@1+8'), ('bocadillo', 'Closed', 'Cerrado')],
    PIC + 'rule_countup_0.dds': [('linea', 'Single Area(x1)', 'Área simple (x1)'), ('linea', 'Double Area(x2)', 'Área doble (x2)'),
                                 ('linea', 'Triple Area(x3)', 'Área triple (x3)'), ('linea', "Bull's-eye: 25 or 50 pts.", 'Diana: 25 o 50 pts.'),
                                 ('linea', 'Max Pts: Triple 20.', 'Máx.: triple 20.'), ('linea', '1 round = 3 throws.', '1 ronda = 3 tiros.'),
                                 ('orig', 'BULL'), ('orig', '25 or 50POINTS'), ('orig', '50POINTS')],
    PIC + 'rule_cricket_0.dds': [('linea', 'NO POINT', 'SIN PUNTOS', 0.75)],
    PIC + 'rule_button_bb.dds': [('linea', 'Back', 'Atrás')],
}


def caja(ruta, ancla, xmin=0.0):
    """«a+b»: une las cajas de a y b (b la más cercana a a); «a@n»: la n-ésima coincidencia exacta"""
    if '+' in ancla and ancla not in ('1 Hit + Open Bonus',):
        cs = [caja(ruta, x, xmin) for x in ancla.split('+')]
        return [min(c[0] for c in cs), min(c[1] for c in cs), max(c[2] for c in cs), max(c[3] for c in cs), ancla]
    ls = PV.ocr2x(ruta); W = Image.open(PV.origen(ruta)).size[0]
    if '@' in ancla:
        t, i = ancla.rsplit('@', 1); c = [l for l in ls if PV.norm(l[4]) == PV.norm(t)]
        return c[int(i)]
    n = PV.norm(ancla)
    c = [l for l in ls if l[0] >= xmin * W and (PV.norm(l[4]) == n)] or [l for l in ls if l[0] >= xmin * W and n and n in PV.norm(l[4])]
    if not c: raise SystemExit(f'{ruta}: no encuentro «{ancla}» en el OCR del original')
    return max(c, key=lambda l: l[0]) if xmin else c[0]


def ajustar(texto, ruta_f, tam, ancho):
    while tam > 8 and ImageFont.truetype(ruta_f, tam).getlength(texto) > ancho: tam -= 1
    return ImageFont.truetype(ruta_f, tam)


def color_de(a, l, claro):
    z = a[l[1]:l[3], l[0]:l[2], :3].reshape(-1, 3).astype(int); s = z.sum(1)
    sel = z[s > np.percentile(s, 80)] if claro else z[s < np.percentile(s, 20)]
    return tuple(int(v) for v in np.median(sel, 0)) + (255,)


def rehacer(ruta, ops):
    o = np.array(Image.open(PV.origen(ruta)).convert('RGBA')); H, W = o.shape[:2]
    _s = os.path.join(SAL, ruta); a = np.array(Image.open(_s if os.path.exists(_s) and ('rule_countup_0' in ruta or 'rule_cricket_0' in ruta) else os.path.join(ES, ruta)).convert('RGBA'))
    dib = []
    for op in ops:
        k = op[0]
        if k == 'titulo':
            src, ancla = op[1]; l = caja(ruta, ancla)
            x0, y0, x1, y1 = max(0, l[0] - 40), max(0, l[1] - 8), min(W, l[2] + 40), min(H, l[3] + 8)
            a[y0:y1, x0:x1] = np.array(Image.open(os.path.join(ES, src)).convert('RGBA'))[y0:y1, x0:x1]
        elif k == 'orig':
            l = caja(ruta, op[1]); px = op[2] if len(op) > 2 else 6
            x0, y0, x1, y1 = max(0, l[0] - px), max(0, l[1] - 4), min(W, l[2] + px), min(H, l[3] + 4)
            a[y0:y1, x0:x1] = o[y0:y1, x0:x1]
        elif k in ('bocadillo', 'linea'):
            l = list(caja(ruta, op[1], op[3] if len(op) > 3 else 0.0))
            if k == 'bocadillo':   # el recuadro blanco entero (más ancho que el texto inglés)
                ym = (l[1] + l[3]) // 2
                while l[0] > 2 and o[ym, l[0] - 1, :3].min() > 170: l[0] -= 1
                while l[2] < W - 2 and o[ym, l[2], :3].min() > 170: l[2] += 1
                l[0] += 4; l[2] -= 4
            x0, y0, x1, y1 = max(0, l[0] - 6), max(0, l[1] - 3), min(W, l[2] + 6), min(H, l[3] + 3)
            a[y0:y1, x0:x1] = o[y0:y1, x0:x1]
            if k == 'bocadillo':   # (sin inpaint: cada fila del recuadro blanco se rellena con su propio blanco)
                col = (40, 40, 44, 255)
                for y in range(max(0, l[1] - 2), min(H, l[3] + 2)):
                    fila = a[y, l[0]:l[2], :3]; br = fila.min(1) > 170
                    if br.sum() > 3: fila[~br] = np.median(fila[br], 0).astype(np.uint8)
            else:
                claro = o[l[1]:l[3], l[0]:l[2], :3].mean() < 128
                col = (236, 236, 236, 255) if claro else color_de(o, l, False)
                a = PV.borrar(a, [[l[0] - 2, l[1], l[2] + 2, l[3]]])
            dib.append((k, l, op[2], col))
        elif k == 'panel':
            ls = [caja(ruta, x) for x in op[1]]
            x0, y0 = int(0.04 * W), min(l[1] for l in ls) - 3   # (25-10) el ancho entero del panel: la v1.0 se salía
            x1, y1 = int(0.99 * W), max(l[3] for l in ls) + 3
            a[y0:y1, x0:x1] = o[y0:y1, x0:x1]
            col = color_de(o, ls[0], True)
            a = PV.borrar(a, [[l[0] - 2, l[1], l[2] + 2, l[3]] for l in ls])
            dib.append(('panel', ls, op[2], col))
    img = Image.fromarray(a); d = ImageDraw.Draw(img)
    for k, l, texto, col in dib:
        if k == 'panel':
            alto = l[0][3] - l[0][1]; paso = (l[1][1] - l[0][1]) if len(l) > 1 else round(alto * 1.3); cx = (min(x[0] for x in l) + max(x[2] for x in l)) / 2
            ancho = max(x[2] for x in l) - min(x[0] for x in l) + 30
            for tam in range(round(alto * 0.95), 8, -1):
                f = ImageFont.truetype(SEG, tam); rs = P.partir(texto, f, ancho)
                if len(rs) <= len(l): break
            for j, x in enumerate(rs):
                d.text((cx, l[0][1] + alto / 2 + j * paso), x, font=f, fill=col, anchor='mm')
        else:
            alto = l[3] - l[1]; ancho = (l[2] - l[0]) * (1.0 if k == 'bocadillo' else 1.15)
            f = ajustar(texto, SEG, round(alto * 0.95), ancho)
            if k == 'bocadillo': d.text(((l[0] + l[2]) / 2, (l[1] + l[3]) / 2), texto, font=f, fill=col, anchor='mm')
            else: d.text((l[0], (l[1] + l[3]) / 2), texto, font=f, fill=col, anchor='lm')
    atlas_es.TEX = os.path.join(T, 'extraido'); atlas_es.SAL = SAL
    atlas_es.guardar_dds(ruta[:-4], img)
    v = Image.new('RGBA', (W * 2 + 12, H), (200, 0, 200, 255)); v.alpha_composite(Image.fromarray(o)); v.alpha_composite(img, (W + 12, 0))
    v.convert('RGB').save(os.path.join(REV, ruta.split('/')[-1][:-4] + '.png'))


if __name__ == '__main__':
    for r, ops in TRABAJO.items():
        if len(sys.argv) > 1 and not any(x in r for x in sys.argv[1:]): continue
        rehacer(r, ops); print('ok', r, flush=True)
