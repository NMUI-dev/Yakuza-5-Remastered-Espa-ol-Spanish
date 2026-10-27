# -*- coding: utf-8 -*-
"""(claude1, 25-10-2026) v1.0.1: rehace desde el ORIGINAL las 8 páginas de reglas del bacará (rule_baccarat3..6 y
rule_baccarat_s_2..5) con un texto revisado a mano y un solo estilo por página (claude2 me las pasó con faltas: título sin
traducir, viñeta perdida, motas en las tablas, renglones de distinto tamaño, «Reglas del Baccarat», «realizada en EMPATE»).
  - se borra solo la tinta de cada renglón inglés (oscura sobre papel / clara sobre gris) y se rellena con su fondo;
  - las celdas de números que no cambian NO se tocan; la viñeta • del original se conserva;
  - Segoe UI del alto medido del inglés, mismo tamaño para todo el texto de la página, color medido;
  - fuera de lo tocado, bloques DXT originales.
  python -I herramientas/bacara_v101.py  -> trabajo/imagenes/es_v101/pausepar_pause_en/picture/rule_baccarat*.dds
"""
import json, os, struct, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(R, 'trabajo'); ORIG = os.path.join(T, 'extraido'); SAL = os.path.join(T, 'imagenes', 'es_v101')
REV = os.path.join(T, 'imagenes', 'revision_v101', 'bacara'); os.makedirs(REV, exist_ok=True)
SEG = 'C:/Windows/Fonts/YuGothM.ttc'   # Yu Gothic Medium: la más parecida a la letra del juego (ancha, cifras iguales)
P = 'pausepar_pause_en/picture/'

# por renglón inglés (como lo lee el OCR, normalizado): español
T3 = {'Theconditionsfordealingathirdcardareknownasthe': 'Las condiciones para repartir una tercera carta se conocen como',
      "player'sruleandthebanker'srule.": 'la regla del jugador y la regla de la banca.',
      "Player'sRule:": 'Regla del jugador:',
      'Thefollowingtableshowstheconditionsunderwhich': 'La siguiente tabla muestra las condiciones en las que',
      'theplayerisdealtathirdcard.': 'se reparte una tercera carta al jugador.',
      "Player'sTwo-cardPointTotal": 'Total de 2 cartas del jugador',
      '0,1,2,3,4,0r5': '0, 1, 2, 3, 4 o 5'}
T4 = {"Banker'sRule(iftheplayerhasbeendealtathirdcard):": 'Regla de la banca (si el jugador recibió una tercera carta):',
      'Thefollowingtableshowstheconditionsunderwhich': 'La siguiente tabla muestra las condiciones en las que',
      'thebankerisdealtathirdcard.': 'se reparte una tercera carta a la banca.',
      "Banker'sTwo-cardPointTotal": 'Total de 2 cartas de la banca',
      "ValueofPlayer'sThirdCard": 'Valor de la 3.ª carta del jugador',
      '0,1,or2': '0, 1 o 2'}
T5 = {"Banker'sRule(iftheplayerhasnotbeendealtathirdcard):": 'Regla de la banca (si el jugador no recibió una tercera carta):',
      'Thefollowingtableshowstheconditionsunderwhich': 'La siguiente tabla muestra las condiciones en las que',
      'thebankerisdealtathirdcard.': 'se reparte una tercera carta a la banca.',
      "Banker'sTwo-cardPointTotal": 'Total de 2 cartas de la banca',
      '0,1,2,3,4,0r5': '0, 1, 2, 3, 4 o 5'}
T6 = {'Thefollowingtableshowsthepayoutforwinning.': 'La siguiente tabla muestra el pago por ganar.',
      'BetandResult': 'Apuesta y resultado', 'Payout': 'Pago',
      'SuccessfullybetonPLAYER': 'Apuesta acertada a JUGADOR', 'SuccessfullybetonBANKER': 'Apuesta acertada a BANCA',
      'SuccessfullybetonTlE': 'Apuesta acertada a EMPATE'}
TS2 = {'Thegameproceedsasfollows:': 'El juego se desarrolla así:',
       '1.Betononeoffivepossiblehandoutcomes.': '1. Apuesta a uno de los cinco resultados posibles de la mano.',
       '2.Theplayerandbankeraredealttwocardseach.': '2. Se reparten dos cartas al jugador y a la banca.',
       '3.Ifeitherofthemhaseightorninepointsatthistime': '3. Si alguno tiene ocho o nueve puntos en ese momento',
       '(referredtoasanatural),thehandsareimmediately': '(lo que se llama natural), las manos se comparan',
       'comparedtodeterminethewinner.': 'de inmediato para determinar el ganador.',
       '4.Ifneitheronehasanatural,anadditionalthirdcard': '4. Si ninguno tiene natural, puede repartirse una tercera',
       'maybedealtundercertainconditions.': 'carta en ciertas condiciones.'}
