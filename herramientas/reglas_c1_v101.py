# -*- coding: utf-8 -*-
"""(claude1, 25-10-2026) v1.0.1: rehace DESDE EL ORIGINAL las páginas de reglas de ruleta, shogi, mahjong, póquer y
cabaré (reparto con claude2 en el buzón). Mismo método que bacara_v101.py, generalizado:
  - una línea de español POR RENGLÓN del original (los saltos de renglón quedan donde estaban);
  - cada renglón con el color de su tinta; {texto} = color de realce (el naranja/rojo de las palabras clave);
  - la viñeta del original (· - ▪) se conserva y el texto empieza donde empezaba;
  - un solo tamaño por clase de renglón en cada página (los del mismo alto miden igual); ^ = centrado;
  - borrado: celdas lisas fila a fila con su fondo, papel con inpaint; fuera de lo tocado, bloques DXT originales.
  python -I herramientas/reglas_c1_v101.py [filtro]  -> trabajo/imagenes/es_v101/... + revision_v101/claude1_reglas/<n>.png
"""
import json, os, re, struct, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
from reglas_c1_textos import PAGINAS

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
ORIG = os.path.join(T, 'extraido'); SAL = os.path.join(T, 'imagenes', 'es_v101')
REV = os.path.join(T, 'imagenes', 'revision_v101', 'claude1_reglas'); os.makedirs(REV, exist_ok=True)
P = 'pausepar_pause_en/picture/'
SEG = 'C:/Windows/Fonts/YuGothM.ttc'   # la misma de bacara_v101 (la más parecida a la del juego)


def fuente(t): return ImageFont.truetype(SEG, max(6, int(round(t))))


def largo(t, s):   # ancho con la letra a 4x (como se dibuja): a tamaño real el ajuste de píxel cambia los anchos
    return ImageFont.truetype(SEG, max(6, int(round(t))) * 4).getlength(s.replace('{', '').replace('}', '')) / 4


def tam_para(txt, alto):
    t = 24.0
    for _ in range(6):
        bb = fuente(t).getbbox(txt, anchor='ls'); t = t * alto / max(1, -bb[1])
    return t


def trozos(es):
    """'a {b} c' -> [('a ', 0), ('b', 1), (' c', 0)]"""
    return [(s, i % 2) for i, s in enumerate(re.split(r'[{}]', es)) if s]


def medir(a, caja, en):
    H, W = a.shape[:2]; x0, y0, x1, y1 = caja
    xa, ya, xb, yb = max(0, x0 - 5), max(0, y0 - 1), min(W, x1 + 5), min(H, y1 + 1)   # poco margen en alto: las rayas de tabla quedan fuera
    z = a[ya:yb, xa:xb, :3].astype(int)
    bg = np.median(z.reshape(-1, 3), 0)   # la letra es minoría en su caja (el borde puede caer en una raya de la tabla)
    m = np.abs(z - bg).max(2) > 60
    m[m.mean(1) > 0.92] = False; m[:, m.mean(0) > 0.95] = False   # rayas de tabla que caen dentro de la caja: no son letra
    if m.sum() < 8: return None
    cols = m.any(0); xs = np.where(cols)[0]
    # viñeta: primera mancha estrecha y BAJA (no llega a media altura de la letra) seguida de un hueco
    filas_t = np.where(m.any(1))[0]; h = filas_t.max() - filas_t.min() + 1
    ini = xs.min(); fin = ini
    while fin + 1 < len(cols) and cols[fin + 1]: fin += 1
    x_txt = ini
    if fin - ini + 1 <= 0.5 * h:
        ys_v = np.where(m[:, ini:fin + 1].any(1))[0]
        sig = fin + 1
        while sig < len(cols) and not cols[sig]: sig += 1
        if ys_v.max() - ys_v.min() + 1 < 0.6 * h and sig - fin - 1 >= 0.25 * h and sig < len(cols): x_txt = sig
    mt = m.copy(); mt[:, :x_txt] = False
    cnt = mt.sum(1); r_base = int(np.where(cnt >= 0.35 * cnt.max())[0].max())
    r_top = r_base
    while r_top - 1 >= 0 and cnt[r_top - 1] > 0: r_top -= 1
    # colores: núcleo de la tinta, separado en saturado (realce) y no saturado
    nuc = cv2.erode(mt.astype(np.uint8), np.ones((2, 2), np.uint8)).astype(bool)
    if nuc.sum() < 10: nuc = mt
    px = z[nuc]; sat = px.max(1) - px.min(1)
    oscuro_fondo = bg.mean() < 110
    clara = px.mean() > bg.mean()   # letra más clara que su fondo (también en placas grises medias)
    def nucleo(p):
        lz = p.max(1)
        return p[lz >= np.percentile(lz, 70)] if clara else p[lz <= np.percentile(lz, 40)]
    s = sat > 70; base = acc = None
    if 0.02 < s.mean() < 0.92:
        base = tuple(int(c) for c in np.median(nucleo(px[~s]), 0)); acc = tuple(int(c) for c in np.median(px[s], 0))
    elif s.mean() >= 0.92: base = acc = tuple(int(c) for c in np.median(px, 0))
    else: base = tuple(int(c) for c in np.median(nucleo(px), 0))
    ink = np.where(mt.any(0))[0]
    return dict(x_txt=xa + x_txt, x_fin=xa + ink.max() + 1, base=ya + r_base, alto=r_base - r_top + 1, color=base, acc=acc,
                mascara=(xa, ya, xb, yb, mt), oscuro=oscuro_fondo, caja=(xa, ya, xb, yb),
                tam=tam_para(re.sub(r'[^A-Za-z0-9 ]', '', en).strip() or 'Ag', r_base - r_top + 1))   # sin ( ) " que suben más


