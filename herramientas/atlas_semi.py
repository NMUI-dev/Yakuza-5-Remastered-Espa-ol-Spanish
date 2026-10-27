# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Atlas de menús con ayudantes: el usuario pidió hacerlos TODOS con calidad («busca una IA
experta y la instalas»). Ayudantes locales y gratuitos:
  - gemma4:12b (Ollama, con visión): mira cada casilla y dice el texto, la familia de letra, cursiva/negrita, efecto
    (brillo, desenfoque) y si es un trozo de palabra; después revisa el antes/después de cada casilla.
  - LaMa (simple-lama-inpainting): borra el texto de las casillas con fondo opaco (botones) rellenando el fondo.
Pasos (cada uno guarda su resultado y se puede repetir):
  python herramientas/atlas_semi.py analizar [filtro]   casillas .sbb + gemma4 -> trabajo/imagenes/semi_celdas.json
  python herramientas/atlas_semi.py traducir            rótulos sin traducción del juego -> ayudantes gratuitos (API)
  python herramientas/atlas_semi.py dibujar [filtro]    -> trabajo/imagenes/es/... + revision_semi/*.png
  python herramientas/atlas_semi.py revisar [filtro]    gemma4 compara cada casilla -> trabajo/imagenes/semi_revision.json
Las texturas hechas a mano (atlas_es.json, textos_menu_es.py, manuales.txt) no se tocan.
"""
import base64, glob, io, json, os, re, sys, urllib.request
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es, sbb_rects
from ocr_imagenes import origen
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo', 'imagenes')
CELDAS = os.path.join(T, 'semi_celdas.json'); TR = os.path.join(T, 'atlas_auto_tr.json'); REV = os.path.join(T, 'semi_revision.json')
VLM = os.environ.get('VLM', 'gemma4:12b')

FUENTES = {('serif', 0, 0): 'times.ttf', ('serif', 1, 0): 'timesi.ttf', ('serif', 0, 1): 'timesbd.ttf', ('serif', 1, 1): 'timesbi.ttf',
           ('sans', 0, 0): 'arial.ttf', ('sans', 1, 0): 'ariali.ttf', ('sans', 0, 1): 'arialbd.ttf', ('sans', 1, 1): 'arialbi.ttf',
           ('display', 0, 0): 'impact.ttf', ('display', 0, 1): 'impact.ttf', ('display', 1, 0): 'arialbi.ttf', ('display', 1, 1): 'arialbi.ttf',
           ('brush', 0, 0): 'Knewave-Regular.ttf', ('brush', 1, 0): 'Knewave-Regular.ttf', ('brush', 0, 1): 'Knewave-Regular.ttf',
           ('brush', 1, 1): 'Knewave-Regular.ttf', ('script', 0, 0): 'CaveatBrush-Regular.ttf', ('script', 1, 0): 'CaveatBrush-Regular.ttf',
           ('script', 0, 1): 'CaveatBrush-Regular.ttf', ('script', 1, 1): 'CaveatBrush-Regular.ttf'}
SEGOE = {'arial.ttf': 'segoeui.ttf', 'ariali.ttf': 'segoeuii.ttf', 'arialbd.ttf': 'segoeuib.ttf', 'arialbi.ttf': 'segoeuiz.ttf'}


def tex_dir(nombre):
    return os.path.join(R, 'trabajo', 'extraido_r' if nombre.startswith('ui_en/') else 'extraido')


def manuales():
    import textos_menu_es
    m = set(json.load(open(os.path.join(T, 'atlas_es.json'), encoding='utf-8'))) | set(textos_menu_es.TRABAJOS)
    m = m | set(open(os.path.join(T, 'manuales.txt'), encoding='utf-8').read().split())
    return {x.lower() for x in m}   # (21-10) «Texlist_0001» y «texlist_0001» son la misma: comparar sin mayúsculas


def atlas_lista():
    ocr = json.load(open(os.path.join(T, 'ocr.json'), encoding='utf-8')); man = manuales()
    lista = [r[:-4] for r in sorted(ocr) if r.startswith(('ui_en/', '2dpar_ui_en/')) and r[:-4].lower() not in man]
    # (21-10) + PÁGINAS que la revisión (revisar_paginas.py, gemma4 + claude2) marcó como mal hechas
    rp = os.path.join(T, 'revision_paginas.json')
    if os.path.exists(rp):
        lista += [k[:-4] for k, v in sorted(json.load(open(rp, encoding='utf-8')).items()) if not v.get('ok', True) and k[:-4].lower() not in man
                  and '/ability/' not in k]   # tarjetas de habilidad: las lleva claude2 (habilidades_es.py)
    return lista


def sbbs_de(nombre):
    """Diseños que usan la textura: el del mismo pjd si existe; si no (texturas comunes), todos."""
    m = re.search(r'(pjd_[^/]+?)\.par/', nombre)
    if m:
        c = [os.path.join(R, 'trabajo', 'extraido_r', 'ui_en', 'surfboard', m.group(1) + '.sbb'),
             os.path.join(R, 'trabajo', 'extraido', '2dpar_ui_en', 'surfboard', m.group(1) + '.sbb')]
        c = [x for x in c if os.path.exists(x)]
        if c: return c
    return glob.glob(os.path.join(R, 'trabajo', 'extraido', '2dpar_ui_en', 'surfboard', '*.sbb'))


def celdas_tinta(a, sbbs):
    H, W = a.shape[:2]; rs = set()
    for f in sbbs: rs.update(sbb_rects.rects(f, W, H))
    con = []
    for r in rs:
        z = a[r[1]:r[3], r[0]:r[2], 3]
        if z.size and (z > 60).mean() > 0.01 and r[2] - r[0] >= 8 and r[3] - r[1] >= 6 and (r[2] - r[0]) * (r[3] - r[1]) < 0.5 * W * H:
            con.append(r)
    # (21-10) solo casillas que de verdad envuelven un rótulo: la tinta llena buena parte del alto y del ancho
    buenas = []
    for r in con:
        z = a[r[1]:r[3], r[0]:r[2], 3] > 60; f = np.where(z.any(1))[0]; cc = np.where(z.any(0))[0]
        if not len(f): continue
        ah, aw = (f[-1] - f[0] + 1) / (r[3] - r[1]), (cc[-1] - cc[0] + 1) / (r[2] - r[0])
        if ah >= 0.4 and aw >= 0.25 and (r[3] - r[1]) <= 120: buenas.append((ah * aw, r))
    # si dos casillas se pisan, gana la más ceñida
    buenas.sort(reverse=True); hojas = []
    for _, r in buenas:
        def iou(o):
            ix = max(0, min(r[2], o[2]) - max(r[0], o[0])); iy = max(0, min(r[3], o[3]) - max(r[1], o[1]))
            return ix * iy / min((r[2] - r[0]) * (r[3] - r[1]), (o[2] - o[0]) * (o[3] - o[1]))
        if not any(iou(o) > 0.3 for o in hojas): hojas.append(r)
    return sorted(hojas, key=lambda r: (r[1], r[0]))


def recorte_png(a, c, escala=None):
    x0, y0, x1, y1 = c; o = Image.fromarray(a[y0:y1, x0:x1]).convert('RGBA')
    b = Image.new('RGBA', o.size, (0, 0, 0, 255)); b.alpha_composite(o); b = b.convert('RGB')
    k = escala or max(1, min(4, 96 // max(1, b.height)))
    b = b.resize((b.width * k, b.height * k), Image.LANCZOS)
    buf = io.BytesIO(); b.save(buf, 'PNG'); return base64.b64encode(buf.getvalue()).decode()


def vlm(prompt, imagenes):
    q = urllib.request.Request('http://localhost:11434/api/chat', headers={'Content-Type': 'application/json'},
        data=json.dumps({'model': VLM, 'stream': False, 'format': 'json', 'think': False, 'options': {'temperature': 0},
                         'messages': [{'role': 'user', 'content': prompt, 'images': imagenes}]}).encode())
    try: return json.loads(json.load(urllib.request.urlopen(q, timeout=600))['message']['content'])
    except Exception as e: return {'error': str(e)[:200]}


DESCRIBIR = ('This is one sprite cut from a video game UI texture atlas (shown on black). Answer ONLY JSON: '
             '{"text": "exact English text, or empty if none", "is_text": true/false, '
             '"partial": true if the text is a fragment cut from a longer word or the letters are split/cropped, '
             '"family": "serif|sans|display|brush|script", "italic": true/false, "bold": true/false, '
             '"effect": "none|glow|outline|shadow|blurred"}')


def analizar(filtro=''):
    cel = json.load(open(CELDAS, encoding='utf-8')) if os.path.exists(CELDAS) else {}
    for nombre in atlas_lista():
        if filtro not in nombre or nombre in cel: continue
        a = np.asarray(Image.open(os.path.join(tex_dir(nombre), nombre + '.dds')).convert('RGBA'))
        res = []
        for c in celdas_tinta(a, sbbs_de(nombre)):
            d = vlm(DESCRIBIR, [recorte_png(a, c)])
            z = a[c[1]:c[3], c[0]:c[2], 3]
            d.update(caja=list(c), opaco=bool((z > 200).mean() > 0.75))
            res.append(d)
        cel[nombre] = res
        json.dump(cel, open(CELDAS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(nombre, len(res), 'casillas', sum(1 for d in res if d.get('is_text') and not d.get('partial')), 'con texto', flush=True)


def traducibles(d):
    t = (d.get('text') or '').strip()
    return d.get('is_text') and not d.get('partial') and re.search(r'[A-Za-z]{2,}', t) and not re.fullmatch(r'[\d\W_]*[A-Za-z]?[\d\W_]*', t)


def del_juego():
    from aplicar import traducciones
    gen, _ = traducciones()
    return {k.lower().strip(): v for k, v in gen.items()}


def traduccion(t, juego, tr):
    return juego.get(t.lower().strip()) or tr.get(t)


def traducir():
    sys.argv = [sys.argv[0], 'semi']
    import traductor_gemini as TG
    cel = json.load(open(CELDAS, encoding='utf-8')); juego = del_juego()
    tr = json.load(open(TR, encoding='utf-8')) if os.path.exists(TR) else {}
    falta = sorted({d['text'].strip() for v in cel.values() for d in v if traducibles(d) and not traduccion(d['text'].strip(), juego, tr)})
    TG.log(f'{len(falta)} rótulos sin traducción')
    encargo = ("Traduce al español neutro latinoamericano estos rótulos de menús y minijuegos de Yakuza 5 (van dibujados en "
               "una imagen: cortos, del largo del inglés o poco más; respeta MAYÚSCULAS). Nombres propios, marcas y títulos de "
               "canciones se dejan igual. Devuelve SOLO JSON {\"t\": {\"id\": \"traducción\"}}.\n")
    for i in range(0, len(falta), 80):
        trozo = {str(n): t for n, t in enumerate(falta[i:i + 80])}
        r, m = TG.pedir(encargo + json.dumps(trozo, ensure_ascii=False, indent=0))
        if r is None: continue
        t = r.get('t', r) if isinstance(r, dict) else {}
        for n, en in enumerate(falta[i:i + 80]):
            if isinstance(t.get(str(n)), str) and t[str(n)].strip(): tr[en] = t[str(n)].strip()
        json.dump(tr, open(TR, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        TG.log(f'{min(i + 80, len(falta))}/{len(falta)} ({m})')


def estilo(en, es):
    if en.isupper() and len(en) > 1: return es.upper()
    return es[:1].upper() + es[1:] if en[:1].isupper() else es


def fuente_de(d, base):
    fam = d.get('family') if d.get('family') in ('serif', 'sans', 'display', 'brush', 'script') else 'sans'
    f = FUENTES[(fam, int(bool(d.get('italic'))), int(bool(d.get('bold'))))]
    if f in SEGOE: f = SEGOE[f]       # (21-10) la Arial de este Windows tumba a FreeType: siempre Segoe UI
    return f


def alineacion(a, c):
    x0, y0, x1, y1 = c; cols = np.where((a[y0:y1, x0:x1, 3] > 60).any(0))[0]
    if not len(cols): return 'centro'
    izq, der = cols[0], (x1 - x0) - 1 - cols[-1]
    if abs(izq - der) <= max(3, 0.15 * (x1 - x0)): return 'centro'
    return 'izq' if izq < der else 'der'


_LAMA = None
def borrar_opaco(rgba, c):
    """Casilla con fondo opaco: máscara = píxeles lejos del color del borde; LaMa rellena el fondo."""
    global _LAMA
    if _LAMA is None:
        from simple_lama_inpainting import SimpleLama
        _LAMA = SimpleLama()
    import cv2
    x0, y0, x1, y1 = c; z = rgba[y0:y1, x0:x1, :3].astype(np.int16)
    borde = np.concatenate([z[0], z[-1], z[:, 0], z[:, -1]]); fondo = np.median(borde, 0)
    m = (np.abs(z - fondo).sum(2) > 90).astype(np.uint8)
    m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=2)
    pad = 8; X0, Y0 = max(0, x0 - pad), max(0, y0 - pad); X1, Y1 = min(rgba.shape[1], x1 + pad), min(rgba.shape[0], y1 + pad)
    full = np.zeros(rgba.shape[:2], np.uint8); full[y0:y1, x0:x1] = m
    trozo = Image.fromarray(rgba[Y0:Y1, X0:X1, :3]); mt = Image.fromarray(full[Y0:Y1, X0:X1] * 255)
    lleno = np.asarray(_LAMA(trozo, mt).resize(trozo.size))
    tinta = z[m[..., None].repeat(3, 2).astype(bool)].reshape(-1, 3) if m.any() else np.array([[255, 255, 255]])
    color = tuple(int(v) for v in np.median(tinta, 0))
    out = rgba.copy(); out[y0:y1, x0:x1, :3] = lleno[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0]
    filas = np.where(m.any(1))[0]; cols = np.where(m.any(0))[0]
    caja_tinta = (x0 + cols[0], y0 + filas[0], x0 + cols[-1] + 1, y0 + filas[-1] + 1) if len(filas) else c
    return out, color, caja_tinta


def dibujar(filtro=''):
    cel = json.load(open(CELDAS, encoding='utf-8')); juego = del_juego()
    tr = json.load(open(TR, encoding='utf-8')) if os.path.exists(TR) else {}
    fa = json.load(open(os.path.join(T, 'atlas_fuentes.json'), encoding='utf-8'))
    rev = os.path.join(T, 'revision_semi'); os.makedirs(rev, exist_ok=True); n = 0
    for nombre, ds in cel.items():
        if filtro not in nombre: continue
        atlas_es.TEX = tex_dir(nombre)
        orig = Image.open(os.path.join(atlas_es.TEX, nombre + '.dds')).convert('RGBA'); a = np.asarray(orig)
        items, opacos = [], []
        for d in ds:
            if not traducibles(d): continue
            en = ' '.join(d['text'].split()); es = traduccion(d['text'].strip(), juego, tr)
            if not es or es.strip().lower() == en.lower(): continue
            es = estilo(en, es.replace('\n', ' ')); c = d['caja']
            f = fuente_de(d, fa.get(nombre, 'arial.ttf'))
            if d.get('opaco'): opacos.append((c, en, es, f)); continue
            ef = {'glow': 'brillo', 'blurred': 'borroso'}.get(d.get('effect'), 'nada')
            it = {'caja': c, 'en': en, 'es': es, 'fuente': f, 'alin': alineacion(a, c), 'ancho_max': c[2] - c[0] - 4, 'efecto': ef}
            if ef == 'borroso':
                z = a[c[1]:c[3], c[0]:c[2], 3] > 15; fl = np.where(z.any(1))[0]
                it.update(alto=int(max(6, (fl[-1] - fl[0] + 1) * 0.7)) if len(fl) else 10, radio=3)
            items.append(it)
        if not items and not opacos: continue
        nuevo = orig
        if items: _, nuevo = atlas_es.traducir(nombre, {'fuente': items[0]['fuente'], 'margen': 0, 'mediana': False, 'items': items})
        if opacos:
            b = np.asarray(nuevo).copy()
            for c, en, es, f in opacos:
                b, color, ct = borrar_opaco(b, c)
                alto = ct[3] - ct[1]; tam = atlas_es.calibrar(f, en, alto)
                m, sup = atlas_es.mascara(f, es, tam, en, c[2] - c[0] - 4)
                px = int(round((ct[0] + ct[2]) / 2 - m.width / 2)); px = max(c[0], min(px, c[2] - m.width))
                capa = Image.new('L', orig.size, 0); capa.paste(m, (px, ct[1] - sup))
                rec = np.zeros(capa.size[::-1], np.uint8); rec[c[1]:c[3], c[0]:c[2]] = 1
                capa = Image.fromarray(np.asarray(capa) * rec)
                im = Image.fromarray(b); col = Image.new('RGBA', orig.size, color + (0,)); col.putalpha(capa); im.alpha_composite(col)
                b = np.asarray(im).copy()
            nuevo = Image.fromarray(b)
        atlas_es.guardar_dds(nombre, nuevo)
        W, H = orig.size; v = Image.new('RGBA', (W * 2, H), (40, 90, 40, 255))
        v.alpha_composite(orig, (0, 0)); v.alpha_composite(nuevo, (W, 0))
        v.convert('RGB').save(os.path.join(rev, nombre.replace('/', '__') + '.png')); n += 1
        print('ok', nombre, len(items), '+', len(opacos), 'opacas', flush=True)
    print('dibujados', n)


REVISAR = ('Left: original English sprite from a game menu. Right: the same sprite with Spanish text "{es}". Answer ONLY JSON '
           '{{"ok": true/false, "problem": "none|cut_off|overlap|unreadable|leftover_english|wrong_style|too_small|other"}}. '
           'ok=false if the Spanish text is cut off, overlaps something, is hard to read, leaves English letters visible, '
           'or looks very different in style/size from the original.')


def revisar(filtro=''):
    cel = json.load(open(CELDAS, encoding='utf-8')); juego = del_juego()
    tr = json.load(open(TR, encoding='utf-8')) if os.path.exists(TR) else {}
    rv = json.load(open(REV, encoding='utf-8')) if os.path.exists(REV) else {}
    for nombre, ds in cel.items():
        if filtro not in nombre: continue
        nuevo_p = os.path.join(atlas_es.SAL, nombre + '.dds')
        if not os.path.exists(nuevo_p): continue
        a = np.asarray(Image.open(os.path.join(tex_dir(nombre), nombre + '.dds')).convert('RGBA'))
        b = np.asarray(Image.open(nuevo_p).convert('RGBA')); malos = []
        for d in ds:
            if not traducibles(d): continue
            es = traduccion(d['text'].strip(), juego, tr)
            if not es: continue
            x0, y0, x1, y1 = d['caja']; pad = 6
            c = [max(0, x0 - pad), max(0, y0 - pad), min(a.shape[1], x1 + pad), min(a.shape[0], y1 + pad)]
            r = vlm(REVISAR.format(es=es), [recorte_png(a, c), recorte_png(b, c)])
            if not r.get('ok', True): malos.append({'caja': d['caja'], 'en': d['text'], 'es': es, 'problema': r.get('problem')})
        rv[nombre] = malos
        json.dump(rv, open(REV, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(nombre, 'marcadas', len(malos), flush=True)


if __name__ == '__main__':
    arg = sys.argv[2] if len(sys.argv) > 2 else ''
    {'analizar': lambda: analizar(arg), 'traducir': traducir, 'dibujar': lambda: dibujar(arg), 'revisar': lambda: revisar(arg)}[sys.argv[1]]()
