# -*- coding: utf-8 -*-
"""(31-10-2026, claude1) Mete la traducción de lo que extraer_extra.py sacó (nombres/opciones de .msg, subtítulos con
salto de línea entre comillas, msg_replacer.bin) ENCIMA de los archivos de una entrega ya armada (no toca Steam):
  python herramientas/aplicar_extra.py <data de la entrega base> <data de salida> [--prueba]
  nom  la cadena nueva va al final del .msg (alineada a 4) y se redirige su puntero u32 big endian de la tabla
  sub  se cambia el texto entre comillas de la fila (el salto \\r\\n de dentro se mantiene)
  rep  como devil.py: cadena al final del archivo y puntero u32 little endian
  --prueba: «ñ·» + inglés, para ver en el juego que se lee lo cambiado sin esperar a la traducción."""
import collections, glob, json, os, re, shutil, struct, subprocess, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
L = os.path.join(T, 'lotes'); PT = os.path.join(R, 'herramientas', 'partool', 'ParTool.exe')
TMP = os.path.join(T, 'extra', 'tmp')
PRUEBA = '--prueba' in sys.argv
LETRAS = str.maketrans({'¡': '½', 'í': '`', 'Í': '|'})      # = aplicar.py (letra del juego)
norm = lambda s: re.sub(r'\s+', ' ', re.sub(r'<[^>]*>', '', s)).strip()


def traducciones():
    gen = {}
    for f in sorted(glob.glob(os.path.join(L, 'lote_???.json'))):
        fe = f[:-5] + '_es.json'
        if f.endswith('lote_310.json') or not os.path.exists(fe): continue      # 310 = versiones cortas de guion
        es = json.load(open(fe, encoding='utf-8'))
        for x in json.load(open(f, encoding='utf-8')):
            t = es.get(str(x['id']))
            if isinstance(t, str) and t.strip(): gen.setdefault(norm(x['en']), t)
    return gen


def es_de(t, gen):
    if PRUEBA: return 'ñ·' + t
    r = gen.get(norm(t))
    if r is None: return None
    r = r.replace('\r\n', '\n')
    if '\r\n' in t: r = r.replace('\n', '\r\n')
    if t[:1] in '○□△●■' and r[:1] != t[:1]: r = t[0] + r.lstrip('○□△●■')       # signo de opción delante
    return r.translate(LETRAS)


def partool(*a):
    r = subprocess.run([PT, *a], stdin=subprocess.DEVNULL, capture_output=True)
    if r.returncode != 0 or b'ERROR' in r.stdout.upper(): raise RuntimeError(f'ParTool {a[0]}: {r.stdout[-300:]!r}')


def anadir(b, s, alin=4):
    while len(b) % alin: b += b'\0'
    off = len(b); b += s.encode('utf-8') + b'\0'
    return off


