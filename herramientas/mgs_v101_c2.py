# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) v1.0.1: guías de controles 2d_*_mgs_* (mi mitad: revision_v101/A_mitad_claude2.json).
Fallos de la v1.0: la etiqueta izquierda invadía la columna del botón, «Botón» sin su símbolo, textos que se salían.
Se parte del ORIGINAL. Cada renglón del OCR a doble tamaño se clasifica en su COLUMNA:
  acción izq. (alineada a la derecha, dentro de su barra) | botón izq. (alineado a la izquierda, azul)
  botón der. (alineado a la derecha) | acción der. (alineada a la izquierda, dentro de su barra) | título (centrado)
Se traduce con los mismos términos de la v1.0 (paginas_es._mgs_linea) y los botones con una tabla fija; el símbolo del
botón (△ ○ □ ×) se reconoce comparando su dibujo con los de la fuente de símbolos. Cada texto cabe en su sitio: se achica
hasta el 55 %; si aun así no cabe, se avisa.
  python herramientas/mgs_v101_c2.py [filtro]  -> trabajo/imagenes/es_v101 + revision_v101/rehechas/A_*.png
"""
import os, sys, json, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
import paginas_v101 as PV
import paginas_es as P
from aplicar import norm as anorm
SEG = 'C:/Windows/Fonts/segoeui.ttf'; SIM = 'C:/Windows/Fonts/seguisym.ttf'
BOTONES = {'leftstick': 'Stick izq.', 'rightstick': 'Stick der.', 'touchpadbutton': 'Panel táctil',
           'optionsbutton': 'Botón OPTIONS', 'l1button': 'Botón L1', 'l2button': 'Botón L2', 'r1button': 'Botón R1',
           'r2button': 'Botón R2', 'l3button': 'Botón L3', 'r3button': 'Botón R3', 'directionalbuttons': 'Botones de dirección',
           'directionalbutton': 'Botones de dirección', 'leftstickr3': 'Stick izq.', 'sharebutton': 'Botón SHARE'}
SIMBOLOS = '△○□×'
CORTOS = {'Mover cámara (solo en primera persona)': 'Mover cámara (1.ª persona)', 'R1+R2: recoger sedal (doble velocidad)': 'R1+R2: recoger rápido',
          'L1+L2: soltar carrete (doble velocidad)': 'L1+L2: soltar rápido', 'Confirmar apuesta/Lanzar dados': 'Apostar/Lanzar dados',
          'Invertir controles del stick izquierdo': 'Invertir stick izq.'}


from imagenes_lotes import arreglar as _arr
def nt(t): return re.sub(r'\s', '', _arr(t or '').lower())   # igual que paginas_es (conserva △○□✕)
P._BLOQUES = json.load(open(os.path.join(PV.T, 'imagenes', 'bloques.json'), encoding='utf-8'))


def simbolo(a, l):
    """símbolo dibujado delante de «Button» (△ ○ □ ×): primera mancha de tinta del renglón, por su forma"""
    h = l[3] - l[1]; x0 = max(0, l[0] - 2); z = a[max(0, l[1] - 2):l[3] + 2, x0:l[0] + int(h * 1.6), :3].max(2)
    if z.size == 0 or z.max() < 40: return None
    m = (z > z.max() * 0.45).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(cv2.dilate(m, np.ones((2, 2), np.uint8)))
    comp = [k for k in range(1, n) if st[k][4] > 6 and st[k][3] > 0.45 * h and st[k][2] < 1.4 * h and st[k][2] > 0.3 * h]
    if not comp: return None
    k = min(comp, key=lambda k: st[k][0]); x, y, w, hh = st[k][:4]
    g = (lab[y:y + hh, x:x + w] == k).astype(np.uint8) * m[y:y + hh, x:x + w]
    g = (cv2.resize(g.astype(np.float32), (24, 24)) > 0.3).astype(float)
    filas = g.mean(1); centro = g[9:15, 9:15].mean(); abajo, arriba = filas[18:].max(), filas[:6].max()
    if centro > 0.4: return '×'
    if abajo > 0.75 and arriba > 0.75: return '□'
    if abajo > 0.75: return '△'
    return '○'


def traducir_boton(a, l):
    t = l[4].strip(); n = re.sub(r'[^a-z0-9]', '', t.lower())
    if n in BOTONES: return BOTONES[n]
    if n.endswith('button') and len(n) <= 8:   # «△Button», «OButton», «Button» (símbolo no leído)
        s = t[0] if t[:1] in SIMBOLOS else simbolo(a, l)
        if s: return 'Botón ' + ('✕' if s == '×' else s)
    r = P._mgs_linea(t, nt)
    return r


def barra(a, y, x, paso):
    """extremo de la barra oscura-azulada a la altura y desde x hacia paso (-1 izq, +1 der)"""
    W = a.shape[1]; fila = a[y, :, :3].astype(int).max(1)
    while 0 < x < W - 1 and fila[x + paso] > 12: x += paso
    return x


def rehacer(ruta):
    a = np.array(Image.open(PV.origen(ruta)).convert('RGBA')); H, W = a.shape[:2]; cx = W / 4   # 2 guías: la de 0..1024
    ls = []
    BOT = re.compile(r'^(.*?)\s*((?:[LR][123]\s*Button)|(?:Left|Right)\s*Stick|Touch\s*Pad\s*Button|OPTIONS\s*Button)$')
    for l in PV.ocr2x(ruta):
        if l[2] - l[0] <= 6: continue
        m = BOT.match(l[4].strip())
        if m and m.group(1) and len(m.group(1)) > 2:   # acción + botón leídos juntos: se corta por el hueco de tinta
            est = l[0] + (l[2] - l[0]) * len(m.group(1)) / len(l[4].strip())
            cols = (a[l[1]:l[3], l[0]:l[2], :3].max(2) > 60).any(0)
            huecos = [x for x in range(2, len(cols) - 2) if not cols[x - 1:x + 2].any()]
            if huecos:
                c = l[0] + min(huecos, key=lambda x: abs(l[0] + x - est))
                ls += [[l[0], l[1], c, l[3], m.group(1), l[5]], [c + 2, l[1], l[2], l[3], m.group(2), l[5]]]; continue
        ls.append(l)
    avisos, cosas = [], []
    # columnas de la guía de la izquierda (la textura lleva la misma guía 2 veces? no: se mira por posición)
    for l in sorted(ls, key=lambda l: (l[1], l[0])):
        mid = (l[0] + l[2]) / 2
        cosas.append(l)
    # clasificación: los botones son los renglones pegados a una línea guía; se reconocen por su texto
    def es_boton(l):
        if l[4].strip().startswith('('): return False   # «(+ Left Stick)» es parte de la acción
        n = re.sub(r'[^a-z0-9]', '', l[4].lower())
        return n in BOTONES or n.endswith('button') or n in ('leftstick', 'rightstick')
    izq = [l for l in cosas if l[2] <= W / 2]; der = [l for l in cosas if l[0] >= W / 2]
    out = []
    centro = (min(l[0] for l in cosas) + max(l[2] for l in cosas)) / 2
    for l in cosas:
        if abs((l[0] + l[2]) / 2 - centro) < 60 and nt(l[4]) in ('controls', 'controles') and l[1] < 0.3 * H:
            out.append(('titulo', [l], 'Controles')); continue
        lado = 'izq' if (l[0] + l[2]) / 2 < centro else 'der'
        if es_boton(l) or nt(l[4]) in ('directional', 'buttons'): out.append(('boton_' + lado, [l], None))
        else: out.append(('accion_' + lado, [l], None))
    # acción en 2 renglones («Adjust Hitting Angle/» + «Position Cue Ball»)
    junt = []
    for k in out:
        if nt(k[1][0][4]) == 'buttons':
            prev = [j for j, q in enumerate(junt) if nt(q[1][-1][4]) == 'directional' and 0 <= k[1][0][1] - q[1][-1][1] < 30]
            if prev: j = prev[-1]; junt[j] = (junt[j][0], junt[j][1] + k[1], 'Botones de/dirección'); continue
        if junt and k[0] == junt[-1][0] and k[0].startswith('accion') and junt[-1][1][-1][4].rstrip().endswith('/') \
                and 0 <= k[1][0][1] - junt[-1][1][-1][3] < 12:
            junt[-1] = (k[0], junt[-1][1] + k[1], None)
        else: junt.append(k)
    trabajos = []
    for tipo, L, es in junt:
        if es is None and L[0][4].strip().startswith('(+'): es = '(+ stick izq.)' if 'left' in L[0][4].lower() else '(+ stick der.)'
        if es is None:
            if tipo.startswith('boton'): es = traducir_boton(a, L[0])
            else:
                en = ' '.join(x[4].strip() for x in L)
                es = P._mgs_linea(en, nt)
                if es is None and len(L) > 1: es = '/'.join(filter(None, [P._mgs_linea(x[4].strip().rstrip('/'), nt) for x in L])) or None
        es = CORTOS.get(es, es)
        if es: es = es.replace('joystick izq.', 'stick izq.').replace('Joystick izq.', 'Stick izq.').replace('joystick der.', 'stick der.').replace('Joystick der.', 'Stick der.')
        if not es: avisos.append(f'sin traducción: «{" ".join(x[4] for x in L)}»'); continue
        m, _ = P.mascara_tinta(a, L[0][:4]); col = P.color_tinta(a, m)
        trabajos.append((tipo, L, es, col))
    import collections
    cb = collections.Counter(t[3] for t in trabajos if t[0].startswith('boton'))
    if cb:
        azul = max(cb, key=lambda c: (c[2] - c[0]) * cb[c])
        trabajos = [(t, L, es, azul if t.startswith('boton') else col) for t, L, es, col in trabajos]
    a2 = P.borrar(a, [[x[0] - 2, x[1], x[2] + 2, x[3]] for t in trabajos for x in t[1]])
    img = Image.fromarray(a2); d = ImageDraw.Draw(img)
    otros = [x for t in trabajos for x in t[1]]
    import statistics
    altos = {}
    for tipo, L, es, col in trabajos: altos.setdefault(tipo.split('_')[0], []).extend(x[3] - x[1] for x in L)
    for tipo, L, es, col in trabajos:
        alto = statistics.median(altos[tipo.split('_')[0]]); tam0 = round(alto * 0.85)   # mismo tamaño en toda la columna
        y0, y1 = L[0][1], L[-1][3]
        partes = es.split('/') if len(L) > 1 and '/' in es else [es]
        if len(L) > 1 and len(partes) == 2 and es != 'Botones de/dirección': partes = [partes[0] + '/', partes[1]]
        # límites horizontales de la columna
        fila = lambda t: [o for tt, LL, _, _ in trabajos if tt == t for o in LL if abs((o[1] + o[3]) / 2 - (L[0][1] + L[0][3]) / 2) < alto * 0.6]
        if tipo == 'accion_izq': x_fin = max(x[2] for x in L); x_ini = barra(a, (y0 + y1) // 2, int(min(x[0] for x in L)), -1) + 4
        elif tipo == 'accion_der': x_ini = min(x[0] for x in L); x_fin = barra(a, (y0 + y1) // 2, int(max(x[2] for x in L)), 1) - 4
        elif tipo == 'boton_izq':
            x_ini = max([L[0][0]] + [o[2] + 5 for o in fila('accion_izq')]); vec = [o[0] for o in otros if o[0] > L[0][2] and abs(o[1] - L[0][1]) < alto]
            x_fin = min([L[0][0] + int((L[0][2] - L[0][0]) * 1.5) + 10] + [v - 6 for v in vec])
        elif tipo == 'boton_der':
            x_fin = min([L[0][2]] + [o[0] - 5 for o in fila('accion_der')]); vec = [o[2] for o in otros if o[2] < L[0][0] and abs(o[1] - L[0][1]) < alto]
            x_ini = max([L[0][2] - int((L[0][2] - L[0][0]) * 1.5) - 10] + [v + 6 for v in vec])
        else: x_ini, x_fin = L[0][0] - 40, L[0][2] + 40
        ancho = max(10, x_fin - x_ini)
        for esc in [x / 100 for x in range(100, 54, -3)]:
            f = ImageFont.truetype(SEG, max(7, round(tam0 * esc)))
            if max(P.largo(p, f) for p in partes) <= ancho: break
        else: avisos.append(f'NO CABE: «{es}» en {ancho}px')
        if esc < 0.75: avisos.append(f'pequeña {int(esc * 100)} %: «{es}»')
        for j, p in enumerate(partes):
            lj = L[min(j, len(L) - 1)]; yc = (lj[1] + lj[3]) / 2 if len(partes) == len(L) else (y0 + y1) / 2 + (j - (len(partes) - 1) / 2) * alto
            w = P.largo(p, f)
            x = x_fin - w if tipo in ('accion_izq', 'boton_der') else ((x_ini + x_fin - w) / 2 if tipo == 'titulo' else x_ini)
            fs = ImageFont.truetype(SIM, f.size)
            for sim, t in P._trozos(p):   # (símbolos con la fuente de símbolos)
                ff = fs if sim else f
                d.text((x, yc), t, font=ff, fill=col + (255,), anchor='lm'); x += ff.getlength(t)
    atlas_es.TEX = os.path.join(PV.T, 'extraido'); atlas_es.SAL = PV.SAL; atlas_es.guardar_dds(ruta[:-4], img)
    o = Image.fromarray(a); bb = o.getbbox()
    v = Image.new('RGBA', (W, H * 2 + 8), (40, 40, 44, 255)); v.alpha_composite(o); v.alpha_composite(img, (0, H + 8))
    v.convert('RGB').save(os.path.join(PV.REV, 'A_' + ruta.split('/')[-1][:-4] + '.png'))
    return avisos


if __name__ == '__main__':
    L = json.load(open(os.path.join(PV.RV, 'A_mitad_claude2.json')))
    for r in L:
        if len(sys.argv) > 1 and not any(x in r for x in sys.argv[1:]): continue
        print(r.split('/')[-1], rehacer(r), flush=True)
