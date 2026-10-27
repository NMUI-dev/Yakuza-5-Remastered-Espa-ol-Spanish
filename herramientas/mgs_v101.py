# -*- coding: utf-8 -*-
"""(claude1, 25-10-2026) v1.0.1: rehace las 78 guías de controles (2d_*_mgs_*) del Y5 desde el ORIGINAL con una regla común:
  - 4 columnas fijas (etiqueta izq. | botón izq. | botón der. | etiqueta der.) + título: nada invade la columna vecina;
  - se borra solo la tinta del inglés (inpaint) y se escribe el español con la letra, alto y color medidos del original;
  - si no cabe: primero más pequeño (hasta 80 %), luego un poco más estrecho (hasta 85 %), nunca fuera de su columna;
  - «Botón X» con su símbolo (Segoe UI Symbol); traducción común de herramientas/mgs_tabla.py;
  - fuera de lo tocado, los bloques DXT ORIGINALES (el compresor estropeaba detalles finos).
  python -I herramientas/mgs_v101.py [filtro]  -> trabajo/imagenes/es_v101/<ruta>.dds + revision_v101/mgs/<nombre>.png
"""
import json, os, re, struct, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
import mgs_tabla as M

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(R, 'trabajo'); ORIG = os.path.join(T, 'extraido'); SAL = os.path.join(T, 'imagenes', 'es_v101')
REV = os.path.join(T, 'imagenes', 'revision_v101', 'mgs'); os.makedirs(REV, exist_ok=True)
FD = 'C:/Windows/Fonts/'
F_TXT, F_SYM = FD + 'segoeui.ttf', FD + 'seguisym.ttf'
SIMBOLOS = '△○✕□'
FIJO = {'L': 24.7, 'B': 20.0, 'T': 25.3}
# columnas (x de la textura 2048x512)
LL = (508, 762)        # etiquetas izquierda (barra)
LB = (766, 1000)       # botones izquierda
RB = (1040, 1280)      # botones derecha
RL = (1286, 1540)      # etiquetas derecha
BOTON_FIN = re.compile(r'^(.*?)\s*((?:L1|L2|R1|R2|L3|R3|Up|O|X|△)?\s*Button|Left\s*Stick|Right\s*Stick|Touch\s*Pad\s*Button)\s*$', re.I)


def fuente(ruta, t):
    return ImageFont.truetype(ruta, max(6, int(t)))


def medir(texto, tam):
    """ancho y caja de tinta (anchor ls) del texto con los símbolos en Segoe UI Symbol."""
    x = 0; top, bot = 0, 0
    for trozo, f in trozos(texto, tam):
        bb = f.getbbox(trozo, anchor='ls'); top = min(top, bb[1]); bot = max(bot, bb[3]); x += f.getlength(trozo)
    return x, top, bot


def trozos(texto, tam):
    out = []; act = ''; sym = None
    for ch in texto:
        s = ch in SIMBOLOS
        if sym is None or s == sym: act += ch
        else: out.append((act, fuente(F_SYM if sym else F_TXT, tam * (0.8 if sym else 1)))); act = ch
        sym = s
    if act: out.append((act, fuente(F_SYM if sym else F_TXT, tam * (0.8 if sym else 1))))
    return out


