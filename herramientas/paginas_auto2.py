# -*- coding: utf-8 -*-
"""(claude1, 21-10-2026) 2.ª pasada de paginas_auto.sh (FULL AHORRO, sin Fable): en los borradores dejados SOLO por
«sin traducción», pide esas traducciones de una vez a los ayudantes gratuitos (traductor_gemini.pedir), las pone, y vuelve
a probar el atlas con gemma4; se acepta si gemma4 marca 0 y no queda nada «revisar».
  python herramientas/paginas_auto2.py
"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_semi as S
from atlas_borrador import BORR
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRU = os.path.join(S.T, 'atlas_pruebas'); DEJ = os.path.join(R, 'tareas', 'paginas_auto_dejadas.txt')
SIN = 'sin traducción'
ids = [l.split()[0] for l in open(DEJ, encoding='utf-8') if l.strip()]
specs = {i: json.load(open(os.path.join(BORR, i + '.json'), encoding='utf-8')) for i in ids if os.path.exists(os.path.join(BORR, i + '.json'))}
tr = json.load(open(S.TR, encoding='utf-8')) if os.path.exists(S.TR) else {}
falta = sorted({it['en'] for d in specs.values() for it in d['items'] if it.get('revisar', '').startswith(SIN) and it['en'] not in tr})
print(len(specs), 'borradores;', len(falta), 'rótulos sin traducción', flush=True)
sys.argv = [sys.argv[0], 'semi']
import traductor_gemini as TG
encargo = ("Traduce al español neutro latinoamericano estos textos que van dibujados en imágenes de Yakuza 5 (menús, reglas de "
           "minijuegos, avisos). Del largo del inglés o poco más; respeta MAYÚSCULAS; frases completas, sin saltarte nada. "
           "Nombres propios, marcas y títulos de canciones se dejan igual. Devuelve SOLO JSON {\"t\": {\"id\": \"traducción\"}}.\n")
# (21-10, usuario) COHERENCIA: no cambiar términos que ya están en español en el juego -> glosario con las frases del
# juego (1-4 palabras) que aparecen dentro de cada rótulo
import re
juego = S.del_juego()
def glosario(textos):
    g = {}
    for t in textos:
        w = re.findall(r"[a-z0-9'-]+", t.lower())
        for n in range(4, 0, -1):
            for a in range(len(w) - n + 1):
                f = ' '.join(w[a:a + n])
                if f in juego and len(f) > 3 and len(g) < 80: g[f] = juego[f]
    return g
for k in range(0, len(falta), 60):
    trozo = falta[k:k + 60]; g = glosario(trozo)
    gl = ("OBLIGATORIO, términos que el juego YA usa en español (úsalos igual): " + json.dumps(g, ensure_ascii=False) + chr(10)) if g else ''
    r, m = TG.pedir(encargo + gl + json.dumps({str(n): t for n, t in enumerate(trozo)}, ensure_ascii=False, indent=0))
    t = (r.get('t', r) if isinstance(r, dict) else {}) if r is not None else {}
    for n, en in enumerate(trozo):
        if isinstance(t.get(str(n)), str) and t[str(n)].strip(): tr[en] = t[str(n)].strip()
    json.dump(tr, open(S.TR, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{min(k + 60, len(falta))}/{len(falta)} ({m})', flush=True)
quedan = []
for i, d in specs.items():
    for it in d['items']:
        if it.get('revisar', '').startswith(SIN) and tr.get(it['en']):
            it['es'] = S.estilo(it['en'], tr[it['en']].replace('\n', ' ')); del it['revisar']
    json.dump(d, open(os.path.join(BORR, i + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if any('revisar' in it for it in d['items']): quedan.append(f'{i} (revisar)'); continue
    subprocess.run([sys.executable, os.path.join(R, 'herramientas', 'atlas_probar.py'), 'probar', i], capture_output=True)
    try: m = len(json.load(open(os.path.join(PRU, i + '_gemma.json'), encoding='utf-8')))
    except Exception: m = 99
    if m == 0:
        subprocess.run([sys.executable, os.path.join(R, 'herramientas', 'atlas_probar.py'), 'aceptar', i], capture_output=True); print(i, 'ACEPTADO', flush=True)
    else: quedan.append(f'{i} (gemma {m})')
open(os.path.join(R, 'tareas', 'paginas_auto2_dejadas.txt'), 'w', encoding='utf-8').write('\n'.join(quedan) + '\n')
print('FIN', len(specs) - len(quedan), 'aceptados,', len(quedan), 'en inglés', flush=True)
