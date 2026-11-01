# -*- coding: utf-8 -*-
"""(01-11-2026, claude1) Lo que el barrido final de la v1.0.2 encontró aún en inglés y a la vista
(trabajo/queda_ingles/, regla del usuario: «confirma que se saca todo lo que anda en inglés»):
  nom  preguntas del concurso, opciones y títulos de tutorial de la tabla de nombres de los .msg: extraer_extra.es_rotulo
       las descartaba (llevan «(改行)» o son largas)
  rep  msg.bin (mensajes del sistema) y msg_replacer.bin: cadenas con salto de línea (\\n), que extraer_extra
       descartaba con isprintable (comentarios de los dardos, frases a Saejima)
Añade las entradas a trabajo/extra/textos.json (las aplica aplicar_extra.py) y escribe el lote nuevo (ids nuevos).
  python herramientas/extraer_extra2.py"""
import glob, json, os, re, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraer_extra import nombres_msg
from barrido import EN, ES
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo'); L = os.path.join(T, 'lotes')
BASE_WDR = os.path.join(T, 'extra', 'tmp', 'wdr_par_en_wdr_full')       # wdr.par de la v1.0.1 (lo deja aplicar_extra.py)
DEVIL = {'db.devil/en/msg.bin': os.path.join(R, 'entrega_v101', 'archivos', 'data', 'db.devil', 'en', 'msg.bin'),
         'db.devil/en/msg_replacer.bin': os.path.join(T, 'db_en', 'msg_replacer.bin')}
EN2 = EN - {'oh', 'no', 'ya', 'so', 'me', 'he', 'i', 'a', 'yo', 'sir', 'bar', 'club', 'hotel', 'park', 'man', 'do', 'go', 'pay'} | \
    {'save', 'data', 'game', 'play', 'time', 'number', 'clear', 'load', 'continue', 'received', 'cannot', 'new', 'file',
     'system', 'true', 'false', 'what', 'which', 'abilities', 'eating', 'stamps', 'balance'}
PAL = re.compile(r"[A-Za-z][a-z']*")
# nombres propios y títulos que se dejan (mangas, canciones, tiendas, programas) y claves internas de voz
DEJAR = re.compile(r'^(?:"Because I Have You"|A Town Where You Live|Attack on Titan|Be Dash!|Cage of Eden|Curry Shop S|'
                   r'Digimono Station|Eye on Fukuoka|My Wife is Wagatsuma-san|The Laughmakers|The Mola Mola|The Remover.*|'
                   r'Yamada-Kun and the Seven Witches|M Store.*|New Serena)$|^adv\d')
CTX_NOM = ('pregunta de un CONCURSO de preguntas (verdadero o falso / elegir respuesta), opción o título de tutorial; '
           '«(改行)» es un salto de línea del cuadro: MANTÉN el mismo número de «(改行)» y en el mismo orden, cada renglón '
           'de 46 letras como mucho; nombres propios igual')
CTX_REP = ('mensaje del sistema (guardar/cargar datos) o frase dicha en un combate o en los dardos; MANTÉN los saltos de '
           'línea y las marcas ${...} exactamente igual')


def ingles(t):
    s = re.sub(r'<[^>]*>|\$\{[^}]*\}|\(改行\)', ' ', t)
    if re.search('[áéíóúñ¿¡ÁÉÍÓÚÑ`|½]', s) or re.search(r'[぀-ヿ一-鿿]', s.replace('改行', '')): return False
    if s.strip().startswith(('[', '(')) or DEJAR.search(t): return False
    if ' ' not in t.strip() or '/' in t and ' ' not in t.split('/')[0]: return False   # claves internas (Talk_Yes, rutas)
    w = [p.lower() for p in PAL.findall(s)]
    return sum(p in EN2 for p in w) > sum(p in ES for p in w) and any(p in EN2 for p in w)


def cadena(b, q):
    if not 0 < q < len(b) or b[q - 1] != 0: return None
    e = b.find(b'\0', q)
    try: t = b[q:e].decode('utf-8')
    except UnicodeDecodeError: return None
    return t if t and all(c.isprintable() or c in '\r\n\t' for c in t) else None


def main():
    textos_p = os.path.join(T, 'extra', 'textos.json'); xs = json.load(open(textos_p, encoding='utf-8'))
    ya = {(x['f'], x['a'], x.get('ptr')) for x in xs}; nuevos = []
    for p in sorted(glob.glob(BASE_WDR + '/**/*.msg', recursive=True)):
        a = 'wdr_par_en_wdr/' + os.path.relpath(p, BASE_WDR).replace(os.sep, '/')
        for ptr, s in nombres_msg(open(p, 'rb').read()):
            if ingles(s) and ('nom', a, ptr) not in ya: nuevos.append(dict(f='nom', a=a, ptr=ptr, t=s))
    # objetos internos de msg_replacer (piezas rotas, modelos, bases): no se ven
    INTERNO = re.compile(r'Broken|Fragment|Model|Base\b|Object|Dummy|Door|Redundant|\[|\]|Taxi|Sedan|Station wagon|Office|'
                         r'Trash Can|Umbrella|Parasol|Bolos|Partition|Vase|Pile of|Bundle of|Cart with|Hammer|Pipe|Materials|'
                         r'Yamazaki|Serena|middle_file|Pillado')
    for a, src in DEVIL.items():
        b = open(src, 'rb').read()
        for p in range(0, len(b) - 3, 4):
            q = struct.unpack('<I', b[p:p + 4])[0]; t = cadena(b, q)
            if not t or not ingles(t) or ('rep', a, p) in ya: continue
            if a.endswith('msg_replacer.bin') and INTERNO.search(t): continue
            if not any(cadena(b, struct.unpack('<I', b[r:r + 4])[0]) for r in (p - 4, p + 4) if 0 <= r <= len(b) - 4): continue
            nuevos.append(dict(f='rep', a=a, off=q, ptr=p, t=t))
    if not nuevos: print('nada nuevo'); return
    json.dump(xs + nuevos, open(textos_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    # lote nuevo con las frases distintas
    nmax = max(int(f[-8:-5]) for f in glob.glob(L + '/lote_[0-9][0-9][0-9].json'))
    mx = max(e['id'] for f in glob.glob(L + '/lote_[0-9][0-9][0-9].json') for e in json.load(open(f, encoding='utf-8')))
    vistos, lote = set(), []
    for x in nuevos:
        if x['t'] in vistos: continue
        vistos.add(x['t']); mx += 1
        lote.append({'id': mx, 'en': x['t'], 'ctx': CTX_NOM if x['f'] == 'nom' else CTX_REP})
    n = nmax + 1
    json.dump(lote, open(os.path.join(L, f'lote_{n:03d}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('entradas', len(nuevos), '(nom', sum(x['f'] == 'nom' for x in nuevos), 'rep', sum(x['f'] == 'rep' for x in nuevos),
          ') frases', len(lote), '-> lote', n)


if __name__ == '__main__': main()
