# -*- coding: utf-8 -*-
"""(Claude Code, 20-10-2026) Reescribe en español las texturas con texto «de documento» de Yakuza 5 (páginas de reglas,
guías de controles, avisos...), a partir del OCR (trabajo/imagenes/ocr.json) y de las traducciones por bloque
(trabajo/imagenes/ocr_es.json: {clave_de_bloque: texto español}).
  1. bloques(): junta las líneas del OCR en párrafos (mismo margen izquierdo, misma altura, renglones seguidos).
  2. borrar(): quita la tinta del texto inglés (píxeles que se apartan del fondo local) y rellena (inpaint).
  3. escribir(): escribe el español con la altura de letra y el color medidos, repartido en renglones del ancho del
     bloque; si no cabe hasta el bloque siguiente, achica la letra (hasta 75 %) y luego estrecha.
Clave de bloque = «ruta#n». Salida: trabajo/imagenes/es/<raíz>/<ruta>.dds.
  python herramientas/paginas_es.py [ruta ...]
"""
import os, sys, json, re
import re as _r
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
from ocr_imagenes import origen
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
FUENTE = os.environ.get('PAG_FUENTE', 'C:/Windows/Fonts/seguisb.ttf')
FUENTE_N = os.environ.get('PAG_FUENTE_N', 'C:/Windows/Fonts/segoeuib.ttf')


def bloques(lineas, modo='parrafos'):
    """[[x0,y0,x1,y1,texto,conf]] -> [{'lineas': [...], 'caja': (x0,y0,x1,y1), 'texto': str, 'alinear'}] en orden de
    lectura. modo 'parrafos' (páginas de reglas): renglones con el mismo margen izquierdo se juntan en párrafos.
    modo 'etiquetas' (guías de controles, menús): cada renglón va solo salvo que esté pegado al siguiente (hueco < 0.25
    de alto) con el mismo borde izquierdo o derecho; la alineación sale de los vecinos (bordes que coinciden)."""
    if modo == 'etiquetas': return _etiquetas(lineas)
    ls = sorted(lineas, key=lambda l: (l[1], l[0])); res = []
    # (21-10) renglón con una ETIQUETA a su izquierda en la misma fila («Storm:  When three cards...»): empieza párrafo
    def con_etiqueta(l):
        h = l[3] - l[1]
        return any(o is not l and abs((o[1] + o[3]) / 2 - (l[1] + l[3]) / 2) < h / 2 and o[2] <= l[0] + 2 for o in ls)
    for l in ls:
        h = l[3] - l[1]; pegado = None
        if con_etiqueta(l) or (len(l) > 7 and l[7]):
            for b in res:
                if l[1] > b['lineas'][-1][3] and l[0] < b['caja_x1'] and l[2] > b['lineas'][0][0]: b['abierto'] = False
            res.append({'lineas': [l], 'abierto': True, 'caja_x1': l[2]}); continue
        for b in res:
            u = b['lineas'][-1]; hu = u[3] - u[1]
            # (21-10) un renglón con viñeta («· Dance Battle (5)») es un título: va solo; renglones CORTOS apilados son
            # etiquetas («1 Hit», «2 Hits»), no un párrafo
            if b['lineas'][0][4].lstrip()[:1] in '·•' or (len(u[4].strip()) < 14 and len(l[4].strip()) < 14): continue
            if len(l) > 7 and l[7]: continue   # renglón con viñeta = elemento nuevo de la lista
            if _r.search(r'\(\d+\)\s*$', b['lineas'][0][4]) and len(b['lineas']) == 1: continue   # «Dance Battle (6)» = título
            if len(l) > 6 and len(u) > 6 and sum(abs(x - y) for x, y in zip(l[6], u[6])) > 90: continue   # otro color (subtítulo rosa)
            if _r.match(r'\s*\d+(?:\s+[A-Za-z]|[-+])', l[4]) and not u[4].rstrip().endswith((',', 'of', 'and', 'the')): continue   # lista: «4 Wind tiles»
            if (abs(l[0] - b['lineas'][0][0]) < max(12, h * 0.6) and 0 <= l[1] - u[3] < 0.45 * max(h, hu)
                    and 0.78 < h / max(1, hu) < 1.28 and b['abierto']):   # (21-10) antes 0.75-1.33 (título pegado); 0.87-1.15 partía párrafos
                pegado = b; break
        if pegado: pegado['lineas'].append(l)
        else:
            for b in res:                       # un bloque se cierra en cuanto aparece algo debajo que no le pertenece
                if l[1] > b['lineas'][-1][3] and l[0] < b['caja_x1'] and l[2] > b['lineas'][0][0]: b['abierto'] = False
            res.append({'lineas': [l], 'abierto': True, 'caja_x1': l[2]})
        b = pegado or res[-1]; b['caja_x1'] = max(b['caja_x1'], l[2])
    for b in res:
        L = b['lineas']; b['caja'] = (min(l[0] for l in L), min(l[1] for l in L), max(l[2] for l in L), max(l[3] for l in L))
        t = ''
        for l in L:
            s = l[4].strip()
            t = (t[:-1] + s) if t.endswith('-') and not t.endswith(' -') else (t + ' ' + s if t else s)
        b['texto'] = t; del b['abierto'], b['caja_x1']
    return res


