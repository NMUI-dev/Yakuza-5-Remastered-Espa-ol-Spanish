# -*- coding: utf-8 -*-
"""(01-11-2026, claude1) Títulos de capítulo (pause_en.par, picture/chapter): en la v1.0.1 solo se tradujo «CAPÍTULO N»;
el subtítulo («BACKSTAGE DREAMS», en dos tamaños) seguía en inglés. Ahora se redibuja la textura entera con los mismos
bloques del OCR (trabajo/imagenes/bloques.json), «CAPÍTULO N» de cortos.json y el subtítulo del lote 315.
Salida aparte (no pisa la v1.0.1): trabajo/imagenes/es_v102/pausepar_pause_en/picture/chapter/*.dds + revision_v102/
  python herramientas/capitulos_v102.py"""
import os, sys, json
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv, _argv = sys.argv[:1], sys.argv
import aplicar_extra as AX
sys.argv = _argv
import paginas_es as P, atlas_es
from imagenes_lotes import validas
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
FIJOS = {'DESTINATIONS': 'DESTINOS', 'THEWAYOFRESOLVE': 'UNA FIRME DECISIÓN', 'THE WAY OF RESOLVE': 'UNA FIRME DECISIÓN'}          # (sin lote; los nombres propios se quedan igual)


def main():
    I = os.path.join(T, 'imagenes')
    bloques = json.load(open(os.path.join(I, 'bloques.json'), encoding='utf-8'))
    ocr = json.load(open(os.path.join(I, 'ocr.json'), encoding='utf-8'))
    cortos = json.load(open(os.path.join(I, 'cortos.json'), encoding='utf-8'))
    gen = AX.traducciones()
    atlas_es.TEX, atlas_es.SAL = os.path.join(T, 'extraido'), os.path.join(I, 'es_v102')
    rev = os.path.join(I, 'revision_v102'); os.makedirs(rev, exist_ok=True)
    rutas = sorted(r for r in ocr if '/picture/chapter/' in r)
    n, falta = 0, []
    for ruta in rutas:
        es = {}
        for k, v in bloques.items():
            if k.startswith(ruta + '#'):
                t = FIJOS.get(v['en'].strip()) or gen.get(AX.norm(v['en']))
                if t: es[k] = t
                elif v['en'].strip() and k not in cortos: falta.append((k, v['en']))
        es.update({k: v for k, v in cortos.items() if k.startswith(ruta + '#')})
        if not es: continue
        lineas = validas(ocr[ruta])
        # paginas_es._basura toma «...RESOLVE» por la marca de agua de los dardos («LVE», menos de 16 letras) y no lo
        # dibujaba: con un «!» al final ya no; la traducción va entonces por número de bloque (la misma)
        lineas = [l[:4] + [l[4] + '!'] + l[5:] if 'LVE' in l[4].replace(' ', '') else l for l in lineas]
        img, av = P.traducir_textura(ruta, lineas, es)
        if img is None: continue
        atlas_es.guardar_dds(ruta[:-4], img); n += 1
        v = Image.new('RGBA', img.size, (60, 60, 60, 255)); v.alpha_composite(img)
        v.convert('RGB').resize((img.width // 2, img.height // 2)).save(os.path.join(rev, ruta.split('/')[-1][:-4] + '.png'))
        if av: print(ruta, av)
    print('texturas', n, 'bloques sin traducción', falta)


if __name__ == '__main__': main()
