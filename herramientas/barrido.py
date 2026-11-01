# (31-10, claude1; el usuario: «verifica más a fondo dónde hay más textos en inglés, que ningún capítulo esté en inglés»)
# Barrido del juego INSTALADO (solo lee): extrae con ParTool -r los .par con texto a <salida>/x/ y busca en TODOS los
# archivos (menos imágenes/modelos/sonido) cadenas que parezcan inglés (UTF-8 terminadas en 0 y CSV UTF-16).
#   python barrido.py extraer <data> <salida>      (una vez)
#   python barrido.py buscar  <salida>              -> <salida>/ingles.jsonl {a: archivo, t: texto, n: veces} + resumen
import collections, json, os, re, subprocess, sys

PT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'partool', 'ParTool.exe')
# carpetas de data/ que se miran (las de otros idiomas, mapas, modelos, sonido y vídeo no)
CARPETAS = ['2dpar', 'auth', 'auth_telop', 'battlepar', 'bootpar', 'chara.par', 'chara_common', 'db.devil', 'fighter',
            'fontpar', 'hact', 'map_par_hd', 'minigame_en', 'module', 'pausepar', 'puid.devil', 'reactorpar', 'scenario',
            'scenario_en', 'staypar', 'wdr_par_en']
if os.environ.get('CARPETAS'): CARPETAS = os.environ['CARPETAS'].split()      # otro juego (Yakuza 6)
NO = {'.dds', '.gmd', '.gmt', '.cmt', '.txbv', '.tex', '.png', '.bmp', '.wav', '.adx', '.hca', '.acb', '.awb', '.usm',
      '.mp4', '.sfd', '.bep', '.gfx', '.ttf', '.otf', '.fnt', '.sgt', '.mep', '.dat_tex'}
EN = set("""the you and of to is it that this with for be have do not what your my we he she they on in at was are i i'm
don't can't won't it's that's you're let's ya gonna get got just me him her them our their there here who how why when
where which will would could should all any some one no yes yeah hey oh well right now then so but if or about from
by up out into over man woman guy girl men boy old young kid sir lady street road apartment office room bar club house
park hotel shop store station building alley chapter part plot unfolds door pretend open home pay take give see look
talk go come leave wait stop help""".split())
ES = set("""de la el que y en los las un una por con es no se su al lo del para como más pero sus le ya o fue este ha sí
porque esta son entre cuando muy sin sobre también me hasta hay donde quien desde todo nos durante estos uno les ni
contra otros ese eso ante ellos e esto mí antes algunos qué unos yo otro otras otra él tanto esa estos mucho quienes
nada muchos cual poco ella estar estas algunas algo nosotros mi mis tú te ti tu tus vosotros os mío mía tuyo""".split())


def extraer(data, sal):
    x = os.path.join(sal, 'x')
    for c in CARPETAS:
        p = os.path.join(data, c)
        fs = [p] if os.path.isfile(p) else [os.path.join(dp, f) for dp, _, ff in os.walk(p) for f in ff]
        for f in fs:
            rel = os.path.relpath(f, data).replace('\\', '/')
            dst = os.path.join(x, rel)
            if f.endswith('.par'):
                if os.path.isdir(dst + '_par'): continue
                r = subprocess.run([PT, 'extract', '-r', f, dst + '_par'], stdin=subprocess.DEVNULL, capture_output=True)
                if r.returncode: print('FALLO', rel, r.stdout[-200:])
            elif not os.path.exists(dst):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(f, 'rb') as a, open(dst, 'wb') as b: b.write(a.read())
        print('hecho', c, flush=True)


U8 = re.compile(rb'(?:[\x20-\x7e]|[\xc2-\xf4][\x80-\xbf]{1,3}|\n)+')
U16 = re.compile(rb'(?:[\x20-\x7e\n\t]\x00|[\xa1-\xff]\x00)+')
PAL = re.compile(r"[A-Za-z][a-z']*")


def ingles(s):
    """¿Es una frase o rótulo en inglés (no un identificador, ruta ni español)?"""
    if len(s) < 4 or not re.search(r'[a-z]{2}|[A-Z]{3}', s): return False
    if re.search(r'[_\\/{}=<>|@#$%^*]|\.(?:bin|dds|par|msg|gmd|txt)\b|^[A-Za-z0-9]+$', re.sub(r'<[^>]*>', '', s)):
        return False
    if re.search('[áéíóúñ¿¡ÁÉÍÓÚÑ]', s): return False
    w = [p.lower() for p in PAL.findall(s)]
    if not w: return False
    en = sum(p in EN for p in w); es = sum(p in ES for p in w)
    if es > en: return False
    if en: return True
    # rótulos sin palabras comunes: 2+ palabras con mayúscula inicial o en MAYÚSCULAS («Shocked Man», «FROZEN ROAR»)
    return len(w) >= 2 and all(p[0].isupper() for p in PAL.findall(s)) and ' ' in s.strip()


def buscar(sal):
    x = os.path.join(sal, 'x'); cnt = collections.Counter(); por = collections.defaultdict(collections.Counter)
    for dp, _, ff in os.walk(x):
        for f in ff:
            p = os.path.join(dp, f)
            if os.path.splitext(f)[1].lower() in NO or f.endswith('.par') or os.path.getsize(p) > 64 << 20: continue
            b = open(p, 'rb').read(); a = os.path.relpath(p, x).replace('\\', '/')
            ss = [m.decode('utf-8', 'ignore') for m in U8.findall(b)]
            ss += [m.decode('utf-16-le', 'ignore') for m in U16.findall(b) if len(m) >= 8]
            for s in ss:
                for t in re.split(r'[\t\n]+', s) if '\t' in s else [s]:
                    t = t.strip()
                    if ingles(t): cnt[(a, t)] += 1
    with open(os.path.join(sal, 'ingles.jsonl'), 'w', encoding='utf-8') as o:
        for (a, t), n in sorted(cnt.items()):
            o.write(json.dumps({'a': a, 't': t, 'n': n}, ensure_ascii=False) + '\n')
            g = '/'.join(a.split('/')[:2]); por[g][t] += 1
    tot = sorted(((len(v), k) for k, v in por.items()), reverse=True)
    print('cadenas únicas en inglés por carpeta:')
    for n, k in tot: print(f'{n:7d}  {k}')
    print('TOTAL', len({t for _, t in cnt}), 'únicas,', len(cnt), 'archivo+cadena')


if __name__ == '__main__':
    {'extraer': lambda: extraer(sys.argv[2], sys.argv[3]), 'buscar': lambda: buscar(sys.argv[2])}[sys.argv[1]]()
