# -*- coding: utf-8 -*-
"""(01-11-2026, claude1) Compara el TEXTO QUE EL JUEGO MUESTRA en dos carpetas data armadas (p. ej. la entrega y lo que
saca la herramienta para traducir): nombres/opciones y registros de cada .msg de wdr.par, filas de subtitle.par y
cadenas apuntadas en db.devil/en/msg.bin y msg_replacer.bin. Dice cuántos difieren y enseña ejemplos.
  python herramientas/comparar_textos.py <data A> <data B>"""
import os, re, struct, subprocess, sys, tempfile, stat, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraer_extra import nombres_msg
import msg_y5
PT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'partool', 'ParTool.exe')


def extraer(par, dst):
    subprocess.run([PT, 'extract', '-r', par, dst], stdin=subprocess.DEVNULL, capture_output=True, check=True)
    return {os.path.relpath(os.path.join(dp, f), dst).replace(os.sep, '/'): os.path.join(dp, f) for dp, _, fs in os.walk(dst) for f in fs}


def textos_msg(b):
    r = [t for _, t in nombres_msg(b)]
    try: r += [g['texto'].decode('utf-8', 'replace') for g in msg_y5.leer(b)[1]]
    except Exception: pass
    return r


def cadenas_devil(b):
    out = {}
    for p in range(0, len(b) - 3, 4):
        q = struct.unpack('<I', b[p:p + 4])[0]
        if 0 < q < len(b) and b[q - 1] == 0:
            e = b.find(b'\0', q)
            try: out[p] = b[q:e].decode('utf-8')
            except UnicodeDecodeError: pass
    return out


def main(A, B):
    tmp = tempfile.mkdtemp(prefix='y5txt_'); dif = 0; tot = 0; ej = []
    try:
        for par, f in (('wdr_par_en/wdr.par', '.msg'), ('auth/subtitle.par', '.csv')):
            fa, fb = extraer(os.path.join(A, par), os.path.join(tmp, 'a')), extraer(os.path.join(B, par), os.path.join(tmp, 'b'))
            for k in sorted(fa):
                if not k.lower().endswith(f): continue
                ba, bb = open(fa[k], 'rb').read(), open(fb[k], 'rb').read()
                if f == '.msg': ta, tb = textos_msg(ba), textos_msg(bb)
                else:
                    ta = re.findall(r'(?:^|\r\n)\d+\t\d+\t("(?:[^"]|"")*"|[^\t]*)\t', ba.decode('utf-16', 'replace'))
                    tb = re.findall(r'(?:^|\r\n)\d+\t\d+\t("(?:[^"]|"")*"|[^\t]*)\t', bb.decode('utf-16', 'replace'))
                tot += max(len(ta), len(tb))
                for x, y in zip(ta, tb):
                    if x != y:
                        dif += 1
                        if len(ej) < 12: ej.append((par.split('/')[-1], k.split('/')[-1], x[:60], y[:60]))
                dif += abs(len(ta) - len(tb))
            for d in ('a', 'b'): shutil.rmtree(os.path.join(tmp, d), onexc=lambda fn, p, e: (os.chmod(p, stat.S_IWRITE), fn(p)))
        for rel in ('db.devil/en/msg.bin', 'db.devil/en/msg_replacer.bin'):
            ca, cb = cadenas_devil(open(os.path.join(A, rel), 'rb').read()), cadenas_devil(open(os.path.join(B, rel), 'rb').read())
            comunes = set(ca) & set(cb); tot += len(comunes)
            for p in sorted(comunes):
                if ca[p] != cb[p]:
                    dif += 1
                    if len(ej) < 24: ej.append((rel.split('/')[-1], p, ca[p][:60], cb[p][:60]))
    finally:
        shutil.rmtree(tmp, onexc=lambda fn, p, e: (os.chmod(p, stat.S_IWRITE), fn(p)))
    print('textos comparados', tot, 'distintos', dif)
    for e in ej: print('  ', e)


if __name__ == '__main__': main(sys.argv[1], sys.argv[2])
