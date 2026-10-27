# -*- coding: utf-8 -*-
"""(claude1, 21-10-2026) 3.ª pasada de las páginas (FULL AHORRO, sin Fable). El usuario: «las 399 en español, con
coherencia y sin cambiar los términos que ya se usan en español». Sobre lo que dejó paginas_auto2.py:
  - «trozo de palabra»: frases partidas en varias casillas (purikura...). Las casillas que se tocan forman un grupo; por
    renglones visuales -> una caja por renglón; gemma4 (local) lee la frase entera del grupo en N renglones.
  - «gemma4 lee X y el OCR Y»: si X tiene palabras de verdad se usa X; si no (adorno, japonés, letras sueltas) se quita
    la casilla (queda el original).
  - todo lo que siga sin español se traduce en bloque con los gratuitos + glosario de términos del juego, en N renglones.
Acepta lo que queda sin «revisar» (incluidas las falsas alarmas de gemma4): la verificación es la de claude1 con
atlas_verificar.py hojas, por tandas. Quedan en tareas/paginas_auto3_dejadas.txt.
  python herramientas/paginas_auto3.py
"""
import json, os, re, subprocess, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_semi as S
from atlas_borrador import BORR
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEJ = os.path.join(R, 'tareas', 'paginas_auto2_dejadas.txt')
LEER = ('This image is cut from a video game texture and shows ONE phrase split over {n} visual line(s). Transcribe the '
        'English text exactly. Answer ONLY JSON: {{"lines": ["line 1", ...]}} with exactly {n} strings, top to bottom.')
juego = S.del_juego()


def glosario(textos):
    g = {}
    for t in textos:
        w = re.findall(r"[a-z0-9'-]+", t.lower())
        for n in range(4, 0, -1):
            for a in range(len(w) - n + 1):
                f = ' '.join(w[a:a + n])
                if f in juego and len(f) > 3 and len(g) < 80: g[f] = juego[f]
    return g


def toca(a, b, m=10):
    return a[0] - m < b[2] and b[0] - m < a[2] and a[1] - m < b[3] and b[1] - m < a[3]


def union(cs):
    return [min(c[0] for c in cs), min(c[1] for c in cs), max(c[2] for c in cs), max(c[3] for c in cs)]


def renglones(its):
    """Casillas del grupo -> renglones visuales (se solapan en alto más de la mitad), de arriba abajo."""
    ls = []
    for it in sorted(its, key=lambda t: (t['caja'][1] + t['caja'][3]) / 2):
        c = it['caja']
        for l in ls:
            u = union([x['caja'] for x in l])
            if min(c[3], u[3]) - max(c[1], u[1]) > 0.5 * min(c[3] - c[1], u[3] - u[1]): l.append(it); break
        else: ls.append([it])
    return ls


def palabras(t):
    return bool(re.search(r'[A-Za-z]{4,}', t or '')) or len(re.findall(r'[A-Za-z]{2,}', t or '')) >= 2


ids = [l.split()[0] for l in open(DEJ, encoding='utf-8') if l.strip()]
specs, grupos = {}, []        # grupos: (id, [renglón = [items]], [inglés por renglón])
for i in ids:
    p = os.path.join(BORR, i + '.json')
    if not os.path.exists(p): continue
    d = json.load(open(p, encoding='utf-8')); specs[i] = d; its = d['items']
    for it in list(its):
        if it.get('revisar', '').startswith('gemma4 lee'):
            if palabras(it['en']): del it['revisar']; it['es'] = ''
            else: its.remove(it)
    parte = [it for it in its if it.get('revisar', '').startswith('trozo')]
    vistos = set()
    if parte:
        a = np.asarray(Image.open(os.path.join(S.tex_dir(d['textura']), d['textura'] + '.dds')).convert('RGBA'))
        for it in parte:
            if id(it) in vistos: continue
            g = [it]; cambio = True
            while cambio:
                cambio = False
                for o in its:
                    if o not in g and any(toca(o['caja'], x['caja']) for x in g): g.append(o); cambio = True
            vistos |= {id(x) for x in g}
            ls = renglones(g)
            r = S.vlm(LEER.format(n=len(ls)), [S.recorte_png(a, union([x['caja'] for x in g]))])
            en = r.get('lines') if isinstance(r.get('lines'), list) and len(r['lines']) == len(ls) else \
                [' '.join(x['en'] for x in sorted(l, key=lambda t: t['caja'][0])) for l in ls]
            grupos.append((i, ls, [str(e).strip() for e in en]))
    for it in its:
        if id(it) in vistos: continue
        if (not it.get('es') and 'revisar' not in it and palabras(it['en'])) or it.get('revisar', '').startswith('sin tr'):
            grupos.append((i, [[it]], [it['en']]))
