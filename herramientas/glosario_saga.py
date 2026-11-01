# -*- coding: utf-8 -*-
"""(01-11-2026, claude1; el usuario: «coherencia con lo oficial» de la saga) Glosario OFICIAL inglés -> español
latinoamericano sacado de otros juegos de la saga instalados en Steam (solo los LEE):
  1. extrae con ParTool los mismos archivos en inglés y en español latino (wdr_par_X/*.par, db.nex/<idioma>, y los
     .par de 2dpar/minigame/pausepar/bootpar con letra de idioma) a trabajo/saga/<juego>/<idioma>/
  2. empareja archivo por archivo las cadenas en el mismo orden (solo si los dos tienen el mismo número de cadenas)
  3. escribe trabajo/saga/<juego>_pares.json [{en, es, a}] y suma al glosario trabajo/saga/glosario.json {en: {es: n}}
  python herramientas/glosario_saga.py <juego>      (juegos: ver JUEGOS)"""
import collections, json, os, re, subprocess, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
PT = os.path.join(R, 'herramientas', 'partool', 'ParTool.exe')
S = 'D:/SteamLibrary/steamapps/common'
# juego: (carpeta data, letra inglés, letra latino, carpeta db inglés, carpeta db latino)
JUEGOS = {
    'kiwami': (S + '/Yakuza Kiwami R/runtime/media/data', 'c', 'l', 'db.nex/en', 'db.nex/ls'),
    'kiwami2': (S + '/Yakuza Kiwami 2 R/runtime/media/data', 'c', 'l', 'db.nex/en', 'db.nex/ls'),
    'yakuza0': (S + '/Yakuza 0 Directors Cut/runtime/media/data', 'c', 'l', 'db.gld/en', 'db.gld/ls'),   # Kamurocho y Sotenbori
}
# motor nuevo (Kiwami 3 & Dark Ties): un .par por idioma; «esl» = español latino («ese» = España)
JUEGOS_PAR = {
    'kiwami3': [(S + '/YakuzaKiwami3/runtime/media/data/db.bis.en.par', S + '/YakuzaKiwami3/runtime/media/data/db.bis.esl.par'),
                (S + '/YakuzaKiwami3/runtime/media/data/ui.bis.en.par', S + '/YakuzaKiwami3/runtime/media/data/ui.bis.esl.par')],
}
CAD = re.compile(rb'(?<=\x00)(?:[\x20-\x7e\n]|[\xc2-\xf4][\x80-\xbf]{1,3})+(?=\x00)')


def extraer(par, dst):
    if os.path.isdir(dst): return
    subprocess.run([PT, 'extract', '-r', par, dst], stdin=subprocess.DEVNULL, capture_output=True)


def archivos(data, letra, db):
    """{ruta lógica (sin la letra): ruta real} de los contenedores de un idioma."""
    out = {}
    for dp, ds, fs in os.walk(data):
        rel = os.path.relpath(dp, data).replace(os.sep, '/')
        if rel.split('/')[0] in ('stage', 'chara', 'chara_arc', 'motion', 'shader', 'soundcpk', 'soundpar', 'stream', 'movie60',
                                 'moviesd', 'effect', 'cloth', 'map_par', 'auth_w64_j', 'hact.par', 'light_anim', 'chara.par', 'puid.nex'):
            continue
        for f in fs:
            r = (rel + '/' + f).lstrip('./')
            if r.startswith('wdr_par_' + letra + '/'): out['wdr/' + f] = os.path.join(dp, f)
            elif r.startswith(db + '/'): out['db/' + f] = os.path.join(dp, f)
            elif re.search(r'_' + letra + r'\.par$', f) and not r.startswith('wdr_par_'):
                out[rel + '/' + f[:-len(letra) - 5] + '.par'] = os.path.join(dp, f)
    return out


def cadenas(p):
    b = open(p, 'rb').read()
    if p.endswith('.msg'):          # .msg: por REGISTROS (msg_y5) + tabla de nombres/opciones; se alinean en orden
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import msg_y5
        from extraer_extra import nombres_msg
        try: regs = [r['texto'].decode('utf-8', 'replace') for r in msg_y5.leer(b)[1]]
        except Exception: regs = []
        return regs + ['\x01' + t for _, t in nombres_msg(b)]      # (marca para no mezclar nombres con registros)
    return None     # (01-11) las tablas NO se emparejan por orden (salían «Baseball» -> «Salero»): ver tabla_armp()


REARMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reARMP', 'reARMP.py')


