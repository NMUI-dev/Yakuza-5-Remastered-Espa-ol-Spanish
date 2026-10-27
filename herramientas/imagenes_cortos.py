# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Textos de imagen que no caben (avisos «no cabe» de imagenes_es.py): pide a los ayudantes
gratuitos una versión más corta, del largo del inglés como mucho, y la guarda en trabajo/imagenes/cortos.json
(clave de bloque -> texto). imagenes_es.py usa esas versiones en lugar de la traducción normal.
  python herramientas/imagenes_cortos.py      (después: python herramientas/imagenes_es.py --solo-cortos)
"""
import json, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = [sys.argv[0], 'cortos']
import traductor_gemini as TG
from aplicar import traducciones, norm
T = os.path.join(TG.Y, 'trabajo', 'imagenes'); CORTOS = os.path.join(T, 'cortos.json')

ENCARGO = """Eres traductor de Yakuza 5 al español neutro latinoamericano. Estos textos van DIBUJADOS en una imagen del juego
y la traducción actual no cabe. Para cada id da una versión MÁS CORTA, con el mismo sentido, que no pase de "max" letras
(cuenta espacios). Usa abreviaturas solo si no hay otra forma (p. ej. «izq.», «der.»). Conserva / y los símbolos △○✕□.
Devuelve SOLO JSON {"t": {"id": "texto corto"}}.
"""

def main():
    bloques = json.load(open(os.path.join(T, 'bloques.json'), encoding='utf-8'))
    gen, _ = traducciones(); es = {}
    for clave, b in bloques.items():
        t = gen.get(norm(b['juego'])) if b['juego'] else gen.get(b['en'])
        if t: es[clave] = t.replace('\r\n', ' ').replace('\n', ' ')
    cortos = json.load(open(CORTOS, encoding='utf-8')) if os.path.exists(CORTOS) else {}
    casos = {}
    for l in open(os.path.join(T, 'avisos.txt'), encoding='utf-8'):
        m = re.match(r'(.+?\.dds): no cabe[^:]*: (.*)', l.rstrip('\n'))
        if not m: continue
        ruta, txt = m.groups()
        for clave, t in es.items():
            if clave.startswith(ruta + '#') and t.startswith(txt[:30]) and clave not in cortos:
                en = bloques[clave]['en']
                casos[clave] = {'en': en, 'es': t, 'max': max(len(en), int(len(t) * 0.8))}
    TG.log(f'{len(casos)} textos para acortar')
    ids = list(casos)
    for i in range(0, len(ids), 40):
        trozo = {str(n): casos[k] for n, k in enumerate(ids[i:i + 40])}
        r, m = TG.pedir(ENCARGO + '\n' + json.dumps(trozo, ensure_ascii=False, indent=0))
        if r is None: continue
        t = r.get('t', r) if isinstance(r, dict) else {}
        for n, k in enumerate(ids[i:i + 40]):
            v = t.get(str(n))
            if isinstance(v, str) and v.strip() and len(v) < len(casos[k]['es']): cortos[k] = v.strip()
        json.dump(cortos, open(CORTOS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        TG.log(f'{min(i + 40, len(ids))}/{len(ids)} ({m})')

if __name__ == '__main__':
    main()