def _etiquetas(lineas):
    ls = sorted(lineas, key=lambda l: (l[1], l[0])); res = []
    for l in ls:
        h = l[3] - l[1]; pegado = None
        for b in res:
            u = b['lineas'][-1]
            if 0 <= l[1] - u[3] < 0.25 * h and 0.75 < h / max(1, u[3] - u[1]) < 1.33 and (abs(l[0] - u[0]) < 6 or abs(l[2] - u[2]) < 6):
                pegado = b; break
        if pegado: pegado['lineas'].append(l)
        else: res.append({'lineas': [l]})
    for b in res:
        L = b['lineas']; b['caja'] = (min(l[0] for l in L), min(l[1] for l in L), max(l[2] for l in L), max(l[3] for l in L))
        b['texto'] = ' '.join(l[4].strip() for l in L)
        x0, x1 = b['caja'][0], b['caja'][2]
        izq = sum(1 for l in ls if l not in L and abs(l[0] - x0) < 5); der = sum(1 for l in ls if l not in L and abs(l[2] - x1) < 5)
        if len(L) > 1: izq += abs(L[0][0] - L[1][0]) < 6; der += abs(L[0][2] - L[1][2]) < 6
        b['alinear'] = 'der' if der > izq else 'izq'
        b['etiqueta'] = True
    return res


def quitar_vineta(a, l):
    """Si la línea empieza con una viñeta (mancha pequeña separada del texto por un hueco), devuelve la línea sin ella
    (la viñeta se queda en la imagen)."""
    x0, y0, x1, y1 = l[:4]; h = y1 - y0
    m = mascara_tinta(a, (x0, y0, x1, y1), pad=0)[0][y0:y1, x0:x1]
    cols = m.any(0); xs = np.where(cols)[0]
    if len(xs) < 4: return l
    # primer hueco de al menos 0.35·h dentro del primer 1.3·h
    run = 0; empezado = False
    for x in range(min(len(cols), int(1.3 * h))):
        if cols[x]: empezado = True; run = 0
        elif empezado:
            run += 1
            if run >= max(3, int(0.35 * h)):
                ancho_mancha = x - run - xs[0] + 1
                if ancho_mancha <= 0.5 * h and cols[x:].any():
                    nx = x0 + x + int(np.argmax(cols[x:])); return [nx, y0, x1, y1] + list(l[4:])
                return l
    return l


def mascara_tinta(a, caja, pad=2):
    """Píxeles de letra dentro de la caja: se separa en dos grupos por brillo (Otsu) y la letra es el grupo menor
    (así una placa o barra detrás del texto queda como fondo). Con transparencia se usa el brillo sobre negro."""
    H, W = a.shape[:2]; x0, y0, x1, y1 = caja
    x0, y0, x1, y1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
    m = np.zeros((H, W), bool)
    z = a[y0:y1, x0:x1].astype(np.float32)
    v = z[..., :3].mean(2) * (z[..., 3] / 255 if a[..., 3].min() < 250 else 1)
    v8 = np.ascontiguousarray(v.clip(0, 255).astype(np.uint8))
    if v8.size == 0 or v8.max() - v8.min() < 20: return m, None
    t, _ = cv2.threshold(v8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    alto = v8 > t
    tinta = alto if alto.sum() <= (~alto).sum() else ~alto
    m[y0:y1, x0:x1] = tinta
    return m, (x0, y0, x1, y1)


def caja_tinta(a, l):
    m, _ = mascara_tinta(a, l[:4], pad=1)
    ys, xs = np.where(m)
    if len(ys) < 5: return l[:4]
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def color_tinta(a, m):
    if m.sum() < 5: return (255, 255, 255)
    nucleo = cv2.erode(m.astype(np.uint8), np.ones((2, 2), np.uint8)).astype(bool)
    if nucleo.sum() < 5: nucleo = m
    return tuple(int(c) for c in np.median(a[..., :3][nucleo], 0))


def borrar(a, cajas):
    """a: RGBA uint8. Quita la tinta de todas las cajas y rellena; con alfa, rellena también el alfa."""
    m = np.zeros(a.shape[:2], bool)
    for c in cajas: m |= mascara_tinta(a, c)[0]
    mk = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2) * 255
    out = a.copy()
    out[..., :3] = cv2.inpaint(np.ascontiguousarray(a[..., :3]), mk, 3, cv2.INPAINT_TELEA)
    if a[..., 3].min() < 250:
        out[..., 3] = cv2.inpaint(np.ascontiguousarray(a[..., 3]), mk, 3, cv2.INPAINT_TELEA)
    return out


