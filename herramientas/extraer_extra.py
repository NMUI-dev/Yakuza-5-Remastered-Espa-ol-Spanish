# -*- coding: utf-8 -*-
"""(31-10-2026, claude1) Lo que se quedó en INGLÉS en la v1.0.1 (barrido.py / barrido_msg.py sobre el juego instalado):
  nom  tabla de NOMBRES de quien habla y OPCIONES a elegir al final de cada .msg (u16 n en 0x0E, tabla de u32 big endian
       en 0x10 -> cadena UTF-8); msg_y5.leer no la leía.  «Astonished Man», «Abre la puerta / Finge que no estás».
  sub  subtítulos de escena con salto de línea DENTRO de comillas («"Just drive.\\r\\nI don't care where."»):
       extraer.py partía las filas por \\r\\n y se los saltaba.
  rep  db.devil/en/msg_replacer.bin: nombres de lugares (cartel de zona: «Kiryu's Apartment»), tiendas, objetos, enemigos.
       Cada cadena tiene UN puntero u32 little endian (como devil.py).
Escribe trabajo/extra/textos.json (todas las apariciones) y lotes NUEVOS trabajo/lotes/lote_326+ solo con las frases
que no tienen ya traducción en los lotes (esas se reutilizan al aplicar).
  python herramientas/extraer_extra.py"""
import glob, json, os, re, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
E = os.path.join(T, 'extraido'); X = os.path.join(T, 'extra'); L = os.path.join(T, 'lotes')
norm = lambda s: re.sub(r'\s+', ' ', re.sub(r'<[^>]*>', '', s)).strip()
JP = re.compile('[぀-ヿ㐀-鿿＀-￯]')


def es_rotulo(s):
    """Texto que lee el jugador (no id de animación, voz, ruta ni clave interna)."""
    t = s.strip().lstrip('○□●■')
    if len(t) < 2 or JP.search(t) or not re.search(r'[A-Za-z]{2}', t): return False
    if re.search(r'[_/\\]', t) or re.fullmatch(r'[A-Z]?[a-z]+[A-Z]\w*|\w*\d\w*', t): return False
    if ' ' not in t and (t.islower() or re.search(r'[a-z][A-Z]', t)): return False
    if t in ('message', 'Display Name', 'TEST', 'test', 'dummy', 'Dummy'): return False
    return True


def nombres_msg(b):
    """[(posición del puntero, texto)] de la tabla de nombres/opciones de un .msg."""
    k = struct.unpack('>H', b[0x0e:0x10])[0]; o = struct.unpack('>I', b[0x10:0x14])[0]
    if not (0 < k < 1000 and 0x18 <= o and o + 4 * k <= len(b)): return []
    r = []
    for i in range(k):
        q = struct.unpack('>I', b[o + 4 * i:o + 4 * i + 4])[0]
        if q < len(b) and b'\0' in b[q:]:
            r.append((o + 4 * i, b[q:b.index(b'\0', q)].decode('utf-8', 'replace')))
    return r


SUB = re.compile(r'(?:^|\r\n)\d+\t\d+\t"(.*?)"\t', re.S)


def main():
    os.makedirs(X, exist_ok=True); out = []
    for p in sorted(glob.glob(E + '/wdr_par_en_*/**/*.msg', recursive=True)):
        a = os.path.relpath(p, E).replace(os.sep, '/')
        for ptr, s in nombres_msg(open(p, 'rb').read()):
            if es_rotulo(s): out.append(dict(f='nom', a=a, ptr=ptr, t=s))
    for p in sorted(glob.glob(E + '/auth_subtitle/*.csv')):
        tx = open(p, 'rb').read().decode('utf-16')
        for m in SUB.finditer(tx):
            if re.search(r'[A-Za-z]{2}', m.group(1)) and not JP.search(m.group(1)):
                out.append(dict(f='sub', a=os.path.basename(p), t=m.group(1)))
    rb = open(os.path.join(T, 'db_en', 'msg_replacer.bin'), 'rb').read()
    for m in re.finditer(rb'(?<=\x00)[^\x00]{2,}?(?=\x00)', rb):
        try: s = m.group().decode('utf-8')
        except UnicodeDecodeError: continue
        if not s.isprintable() or not es_rotulo(s): continue
        # etiquetas de desarrollo (piezas rompibles, modelos, versiones): no salen en pantalla, no gastar cuota
        if re.search(r'[\[\]<>]|\b(?:Broken|Model|Redundant|Fragment|Piece|Object|Dummy|Base|Ammo|Y4|Hand)\b', s): continue
        ptrs = [q.start() for q in re.finditer(re.escape(struct.pack('<I', m.start())), rb) if q.start() % 4 == 0]
        if len(ptrs) == 1: out.append(dict(f='rep', a='db.devil/en/msg_replacer.bin', off=m.start(), ptr=ptrs[0], t=s))
    json.dump(out, open(os.path.join(X, 'textos.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    # frases que ya tienen traducción en los lotes: no se mandan otra vez
    ya = set(); mx = 0
    for f in glob.glob(L + '/lote_[0-9][0-9][0-9].json'):
        for e in json.load(open(f, encoding='utf-8')): ya.add(norm(e['en'])); mx = max(mx, e['id'])
    CTX = {'nom': 'nombre de quien habla (rótulo corto encima del diálogo) u OPCIÓN de respuesta a elegir en una '
                  'conversación o misión; si empieza por ○ o □ mantener ese signo al principio',
           'sub': 'subtítulo de cinemática de la historia; MANTENER el salto de línea \\n en el mismo sitio '
                  '(2 renglones); no usar comillas dobles "',
           'rep': 'nombre que sale en pantalla: lugar o calle (cartel de zona al entrar), tienda, objeto, arma o '
                  'enemigo; corto, estilo cartel; nombres propios japoneses y marcas se dejan igual'}
    nuevos = {}
    for x in out:
        n = norm(x['t'])
        if n in ya or n in nuevos: continue
        nuevos[n] = dict(en=x['t'].replace('\r\n', '\n'), ctx=CTX[x['f']])
    ls = list(nuevos.values()); TAM = 200; i0 = 326
    for k in range(0, len(ls), TAM):
        lote = [dict(id=mx + 1 + k + j, **e) for j, e in enumerate(ls[k:k + TAM])]
        json.dump(lote, open(f'{L}/lote_{i0 + k // TAM:03d}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    from collections import Counter
    print('apariciones', Counter(x['f'] for x in out), '| distintas nuevas', len(ls),
          Counter(nuevos[n]['ctx'][:6] for n in nuevos), '| lotes', i0, '..', i0 + (len(ls) - 1) // TAM)


if __name__ == '__main__': main()
