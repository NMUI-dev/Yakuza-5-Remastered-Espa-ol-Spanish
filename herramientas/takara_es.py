# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Cartas del tesoro (pausepar_pause_en/picture/takara/2d_jm_takaraX + sus 5 pedazos _01.._05).
Los pedazos son trozos ROTOS de la carta entera (a veces ampliados): traducirlos sueltos salía sin sentido. Aquí:
  1. la carta entera se traduce por párrafos (ayudantes gratuitos; caché en trabajo/imagenes/takara_es.json);
  2. se borra el inglés del pergamino (inpaint) y se escribe el español con letra de serifa en negrita, mismos
     párrafos, margen y color de tinta;
  3. cada pedazo se localiza en la carta (plantilla a varias escalas) y recibe la DIFERENCIA (español - inglés) de esa
     zona: conserva sus bordes quemados y su transparencia, y al juntar los pedazos se lee la carta en español.
Van en trabajo/imagenes/manuales.txt (imagenes_es.py no las toca).   python herramientas/takara_es.py
"""
import json, os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo', 'imagenes')
atlas_es.TEX = os.path.join(R, 'trabajo', 'extraido'); D = 'pausepar_pause_en/picture/takara/'
CACHE = os.path.join(T, 'takara_es.json'); F = 'C:/Windows/Fonts/timesbd.ttf'


def parrafos(lineas):
    ls = sorted(lineas, key=lambda l: l[1]); ps = []; h = np.median([l[3] - l[1] for l in ls])
    for l in ls:
        if ps and l[1] - ps[-1][-1][3] < 0.9 * h: ps[-1].append(l)
        else: ps.append([l])
    return ps


def traducir(textos):
    sys.argv = [sys.argv[0], 'takara']
    import traductor_gemini as TG
    enc = ('Traduce al español neutro latinoamericano esta carta de un juego (Yakuza 5), párrafo por párrafo, con estilo '
           'literario natural. El OCR puede haber pegado palabras: corrígelo. Devuelve SOLO JSON {"t": {"id": "traducción"}} '
           'con los MISMOS ids.\n')
    r, m = TG.pedir(enc + json.dumps({str(i): t for i, t in enumerate(textos)}, ensure_ascii=False, indent=0))
    t = (r.get('t', r) if isinstance(r, dict) else {}) if r else {}
    return [t.get(str(i)) for i in range(len(textos))]


def tinta(a, lineas):
    m = np.zeros(a.shape[:2], np.uint8)
    for x0, y0, x1, y1, *_ in lineas:
        z = a[y0 - 2:y1 + 2, x0 - 2:x1 + 2, :3].astype(int).mean(2)
        m[y0 - 2:y1 + 2, x0 - 2:x1 + 2] = (z < min(np.percentile(z, 60) - 25, 95)).astype(np.uint8) * 255   # solo tinta oscura (no el dibujo)
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=2)


def hoja_es(clave, ocr, cache):
    ruta = D + f'2d_jm_takara{clave}'
    o = Image.open(os.path.join(atlas_es.TEX, ruta + '.dds')).convert('RGBA'); a = np.asarray(o).copy()
    ps = parrafos(ocr[ruta + '.dds'])
    if clave not in cache or any(not x for x in cache[clave]):
        cache[clave] = traducir([' '.join(l[4] for l in p) for p in ps])
        json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    m = tinta(a, [l for p in ps for l in p])
    lum = a[..., :3].astype(int).mean(2); sel = (m > 0) & (lum < np.percentile(lum[m > 0], 15))
    col = tuple(int(c) for c in np.median(a[..., :3][sel], 0))      # el marrón oscuro del centro de las letras
    a[..., :3] = cv2.inpaint(np.ascontiguousarray(a[..., :3]), m, 5, cv2.INPAINT_TELEA)
    limpia = Image.fromarray(a.copy())
    img = Image.fromarray(a); d = ImageDraw.Draw(img)
    x0 = min(l[0] for p in ps for l in p); x1 = int(np.percentile([l[2] for p in ps for l in p], 80))
    h = int(np.median([l[3] - l[1] for p in ps for l in p])) * 0.82   # la caja del OCR incluye colas: cuerpo algo menor
    pasos = [p[i + 1][1] - p[i][1] for p in ps for i in range(len(p) - 1)]
    paso = int(np.median(pasos)) if pasos else int(h * 1.15)
    def caja(p):   # (21-10) cada párrafo en SU sitio: su ancho y su alineación (centrado si el inglés iba centrado)
        a0 = min(l[0] for l in p); a1 = max(l[2] for l in p); cs = [(l[0] + l[2]) / 2 for l in p]
        centrado = len(p) > 1 and max(cs) - min(cs) < 12 and max(l[0] for l in p) - a0 > 12
        cuerpo = len(p) > 1 and not centrado and a1 - a0 > 0.6 * (x1 - x0)
        return (x0, x1, 'izq') if cuerpo else (a0, max(a1, a0 + 40), 'centro' if centrado else ('der' if a0 > o.width * 0.35 and len(p) == 1 else 'izq'))
    for tam in range(int(h * 0.95), 8, -1):          # un solo cuerpo para toda la carta, que quepa en los mismos renglones
        f = ImageFont.truetype(F, tam); ok = True; lay = []
        for k, (p, es) in enumerate(zip(ps, cache[clave])):
            c0, c1, al = caja(p); ancho = (c1 - c0) * (1.08 if al != 'izq' or c1 != x1 else 1.0)
            ren = ['']
            for w in es.split():
                if f.getlength((ren[-1] + ' ' + w).strip()) <= ancho: ren[-1] = (ren[-1] + ' ' + w).strip()
                else: ren.append(w)
            sig = ps[k + 1][0][1] if k + 1 < len(ps) else o.height - 20
            if p[0][3] + (len(ren) - 1) * paso > sig - 4 or len(ren) > max(len(p), 1) + 1: ok = False; break
            lay.append((p[0][3] - 4, ren, c0, c1, al))
        if ok: break
    for yb, ren, c0, c1, al in lay:
        for i, s in enumerate(ren):
            w = f.getlength(s); xx = c0 if al == 'izq' else (c1 - w if al == 'der' else (c0 + c1 - w) / 2)
            d.text((xx, yb + i * paso), s, font=f, fill=col + (255,), anchor='ls')
    global TINTA; TINTA = m
    return o, img, limpia, col


def pedazo(hoja_en, hoja_es, limpia, col, nombre):
    """El pedazo se localiza en la carta; se le BORRA su tinta inglesa y se le pinta la tinta española de esa zona."""
    p = Image.open(os.path.join(atlas_es.TEX, D + nombre + '.dds')).convert('RGBA'); pa = np.asarray(p).copy()
    he = cv2.cvtColor(np.asarray(hoja_en.convert('RGB')), cv2.COLOR_RGB2GRAY).astype(np.float32)
    pg = cv2.cvtColor(pa[..., :3], cv2.COLOR_RGB2GRAY).astype(np.float32)
    mask = (pa[..., 3] > 200).astype(np.uint8)
    ys, xs = np.where(mask); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    tpl = pg[y0:y1, x0:x1]; mk = mask[y0:y1, x0:x1].astype(np.float32)
    def prueba(s):
        hs = cv2.resize(he, None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
        if hs.shape[0] < tpl.shape[0] or hs.shape[1] < tpl.shape[1]: return None
        r = cv2.matchTemplate(hs, tpl, cv2.TM_CCORR_NORMED, mask=mk)
        _, v, _, loc = cv2.minMaxLoc(np.nan_to_num(r, nan=-1, posinf=-1, neginf=-1)); return v, s, loc
    cand = [x for x in (prueba(s) for s in np.arange(0.3, 4.01, 0.02)) if x]
    v, s, _ = max(cand)
    v, s, (lx, ly) = max(x for x in (prueba(s2) for s2 in np.arange(s - 0.02, s + 0.021, 0.002)) if x)
    # 1) borrar la tinta inglesa del pedazo (píxeles oscuros sobre el papel)
    lum = pa[..., :3].astype(int).mean(2); papel = mask > 0
    fondo = cv2.medianBlur(pa[..., :3], 15).astype(int).mean(2)
    tin = (papel & (lum < fondo - 22)).astype(np.uint8) * 255
    tin = cv2.dilate(tin, np.ones((3, 3), np.uint8), iterations=1)
    borde = cv2.erode(mask, np.ones((3, 3), np.uint8), iterations=1) == 0      # el borde quemado no se toca
    tin[borde] = 0
    mi = cv2.resize(TINTA, None, fx=s, fy=s, interpolation=cv2.INTER_NEAREST)
    mm = np.zeros(tin.shape, np.uint8); oy_, ox_ = ly - y0, lx - x0
    ya_, xa_ = max(0, -oy_), max(0, -ox_); yb_, xb_ = min(tin.shape[0], mi.shape[0] - oy_), min(tin.shape[1], mi.shape[1] - ox_)
    if yb_ > ya_ and xb_ > xa_: mm[ya_:yb_, xa_:xb_] = mi[oy_ + ya_:oy_ + yb_, ox_ + xa_:ox_ + xb_]
    tin[cv2.dilate(mm, np.ones((5, 5), np.uint8)) == 0] = 0   # solo las letras: el dibujo (cabina, flechas) no se toca
    rgb = cv2.inpaint(np.ascontiguousarray(pa[..., :3]), tin, 4, cv2.INPAINT_TELEA)
    # 2) tinta española de la misma zona (alfa = cuánto oscurece la letra respecto al papel limpio)
    ci = cv2.resize(np.asarray(limpia.convert('RGB')).astype(np.float32), None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC).mean(2)
    ce = cv2.resize(np.asarray(hoja_es.convert('RGB')).astype(np.float32), None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC).mean(2)
    alfa_h = np.clip((ci - ce) / max(1, np.mean(ci) - np.mean(col)), 0, 1)
    H, W = pa.shape[:2]; ox, oy = lx - x0, ly - y0; alfa = np.zeros((H, W), np.float32)
    yy0, xx0 = max(0, -oy), max(0, -ox); yy1, xx1 = min(H, alfa_h.shape[0] - oy), min(W, alfa_h.shape[1] - ox)
    alfa[yy0:yy1, xx0:xx1] = alfa_h[oy + yy0:oy + yy1, ox + xx0:ox + xx1]
    alfa *= (pa[..., 3] > 0)
    sal = pa.copy(); c = np.array(col, np.float32)
    sal[..., :3] = np.clip(rgb * (1 - alfa[..., None]) + c * alfa[..., None], 0, 255).astype(np.uint8)
    return Image.fromarray(sal), v, s


def main():
    ocr = json.load(open(os.path.join(T, 'ocr.json'), encoding='utf-8'))
    cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
    man = os.path.join(T, 'manuales.txt'); ya = set(open(man, encoding='utf-8').read().split())
    for clave in 'abcde':
        if D + f'2d_jm_takara{clave}.dds' not in ocr: print('sin texto', clave); continue
        en, es, limpia, col = hoja_es(clave, ocr, cache)
        atlas_es.guardar_dds(D + f'2d_jm_takara{clave}', es); nuevos = [D + f'2d_jm_takara{clave}']
        for n in range(1, 6):
            nombre = f'2d_jm_takara{clave}_0{n}'
            img, v, s = pedazo(en, es, limpia, col, nombre)
            atlas_es.guardar_dds(D + nombre, img); nuevos.append(D + nombre)
            print(nombre, 'parecido', round(float(v), 3), 'escala', round(float(s), 2))
        with open(man, 'a', encoding='utf-8') as fh:
            for x in nuevos:
                if x not in ya: fh.write(x + '\n')


if __name__ == '__main__': main()
