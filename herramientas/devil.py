# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Tablas ARMP v2 de data/db.devil/en (msg.bin = mensajes del sistema: guardar, regalos
recibidos, errores; msg_replacer.bin = nombres de enemigos y otros reemplazos). Se descubrió en la revisión final que
no entraban en la traducción (formato distinto de las tablas 20 07 03 19).
Formato: cada cadena UTF-8 terminada en 0 tiene UN puntero u32 LITTLE endian (offset absoluto) en la tabla -> como el
método «ptr» de aplicar.py: el español se añade al final del archivo y se redirige el puntero.
  python herramientas/devil.py extraer     -> trabajo/devil/textos.json (cadena, archivo, offset, puntero)
  python herramientas/devil.py traducir    -> trabajo/devil/es.json (frases del juego ya traducidas + ayudantes gratuitos)
  python herramientas/devil.py aplicar     -> trabajo/salida/data/db.devil/en/*.bin
"""
import json, os, re, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
JUEGO = os.path.join(os.environ.get('Y5_JUEGO', 'D:/SteamLibrary/steamapps/common/Yakuza 5/main/data'), 'db.devil', 'en')
# (21-10) mejor la copia de los originales (Steam pudo quedar con la traducción de una prueba)
if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'trabajo', 'originales', 'db.devil', 'en', 'msg.bin')):
    JUEGO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'trabajo', 'originales', 'db.devil', 'en')
# (21-10) si la traducción está INSTALADA en Steam, el «original» ya no lo es: parar (quitarla antes con el instalador)
if os.path.exists(os.path.join(os.environ.get('Y5_JUEGO', 'D:/SteamLibrary/steamapps/common/Yakuza 5/main/data'), 'traduccion_es_version.txt')):
    sys.exit('La traducción está instalada en Steam: quítala (INSTALAR o QUITAR.bat, opción 2) antes de rearmar.')
D = os.path.join(T, 'devil'); TXT = os.path.join(D, 'textos.json'); ES = os.path.join(D, 'es.json')
# msg_replacer.bin y middle_file_reactor_name.bin = nombres INTERNOS de desarrollo (traducción literal de las etiquetas
# japonesas: «(L)素手ザコ», «... (Adventure)», piezas rompibles): no los ve el jugador, NO se tocan.
ARCHIVOS = ['msg.bin']


def es_texto(s):
    """Lo que lee el jugador: letras de verdad; fuera claves internas, pruebas y nombres de columna."""
    if not re.search(r'[A-Za-z]{2,}', s) or s.startswith('(') and s.endswith(')'): return False
    if re.fullmatch(r'[A-Za-z0-9_./\-:#]+', s) and ('_' in s or '/' in s or '.' in s or s.islower() or s.isupper() and len(s) <= 4): return False
    if s in ('message', 'Display Name', 'TEST', 'test'): return False
    return True


def cadenas(b):
    for m in re.finditer(rb'(?<=\x00)[^\x00]{2,}?(?=\x00)', b):
        try: s = m.group().decode('utf-8')
        except UnicodeDecodeError: continue
        if s.isprintable(): yield m.start(), s


def extraer():
    os.makedirs(D, exist_ok=True); out = []
    for f in ARCHIVOS:
        b = open(os.path.join(JUEGO, f), 'rb').read()
        for off, s in cadenas(b):
            if not es_texto(s): continue
            ptrs = [m.start() for m in re.finditer(re.escape(struct.pack('<I', off)), b) if m.start() % 4 == 0]
            if len(ptrs) == 1: out.append({'archivo': f, 'off': off, 'ptr': ptrs[0], 'en': s})
    json.dump(out, open(TXT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    u = {x['en'] for x in out}
    print(len(out), 'cadenas', len(u), 'distintas', {f: sum(1 for x in out if x['archivo'] == f) for f in ARCHIVOS})


def traducir():
    sys.argv = [sys.argv[0], 'devil']
    import traductor_gemini as TG
    from aplicar import traducciones, norm
    gen, _ = traducciones()
    xs = json.load(open(TXT, encoding='utf-8'))
    es = json.load(open(ES, encoding='utf-8')) if os.path.exists(ES) else {}
    for x in xs:
        t = gen.get(norm(x['en']))
        if t and x['en'] not in es: es[x['en']] = t
    falta = sorted({x['en'] for x in xs} - set(es))
    TG.log(f'{len(es)} ya traducidas por el juego, {len(falta)} para los ayudantes')
    guia = open(os.path.join(T, 'lotes', 'GUIA_TRADUCCION.md'), encoding='utf-8').read()
    encargo = (guia + "\n\nTraduce al español neutro latinoamericano estos textos de Yakuza 5 (mensajes del sistema y nombres "
               "de enemigos). Nombres propios de personas se dejan igual; apodos y descripciones de enemigos sí se traducen "
               "(«Unarmed Lowlife» -> «Matón desarmado»). Mismas marcas, %s, comillas y saltos de línea. "
               "Devuelve SOLO JSON {\"t\": {\"id\": \"traducción\"}}.\n")
    for i in range(0, len(falta), 80):
        trozo = {str(n): t for n, t in enumerate(falta[i:i + 80])}
        r, m = TG.pedir(encargo + json.dumps(trozo, ensure_ascii=False, indent=0))
        if r is None: continue
        t = r.get('t', r) if isinstance(r, dict) else {}
        for n, en in enumerate(falta[i:i + 80]):
            v = t.get(str(n))
            if isinstance(v, str) and v.strip() and v.count('\n') == en.count('\n') and v.count('%') == en.count('%'): es[en] = v
        json.dump(es, open(ES, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        TG.log(f'{min(i + 80, len(falta))}/{len(falta)} ({m})')


def aplicar():
    xs = json.load(open(TXT, encoding='utf-8')); es = json.load(open(ES, encoding='utf-8'))
    sal = os.path.join(T, 'salida', 'data', 'db.devil', 'en'); os.makedirs(sal, exist_ok=True); n = 0
    for f in ARCHIVOS:
        b = bytearray(open(os.path.join(JUEGO, f), 'rb').read()); cambios = 0
        for x in xs:
            if x['archivo'] != f or x['en'] not in es or es[x['en']] == x['en']: continue
            while len(b) % 4: b.append(0)
            nuevo = len(b); b += es[x['en']].replace('¡', '½').replace('í', '`').replace('Í', '|').encode('utf-8') + b'\0'   # «¡» en la casilla de «~» (aplicar.LETRAS)
            assert struct.unpack_from('<I', b, x['ptr'])[0] == x['off']
            struct.pack_into('<I', b, x['ptr'], nuevo); cambios += 1
        if cambios:
            while len(b) % 16: b.append(0)
            open(os.path.join(sal, f), 'wb').write(b); n += cambios
            print(f, cambios, 'textos')
    print('db.devil:', n, 'textos ->', sal)


if __name__ == '__main__':
    {'extraer': extraer, 'traducir': traducir, 'aplicar': aplicar}[sys.argv[1]]()