TD = {'0,1,2,3,4,0r5', '0,1,or2', 'SuccessfullybetonPLAYER', 'SuccessfullybetonBANKER', 'SuccessfullybetonTlE'}
PAGINAS = {'rule_baccarat3': (T3, 'Bacará', '(4-1)'), 'rule_baccarat4': (T4, 'Bacará', '(4-2)'),
           'rule_baccarat5': (T5, 'Bacará', '(4-3)'), 'rule_baccarat6': (T6, 'Bacará', '(5)'),
           'rule_baccarat_s_2': (TS2, 'Bacará (Super 6)', '(3)'), 'rule_baccarat_s_3': (T3, 'Bacará (Super 6)', '(4-1)'),
           'rule_baccarat_s_4': (T4, 'Bacará (Super 6)', '(4-2)'), 'rule_baccarat_s_5': (T5, 'Bacará (Super 6)', '(4-3)')}


def clave(t): return ''.join(t.replace('·', '').split())


def lum(z): return z[..., :3].max(2).astype(float) * z[..., 3] / 255


def fuente(t): return ImageFont.truetype(SEG, max(6, int(round(t))))


def tam_para(txt, alto):
    """tamaño con el que lo que el texto sube sobre la base mide 'alto'."""
    t = 24.0
    for _ in range(6):
        bb = fuente(t).getbbox(txt, anchor='ls'); t = t * alto / max(1, -bb[1])
    return t


def rehacer(nombre, ocr):
    tabla, titulo, num = PAGINAS[nombre]
    o = Image.open(os.path.join(ORIG, P + nombre + '.dds')).convert('RGBA'); a = np.asarray(o).copy(); H, W = a.shape[:2]
    trabajos = []
    for b in ocr:
        x0, y0, x1, y1, en = b[0], b[1], b[2], b[3], b[4]
        k = clave(en)
        if y1 < 50: tipo, es = 'titulo', titulo
        elif k.startswith('RulesofBaccarat'): tipo, es, x0 = 'cab', 'Reglas del bacará ' + num, max(x0, 72)   # la viñeta queda
        elif k in tabla: es = tabla[k]; tipo = None
        else: continue   # números que no cambian
        if tipo is None:
            z = a[y0:y1, x0:x1]; fondo = np.median(lum(z))
            tipo = 'th' if fondo < 150 else ('td' if k in TD else 'texto')
        trabajos.append((tipo, (x0, y0, x1, y1), en, es))
    # medir: alto de tinta de cada renglón inglés y su color
    toc = np.zeros((H, W), np.uint8); med = []
    for tipo, (x0, y0, x1, y1), en, es in trabajos:
        xa, ya, xb, yb = max(0, x0 - 2), max(0, y0 - 2), min(W, x1 + 2), min(H, y1 + 2)
        z = a[ya:yb, xa:xb]; L = lum(z); f = np.median(L)
        m = (L > f + 45) if tipo in ('titulo', 'th') else (L < f - 45)
        if not m.any(): continue
        cnt = m.sum(1); r_base = int(np.where(cnt >= 0.35 * cnt.max())[0].max())   # base: última fila con mucha tinta
        r_top = r_base
        while r_top - 1 >= 0 and cnt[r_top - 1] > 0: r_top -= 1                      # hasta el primer hueco por arriba
        filas = np.arange(r_top, r_base + 1); cols = np.where(m[r_top:r_base + 1].any(0))[0]
        zz = z[m][:, :3]; lz = zz.max(1)
        nuc = zz[lz >= np.percentile(lz, 90)] if tipo in ('titulo', 'th') else zz[lz <= np.percentile(lz, 25)]   # núcleo de la letra
        color = tuple(int(c) for c in np.median(nuc, 0))
        mm = np.zeros((H, W), np.uint8); mm[ya:yb, xa:xb] = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)); toc |= mm
        en_l = en.replace('·', '').strip()
        med.append((tipo, en_l, es, xa + cols.min(), xa + cols.max() + 1, ya + r_top, r_base - r_top + 1, color, (xa, ya, xb, yb), f))
    # borrar: celdas y título = color plano del fondo de la caja; papel = inpaint
    plano = np.zeros((H, W), np.uint8)
    for tipo, en, es, tx0, tx1, top, alto, color, (xa, ya, xb, yb), f in med:
        if tipo in ('th', 'td'):
            sel = toc[ya:yb, xa:xb] > 0; z = a[ya:yb, xa:xb]
            for r_ in range(z.shape[0]):   # fila a fila: el fondo de la celda en esa fila (sin manchas más claras)
                if sel[r_].any() and (~sel[r_]).any(): z[r_, sel[r_]] = np.median(z[r_, ~sel[r_]], 0).astype(np.uint8)
            plano[ya:yb, xa:xb] |= sel
    resto = (toc > 0) & (plano == 0)
    for c in range(4): a[..., c] = cv2.inpaint(np.ascontiguousarray(a[..., c]), resto.astype(np.uint8), 4, cv2.INPAINT_TELEA)
    img = Image.fromarray(a)
    # tamaño común: el del texto de la página (mediana de los renglones de párrafo), tablas y título el suyo
    def tam_de(m_):   # por ANCHO: el inglés con esta letra mide lo mismo que su tinta (la altura engañaba)
        if m_[0] == 'titulo': return tam_para(m_[1], m_[6])
        if m_[0] == 'td' and m_[1][:1].isdigit(): return tam_para('0', m_[6])   # celdas de cifras: el alto de un «0»
        t = 24.0
        for _ in range(6): t = t * (m_[4] - m_[3]) / max(1, fuente(t).getlength(m_[1]))
        return t
    grupos = {}
    for m_ in med: grupos.setdefault('t' if m_[0] in ('texto', 'cab') else m_[0], []).append(tam_de(m_))
    TAM = {g: float(np.median(v)) for g, v in grupos.items()}
    for tipo, en, es, tx0, tx1, top, alto, color, (xa, ya, xb, yb), f in med:
        t = TAM['t' if tipo in ('texto', 'cab') else tipo]
        F = fuente(t); base = top + alto
        if tipo in ('texto', 'cab'): amax = 960 - tx0; x, alin = tx0, 'izq'
        else: amax = (xb - xa) - 6 if tipo != 'titulo' else 600; x, alin = (tx0 + tx1) / 2, 'centro'
        if tipo == 'td' or tipo == 'th':   # centrado en la CELDA (la caja del OCR sí va centrada en ella)
            x = (xa + xb) / 2
            # ancho real de la celda: hasta las rayas de la tabla
            fila = lum(np.asarray(o)[int(top + alto / 2):int(top + alto / 2) + 1])[0]
            izq = next((i for i in range(int(tx0) - 1, 0, -1) if fila[i] < 60 and tipo == 'td' or (tipo == 'th' and fila[i] < 40)), 0)
            der = next((i for i in range(int(tx1) + 1, W) if fila[i] < 60 and tipo == 'td' or (tipo == 'th' and fila[i] < 40)), W - 1)
            x = (izq + der) / 2; amax = der - izq - 10
        if tipo == 'titulo':   # el título, del alto de las mayúsculas del original
            FB = lambda tt: ImageFont.truetype(SEG, max(6, int(round(tt))))
            t = 20.0
            for _ in range(6): t = t * alto / max(1, -FB(t).getbbox('B', anchor='ls')[1])
            F = FB(t)
        while F.getlength(es) > amax and t > 8: t -= 0.25; F = (FB(t) if tipo == 'titulo' else fuente(t))
        w = F.getlength(es); px = x if alin == 'izq' else x - w / 2
        # a 4x con trazo de 1 px y reducido: un cuarto de píxel más gruesa (la letra del juego es algo más gruesa)
        F2 = ImageFont.truetype(F.path, F.size * 4)
        lay2 = Image.new('L', (W * 4, H * 4)); ImageDraw.Draw(lay2).text((px * 4, base * 4), es, font=F2, fill=255, anchor='ls', stroke_width=1, stroke_fill=255)
        lay = lay2.resize((W, H), Image.LANCZOS)
        capa = Image.new('RGBA', (W, H), color + (0,)); capa.putalpha(lay); img = Image.alpha_composite(img, capa)
        toc |= cv2.dilate((np.asarray(lay) > 0).astype(np.uint8), np.ones((5, 5), np.uint8))
    return o, img, toc