_DON = []


def donantes():
    """todas las páginas rule_* originales con su máscara de texto (cajas del OCR + 6 px)"""
    if not _DON:
        ocr = json.load(open(os.path.join(T, 'imagenes', 'revision_v101', 'ocr2x.json'), encoding='utf-8'))
        for k, ls in ocr.items():
            if not k.startswith(P + 'rule_'): continue
            d = np.asarray(Image.open(os.path.join(ORIG, k)).convert('RGBA'))
            if d.shape[:2] != (512, 1024): continue
            tx = np.zeros(d.shape[:2], bool)
            for l in ls: tx[max(0, l[1] - 6):l[3] + 6, max(0, l[0] - 6):l[2] + 6] = True
            _DON.append((os.path.basename(k)[:-4], d, tx))
    return _DON


def rellenar_con_donantes(nombre, a, mk):
    """(25-10) los huecos del papel se rellenan con los MISMOS píxeles de otra página de reglas que tiene ahí el fondo
    limpio (misma plantilla: diferencia media < 3 en la zona libre de las dos); lo que no se cubre, con inpaint"""
    if a.shape[:2] != (512, 1024) or not mk.any(): return mk
    yo = next((tx for n, d, tx in donantes() if n == nombre), None)
    if yo is None: return mk
    cand = []
    for n, d, tx in donantes():
        if n == nombre: continue
        libre = ~(yo | tx); libre[:50] = False
        if libre.sum() < 20000: continue
        dif = np.abs(d[..., :3].astype(int) - a[..., :3].astype(int)).max(2)[libre].mean()
        if dif < 3: cand.append((dif, d, tx))
    cand.sort(key=lambda c: c[0]); falta = cv2.dilate(mk.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    n_, lab = cv2.connectedComponents(falta.astype(np.uint8))
    for i in range(1, n_):   # hueco a hueco: el donante debe coincidir en el anillo de alrededor y no tener tinta dentro
        h = lab == i; anillo = (cv2.dilate(h.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0) & ~falta
        if anillo.sum() < 10: continue
        ref = a[..., :3][anillo].astype(int)
        for dif, d, tx in cand:
            if (tx & h).any(): continue
            dd = d[..., :3].astype(int)
            if np.abs(dd[anillo] - ref).max(1).mean() > 4: continue
            if np.abs(dd[h] - np.median(ref, 0)).max(1).max() > 45: continue   # tinta (o algo que no es papel) dentro
            a[h] = d[h]; falta &= ~h; break
    return falta & mk


def rehacer(nombre, ocr):
    o = Image.open(os.path.join(ORIG, P + nombre + '.dds')).convert('RGBA'); a = np.asarray(o).copy(); H, W = a.shape[:2]
    spec = PAGINAS[nombre]; lineas = spec['lineas']; extra = spec.get('extra', [])
    assert len(lineas) == len(ocr), (nombre, len(lineas), len(ocr))
    trab = [(tuple(l[:4]), l[4], es) for l, es in zip(ocr, lineas) if es != '=']
    trab += [(tuple(c), en, es) for c, en, es in extra]
    for c, (x0, y0, x1, y1) in spec.get('cajas', {}).items():   # caja corregida para un renglón (p. ej. «Five-Number x»)
        trab = [((x0, y0, x1, y1), en, es) if en == c else (cj, en, es) for cj, en, es in trab]
    med = []
    for caja, en, es in trab:
        m = medir(a, caja, en)
        if m is None: print('  sin tinta:', nombre, en); continue
        centro = es.startswith('^'); es = es.lstrip('^')
        m.update(es=es, en=en, centro=centro); med.append(m)
    if 'columnas' in spec:   # tabla: todos los textos de una fila sobre la misma base
        ref = [(m['base'], m['alto'], m['x_fin'] - m['x_txt']) for m in med]
        for m in med:   # la base del texto más largo de la fila (el que mejor se mide)
            fila = [r for r in ref if abs(r[0] - m['base']) <= m['alto'] * 0.6]
            m['base'] = max(fila, key=lambda r: r[2])[0]
    acc_pag = next((m['acc'] for m in med if m['acc'] and m['acc'] != m['color']), None) or spec.get('realce', (230, 120, 40))
    # borrar
    toc = np.zeros((H, W), np.uint8); plano = np.zeros((H, W), bool); mk = np.zeros((H, W), bool)
    todo = np.zeros((H, W), bool)
    for m in med:
        xa, ya, xb, yb, mt = m['mascara']; sel = cv2.dilate(mt.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2) > 0
        todo[ya:yb, xa:xb] |= sel; toc[ya:yb, xa:xb] |= sel
    falta = rellenar_con_donantes(nombre, a, todo)   # 1.º el papel se copia de otra página con la misma plantilla
    for m in med:   # 2.º lo que no se cubrió: fondo liso (celda, barra, botón) fila a fila con su color; si no, inpaint
        xa, ya, xb, yb, mt = m['mascara']; sel = falta[ya:yb, xa:xb]
        if not sel.any(): continue
        z = a[ya:yb, xa:xb]; resto = z[~todo[ya:yb, xa:xb]][:, :3].astype(float)
        if len(resto) and resto.std(0).max() < 9:
            for r_ in range(z.shape[0]):
                if sel[r_].any() and (~sel[r_]).any(): z[r_, sel[r_]] = np.median(z[r_, ~sel[r_]], 0).astype(np.uint8)
            plano[ya:yb, xa:xb] |= sel
        else: mk[ya:yb, xa:xb] |= sel
    for c in range(4): a[..., c] = cv2.inpaint(np.ascontiguousarray(a[..., c]), mk.astype(np.uint8), 4, cv2.INPAINT_TELEA)
    img = Image.fromarray(a)
    # sitio de cada renglón: centrado = su caja (+15 %); a la izquierda = hasta lo siguiente que haya en el original a la derecha
    ao = np.asarray(o)
    margen = max([m['x_fin'] for m in med if not m['centro']] + [953]) + 12   # todas las páginas tienen papel hasta ~965
    for m in med:
        if m['centro']:
            m['ancho'] = spec.get('ancho_centro', {}).get(m['en'], (m['x_fin'] - m['x_txt']) * 1.15 + 8); continue
        y0, y1 = m['base'] - m['alto'], m['base'] + max(3, m['alto'] // 3)
        z = ao[max(0, y0):y1, :, :3].astype(int); bg = np.median(z[:, m['x_txt']:m['x_fin']].reshape(-1, 3), 0)
        mz = np.abs(z - bg).max(2) > 60; mz[mz[:, m['x_fin']:].mean(1) > 0.5] = False   # rayas horizontales de tabla
        tinta = mz.sum(0) >= 2
        limite = min(W - 8, spec.get('derecha', margen))
        for x in range(m['x_fin'] + 14, limite):
            if tinta[x]: limite = x - 12; break
        m['ancho'] = limite - m['x_txt']
    # tamaño común por clase (centrado/no, fondo oscuro/no, alto parecido)
    clases = {}
    grupos = {}   # (25-10) tamaños a menos de un 13 % entre sí = la misma clase (el alto medido varía un poco por renglón)
    for m in sorted(med, key=lambda m: m['tam']):
        g = grupos.setdefault((m['centro'], m['oscuro']), [])
        if not g or m['tam'] > g[-1][0] * 1.13: g.append([m['tam'], len(g)])
        m['grupo'] = g[-1][1]
    for m in med:
        if 'columnas' in spec and not m['centro'] and m['base'] > spec.get('tabla_y', 0):   # tabla: un tamaño por columna
            clave = (False, m['oscuro'], 'c%d' % sum(m['x_txt'] >= c for c in spec['columnas']))
        else: clave = (m['centro'], m['oscuro'], m['grupo'])
        clases.setdefault(clave, []).append(m)
    for cl, ms in clases.items():
        t = float(np.median([m['tam'] for m in ms])) * spec.get('escala', 1.0)
        k = min([1.0] + [m['ancho'] / max(1, largo(t, m['es'])) for m in ms])
        if k < 0.9: print(f'  {nombre}: clase {cl} achicada a {k:.2f} por', [m['es'] for m in ms if m['ancho'] < largo(t, m['es'])])
        for m in ms: m['t'] = t * k
    for ms in clases.values():   # comienzos de renglón que casi coinciden (±8 px) = el mismo margen
        xs = [m['x_txt'] for m in ms if not m['centro']]
        for m in ms:
            if not m['centro']:
                cerca = [x for x in xs if abs(x - m['x_txt']) <= 8]; m['x_txt'] = int(np.median(cerca))
    for m in med:
        F = fuente(m['t']); es = m['es']; w = largo(m['t'], es)
        x = (m['x_txt'] + m['x_fin']) / 2 - w / 2 if m['centro'] else m['x_txt']
        F4 = ImageFont.truetype(SEG, F.size * 4)
        for txt, realce in trozos(es):
            col = (m['acc'] or acc_pag) if realce else m['color']
            lay4 = Image.new('L', (W * 4, H * 4))
            ImageDraw.Draw(lay4).text((x * 4, m['base'] * 4), txt, font=F4, fill=255, anchor='ls', stroke_width=1, stroke_fill=255)
            lay = lay4.resize((W, H), Image.LANCZOS)
            capa = Image.new('RGBA', (W, H), tuple(col) + (0,)); capa.putalpha(lay); img = Image.alpha_composite(img, capa)
            toc |= cv2.dilate((np.asarray(lay) > 0).astype(np.uint8), np.ones((5, 5), np.uint8))
            x += F4.getlength(txt) / 4
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
    return p


def main(filtro=''):
    ocr = json.load(open(os.path.join(T, 'imagenes', 'revision_v101', 'ocr2x.json'), encoding='utf-8'))
    for n in PAGINAS:
        if filtro not in n: continue
        o, img, toc = rehacer(n, ocr[P + n + '.dds'])
        p = guardar(n, img, toc)
        W, H = o.size; v = Image.new('RGB', (W * 2 + 10, H), (255, 0, 255))
        fin = Image.open(p).convert('RGBA')   # la revisión se hace sobre el .dds YA comprimido
        for i, im in enumerate((o, fin)):
            f = Image.new('RGBA', im.size, (0, 0, 0, 255)); f.alpha_composite(im); v.paste(f.convert('RGB'), (i * (W + 10), 0))
        v.save(os.path.join(REV, n + '.png')); print('ok', n, flush=True)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '')
