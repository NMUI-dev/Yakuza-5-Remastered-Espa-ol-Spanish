# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Atlas de menús (ui_en, 2dpar_ui_en): palabras sueltas sobre fondo transparente que el
juego recorta una a una. El método de páginas (imagenes_es.py) las juntaba en párrafos y las dejaba feas; aquí:
  1. cada renglón del OCR se parte en «piezas» por los huecos de tinta (cada pieza = un recorte del juego) y cada pieza
     se vuelve a leer con OCR por separado;
  2. se elige la letra que más se parece a la original (se dibuja el inglés con cada candidata y se compara la tinta);
  3. la traducción sale del juego (misma frase, sin mirar mayúsculas) o, si no está, de los ayudantes gratuitos
     (corta, del largo del inglés) -> trabajo/imagenes/atlas_auto_tr.json;
  4. atlas_es.traducir dibuja cada pieza DENTRO de su caja (mismo alto, se estrecha si no cabe, color y brillo medidos).
Piezas con fondo opaco, palabras partidas («ABI|LITY») o sin letras se dejan como están (se apuntan en avisos).
Salida: trabajo/imagenes/es/... (.dds) + trabajo/imagenes/revision_atlas/*.png  ;  spec en trabajo/imagenes/atlas_auto.json
  python herramientas/atlas_auto.py spec        (OCR por pieza + letra: sin conexión)
  python herramientas/atlas_auto.py traducir    (piezas sin traducción del juego -> ayudantes gratuitos)
  python herramientas/atlas_auto.py dibujar [filtro]
"""
import json, os, re, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
from ocr_imagenes import origen
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo', 'imagenes')
SPEC = os.path.join(T, 'atlas_auto.json'); TR = os.path.join(T, 'atlas_auto_tr.json')
CANDIDATAS = ['times.ttf', 'timesbd.ttf', 'timesi.ttf', 'georgia.ttf', 'georgiab.ttf', 'georgiai.ttf', 'georgiaz.ttf',
              'segoeui.ttf', 'segoeuib.ttf', 'segoeuii.ttf', 'arial.ttf', 'arialbd.ttf', 'ariali.ttf', 'arialbi.ttf',
              'impact.ttf', 'trebucbd.ttf', 'verdanab.ttf', 'tahomabd.ttf', 'Oswald.ttf', 'Knewave-Regular.ttf']


def es_atlas(ruta):
    return ruta.startswith(('ui_en/', '2dpar_ui_en/'))


def piezas(a, caja):
    """Parte el renglón del OCR por columnas vacías anchas. Devuelve cajas ceñidas a la tinta (con el halo)."""
    x0, y0, x1, y1 = caja; H, W = a.shape[:2]
    x0, y0, x1, y1 = max(0, x0 - 3), max(0, y0 - 3), min(W, x1 + 3), min(H, y1 + 3)
    tinta = a[y0:y1, x0:x1, 3] > 60
    if not tinta.any(): return []
    filas = np.where(tinta.any(1))[0]; alto = filas[-1] - filas[0] + 1
    col = tinta.any(0); hueco_min = max(6, int(alto * 0.7)); res = []; ini = None; vacio = 0
    for i, c in enumerate(list(col) + [False] * (hueco_min + 1)):
        if c:
            if ini is None: ini = i
            vacio = 0; fin = i
        elif ini is not None:
            vacio += 1
            if vacio >= hueco_min: res.append((ini, fin)); ini = None
    out = []
    for i0, i1 in res:
        sub = tinta[:, i0:i1 + 1]; f = np.where(sub.any(1))[0]
        out.append([int(x0 + i0), int(y0 + f[0]), int(x0 + i1 + 1), int(y0 + f[-1] + 1)])
    return out


def leer_pieza(ocr, a, c):
    x0, y0, x1, y1 = c; m = 4
    rec = Image.fromarray(a[max(0, y0 - m):y1 + m, max(0, x0 - m):x1 + m])
    mejor = ''
    for fondo in ((0, 0, 0, 255), (255, 255, 255, 255)):
        b = Image.new('RGBA', rec.size, fondo); b.alpha_composite(rec)
        b = b.convert('RGB').resize((b.width * 2, b.height * 2), Image.LANCZOS)
        r, _ = ocr(np.asarray(b))
        t = ' '.join(x[1] for x in (r or []))
        if len(t) > len(mejor): mejor = t
    return mejor.strip()


def parecido(nf, en, mascara_orig):
    """IoU entre la tinta original y el inglés dibujado con la fuente nf, escalado a la misma caja."""
    h, w = mascara_orig.shape
    try: f = atlas_es.fuente(nf, 64)
    except Exception: return 0
    bb = f.getbbox(en)
    im = Image.new('L', (bb[2] - bb[0] + 2, bb[3] - bb[1] + 2), 0)
    ImageDraw.Draw(im).text((1 - bb[0], 1 - bb[1]), en, font=f, fill=255)
    im = np.asarray(im.resize((w, h), Image.LANCZOS)) > 128
    return (im & mascara_orig).sum() / max(1, (im | mascara_orig).sum())


def spec():
    from rapidocr_onnxruntime import RapidOCR
    ocr_m = RapidOCR()
    ocr = json.load(open(os.path.join(T, 'ocr.json'), encoding='utf-8'))
    manuales = set(json.load(open(os.path.join(T, 'atlas_es.json'), encoding='utf-8')))
    import textos_menu_es; manuales |= set(textos_menu_es.TRABAJOS)
    sp = {}; avisos = []
    for ruta, lineas in sorted(ocr.items()):
        if not es_atlas(ruta) or ruta[:-4] in manuales: continue
        a = np.asarray(Image.open(origen(ruta)).convert('RGBA'))
        items = []
        for l in lineas:
            if not re.search(r'[A-Za-z]{2,}', l[4]): continue
            ps = piezas(a, l[:4])
            for c in ps:
                t = l[4] if len(ps) == 1 else leer_pieza(ocr_m, a, c)
                if not re.search(r'[A-Za-z]{2,}', t): continue
                x0, y0, x1, y1 = c; zona = a[y0:y1, x0:x1, 3]
                if (zona > 200).mean() > 0.75: avisos.append(f'{ruta}: fondo opaco, se deja: {t}'); continue
                m = zona > 128; mejores = sorted(((parecido(nf, t, m), nf) for nf in CANDIDATAS), reverse=True)
                alto = int(np.where(m.any(1))[0][-1] - np.where(m.any(1))[0][0] + 1) if m.any() else y1 - y0
                op = (zona > 200).sum(); medio = ((zona > 15) & (zona <= 200)).sum()
                efecto = 'borroso' if op < 0.15 * max(1, op + medio) else 'auto'
                items.append({'caja': [x0 - 1, y0 - 1, x1 + 1, y1 + 1], 'en': t, 'fuente': mejores[0][1],
                              'parecido': round(mejores[0][0], 2), 'efecto': efecto, 'alto': alto})
        if items: sp[ruta[:-4]] = {'fuente': items[0]['fuente'], 'ceñido': True, 'margen': 1, 'mediana': False, 'items': items}
        print(ruta, len(items), flush=True)
    json.dump(sp, open(SPEC, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=int)
    open(os.path.join(T, 'avisos_atlas.txt'), 'w', encoding='utf-8').write('\n'.join(avisos))
    print('atlas', len(sp), 'piezas', sum(len(s['items']) for s in sp.values()))


def puntuar(nf, en, m):
    """Parecido de la letra nf con la tinta m: forma (IoU estirado a la caja) y, sobre todo, la proporción ancho/alto
    natural de la palabra (cada letra tiene la suya: serif, sans, estrecha...)."""
    import math
    h, w = m.shape
    try: f = atlas_es.fuente(nf, 64)
    except Exception: return -9
    bb = f.getbbox(en); r = ((bb[2] - bb[0]) / max(1, bb[3] - bb[1])) / max(1e-3, w / max(1, h))
    return parecido(nf, en, m) - 0.8 * abs(math.log(max(1e-3, r)))


def fuentes():
    """(21-10) Segunda pasada sobre la spec: una letra por atlas (la de más puntos sumando todas sus piezas); una pieza
    solo usa otra si le encaja claramente mejor. Las letras de adorno (Impact, Knewave) solo si ganan con margen."""
    sp = json.load(open(SPEC, encoding='utf-8')); ADORNO = {'impact.ttf', 'Knewave-Regular.ttf'}
    for nombre, s in sp.items():
        atlas_es.TEX = os.path.join(R, 'trabajo', 'extraido_r' if nombre.startswith('ui_en/') else 'extraido')
        a = np.asarray(Image.open(os.path.join(atlas_es.TEX, nombre + '.dds')).convert('RGBA'))
        pts = []
        for it in s['items']:
            x0, y0, x1, y1 = it['caja']; m = a[y0 + 1:y1 - 1, x0 + 1:x1 - 1, 3] > 128
            pts.append({nf: puntuar(nf, it['en'], m) - (0.12 if nf in ADORNO else 0) for nf in CANDIDATAS})
        total = {nf: sum(p[nf] for p in pts) for nf in CANDIDATAS}; base = max(total, key=total.get)
        s['fuente'] = base
        for it, p in zip(s['items'], pts):
            mejor = max(p, key=p.get)
            it['fuente'] = mejor if p[mejor] > p[base] + 0.15 else base
        print(nombre, base, flush=True)
    json.dump(sp, open(SPEC, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=int)


FAMILIAS = {'times': ['times.ttf', 'timesi.ttf', 'timesbd.ttf', 'timesbi.ttf'],
            'georgia': ['georgia.ttf', 'georgiai.ttf', 'georgiab.ttf', 'georgiaz.ttf'],
            'segoeui': ['segoeui.ttf', 'segoeuii.ttf', 'segoeuib.ttf', 'segoeuiz.ttf'],
            'arial': ['arial.ttf', 'ariali.ttf', 'arialbd.ttf', 'arialbi.ttf']}
_RECTS = {}

def rects_juego(W, H):
    """Todas las cajas que los diseños .sbb del juego recortan en una textura de W x H (caché por tamaño)."""
    if (W, H) not in _RECTS:
        import glob, sbb_rects
        rs = set()
        for f in glob.glob(os.path.join(R, 'trabajo', 'extraido', '2dpar_ui_en', 'surfboard', '*.sbb')) +                  glob.glob(os.path.join(R, 'trabajo', 'extraido_r', 'ui_en', 'surfboard', '**', '*.sbb'), recursive=True):
            rs.update(sbb_rects.rects(f, W, H))
        _RECTS[(W, H)] = sorted(rs)
    return _RECTS[(W, H)]


def afinar():
    """(21-10) Tras ver el menú de pausa mal hecho: cada pieza a la CASILLA EXACTA del juego que la contiene (rejilla del
    .sbb: mismo alto para todas las opciones de una columna, nada se corta), variante de la letra elegida para el atlas
    (normal/cursiva/negrita) según la tinta, y las copias desenfocadas (brillo de la opción elegida) también en español."""
    sp = json.load(open(SPEC, encoding='utf-8')); fuentes_atlas = json.load(open(os.path.join(T, 'atlas_fuentes.json'), encoding='utf-8'))
    for nombre, s in sp.items():
        atlas_es.TEX = os.path.join(R, 'trabajo', 'extraido_r' if nombre.startswith('ui_en/') else 'extraido')
        a = np.asarray(Image.open(os.path.join(atlas_es.TEX, nombre + '.dds')).convert('RGBA')); H, W = a.shape[:2]
        base = fuentes_atlas.get(nombre, s['fuente']); fam = next((v for k, v in FAMILIAS.items() if base.startswith(k)), [base])
        cands = rects_juego(W, H); usados = []
        for it in s['items']:
            x0, y0, x1, y1 = it.get('tinta', it['caja']); it['tinta'] = [x0, y0, x1, y1]
            m = a[y0 + 1:y1 - 1, x0 + 1:x1 - 1, 3] > 128
            if m.size and m.any():
                it['fuente'] = max(fam, key=lambda nf: puntuar(nf, it['en'], m))
            h, w = y1 - y0, x1 - x0
            dentro = [r for r in cands if r[0] <= x0 + 1 and r[1] <= y0 + 1 and r[2] >= x1 - 1 and r[3] >= y1 - 1
                      and r[3] - r[1] <= 2.2 * h + 4 and r[2] - r[0] <= max(6 * w, 64)]
            if dentro:
                r = min(dentro, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
                if not any(r == u for u in usados): it['caja'] = list(r); it.pop('alto', None); usados.append(r)
        # copias desenfocadas: casilla del mismo ancho y x que una pieza nítida, con tinta casi toda a medio alfa
        nuevos = []
        for r in cands:
            if r in usados: continue
            z = a[r[1]:r[3], r[0]:r[2], 3]
            op = (z > 200).sum(); medio = ((z > 15) & (z <= 200)).sum()
            if medio < 40 or op > 0.15 * (op + medio): continue
            gemelas = [it for it in s['items'] if it['caja'][0] == r[0] and it['caja'][2] == r[2] and it['efecto'] != 'borroso'
                       and abs(it['caja'][1] - r[1]) <= 3 * (r[3] - r[1])]
            if gemelas:
                g = min(gemelas, key=lambda it: abs(it['caja'][1] - r[1]))
                x0, y0, x1, y1 = g['tinta']
                nuevos.append(dict(g, caja=list(r), efecto='borroso', alto=int(y1 - y0)))
        s['items'] += nuevos
        s['fuente'] = base; s['mediana'] = True; s['ceñido'] = True
        print(nombre, base, len(usados), 'casillas', len(nuevos), 'desenfocadas', flush=True)
    json.dump(sp, open(SPEC, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=int)


def del_juego():
    from aplicar import traducciones
    gen, _ = traducciones()
    return {k.lower().strip(): v for k, v in gen.items()}


def estilo(en, es):
    """Mayúsculas: solo si el inglés va todo en mayúsculas; si no, como en español (no «Lista De Misiones»)."""
    if en.isupper() and len(en) > 1: return es.upper()
    return es[:1].upper() + es[1:] if en[:1].isupper() else es


def traducir():
    sys.argv = [sys.argv[0], 'atlas']
    import traductor_gemini as TG
    sp = json.load(open(SPEC, encoding='utf-8')); juego = del_juego()
    tr = json.load(open(TR, encoding='utf-8')) if os.path.exists(TR) else {}
    falta = sorted({it['en'] for s in sp.values() for it in s['items'] if it['en'].lower().strip() not in juego and it['en'] not in tr})
    TG.log(f'{len(falta)} rótulos sin traducción del juego')
    encargo = ("Traduce al español neutro latinoamericano estos rótulos de menú de Yakuza 5 (van dibujados en una imagen: "
               "cortos, del largo del inglés o poco más; respeta mayúsculas). Si es un nombre propio, una marca o un trozo "
               "de palabra que no se entiende solo, devuélvelo igual. Devuelve SOLO JSON {\"t\": {\"id\": \"traducción\"}}.\n")
    for i in range(0, len(falta), 80):
        trozo = {str(n): t for n, t in enumerate(falta[i:i + 80])}
        r, m = TG.pedir(encargo + json.dumps(trozo, ensure_ascii=False, indent=0))
        if r is None: continue
        t = r.get('t', r) if isinstance(r, dict) else {}
        for n, en in enumerate(falta[i:i + 80]):
            if isinstance(t.get(str(n)), str) and t[str(n)].strip(): tr[en] = t[str(n)].strip()
        json.dump(tr, open(TR, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        TG.log(f'{min(i + 80, len(falta))}/{len(falta)} ({m})')


def dibujar(filtro=''):
    sp = json.load(open(SPEC, encoding='utf-8')); juego = del_juego()
    tr = json.load(open(TR, encoding='utf-8')) if os.path.exists(TR) else {}
    rev = os.path.join(T, 'revision_atlas'); os.makedirs(rev, exist_ok=True); n = 0
    for nombre, s in sp.items():
        if filtro not in nombre: continue
        items = []
        for it in s['items']:
            es = juego.get(it['en'].lower().strip()) or tr.get(it['en'])
            if not es or es.strip() == it['en'].strip(): continue
            items.append(dict(it, es=estilo(it['en'], es.replace('\n', ' '))))
        if not items: continue
        atlas_es.TEX = os.path.join(R, 'trabajo', 'extraido_r' if nombre.startswith('ui_en/') else 'extraido')
        orig, nuevo = atlas_es.traducir(nombre, dict(s, items=items))
        atlas_es.guardar_dds(nombre, nuevo)
        W, H = orig.size; v = Image.new('RGBA', (W * 2, H), (40, 90, 40, 255))
        v.alpha_composite(orig, (0, 0)); v.alpha_composite(nuevo, (W, 0))
        v.convert('RGB').save(os.path.join(rev, nombre.replace('/', '__') + '.png')); n += 1
    print('dibujados', n)


if __name__ == '__main__':
    {'spec': spec, 'fuentes': fuentes, 'afinar': afinar, 'traducir': traducir, 'dibujar': lambda: dibujar(sys.argv[2] if len(sys.argv) > 2 else '')}[sys.argv[1]]()
