# -*- coding: utf-8 -*-
"""Dice el formato de una o varias imágenes .dds y la orden de texconv para guardar la imagen nueva igual. Solo lee.

  python dds_formato.py <archivo.dds> [más archivos .dds]

Sirve para no cambiar de formato al traducir una imagen: el juego espera el mismo tamaño, compresión y mipmaps."""
import os, struct, sys

DX10 = {71: 'BC1_UNORM', 72: 'BC1_UNORM_SRGB', 74: 'BC2_UNORM', 75: 'BC2_UNORM_SRGB', 77: 'BC3_UNORM', 78: 'BC3_UNORM_SRGB',
        80: 'BC4_UNORM', 83: 'BC5_UNORM', 87: 'B8G8R8A8_UNORM', 91: 'B8G8R8A8_UNORM_SRGB', 28: 'R8G8B8A8_UNORM',
        29: 'R8G8B8A8_UNORM_SRGB', 98: 'BC7_UNORM', 99: 'BC7_UNORM_SRGB'}
CC = {b'DXT1': 'BC1_UNORM', b'DXT3': 'BC2_UNORM', b'DXT5': 'BC3_UNORM', b'ATI1': 'BC4_UNORM', b'ATI2': 'BC5_UNORM'}


def formato(p):
    """(ancho, alto, mipmaps, formato de texconv, ¿lleva cabecera DX10?)"""
    with open(p, 'rb') as f:
        b = f.read(148)
    if b[:4] != b'DDS ':
        raise ValueError('no es un .dds')
    alto, ancho = struct.unpack('<II', b[12:20])
    mips = max(1, struct.unpack('<I', b[28:32])[0])
    cc = b[84:88]
    if cc == b'DX10':
        n = struct.unpack('<I', b[128:132])[0]
        return ancho, alto, mips, DX10.get(n, f'DXGI_{n}'), True
    if cc in CC:
        return ancho, alto, mips, CC[cc], False
    return ancho, alto, mips, 'B8G8R8A8_UNORM', False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        w, h, m, f, dx = formato(p)
        print(f'{os.path.basename(p)}: {w}x{h}, {m} mipmaps, {f}')
        print(f'  texconv -nologo -y -f {f} -m {m} {"-dx10 " if dx else ""}-o <carpeta de salida> <imagen>.png')