def capa_texto(size, texto, tam, color, x, base, estrecho=1.0, alin='izq', ancho_max=None):
    W, H = size
    ancho, top, bot = medir(texto, tam)
    lay = Image.new('L', (int(ancho) + 8, int(bot - top) + 8), 0); d = ImageDraw.Draw(lay); cx = 4
    for trozo, f in trozos(texto, tam):
        d.text((cx, 4 - top), trozo, font=f, fill=255, anchor='ls'); cx += f.getlength(trozo)
    if estrecho < 1: lay = lay.resize((max(1, int(lay.width * estrecho)), lay.height), Image.LANCZOS)
    w = lay.width - 8
    px = x if alin == 'izq' else (x - w if alin == 'der' else x - w // 2)
    full = Image.new('L', size, 0); full.paste(lay, (int(px) - 4, int(base + top) - 4))
    return full, w


def ajustar(texto, tam, ancho_max):
    """tamaño y estrechado para que quepa: hasta 80 % del cuerpo, luego hasta 85 % de ancho, luego más pequeño."""
    t = tam
    while t > tam * 0.8 and medir(texto, t)[0] > ancho_max: t -= 0.5
    w = medir(texto, t)[0]; e = 1.0
    if w > ancho_max: e = max(0.85, ancho_max / w)
    while medir(texto, t)[0] * e > ancho_max and t > 8: t -= 0.5
    return t, e


def tinta(a, caja):
    x0, y0, x1, y1 = caja
    z = a[y0:y1, x0:x1].astype(int); v = z[..., :3].max(2) * z[..., 3] / 255
    return v > 140


def calibrar(en, alto):
    t = 20.0
    for _ in range(6):
        _, top, bot = medir(en, t); h = max(1, -top)   # alto sobre la base (mayúsculas), sin descendentes
        t = t * alto / h
    return t


def glifo_de(a, caja):
    """caja del símbolo (△○✕□) que va justo a la izquierda de la palabra «Button» (tinta con umbral bajo)."""
    x0, y0, x1, y1 = caja
    z = a[y0:y1, x0:x1].astype(int); v = z[..., :3].max(2) * z[..., 3] / 255 > 60
    colx = v.any(0); runs = []; i = 0
    while i < len(colx):
        if colx[i]:
            j = i
            while j + 1 < len(colx) and colx[j + 1]: j += 1
            runs.append([i, j]); i = j + 1
        else: i += 1
    if len(runs) < 2: return None
    # la palabra: grupos de la derecha separados por huecos de <= 3 px
    k = len(runs) - 1
    while k > 0 and runs[k][0] - runs[k - 1][1] <= 4: k -= 1
    if k == 0: return None
    g = runs[k - 1]
    if not (5 <= g[1] - g[0] + 1 <= 22): return None
    filas = np.where(v[:, g[0]:g[1] + 1].any(1))[0]
    return (x0 + g[0], y0 + filas.min(), x0 + g[1] + 1, y0 + filas.max() + 1)


_GUIAS = None
def otras_guias():
    """originales de las 78 guías (mismas posiciones de barras), en memoria una vez."""
    global _GUIAS
    if _GUIAS is None:
        malas = json.load(open(os.path.join(T, 'imagenes', 'revision_v101', 'TODAS_MALAS.json'), encoding='utf-8'))
        _GUIAS = [np.asarray(Image.open(os.path.join(ORIG, x)).convert('RGBA')) for x in malas if '_mgs_' in x]
    return _GUIAS


def partes(b):
    """reparte un renglón del OCR en (columna, caja, texto); los pegados (etiqueta + botón) se separan."""
    x0, y0, x1, y1, txt = b[0], b[1], b[2], b[3], b[4].strip()
    if 940 <= x0 and x1 <= 1110: return [('T', (x0, y0, x1, y1), txt)]
    if x1 <= 790: return [('LL', (max(x0, 498), y0, min(x1, LL[1] + 2), y1), txt)]
    if x0 >= 735 and x1 < 1010: return [('LB', (max(x0, 764), y0, x1, y1), txt)]
    if x0 < 735 and x1 > 790:
        m = BOTON_FIN.match(txt)
        if m and m.group(1): return [('LL', (x0, y0, 762, y1), m.group(1)), ('LB', (764, y0, x1, y1), m.group(2))]
        return []
    if x0 >= 1040 and x1 <= 1290: return [('RB', (x0, y0, min(x1, 1281), y1), txt)]
    if x0 >= 1270: return [('RL', (max(x0, 1283), y0, x1, y1), txt)]
    m = re.match(r'^(L1\s*\+\s*L2|R1\s*\+\s*R2)\s*(.*)$', txt)
    if m and x0 < 1282 < x1: return [('RB', (x0, y0, 1281, y1), m.group(1)), ('RL', (1283, y0, x1, y1), m.group(2))]
    return []


def rehacer(ruta, ocr):
    o = Image.open(os.path.join(ORIG, ruta)).convert('RGBA'); a = np.asarray(o).copy(); W, H = o.size
    trabajos = []; avisos = []
    for b in ocr:
        for col, caja, txt in partes(b):
            es = M.traducir(txt)
            if es is None: avisos.append(f'sin traducción: {txt!r}'); continue
            x0, y0, x1, y1 = caja
            if col == 'RB' and M.clave(txt) == 'button':
                x0 = max(1040, x0 - 26)   # el OCR no ve el símbolo □ a la izquierda de «Button»
            trabajos.append((col, (x0, max(0, y0 - 2), x1, min(H, y1 + 2)), txt, es))
    # 1) medir del original y borrar la tinta inglesa
    toc = np.zeros((H, W), np.uint8); medidas = []; transp = []; barras = []
    for col, (x0, y0, x1, y1), txt, es in trabajos:
        m = tinta(a, (x0, y0, x1, y1))
        if not m.any(): avisos.append(f'sin tinta: {txt!r}'); continue
        filas = np.where(m.any(1))[0]; ys, xs = np.nonzero(m)
        z = a[y0:y1, x0:x1][m]; brillo = z[:, :3].max(1)
        color = tuple(int(c) for c in np.median(z[brillo >= np.percentile(brillo, 70)][:, :3], 0))
        ink_top, ink_h = y0 + filas.min(), filas.max() - filas.min() + 1
        tx0, tx1 = x0 + xs.min(), x0 + xs.max() + 1
        if col in ('LB', 'RB'):   # los símbolos (○ ✕) son más tenues: el ancho del inglés con umbral bajo
            zb = a[y0:y1, x0:x1].astype(int); vb = (zb[..., :3].max(2) * zb[..., 3] / 255 > 60).any(0)
            if vb.any(): tx0 = min(tx0, x0 + int(np.argmax(vb)))
        mm = np.zeros((H, W), np.uint8); mm[y0:y1, x0:x1] = m
        mm = cv2.dilate(mm, np.ones((3, 3), np.uint8)); toc |= mm
        # símbolo del botón (△○✕□) a la izquierda: grupo de tinta separado del resto -> se copia tal cual al final
        glifo = None   # (los símbolos se dibujan con Segoe UI Symbol; copiar el original fallaba con O/B pegadas)
        if col in ('LB', 'RB'):   # borrar también la tinta tenue (símbolos △○✕□) del renglón del botón
            zb = a[y0:y1, x0:x1].astype(int)
            mb = (zb[..., :3].max(2) * zb[..., 3] / 255 > 60).astype(np.uint8)
            mm[y0:y1, x0:x1] |= cv2.dilate(mb, np.ones((3, 3), np.uint8)); toc |= mm
        medidas.append((col, txt, es, tx0, tx1, ink_top, ink_h, color, glifo))
        if col in ('LB', 'RB'): transp.append((x0, y0, x1, y1))
        else: barras.append((x0, y0, x1, y1))
    # tamaño común por guía y columna: mediana de lo que mide cada renglón inglés (alto total de tinta)
    def tam_de(txt, ink_h):
        txt = txt.replace('/', 'l').replace('(', 'l').replace(')', 'l')   # en la letra del juego no bajan de la base
        t = 20.0
        for _ in range(6):
            _, top, bot = medir(txt, t); t = t * ink_h / max(1, bot - top)
        return t
    grupos = {}
    for md in medidas:
        g = 'L' if md[0] in ('LL', 'RL') else ('B' if md[0] in ('LB', 'RB') else 'T')
        grupos.setdefault(g, []).append(tam_de(md[1], md[6]))
    TAM = {g: float(np.median(v)) for g, v in grupos.items()}
    MED = TAM
    orig = np.asarray(o)
    for c in range(4):
        a[..., c] = cv2.inpaint(np.ascontiguousarray(a[..., c]), toc, 3, cv2.INPAINT_TELEA)
    # etiquetas: lo borrado se copia de OTRA barra resaltada de la misma columna (mismo degradado) donde esa zona no
    # tenga letras; si no hay ninguna, se interpola por filas entre los píxeles sanos (el inpaint dejaba manchas)
    o_a0 = np.asarray(o).astype(float); o_u8 = np.asarray(o)
    for x0, y0, x1, y1 in barras:
        sub = (toc[y0:y1, x0:x1] > 0).astype(np.uint8)
        toc[y0:y1, x0:x1] |= cv2.dilate(sub, np.ones((1, 7), np.uint8))
        # (25-10, claude2) restos fuera de la caja del OCR: toda la tinta clara de la caja ensanchada 8 px, umbral bajo
        xa_, xb_ = max(0, x0 - 8), min(W, x1 + 8)
        zz_ = o_a0[y0:y1, xa_:xb_]; lum_ = zz_[..., :3].max(2) * zz_[..., 3] / 255
        med_ = np.median(lum_[zz_[..., 3] > 200]) if (zz_[..., 3] > 200).any() else np.median(lum_)
        opaco = zz_[..., 3] > 200
        claro = (((lum_ > med_ + 45) | ((lum_ < med_ - 25) & opaco))).astype(np.uint8)   # letras claras y su sombra oscura
        toc[y0:y1, xa_:xb_] |= cv2.dilate(claro, np.ones((3, 3), np.uint8))
    for x0, y0, x1, y1 in barras:
        sel = toc[y0:y1, x0:x1] > 0
        if not sel.any(): continue
        cols_ = np.where(sel.any(0))[0]; ea, eb = x0 + cols_.min(), x0 + cols_.max() + 1
        pend = sel.copy()
        # 1.º: la barra resaltada es el MISMO dibujo en todas las guías: cada columna borrada se copia de una guía con esa
        # barra resaltada (trozo sin letras igual) y SIN letras en esa columna (ni a 7 px: sombra y antialias)
        xa_, xb_ = max(0, x0 - 10), min(W, x1 + 10)
        if x1 < 1000: xb_ = min(xb_, LL[1] - 3); xa_ = max(xa_, LL[0] + 6)   # sin tocar el filo de la barra (junto al mando)
        else: xa_ = max(xa_, RL[0] + 1); xb_ = min(xb_, RL[1] - 6)
        selw = toc[y0:y1, xa_:xb_] > 0
        lado = (LL[0] + 2, LL[0] + 26) if x1 < 1000 else (RL[1] - 26, RL[1] - 2)
        ya_, yb_ = max(0, y0 - 7), min(H, y1 + 7)   # con los filos de la barra (la resaltada tiene filo claro abajo)
        bx0_, bx1_ = (LL[0] + 2, LL[1] - 2) if x1 < 1000 else (RL[0], RL[1] - 2)
        bandas = lambda X: np.concatenate([X[ya_:y0, bx0_:bx1_].reshape(-1, 4), X[y1:yb_, bx0_:bx1_].reshape(-1, 4)]).astype(float)
        ref_p = bandas(o_a0)
        cols_pend = selw.any(0)
        for T_ in otras_guias():
            if not cols_pend.any(): break
            if np.abs(bandas(T_) - ref_p).mean() >= 4: continue
            libre_ = ~selw & (o_a0[y0:y1, xa_:xb_, 3] > 200)
            dif_ = np.abs(T_[y0:y1, xa_:xb_].astype(float) - o_a0[y0:y1, xa_:xb_]).max(2)
            if libre_.any() and np.percentile(dif_[libre_], 97) > 14: continue   # el fondo libre de la barra tiene que coincidir
            z_ = T_[y0 - 2:y1 + 2, xa_:xb_].astype(int); lz = z_[..., :3].max(2) * z_[..., 3] / 255
            letras = (lz > 95).any(0).astype(np.uint8)
            letras = cv2.dilate(letras[None], np.ones((1, 15), np.uint8))[0] > 0
            usar = cols_pend & ~letras
            if not usar.any(): continue
            m_ = selw & usar[None, :]
            blk = a[y0:y1, xa_:xb_]; blk[m_] = T_[y0:y1, xa_:xb_][m_]; a[y0:y1, xa_:xb_] = blk
            cols_pend &= ~usar
        pend[:] = False
        if cols_pend.any(): avisos.append(f'relleno sin guía limpia: {int(cols_pend.sum())} columnas en {(x0, y0)}')
        pend = selw & cols_pend[None, :]
        toc_rest = np.zeros_like(toc); toc_rest[y0:y1, xa_:xb_] = pend
        hecho = not pend.any()
        if hecho: continue
        for y in range(y0, y1):
            fila_m = toc_rest[y, :] > 0
            xs_m = np.where(fila_m[max(0, x0 - 12):min(W, x1 + 12)])[0] + max(0, x0 - 12)
            if not len(xs_m): continue
            xa, xb = xs_m.min() - 1, xs_m.max() + 1
            if xa < 0 or xb >= W: continue
            sanos = np.where(~fila_m[xa:xb + 1])[0] + xa
            sanos = sanos[o_a0[y, sanos, 3] > 200] if (o_a0[y, sanos, 3] > 200).sum() >= 2 else sanos
            if len(sanos) < 2: continue
            lum = a[y, sanos, :3].max(1).astype(float); med = np.median(lum)
            ok_ = lum <= med * 1.35 + 8   # sin el filo brillante de la barra (hacía una raya)
            if ok_.sum() >= 2: sanos = sanos[ok_]
            act_ = a[y].astype(float)   # anclas = valores YA rellenados (no el original con el inglés)
            for ch in range(4):
                a[y, xa:xb + 1, ch] = np.clip(np.interp(np.arange(xa, xb + 1), sanos, act_[sanos, ch]), 0, 255).astype(np.uint8)
        # suavizado vertical solo en lo rellenado (quita las rayas de fila a fila)
        zona = a[y0:y1, xa_:xb_].astype(np.float32); suave = cv2.GaussianBlur(zona, (1, 7), 0)
        mz = cv2.dilate(pend.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        zona[mz] = suave[mz]; a[y0:y1, xa_:xb_] = np.clip(zona, 0, 255).astype(np.uint8)
    # botones: van sobre fondo TRANSPARENTE; lo borrado vuelve a alfa 0 (el inpaint dejaba manchas grises)
    o_a = np.asarray(o)
    for x0, y0, x1, y1 in transp:
        z = o_a[y0:y1, x0:x1]; fondo = z[..., 3][toc[y0:y1, x0:x1] == 0]
        if len(fondo) and np.median(fondo) < 10:
            sel = toc[y0:y1, x0:x1] > 0; blk = a[y0:y1, x0:x1]; blk[sel] = 0; a[y0:y1, x0:x1] = blk
    # tamaño común en renglones apilados de una misma etiqueta (p. ej. «Posición/ Ajustar efecto/ Elegir bola»)
    img = Image.fromarray(a)
    # 2) escribir el español
    tams = []
    for col, txt, es, tx0, tx1, ink_top, ink_h, color, glifo in medidas:
        # (25-10) tamaño FIJO de la serie (medido en airhockey); si el original lo hizo más pequeño (renglón largo), el suyo
        g = 'L' if col in ('LL', 'RL') else ('B' if col in ('LB', 'RB') else 'T')
        r = tam_de(txt, ink_h) / FIJO[g]
        tams.append(FIJO[g] * r if r < 0.93 else FIJO[g])
    desp = [0] * len(medidas); vecinos = [0] * len(medidas); pares = []
    for i, mi in enumerate(medidas):
        for j, mj in enumerate(medidas):
            if i != j and mi[0] == mj[0] and mi[0] in ('LL', 'RL') and 0 < mj[5] - mi[5] < 40 and mj[5] - (mi[5] + mi[6]) < 5 and abs(mi[3] - mj[3]) < 60:
                tams[i] = tams[j] = min(tams[i], tams[j], FIJO['L'] * 0.85)
                arriba, abajo = (i, j) if mi[5] < mj[5] else (j, i)
                vecinos[arriba] += 1; vecinos[abajo] += 1; pares.append((arriba, abajo))
    for ar, ab in pares:   # solo grupos de DOS renglones se separan un poco (con tres ya van bien repartidos)
        if vecinos[ar] == 2 and vecinos[ab] == 2 and sum(1 for p_ in pares if ar in p_ or ab in p_) == 2:
            desp[ar], desp[ab] = -4, 4
    bases = [mi[5] - medir(mi[1], tams[k])[1] + desp[k] for k, mi in enumerate(medidas)]
    for ar, ab in set(pares):   # dos renglones: interlineado mínimo de 1,05 cuerpos (los cuadros del OCR se pisan)
        if desp[ar] == -4:
            centro = (bases[ar] + bases[ab]) / 2; sep = max(bases[ab] - bases[ar], 1.05 * max(tams[ar], tams[ab]))
            bases[ar], bases[ab] = centro - sep / 2, centro + sep / 2
    for k in range(len(medidas)):   # el del medio de tres renglones apilados: a mitad de camino entre los otros dos
        if vecinos[k] == 4:
            vs = sorted({b for p_ in pares if k in p_ for b in p_ if b != k}, key=lambda q: bases[q])
            if len(vs) == 2: bases[k] = (bases[vs[0]] + bases[vs[1]]) / 2
    for idx, (col, txt, es, tx0, tx1, ink_top, ink_h, color, glifo) in enumerate(medidas):
        tam = tams[idx]
        _, top_en, _ = medir(txt, tam)
        base = bases[idx]
        alto = ink_h
        if glifo:   # «Botón» + el símbolo original copiado al final
            es = es.replace(' ' + es[-1], '') if es[-1] in SIMBOLOS else es
            gx0, gy0, gx1, gy1 = glifo; gw = gx1 - gx0
            parche = Image.fromarray(orig[gy0:gy1, gx0:gx1])
            if col == 'RB': destx = tx1 - gw; tx1 = destx - 5
            else: destx = None
        if col == 'LL': x, alin, amax = tx1, 'der', tx1 - min(LL[0], tx0)
        elif col == 'LB': x, alin, amax = tx0, 'izq', min(LB[1], max(tx1 + 30, tx0 + (tx1 - tx0) * 1.3)) - tx0
        elif col == 'RB': x, alin, amax = tx1, 'der', tx1 - max(RB[0], min(tx0 - 30, tx1 - (tx1 - tx0) * 1.3))
        elif col == 'RL': x, alin, amax = tx0, 'izq', max(RL[1], tx1) - tx0
        else: x, alin, amax = (tx0 + tx1) // 2, 'centro', (tx1 - tx0) * 1.6
        # botones de la columna: no se acercan a la raya más que el inglés
        if col in ('LB', 'RB'):
            yc = int(base - alto / 2); zz = orig[max(0, yc - 4):yc + 5].astype(int)
            vv = zz[..., :3].max(2) * zz[..., 3] / 255; fila = vv.max(0)
            yr_raya = max(0, yc - 4) + int(np.argmax(vv[:, min(W - 1, tx1 + 30) if col == 'LB' else max(0, tx0 - 30)]))
            if col == 'LB':
                k = next((i for i in range(tx1 + 2, min(W, tx1 + 60)) if fila[i] > 120), None)
                if k: amax = min(amax, k - 4 - tx0)
                raya = k
                if k: yr_raya = max(0, yc - 4) + int(np.argmax(vv[:, min(W - 1, k + 1)]))
            else:
                k = next((i for i in range(tx0 - 2, max(0, tx0 - 60), -1) if fila[i] > 120), None)
                if k: amax = min(amax, tx1 - (k + 4))
                raya = k
                if k: yr_raya = max(0, yc - 4) + int(np.argmax(vv[:, max(0, k - 1)]))
        if col not in ('LB', 'RB'): raya = None
        else: amax = max(amax, (tx1 - tx0) * 1.0)   # un botón siempre puede ocupar lo mismo que el inglés
        if not es.strip(): continue   # renglón que sobra en español (se queda solo borrado)
        if glifo and col == 'RB': x = tx1; amax -= gw + 5
        t, e = ajustar(es, tam, amax)
        cap, w = capa_texto(img.size, es, t, color, x, base, e, alin)
        if glifo:
            if col == 'LB': destx = x + w + 5
            img.alpha_composite(parche, (int(destx), gy0))
            toc[gy0:gy1, int(destx):int(destx) + gw] = 1
        # la raya del botón llega hasta el texto nuevo (el español puede ser más corto que el inglés)
        if raya:
            yr = yr_raya; col_px = orig[max(0, yr - 6):yr + 7, raya + 1 if col == 'LB' else raya - 1]
            ini, fin = ((int(x + w + (gw + 5 if glifo else 0)) + 4, raya) if col == 'LB' else (raya + 1, int(x - w - (gw + 5 if glifo else 0)) - 4))
            if col == 'RB' and glifo: ini, fin = raya + 1, int(destx - 5 - w) - 4
            if fin > ini:
                aa = np.asarray(img).copy(); y_ = max(0, yr - 6)
                c0 = yr - y_   # solo la raya: filas brillantes contiguas a la fila central (máx. 3)
                br = [int(px[:3].max()) * int(px[3]) / 255 > 110 for px in col_px]
                filas_r = [r_ for r_ in range(len(col_px)) if br[r_] and abs(r_ - c0) <= 1]
                for r_ in filas_r:
                    aa[y_ + r_, ini:fin] = col_px[r_]; toc[y_ + r_, ini:fin] = 1
                img = Image.fromarray(aa)
        capa = Image.new('RGBA', img.size, color + (0,)); capa.putalpha(cap)
        img = Image.alpha_composite(img, capa)
        mm = (np.asarray(cap) > 0).astype(np.uint8); toc |= cv2.dilate(mm, np.ones((5, 5), np.uint8))
    return o, img, toc, avisos


def guardar(ruta, img, toc):
    nombre = ruta[:-4]
    atlas_es.TEX = ORIG; atlas_es.SAL = SAL
    os.makedirs(os.path.dirname(os.path.join(SAL, nombre)), exist_ok=True)
    p = atlas_es.guardar_dds(nombre, img)
    ob = open(os.path.join(ORIG, ruta), 'rb').read(); nb = bytearray(open(p, 'rb').read())
    if ob[84:88] in (b'DXT1', b'DXT3', b'DXT5') and len(ob) == len(nb):
        H, W = struct.unpack('<II', ob[12:20]); bs = 8 if ob[84:88] == b'DXT1' else 16; fila = (W + 3) // 4
        z = cv2.dilate(toc, np.ones((25, 25), np.uint8))
        for by in range(H // 4):
            for bx in range(W // 4):
                if not z[by*4:by*4+4, bx*4:bx*4+4].any():
                    k = 128 + (by * fila + bx) * bs; nb[k:k+bs] = ob[k:k+bs]
        open(p, 'wb').write(bytes(nb))
    return p


def main(filtro=''):
    o_ = json.load(open(os.path.join(T, 'imagenes', 'ocr.json'), encoding='utf-8'))
    malas = json.load(open(os.path.join(T, 'imagenes', 'revision_v101', 'TODAS_MALAS.json'), encoding='utf-8'))
    rutas = [x for x in malas if '_mgs_' in x and filtro in x]
    for ruta in rutas:
        k = next(kk for kk in o_ if kk.endswith(ruta))
        o, img, toc, avisos = rehacer(ruta, o_[k])
        guardar(ruta, img, toc)
        W, H = o.size; v = Image.new('RGB', (W, H * 2 + 8), (40, 40, 40))
        for i, im in enumerate((o, img)):
            f = Image.new('RGBA', im.size, (0, 0, 0, 255)); f.alpha_composite(im); v.paste(f.convert('RGB'), (0, i * (H + 8)))
        v.crop((440, 0, 1600, H * 2 + 8)).save(os.path.join(REV, os.path.basename(ruta)[:-4] + '.png'))
        print('ok', ruta, '; '.join(avisos), flush=True)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '')
