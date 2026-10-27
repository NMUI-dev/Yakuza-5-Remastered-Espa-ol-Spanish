# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) Arma la v1.0.1 del Y5:
 1. trabajo/imagenes/es_final = imagenes/es (v1.0) + es_v101 encima (con los bloques DXT originales devueltos donde no
    cambió nada: v101_bloques.py).
 2. imagenes_aplicar.py con ES = es_final -> trabajo/salida_img/data (+ copia en trabajo/salida/data).
 3. Copia a entrega_v101/archivos/data SOLO los .par que llevan imágenes (los textos no cambian respecto a la v1.0) y
    dice qué archivos cambiaron frente a la entrega v1.0.
  python herramientas/armar_v101.py
"""
import os, sys, shutil, hashlib, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
ES, V101, FIN = (os.path.join(T, 'imagenes', x) for x in ('es', 'es_v101', 'es_final'))
TMPV = os.path.join(T, 'imagenes', 'es_v101_bloques')


def md5(p): return hashlib.md5(open(p, 'rb').read()).hexdigest()


def main():
    shutil.rmtree(TMPV, ignore_errors=True); shutil.copytree(V101, TMPV)
    subprocess.run([sys.executable, '-I', os.path.join(R, 'herramientas', 'v101_bloques.py'), TMPV], check=True)
    shutil.rmtree(FIN, ignore_errors=True); shutil.copytree(ES, FIN)
    n = 0
    for dp, _, fs in os.walk(TMPV):
        for f in fs:
            src = os.path.join(dp, f); rel = os.path.relpath(src, TMPV); dst = os.path.join(FIN, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst); n += 1
    print('es_final: v1.0 +', n, 'texturas v1.0.1')
    import imagenes_aplicar as IA
    IA.ES = FIN; IA.main()
    ent = os.path.join(R, 'entrega', 'archivos', 'data'); sal = os.path.join(T, 'salida_img', 'data')
    nueva = os.path.join(R, 'entrega_v101'); shutil.rmtree(nueva, ignore_errors=True)
    shutil.copytree(os.path.join(R, 'entrega'), nueva)
    for dp, _, fs in os.walk(sal):
        for f in fs:
            src = os.path.join(dp, f); rel = os.path.relpath(src, sal); vieja = os.path.join(ent, rel)
            if not os.path.exists(vieja): print('NUEVO (no estaba en la v1.0):', rel); continue
            if md5(src) != md5(vieja): shutil.copy2(src, os.path.join(nueva, 'archivos', 'data', rel)); print('cambia', rel)
            else: print('igual', rel)


if __name__ == '__main__': main()
