# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Párrafos de las páginas de reglas cuya traducción quedó INCOMPLETA (los ayudantes se
saltaron frases: el resto se veía en inglés). Si el español es mucho más corto que el inglés, se vuelve a pedir a los
ayudantes gratuitos y se guarda en trabajo/imagenes/cortos.json (imagenes_es.py lo usa antes que el lote).
  python herramientas/reglas_completar.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = [sys.argv[0], 'reglas']
import traductor_gemini as TG
from aplicar import traducciones, norm
T = os.path.join(TG.Y, 'trabajo', 'imagenes'); C = os.path.join(T, 'cortos.json')
b = json.load(open(os.path.join(T, 'bloques.json'), encoding='utf-8')); gen, _ = traducciones()
cortos = json.load(open(C, encoding='utf-8')) if os.path.exists(C) else {}
casos = {}
for k, v in b.items():
    if '/rule_' not in k or k in cortos: continue
    es = gen.get(norm(v['juego'])) if v['juego'] else gen.get(v['en'])
    if es and len(v['en']) > 40 and len(es) < 1.0 * len(v["en"]): casos[k] = v['en']
TG.log(f'{len(casos)} párrafos incompletos')
enc = ("Traduce COMPLETO al español neutro latinoamericano cada párrafo de reglas de un minijuego de Yakuza 5 (texto "
       "leído por OCR de una imagen: puede venir sin espacios entre palabras; corrígelo). Traduce TODAS las frases, sin "
       "resumir. Devuelve SOLO JSON {\"t\": {\"id\": \"traducción\"}}.\n")
ids = list(casos)
for i in range(0, len(ids), 20):
    trozo = {str(n): casos[k] for n, k in enumerate(ids[i:i + 20])}
    r, m = TG.pedir(enc + json.dumps(trozo, ensure_ascii=False, indent=0))
    t = (r.get('t', r) if isinstance(r, dict) else {}) if r else {}
    for n, k in enumerate(ids[i:i + 20]):
        v = t.get(str(n))
        if isinstance(v, str) and len(v) >= 0.85 * len(casos[k]): cortos[k] = ' '.join(v.split())
    json.dump(cortos, open(C, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    TG.log(f'{min(i + 20, len(ids))}/{len(ids)} ({m})')