SIMBOLOS = set('△○✕□×◯◎●■▲▼◆★☆→←↑↓')
F_SIMB = 'C:/Windows/Fonts/seguisym.ttf'


def _trozos(s):
    t = []
    for c in s:
        sim = c in SIMBOLOS
        if t and t[-1][0] == sim: t[-1][1] += c
        else: t.append([sim, c])
    return t


def largo(s, f):
    fs = ImageFont.truetype(F_SIMB, f.size)
    return sum((fs if sim else f).getlength(x) for sim, x in _trozos(s))


def pintar(d, x, y, s, f, fill):
    fs = ImageFont.truetype(F_SIMB, f.size)
    for sim, x_ in _trozos(s):
        ff = fs if sim else f; d.text((x, y), x_, font=ff, fill=fill, anchor='ls'); x += ff.getlength(x_)


def medir(a, l, ruta_fuente):
    """Tamaño de letra y línea base de un renglón a partir de su tinta real y del texto inglés leído."""
    ix0, iy0, ix1, iy1 = caja_tinta(a, l)
    f = ImageFont.truetype(ruta_fuente, 100); bb = f.getbbox(l[4].strip() or 'H', anchor='ls')
    alto100 = max(1, bb[3] - bb[1])
    tam = max(7, round(100 * (iy1 - iy0) / alto100))
    base = iy1 - round(bb[3] * tam / 100)
    return tam, base, (ix0, iy0, ix1, iy1)


def partir(texto, fuente, ancho):
    pal = texto.split(); ls = []; cur = ''
    for p in pal:
        prueba = (cur + ' ' + p).strip()
        if fuente.getlength(prueba) <= ancho or not cur: cur = prueba
        else: ls.append(cur); cur = p
    if cur: ls.append(cur)
    return ls


def escribir_pincel(img, a, bloque, texto):
    """Rótulo de pincel en un renglón (títulos de capítulo): letra de pincel blanca a la altura de la tinta original,
    alineada como el original y sin pasar de su ancho (x1.15); si el original está desenfocado (estela), se desenfoca."""
    import rotulos
    from PIL import ImageFilter
    L = bloque['lineas']
    if ' / ' in texto and len(L) > 1:   # (21-10) rótulo de varios renglones: un trozo por renglón («A Y / B»)
        for l, parte in zip(L, texto.split(' / ')): escribir_pincel(img, a, dict(bloque, lineas=[l]), parte)
        return None
    ix0, iy0, ix1, iy1 = caja_tinta(a, L[0])
    z = a[iy0:iy1, ix0:ix1].astype(np.float32); v = z[..., :3].mean(2) * z[..., 3] / 255
    borroso = ((v > 40) & (v < 200)).sum() / max(1, (v > 40).sum()) > 0.45
    # (21-10, pedido del usuario) el juego muestra SOLO el trozo de la textura donde estaba el inglés: el español debe
    # caber entero en esa caja (ancho del inglés, y el alto CON tildes); antes se permitía 1.15 y el «1» salía cortado
    alto = int((iy1 - iy0) * 0.95); texto = texto.upper().replace(' ', '  ')   # el espacio de la letra de pincel es muy estrecho
    m, _ = rotulos._texto(texto, alto, int((ix1 - ix0) * 0.98))
    if m.height > iy1 - iy0:
        m, _ = rotulos._texto(texto, int(alto * (iy1 - iy0) / m.height), int((ix1 - ix0) * 0.98))
    # (21-10) en renglones chicos el engorde y el desenfoque fuerte dejaban una mancha ilegible: solo en los grandes
    if m.height >= 40: m = m.filter(ImageFilter.MaxFilter(3))
    if borroso: m = m.filter(ImageFilter.GaussianBlur(1.2 if m.height >= 40 else 0.6))
    x = ix1 - m.width if bloque.get('alinear') == 'der' else ix0
    y = iy1 - m.height if m.height >= (iy1 - iy0) * 0.9 else (iy0 + iy1 - m.height) // 2
    capa = Image.new('RGBA', m.size, (255, 255, 255, 0)); capa.putalpha(m)
    img.alpha_composite(capa, (max(0, x), max(0, y)))
    return None



