# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Revisión final automática: toma lo que marca buscar_fallos.py (español de España o regional,
¿¡ de apertura que faltan, restos en inglés) y se lo manda a los ayudantes gratuitos (los mismos modelos de
traductor_gemini.py) con el inglés, la traducción y el problema; guarda la corrección solo si el lote sigue validando.
Cada hilo trabaja sus propios lotes (n % HILOS == hilo), así nunca escriben el mismo archivo a la vez.
  python herramientas/corregir_fallos.py HILO HILOS        (copia previa: trabajo/lotes_antes_revision_2026-10-21)
"""
import contextlib, io, json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HILO, HILOS = int(sys.argv[1]), int(sys.argv[2])
sys.argv = [sys.argv[0], f'corrector{HILO}']
import traductor_gemini as TG
sys.argv = [sys.argv[0], '0']
with contextlib.redirect_stdout(io.StringIO()):
    import buscar_fallos as BF
L = TG.L

PROBLEMA = {'españa': 'tiene una palabra de España o muy regional («{m}»): pásala a español NEUTRO latinoamericano '
                      '(p. ej. coche->auto, gafas->lentes, cabrear->enojar, cutre->de mala muerte, desmadre->relajo)',
            'signos': 'le falta el signo de apertura ¿ o ¡ de alguna pregunta o exclamación: ponlo donde empieza esa frase',
            'basura': 'tiene un resto en inglés o basura del modelo («{m}»): tradúcelo bien'}
ENCARGO = """Eres revisor de la traducción al español neutro latinoamericano de Yakuza 5. Para cada id te doy el inglés
original, la traducción actual y su problema. Corrige SOLO ese problema, cambiando lo mínimo. Si el problema es falso
(nombre propio, título de canción o marca, código interno como «battle_start != 0», palabra que también es neutra), devuelve
la traducción igual. Mantén EXACTAS las marcas (<Color:..>, <Italic>, %s, %d), el número de \\n y los espacios del final.
Devuelve SOLO JSON {"t": {"id": "traducción corregida"}}.
"""

import re
FRASE_ENTERA = re.compile(r"""^(?:<[^>]*>|[\s"«(“'¿¡….-])*(?:[A-ZÁÉÍÓÚÑ0-9¿¡]|%s)""")
HECHAS = set()
if os.path.exists(f'{TG.Y}/tareas/gemini/correcciones.jsonl'):
    HECHAS = {(x['lote'], x['id']) for x in map(json.loads, open(f'{TG.Y}/tareas/gemini/correcciones.jsonl', encoding='utf-8'))}
def cierres(s): return (s.count('?'), s.count('!'))

def main():
    casos = collections.defaultdict(dict)
    for tipo, l in BF.tipos.items():
        if tipo not in PROBLEMA: continue
        for n, k, m, t in l:
            if int(n) % HILOS != HILO or (n, k) in HECHAS: continue
            if tipo == 'signos' and not FRASE_ENTERA.match(t): continue   # (21-10) trozo de una frase partida: su ¿¡ va en el anterior
            p = PROBLEMA[tipo].format(m=m)
            casos[n][k] = casos[n].get(k, '') + ('; ' if k in casos[n] else '') + p
    TG.log(f'{sum(len(v) for v in casos.values())} frases en {len(casos)} lotes')
    for n in sorted(casos):
        en = {str(x['id']): x['en'] for x in json.load(open(f'{L}/lote_{n}.json', encoding='utf-8'))}
        ruta = f'{L}/lote_{n}_es.json'; es = json.load(open(ruta, encoding='utf-8'))
        ids = list(casos[n]); cambios = {}
        for i in range(0, len(ids), 40):
            trozo = {k: {'en': en[k], 'es': es[k], 'problema': casos[n][k]} for k in ids[i:i + 40]}
            r, m = TG.pedir(ENCARGO + '\n' + json.dumps(trozo, ensure_ascii=False, indent=0))
            if r is None: TG.log(f'lote {n}: sin respuesta'); continue
            t = r.get('t', r) if isinstance(r, dict) else {}
            cambios.update({k: v for k, v in t.items() if k in trozo and isinstance(v, str) and v.strip() and v != es[k]
                            and cierres(v) == cierres(es[k])})     # (21-10) nunca quitar ni añadir ? o ! de cierre
        if not cambios: continue
        viejo = dict(es); es.update(cambios)
        json.dump(es, open(ruta, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        ok, salida = TG.validar(n)
        if not ok:      # quitar solo las frases que rompen la validación
            for k in cambios:
                if k in salida: es[k] = viejo[k]
            json.dump(es, open(ruta, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
            ok, salida = TG.validar(n)
            if not ok: json.dump(viejo, open(ruta, 'w', encoding='utf-8'), ensure_ascii=False, indent=0); TG.log(f'lote {n}: revertido'); continue
        open(f'{TG.Y}/tareas/gemini/correcciones.jsonl', 'a', encoding='utf-8').write(''.join(
            json.dumps({'lote': n, 'id': k, 'antes': viejo[k], 'despues': es[k]}, ensure_ascii=False) + '\n'
            for k in cambios if es[k] != viejo[k]))
        TG.log(f'lote {n}: {sum(1 for k in cambios if es[k] != viejo[k])} corregidas')
    TG.log('fin')

if __name__ == '__main__':
    main()
