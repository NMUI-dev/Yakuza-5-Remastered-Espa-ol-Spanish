"""(claude2, 25-10-2026, adaptado del de claude1 del Y6) Al guardar una textura editada, el compresor DXT de Pillow recomprime
TODA la imagen y estropea detalles finos que no se tocaron. Este paso devuelve, en el nivel 0, los bloques 4x4 ORIGINALES
(comprimidos tal cual) donde la imagen no cambió de verdad (diferencia fuerte > 60 con 12 px de margen alrededor).
  python -I herramientas/v101_bloques.py <carpeta_con_dds_editadas>   (cada ruta relativa se compara con su original)
"""
import os, sys, struct
import numpy as np, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from revisar_v101 import orig


def main(carpeta):
    tot = nt = 0
    for dp, _, fs in os.walk(carpeta):
        for f in sorted(fs):
            if not f.endswith('.dds'): continue
            nuevo = os.path.join(dp, f); rel = os.path.relpath(nuevo, carpeta).replace(os.sep, '/'); o = orig(rel)
            if not os.path.exists(o): print('sin original', rel); continue
            ob = open(o, 'rb').read(); nb = bytearray(open(nuevo, 'rb').read())
            if ob == bytes(nb) or len(ob) != len(nb) or ob[84:88] not in (b'DXT1', b'DXT3', b'DXT5'): continue
            bs = 8 if ob[84:88] == b'DXT1' else 16
            H, W = struct.unpack('<II', ob[12:20])
            a = np.asarray(Image.open(o).convert('RGBA')).astype(int); b = np.asarray(Image.open(nuevo).convert('RGBA')).astype(int)
            fuerte = (np.abs(a - b).max(2) > 60).astype(np.uint8)
            tocado = cv2.dilate(fuerte, np.ones((25, 25), np.uint8)).astype(bool)
            fila = (W + 3) // 4; n = 0
            for by in range(H // 4):
                for bx in range(W // 4):
                    if not tocado[by*4:by*4+4, bx*4:bx*4+4].any():
                        k = 128 + (by * fila + bx) * bs
                        if nb[k:k+bs] != ob[k:k+bs]: nb[k:k+bs] = ob[k:k+bs]; n += 1
            open(nuevo, 'wb').write(bytes(nb)); tot += n; nt += 1
    print('texturas', nt, 'bloques devueltos al original', tot)


if __name__ == '__main__':
    main(sys.argv[1])
