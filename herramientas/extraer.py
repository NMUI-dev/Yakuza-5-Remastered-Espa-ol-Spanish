# (Claude Code, 20-10-2026) Saca TODOS los textos en inglés de Yakuza 5 a trabajo/textos_en.jsonl (uno por celda/frase,
# con su fuente y su clave para reinsertar) y trabajo/unicos_en.json (textos únicos con su contexto, para traducir).
# Fuentes: msg (diálogos .msg), sub (subtítulos CSV UTF-16), tabla (tablas 20 07 03 19), ptr (.bin con punteros
# absolutos big endian), pac (guiones con texto en línea; reinserción aparte).
import os, re, sys, json, struct, collections
sys.path.insert(0, os.path.dirname(__file__))
import msg_y5, tabla_y5
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = os.path.join(R, 'trabajo', 'extraido')
NO = ('wdr_ja', 'font_font', 'hact_', 'auth_a1010', 'syscache')

def es_texto(s):
    """¿Es una frase o nombre para traducir (y no un identificador, ruta o número)?"""
    if not re.search(r'[A-Za-z]{2}', s): return False
    if re.fullmatch(r'[a-z0-9_./\-]+', s) or re.fullmatch(r'[A-Z0-9_./\-]+', s): return False
    if re.search(r'\.(dds|bin|gmt|par|wav|adx|hca|usm|tex|txt|csv|cmt|bux|sbb)\b', s, re.I): return False
    if re.fullmatch(r'[A-Za-z]+[_][A-Za-z0-9_]*', s): return False
    if '\ufffd' in s: return False
    if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', s): return False     # bytes de control = datos, no texto
    if '_' in s and ' ' not in s: return False                       # nombres de animación/ids (MnG06KA_F_..., SUB_A17_...)
    if not re.search(r'[aeiouyAEIOUY]', s): return False
    return True

def rel(p): return os.path.relpath(p, E).replace('\\', '/')

def main():
    sal = []
    for dp, _, fs in os.walk(E):
        if any(n in dp for n in NO): continue
        for f in sorted(fs):
            p = os.path.join(dp, f); b = open(p, 'rb').read()
            if f.endswith('.msg'):
                secs, regs = msg_y5.leer(b)
                for r in regs:
                    t = r['texto'].decode('utf-8', 'replace')
                    if es_texto(t): sal.append(dict(f='msg', a=rel(p), k=r['reg'], t=t))
            elif f.endswith('.csv') and 'auth_subtitle' in dp:
                filas = b.decode('utf-16').split('\r\n')
                for i, l in enumerate(filas):
                    c = l.split('\t')
                    if len(c) > 3 and es_texto(c[2]): sal.append(dict(f='sub', a=rel(p), k=i, t=c[2]))
            elif f.endswith('.bin') and tabla_y5.es_tabla(b):
                t = tabla_y5.leer(b)
                porcol = collections.defaultdict(list)
                for col, clave, x in tabla_y5.textos(t): porcol[col].append((clave, x.decode('utf-8', 'replace')))
                for col, v in porcol.items():
                    txt = [x for _, x in v if es_texto(x)]
                    if not txt: continue
                    for clave, x in v:
                        if es_texto(x): sal.append(dict(f='tabla', a=rel(p), c=col, k=list(clave), t=x))
            elif f.endswith('.bin') and f.startswith('pac_'):
                for m in re.finditer(rb'(?<=\x00)[^\x00]{2,}(?=\x00)', b):
                    x = m.group().decode('utf-8', 'replace')
                    if es_texto(x) and re.search(r'[a-z]{2}', x) and (' ' in x or re.search(r'[.!?)]$', x) or len(x) >= 5): sal.append(dict(f='pac', a=rel(p), k=m.start(), t=x))
            elif f.endswith('.bin'):
                al = set(struct.unpack('>I', b[i:i + 4])[0] for i in range(0, len(b) - 3, 4))
                for m in re.finditer(rb'(?<=\x00)[^\x00]{2,}(?=\x00)', b):
                    if m.start() not in al: continue
                    x = m.group().decode('utf-8', 'replace')
                    if es_texto(x): sal.append(dict(f='ptr', a=rel(p), k=m.start(), t=x))
    os.makedirs(os.path.join(R, 'trabajo'), exist_ok=True)
    with open(os.path.join(R, 'trabajo', 'textos_en.jsonl'), 'w', encoding='utf-8') as o:
        for e in sal: o.write(json.dumps(e, ensure_ascii=False) + '\n')
    uni = collections.OrderedDict()
    for e in sal:
        u = uni.setdefault(e['t'], dict(n=0, donde=[]))
        u['n'] += 1
        if len(u['donde']) < 3: u['donde'].append(e['f'] + ':' + e['a'] + (':' + e['c'] if 'c' in e else ''))
    json.dump(uni, open(os.path.join(R, 'trabajo', 'unicos_en.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    cf = collections.Counter(); lf = collections.Counter()
    vistos = set()
    for e in sal:
        cf[e['f']] += 1
        if e['t'] not in vistos: vistos.add(e['t']); lf[e['f']] += len(e['t'])
    print('celdas', len(sal), dict(cf)); print('únicos', len(uni), 'letras', sum(map(len, uni)), dict(lf))

if __name__ == '__main__': main()
