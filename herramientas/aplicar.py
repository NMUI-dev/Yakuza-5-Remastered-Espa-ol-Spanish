# -*- coding: utf-8 -*-
"""(Claude Code, 20-10-2026) Reinserta la traducción de Yakuza 5 y rearma los archivos del juego.
Entrada: trabajo/textos_en.jsonl (extraer.py) + trabajo/lotes/lote_NNN(_es).json (traducción).
Salida: trabajo/salida/data/... con la MISMA ruta que en main/data (listo para copiar al juego o al laboratorio).
  python herramientas/aplicar.py              -> traducción real (lo que falte queda en inglés)
  python herramientas/aplicar.py --prueba     -> en vez de traducir, pone «ñ·» delante de cada texto (prueba de caminos)
Formatos (ver PASO_A_PASO.txt):
  msg   : texto nuevo AL FINAL del archivo; el registro apunta ahí; las posiciones de las funciones (pausas, colores,
          fin) se recalculan sobre las letras visibles del español.
  sub   : CSV UTF-16 de auth/subtitle.par (columna 3).
  tabla : tablas 20 07 03 19 (tabla_y5.py).
  ptr   : texto nuevo al final del .bin y se cambian TODOS los punteros (u32 big endian alineados) que apuntaban al viejo.
  pac   : en su sitio, sin pasar del largo original (lote 310 = versiones cortas); si no cabe, queda en inglés.
"""
import os, re, sys, json, glob, struct, shutil, subprocess, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import msg_y5, tabla_y5
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(R, 'trabajo'); E = os.path.join(T, 'extraido'); L = os.path.join(T, 'lotes')
SAL = os.path.join(T, 'salida'); TMP = os.path.join(T, 'salida_tmp')
JUEGO = os.environ.get('Y5_JUEGO', 'D:/SteamLibrary/steamapps/common/Yakuza 5/main/data')   # (30-10) otra carpeta: variable de entorno Y5_JUEGO
# (21-10) si la traducción está INSTALADA en Steam, el «original» ya no lo es: parar (quitarla antes con el instalador)
if os.path.exists(os.path.join(os.environ.get('Y5_JUEGO', 'D:/SteamLibrary/steamapps/common/Yakuza 5/main/data'), 'traduccion_es_version.txt')):
    sys.exit('La traducción está instalada en Steam: quítala (INSTALAR o QUITAR.bat, opción 2) antes de rearmar.')
PT = os.path.join(R, 'herramientas', 'partool', 'ParTool.exe')
PRUEBA = '--prueba' in sys.argv
# carpeta extraída -> archivo .par del juego (relativo a data)
ARCHIVOS = {'wdr_par_en_wdr': 'wdr_par_en/wdr.par', 'wdr_par_en_common': 'wdr_par_en/common.par',
            'staypar_stay_en': 'staypar/stay_en.par', 'bootpar_boot_en': 'bootpar/boot_en.par',
            'auth_subtitle': 'auth/subtitle.par', '2dpar_ui_en': '2dpar/ui_en.par', '2dpar_sprite_en': '2dpar/sprite_en.par'}
for n in ('pause', 'title_menu', 'movie', 'kigae', 'idol_work', 'snowball', 'staffroll', 'taxi', 'tougijyo', 'book'):
    ARCHIVOS[f'pausepar_{n}_en'] = f'pausepar/{n}_en.par'
ARCHIVOS['minigame_en_karaoke'] = 'minigame_en/karaoke.par'; ARCHIVOS['minigame_en_karaoke_e'] = 'minigame_en/karaoke_e.par'
SUELTOS = ('scenario_en', 'minigame_en')            # carpetas que en el juego son archivos sueltos
# nombres internos que el juego no muestra (etiquetas de guion y de diseño): no se tocan
EXCLUIR = ('scenario_en/scenario2.bin', 'scenario_en/scenario_state.bin', 'scenario_en/player_pos.bin',
           'minigame_en/live_btl/live_btl_AI.bin', 'minigame_en/baseball/BaseBallPitcher.bin')
