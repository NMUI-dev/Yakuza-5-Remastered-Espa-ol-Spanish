# -*- coding: utf-8 -*-
"""(Claude Code, 20-10-2026, adaptado de Yakuza 6) Valida trabajo/lotes/lote_NNN_es.json contra lote_NNN.json.
Comprueba: que estén todos los id; marcas idénticas (<Color:..>, <Italic>, </Italic>, %s/%d); mismo número de saltos de
línea; nada vacío; caracteres que la fuente del juego no tiene (fuera de Latin-1, salvo los del original); restos de
inglés pegados. Sale con código 1 si hay errores.
  python herramientas/validar_lote.py 000 [001 ...]      (o «todos»)
"""
import json, os, re, sys, glob
T = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'trabajo', 'lotes')
MARCA = re.compile(r'</?[A-Za-z_]+(?:[=:][^>]*)?>|%[0-9.]*[dsfx]')
# la letra del juego (font_hd_en, gothic_en/sd_hankaku) es Latin-1; « » se evitan por coherencia con Yakuza 6
PERMITIDOS = (set(chr(c) for c in range(0x20, 0x100)) | set('\n　')) - set('«»')
INGLES = re.compile(r"\b(the|and|you|your|with|this|that|what|don't|I'm|it's|just|really|gonna)\b")

def validar(n):
    orig = json.load(open(os.path.join(T, f'lote_{n}.json'), encoding='utf-8'))
    ruta = os.path.join(T, f'lote_{n}_es.json')
    if not os.path.exists(ruta): return [f'falta {os.path.basename(ruta)}']
    es = json.load(open(ruta, encoding='utf-8')); err = []
    for it in orig:
        k = str(it['id']); en = it['en']; tr = es.get(k)
        if tr is None: err.append(f'{k}: SIN TRADUCIR'); continue
        if not tr.strip() and en.strip(): err.append(f'{k}: vacío'); continue
        if sorted(MARCA.findall(en)) != sorted(MARCA.findall(tr)):
            err.append(f'{k}: marcas distintas {MARCA.findall(en)} -> {MARCA.findall(tr)}')
        if en.count('\n') != tr.count('\n'):
            err.append(f'{k}: saltos de línea {en.count(chr(10))} -> {tr.count(chr(10))}')
        if it.get('max') is not None and len(tr.encode('utf-8')) > it['max']:
            err.append(f'{k}: {len(tr.encode("utf-8"))} bytes > máximo {it["max"]} (frase de guion: tiene que caber)')
        raros = {c for c in tr if c not in PERMITIDOS and c not in en}
        if raros: err.append(f'{k}: caracteres que la fuente no tiene: {"".join(sorted(raros))}')
        ing = set(INGLES.findall(tr)) if len(tr) > 25 else set()
        if len(ing) >= 2 and tr != en: err.append(f'{k}: parece que quedó inglés: {sorted(ing)}')
    sobran = set(es) - {str(it['id']) for it in orig}
    if sobran: err.append(f'id que no son de este lote: {sorted(sobran)[:5]}')
    return err

if __name__ == '__main__':
    nums = [os.path.basename(p)[5:8] for p in sorted(glob.glob(os.path.join(T, 'lote_???.json')))] if sys.argv[1:] == ['todos'] else sys.argv[1:]
    malo = False
    for n in nums:
        e = validar(n)
        print(f'lote {n}: ' + ('OK' if not e else f'{len(e)} errores'))
        for x in e[:40]: print('   ', x)
        malo |= bool(e)
    sys.exit(1 if malo else 0)