def repartir(texto, anchos):
    """(21-10) Parte el español en tantos renglones como el inglés, con longitudes proporcionales a las del inglés
    (cortando entre palabras): así cada renglón va en su sitio y la maquetación del original se respeta."""
    if texto.count(' / ') == len(anchos) - 1: return [s.strip() for s in texto.split(' / ')]   # reparto a mano
    pal = texto.split(); total = sum(anchos); n = len(anchos)
    if n <= 1 or len(pal) <= 1: return [texto] + [''] * (n - 1)
    largo_t = len(texto); res = []; i = 0
    for k in range(n - 1):
        meta = largo_t * sum(anchos[:k + 1]) / total
        cur = ' '.join(res + [''])
        mejor, mejor_d = i, None
        for j in range(i + 1, len(pal) - (n - 2 - k)):
            d = abs(len(' '.join(pal[:j])) - meta)
            if mejor_d is None or d < mejor_d: mejor, mejor_d = j, d
        res.append(' '.join(pal[i:mejor])); i = mejor
    res.append(' '.join(pal[i:]))
    return res


def escribir_renglones(img, a, bloque, texto, negrita=False):
    """(21-10) Párrafo renglón a renglón: cada trozo del español en la línea base y el margen de SU renglón inglés, con
    el tamaño medido; si alguno no cabe en el ancho del párrafo (+6 %), se achica el párrafo ENTERO por igual (hasta
    70 %) y después se estrecha ese renglón. Nada se sale del panel ni se pisa con lo de al lado."""
    L = bloque['lineas']; ruta = FUENTE_N if negrita else FUENTE
    med = [medir(a, l, ruta) for l in L]
    tam = bloque.get('tam_fijo') or int(np.median([m[0] for m in med]))
    x0 = min(m[2][0] for m in med); x1 = max(m[2][2] for m in med)
    tope = min(int((x1 - x0) * 1.06), img.width - x0 - 10)   # nunca hasta el borde de la textura
    trozos = repartir(texto, [max(1, m[2][2] - m[2][0]) for m in med])
    for esc in (1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7):
        f = ImageFont.truetype(ruta, max(7, int(tam * esc)))
        if all(largo(s, f) <= tope for s in trozos): break
    d = ImageDraw.Draw(img); color = bloque.get('color', (255, 255, 255)) + (255,)
    for s, m in zip(trozos, med):
        if not s: continue
        xx = m[2][0] if abs(m[2][0] - x0) > 3 * tam else x0; y = m[1]; w = largo(s, f)   # mismo margen del párrafo (el OCR a veces empieza tarde)
        if xx + w > x0 + tope:                               # estrechar este renglón para que no se salga
            capa = Image.new('RGBA', (int(w) + 4, f.size * 2), (0, 0, 0, 0))
            pintar(ImageDraw.Draw(capa), 2, f.size * 1.5, s, f, color)
            capa = capa.resize((max(1, x0 + tope - xx), capa.height), Image.LANCZOS)
            img.alpha_composite(capa, (max(0, int(xx) - 2), int(y - f.size * 1.5))); continue
        pintar(d, xx, y, s, f, color)
    return None