# columnas de tabla que son CÓDIGO interno (expresiones, ids, claves de enum/modelo/animación): cambiarlas cierra el juego
# (20-10: battle_condition «battle_start != 0» y compañía cerraban Yakuza 5 al llegar al primer diálogo)
COL_INTERNAS = {('battle_condition.bin', '条件'), ('effect_low_list.bin', 'EID_AFTER'), ('effect_low_list.bin', 'EID_BEFORE'),
    ('item.bin', 'ID'), ('item.bin', 'PRESENT'), ('drive_mission.bin', 'GOAL'), ('drive_mission.bin', 'MODEL'),
    ('tips_tutorial.bin', 'ENUM'), ('zactparam.bin', 'ROBJID'), ('aiming_param.bin', 'CATEGORY'),
    ('continuepoint.bin', 'SCENARIO'), ('restaurant_menu.bin', 'NAME'), ('restaurant_menu.bin', 'DECIDE'),
    ('drive_tutorial.bin', 'TYPE'), ('drive_camera.bin', 'NAME'), ('live_event.bin', 'MISSION'),
    ('live_btl_point.bin', 'MISSION'), ('EncountTable_1.bin', 'CATEGORY'), ('EncountTable_2.bin', 'CATEGORY'),
    ('EncountTable_3.bin', 'CATEGORY'), ('EncountTable_4.bin', 'CATEGORY'), ('fishing_river_motion.bin', 'NAME'),
    ('dance_battle.bin', 'NAME'), ('mission_snow.bin', 'EXPLANATION'), ('drive_parts.bin', 'CATEGORY')}
CJK = re.compile('[぀-ヿ一-鿿]')


def norm(t): return t.replace('\r\n', '\n')


def traducciones():
    gen = {}; corto = {}
    for f in sorted(glob.glob(os.path.join(L, 'lote_???.json'))):
        fe = f[:-5] + '_es.json'
        if not os.path.exists(fe): continue
        es = json.load(open(fe, encoding='utf-8')); dest = corto if f.endswith('lote_310.json') else gen
        for x in json.load(open(f, encoding='utf-8')):
            t = es.get(str(x['id']))
            if isinstance(t, str) and t.strip(): dest[x['en']] = t
    return gen, corto


# (21-10) el «¡» de la letra del juego (0xA1) tiene un ancho fijo grande («¡ Un»): se dibuja en la casilla de «~»
# (que ningún texto usa) y los textos lo escriben así. Las imágenes NO (usan traducciones() sin pasar por aquí).
LETRAS = str.maketrans({'¡': '½', 'í': '`', 'Í': '|'})   # (21-10) í en la casilla de «`» (ancho de la tabla del juego: herramientas/letra_i.py)


def es_de(t, gen, maxb=None, corto=None):
    """traducción del texto inglés t (con \\r\\n del juego) o None."""
    if PRUEBA:
        r = 'ñ·' + t
        return r if maxb is None or len(r.encode()) <= maxb else None
    k = norm(t); r = (corto or {}).get(k) if maxb is not None else None
    r = r or gen.get(k)
    if r is None: return None
    if '\r\n' in t: r = r.replace('\r\n', '\n').replace('\n', '\r\n')
    r = r.translate(LETRAS)
    if maxb is not None and len(r.encode('utf-8')) > maxb: return None
    return r


# ---------- msg ----------
ETQ = re.compile(r'<[^>]*>')
def visibles(t): return ETQ.sub('', t.replace('\r\n', '\n'))
def pos_etiquetas(t):
    """posiciones (en letras visibles) de cada etiqueta, en orden."""
    p = []; v = 0; i = 0; s = t.replace('\r\n', '\n')
    while i < len(s):
        if s[i] == '<':
            j = s.find('>', i)
            if j > 0: p.append(v); i = j + 1; continue
        v += 1; i += 1
    return p
