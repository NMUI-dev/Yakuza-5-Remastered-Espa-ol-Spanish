# Lector/escritor de las tablas .bin de Yakuza 5 (cabecera 20 07 03 19, big endian). Ver PASO_A_PASO.txt.
# Cabecera: u16 0x2007, u16 0x0319, u32 n_columnas, u32 n_filas, u32 0; luego n_columnas x 64 bytes:
#   nombre[48], u32 tipo, u32 cuenta, u32 tamaño_datos, u32 0. Los datos de las columnas van seguidos, en orden.
# Tipos: 0 y 3 = un texto por fila (separados por \0); 2 y 5 = dispersa (cuenta x [u16 fila, texto\0]);
#        1 = diccionario (cuenta textos \0 + un byte por fila con el índice); otros tipos = números, se copian tal cual.
# A veces sobran bytes (relleno) tras los textos: se guardan en 'resto' y se vuelven a poner igual.
import struct
MAGIA = b'\x20\x07\x03\x19'
NUL = b'\x00'


def es_tabla(b):
    return b[:4] == MAGIA and len(b) > 16


def leer(b):
    nc, nf = struct.unpack('>II', b[4:12]); cols = []; o = 0x10 + 64 * nc
    for i in range(nc):
        h = 0x10 + 64 * i; nombre = b[h:h + 48].split(NUL)[0].decode('cp932', 'replace')
        tipo, cuenta, tam, z = struct.unpack('>4I', b[h + 48:h + 64]); d = b[o:o + tam]; o += tam
        c = dict(nombre=nombre, tipo=tipo, cuenta=cuenta, z=z, crudo=d, cab=b[h:h + 48])
        try:
            if tipo in (0, 3):
                p = d.split(NUL, cuenta); assert len(p) == cuenta + 1 and set(p[-1]) <= {0}, 'faltan textos'
                c['filas'] = p[:cuenta]; c['resto'] = p[-1]
            elif tipo in (2, 5):
                v = []; q = 0
                for k in range(cuenta):
                    fila = struct.unpack('>H', d[q:q + 2])[0]; e = d.index(NUL, q + 2); v.append([fila, d[q + 2:e]]); q = e + 1
                assert set(d[q:]) <= {0}; c['dispersa'] = v; c['resto'] = d[q:]
            elif tipo == 1:
                p = d.split(NUL, cuenta); assert len(p[cuenta]) == nf
                c['dicc'] = p[:cuenta]; c['indices'] = p[cuenta]
        except (AssertionError, ValueError, struct.error):
            for k in ('filas', 'dispersa', 'dicc', 'resto', 'indices'): c.pop(k, None)
        cols.append(c)
    assert o == len(b), (o, len(b))
    return dict(nc=nc, nf=nf, cab=b[:16], cols=cols)


def escribir(t):
    cab = bytearray(t['cab']); datos = bytearray()
    for c in t['cols']:
        if 'filas' in c: d = b''.join(x + NUL for x in c['filas']) + c['resto']
        elif 'dispersa' in c: d = b''.join(struct.pack('>H', f) + x + NUL for f, x in c['dispersa']) + c['resto']
        elif 'dicc' in c: d = b''.join(x + NUL for x in c['dicc']) + c['indices']
        else: d = c['crudo']
        cab += c['cab'] + struct.pack('>4I', c['tipo'], c['cuenta'], len(d), c['z']); datos += d
    return bytes(cab + datos)


def textos(t):
    """(columna, clave, texto) de todas las celdas con texto."""
    for c in t['cols']:
        if 'filas' in c:
            for i, x in enumerate(c['filas']): yield c['nombre'], ('f', i), x
        elif 'dispersa' in c:
            for i, (f, x) in enumerate(c['dispersa']): yield c['nombre'], ('d', i), x
        elif 'dicc' in c:
            for i, x in enumerate(c['dicc']): yield c['nombre'], ('k', i), x


def poner(t, col, clave, valor):
    for c in t['cols']:
        if c['nombre'] != col: continue
        k, i = clave
        if k == 'f': c['filas'][i] = valor
        elif k == 'd': c['dispersa'][i][1] = valor
        elif k == 'k': c['dicc'][i] = valor
        return
    raise KeyError(col)
