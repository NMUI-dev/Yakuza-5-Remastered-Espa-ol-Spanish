# -*- coding: utf-8 -*-
"""(Claude Code, 20-10-2026) Textos de las imágenes (OCR) -> lotes de traducción para los ayudantes gratuitos.
  - Junta los renglones del OCR en bloques (paginas_es.bloques) y arregla errores típicos del OCR («L2Button»).
  - Descarta lo que no es inglés (japonés, números, lecturas dudosas).
  - Si el texto ya está entre las frases del juego (unicos_en.json), no se manda: se usará esa traducción.
  - El resto va a trabajo/lotes/lote_311.json en adelante (id desde 70000), con contexto («página de reglas de X»,
    «etiqueta de guía de controles») y, en las etiquetas cortas, «max» de bytes para que quepan.
Escribe trabajo/imagenes/bloques.json {ruta#n: {"en": texto, "modo": ..}} (lo lee imagenes_es.py al dibujar).
  python herramientas/imagenes_lotes.py
"""
import os, re, sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paginas_es as P
from ocr_imagenes import origen
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo'); L = os.path.join(T, 'lotes')
CJK = re.compile(r'[぀-ヿ一-鿿]')
PRIMER_LOTE, PRIMER_ID, TAM = 311, 70000, 150
PINCEL = ('/caption/2d_jm_ac_', '/caption/2d_jm_bc_')   # rótulos de pincel: la textura entera es un texto (líneas con « / »)


def validas(lineas):
    """Renglones que se traducen (los mismos aquí y al dibujar, para que las claves ruta#n coincidan)."""
    return [l for l in lineas if l[5] >= 0.6 and re.search('[A-Za-z]{2}', l[4]) and not CJK.search(l[4])]


def arreglar(t):
    t = re.sub(r'([A-Za-z0-9])Button\b', r'\1 Button', t)
    t = re.sub(r'^[Oo0] ?Button\b', '○ Button', t); t = re.sub(r'^[Xx×] ?Button\b', '✕ Button', t)
    t = t.replace('TouchPad', 'Touch Pad').replace('OPTIONSButton', 'OPTIONS Button').replace('  ', ' ')
    return t.strip()


NOTA_OCR = ('. Texto leído por OCR de una imagen: si parece un error de lectura o es un nombre propio, devuélvelo IGUAL; '
            'puede ser un trozo de un párrafo más largo')


def contexto(ruta, modo):
    return _contexto(ruta, modo) + NOTA_OCR


def _contexto(ruta, modo):
    n = ruta.split('/')[-1][:-4]
    if n.startswith('rule_'): return f'imagen: página de reglas de minijuego ({n}); párrafo de instrucciones'
    if '_mgs_' in n: return f'imagen: guía de controles de minijuego ({n}); etiqueta corta junto a un botón'
    if 'syotitle' in n: return 'imagen: título de capítulo'
    if n.startswith('2d_jm_bc'): return 'imagen: presentación de jefe (nombres propios: se dejan igual; cargos y apodos se traducen)'
    return f'imagen de menú ({n})' + ('; etiqueta corta' if modo == 'etiquetas' else '')


def main():
    ocr = json.load(open(os.path.join(T, 'imagenes', 'ocr.json'), encoding='utf-8'))
    unicos = set(json.load(open(os.path.join(T, 'unicos_en.json'), encoding='utf-8')))
    unicos_n = {u.replace('\r\n', ' ').replace('\n', ' ').strip().lower(): u for u in unicos}
    bloques, nuevos = {}, {}
    for ruta, lineas in sorted(ocr.items()):
        lineas = validas(lineas)
        if not lineas: continue
        if any(p in ruta for p in PINCEL):
            en = ' / '.join(arreglar(l[4]) for l in sorted(lineas, key=lambda l: l[1]))
            juego = unicos_n.get(en.replace(' / ', ' ').lower())
            bloques[f'{ruta}#pincel'] = {'en': en, 'modo': 'pincel', 'juego': None}
            nuevos.setdefault(en, {'en': en, 'ctx': 'imagen: rótulo de pincel en MAYÚSCULAS (objetivo de misión o presentación de '
                               'personaje); « / » separa las líneas: deja el mismo número de líneas; los nombres propios no se traducen' + NOTA_OCR})
            continue
        a = np.asarray(Image.open(origen(ruta)).convert('RGBA'))
        modo = P.modo_de(ruta)
        for i, b in enumerate(P.bloques([P.quitar_vineta(a, l) for l in lineas], modo)):
            en = arreglar(b['texto'])
            if not re.search('[A-Za-z]{2}', en) or re.search(r'\d{4,}', en): continue   # tiras de cifras de los atlas
            clave = f'{ruta}#{i}'
            juego = unicos_n.get(en.lower())
            bloques[clave] = {'en': en, 'modo': modo, 'juego': juego}
            if juego is None:
                it = nuevos.setdefault(en, {'en': en, 'ctx': contexto(ruta, modo)})
                if modo == 'etiquetas' and len(b['lineas']) == 1:
                    m = int(len(en.encode('utf-8')) * 1.45) + 4
                    it['max'] = min(it.get('max', m), m)
    json.dump(bloques, open(os.path.join(T, 'imagenes', 'bloques.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    # lotes nuevos (se rehacen solo si aún no hay ninguna traducción de imágenes)
    if any(os.path.exists(os.path.join(L, f'lote_{n:03d}_es.json')) for n in range(PRIMER_LOTE, PRIMER_LOTE + 50)):
        print('ya hay lotes de imágenes traducidos: no se rehacen'); return
    items = list(nuevos.values())
    for k, it in enumerate(items): it['id'] = PRIMER_ID + k
    for j in range(0, len(items), TAM):
        n = PRIMER_LOTE + j // TAM
        json.dump([{k: it[k] for k in ('id', 'en', 'ctx', 'max') if k in it} for it in items[j:j + TAM]],
                  open(os.path.join(L, f'lote_{n:03d}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('bloques', len(bloques), 'ya en el juego', sum(1 for b in bloques.values() if b['juego']),
          'nuevos', len(items), 'lotes', (len(items) + TAM - 1) // TAM)


if __name__ == '__main__': main()
