# -*- coding: utf-8 -*-
"""(Claude Code, 20-10-2026) Rectángulos UV (en píxeles) que un .sbb de Yakuza 5 usa sobre una textura de W x H.
Los UV son 4 float32 big endian (u0, v0, u1, v1) en [0, 1]. Se listan los que caen en píxeles enteros y cubren tinta.
  python herramientas/sbb_rects.py <archivo.sbb> <textura.dds>
"""
import struct, sys
import numpy as np
from PIL import Image

def rects(sbb, W, H):
    b = open(sbb, 'rb').read(); vistos = set(); res = []
    for o in range(0, len(b) - 16, 4):
        v = struct.unpack('>4f', b[o:o + 16])
        if not all(0 <= x <= 1 for x in v) or not (v[2] > v[0] and v[3] > v[1]): continue
        px = (v[0] * W, v[1] * H, v[2] * W, v[3] * H)
        if any(abs(p - round(p)) > 0.02 for p in px): continue
        r = tuple(int(round(p)) for p in px)
        if r[2] - r[0] < 6 or r[3] - r[1] < 6 or r in vistos or r == (0, 0, W, H): continue
        vistos.add(r); res.append(r)
    return res

if __name__ == '__main__':
    im = np.asarray(Image.open(sys.argv[2]).convert('RGBA'))[..., 3]; H, W = im.shape
    for r in rects(sys.argv[1], W, H):
        tinta = (im[r[1]:r[3], r[0]:r[2]] > 100).mean()
        if tinta > 0.02: print(list(r), round(tinta, 2))
