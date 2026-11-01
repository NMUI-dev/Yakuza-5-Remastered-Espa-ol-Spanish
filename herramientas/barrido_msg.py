# (31-10, claude1) Barrido de los .msg INSTALADOS (barrido.py extraer): textos que apuntan los registros y la tabla de
# NOMBRES de quien habla (u16 n en 0x0E, tabla de u32 en 0x10 -> cadenas UTF-8). Dice qué sigue en inglés.
#   python barrido_msg.py <barrido>/x  -> resumen + <barrido>/msg_ingles.jsonl
import glob, json, os, re, struct, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import msg_y5
from barrido import ingles
X = sys.argv[1]
T = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'trabajo')
norm = lambda s: re.sub(r'\s+', ' ', re.sub(r'<[^>]*>', '', s)).strip()
EN = {}
for f in glob.glob(T + '/lotes/lote_[0-9][0-9][0-9].json'):
    es = json.load(open(f[:-5] + '_es.json', encoding='utf-8')) if os.path.exists(f[:-5] + '_es.json') else {}
    for e in json.load(open(f, encoding='utf-8')): EN[norm(e['en'])] = es.get(str(e['id']))
c = collections.Counter(); out = []; letras = collections.Counter()
for p in glob.glob(X + '/wdr_par_en/**/*.msg', recursive=True):
    b = open(p, 'rb').read(); a = os.path.relpath(p, X).replace(os.sep, '/')
    try: _, regs = msg_y5.leer(b)
    except Exception: c['ilegible'] += 1; continue
    for r in regs:
        t = r['texto'].decode('utf-8', 'ignore'); n = norm(t)
        if not n: continue
        c['textos'] += 1; letras['textos'] += len(n)
        if n in EN and EN[n] and norm(EN[n]) != n: c['textos_en_ingles_con_traduccion'] += 1; out.append((a, 'texto_sin_aplicar', n)); letras['ing'] += len(n)
        elif n not in EN and ingles(n): c['textos_ingles_no_extraidos'] += 1; out.append((a, 'texto_no_extraido', n)); letras['ing'] += len(n)
    k = struct.unpack('>H', b[0x0e:0x10])[0]; o = struct.unpack('>I', b[0x10:0x14])[0]
    if 0 < k < 500 and 0x18 <= o and o + 4 * k <= len(b):
        for i in range(k):
            q = struct.unpack('>I', b[o + 4 * i:o + 4 * i + 4])[0]
            if q >= len(b): c['nombre_malo'] += 1; continue
            s = b[q:b.index(b'\0', q)].decode('utf-8', 'ignore')
            c['nombres'] += 1; letras['nombres'] += len(s)
            if re.search(r'[A-Za-z]', s) and not re.search('[áéíóúñÁÉÍÓÚÑ`½]', s): c['nombres_ascii'] += 1; out.append((a, 'nombre', s))
print(dict(c), dict(letras))
with open(os.path.join(os.path.dirname(X), 'msg_ingles.jsonl'), 'w', encoding='utf-8') as f:
    for a, k, t in out: f.write(json.dumps({'a': a, 'k': k, 't': t}, ensure_ascii=False) + '\n')
u = collections.defaultdict(set)
for a, k, t in out: u[k].add(t)
for k, v in u.items(): print(k, len(v), 'únicos', sorted(v)[:12])
