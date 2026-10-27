# -*- coding: utf-8 -*-
"""(Claude Code, 19-10-2026) Barrido final de calidad sobre TODOS los lote_NNN_es.json (después de la revisión):
español de España, signos ¿¡ desparejados y basura de los modelos (palabras inglesas pegadas, restos de API).
No corrige nada: lista id, lote y frase para revisarlas a mano.
  python -X utf8 herramientas/buscar_fallos.py [máx_por_tipo]
"""
import json, glob, os, re, sys
L = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'trabajo', 'lotes')
MAX = int(sys.argv[1]) if len(sys.argv) > 1 else 40
ESPANA = re.compile(r"\b(vosotr[oa]s|os\b(?= [a-záéíóú])|vuestr[oa]s?|[a-záéíóú]+(?:áis|éis)\b|vale\b(?=[,.!?])|coger|cogí|cogido|"
                    r"t[ií]o\b(?! [A-Z])|t[ií]a\b(?! [A-Z])|guay|mola|curro|pillar|pilla[rsd]?|coño|joder|gilipollas|ordenador|móvil|pulsa\b|pulse\b|"
                    r"vaale|chaval|crío|mogollón|flipar|tronco|majo|hostia|coches?|gafas|zumo|conduc[ei]r|conduzc|aparca[rd]?|enfad|cabre[ao]|currar|chulo|cutre|desmadre|chorrad|ahorita|chido|güey|wey|neta|pinche|órale|che|boludo|pibe|laburo|bacán|chévere|parcero|vos)", re.I)
BASURA = re.compile(r"\b[a-z]+(?:tion|ness)\b|\b[a-z]{2,}ing\b|\bapi\.|openai|content_filter|\b(?:the|and|you|with|this|that|of)\b", re.I)
ABRE = {'?': '¿', '!': '¡'}

def signos(t):
    # cada frase con ? o ! al final debe tener su ¿ o ¡ antes (en cualquier orden si van mezclados)
    for frase in re.findall(r"[^.?!]*[?!]+", t.replace('...', '…')):
        cierra = set(re.search(r"[?!]+$", frase).group())
        for c in cierra:
            if ABRE[c] not in frase: return True
    return False

tipos = {'españa': [], 'signos': [], 'basura': [], 'igual_inglés': []}
for f in sorted(glob.glob(os.path.join(L, 'lote_*_es.json'))):
    n = os.path.basename(f)[5:8]
    en = {str(x['id']): x for x in json.load(open(os.path.join(L, f'lote_{n}.json'), encoding='utf-8'))}
    es = json.load(open(f, encoding='utf-8'))
    for k, t in es.items():
        e = en[k]['en']
        if ESPANA.search(t): tipos['españa'].append((n, k, ESPANA.search(t).group(), t))
        if signos(t): tipos['signos'].append((n, k, '', t))
        b = [m for m in BASURA.findall(t) if m.lower() not in e.lower()]
        if b: tipos['basura'].append((n, k, b[0], t))
        if t == e and len(e) > 12 and re.search(r'[a-z]{4} [a-z]{4}', e) and en[k]['ctx'].split('|')[0] not in ('rumble',):
            tipos['igual_inglés'].append((n, k, '', t))
for tipo, l in tipos.items():
    print(f'== {tipo}: {len(l)}')
    for n, k, m, t in l[:MAX]: print(f'  {n}/{k} [{m}] {t[:110]!r}')
