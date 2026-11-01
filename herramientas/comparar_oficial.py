# -*- coding: utf-8 -*-
"""(01-11-2026, claude1) Compara nuestra traducción del Yakuza 5 (trabajo/lotes) con el español latino OFICIAL de la
saga (trabajo/saga/glosario.json, de glosario_saga.py):
  A. textos IGUALES en inglés en los dos juegos: nuestra traducción frente a la oficial (los cortos = menús, objetos,
     lugares, minijuegos, términos; los largos solo se informan)
  B. TÉRMINOS de la saga (entradas cortas del glosario, 1-3 palabras con mayúscula) que aparecen DENTRO de nuestras frases:
     cómo los traducimos nosotros y cómo la saga
Escribe trabajo/saga/diferencias_cortas.json, trabajo/saga/terminos.json y un resumen.
  python herramientas/comparar_oficial.py"""
import collections, glob, json, os, re
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo'); L = os.path.join(T, 'lotes')
LET = str.maketrans({'½': '¡', '`': 'í', '|': 'Í'})


def nuestros():
    d = {}
    for f in sorted(glob.glob(L + '/lote_???.json')):
        if f.endswith('310.json'): continue
        try: es = json.load(open(f[:-5] + '_es.json', encoding='utf-8'))
        except FileNotFoundError: continue
        for x in json.load(open(f, encoding='utf-8')):
            t = es.get(str(x['id']))
            if isinstance(t, str) and t.strip(): d.setdefault(x['en'].strip(), (t.strip(), int(f[-8:-5]), x['id']))
    return d


def main():
    g = json.load(open(os.path.join(T, 'saga', 'glosario.json'), encoding='utf-8'))
    of = {k.strip(): max(v, key=v.get) for k, v in g.items()}
    nu = nuestros()
    comunes = [k for k in nu if k in of]
    dif = [k for k in comunes if nu[k][0].translate(LET) != of[k] and re.sub(r'[\W_]', '', nu[k][0].lower()) != re.sub(r'[\W_]', '', of[k].lower())]
    cortos = [k for k in dif if len(k.split()) <= 4 and '\n' not in k]
    json.dump([{'en': k, 'nuestro': nu[k][0], 'oficial': of[k], 'lote': nu[k][1], 'id': nu[k][2]} for k in sorted(cortos)],
              open(os.path.join(T, 'saga', 'diferencias_cortas.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('textos en inglés iguales en los dos juegos', len(comunes), '| traducidos distinto', len(dif), '| cortos', len(cortos))
    # B. términos
    term = {k: v for k, v in of.items() if 1 <= len(k.split()) <= 3 and re.fullmatch(r"[A-Z][\w'\-]*(?: [A-Z&][\w'\-]*){0,2}", k)
            and k.lower() != v.lower() and len(k) >= 4}
    uso = collections.defaultdict(collections.Counter); veces = collections.Counter()
    # (más rápido: n-gramas de 1-3 palabras de cada frase, buscados en el diccionario de términos; sensible a mayúsculas)
    PAL = re.compile(r"[A-Za-z0-9][\w'\-&]*")
    for en, (es, _, _) in nu.items():
        w = PAL.findall(en); esl = es.translate(LET).lower(); vistos = set()
        for n in (1, 2, 3):
            for i in range(len(w) - n + 1):
                k = ' '.join(w[i:i + n])
                if k in term and k not in vistos:
                    vistos.add(k); veces[k] += 1
                    uso[k]['OFICIAL' if term[k].lower() in esl else 'otra'] += 1
    malos = sorted(((veces[k], k) for k in veces if uso[k]['otra'] > uso[k]['OFICIAL']), reverse=True)
    json.dump([{'en': k, 'oficial': term[k], 'veces': n, 'con_oficial': uso[k]['OFICIAL']} for n, k in malos],
              open(os.path.join(T, 'saga', 'terminos.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('términos de la saga en nuestras frases', len(veces), '| usados distinto a lo oficial', len(malos))
    for n, k in malos[:40]: print(f'  {n:4d}  {k!r} -> oficial {term[k]!r} (nosotros lo usamos {uso[k]["OFICIAL"]} veces)')


if __name__ == '__main__': main()