def main():
    base, sal = sys.argv[1], sys.argv[2]
    xs = json.load(open(os.path.join(T, 'extra', 'textos.json'), encoding='utf-8'))
    gen = traducciones(); st = collections.Counter(); sin = collections.Counter()
    por = collections.defaultdict(list)
    for x in xs: por[(x['f'], x['a'])].append(x)
    shutil.rmtree(TMP, ignore_errors=True)
    # --- .msg dentro de wdr.par / common.par ---
    PARES = {'wdr_par_en_wdr': 'wdr_par_en/wdr.par', 'wdr_par_en_common': 'wdr_par_en/common.par'}
    for raiz, par in PARES.items():
        cosas = {a: v for (f, a), v in por.items() if f == 'nom' and a.startswith(raiz + '/')}
        if not cosas: continue
        full = os.path.join(TMP, raiz + '_full'); add = os.path.join(TMP, raiz + '_add')
        partool('extract', os.path.join(base, par), full)
        for a, v in cosas.items():
            rel = a[len(raiz) + 1:]; p = os.path.join(full, rel)
            b = bytearray(open(p, 'rb').read()); cambio = False
            for x in v:
                es = es_de(x['t'], gen)
                if es is None: sin['nom'] += 1; continue
                q = struct.unpack('>I', b[x['ptr']:x['ptr'] + 4])[0]
                actual = b[q:b.index(b'\0', q)].decode('utf-8', 'replace')
                if actual != x['t']: st['nom_distinto'] += 1; continue          # no es el inglés esperado: no tocar
                struct.pack_into('>I', b, x['ptr'], anadir(b, es)); st['nom'] += 1; cambio = True
            if cambio:
                while len(b) % 4: b += b'\0'
                d = os.path.join(add, rel); os.makedirs(os.path.dirname(d), exist_ok=True); open(d, 'wb').write(b)
        if os.path.isdir(add):
            o = os.path.join(sal, par); os.makedirs(os.path.dirname(o), exist_ok=True)
            partool('add', os.path.join(base, par), add, o); print('par', par)
    # --- subtítulos ---
    cosas = {a: v for (f, a), v in por.items() if f == 'sub'}
    if cosas:
        full = os.path.join(TMP, 'sub_full'); add = os.path.join(TMP, 'sub_add')
        partool('extract', os.path.join(base, 'auth/subtitle.par'), full)
        for a in cosas:
            ps = glob.glob(os.path.join(full, '**', a), recursive=True)
            if len(ps) != 1: st['sub_sin_archivo'] += 1; continue
            raw = open(ps[0], 'rb').read(); tx = raw.decode('utf-16'); n0 = st['sub']

            def cambia(m):
                es = es_de(m.group(2), gen)
                if es is None: sin['sub'] += 1; return m.group(0)
                st['sub'] += 1      # comilla de dentro = "" (como en el CSV original)
                return m.group(1) + '"' + es.replace('""', '"').replace('"', '""') + '"\t'
            tx2 = re.sub(r'((?:^|\r\n)\d+\t\d+\t)"(.*?)"\t', cambia, tx, flags=re.S)
            if st['sub'] > n0:
                assert tx2.count('\r\n') == tx.count('\r\n'), a                  # mismas filas y renglones
                d = os.path.join(add, os.path.relpath(ps[0], full)); os.makedirs(os.path.dirname(d), exist_ok=True)
                open(d, 'wb').write(tx2.encode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else tx2.encode('utf-16-le'))
        if os.path.isdir(add):
            o = os.path.join(sal, 'auth/subtitle.par'); os.makedirs(os.path.dirname(o), exist_ok=True)
            partool('add', os.path.join(base, 'auth/subtitle.par'), add, o); print('par auth/subtitle.par')
    # --- msg_replacer.bin ---
    v = por.get(('rep', 'db.devil/en/msg_replacer.bin'))
    if v:
        src = os.path.join(base, 'db.devil/en/msg_replacer.bin')
        if not os.path.exists(src): src = os.path.join(T, 'db_en', 'msg_replacer.bin')     # la v1.0.1 no lo traía
        b = bytearray(open(src, 'rb').read()); b0 = bytes(b)

        def cadena_en(q):
            if not 0 < q < len(b0) or b0[q - 1] != 0: return False
            try: t = b0[q:b0.index(b'\0', q)].decode('utf-8')
            except (ValueError, UnicodeDecodeError): return False
            return bool(t) and all(c.isprintable() or c in '\r\n\t' for c in t)
        for x in v:
            es = es_de(x['t'], gen)
            if es is None: sin['rep'] += 1; continue
            if es == x['t']: st['rep_igual'] += 1; continue                       # igual: no hace falta tocar nada
            # (01-11) el «puntero» se buscó por su valor: puede ser OTRO dato que vale lo mismo. «Po» lo apuntaba la
            # cabecera de una subtabla (inicio de su zona de cadenas) y cambiarla cerraba el juego al arrancar. Un
            # puntero de verdad está en una tabla de punteros: el de al lado también apunta a una cadena.
            p = x['ptr']; vec = [struct.unpack('<I', b0[q:q + 4])[0] for q in (p - 4, p + 4) if 0 <= q <= len(b0) - 4]
            if not any(cadena_en(q) for q in vec): st['rep_no_puntero'] += 1; continue
            if struct.unpack('<I', b[x['ptr']:x['ptr'] + 4])[0] != x['off']: st['rep_distinto'] += 1; continue
            struct.pack_into('<I', b, x['ptr'], anadir(b, es)); st['rep'] += 1
        while len(b) % 16: b += b'\0'
        o = os.path.join(sal, 'db.devil/en/msg_replacer.bin'); os.makedirs(os.path.dirname(o), exist_ok=True)
        open(o, 'wb').write(b); print('db.devil/en/msg_replacer.bin')
    print('puestos', dict(st), '| sin traducción todavía', dict(sin))


if __name__ == '__main__': main()
