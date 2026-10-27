# -*- coding: utf-8 -*-
"""Yakuza 5 Remastered - herramienta de traducción (Kilo, 21-10-2026).

Saca TODOS los textos del juego en inglés a una hoja (trabajo\\textos.csv, UTF-8 con BOM) con el inglés original y la
traducción actual al lado, y después vuelve a meter en el juego lo que cambies en la columna «espanol».

  python herramienta_traduccion.py extraer     -> trabajo\\textos.csv
  python herramienta_traduccion.py aplicar     -> salida\\data\\  (solo los archivos que cambian: lo mismo que la
                                                   carpeta «archivos» del instalador)
  python herramienta_traduccion.py aplicar --a-archivos   -> además copia salida\\data\\ encima de ..\\archivos\\data\\

Los mensajes del sistema (data\\db.devil\\en\\msg.bin) se aplican DESPUÉS de los demás, dentro de este mismo programa.

El código viene del proyecto (herramientas\\extraer.py, aplicar.py, msg_y5.py, tabla_y5.py, devil.py): aquí está
copiado y joined en un solo archivo para que la herramienta no dependa de nada más que Python 3.

Opciones: --ingles "<carpeta data del juego en inglés>" (por defecto: ..\\respaldo_original que deja el instalador, o el
juego de Steam si aún no tiene la traducción). Ver COMO_USAR.txt y PASO_A_PASO.txt.
"""
import calendar, csv, json, os, re, shutil, struct, subprocess, sys, time, collections

# ---------------------------------------------------------------- rutas
AQUI = os.path.dirname(os.path.abspath(__file__))
PAQUETE = os.path.dirname(AQUI)                          # carpeta del instalador (entrega\)
TRABAJO = os.path.join(AQUI, 'trabajo')
SALIDA = os.path.join(AQUI, 'salida')
DATOS = os.path.join(AQUI, 'datos')
PROGRAMAS = os.path.join(AQUI, 'programas')
PARTOOL = os.path.join(PROGRAMAS, 'ParTool', 'ParTool.exe')
if not os.path.isfile(PARTOOL):
    print('Falta ParTool.exe. Lee «1 - LEEME PRIMERO - Instalar ParTool.txt». Descarga directa:'); print('https://github.com/Kaplas80/ParManager/releases/download/v1.3.4/v1.3.4-windows-x64.zip')
    print('Descomprímelo y copia ParTool.exe en: ' + os.path.dirname(PARTOOL))
    input('Pulsa Intro para salir...'); sys.exit(1)
REARMP = os.path.join(PROGRAMAS, 'reARMP', 'reARMP.py')
CSV_TEXTOS = os.path.join(TRABAJO, 'textos.csv')
EXTRAIDO = os.path.join(TRABAJO, 'extraido_en')
OBRA = os.path.join(TRABAJO, 'obra')
TRADUCCIONES = os.path.join(DATOS, 'traducciones.json')
CORTAS = os.path.join(DATOS, 'cortas.json')
DEVIL_ES = os.path.join(DATOS, 'devil.json')

# ---------------------------------------------------------------- qué archivos del juego se tocan
# carpeta extraída -> archivo .par del juego (relativo a data). Los mismos que el proyecto.
PAR_FILES = {
    'wdr_par_en_wdr': 'wdr_par_en/wdr.par',
    'wdr_par_en_common': 'wdr_par_en/common.par',
    'staypar_stay_en': 'staypar/stay_en.par',
    'bootpar_boot_en': 'bootpar/boot_en.par',
    'auth_subtitle': 'auth/subtitle.par',
    'auth_telop_auth_telop_en': 'auth_telop/auth_telop_en.par',
    '2dpar_ui_en': '2dpar/ui_en.par',
    '2dpar_sprite_en': '2dpar/sprite_en.par',
    'pausepar_pause_en': 'pausepar/pause_en.par',
    'pausepar_title_menu_en': 'pausepar/title_menu_en.par',
    'pausepar_movie_en': 'pausepar/movie_en.par',
    'pausepar_kigae_en': 'pausepar/kigae_en.par',
    'pausepar_idol_work_en': 'pausepar/idol_work_en.par',
    'pausepar_snowball_en': 'pausepar/snowball_en.par',
    'pausepar_staffroll_en': 'pausepar/staffroll_en.par',
    'pausepar_taxi_en': 'pausepar/taxi_en.par',
    'pausepar_tougijyo_en': 'pausepar/tougijyo_en.par',
    'minigame_en_karaoke': 'minigame_en/karaoke.par',
    'minigame_en_karaoke_e': 'minigame_en/karaoke_e.par',
    }
