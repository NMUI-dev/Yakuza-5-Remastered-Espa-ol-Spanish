# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) v1.0.1: rehace las PÁGINAS de imagen que salieron mal en la v1.0 (renglones en inglés, letra
diminuta, filas cambiadas). Causa en la v1.0: el OCR a tamaño real juntaba palabras y se saltaba renglones, y los bloques
no coincidían con las frases de la traducción (el español de varias frases acababa en un solo hueco).
Método:
 1. OCR a DOBLE tamaño (lee bien) -> revision_v101/ocr2x.json.
 2. Las etiquetas de color dentro del renglón («Chi: If an...») se separan del texto por el hueco de tinta.
 3. En el texto de la página se buscan las frases EXACTAS del juego (traducciones.json) que ocupan renglones enteros;
    lo que no está en el juego lo traduce un modelo gratis de OpenRouter con el contexto de la página (frases_extra.json).
 4. Cada frase se escribe en el hueco de SUS renglones: Segoe (Georgia en el Coliseo), su color, el tamaño común de la
    página, sangría francesa como el original; si no cabe se achica hasta el 72 % y se avisa.
  python herramientas/paginas_v101.py <ruta.dds> ...  -> trabajo/imagenes/es_v101/<ruta>.dds + revision_v101/rehechas/*.png
"""
import os, sys, json, re, time, statistics
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
import paginas_es as P
from ocr_imagenes import origen
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
TR = json.load(open(os.path.join(R, 'entrega', 'Herramientas para traduccion', 'datos', 'traducciones.json'), encoding='utf-8'))
RV = os.path.join(T, 'imagenes', 'revision_v101')
SAL = os.path.join(T, 'imagenes', 'es_v101'); REV = os.path.join(RV, 'rehechas')
EXTRA = os.path.join(RV, 'frases_extra.json')   # inglés -> español que no está en el juego (traducido aparte / a mano)
if os.path.exists(EXTRA): TR.update(json.load(open(EXTRA, encoding='utf-8')))
GEO = 'C:/Windows/Fonts/georgia.ttf'
NO_TOCAR = {'pausepar_pause_en/picture/rule_h_dance_battle3.dds': ('Power', 'Low', 'High')}   # rótulos del medidor: a mano
CORTAS = {'Todos impares': 'Impares', 'Todos pares': 'Pares'}   # etiquetas que no caben junto a sus iconos
F2X = os.path.join(RV, 'ocr2x.json')
OCR = json.load(open(F2X, encoding='utf-8')) if os.path.exists(F2X) else {}
_MOTOR = []


def norm(s): return re.sub(r'[^a-z0-9]', '', s.lower().replace('’', "'"))


INDICE = {}
for _en, _es in TR.items():
    _n = norm(_en)
    if len(_n) >= 3 and _es and _es != _en and _n not in INDICE: INDICE[_n] = (_en, _es)
if os.path.exists(EXTRA):   # (25-10) lo puesto a mano manda sobre el texto del juego
    for _en, _es in json.load(open(EXTRA, encoding='utf-8')).items():
        if len(norm(_en)) >= 3 and _es and _es != _en: INDICE[norm(_en)] = (_en, _es)


def ocr2x(ruta):
    if ruta not in OCR:
        if not _MOTOR:
            from rapidocr_onnxruntime import RapidOCR; _MOTOR.append(RapidOCR())
        im = Image.open(origen(ruta)).convert('RGBA'); b = Image.new('RGBA', im.size, (0, 0, 0, 255)); b.alpha_composite(im)
        b = b.convert('RGB').resize((im.width * 2, im.height * 2), Image.LANCZOS)
        r, _ = _MOTOR[0](np.asarray(b))
        OCR[ruta] = [[int(min(p[0] for p in c) / 2), int(min(p[1] for p in c) / 2), int(max(p[0] for p in c) / 2 + 1),
                      int(max(p[1] for p in c) / 2 + 1), t, round(float(sc), 3)] for c, t, sc in (r or []) if sc > 0.5]
        json.dump(OCR, open(F2X, 'w', encoding='utf-8'), ensure_ascii=False)
    return [list(l) for l in OCR[ruta]]


def frases(lineas):
    """-> [(renglones, en, es)] con las frases del juego que ocupan renglones enteros, y los renglones sin frase"""
    texto, dueño, inicios, finales = '', [], set(), set()
    for i, l in enumerate(lineas):
        n = norm(l[4]); inicios.add(len(texto)); texto += n; dueño += [i] * len(n); finales.add(len(texto))
    def alineada(ini, ln): return ln >= 40 or (ini in inicios and ini + ln in finales) or (ln >= 12 and (ini in inicios or ini + ln in finales))
    cands = [(len(k), texto.find(k), k) for k in INDICE if len(k) >= 6 and k in texto]
    usado = [False] * len(texto); out = []
    for ln, ini, k in sorted(cands, reverse=True):
        while ini >= 0 and (any(usado[ini:ini + ln]) or not alineada(ini, ln)): ini = texto.find(k, ini + 1)
        if ini < 0: continue
        rr = sorted(set(dueño[ini:ini + ln]))
        if any(abs(lineas[x][1] - lineas[y][1]) < 6 for x in rr for y in rr if x < y): continue
        for j in range(ini, ini + ln): usado[j] = True
        out.append((ini, rr, INDICE[k]))
    sueltos = sorted({dueño[j] for j in range(len(texto)) if not usado[j]})
    return [[r, en, es] for _, r, (en, es) in sorted(out)], sueltos


MT_MODELOS = ('nvidia/nemotron-3-ultra-550b-a55b:free', 'google/gemma-4-31b-it:free', 'nvidia/nemotron-3.5-super-vl:free')


def traducir_extra(en, pagina, hechas):
    import urllib.request
    extra = json.load(open(EXTRA, encoding='utf-8')) if os.path.exists(EXTRA) else {}
    if en in extra: return extra[en]
    if os.environ.get('SIN_RED'):   # (25-10) cupo gratis agotado: se apunta y lo traduce Claude a mano (frases_extra.json)
        pf = os.path.join(RV, 'pendientes_traduccion.json')
        pend = json.load(open(pf, encoding='utf-8')) if os.path.exists(pf) else {}
        if en not in pend: pend[en] = pagina; json.dump(pend, open(pf, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        return None
    pr = ('Traduce al español neutro latinoamericano este fragmento de una página de reglas de un minijuego del videojuego '
          'Yakuza 5. Usa EXACTAMENTE los mismos términos que ya tiene la página en español (lista de abajo). Si es un nombre '
          'propio o de un juego (Mahjong, Cee-lo, Musashi...), déjalo igual. Devuelve SOLO JSON {"es": "..."}.\n\n'
          'PÁGINA EN INGLÉS:\n' + pagina + '\n\nYA TRADUCIDO EN ESTA PÁGINA:\n' +
          '\n'.join(f'{a} => {b}' for a, b in hechas) + '\n\nFRAGMENTO A TRADUCIR:\n' + en)
    for m in MT_MODELOS:
        for _ in range(2):
            try:
                q = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
                    json.dumps({'model': m, 'messages': [{'role': 'user', 'content': pr}], 'temperature': 0}).encode(),
                    {'Authorization': 'Bearer ' + os.environ['OPENROUTER_API_KEY'], 'Content-Type': 'application/json'})
                t = json.load(urllib.request.urlopen(q, timeout=240))['choices'][0]['message']['content']
                es = json.loads(re.search(r'\{.*\}', t, re.S).group(0))['es'].strip()
                if es:
                    extra[en] = es; json.dump(extra, open(EXTRA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
                    TR[en] = es; return es
            except Exception as e:
                print('  traducción', m, str(e)[:80], flush=True); time.sleep(15)
    return None


def tinta_fondo(a, caja):
    """tinta = lo que se aparta del color del fondo (borde de la caja); a diferencia de Otsu, ve también la tinta ROJA"""
    x0, y0, x1, y1 = caja; z = a[y0:y1, x0:x1, :3].astype(int)
    borde = np.concatenate([z[0], z[-1]]); bg = np.median(borde, 0)
    return np.abs(z - bg).max(2) > 60


def borrar(a, cajas):
    """como paginas_es.borrar pero con la tinta medida contra el fondo (borra también la roja/naranja)"""
    import cv2
    H, W = a.shape[:2]; m = np.zeros((H, W), np.uint8)
    for x0, y0, x1, y1 in cajas:
        x0, y0, x1, y1 = max(0, x0), max(0, y0 - 2), min(W, x1), min(H, y1 + 2)
        if x1 - x0 > 2 and y1 - y0 > 2: m[y0:y1, x0:x1] |= tinta_fondo(a, (x0, y0, x1, y1)).astype(np.uint8)
    m = cv2.dilate(m * 255, np.ones((3, 3), np.uint8), iterations=2)
    out = a.copy(); out[..., :3] = cv2.inpaint(np.ascontiguousarray(a[..., :3]), m, 3, cv2.INPAINT_TELEA)
    if a[..., 3].min() < 250: out[..., 3] = cv2.inpaint(np.ascontiguousarray(a[..., 3]), m, 3, cv2.INPAINT_TELEA)
    return out


def separar_etiquetas(a, ls, FU):
    """«Chi: If an opponent...» en un renglón -> renglón «Chi:» (con su color) + renglón del texto, cortando por el
    primer hueco ancho (> 0,22 del alto) después de la etiqueta"""
    out = []
    for l in ls:
        m = re.match(r"^\W*([A-Za-z][\w \-/'.]{0,22}):\s*(\S.*)$", l[4])
        if m and len(m.group(2)) > 8:
            caja = [l[0], max(0, l[1] - 2), l[2], min(a.shape[0], l[3] + 2)]
            mk = tinta_fondo(a, caja); cols = mk.any(0); h = l[3] - l[1]
            w = ImageFont.truetype(FU, max(8, h)).getlength(m.group(1) + ':') * 0.8
            gap = max(4, int(0.22 * h)); c = None
            for x in range(int(w * 0.6), min(len(cols) - gap, int(w * 2))):
                if cols[x - 1] and not cols[x:x + gap].any(): c = x; break
            if c is not None:
                sig = c + gap + int(np.argmax(cols[c + gap:]))
                tinta = a[caja[1]:caja[3], caja[0]:caja[0] + c, :3][mk[:, :c]]
                resto = a[caja[1]:caja[3], caja[0] + sig:caja[2], :3][mk[:, sig:]]
                col = tuple(int(v) for v in np.median(tinta, 0)) if len(tinta) else (220, 60, 60)
                if not len(resto) or np.abs(np.median(resto, 0) - np.array(col)).max() < 60: out.append(l); continue
                out.append([l[0], l[1], l[0] + c, l[3], m.group(1) + ':', l[5], 'etq', None, col])
                out.append([l[0] + sig, l[1], l[2], l[3], m.group(2), l[5], None, 'tras_etq'])
                continue
        out.append(l)
    return out


def liso(a, y0, y1, x):
    """(25-10) la franja de 12 px en x es fondo de la página: poca variación Y del mismo color que el margen izquierdo
    (un recuadro gris liso de una imagen no cuenta)"""
    z = a[y0:y1, x:x + 12, :3].astype(float); ref = a[y0:y1, 4:30, :3].astype(float)
    return z.std() < 24 and np.abs(z.mean((0, 1)) - ref.mean((0, 1))).max() < 10


def rehacer(ruta):
    a = np.array(Image.open(origen(ruta)).convert('RGBA'))
    H, W = a.shape[:2]
    FU = GEO if 'tougijyo' in ruta else P.FUENTE
    ls = sorted(ocr2x(ruta), key=lambda l: (round(l[1] / 8), l[0]))
    # (25-10) letra diminuta de capturas/iconos («CLIMAX HEAT», «Strength») no es texto de la página: no se toca
    if len(ls) > 4:
        hm = statistics.median(l[3] - l[1] for l in ls)
        ls = [l for l in ls if (l[3] - l[1]) >= 0.7 * hm or l[0] < 0.6 * W]
    ls = [l for l in ls if l[4].strip() not in NO_TOCAR.get(ruta, ()) and not re.match(r'^\s*\d\s*[sSnNrR][tTdD]\.?\s*12|^2\s*to\s*1|^\d+-\d+$|^(EVEN|ODD|1-18|19-36)$', l[4].strip())]
    ls = separar_etiquetas(a, ls, FU)
    vin = []; VIN_IZQ = {}
    for i, l in enumerate(ls):
        n = P.quitar_vineta(a, l)
        if n[0] != l[0] and l[4].lstrip()[:1].isalnum():
            # el OCR leyó una letra ahí («If», «a hand»): solo es viñeta si la mancha es un punto pequeño
            h = l[3] - l[1]; mk = tinta_fondo(a, (l[0], max(0, l[1] - 2), n[0] - 2, min(a.shape[0], l[3] + 2)))
            ys = np.where(mk.any(1))[0]; xs = np.where(mk.any(0))[0]
            if len(ys) and (ys.max() - ys.min() > 0.42 * h or xs.max() - xs.min() > 0.42 * h): n = l   # letra («I», «a»), no viñeta
        if n[0] == l[0]:   # (25-10) viñeta que el OCR dejó fuera de su caja (a la izquierda)
            h = l[3] - l[1]; xa = max(0, l[0] - int(1.2 * h))
            mk = tinta_fondo(a, (xa, l[1], max(xa + 1, l[0] - 2), l[3]))
            ys = np.where(mk.any(1))[0]; xs = np.where(mk.any(0))[0]
            if len(ys) and ys.max() - ys.min() <= 0.42 * h and xs.max() - xs.min() <= 0.42 * h: nl = [max(l[0], xa + int(xs.max()) + int(0.55 * h))] + list(l[1:]); vin.append(True); ls[i] = nl; VIN_IZQ[tuple(nl[:4])] = l[0]; continue
        vin.append(n[0] != l[0]); ls[i] = n
    grupos, sueltos = frases(ls)
    avisos = []
    pagina = '\n'.join(l[4] for l in ls)
    k = 0
    while k < len(sueltos):   # renglones sueltos seguidos y alineados = un párrafo
        r = [sueltos[k]]
        while (k + 1 < len(sueltos) and sueltos[k + 1] == r[-1] + 1 and len(ls[r[-1]]) < 7 and len(ls[sueltos[k + 1]]) < 7
               and not re.search(r'\(\d+\)\s*$', ls[r[-1]][4])   # «· Dance Battle (4)» es un título: va solo
               and 0.8 < (ls[sueltos[k + 1]][3] - ls[sueltos[k + 1]][1]) / max(1, ls[r[-1]][3] - ls[r[-1]][1]) < 1.25
               and (abs(ls[sueltos[k + 1]][0] - ls[r[-1]][0]) < 14 or abs((ls[sueltos[k + 1]][0] + ls[sueltos[k + 1]][2]) - (ls[r[-1]][0] + ls[r[-1]][2])) < 40) and ls[sueltos[k + 1]][1] - ls[r[-1]][3] < 0.8 * (ls[r[-1]][3] - ls[r[-1]][1])):
            k += 1; r.append(sueltos[k])
        k += 1
        en = ' '.join(ls[i][4].strip() for i in r)
        es = TR.get(en) or TR.get(en.rstrip(':')) or (en if len(ls[r[0]]) > 6 and ls[r[0]][6] == 'etq' else None)
        if es and en.endswith(':') and not es.endswith(':'): es += ':'
        if not es and len(norm(en)) > 3: es = traducir_extra(en, pagina, [(g[1], g[2]) for g in grupos])
        if es and (norm(es) != norm(en) or any(len(ls[i]) > 6 and ls[i][6] == 'etq' for i in r)): grupos.append([r, en, es]); avisos.append(f'traducido aparte: «{en[:45]}» -> «{es[:45]}»')
        else:
            # (25-10) palabra suelta pegada al principio de un renglón ya traducido («If» + «you are successful»): se borra con él
            pegado_a = [g for g in grupos if len(r) == 1 and len(norm(en)) <= 4 and abs(ls[g[0][0]][1] - ls[r[0]][1]) < 8
                        and 0 <= ls[g[0][0]][0] - ls[r[0]][2] < 40]
            if pegado_a: pegado_a[0][0].insert(0, r[0]); avisos.append(f'pegado: «{en}»')
            else: avisos.append(f'igual: «{en[:40]}»')
    grupos.sort(key=lambda g: g[0][0])
    # trozos: una lista aplanada se reparte por renglones; «Etiqueta: texto» en dos renglones se separa
    def sin_vin(t): return re.sub(r'^\s*[-·•▪]\s*', '', t)
    trozos = []
    for r, en, es in grupos:
        L = [ls[i] for i in r]
        partes = []
        for pat in (r';\s+|\s+-\s+|\s*·\s+|\n', r'(?<=[.)])\s+(?=[*A-ZÁÉÍÓÚ¿¡(])',
                    r'\s+(?=-?\s*[A-ZÁÉÍÓÚ][a-záéíóúñ]+:)|(?<=\.)\s+(?=\*)'):
            partes = [re.sub(r'^-\s*', '', x.strip()) for x in re.split(pat, es) if x.strip()]
            if len(partes) == len(L): break
        if len(L) > 1 and len(partes) == len(L):
            trozos += [([i], en, sin_vin(x) if vin[i] else x) for i, x in zip(r, partes)]
        elif len(L) > 1 and len(L[0][4].strip()) < 60 and ':' in es[:75] and (L[1][1] > L[0][3] - 2 or (len(L[0]) > 6 and L[0][6] == 'etq')):
            et, resto = es.split(':', 1)
            trozos += [([r[0]], '#etiqueta', et.strip() + ':'), (r[1:], en, resto.strip())]
        else:
            et_en = L[0][4].strip().lstrip('·•* ').strip()
            et_es = TR.get(et_en) if len(L) > 1 and len(et_en) < 60 and L[1][1] > L[0][3] - 2 else None
            if et_es and es.startswith(et_es):   # «All Simples» + explicación sin dos puntos: etiqueta aparte
                trozos += [([r[0]], '#etiqueta', et_es), (r[1:], en, es[len(et_es):].strip())]; continue
            m_t = re.search(r'\(\d+\)', es[:60])
            if len(L) > 1 and re.search(r'\(\d+\)\s*$', L[0][4]) and m_t:   # «· Live Battle (6)» + párrafo: título aparte
                trozos += [([r[0]], '#titulo', sin_vin(es[:m_t.end()]) if vin[r[0]] else es[:m_t.end()]), (r[1:], en, es[m_t.end():].strip())]
            else: trozos.append((r, en, sin_vin(es) if vin[r[0]] else es))
    trozos = [(r, en, re.sub(r'^[\s↓]+', '', es) if ls[r[0]][4].lstrip().startswith('*') else re.sub(r'^[\s*↓]+', '', es)) for r, en, es in trozos]
    trozos = [(r, en, es.replace('《', '«').replace('》', '»')) for r, en, es in trozos]   # flechas y asteriscos del dibujo se quedan
    trozos = [(r, en, es[:-1] if es.endswith(':') and not ls[r[-1]][4].rstrip().endswith(':') else es) for r, en, es in trozos]
    info = []
    for r, en, es in trozos:
        L = [ls[i] for i in r]
        tam, base, _ = P.medir(a, L[0], FU)
        m, _ = P.mascara_tinta(a, L[-1][:4]); col = P.color_tinta(a, m)   # (25-10) el último renglón: el 1.º puede llevar palabras de color
        if len(L[0]) > 8 and L[0][8]: col = tuple(L[0][8])
        etq = en == '#etiqueta' or (len(L[0]) > 6 and L[0][6] == 'etq' and len(L) == 1)
        if etq and es.rstrip(':') in CORTAS: es = CORTAS[es.rstrip(':')] + (':' if es.endswith(':') else '')
        paso = (L[1][1] - L[0][1]) if len(L) > 1 else round((L[0][3] - L[0][1]) * 1.25)
        unico = len(L) == 1 and not any(abs(o[0] - L[0][0]) < 12 for o in ls if o is not L[0])
        info.append(dict(L=L, en=en, es=es, tam=tam, base=base, col=col, paso=max(paso, 10), etq=etq, unico=unico,
                         alto=L[0][3] - L[0][1], x0=L[0][0], xs=min((l[0] for l in L[1:]), default=L[0][0]),
                         y0=min(l[1] for l in L), x1=max(l[2] for l in L), y1=max(l[3] for l in L)))
    # mismo tamaño para renglones de la misma altura (medir varía con mayúsculas/rabos)
    for g in info:
        par = [o['tam'] for o in info if abs(o['alto'] - g['alto']) <= 0.15 * g['alto']]
        if not g['unico']: g['tam'] = round(statistics.median(par))   # (25-10) el título centrado conserva su tamaño
    pasos = [g['paso'] for g in info if len(g['L']) > 1]
    if pasos:   # (25-10) la letra nunca más grande que lo que permite el interlineado del original
        tope = round(statistics.median(pasos) * 0.9)
        for g in info:
            if not g['unico'] and abs(g['alto'] - statistics.median(o['alto'] for o in info)) < 0.2 * g['alto']: g['tam'] = min(g['tam'], tope)
    der = max(l[2] for l in ls); DER_PAG = der
    for g in info:   # el texto que va tras una etiqueta en el mismo renglón empieza donde acaba la etiqueta ya traducida
        if len(g['L'][0]) > 7 and g['L'][0][7] == 'tras_etq':
            et = [o for o in info if o['etq'] and abs(o['y0'] - g['y0']) < 0.5 * g['alto'] and o['x0'] < g['x0']]
            if et:
                et[-1]['tam'] = g['tam']; et[-1]['base'] = g['base']   # la etiqueta, del tamaño de su texto
                g['x0'] = int(et[-1]['x0'] + P.largo(et[-1]['es'] + ' ', ImageFont.truetype(FU, g['tam'])))
            m2, _ = P.mascara_tinta(a, g['L'][0][:4]); g['col'] = P.color_tinta(a, m2)
    def en_tabla(l):   # renglón dentro de una celda con raya oscura encima o debajo
        def raya(y):
            if not 0 <= y < H: return False
            return (a[y, max(0, l[0] - 4):min(W, l[2] + 4), :3].max(1) < 90).mean() > 0.7
        return any(raya(y) for y in range(l[1] - 6, l[1])) and any(raya(y) for y in range(l[3], l[3] + 6))
    todas = [l for g in info for l in g['L']]
    cajas = [[VIN_IZQ[tuple(l[:4])] - 1 if tuple(l[:4]) in VIN_IZQ else l[0] - 8, l[1], l[2] + 4, l[3]] for l in todas if not en_tabla(l)]
    celdas = [l[:4] for l in todas if en_tabla(l)]
    a1 = borrar(a, cajas) if cajas else a
    if celdas: a1 = P.borrar(a1, celdas)   # en la celda, Otsu sobre su caja exacta (no se come el gris de la cabecera)
    img = Image.fromarray(a1); d = ImageDraw.Draw(img)
    for g in info:
        abajo = [o['y0'] for o in info if o['y0'] > g['y1'] - 2 and o['x0'] < max(g['x1'], DER_PAG) and o['x1'] > g['x0']]
        lim_y = (min(abajo) - 2) if abajo else min(H - 4, max(l[3] for l in ls) + 0.6 * g['alto'])
        # (25-10) margen derecho de ESTE bloque: el de los renglones originales de su franja (al lado hay fotos/iconos)
        h3 = 3 * g['alto']
        banda = [l[2] for l in ls if l[1] < lim_y + h3 and l[3] > g['y0'] - h3 and abs(l[0] - g['xs']) < 30]
        der = max([g['x1']] + banda)
        # (25-10) si a la derecha solo hay fondo liso (sin foto ni icono), el texto puede llegar más lejos
        y_a, y_b = max(0, g['y0']), int(min(H, lim_y))
        while der + 12 < W - 0.07 * W and y_b > y_a and liso(a, y_a, y_b, int(der)): der += 12
        centrado = g['unico'] and abs((g['x0'] + g['x1']) / 2 - W / 2) < 25 and g['x0'] > 60
        pegado = len(g['L']) == 1 and any(o is not g['L'][0] and abs(o[0] - g['x0']) < 0.6 * (g['x1'] - g['x0']) and
                                             (0 <= o[1] - g['y1'] < 0.35 * g['alto'] or 0 <= g['y0'] - o[3] < 0.35 * g['alto']) for o in ls)
        def raya(y):
            if not 0 <= y < H: return False
            fila = a[y, max(0, g['x0'] - 4):min(W, g['x1'] + 4), :3].max(1)
            return (fila < 90).mean() > 0.7
        pegado = pegado and any(raya(y) for y in range(g['y0'] - 6, g['y0'])) and any(raya(y) for y in range(g['y1'], g['y1'] + 6))
        g['celda'] = pegado
        # (25-10) rótulo corto suelto (bocadillo, botón): una sola línea, se achica hasta su caja (+30 %)
        corto = (len(g['L']) == 1 and len(g['L'][0][4].strip()) <= 26 and not g['etq'] and not pegado and
                 not any(o is not g['L'][0] and abs(o[0] - g['x0']) < 14 and 0 < o[1] - g['y1'] < 1.5 * g['alto'] for o in ls))
        if corto and not g['unico'] is None:
            g['tam'] = min(g['tam'], round(g['alto'] * 1.15))
            ancho_c = (g['x1'] - g['x0']) * 1.3 + 10
            for f_esc in [x / 100 for x in range(100, 59, -3)]:
                f = ImageFont.truetype(FU, max(8, round(g['tam'] * f_esc)))
                if P.largo(g['es'], f) <= ancho_c: break
            cx = (g['x0'] + g['x1']) / 2
            xx = cx - P.largo(g['es'], f) / 2 if abs(cx - W / 2) < 25 or g.get('caja_blanca') else g['x0']   # (25-10) centrado solo si el original lo estaba
            P.pintar(d, xx, g['base'], g['es'], f, g['col'] + (255,)); continue
        if pegado and not g['etq']:   # (25-10) celda de tabla
            cx = (g['x0'] + g['x1']) / 2; ancho_c = (g['x1'] - g['x0']) + 0.5 * g['alto']
            for f_esc in [x / 100 for x in range(100, 49, -3)]:
                f = ImageFont.truetype(FU, max(8, round(g['tam'] * f_esc)))
                if P.largo(g['es'], f) <= ancho_c: break
            else: avisos.append(f'celda larga: «{g["es"]}»')
            xx = cx - P.largo(g['es'], f) / 2 if g['unico'] or abs(cx - W / 2) > 1 else g['x0']
            P.pintar(d, xx, g['base'], g['es'], f, g['col'] + (255,)); continue
        if g['etq']:   # etiqueta: un renglón, sin salirse mucho de su caja (a su derecha hay iconos o texto)
            lim_x = min([o['x0'] for o in info if o is not g and abs(o['y0'] - g['y0']) < g['alto'] and o['x0'] > g['x0']] + [g['x1'] + 0.1 * (g['x1'] - g['x0'])])
            for f_esc in [x / 100 for x in range(100, 49, -4)]:
                f = ImageFont.truetype(FU, max(8, round(g['tam'] * f_esc)))
                if g['x0'] + P.largo(g['es'], f) <= lim_x: break
            else: avisos.append(f'etiqueta larga: «{g["es"]}»')
            P.pintar(d, g['x0'], g['base'], g['es'], f, g['col'] + (255,)); continue
        for f_esc in [x / 100 for x in range(100, 71, -4)]:
            f = ImageFont.truetype(FU, max(8, round(g['tam'] * f_esc)))
            if centrado:
                rs = [g['es']]; anchos = [max(g['x1'] - g['x0'], P.largo(g['es'], f))]
            else:   # sangría francesa: el 1.er renglón empieza en su sitio, los demás donde los del original
                paso = round(g['paso'] * max(f_esc, 0.85))
                def fin_x(j):   # (25-10) cada renglón llega hasta donde llegaba el renglón original de esa altura,
                    o = g['L'][min(j, len(g['L']) - 1)][2]   # o más allá si a su derecha solo hay fondo liso
                    yb = int(g['base'] + j * paso); ya = max(0, yb - f.size)
                    tope = max(o, der if len(g['L']) == 1 else o)
                    while tope + 12 < W - 0.07 * W and yb > ya and liso(a, ya, min(H, yb + 4), int(tope)): tope += 12
                    return tope
                rs, cur = [], ''
                for p in g['es'].split():
                    an = fin_x(len(rs)) - (g['x0'] if not rs else g['xs'])
                    if not cur or P.largo(cur + ' ' + p, f) <= an: cur = (cur + ' ' + p).strip()
                    else: rs.append(cur); cur = p
                if cur: rs.append(cur)
                anchos = [fin_x(j) - (g['x0'] if j == 0 else g['xs']) for j in range(len(rs))]
            paso = round(g['paso'] * max(f_esc, 0.85))
            cabe = g['base'] + (len(rs) - 1) * paso + 0.2 * f.size <= lim_y + 2 and all(P.largo(x, f) <= an + 2 for x, an in zip(rs, anchos))
            if cabe: break
        if not cabe: avisos.append(f'NO CABE: «{g["es"][:50]}»')
        elif f_esc < 1: avisos.append(f'achicada {int(f_esc * 100)} %: «{g["es"][:35]}»')
        for j, x in enumerate(rs):
            xx = (g['x0'] + g['x1']) / 2 - P.largo(x, f) / 2 if centrado else (g['x0'] if j == 0 else g['xs'])
            P.pintar(d, xx, g['base'] + j * paso, x, f, g['col'] + (255,))
    nombre = ruta[:-4]
    atlas_es.TEX = os.path.join(T, 'extraido_r' if ruta.startswith('ui_en/') else 'extraido'); atlas_es.SAL = SAL
    atlas_es.guardar_dds(nombre, img)
    os.makedirs(REV, exist_ok=True)
    o = Image.open(origen(ruta)).convert('RGBA')
    v = Image.new('RGBA', (W * 2 + 12, H), (200, 0, 200, 255)); v.alpha_composite(o); v.alpha_composite(img, (W + 12, 0))
    v.convert('RGB').save(os.path.join(REV, nombre.split('/')[-1] + '.png'))
    return avisos


if __name__ == '__main__':
    for r in sys.argv[1:]:
        print(r, rehacer(r), flush=True)
