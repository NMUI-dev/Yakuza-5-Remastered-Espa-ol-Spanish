# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) v1.0.1: pegatinas de purikura (2d_jm_puri_*). La v1.0 las dejó con inglés y español mezclados,
cortadas o en letra lisa. Aquí se parte del ORIGINAL: cada pegatina (mancha opaca) se borra entera (alfa 0) y se escribe el
español con estilo de pegatina: relleno claro + borde grueso del color del original («burbuja», Comic Sans negrita) o
letra a mano con borde fino («mano», Segoe Print). Los nombres propios («Kiryu-san ♥ Riku», «Kamurocho») se quedan.
  python herramientas/puri_v101.py  -> trabajo/imagenes/es_v101 + revision_v101/rehechas
"""
import os, sys, json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
import paginas_v101 as PV
F = 'C:/Windows/Fonts/'
BURBUJA, MANO, SIMB = F + 'comicbd.ttf', F + 'segoeprb.ttf', F + 'seguisym.ttf'
PIC = 'pausepar_pause_en/picture/2d_jm_puri_'
# textura: [(caja o índice de mancha, renglones, estilo)]; caja = (x0, y0, x1, y1) cuando solo se cambia una parte
P = {
    'a2': [(0, ['¡No huyas!'], 'burbuja')],
    'a3': [(0, ['Bienvenido a', 'Sky Finance'], 'burbuja')],
    'h3': [(0, ['Kamurocho,', 'tantos recuerdos'], 'burbuja')],
    'h6': [(0, ['¡La especial de Haruka!', '¡A comer!'], 'mano')],
    'h7': [(0, ['Ojalá lloviera', 'también en Okinawa.'], 'mano')],
    'h8': [(0, ['Algún día quiero subir a la noria', 'con alguien~ (T.T)'], 'mano')],
    'h9': [(0, ['Soy Haru-nyan♥'], 'burbuja')],
    'k5': [(0, ['¡Me encanta', 'verte sonreír!'], 'mano')],
    'k7': [(0, ['Vine al norte'], 'mano')],
    'k8': [(0, ['¡Hola, Nagoya!'], 'mano')],
    'k_kyaba01': [(1, ['Más fideos,', 'bien duros♥'], 'burbuja')],
    'kh02': [((22, 160, 274, 230), ['Bienvenido a'], 'burbuja')],
    'kh03': [(0, ['Si tocas a mi Haruka,', 'te mato.'], 'burbuja'), (1, ['¡Hola, soy Haruka!'], 'burbuja')],
    'kh04': [(0, ['¡Me encanta', 'verte sonreír!'], 'burbuja')],
    'kh05': [(0, ['No te perdono', 'si dejas sobras.'], 'burbuja'), (1, ['¡La especial de Haruka!', '¡A comer!'], 'burbuja')],
    'kh06': [(0, ['El romance', 'nunca se detiene♪'], 'burbuja')],
    'kh07': [(0, ['¡Yo también quiero', 'chuletas de miso!'], 'burbuja'), (1, ['Vas a engordar, Haruka...'], 'burbuja')],
    'sa6': [(0, ['¡Cállate y come!'], 'mano')],
    'sa7': [(0, ['No te metas', 'con la montaña'], 'burbuja')],
    'sa8': [(0, ['¡Dame chuletas de miso!'], 'mano')],
    'si3': [(0, ['Dicen que aquí hay', 'buenos masajes'], 'burbuja')],
    'si5': [(0, ['¡Me encanta', 'verte sonreír!'], 'mano')],
    'si6': [(0, ['¡Trabajaré duro y', 'saldré de deudas!'], 'mano')],
}
ORIGINAL = ['k_k02']   # solo nombres: se queda como el original


def manchas(a):
    m = cv2.dilate((a[..., 3] > 30).astype(np.uint8), np.ones((15, 25), np.uint8))
    n, _, st, _ = cv2.connectedComponentsWithStats(m)
    bl = [st[k][:4] for k in range(1, n) if st[k][4] > 800]
    return sorted([(int(x), int(y), int(x + w), int(y + h)) for x, y, w, h in bl], key=lambda b: b[1])


def colores(a, c):
    z = a[c[1]:c[3], c[0]:c[2]].reshape(-1, 4).astype(int); z = z[z[:, 3] > 220][:, :3]
    if not len(z): return (255, 255, 255), (30, 120, 230)
    br = z.sum(1); fill = np.median(z[br >= np.percentile(br, 85)], 0)
    sat = z.max(1) - z.min(1); bord = np.median(z[sat >= np.percentile(sat, 75)], 0)
    return tuple(int(v) for v in fill), tuple(int(v) for v in bord)


def trozos(s):
    t = []
    for ch in s:
        sim = ch in '♥♪'
        if t and t[-1][0] == sim: t[-1][1] += ch
        else: t.append([sim, ch])
    return t


def largo(s, f, fs): return sum((fs if sim else f).getlength(x) for sim, x in trozos(s))


def escribir(img, caja, renglones, estilo, fill, bord):
    d = ImageDraw.Draw(img); x0, y0, x1, y1 = caja; W, H = x1 - x0, y1 - y0
    ruta = BURBUJA if estilo == 'burbuja' else MANO
    for tam in range(int(H * (0.62 if len(renglones) == 1 else 0.47) * (1 if estilo == 'burbuja' else 1.15)), 8, -1):
        f, fs = ImageFont.truetype(ruta, tam), ImageFont.truetype(SIMB, tam)
        sw = max(2, round(tam * (0.15 if estilo == 'burbuja' else 0.06)))
        paso = tam * (1.0 if estilo == 'burbuja' else 1.05)
        if max(largo(r, f, fs) for r in renglones) + 2 * sw <= W * 1.04 and paso * len(renglones) + 2 * sw <= H * 1.1: break
    alto = paso * len(renglones); y = y0 + (H - alto) / 2 + paso / 2
    for r in renglones:
        x = x0 + (W - largo(r, f, fs)) / 2
        for sim, t in trozos(r):
            ff = fs if sim else f
            if estilo == 'mano':   # como el original: borde oscuro fino, borde rojo y relleno blanco engordado 1 px
                d.text((x, y), t, font=ff, fill=bord + (255,), anchor='lm', stroke_width=sw + 2, stroke_fill=(30, 20, 20, 255))
                d.text((x, y), t, font=ff, fill=bord + (255,), anchor='lm', stroke_width=sw, stroke_fill=bord + (255,))
                d.text((x, y), t, font=ff, fill=fill + (255,), anchor='lm', stroke_width=1, stroke_fill=fill + (255,))
            else:
                d.text((x, y), t, font=ff, fill=fill + (255,), anchor='lm', stroke_width=sw, stroke_fill=bord + (255,))
            x += ff.getlength(t)
        y += paso


def rehacer(clave):
    ruta = PIC + clave + '.dds'
    o = np.array(Image.open(PV.origen(ruta)).convert('RGBA')); a = o.copy()
    if clave not in ORIGINAL:
        bl = manchas(o); trabajos = []
        for c, ren, est in P[clave]:
            caja = bl[c] if isinstance(c, int) else c
            fill, bord = colores(o, caja)
            if est == 'mano': fill = (255, 255, 255)
            a[caja[1]:caja[3], caja[0]:caja[2], 3] = 0
            trabajos.append((caja, ren, est, fill, bord))
        img = Image.fromarray(a)
        for caja, ren, est, fill, bord in trabajos: escribir(img, caja, ren, est, fill, bord)
    else: img = Image.fromarray(a)
    atlas_es.TEX = os.path.join(PV.T, 'extraido'); atlas_es.SAL = PV.SAL
    atlas_es.guardar_dds(ruta[:-4], img)
    H, W = o.shape[:2]
    v = Image.new('RGBA', (W * 2 + 12, H), (40, 40, 44, 255)); v.alpha_composite(Image.fromarray(o)); v.alpha_composite(img, (W + 12, 0))
    v.convert('RGB').save(os.path.join(PV.REV, 'puri_' + clave + '.png'))


if __name__ == '__main__':
    for k in list(P) + ORIGINAL: rehacer(k); print('ok', k, flush=True)