def tabla_armp(p):
    """{ruta fila/columna: texto} de una tabla ARMP exportada con reARMP, o None. Se trabaja SIEMPRE sobre una copia en
    trabajo/saga/armp (reARMP escribe el .json al lado del archivo: nunca en la carpeta del juego)."""
    if not os.path.abspath(p).lower().startswith(os.path.abspath(T).lower()):
        import hashlib, shutil
        c = os.path.join(T, 'saga', 'armp', hashlib.md5(p.encode()).hexdigest()[:12] + '_' + os.path.basename(p))
        os.makedirs(os.path.dirname(c), exist_ok=True)
        if not os.path.exists(c): shutil.copy2(p, c)
        p = c
    j = p + '.json'
    if not os.path.exists(j):      # (reARMP deja el .json en la carpeta DESDE la que se ejecuta: cwd = la de la tabla)
        subprocess.run([sys.executable, REARMP, os.path.basename(p)], input=b'\n', capture_output=True, timeout=900,
                       cwd=os.path.dirname(p))
    if not os.path.exists(j): return None
    try: d = json.load(open(j, encoding='utf-8'))
    except Exception: return None
    out = {}

    def walk(o, ruta):
        if isinstance(o, dict):
            for k, v in o.items():
                if k not in ('VERSION', 'REVISION', 'ROW_COUNT', 'COLUMN_COUNT', 'TEXT_COUNT'): walk(v, ruta + '/' + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o): walk(v, ruta + '/' + str(i))
        elif isinstance(o, str): out[ruta] = o
    walk(d, '')
    return out


# motor nuevo con TODOS los idiomas en un .par: db.par/<idioma>/... (Kiwami 2 R)
JUEGOS_DIR = {'kiwami2': (S + '/Yakuza Kiwami 2 R/runtime/media/data/db.par', 'en', 'esl')}


def main(juego):
    base = os.path.join(T, 'saga', juego); os.makedirs(base, exist_ok=True)
    if juego in JUEGOS_DIR:
        par, le, ll = JUEGOS_DIR[juego]; dst = os.path.join(base, 'db'); extraer(par, dst)
        raiz = next((os.path.join(dp, d) for dp, ds, _ in os.walk(dst) for d in ds if d == le), None)
        fe = {os.path.relpath(os.path.join(dp, f), raiz).replace(os.sep, '/'): os.path.join(dp, f)
              for dp, _, fs in os.walk(raiz) for f in fs}
        rl = os.path.join(os.path.dirname(raiz), ll)
        fl = {os.path.relpath(os.path.join(dp, f), rl).replace(os.sep, '/'): os.path.join(dp, f) for dp, _, fs in os.walk(rl) for f in fs}
    elif juego in JUEGOS_PAR:
        fe = {os.path.basename(e).replace('.en.', '.'): e for e, _ in JUEGOS_PAR[juego]}
        fl = {os.path.basename(e).replace('.en.', '.'): l for e, l in JUEGOS_PAR[juego]}
    else:
        data, le, ll, de, dl = JUEGOS[juego]
        fe, fl = archivos(data, le, de), archivos(data, ll, dl)
    comunes = sorted(set(fe) & set(fl))
    print(juego, 'contenedores en inglés', len(fe), 'en latino', len(fl), 'comunes', len(comunes))
    pares, sin_par = [], collections.Counter()
    for k in comunes:
        def lista(p, lado):
            if p.endswith('.par'):
                dst = os.path.join(base, lado, k.replace('/', '__')); extraer(p, dst)
                return {os.path.relpath(os.path.join(a, f), dst).replace(os.sep, '/'): os.path.join(a, f)
                        for a, _, fs in os.walk(dst) for f in fs}
            return {'': p}
        ae, al = lista(fe[k], 'en'), lista(fl[k], 'ls')
        for sub in sorted(set(ae) & set(al)):
            if re.search(r'\.(dds|gmd|gmt|cmt|png|tex|txbv|sgt|ttf|fnt|bin_|usm|acb|awb)$', sub, re.I): continue
            ce = cadenas(ae[sub])
            if ce is None:                                # tabla: fila/columna con reARMP
                te, tl = tabla_armp(ae[sub]), tabla_armp(al[sub])
                if te is None or tl is None: sin_par[k] += 1; continue
                for ruta, x in te.items():
                    y = tl.get(ruta)
                    if y is not None and x != y and re.search('[A-Za-z]{2}', x) and ' ' in x.strip() + ' ' and not re.fullmatch(r'[\w\-./]+', x):
                        pares.append({'en': x, 'es': y, 'a': k + ':' + sub + ruta})
                    elif y is not None and x != y and re.fullmatch(r"[A-Z][\w'\-]+", x):     # una palabra con mayúscula
                        pares.append({'en': x, 'es': y, 'a': k + ':' + sub + ruta})
                continue
            cl = cadenas(al[sub])
            if not ce: continue
            if len(ce) != len(cl): sin_par[k] += 1; continue
            for x, y in zip(ce, cl):
                x, y = x.lstrip('\x01'), y.lstrip('\x01')
                if x != y and re.search('[A-Za-z]{2}', x): pares.append({'en': x, 'es': y, 'a': k + ':' + sub})
    json.dump(pares, open(os.path.join(T, 'saga', juego + '_pares.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    gp = os.path.join(T, 'saga', 'glosario.json')
    g = json.load(open(gp, encoding='utf-8')) if os.path.exists(gp) else {}
    for p in pares:
        d = g.setdefault(p['en'], {}); d[p['es']] = d.get(p['es'], 0) + 1
    json.dump(g, open(gp, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('pares', len(pares), 'archivos sin emparejar (distinto número de cadenas)', sum(sin_par.values()),
          dict(sin_par.most_common(8)), '| glosario', len(g))


if __name__ == '__main__': main(sys.argv[1])