print(len(specs), 'borradores;', len(grupos), 'frases a traducir', flush=True)
sys.argv = [sys.argv[0], 'semi']
import traductor_gemini as TG
encargo = ("Traduce al español neutro latinoamericano estos textos dibujados en imágenes de Yakuza 5 (pegatinas de "
           "purikura, reglas de minijuegos, avisos). Cada uno es UNA frase repartida en N renglones: devuelve la traducción "
           "en EXACTAMENTE N renglones, cada uno de largo parecido a su renglón inglés; respeta MAYÚSCULAS; sin saltarte "
           "nada. Nombres propios y títulos de canciones se dejan igual. Devuelve SOLO JSON {\"t\": {\"id\": [\"renglón\", ...]}}.\n")
tr = {}
for k in range(0, len(grupos), 25):
    trozo = {str(k + n): g[2] for n, g in enumerate(grupos[k:k + 25])}
    gl = glosario([e for v in trozo.values() for e in v])
    gl = ("OBLIGATORIO, términos que el juego YA usa en español (úsalos igual): " + json.dumps(gl, ensure_ascii=False) + "\n") if gl else ''
    r, m = TG.pedir(encargo + gl + json.dumps(trozo, ensure_ascii=False, indent=0))
    t = (r.get('t', r) if isinstance(r, dict) else {}) if r is not None else {}
    for n in trozo:
        v = t.get(n); v = [v] if isinstance(v, str) else v
        if isinstance(v, list) and len(v) == len(trozo[n]) and all(isinstance(x, str) and x.strip() for x in v): tr[int(n)] = v
    print(f'{min(k + 25, len(grupos))}/{len(grupos)} ({m})', flush=True)
for n, (i, ls, en) in enumerate(grupos):
    if n not in tr: continue
    its = specs[i]['items']; pos = min(its.index(x) for l in ls for x in l)
    nuevos = []
    for l, e, s in zip(ls, en, tr[n]):
        base = dict(max(l, key=lambda t: (t['caja'][2] - t['caja'][0]) * (t['caja'][3] - t['caja'][1])))
        base.pop('revisar', None); c = union([x['caja'] for x in l])
        base.update(caja=c, en=e, es=S.estilo(e, s.replace('\n', ' ')))
        if 'ancho_max' in base: base['ancho_max'] = c[2] - c[0]
        nuevos.append(base)
    for l in ls:
        for x in l: its.remove(x)
    its[pos:pos] = nuevos
quedan = []
for i, d in specs.items():
    json.dump(d, open(os.path.join(BORR, i + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if any('revisar' in it or not it.get('es') for it in d['items'] if palabras(it['en'])): quedan.append(i); continue
    subprocess.run([sys.executable, os.path.join(R, 'herramientas', 'atlas_probar.py'), 'aceptar', i], capture_output=True)
    print(i, 'ACEPTADO', flush=True)
open(os.path.join(R, 'tareas', 'paginas_auto3_dejadas.txt'), 'w', encoding='utf-8').write('\n'.join(quedan) + '\n')
print('FIN', len(specs) - len(quedan), 'aceptados,', len(quedan), 'quedan', flush=True)
