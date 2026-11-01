# -*- coding: utf-8 -*-
"""(01-11-2026, claude1; el usuario: «compara con la versión original para que no falten textos o algo parecido»)
Compara la entrega armada (v1.0.1 + trabajo/salida_v102 encima) con los ORIGINALES del juego, archivo por archivo:
  - .par: la misma lista de archivos dentro (ni falta ni sobra ninguno), y cada .dds con el mismo tamaño
  - .msg: el mismo número de registros de nombres/opciones (tabla de 0x0E/0x10)
  - subtítulos CSV: las mismas filas (tiempos iguales) y ninguna vacía
  - .bin ARMP de db.devil: los mismos punteros de tabla apuntando a una cadena (ninguno roto)
Originales: trabajo/respaldos/respaldo_original_y5_steam_2510 (los 29 de la v1.0.1) y, para lo que no tocaba la
v1.0.1, el juego (Y5_JUEGO, que no lleva esos archivos cambiados). Solo lee.
  python herramientas/comparar_original.py"""
import glob, os, re, struct, subprocess, sys, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraer_extra import nombres_msg
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
PT = os.path.join(R, 'herramientas', 'partool', 'ParTool.exe')
JUEGO = os.environ.get('Y5_JUEGO', 'D:/SteamLibrary/steamapps/common/Yakuza 5/main/data')
RESP = os.path.join(T, 'respaldos', 'respaldo_original_y5_steam_0111')     # (01-11) los 35 originales de la v1.0.2+
if not os.path.isdir(RESP): RESP = os.path.join(T, 'respaldos', 'respaldo_original_y5_steam_2510')
V101 = os.path.join(R, 'entrega_v101', 'archivos', 'data'); V102 = os.path.join(T, 'salida_v102', 'data')
DB_ORIG = os.path.join(T, 'db_en')                                  # msg_replacer.bin original (md5 e150ab5c7625)
# (01-11) python comparar_original.py <carpeta data de una entrega>: compara esa carpeta entera (p. ej. entrega_v103)
ENTREGAS = [sys.argv[1]] if len(sys.argv) > 1 else [V102, V101]


def entrega(rel):
    for d in ENTREGAS:
        if os.path.exists(os.path.join(d, rel)): return os.path.join(d, rel)


def original(rel):
    for p in (os.path.join(RESP, rel), os.path.join(DB_ORIG, os.path.basename(rel)) if rel.startswith('db.devil/en/msg_replacer') else '',
              os.path.join(JUEGO, rel)):
        if p and os.path.exists(p): return p


def extraer(par, dst):
    subprocess.run([PT, 'extract', '-r', par, dst], stdin=subprocess.DEVNULL, capture_output=True, check=True)
    return {os.path.relpath(os.path.join(dp, f), dst).replace(os.sep, '/'): os.path.join(dp, f) for dp, _, fs in os.walk(dst) for f in fs}


def punteros(b):
    def cad(q):
        if not 0 < q < len(b) or b[q - 1] != 0: return False
        try: t = b[q:b.index(b'\0', q)].decode('utf-8')
        except (ValueError, UnicodeDecodeError): return False
        return bool(t)
    return sum(1 for p in range(0, len(b) - 3, 4) if cad(struct.unpack('<I', b[p:p + 4])[0]))


def borrar(d):          # ParTool deja los archivos extraídos como solo lectura
    import stat
    shutil.rmtree(d, onexc=lambda f, p, e: (os.chmod(p, stat.S_IWRITE), f(p)))


def main():
    rels = sorted({os.path.relpath(os.path.join(dp, f), d).replace(os.sep, '/') for d in ENTREGAS for dp, _, fs in os.walk(d) for f in fs})
    fallos = 0; tmp = tempfile.mkdtemp(prefix='y5cmp_')
    try:
        for rel in rels:
            e, o = entrega(rel), original(rel)
            if not o: print('SIN ORIGINAL', rel); fallos += 1; continue
            if rel.endswith('.par'):
                fe = extraer(e, os.path.join(tmp, 'e')); fo = extraer(o, os.path.join(tmp, 'o'))
                faltan, sobran = set(fo) - set(fe), set(fe) - set(fo)
                tam = [k for k in fo if k in fe and k.lower().endswith('.dds') and os.path.getsize(fo[k]) != os.path.getsize(fe[k])]
                msg = [k for k in fo if k in fe and k.endswith('.msg')
                       and len(nombres_msg(open(fo[k], 'rb').read())) != len(nombres_msg(open(fe[k], 'rb').read()))]
                csv = []
                for k in fo:
                    if k in fe and k.lower().endswith('.csv'):
                        to = open(fo[k], 'rb').read().decode('utf-16', 'replace'); te = open(fe[k], 'rb').read().decode('utf-16', 'replace')
                        fo_t = re.findall(r'(?:^|\r\n)(\d+\t\d+)\t', to); fe_t = re.findall(r'(?:^|\r\n)(\d+\t\d+)\t', te)
                        vacias = re.findall(r'(?:^|\r\n)\d+\t\d+\t""\t', te)
                        if fo_t != fe_t or len(vacias) > len(re.findall(r'(?:^|\r\n)\d+\t\d+\t""\t', to)): csv.append(k)
                ok = not (faltan or sobran or tam or msg or csv)
                fallos += not ok
                print(('OK  ' if ok else 'MAL ') + rel, f'{len(fo)} archivos', *(f'{n}: {sorted(x)[:3]}' for n, x in
                      (('faltan', faltan), ('sobran', sobran), ('dds_tamaño', tam), ('msg_nombres', msg), ('csv_filas', csv)) if x))
                borrar(os.path.join(tmp, 'e')); borrar(os.path.join(tmp, 'o'))
            elif rel.endswith('.bin'):
                be, bo = open(e, 'rb').read(), open(o, 'rb').read()
                # tablas rehechas con reARMP (minijuegos): los punteros cambian de sitio; entonces se cuentan las
                # cadenas con letras (las mismas o más: ninguna perdida). Sin bytes de control: «\x03a» de la cabecera
                # contaba como cadena en el original
                cads = lambda b: len(re.findall(rb'(?<=\x00)[^\x00-\x09\x0b-\x1f]*[A-Za-z][^\x00-\x09\x0b-\x1f]*(?=\x00)', b))
                ok = (punteros(be) >= punteros(bo) or cads(be) >= cads(bo)) and be[:4] == bo[:4]
                fallos += not ok
                print(('OK  ' if ok else 'MAL ') + rel, f'punteros a cadena {punteros(bo)} -> {punteros(be)}, cadenas {cads(bo)} -> {cads(be)}')
            else:
                ok = os.path.getsize(e) == os.path.getsize(o); fallos += not ok
                print(('OK  ' if ok else 'MAL ') + rel, 'mismo tamaño' if ok else 'TAMAÑO DISTINTO')
    finally:
        borrar(tmp)
    print('FALLOS', fallos, 'de', len(rels))


if __name__ == '__main__': main()
