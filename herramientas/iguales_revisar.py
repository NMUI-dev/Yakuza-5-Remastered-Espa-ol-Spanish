# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Textos que quedaron IGUAL que el inglés (en el laboratorio salió «Hard» sin traducir en la
dificultad; buscar_fallos.py solo miraba frases de más de 12 letras). Los ayudantes gratuitos deciden uno por uno:
nombre propio / marca / japonés / término que se dice igual -> se deja; si no -> se traduce. Solo se guarda si el lote
sigue validando. Registro antes/después en tareas/gemini/correcciones.jsonl.
  python herramientas/iguales_revisar.py
"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = [sys.argv[0], 'iguales']
import traductor_gemini as TG
L = TG.L
ENCARGO = """Eres revisor de la traducción al español neutro latinoamericano de Yakuza 5. Estos textos se quedaron en
inglés. Para cada id decide: si es un NOMBRE PROPIO (persona, lugar, local, marca, título de juego o canción), un texto
japonés, un código interno, o una palabra que en español se dice igual, devuelve el texto IGUAL. Si no, TRADÚCELO
(dificultad, interjecciones como «Huh? Whoa!» -> «¿Eh? ¡Guau!», risas «Hahaha!» -> «¡Jajaja!», nombres comunes de
objetos o juegos como «Eight-Ball» -> «Bola 8»). Respeta signos ¿¡, marcas <...>, %s y el número de \\n.
Devuelve SOLO JSON {"t": {"id": "texto"}}.
"""

def main():
    casos = {}
    for p in sorted(glob.glob(f'{L}/lote_???.json')):
        n = os.path.basename(p)[5:8]; es = json.load(open(f'{L}/lote_{n}_es.json', encoding='utf-8'))
        for x in json.load(open(p, encoding='utf-8')):
            e, t = x['en'], es.get(str(x['id']), '')
            if t.strip() == e.strip() and re.search(r'[a-z]{3}', e): casos.setdefault(n, {})[str(x['id'])] = {'en': e, 'ctx': x['ctx'][:60]}
    TG.log(f"{sum(len(v) for v in casos.values())} textos iguales al inglés en {len(casos)} lotes")
    for n, cs in sorted(casos.items()):
        ruta = f'{L}/lote_{n}_es.json'; es = json.load(open(ruta, encoding='utf-8')); viejo = dict(es); cambios = {}
        ids = list(cs)
        for i in range(0, len(ids), 60):
            trozo = {k: cs[k] for k in ids[i:i + 60]}
            r, m = TG.pedir(ENCARGO + json.dumps(trozo, ensure_ascii=False, indent=0))
            t = (r.get('t', r) if isinstance(r, dict) else {}) if r else {}
            cambios.update({k: v for k, v in t.items() if k in trozo and isinstance(v, str) and v.strip() and v.strip() != trozo[k]['en'].strip()})
        if not cambios: continue
        es.update(cambios); json.dump(es, open(ruta, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        ok, salida = TG.validar(n)
        if not ok:
            for k in cambios:
                if k in salida: es[k] = viejo[k]
            json.dump(es, open(ruta, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
            if not TG.validar(n)[0]: json.dump(viejo, open(ruta, 'w', encoding='utf-8'), ensure_ascii=False, indent=0); continue
        open(f'{TG.Y}/tareas/gemini/correcciones.jsonl', 'a', encoding='utf-8').write(''.join(
            json.dumps({'lote': n, 'id': k, 'antes': viejo[k], 'despues': es[k], 'motivo': 'igual_ingles'}, ensure_ascii=False) + '\n'
            for k in cambios if es[k] != viejo[k]))
        TG.log(f'lote {n}: {sum(1 for k in cambios if es[k] != viejo[k])} traducidos')
    TG.log('fin')

if __name__ == '__main__':
    main()