# .par que además llevan las IMÁGENES ya traducidas: su base es la versión que instala el paquete
# (..\archivos\data), no el original en inglés, para no perderlas. Solo se cambian los textos.
IMAGE_PARS = {'2dpar/ui_en.par', '2dpar/sprite_en.par', 'pausepar/pause_en.par', 'bootpar/boot_en.par',
              'pausepar/idol_work_en.par', 'pausepar/movie_en.par', 'pausepar/taxi_en.par',
              'pausepar/title_menu_en.par', 'pausepar/tougijyo_en.par'}
# carpetas del juego que no son .par: sus archivos sueltos se cambian y se copian tal cual
SUELTOS = ('scenario_en', 'minigame_en')
# la fuente: el paquete ya trae la versión con las tildes, la ñ y el ¿ ¡ bien dibujados
FUENTE = 'fontpar/font_hd_en.par'
# nombres internos que el juego no muestra: no se tocan
EXCLUIR = ('scenario_en/scenario2.bin', 'scenario_en/scenario_state.bin', 'scenario_en/player_pos.bin',
           'minigame_en/live_btl/live_btl_AI.bin', 'minigame_en/baseball/BaseBallPitcher.bin')
# columnas de tabla que son CÓDIGO interno (cambiarlas cierra el juego)
COL_INTERNAS = {('battle_condition.bin', '条件'), ('effect_low_list.bin', 'EID_AFTER'), ('effect_low_list.bin', 'EID_BEFORE'),
    ('item.bin', 'ID'), ('item.bin', 'PRESENT'), ('drive_mission.bin', 'GOAL'), ('drive_mission.bin', 'MODEL'),
    ('tips_tutorial.bin', 'ENUM'), ('zactparam.bin', 'ROBJID'), ('aiming_param.bin', 'CATEGORY'),
    ('continuepoint.bin', 'SCENARIO'), ('restaurant_menu.bin', 'NAME'), ('restaurant_menu.bin', 'DECIDE'),
    ('drive_tutorial.bin', 'TYPE'), ('drive_camera.bin', 'NAME'), ('live_event.bin', 'MISSION'),
    ('live_btl_point.bin', 'MISSION'), ('EncountTable_1.bin', 'CATEGORY'), ('EncountTable_2.bin', 'CATEGORY'),
    ('EncountTable_3.bin', 'CATEGORY'), ('EncountTable_4.bin', 'CATEGORY'), ('fishing_river_motion.bin', 'NAME'),
    ('dance_battle.bin', 'NAME'), ('mission_snow.bin', 'EXPLANATION'), ('drive_parts.bin', 'CATEGORY')}
CJK = re.compile('[぀-ヿ一-鿿]')
# (21-10) El juego dibuja la «¡» en la casilla de la «½» y la «í» en la de la «» ( grave) porque la tabla de la fuente
# les da un ancho fijo enorme. Los textos se escriben con esos códigos (herramientas\aplicar.py y devil.py).
LETRAS = str.maketrans({'¡': '½', 'í': '`', 'Í': '|'})
PRUEBA = '--prueba' in sys.argv


# ---------------------------------------------------------------- utilidades
def rm_tree(p):
    """Borra una carpeta (o un archivo) aunque esté en solo lectura."""
    if not os.path.exists(p): return
    if os.path.islink(p) or os.path.isfile(p):
        try: os.chmod(p, 0o777)
        except OSError: pass
        os.unlink(p); return
    for root, dirs, files in os.walk(p, topdown=False):
        for d in dirs:
            try: os.chmod(os.path.join(root, d), 0o777)
            except OSError: pass
        for f in files:
            fp = os.path.join(root, f)
            try: os.chmod(fp, 0o777)
            except OSError: pass
            os.unlink(fp)
        try: os.rmdir(root)
        except OSError: pass