def guardar(nombre, img, toc):
    atlas_es.TEX = os.path.join(ORIG, os.path.dirname(P)); atlas_es.SAL = os.path.join(SAL, os.path.dirname(P))
    os.makedirs(atlas_es.SAL, exist_ok=True)
    p = atlas_es.guardar_dds(nombre, img)
    ob = open(os.path.join(ORIG, P + nombre + '.dds'), 'rb').read(); nb = bytearray(open(p, 'rb').read())
    if ob[84:88] in (b'DXT1', b'DXT3', b'DXT5') and len(ob) == len(nb):
        H, W = struct.unpack('<II', ob[12:20]); bs = 8 if ob[84:88] == b'DXT1' else 16; fila = (W + 3) // 4
        z = cv2.dilate(toc, np.ones((9, 9), np.uint8))
        for by in range(H // 4):
            for bx in range(W // 4):
                if not z[by*4:by*4+4, bx*4:bx*4+4].any():
                    k = 128 + (by * fila + bx) * bs; nb[k:k+bs] = ob[k:k+bs]
        open(p, 'wb').write(bytes(nb))


def main():
    ocr = json.load(open(os.path.join(T, 'imagenes', 'revision_v101', 'ocr2x.json'), encoding='utf-8'))
    for n in PAGINAS:
        o, img, toc = rehacer(n, ocr[P + n + '.dds'])
        guardar(n, img, toc)
        W, H = o.size; v = Image.new('RGB', (W * 2 + 10, H))
        for i, im in enumerate((o, img)):
            f = Image.new('RGBA', im.size, (0, 0, 0, 255)); f.alpha_composite(im); v.paste(f.convert('RGB'), (i * (W + 10), 0))
        v.save(os.path.join(REV, n + '.png')); print('ok', n, flush=True)


if __name__ == '__main__':
    main()
