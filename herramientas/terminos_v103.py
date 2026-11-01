# -*- coding: utf-8 -*-
"""(01-11-2026, claude1) v1.0.3: con el glosario oficial latino de la saga (trabajo/saga/glosario.json), lo que
DEJAMOS EN INGLÉS y la saga sí traduce = errores que se nos pasaron. Reglas del usuario:
  - «Heat», DEALER, HOME RUN, Cricket/Count-Up, marcas y nombres propios se quedan como están
  - si lo traducido no cabe bien (y encajarlo costaría mucho), se deja el inglés: aquí se descarta lo que sea mucho
    más largo que el inglés en textos cortos (menús/etiquetas)
  - los sinónimos de estilo (Bolsa/Bolso) NO se cambian: no son errores
Escribe trabajo/saga/cambios_v103.json [{lote, id, en, antes, despues, n_oficial}] (para revisar y aplicar).
  python herramientas/terminos_v103.py"""
import glob, json, os, re
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo'); L = os.path.join(T, 'lotes')
DEJAR = re.compile(r'\bheat\b|\bdealer\b|home ?run|cricket|count-?up|bull\b|\bsega\b|don quijote|\bboss\b|club\b', re.I)


def main():
    g = json.load(open(os.path.join(T, 'saga', 'glosario.json'), encoding='utf-8'))
    cambios = []
    for f in sorted(glob.glob(L + '/lote_???.json')):
        if f.endswith('310.json'): continue
        try: es = json.load(open(f[:-5] + '_es.json', encoding='utf-8'))
        except FileNotFoundError: continue
        for x in json.load(open(f, encoding='utf-8')):
            en = x['en'].strip(); t = es.get(str(x['id']))
            if not isinstance(t, str) or t.strip().lower() != en.lower(): continue      # solo lo que dejamos en inglés
            if en not in g or DEJAR.search(en) or not re.search('[a-z]', en): continue
            of = max(g[en], key=g[en].get); n = g[en][of]
            if of.strip().lower() == en.lower() or '\n' in of != ('\n' in en) or not re.search('[a-záéíóúñ]', of): continue
            if len(en) <= 25 and len(of) > max(len(en) * 1.6, len(en) + 8): continue      # no cabría en un menú
            cambios.append({'lote': int(f[-8:-5]), 'id': x['id'], 'en': x['en'], 'antes': t, 'despues': of.strip(), 'n_oficial': n})
    json.dump(cambios, open(os.path.join(T, 'saga', 'cambios_v103.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('textos que dejamos en inglés y la saga traduce:', len(cambios))
    for c in cambios: print(f"  {c['en']!r:40} -> {c['despues']!r}  (lote {c['lote']}, visto {c['n_oficial']} veces)")


if __name__ == '__main__': main()
