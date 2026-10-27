# -*- coding: utf-8 -*-
"""(Claude Code, 20-10-2026) Dibuja en español todas las imágenes con texto leídas por OCR.
Para cada bloque de trabajo/imagenes/bloques.json (imagenes_lotes.py) busca la traducción: la del juego si el texto ya
era una frase del juego, o la de los lotes de imágenes (311 en adelante). Bloques sin traducir o iguales al inglés
(nombres) no se tocan. Luego paginas_es.traducir_textura borra el inglés y escribe el español.
Salida: trabajo/imagenes/es/<raíz>/<ruta>.dds + trabajo/imagenes/revision/*.png + trabajo/imagenes/avisos.txt
  python herramientas/imagenes_es.py [filtro]      (filtro: parte de la ruta, p. ej. rule_ o _mgs_)
"""
import os, sys, json, glob
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paginas_es as P, atlas_es
from ocr_imagenes import origen
from aplicar import traducciones, norm
from imagenes_lotes import validas
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')


def main(filtro=''):
    bloques = json.load(open(os.path.join(T, 'imagenes', 'bloques.json'), encoding='utf-8'))
    ocr = json.load(open(os.path.join(T, 'imagenes', 'ocr.json'), encoding='utf-8'))
    gen, _ = traducciones()
    es, falta = {}, 0
    for clave, b in bloques.items():
        if filtro not in clave: continue
        t = gen.get(norm(b['juego'])) if b['juego'] else gen.get(b['en'])
        if t is None: falta += 1; continue
        es[clave] = t.replace('\r\n', ' ').replace('\n', ' ')
    # (21-10) versiones cortas de los textos que no cabían (imagenes_cortos.py)
    cortos_p = os.path.join(T, 'imagenes', 'cortos.json')
    cortos = json.load(open(cortos_p, encoding='utf-8')) if os.path.exists(cortos_p) else {}
    es.update({k: v for k, v in cortos.items() if filtro in k and (k in es or '/chapter/' in k or k in bloques)})   # capítulos y renglones nuevos (renglones_perdidos.py)
    rutas = sorted({k.split('#')[0] for k in es}); avisos = []; pendientes = {}
    if '--solo-cortos' in sys.argv: rutas = sorted({k.split('#')[0] for k in cortos})
    os.environ.setdefault('ROT_FUENTE', 'CaveatBrush-Regular.ttf'); os.environ.setdefault('ROT_ESTRECHO', '0.95'); os.environ.setdefault('ROT_GROSOR', '5')
    import rotulos
    rev = os.path.join(T, 'imagenes', 'revision'); os.makedirs(rev, exist_ok=True)
    # (21-10) texturas hechas A MANO (atlas_es.json, textos_menu_es.py): esta pasada NO las toca (antes las pisó)
    import textos_menu_es
    manuales = set(json.load(open(os.path.join(T, 'imagenes', 'atlas_es.json'), encoding='utf-8'))) | set(textos_menu_es.TRABAJOS) | \
        set(open(os.path.join(T, 'imagenes', 'manuales.txt'), encoding='utf-8').read().split())
    rutas = [r for r in rutas if r[:-4] not in manuales and not r.startswith(('ui_en/', '2dpar_ui_en/'))]   # atlas: atlas_auto.py
    for ruta in rutas:
        # los bloques se recalculan igual que en imagenes_lotes (mismo OCR, mismo orden): la clave ruta#n coincide
        try:
            if f'{ruta}#pincel' in es:
                if es[f'{ruta}#pincel'].strip() == bloques[f'{ruta}#pincel']['en'].strip(): continue   # nombres: igual
                o = Image.open(origen(ruta)).convert('RGBA')
                img, av = rotulos.dibujar(o, [x.strip() for x in es[f'{ruta}#pincel'].split(' / ')], semilla=len(ruta)), []
            else: img, av = P.traducir_textura(ruta, validas(ocr[ruta]), es)
        except Exception as e: avisos.append(f'{ruta}: ERROR {e}'); continue
        if img is None: continue
        atlas_es.TEX = os.path.join(T, 'extraido_r' if ruta.startswith('ui_en/') else 'extraido')
        try: atlas_es.guardar_dds(ruta[:-4], img)
        except ValueError as e: avisos.append(f'{ruta}: PENDIENTE {e}'); pendientes[ruta] = img; continue   # (21-10) BC7: aparte
        o = Image.open(origen(ruta)).convert('RGBA'); W, H = o.size
        v = Image.new('RGBA', (W, H * 2), (40, 90, 40, 255)); v.alpha_composite(o); v.alpha_composite(img, (0, H))
        v.convert('RGB').save(os.path.join(rev, ruta.replace('/', '__')[:-4] + '.png'))
        avisos += [f'{ruta}: {a}' for a in av]
    os.makedirs(os.path.join(T, 'imagenes', 'pendientes_bc7'), exist_ok=True)
    for r, im in pendientes.items(): im.save(os.path.join(T, 'imagenes', 'pendientes_bc7', r.replace('/', '__')[:-4] + '.png'))
    open(os.path.join(T, 'imagenes', 'avisos_cortos.txt' if '--solo-cortos' in sys.argv else 'avisos.txt'), 'w', encoding='utf-8').write('\n'.join(avisos))
    print('texturas', len(rutas), 'bloques traducidos', len(es), 'sin traducción aún', falta, 'avisos', len(avisos))


if __name__ == '__main__': main(next((a for a in sys.argv[1:] if not a.startswith('--')), ''))
