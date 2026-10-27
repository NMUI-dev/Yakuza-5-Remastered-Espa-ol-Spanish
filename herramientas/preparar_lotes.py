# -*- coding: utf-8 -*-
"""(Claude Code, 20-10-2026) Prepara los lotes de traducción de Yakuza 5 desde trabajo/textos_en.jsonl (extraer.py).
Textos únicos -> trabajo/lotes/lote_NNN.json: [{"id": n, "en": texto, "ctx": "dónde sale"}]. Los \\r\\n del juego se
escriben como \\n (al reinsertar se vuelven a poner). Orden: menús y tablas, luego subtítulos de escenas, luego los
diálogos (.msg) en el orden en que salen en cada archivo (así cada conversación queda junta), y al final los «pac».
Las traducciones van en lote_NNN_es.json: {"id": "texto en español"}.
  python herramientas/preparar_lotes.py [letras_por_lote]
"""
import json, os, sys, collections
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
LOTE = int(sys.argv[1]) if len(sys.argv) > 1 else 12000
PRIO = {'tabla': 0, 'ptr': 0, 'sub': 1, 'msg': 2, 'pac': 3}

def ctx(e):
    a = e['a'].split('/')
    if e['f'] == 'msg': return 'diálogo ' + a[-1][:-4]
    if e['f'] == 'sub': return 'subtítulo de escena ' + a[-1][:-4]
    if e['f'] == 'tabla': return f'tabla {a[-1][:-4]}|{e["c"]}'
    if e['f'] == 'pac': return 'frase de acompañante/calle ' + a[-1][4:-4]
    return 'menú/texto ' + a[-1][:-4]

def norm(t): return t.replace('\r\n', '\n')

if __name__ == '__main__':
    uni = collections.OrderedDict()
    for n, l in enumerate(open(os.path.join(T, 'textos_en.jsonl'), encoding='utf-8')):
        e = json.loads(l); k = norm(e['t'])
        u = uni.setdefault(k, {'ctx': [], 'prio': 9, 'orden': n})
        c = ctx(e)
        if c not in u['ctx']: u['ctx'].append(c)
        u['prio'] = min(u['prio'], PRIO[e['f']])
    items = sorted(uni.items(), key=lambda kv: (kv[1]['prio'], kv[1]['orden']))
    d = os.path.join(T, 'lotes'); os.makedirs(d, exist_ok=True)
    lotes = []; act = []; letras = 0
    for i, (en, u) in enumerate(items):
        act.append({'id': i, 'en': en, 'ctx': ' + '.join(u['ctx'][:2]) + (' …' if len(u['ctx']) > 2 else '')})
        letras += len(en)
        if letras >= LOTE: lotes.append(act); act = []; letras = 0
    if act: lotes.append(act)
    for n, l in enumerate(lotes):
        json.dump(l, open(os.path.join(d, f'lote_{n:03d}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    json.dump({en: i for i, (en, _) in enumerate(items)}, open(os.path.join(d, 'indice.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print(len(items), 'textos únicos,', sum(len(e) for e, _ in items), 'letras,', len(lotes), 'lotes;',
          collections.Counter(u['prio'] for _, u in items))
