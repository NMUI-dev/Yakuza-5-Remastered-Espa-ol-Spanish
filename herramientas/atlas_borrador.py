# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) KIT DE ATLAS para el equipo (claude1 + Fable; Claude claude2 verifica). Ver
trabajo/imagenes/GUIA_ATLAS.md. Prepara un BORRADOR editable por atlas de menú:
  - casillas reales del juego (.sbb) con tinta, una por rótulo;
  - texto: gemma4 (visión, local) y el OCR tienen que coincidir; si no, la casilla va marcada «revisar»;
  - traducción (frases del juego, o la de los ayudantes gratuitos), letra según gemma4, alineación medida, efecto:
    «estilo» (degradado/contorno/brillo medidos) si el original tiene color o contorno, si no «nada»;
  - casillas opacas (botones): fondo «lama» (LaMa borra solo el texto).
Salida: trabajo/imagenes/atlas_borradores/<id>.json  +  <id>_casillas.png (casillas numeradas sobre la textura).
  python herramientas/atlas_borrador.py lista              (atlas pendientes con su id)
  python herramientas/atlas_borrador.py hacer <id|filtro>  (uno o varios)
"""
import difflib, json, os, re, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es, atlas_semi as S
R = S.R; T = S.T
BORR = os.path.join(T, 'atlas_borradores'); HECHOS = os.path.join(T, 'atlas_hechos')


def ident(nombre):
    return nombre.replace('/', '__')


def pendientes():
    hechos = {f[:-5] for f in os.listdir(HECHOS)} if os.path.isdir(HECHOS) else set()
    return [n for n in S.atlas_lista() if ident(n) not in hechos]


def parecido(a, b):
    f = lambda s: re.sub(r'[^a-z0-9]', '', (s or '').lower())
    return difflib.SequenceMatcher(None, f(a), f(b)).ratio()


def ocr_en(lineas, c):
    """Texto del OCR cuyo centro cae dentro de la casilla."""
    return ' '.join(l[4] for l in lineas if c[0] <= (l[0] + l[2]) / 2 <= c[2] and c[1] <= (l[1] + l[3]) / 2 <= c[3])


def hacer(nombre, ocr, juego, tr, fa):
    a = np.asarray(Image.open(os.path.join(S.tex_dir(nombre), nombre + '.dds')).convert('RGBA'))
    lineas = ocr.get(nombre + '.dds', []); items = []
    if nombre.startswith(('ui_en/', '2dpar_ui_en/')): casillas = S.celdas_tinta(a, S.sbbs_de(nombre))
    else:   # (21-10) página (sin diseño .sbb): una casilla por renglón del OCR, con un poco de aire
        H, W = a.shape[:2]
        casillas = [[max(0, l[0] - 3), max(0, l[1] - 3), min(W, l[2] + 3), min(H, l[3] + 3)] for l in lineas]
    # (21-10, aviso de claude1) renglones del OCR que ninguna casilla cubre (o atlas sin .sbb útil): casilla = renglón
    H, W = a.shape[:2]
    for l in lineas:
        cx, cy = (l[0] + l[2]) / 2, (l[1] + l[3]) / 2
        if re.search(r'[A-Za-z]{2,}', l[4]) and not any(c[0] <= cx <= c[2] and c[1] <= cy <= c[3] for c in casillas):
            casillas.append([max(0, l[0] - 3), max(0, l[1] - 3), min(W, l[2] + 3), min(H, l[3] + 3)])
    for c in casillas:
        o = ocr_en(lineas, c)
        if not re.search(r'[A-Za-z]{2,}', o): continue                 # sin letras según el OCR: icono, número, adorno
        d = S.vlm(S.DESCRIBIR, [S.recorte_png(a, c)])
        t = ' '.join((d.get('text') or '').split())
        it = {'caja': list(c), 'en': t or o, 'ocr': o}
        if parecido(t, o) < 0.6: it['revisar'] = f'gemma4 lee «{t}» y el OCR «{o}»'
        if d.get('partial'): it['revisar'] = 'trozo de palabra (gemma4): ¿se junta con la casilla vecina o se deja?'
        es = S.traduccion(it['en'], juego, tr)
        it['es'] = S.estilo(it['en'], es.replace('\n', ' ')) if es else ''
        if not es: it['revisar'] = it.get('revisar', 'sin traducción: escríbela')
        it['fuente'] = S.fuente_de(d, fa.get(nombre, 'segoeui.ttf'))
        z = a[c[1]:c[3], c[0]:c[2]]
        borde = np.concatenate([z[0, :, 3], z[-1, :, 3], z[:, 0, 3], z[:, -1, 3]])
        if (z[..., 3] > 200).mean() > 0.75 and (borde > 200).mean() > 0.9: it['fondo'] = 'lama'   # (21-10) solo si el BORDE es opaco (fondo de verdad, no un contorno grueso)
        est = atlas_es.medir_estilo(atlas_es.zona_texto(a, it))
        color = est['contorno'] or est['brillo'] or np.abs(np.array(est['arriba']) - np.array(est['abajo'])).sum() > 60
        it['efecto'] = 'borroso' if d.get('effect') == 'blurred' else 'estilo' if color else 'nada'
        it['alin'] = S.alineacion(a, c); it['ancho_max'] = c[2] - c[0] - 4
        items.append(it)
    base = S.SEGOE.get(fa.get(nombre, 'segoeui.ttf'), fa.get(nombre, 'segoeui.ttf'))   # (21-10) nunca arial*
    spec = {'textura': nombre, 'fuente': base, 'margen': 0, 'mediana': False, 'items': items}
    os.makedirs(BORR, exist_ok=True)
    json.dump(spec, open(os.path.join(BORR, ident(nombre) + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # casillas numeradas (rojo = revisar)
    base = Image.new('RGBA', (a.shape[1], a.shape[0]), (40, 90, 40, 255)); base.alpha_composite(Image.fromarray(a))
    k = max(1, 1024 // max(a.shape[:2])); base = base.resize((a.shape[1] * k, a.shape[0] * k), Image.NEAREST); dr = ImageDraw.Draw(base)
    for i, it in enumerate(items):
        x0, y0, x1, y1 = [v * k for v in it['caja']]; col = (255, 60, 60, 255) if it.get('revisar') else (255, 255, 0, 255)
        dr.rectangle([x0, y0, x1 - 1, y1 - 1], outline=col); dr.text((x0 + 2, y0 + 1), str(i), fill=col)
    base.convert('RGB').save(os.path.join(BORR, ident(nombre) + '_casillas.png'))
    print(ident(nombre), len(items), 'rótulos', sum(1 for it in items if it.get('revisar')), 'para revisar', flush=True)


def main():
    if sys.argv[1] == 'lista':
        for n in pendientes(): print(ident(n))
        return
    ocr = json.load(open(os.path.join(T, 'ocr.json'), encoding='utf-8')); juego = S.del_juego()
    tr = json.load(open(S.TR, encoding='utf-8')) if os.path.exists(S.TR) else {}
    fa = json.load(open(os.path.join(T, 'atlas_fuentes.json'), encoding='utf-8'))
    filtro = sys.argv[2]
    for n in pendientes():
        if filtro in n or filtro == ident(n): hacer(n, ocr, juego, tr, fa)


if __name__ == '__main__':
    main()