def partool(*a):
    """ParTool (programas\\ParTool\\ParTool.exe): extract | add."""
    for intento in range(4):
        if a[0] == 'extract' and os.path.isdir(a[-1]): rm_tree(a[-1])
        r = subprocess.run([PARTOOL, *a], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode == 0 and b'ERROR' not in r.stdout.upper(): return
    raise RuntimeError(f'ParTool {a[0]} falló: {r.stdout[-300:]!r} {r.stderr[-300:]!r}')


def norm(t):
    """El juego usa \\r\\n; las hojas de traducción usan \\n."""
    return t.replace('\r\n', '\n')


def par_sellos(par):
    """Fecha que tiene cada archivo dentro de un .par: {ruta interna: segundos desde 1970}.
    El .par guarda la fecha de cada archivo (la HORA LOCAL del archivo, leída como si fuera UTC) y
    ParTool la usa al rearmarlo: si no se respeta, el .par sale distinto aunque el texto sea el mismo."""
    r = subprocess.run([PARTOOL, 'list', par], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    salida = {}
    for linea in r.stdout.split(b'\n'):
        partes = linea.split(b'\t')
        if len(partes) < 3: continue
        ruta = partes[0].decode('cp932', 'replace').strip()
        if not ruta.startswith('/'): continue
        pedazos = ruta.split('/', 2)                   # /<nombre>.par/<ruta interna>
        if len(pedazos) < 3: continue
        interna = pedazos[2]
        if interna.startswith('./'): interna = interna[2:]
        interna = interna.rstrip('*')
        fecha = partes[2]
        m = re.match(rb'(\d+)/(\d+)/(\d+)\s+(\d+):(\d+):(\d+)', fecha)
        if not m: continue
        d, mes, y, h, mi, s = (int(x) for x in m.groups())
        h = h % 12 + (12 if b'p.' in fecha else 0)      # ParTool lo enseña en formato de 12 horas
        salida[interna] = calendar.timegm((y, mes, d, h, mi, s, 0, 0, 0))
    return salida


def mtime_para(v):
    """El instante que hay que ponerle a un archivo para que el .par guarde ese valor: el .par guarda
    la hora local del archivo leída como si fuera UTC, así que se busca el instante con esa hora local."""
    g = list(time.gmtime(v))
    for isdst in (-1, 0, 1):
        t = time.mktime(time.struct_time(g[:8] + [isdst]))
        if t == -1: continue
        if tuple(time.localtime(t)[:6]) == tuple(g[:6]): return int(t)
    return int(time.mktime(time.struct_time(g[:8] + [0])))


def poner_fecha(destino, v):
    """Pone al archivo la fecha que tenía en el .par (para que el .par rearmado sea idéntico)."""
    if v is None: return
    try:
        t = mtime_para(v)
        os.utime(destino, (t, t))
    except (OSError, OverflowError, ValueError):
        pass


def json_leer(ruta):
    if not os.path.exists(ruta): return {}
    return json.load(open(ruta, encoding='utf-8'))


# ---------------------------------------------------------------- formatos (copiados de msg_y5.py y tabla_y5.py)
def msg_leer(b):
    """Formato .msg de Yakuza 5 (big endian)."""
    secs = []; o = 0x18
    while True:
        z, off, cnt, a, c = struct.unpack('>IIHHI', b[o:o + 16])
        if z != 0 or off < 0x18 or off > len(b): break
        secs.append((o, off, cnt)); o += 16
        if o >= secs[0][1]: break
    regs = []
    for so, off, cnt in secs:
        for i in range(cnt):
            r = off + 12 * i
            L, nf, y, t, p = struct.unpack('>HBBII', b[r:r + 12])
            funcs = [(p + 16 * k, b[p + 16 * k:p + 16 * k + 16]) for k in range(nf)]
            regs.append(dict(reg=r, L=L, nf=nf, y=y, t=t, p=p, texto=b[t:t + L], funcs=funcs))
    return secs, regs


MAGIA = b'\x20\x07\x03\x19'
NUL = b'\x00'


def tabla_es_tabla(b):
    return b[:4] == MAGIA and len(b) > 16


def tabla_leer(b):
    nc, nf = struct.unpack('>II', b[4:12]); cols = []; o = 0x10 + 64 * nc
    for i in range(nc):
        h = 0x10 + 64 * i; nombre = b[h:h + 48].split(NUL)[0].decode('cp932', 'replace')
        tipo, cuenta, tam, z = struct.unpack('>4I', b[h + 48:h + 64]); d = b[o:o + tam]; o += tam
        c = dict(nombre=nombre, tipo=tipo, cuenta=cuenta, z=z, crudo=d, cab=b[h:h + 48])
        try:
            if tipo in (0, 3):
                p = d.split(NUL, cuenta); assert len(p) == cuenta + 1 and set(p[-1]) <= {0}, 'faltan textos'
                c['filas'] = p[:cuenta]; c['resto'] = p[-1]
            elif tipo in (2, 5):
                v = []; q = 0
                for k in range(cuenta):
                    fila = struct.unpack('>H', d[q:q + 2])[0]; e = d.index(NUL, q + 2); v.append([fila, d[q + 2:e]]); q = e + 1
                assert set(d[q:]) <= {0}; c['dispersa'] = v; c['resto'] = d[q:]
            elif tipo == 1:
                p = d.split(NUL, cuenta); assert len(p[cuenta]) == nf
                c['dicc'] = p[:cuenta]; c['indices'] = p[cuenta]
        except (AssertionError, ValueError, struct.error):
            for k in ('filas', 'dispersa', 'dicc', 'resto', 'indices'): c.pop(k, None)
        cols.append(c)
    assert o == len(b), (o, len(b))
    return dict(nc=nc, nf=nf, cab=b[:16], cols=cols)


def tabla_escribir(t):
    cab = bytearray(t['cab']); datos = bytearray()
    for c in t['cols']:
        if 'filas' in c: d = b''.join(x + NUL for x in c['filas']) + c['resto']
        elif 'dispersa' in c: d = b''.join(struct.pack('>H', f) + x + NUL for f, x in c['dispersa']) + c['resto']
        elif 'dicc' in c: d = b''.join(x + NUL for x in c['dicc']) + c['indices']
        else: d = c['crudo']
        cab += c['cab'] + struct.pack('>4I', c['tipo'], c['cuenta'], len(d), c['z']); datos += d
    return bytes(cab + datos)


def tabla_textos(t):
    for c in t['cols']:
        if 'filas' in c:
            for i, x in enumerate(c['filas']): yield c['nombre'], ('f', i), x
        elif 'dispersa' in c:
            for i, (f, x) in enumerate(c['dispersa']): yield c['nombre'], ('d', i), x
        elif 'dicc' in c:
            for i, x in enumerate(c['dicc']): yield c['nombre'], ('k', i), x


def tabla_poner(t, col, clave, valor):
    for c in t['cols']:
        if c['nombre'] != col: continue
        k, i = clave
        if k == 'f': c['filas'][i] = valor
        elif k == 'd': c['dispersa'][i][1] = valor
        elif k == 'k': c['dicc'][i] = valor
        return
    raise KeyError(col)


# ---------------------------------------------------------------- qué es texto (copiado de extraer.py y devil.py)
def es_texto(s):
    """¿Es una frase o nombre para traducir (y no un identificador, ruta o número)?"""
    if not re.search(r'[A-Za-z]{2}', s): return False
    if re.fullmatch(r'[a-z0-9_./\-]+', s) or re.fullmatch(r'[A-Z0-9_./\-]+', s): return False
    if re.search(r'\.(dds|bin|gmt|par|wav|adx|hca|usm|tex|txt|csv|cmt|bux|sbb)\b', s, re.I): return False
    if re.fullmatch(r'[A-Za-z]+[_][A-Za-z0-9_]*', s): return False
    if '�' in s: return False
    if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', s): return False
    if '_' in s and ' ' not in s: return False
    if not re.search(r'[aeiouyAEIOUY]', s): return False
    return True


def es_texto_devil(s):
    """Lo que lee el jugador en los mensajes del sistema."""
    if not re.search(r'[A-Za-z]{2,}', s) or (s.startswith('(') and s.endswith(')')): return False
    if re.fullmatch(r'[A-Za-z0-9_./\-:#]+', s) and ('_' in s or '/' in s or '.' in s or s.islower() or s.isupper() and len(s) <= 4): return False
    if s in ('message', 'Display Name', 'TEST', 'test'): return False
    return True


# ---------------------------------------------------------------- el juego original en inglés
def buscar_juego_steam():
    """La carpeta data del juego (como en instalar.ps1)."""
    import winreg
    carpetas = []
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam') as k:
            steam = winreg.QueryValueEx(k, 'SteamPath')[0]
        carpetas.append(steam)
        vdf = os.path.join(steam, 'steamapps', 'libraryfolders.vdf')
        if os.path.exists(vdf):
            carpetas += [m.replace('\\\\', '\\') for m in re.findall(r'"path"\s+"([^"]+)"', open(vdf, encoding='utf-8').read())]
    except OSError:
        pass
    for c in carpetas:
        d = os.path.join(c, 'steamapps', 'common', 'Yakuza 5', 'main', 'data')
        if os.path.exists(os.path.join(d, 'wdr_par_en', 'wdr.par')): return d
    return None


def origen_ingles():
    """Carpeta con los archivos ORIGINALES en inglés del juego."""
    if '--ingles' in sys.argv:
        d = sys.argv[sys.argv.index('--ingles') + 1]
    elif os.path.exists(os.path.join(PAQUETE, 'respaldo_original', 'wdr_par_en', 'wdr.par')):
        d = os.path.join(PAQUETE, 'respaldo_original')
    else:
        d = buscar_juego_steam()
        if not d:
            sys.exit('No encontré el juego de Yakuza 5.\n'
                     'Usa:  python herramienta_traduccion.py extraer --ingles "<carpeta data del juego en inglés>"')
        if os.path.exists(os.path.join(d, 'traduccion_es_version.txt')):
            sys.exit('El juego de Steam ya tiene la traducción puesta y no hay «respaldo_original» junto al instalador.\n'
                     'Quita la traducción (INSTALAR o QUITAR.bat, opción 2) o usa Steam > Propiedades > Archivos '
                     'instalados > Verificar integridad.')
    if not os.path.isdir(d):
        sys.exit(f'No existe la carpeta: {d}')
    print(f'Inglés original: {d}')
    return d


# ---------------------------------------------------------------- extraer
def celdas_de(b, rel):
    """Celdas de texto de un archivo ya extraído: [{f, k, c?, t}]."""
    celdas = []
    if rel.endswith('.msg'):
        secs, regs = msg_leer(b)
        for r in regs:
            t = r['texto'].decode('utf-8', 'replace')
            if es_texto(t): celdas.append(dict(f='msg', k=r['reg'], t=t))
    elif rel.endswith('.csv') and 'auth_subtitle' in rel:
        filas = b.decode('utf-16').split('\r\n')
        for i, l in enumerate(filas):
            c = l.split('\t')
            if len(c) > 3 and es_texto(c[2]): celdas.append(dict(f='sub', k=i, t=c[2]))
    elif rel.endswith('.bin') and tabla_es_tabla(b):
        t = tabla_leer(b)
        porcol = collections.defaultdict(list)
        for col, clave, x in tabla_textos(t): porcol[col].append((clave, x.decode('utf-8', 'replace')))
        for col, v in porcol.items():
            txt = [x for _, x in v if es_texto(x)]
            if not txt: continue
            for clave, x in v:
                if es_texto(x): celdas.append(dict(f='tabla', c=col, k=list(clave), t=x))
    elif rel.endswith('.bin') and os.path.basename(rel).startswith('pac_'):
        for m in re.finditer(rb'(?<=\x00)[^\x00]{2,}(?=\x00)', b):
            x = m.group().decode('utf-8', 'replace')
            if es_texto(x) and re.search(r'[a-z]{2}', x) and (' ' in x or re.search(r'[.!?)]$', x) or len(x) >= 5):
                celdas.append(dict(f='pac', k=m.start(), t=x))
    elif rel.endswith('.bin'):
        al = set(struct.unpack('>I', b[i:i + 4])[0] for i in range(0, len(b) - 3, 4))
        for m in re.finditer(rb'(?<=\x00)[^\x00]{2,}(?=\x00)', b):
            if m.start() not in al: continue
            x = m.group().decode('utf-8', 'replace')
            if es_texto(x): celdas.append(dict(f='ptr', k=m.start(), t=x))
    return celdas


def extraer_mensajes_sistema(d_en):
    """Los mensajes del sistema (data\\db.devil\\en\\msg.bin): cadenas con UN puntero."""
    b = open(os.path.join(d_en, 'db.devil', 'en', 'msg.bin'), 'rb').read()
    out = []
    for m in re.finditer(rb'(?<=\x00)[^\x00]{2,}?(?=\x00)', b):
        try: s = m.group().decode('utf-8')
        except UnicodeDecodeError: continue
        if not s.isprintable() or not es_texto_devil(s): continue
        ptrs = [x.start() for x in re.finditer(re.escape(struct.pack('<I', m.start())), b) if x.start() % 4 == 0]
        if len(ptrs) == 1: out.append(dict(f='devil', k=m.start(), ptr=ptrs[0], t=s))
    return out


def extraer():
    d_en = origen_ingles()
    os.makedirs(TRABAJO, exist_ok=True)
    rm_tree(EXTRAIDO); os.makedirs(EXTRAIDO)
    print('Abriendo los .par del juego (ParTool)...')
    for raiz, par in PAR_FILES.items():
        p = os.path.join(d_en, par)
        if not os.path.exists(p):
            print('  (no existe en este juego, se salta)', par); continue
        partool('extract', p, os.path.join(EXTRAIDO, raiz))
        print('  ', par)
    for suelto in SUELTOS:
        src = os.path.join(d_en, suelto)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(EXTRAIDO, suelto), dirs_exist_ok=True)
            print('  ', suelto + '/')
    print('Leyendo los textos...')
    unicos = collections.OrderedDict()          # inglés -> {es, donde, veces}

    def anotar(en, donde):
        k = norm(en); u = unicos.setdefault(k, {'es': '', 'donde': donde, 'veces': 0})
        u['veces'] += 1

    nceldas = 0
    for dp, _, fs in os.walk(EXTRAIDO):
        for f in sorted(fs):
            p = os.path.join(dp, f); rel = os.path.relpath(p, EXTRAIDO).replace('\\', '/')
            if rel in EXCLUIR: continue
            b = open(p, 'rb').read()
            for c in celdas_de(b, rel):
                if c['f'] == 'tabla' and ((rel.split('/')[-1], c['c']) in COL_INTERNAS or c['c'].startswith('モ')): continue
                if CJK.search(c['t']): continue
                donde = c['f'] + ' | ' + rel + ((':' + c['c']) if 'c' in c else (':' + str(c['k'])))
                anotar(c['t'], donde); nceldas += 1
    for c in extraer_mensajes_sistema(d_en):
        anotar(c['t'], 'devil | db.devil/en/msg.bin:' + str(c['k'])); nceldas += 1
    # rellenar el español con la traducción actual
    tr = json_leer(TRADUCCIONES)
    rellenas = 0
    for k, u in unicos.items():
        if tr.get(k, '').strip():
            u['es'] = tr[k]; rellenas += 1
    with open(CSV_TEXTOS, 'w', encoding='utf-8-sig', newline='') as fh:
        w = csv.writer(fh, delimiter=';', quoting=csv.QUOTE_ALL)
        w.writerow(['id', 'donde', 'veces', 'ingles', 'espanol'])
        for i, (en, u) in enumerate(unicos.items()):
            w.writerow([i, u['donde'], u['veces'], en, u['es']])
    faltan = sum(1 for u in unicos.values() if not u['es'])
    print(f'\nListo: {len(unicos)} textos distintos en {CSV_TEXTOS}  ({nceldas} celdas)')
    print(f'  Español rellenado: {rellenas}   (sin traducción: {faltan})')


# ---------------------------------------------------------------- aplicar
def leer_csv():
    """La hoja de traducción: inglés -> español (lo que escribió el usuario)."""
    if not os.path.exists(CSV_TEXTOS):
        sys.exit('Primero ejecuta «extraer» (no existe trabajo\\textos.csv).')
    tr = {}
    with open(CSV_TEXTOS, encoding='utf-8-sig', newline='') as fh:
        primera = fh.readline(); fh.seek(0)
        sep = ';' if primera.count(';') >= primera.count(',') else ','
        for f in csv.DictReader(fh, delimiter=sep):
            es = norm(f.get('espanol') or '')
            if es.strip(): tr[norm(f.get('ingles') or '')] = es
    return tr


def es_de(t, gen, maxb=None, corto=None):
    """La traducción del texto inglés t, o None si no hay."""
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


ETQ = re.compile(r'<[^>]*>')


def visibles(t):
    return ETQ.sub('', t.replace('\r\n', '\n'))


def pos_etiquetas(t):
    """Posiciones (en letras visibles) de cada etiqueta, en orden."""
    p = []; v = 0; i = 0; s = t.replace('\r\n', '\n')
    while i < len(s):
        if s[i] == '<':
            j = s.find('>', i)
            if j > 0: p.append(v); i = j + 1; continue
        v += 1; i += 1
    return p


PUNT = '.,!?…:;)」'


def remapear(pos, en, es, tipo):
    """Posición de una función (pausa, color, fin) en el inglés -> en el español."""
    ve, vs = len(visibles(en)), len(visibles(es))
    if pos == 0: return 0
    if pos >= ve: return vs
    te, ts = pos_etiquetas(en), pos_etiquetas(es)
    if pos in te and len(te) == len(ts): return ts[te.index(pos)]
    p = int(round(pos * vs / max(1, ve)))
    if tipo in (0x0200, 0x020a):
        txt = visibles(es); cand = [i + 1 for i, c in enumerate(txt) if c in PUNT]
        if cand:
            c = min(cand, key=lambda x: abs(x - p))
            if abs(c - p) <= max(6, vs // 6): p = c
    return max(0, min(vs, p))


def aplicar_msg(b, celdas, gen, stats):
    """Diálogos .msg: el texto nuevo va al final del archivo y el registro apunta allí."""
    b = bytearray(b); secs, regs = msg_leer(bytes(b))
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


def aplicar_sub(b, celdas, gen, stats):
    """Subtítulos: CSV en UTF-16, la traducción va en la columna 3."""
    filas = b.decode('utf-16').split('\r\n')
    for c in celdas:
        col = filas[c['k']].split('\t'); es = es_de(col[2], gen)
        if es is None: stats['sub_sin'] += 1; continue
        col[2] = es.replace('\r\n', '\n'); filas[c['k']] = '\t'.join(col); stats['sub'] += 1
    return '\r\n'.join(filas).encode('utf-16')


def aplicar_tabla(b, celdas, gen, stats):
    """Tablas .bin (cabecera 20 07 03 19)."""
    t = tabla_leer(b)
    for c in celdas:
        es = es_de(c['t'], gen)
        if es is None: stats['tabla_sin'] += 1; continue
        tabla_poner(t, c['c'], tuple(c['k']), es.encode('utf-8')); stats['tabla'] += 1
    return tabla_escribir(t)


def aplicar_ptr(b, celdas, gen, stats):
    """Archivos con punteros absolutos (big endian, alineados a 4): el texto va al final."""
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


def aplicar_pac(b, celdas, gen, corto, stats):
    """Guiones en línea (pac): el texto va en su sitio, sin pasar del largo original."""
    b = bytearray(b)
    for c in celdas:
        n = len(c['t'].encode('utf-8')); es = es_de(c['t'], gen, n, corto)
        if es is None: stats['pac_sin'] += 1; continue
        x = es.encode('utf-8'); b[c['k']:c['k'] + n] = x + b'\0' * (n - len(x)); stats['pac'] += 1
    return bytes(b)


def aplicar_mensajes_sistema(d_en, tr):
    """data\\db.devil\\en\\msg.bin: cada cadena tiene un puntero; el texto va al final."""
    p = os.path.join(d_en, 'db.devil', 'en', 'msg.bin')
    if not os.path.exists(p): return None
    base = json_leer(TRADUCCIONES)          # el mapa principal (para saber si el usuario cambió algo)
    devil = json_leer(DEVIL_ES)             # la traducción de los mensajes del sistema
    original = open(p, 'rb').read()
    # primero se(localizan) las cadenas y su puntero en el archivo ORIGINAL
    encontrados = []
    for m in re.finditer(rb'(?<=\x00)[^\x00]{2,}?(?=\x00)', original):
        try: s = m.group().decode('utf-8')
        except UnicodeDecodeError: continue
        if not s.isprintable() or not es_texto_devil(s): continue
        ptrs = [x.start() for x in re.finditer(re.escape(struct.pack('<I', m.start())), original) if x.start() % 4 == 0]
        if len(ptrs) == 1: encontrados.append((s, ptrs[0]))
    b = bytearray(original); cambios = 0
    for s, ptr in encontrados:
        k = norm(s)
        es = tr.get(k)
        if es is not None and es == base.get(k): es = None      # no lo cambió el usuario: usa el del sistema
        if es is None: es = devil.get(k)
        if es is None or es == s: continue
        while len(b) % 4: b.append(0)
        nuevo = len(b); b += es.translate(LETRAS).encode('utf-8') + b'\0'
        struct.pack_into('<I', b, ptr, nuevo); cambios += 1
    if not cambios: return None
    while len(b) % 16: b.append(0)
    return bytes(b)


def aplicar():
    d_en = origen_ingles()
    tr = leer_csv()
    if not os.path.isdir(EXTRAIDO):
        sys.exit('Primero ejecuta «extraer» (falta trabajo\\extraido_en).')
    rm_tree(SALIDA); os.makedirs(SALIDA)
    rm_tree(OBRA); os.makedirs(OBRA)
    print('Aplicando las traducciones...')
    porarch = collections.defaultdict(list)
    for dp, _, fs in os.walk(EXTRAIDO):
        for f in sorted(fs):
            p = os.path.join(dp, f); rel = os.path.relpath(p, EXTRAIDO).replace('\\', '/')
            if rel in EXCLUIR: continue
            b = open(p, 'rb').read()
            for c in celdas_de(b, rel):
                if c['f'] == 'tabla' and ((rel.split('/')[-1], c['c']) in COL_INTERNAS or c['c'].startswith('モ')): continue
                if CJK.search(c['t']): continue
                c['a'] = rel
                porarch[rel].append(c)
    stats = collections.Counter()
    tocados = collections.defaultdict(list)          # carpeta extraída -> rutas relativas cambiadas
    for rel, celdas in porarch.items():
        p = os.path.join(EXTRAIDO, rel)
        b = open(p, 'rb').read(); f = celdas[0]['f']
        if f == 'msg': n = aplicar_msg(b, celdas, tr, stats)
        elif f == 'sub': n = aplicar_sub(b, celdas, tr, stats)
        elif f == 'tabla': n = aplicar_tabla(b, celdas, tr, stats)
        elif f == 'ptr': n = aplicar_ptr(b, celdas, tr, stats)
        elif f == 'pac': n = aplicar_pac(b, celdas, tr, json_leer(CORTAS), stats)
        else: continue
        if n == b: continue
        dest = os.path.join(OBRA, rel); os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, 'wb').write(n)
        tocados[rel.split('/')[0]].append(rel)
    print('  ', dict(stats))
    # rearmar: los .par del juego (ParTool «add») y los archivos sueltos
    salida_data = os.path.join(SALIDA, 'data')
    for raiz in sorted(tocados):
        if raiz in PAR_FILES:
            par = PAR_FILES[raiz]
            ref = os.path.join(PAQUETE, 'archivos', 'data', par)      # el .par del paquete (la referencia)
            # base: la del paquete si lleva las imágenes ya traducidas; si no, el original en inglés
            base = ref if par in IMAGE_PARS else os.path.join(d_en, par)
            if not os.path.exists(base): base = os.path.join(d_en, par)
            if not os.path.exists(base): continue
            # las fechas de cada archivo van dentro del .par: se copian las del paquete (si no, sale distinto)
            sellos = par_sellos(ref) if os.path.exists(ref) else {}
            if not sellos: sellos = par_sellos(base)
            for rel in tocados[raiz]:
                interna = rel[len(raiz) + 1:]
                poner_fecha(os.path.join(OBRA, raiz, interna.replace('/', os.sep)), sellos.get(interna))
            out = os.path.join(salida_data, par)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            partool('add', base, os.path.join(OBRA, raiz), out)
            print('  par', par, len(tocados[raiz]), 'archivos con texto')
        elif raiz in SUELTOS:
            for rel in tocados[raiz]:
                out = os.path.join(salida_data, rel); os.makedirs(os.path.dirname(out), exist_ok=True)
                shutil.copy(os.path.join(OBRA, rel), out)
            print('  ', raiz, len(tocados[raiz]), 'archivos sueltos')
        else:
            print('  AVISO: sin destino para', raiz, len(tocados[raiz]))
    # los .par que solo llevan imágenes (sin textos que cambiar): se copian tal cual del paquete
    for raiz, par in PAR_FILES.items():
        if raiz in tocados: continue
        ref = os.path.join(PAQUETE, 'archivos', 'data', par)
        if not os.path.exists(ref): continue
        out = os.path.join(salida_data, par); os.makedirs(os.path.dirname(out), exist_ok=True)
        shutil.copy(ref, out); print('  par', par, '(solo imágenes)')
    # los mensajes del sistema (van después de todo lo demás)
    nuevo = aplicar_mensajes_sistema(d_en, tr)
    if nuevo:
        out = os.path.join(salida_data, 'db.devil', 'en', 'msg.bin'); os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, 'wb').write(nuevo); print('  db.devil/en/msg.bin (mensajes del sistema)')
    # la fuente con las tildes, la ñ y el ¿ ¡ bien dibujados
    fuente = os.path.join(PAQUETE, 'archivos', 'data', FUENTE)
    if os.path.exists(fuente):
        out = os.path.join(salida_data, FUENTE); os.makedirs(os.path.dirname(out), exist_ok=True)
        shutil.copy(fuente, out); print('  ', FUENTE, '(la letra del juego)')
    rm_tree(OBRA)
    n = sum(len(fs) for _, _, fs in os.walk(salida_data))
    print(f'\nListo: {n} archivos en {SALIDA}')
    if '--a-archivos' in sys.argv:
        destino = os.path.join(PAQUETE, 'archivos', 'data')
        os.makedirs(destino, exist_ok=True)
        for dp, _, fs in os.walk(salida_data):
            for f in fs:
                s = os.path.join(dp, f); d = os.path.join(destino, os.path.relpath(s, salida_data))
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copy(s, d)
        print(f'Copiado encima de {destino}: ahora ejecuta «INSTALAR o QUITAR.bat» y elige 1.')
    else:
        print(f'Para probarlo, copia «salida\\data» encima de la carpeta «archivos\\data» y ejecuta el instalador.')


# ---------------------------------------------------------------- main
if __name__ == '__main__':
    orden = sys.argv[1] if len(sys.argv) > 1 else ''
    if orden == 'extraer': extraer()
    elif orden == 'aplicar': aplicar()
    else: print(__doc__)