PUNT = '.,!?…:;)」'
def remapear(pos, en, es, tipo):
    """posición de una función en el inglés -> en el español."""
    ve, vs = len(visibles(en)), len(visibles(es))
    if pos == 0: return 0
    if pos >= ve: return vs
    te, ts = pos_etiquetas(en), pos_etiquetas(es)
    if pos in te and len(te) == len(ts): return ts[te.index(pos)]
    p = int(round(pos * vs / max(1, ve)))
    if tipo in (0x0200, 0x020a):                      # pausas: caer justo tras un signo de puntuación cercano
        txt = visibles(es); cand = [i + 1 for i, c in enumerate(txt) if c in PUNT]
        if cand:
            c = min(cand, key=lambda x: abs(x - p))
            if abs(c - p) <= max(6, vs // 6): p = c
    return max(0, min(vs, p))


def aplicar_msg(b, celdas, gen, stats):
    b = bytearray(b); secs, regs = msg_y5.leer(bytes(b))
    porreg = {r['reg']: r for r in regs}
    for c in celdas:
        r = porreg[c['k']]; en = r['texto'].decode('utf-8'); es = es_de(en, gen)
        if es is None: stats['msg_sin'] += 1; continue
        nuevo = es.encode('utf-8')
        if len(nuevo) > 0xFFFF: stats['msg_largo'] += 1; continue
        off = len(b); b += nuevo + b'\0'
        while len(b) % 4: b += b'\0'
        struct.pack_into('>HBBI', b, c['k'], len(nuevo), r['nf'], r['y'], off)
        for fo, fb in r['funcs']:
            tipo = struct.unpack('>H', fb[:2])[0]; pos = struct.unpack('>H', fb[6:8])[0]
            struct.pack_into('>H', b, fo + 6, remapear(pos, en, es, tipo))
        stats['msg'] += 1
    return bytes(b)


# ---------- subtítulos ----------
def aplicar_sub(b, celdas, gen, stats):
    filas = b.decode('utf-16').split('\r\n')
    for c in celdas:
        col = filas[c['k']].split('\t'); es = es_de(col[2], gen)
        if es is None: stats['sub_sin'] += 1; continue
        col[2] = es.replace('\r\n', '\n'); filas[c['k']] = '\t'.join(col); stats['sub'] += 1
    return '\r\n'.join(filas).encode('utf-16')


# ---------- tablas ----------
def aplicar_tabla(b, celdas, gen, stats):
    t = tabla_y5.leer(b)
    for c in celdas:
        es = es_de(c['t'], gen)
        if es is None: stats['tabla_sin'] += 1; continue
        tabla_y5.poner(t, c['c'], tuple(c['k']), es.encode('utf-8')); stats['tabla'] += 1
    return tabla_y5.escribir(t)


# ---------- punteros ----------
def aplicar_ptr(b, celdas, gen, stats):
    b = bytearray(b); orig = bytes(b)
    punteros = collections.defaultdict(list)
    for i in range(0, len(orig) - 3, 4): punteros[struct.unpack('>I', orig[i:i + 4])[0]].append(i)
    for c in celdas:
        es = es_de(c['t'], gen)
        if es is None: stats['ptr_sin'] += 1; continue
        while len(b) % 4: b += b'\0'
        off = len(b); b += es.encode('utf-8') + b'\0'
        for p in punteros[c['k']]: struct.pack_into('>I', b, p, off)
        stats['ptr'] += 1
    while len(b) % 4: b += b'\0'
    return bytes(b)


# ---------- pac ----------
def aplicar_pac(b, celdas, gen, corto, stats):
    b = bytearray(b)
    for c in celdas:
        n = len(c['t'].encode('utf-8')); es = es_de(c['t'], gen, n, corto)
        if es is None: stats['pac_sin'] += 1; continue
        x = es.encode('utf-8'); b[c['k']:c['k'] + n] = x + b'\0' * (n - len(x)); stats['pac'] += 1
    return bytes(b)


def partool(*a):
    r = subprocess.run([PT, *a], stdin=subprocess.DEVNULL, capture_output=True)
    if r.returncode != 0 or b'ERROR' in r.stdout.upper(): raise RuntimeError(f'ParTool {a[0]}: {r.stdout[-300:]!r}')


def main():
    gen, corto = traducciones()
    print('traducciones:', len(gen), '+ cortas', len(corto), '(PRUEBA)' if PRUEBA else '')
    porarch = collections.defaultdict(list)
    for l in open(os.path.join(T, 'textos_en.jsonl'), encoding='utf-8'):
        e = json.loads(l)
        if e['a'] in EXCLUIR or CJK.search(e['t']): continue
        if e['f'] == 'tabla' and ((e['a'].split('/')[-1], e['c']) in COL_INTERNAS or e['c'].startswith('モ')): continue
        porarch[e['a']].append(e)
    stats = collections.Counter()
    for d in (SAL, TMP): shutil.rmtree(d, ignore_errors=True)
    tocados = collections.defaultdict(list)              # carpeta extraída raíz -> rutas relativas cambiadas
    for a, celdas in porarch.items():
        b = open(os.path.join(E, a), 'rb').read(); f = celdas[0]['f']
        if f == 'msg': n = aplicar_msg(b, celdas, gen, stats)
        elif f == 'sub': n = aplicar_sub(b, celdas, gen, stats)
        elif f == 'tabla': n = aplicar_tabla(b, celdas, gen, stats)
        elif f == 'ptr': n = aplicar_ptr(b, celdas, gen, stats)
        elif f == 'pac': n = aplicar_pac(b, celdas, gen, corto, stats)
        if n == b: continue
        dest = os.path.join(TMP, a); os.makedirs(os.path.dirname(dest), exist_ok=True); open(dest, 'wb').write(n)
        tocados[a.split('/')[0]].append(a)
    print(dict(stats))
    # rearmar: .par del juego (con «add») o archivos sueltos (con .par anidados de minijuegos)
    for raiz, rutas in tocados.items():
        if raiz in ARCHIVOS:
            par = os.path.join(JUEGO, ARCHIVOS[raiz]); out = os.path.join(SAL, 'data', ARCHIVOS[raiz])
            os.makedirs(os.path.dirname(out), exist_ok=True)
            partool('add', par, os.path.join(TMP, raiz), out); print('par', ARCHIVOS[raiz], len(rutas))
        elif raiz in SUELTOS:
            anid = collections.defaultdict(list)
            for a in rutas:
                m = re.match(r'(.*?)/([^/]+)_par/(.*)', a)
                if m: anid[(m.group(1), m.group(2))].append(a)
                else:
                    out = os.path.join(SAL, 'data', a); os.makedirs(os.path.dirname(out), exist_ok=True)
                    shutil.copy(os.path.join(TMP, a), out)
            for (carpeta, nombre), rs in anid.items():
                par = os.path.join(JUEGO, carpeta, nombre + '.par'); out = os.path.join(SAL, 'data', carpeta, nombre + '.par')
                os.makedirs(os.path.dirname(out), exist_ok=True)
                partool('add', par, os.path.join(TMP, carpeta, nombre + '_par'), out); print('par anidado', carpeta, nombre, len(rs))
        else: print('AVISO: sin destino para', raiz, len(rutas))
    # letra con ¿ ¡ í corregidas (trabajo/fuente/font_hd_en.par, ver PASO_A_PASO 17)
    os.makedirs(os.path.join(SAL, 'data', 'fontpar'), exist_ok=True)
    shutil.copy(os.path.join(T, 'fuente', 'font_hd_en.par'), os.path.join(SAL, 'data', 'fontpar', 'font_hd_en.par'))
    # imágenes de menú traducidas (después de los textos: pause_en.par lleva las dos cosas)
    import imagenes_aplicar; imagenes_aplicar.main()
    print('salida en', SAL)


if __name__ == '__main__': main()
