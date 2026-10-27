# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) KIT DE ATLAS (ver trabajo/imagenes/GUIA_ATLAS.md).
  python herramientas/atlas_probar.py reclamar <quien> reserva el siguiente atlas libre y dice su id
  python herramientas/atlas_probar.py probar <id>    dibuja el borrador -> atlas_pruebas/<id>.png (antes | después,
                                                     ampliado) + <id>_casillas.png (cada rótulo de cerca, numerado)
                                                     y gemma4 marca problemas -> atlas_pruebas/<id>_gemma.json
  python herramientas/atlas_probar.py aceptar <id>   copia el borrador a atlas_hechos/ (lo da por bueno quien lo hizo)
  python herramientas/atlas_probar.py aplicar        dibuja TODOS los atlas_hechos -> trabajo/imagenes/es/*.dds
  python herramientas/atlas_probar.py estado         cuántos hay hechos, verificados, pendientes
La verificación final la hace claude2: atlas_verificados.txt (un id por línea). Solo se APLICAN al juego los verificados.
"""
import json, os, shutil, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es, atlas_semi as S
from atlas_borrador import BORR, HECHOS, ident, pendientes
T = S.T; PRU = os.path.join(T, 'atlas_pruebas'); VERIF = os.path.join(T, 'atlas_verificados.txt')


def cargar(i):
    for d in (HECHOS, BORR):
        p = os.path.join(d, i + '.json')
        if os.path.exists(p): return json.load(open(p, encoding='utf-8')), p
    sys.exit(f'no existe el borrador {i} (atlas_borrador.py hacer {i})')


def dibujar(spec):
    n = spec['textura']; atlas_es.TEX = S.tex_dir(n)
    W, H = Image.open(os.path.join(atlas_es.TEX, n + '.dds')).size
    for k, it in enumerate(spec['items']):   # (21-10, aviso de fableC2b) caja fuera de la textura: aviso claro
        x0, y0, x1, y1 = it['caja']
        if not (0 <= x0 < x1 <= W and 0 <= y0 < y1 <= H): sys.exit(f'rótulo {k} ({it["en"]!r}): caja {it["caja"]} fuera de la textura {W}x{H} (las _casillas.png pueden ir ampliadas)')
    items = [it for it in spec['items'] if it.get('es') and it['es'].strip() != it['en'].strip() and not it.get('dejar')]
    sp = dict(spec, items=json.loads(json.dumps(items)))
    if not items:
        o = Image.open(os.path.join(atlas_es.TEX, n + '.dds')).convert('RGBA'); return o, o, items
    o, nv = atlas_es.traducir(n, sp)
    return o, nv, items


def probar(i):
    spec, _ = cargar(i); o, nv, items = dibujar(spec); os.makedirs(PRU, exist_ok=True)
    W, H = o.size; k = max(1, min(3, 1400 // (2 * W)))
    v = Image.new('RGBA', (W * 2 + 8, H), (40, 90, 40, 255)); v.alpha_composite(o, (0, 0)); v.alpha_composite(nv, (W + 8, 0))
    v = v.resize((v.width * k, v.height * k), Image.LANCZOS); v.convert('RGB').save(os.path.join(PRU, i + '.png'))
    # cada rótulo de cerca: original | español
    a, b = np.asarray(o), np.asarray(nv); filas = []
    for j, it in enumerate(items):
        x0, y0, x1, y1 = it['caja']; p = 4; c = [max(0, x0 - p), max(0, y0 - p), min(W, x1 + p), min(H, y1 + p)]
        ca = Image.fromarray(a[c[1]:c[3], c[0]:c[2]]); cb = Image.fromarray(b[c[1]:c[3], c[0]:c[2]])
        z = max(1, min(4, 60 // max(1, ca.height)))
        fila = Image.new('RGBA', (ca.width * 2 * z + 60, ca.height * z), (40, 90, 40, 255))
        fila.alpha_composite(ca.resize((ca.width * z, ca.height * z)), (40, 0)); fila.alpha_composite(cb.resize((cb.width * z, cb.height * z)), (60 + ca.width * z, 0))
        ImageDraw.Draw(fila).text((2, 2), str(spec['items'].index(it)), fill=(255, 255, 0, 255)); filas.append(fila)
    if filas:
        hoja = Image.new('RGB', (max(f.width for f in filas), sum(f.height + 4 for f in filas)), (20, 20, 20)); y = 0
        for f in filas: hoja.paste(f.convert('RGB'), (0, y)); y += f.height + 4
        hoja.save(os.path.join(PRU, i + '_casillas.png'))
    marcas = []
    for it in items:
        x0, y0, x1, y1 = it['caja']; p = 6; c = [max(0, x0 - p), max(0, y0 - p), min(W, x1 + p), min(H, y1 + p)]
        r = S.vlm(S.REVISAR.format(es=it['es']), [S.recorte_png(a, c), S.recorte_png(b, c)])
        if not r.get('ok', True): marcas.append({'n': spec['items'].index(it), 'es': it['es'], 'problema': r.get('problem')})
    json.dump(marcas, open(os.path.join(PRU, i + '_gemma.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(i, len(items), 'rótulos dibujados; gemma4 marca', len(marcas), [m['n'] for m in marcas])


RECL = os.path.join(T, 'atlas_reclamados')

def reclamar(quien):
    """Reserva el siguiente atlas pendiente (mkdir atómico) e imprime su id; nada si no quedan."""
    os.makedirs(RECL, exist_ok=True)
    import hashlib
    md5 = lambda n: hashlib.md5(open(os.path.join(S.tex_dir(n), n + '.dds'), 'rb').read()).hexdigest()
    hechos = {}
    for f in os.listdir(HECHOS) if os.path.isdir(HECHOS) else []:
        try: hechos.setdefault(md5(json.load(open(os.path.join(HECHOS, f), encoding='utf-8'))['textura']), f)
        except Exception: pass
    for n in pendientes():
        i = ident(n)
        # (21-10) la MISMA textura en otro .par: se copia el atlas ya hecho (misma traducción, sin gastar ayudantes)
        h = hechos.get(md5(n))
        if h:
            d = json.load(open(os.path.join(HECHOS, h), encoding='utf-8')); d['textura'] = n; d['copiado_de'] = h[:-5]
            json.dump(d, open(os.path.join(HECHOS, i + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            if h[:-5] in verificados(): open(VERIF, 'a', encoding='utf-8').write(i + chr(10))
            continue
        try: os.mkdir(os.path.join(RECL, i))
        except FileExistsError: continue
        open(os.path.join(RECL, i, 'quien'), 'w', encoding='utf-8').write(quien); print(i); return


def aceptar(i):
    # (21-10) no pisar un atlas ya VERIFICADO por claude2 (sus correcciones se perderían): hace falta --forzar
    if i in verificados() and '--forzar' not in sys.argv and os.path.exists(os.path.join(HECHOS, i + '.json')):
        sys.exit(f'{i} ya está VERIFICADO: no se acepta encima (si de verdad hay que rehacerlo, avisa a claude2)')
    _, p = cargar(i); os.makedirs(HECHOS, exist_ok=True)
    if os.path.dirname(p) != HECHOS: shutil.copy(p, os.path.join(HECHOS, i + '.json'))
    print('aceptado', i)


def verificados():
    return set(open(VERIF, encoding='utf-8').read().split()) if os.path.exists(VERIF) else set()


def aplicar():
    v = verificados(); n = 0
    for f in sorted(os.listdir(HECHOS)):
        i = f[:-5]
        if i not in v: continue
        spec = json.load(open(os.path.join(HECHOS, f), encoding='utf-8'))
        # (21-10) atlas con todo en «dejar» (la página la hace otro programa): NO escribir, pisaría esa versión
        if not any(it.get('es') and it.get('es') != it.get('en') and not it.get('dejar') for it in spec['items']): continue
        o, nv, items = dibujar(spec)
        if items: atlas_es.guardar_dds(spec['textura'], nv); n += 1
    print('aplicados', n, 'atlas verificados')


def estado():
    h = {f[:-5] for f in os.listdir(HECHOS)} if os.path.isdir(HECHOS) else set(); v = verificados()
    print('pendientes', len(pendientes()), '| hechos', len(h), '| verificados', len(h & v), '| hechos sin verificar', len(h - v))


if __name__ == '__main__':
    o = sys.argv[1]
    {'reclamar': lambda: reclamar(sys.argv[2]), 'probar': lambda: probar(sys.argv[2]), 'aceptar': lambda: aceptar(sys.argv[2]), 'aplicar': aplicar, 'estado': estado}[o]()
