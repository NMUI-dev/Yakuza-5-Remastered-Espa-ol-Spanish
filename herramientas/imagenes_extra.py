# -*- coding: utf-8 -*-
"""(31-10-2026, claude1) Imágenes en inglés que la revisión de la v1.0.1 no miró (ocr_sin_revisar.py ->
trabajo/telop/ocr_nuevas.json). El usuario: traducir rótulos de escena, dardos y el KARAOKE (letras en inglés y títulos de
las portadas); los créditos finales se quedan en inglés, como el contrato. Las tarjetas de habilidad ya estaban en
español y las marcas (premios UFO, béisbol) se dejan.
Como imagenes_lotes.py (mismos bloques y claves ruta#n), pero NO toca bloques.json ni los lotes 311+: escribe
trabajo/telop/bloques_extra.json y lotes NUEVOS desde el primer número libre (ids desde el máximo + 1).
  python herramientas/imagenes_extra.py"""
import os, re, sys, json, glob
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paginas_es as P
from imagenes_lotes import validas, arreglar, NOTA_OCR
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo'); L = os.path.join(T, 'lotes')
TAM = 150


def que_es(ruta):
    """Contexto para el traductor, o None si la imagen no se traduce."""
    n = ruta.split('/')[-1].lower()
    if '/auth_telop_en' in ruta:
        if n.startswith('ifc_jimaku'): return ('imagen: presentación de personaje en MAYÚSCULAS (nombre propio igual; el cargo se '
                                               'traduce); « / » separa las líneas: deja el mismo número de líneas')
        return 'imagen: rótulo de escena con la fecha y el lugar (p. ej. «A principios de verano, 2011»); nombres de lugar igual'
    if '/karaoke_e' in ruta and n.startswith('2d_jm_ok_'):
        return ('imagen: una línea de la LETRA de una canción de karaoke (traducción inglesa de la letra japonesa); tradúcela '
                'al español natural y corta, de longitud parecida; sin comillas')
    if '/karaoke' in ruta and n.startswith('artwork_back_'):
        return ('imagen: portada de canción de karaoke: título de la canción y créditos («Lyrics by», «Music by»); el '
                'título va traducido entre paréntesis solo si es inglés corriente; nombres propios igual')
    if '/darts_tex' in ruta: return 'imagen: marcador de dardos; etiqueta corta (modo de juego, RESULT, ROUND)'
    return None


def main():
    ocr = json.load(open(os.path.join(T, 'telop', 'ocr_nuevas.json'), encoding='utf-8'))
    bloques, nuevos = {}, {}
    for ruta, lineas in sorted(ocr.items()):
        ctx = que_es(ruta)
        lineas = validas(lineas)
        if ctx is None or not lineas: continue
        if 'MAYÚSCULAS' in ctx:                       # presentación: la textura entera es un rótulo de pincel
            en = ' / '.join(arreglar(l[4]) for l in sorted(lineas, key=lambda l: l[1]))
            bloques[f'{ruta}#pincel'] = {'en': en, 'modo': 'pincel', 'juego': None}
            nuevos.setdefault(en, {'en': en, 'ctx': ctx + NOTA_OCR}); continue
        a = np.asarray(Image.open(os.path.join(T, ruta)).convert('RGBA'))
        modo = P.modo_de(ruta)
        for i, b in enumerate(P.bloques([P.quitar_vineta(a, l) for l in lineas], modo)):
            en = arreglar(b['texto'])
            if not re.search('[A-Za-z]{2}', en) or re.search(r'\d{4,}', en): continue
            bloques[f'{ruta}#{i}'] = {'en': en, 'modo': modo, 'juego': None}
            it = nuevos.setdefault(en, {'en': en, 'ctx': ctx + NOTA_OCR})
            if modo == 'etiquetas' and len(b['lineas']) == 1:
                m = int(len(en.encode('utf-8')) * 1.45) + 4
                it['max'] = min(it.get('max', m), m)
    json.dump(bloques, open(os.path.join(T, 'telop', 'bloques_extra.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    if glob.glob(os.path.join(T, 'telop', 'lotes_hechos.txt')):
        print('los lotes ya se hicieron (telop/lotes_hechos.txt): no se rehacen'); return
    # frases que ya tienen traducción en algún lote: no se mandan otra vez
    ya, mx, nmax = set(), 0, 0
    for f in glob.glob(L + '/lote_[0-9][0-9][0-9].json'):
        nmax = max(nmax, int(f[-8:-5]))
        for e in json.load(open(f, encoding='utf-8')): ya.add(e['en'].strip().lower()); mx = max(mx, e['id'])
    items = [it for it in nuevos.values() if it['en'].strip().lower() not in ya]
    for k, it in enumerate(items): it['id'] = mx + 1 + k
    hechos = []
    for j in range(0, len(items), TAM):
        n = nmax + 1 + j // TAM
        json.dump([{k: it[k] for k in ('id', 'en', 'ctx', 'max') if k in it} for it in items[j:j + TAM]],
                  open(os.path.join(L, f'lote_{n:03d}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        hechos.append(n)
    open(os.path.join(T, 'telop', 'lotes_hechos.txt'), 'w').write(' '.join(map(str, hechos)))
    print('bloques', len(bloques), 'nuevos', len(items), 'lotes', hechos)


if __name__ == '__main__': main()