def escribir(img, a, bloque, texto, limite_y, ancho_pag, negrita=False, alinear=None):
    """Escribe el bloque traducido sobre img (PIL RGBA ya borrada); a = original (para medir). Devuelve aviso o None."""
    texto = texto.replace('《', '«').replace('》', '»')   # (21-10) la letra no tiene 《》: salían cuadraditos
    if bloque['lineas'][0][4].lstrip()[:1] in '·•▪■-*' or (len(bloque['lineas'][0]) > 7 and bloque['lineas'][0][7]):
        texto = texto.lstrip('·•▪■-*· ')   # la viñeta del original ya se conserva en la imagen
    L0 = bloque['lineas']
    if len(L0) > 1 and not bloque.get('etiqueta') and not bloque.get('pincel'):
        return escribir_renglones(img, a, bloque, texto, negrita)
    if bloque.get('pincel'): return escribir_pincel(img, a, bloque, texto)
    L = bloque['lineas']; ruta = FUENTE_N if negrita else FUENTE
    med = [medir(a, l, ruta) for l in L]
    tam = bloque.get('tam_fijo') or int(np.median([m[0] for m in med]))
    x0 = min(m[2][0] for m in med); x1 = max(m[2][2] for m in med)
    if bloque.get('x_alinear') is not None: x0 = bloque['x_alinear']
    if bloque.get('x_min'): x0 = max(x0, bloque['x_min'])
    y_top = min(m[2][1] for m in med); base0 = med[0][1]
    paso = int(np.median([med[i + 1][1] - med[i][1] for i in range(len(L) - 1)])) if len(L) > 1 else None
    ancho = x1 - x0
    # (21-10, pedido del usuario: nada fuera de su sitio) el párrafo NO se ensancha hacia el resto de la página (se salía
    # del panel): mismo ancho que el inglés; si no cabe, más renglones o letra algo menor
    if len(L) > 1 and not bloque.get('etiqueta'): ancho = int(ancho * 1.03)
    if alinear is None: alinear = bloque.get('alinear')
    if alinear is None:
        cx = (x0 + x1) / 2   # (21-10) centrado solo los títulos cortos: un renglón ancho que «cae» en el centro va a la izquierda
        alinear = 'centro' if len(L) == 1 and abs(cx - ancho_pag / 2) < ancho_pag * 0.03 and (x1 - x0) < ancho_pag * 0.45 and not (len(L[0]) > 7 and L[0][7]) else 'izq'
    tope = int(ancho * (1.35 if bloque.get('etiqueta') and not bloque.get('estricto') else 1.0))
    if bloque.get('tope_x'): tope = max(tope, bloque['tope_x'] - x0)
    if len(L) == 1 and not bloque.get('estricto') and not bloque.get('etiqueta'):   # (21-10) título de un renglón: puede crecer
        tope = max(tope, min(int(ancho * 1.5), int(ancho_pag - x0 - 12) if alinear != 'centro' else int(ancho * 1.5)))   # hasta su tamaño
    for esc in ((1.0, 0.95, 0.9) if bloque.get('etiqueta') else (1.0, 0.95, 0.9, 0.85, 0.8, 0.75)):
        f = ImageFont.truetype(ruta, max(7, int(tam * esc)))
        p = int(paso * max(esc, 0.9)) if paso else int(f.size * 1.25)
        ls = partir(texto, f, ancho) if len(L) > 1 else [texto]
        alto_total = (len(ls) - 1) * p + (base0 - y_top) + int(f.size * 0.25)
        if (y_top + alto_total <= limite_y or (bloque.get('tam_fijo') and len(L) == 1)) and all(largo(s, f) <= tope * 1.02 for s in ls): break   # (21-10) renglón de tamaño fijo: va en su línea base, no se achica por el de abajo
    aviso = f'no cabe en alto: {texto[:40]}' if y_top + alto_total > limite_y else None
    d = ImageDraw.Draw(img); color = bloque.get('color', (255, 255, 255)) + (255,)
    for i, s in enumerate(ls):
        w = largo(s, f); y = base0 + i * p
        if w > tope:                                      # estrechar este renglón
            capa = Image.new('RGBA', (int(w) + 4, f.size * 2), (0, 0, 0, 0))
            pintar(ImageDraw.Draw(capa), 2, f.size * 1.5, s, f, color)
            capa = capa.resize((tope, capa.height), Image.LANCZOS); w = tope
            xx = x0 if alinear == 'izq' else (x1 - w if alinear == 'der' else (x0 + x1 - w) / 2)
            img.alpha_composite(capa, (max(0, int(xx) - 2), int(y - f.size * 1.5))); continue
        xx = x0 if alinear == 'izq' else (x1 - w if alinear == 'der' else (x0 + x1 - w) / 2)
        pintar(d, xx, y, s, f, color)
    return aviso


def modo_de(ruta):
    n = ruta.split('/')[-1]
    return 'parrafos' if n.startswith(('rule_', '2d_yk_sstory', 'firstload', '2d_cf_light', '2d_cf_first')) else 'etiquetas'


_BLOQUES = None
_MGS = None
ARREGLOS_MGS = {'Pulsa': 'Presiona', 'Apretar manos': 'Dar la mano', 'apretar manos': 'dar la mano', 'No batear': 'Evitar'}


_GEN = None
def _mgs_linea(texto, nt):
    """(21-10) Renglón de controles sin traducción propia (venía pegado a otros): el texto del juego o, si lleva «/»,
    cada parte por separado. None si alguna parte no se conoce (se deja en inglés)."""
    global _GEN
    from imagenes_lotes import arreglar
    from aplicar import traducciones
    if _GEN is None:
        g, _ = traducciones(); _GEN = {nt(k): v for k, v in g.items()}
    v = _mgs_votos(nt)
    def una(t):
        k = nt(t); r = v.get(k) or _GEN.get(k)
        return ' '.join(r.split()) if r else None
    t = arreglar(texto); r = una(t)
    if r: return r
    partes = [una(x) for x in t.split('/')]
    return '/'.join(partes) if len(partes) > 1 and all(partes) else None


def _mgs_votos(nt):
    """Traducción más repetida de cada texto en TODAS las páginas de controles (_mgs_), con arreglos de español neutro."""
    global _MGS
    if _MGS is None:
        import collections
        from aplicar import traducciones, norm
        gen, _ = traducciones(); votos = collections.defaultdict(collections.Counter)
        for k, v in _BLOQUES.items():
            if '_mgs_' not in k: continue
            t = gen.get(norm(v['juego'])) if v.get('juego') else gen.get(v['en'])
            if t: votos[nt(v['en'])][' '.join(t.split())] += 1
        _MGS = {}
        FIJOS = {'adjusthittingangle/': 'Ajustar ángulo/', 'controlmallet/': 'Mover mazo/', 'controlperspective': 'Mover cámara', 'displayscores': 'Mostrar puntajes', 'display/': 'Mostrar/', 'hideactioncommands': 'Ocultar comandos', 'positioncueball': 'Colocar bola blanca', '（+withleftstick)': '(+ joystick izq.)', '(+withleftstick)': '(+ joystick izq.)', 'supertakeback': 'Súper deshacer', 'takeback': 'Deshacer', 'bet:': 'Con apuesta:', 'retrievethechipsyoubet': 'Recuperar fichas', 'nobet:': 'Sin apuesta:', 'betthesameamountas': 'Repetir la', 'thepreviousbet': 'apuesta anterior', 'firegun': 'Disparar', 'stance': 'Postura', 'long-rangeattack': 'Ataque a distancia', 'loveshineattack': 'Ataque Love Shine', 'tackle': 'Placaje', '(+leftstick)': '(+ joystick izq.)', 'climaxheat': 'Clímax Heat', 'avoid': 'Evitar', 'swing': 'Batear', 'jump': 'Saltar', 'rightstick': 'Joystick der.', 'reload': 'Recargar', 'timinginput': 'Toca a tiempo', 'shakehands': 'Dar la mano'}
        for k, c in votos.items():
            t = c.most_common(1)[0][0]
            for a_, b_ in ARREGLOS_MGS.items(): t = t.replace(a_, b_)
            _MGS[k] = t
        _MGS.update(FIJOS)
    return _MGS


def traducir_textura(ruta, lineas, es, negritas=(), alineaciones=None):
    a = np.asarray(Image.open(origen(ruta)).convert('RGBA')).copy()
    def _con_color(l):   # (21-10) color de la tinta + si llevaba viñeta (cada viñeta empieza renglón propio)
        l2 = quitar_vineta(a, l); m, _ = mascara_tinta(a, l2[:4]); return list(l2[:6]) + [color_tinta(a, m), l2[0] != l[0]]
    bs = bloques([_con_color(l) for l in lineas], modo_de(ruta))
    if '_mgs_' in ruta:   # (21-10) controles: un bloque POR RENGLÓN (juntar renglones de la columna mezclaba filas)
        bs = [x for l in lineas for x in bloques([quitar_vineta(a, l)], modo_de(ruta))]
        for x in bs:     # renglones que se pisan en vertical (OCR con aire): cada caja termina donde empieza la de abajo
            c = x['caja']
            sig = [o['caja'][1] for o in bs if o is not x and c[1] < o['caja'][1] < c[3] and o['caja'][0] < c[2] and o['caja'][2] > c[0]]
            if sig: x['caja'] = [c[0], c[1], c[2], max(c[1] + 6, min(sig))]
    if modo_de(ruta) == 'etiquetas' and '_mgs_' not in ruta and len(lineas) >= 10:
        for b in bs: b['estricto'] = True          # atlas de palabras sueltas: no pasar del ancho (pisaría a la vecina)
    if '/chapter/' in ruta:
        for b in bs: b['pincel'] = True            # títulos de capítulo: letra de pincel
    # (21-10) la traducción se busca por el TEXTO del renglón, no por su número: el orden de los bloques al dibujar no
    # siempre es el del momento de traducir (salían filas cambiadas: «Avoid» -> «No batear»)
    global _BLOQUES
    if '_BLOQUES' not in globals() or _BLOQUES is None:
        _BLOQUES = json.load(open(os.path.join(T, 'imagenes', 'bloques.json'), encoding='utf-8'))
    import re as _re
    from imagenes_lotes import arreglar as _arr
    nt = lambda t: _re.sub(r'\s', '', _arr(t or '').lower())    # conserva △○□✕
    por_texto = {}
    for k, v in _BLOQUES.items():
        if k.split('#')[0] == ruta and k in es: por_texto.setdefault(nt(v['en']), es[k])
    es = dict(es)
    if '_mgs_' in ruta:                 # (21-10) controles: la MISMA traducción para el mismo control en todas las páginas
        por_texto = dict(por_texto); por_texto.update(_mgs_votos(nt))
    _fijos_p = os.path.join(T, 'imagenes', 'terminos_paginas.json')
    if os.path.exists(_fijos_p): por_texto.update({nt(k): v for k, v in json.load(open(_fijos_p, encoding='utf-8')).items()})
    for i, b in enumerate(bs):
        t = por_texto.get(nt(b['texto']))
        if t is not None and '_mgs_' in ruta and nt(b['texto']) == 'button': t = 'Botón □'   # el OCR no lee el □
        if t is None and '_mgs_' in ruta: t = _mgs_linea(b['texto'], nt)
        # el ✕ de delante es una viñeta que se conserva: no repetirlo detrás («✕ Botón ✕»)
        if t: t = t.replace('（', '(').replace('）', ')')   # paréntesis japoneses: la letra no los tiene
        if t and '_mgs_' in ruta and b['texto'].lstrip()[:1] in '✕×' and t.endswith(('✕', '×')): t = t[:-1].rstrip()
        if t is not None: es[f'{ruta}#{i}'] = t
        elif f'{ruta}#{i}' in es and '_mgs_' in ruta: del es[f'{ruta}#{i}']   # controles: sin traducción segura se deja; resto: por número (como antes)
    # (21-10) marcas de agua del fondo (DARTSLIVE2 leído a trozos: DARTS, VE2, DAF...) y rótulos diminutos de las
    # capturas del juego: NO son texto a traducir (salían «Dardos», «PARTE» encima del fondo)
    import re as _r2
    def _basura(b):
        s = b['texto'].replace(' ', '')
        alto = min(l[3] - l[1] for l in b['lineas'])
        if all(l[2] - l[0] < 20 and l[3] - l[1] > 30 for l in b['lineas']): return True   # rótulo vertical («2to1» del tapete)
        return (_r2.search(r'DART|TSL|LVE|IVE2|^VE2$|^DAF$|^DAR$|^CR$|R2XX' + ('|^A?R?TS?$|PART' if 'darts' in ruta else ''), s, _r2.I) and len(s) < 16) or ('/rule_' in ruta and alto < 20)
    hacer = [(i, b) for i, b in enumerate(bs) if es.get(f'{ruta}#{i}', b['texto']).strip() != b['texto'].strip() and not _basura(b)]
    if '/rule_' in ruta or '/takara/' in ruta:   # (21-10) un solo cuerpo de letra para el texto normal de la página (uniforme)
        alts = sorted(l[3] - l[1] for i, b in hacer for l in b['lineas'])
        if alts:
            H0 = alts[len(alts) // 2]
            normales = [l for i, b in hacer for l in b['lineas'] if 0.8 * H0 <= l[3] - l[1] <= 1.2 * H0 and len(l[4]) > 12]
            if len(normales) >= 3:
                tf = int(np.median([medir(a, l, FUENTE)[0] for l in normales]))
                for i, b in hacer:
                    if all(l[3] - l[1] <= 1.35 * H0 for l in b['lineas']): b['tam_fijo'] = tf   # también etiquetas cortas («Uno:»)
        for i, b in hacer:   # (21-10) etiqueta con algo a su derecha en la misma fila: puede crecer hasta ahí (no se achica sola)
            c = b['caja']; h = c[3] - c[1]
            der = [o['caja'][0] for o in bs if o is not b and o['caja'][0] > c[2] and abs((o['caja'][1] + o['caja'][3]) / 2 - (c[1] + c[3]) / 2) < h / 2]
            if der and len(b['lineas']) == 1: b['tope_x'] = min(der) - 18
            izq = [o['caja'][2] for o in bs if o is not b and o['caja'][2] <= c[0] + 12 and c[0] - o['caja'][2] < 40 and abs((o['caja'][1] + o['caja'][3]) / 2 - (c[1] + c[3]) / 2) < h / 2]
            if izq and len(b['lineas']) == 1: b['x_min'] = max(izq) + 10   # etiqueta a la izquierda («1-4 Han:»): no pisarla
    if not hacer: return None, []
    for i, b in hacer:
        m = np.zeros(a.shape[:2], bool)
        for l in b['lineas']: m |= mascara_tinta(a, l[:4])[0]
        b['color'] = color_tinta(a, m)
    cajas_b = []
    for i, b in hacer:
        mx = min(l[0] for l in b['lineas']) if len(b['lineas']) > 1 else None
        for l in b['lineas']: cajas_b.append([min(l[0], mx - (l[3] - l[1]) // 2) if mx is not None else l[0]] + list(l[1:4]))   # medio alto más a la izq.: restos como «a»
        if b.get('x_min'): cajas_b[-1][0] = max(cajas_b[-1][0], b['x_min'] - 4)
        if mx is None and '/rule_' in ruta and not (len(b['lineas'][0]) > 7 and b['lineas'][0][7]):   # (21-10) renglón suelto JUSTO debajo de un párrafo que empieza más a la izquierda:
            l = b['lineas'][0]; h = l[3] - l[1]   # el OCR empezó tarde («a rival»): borrar desde ese margen y escribir alineado
            arriba = [o for o in bs if o is not b and 0 <= l[1] - o['caja'][3] < h and o['caja'][0] < l[0] - 4 and l[0] - o['caja'][0] < 2 * h]
            if arriba: cajas_b[-1][0] = arriba[0]['caja'][0]; b['x_alinear'] = arriba[0]['caja'][0]
        if mx is None and '/rule_' in ruta and len(b['texto'].strip()) <= 12 and b['texto'].lstrip()[:1].isdigit():   # solo etiquetas cortas que empiezan por número («1 Hit»)   # renglón suelto: mirar si a su izquierda pegada hay tinta (un «1 » perdido)
            cajas_b[-1][0] = max(0, l[0] - int((l[3] - l[1]) * 0.9))
    limpia = borrar(a, cajas_b)
    hechos_ids = {id(b) for i, b in hacer}   # (21-10) lo que NO se traduce (etiquetas «1-4 Han:», números) vuelve tal cual:
    for o_ in bs:                            # el borrado del renglón vecino no se lo puede comer
        if id(o_) not in hechos_ids and not _basura(o_):
            x0_, y0_, x1_, y1_ = o_['caja']; limpia[y0_:y1_, x0_:x1_] = a[y0_:y1_, x0_:x1_]
    H, W = a.shape[:2]
    if a[..., 3].min() < 250:                     # fondo transparente: en los rótulos de pincel (con estela) se vacía la caja
        for i, b in hacer:
            if b.get('pincel'):
                x0, y0, x1, y1 = b['caja']; limpia[max(0, y0 - 6):y1 + 6, max(0, x0 - 10):(W if '/chapter/' in ruta else x1 + 24), 3] = 0   # capítulos: la estela llega al borde
    img = Image.fromarray(limpia); avisos = []
    H, W = a.shape[:2]
    for i, b in hacer:
        debajo = [c['caja'][1] for c in bs if c['caja'][1] > b['caja'][3] and c['caja'][0] < b['caja'][2] and c['caja'][2] > b['caja'][0]]
        lim = min(debajo) - 4 if debajo else H - 4
        al = (alineaciones or {}).get(i)
        av = escribir(img, a, b, es[f'{ruta}#{i}'], lim, W, negrita=i in negritas, alinear=al)
        if av: avisos.append(av)
    return img, avisos


if __name__ == '__main__':
    ocr = json.load(open(os.path.join(T, 'imagenes', 'ocr.json'), encoding='utf-8'))
    es = json.load(open(os.path.join(T, 'imagenes', 'ocr_es.json'), encoding='utf-8'))
    for ruta in (sys.argv[1:] or sorted({k.split('#')[0] for k in es})):
        img, av = traducir_textura(ruta, ocr[ruta], es)
        if img is None: continue
        atlas_es.TEX = os.path.join(T, 'extraido_r' if ruta.startswith('ui_en/') else 'extraido')
        atlas_es.guardar_dds(ruta[:-4], img)
        o = Image.open(origen(ruta)).convert('RGBA'); W, H = o.size
        v = Image.new('RGBA', (W, H * 2), (40, 90, 40, 255)); v.alpha_composite(o); v.alpha_composite(img, (0, H))
        os.makedirs(os.path.join(T, 'imagenes', 'revision'), exist_ok=True)
        v.convert('RGB').save(os.path.join(T, 'imagenes', 'revision', ruta.split('/')[-1][:-4] + '.png'))
        print('ok', ruta, av)
