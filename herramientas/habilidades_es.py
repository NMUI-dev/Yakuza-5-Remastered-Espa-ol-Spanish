# -*- coding: utf-8 -*-
"""(Claude Code, 20-10-2026) Tarjetas de habilidad de Yakuza 5 (pausepar/pause_en.par: ability/*.dds, 256x256 DXT5).
Cada tarjeta lleva abajo a la derecha una etiqueta de pincel: HEAT (se deja, el texto del juego dice «Heat»), TECH, SOUL,
BODY. La etiqueta es la misma capa en todas las tarjetas de su clase, así que:
  1. se halla dónde está la etiqueta inglesa y dónde la japonesa (poca variación entre tarjetas = capa fija encima);
  2. el fondo limpio sale de la versión japonesa donde no tiene su kanji, y donde se pisan las dos se rellena (inpaint);
  3. se escribe la palabra en español con Knewave (pincel en cursiva), con el degradado de color y el borde oscuro
     medidos de la etiqueta original, alineada a la derecha y con la misma altura de mayúscula.
Clases: trabajo/habilidades_clases.json (habilidades_clasificar.py).
Salida: trabajo/imagenes/es/pausepar_pause_en/ability/*.dds y trabajo/imagenes/habilidades_es.png (muestra).
  python herramientas/habilidades_es.py [n_max]
"""
import os, sys, json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
FUENTE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuentes_img", "Knewave-Regular.ttf")
ES = {'TECH': 'TÉCNICA', 'ROJO': 'ALMA', 'NARANJA': 'CUERPO'}
Y0, X0 = 120, 60                       # zona de trabajo: filas Y0..256, columnas X0..256
CAJA = (157, 195, 246)                 # fila de arriba de las mayúsculas, línea base, borde derecho (TECH/SOUL/BODY)
X_IZQ = 96                             # la palabra española no pasa de esta columna (izquierda)


def cargar(p, ja=False):
    q = os.path.join(T, 'extraido_ja', p.replace('pause_en', 'pause_ja')) if ja else os.path.join(T, 'extraido', p)
    return np.asarray(Image.open(q).convert('RGBA'), np.float32)


def capas(lista):
    """Máscaras fijas de la etiqueta inglesa y la japonesa de una clase. Un píxel es de etiqueta si en casi todas las
    tarjetas vale lo mismo (la capa no cambia) y la otra versión varía; si las dos son constantes (fondo negro
    uniforme), la etiqueta es la más clara. Si las dos etiquetas se pisan, va a las dos máscaras (se rellena)."""
    en = np.stack([cargar(p)[Y0:, X0:, :3] for p in lista]); ja = np.stack([cargar(p, True)[Y0:, X0:, :3] for p in lista])
    me, mj = np.median(en, 0), np.median(ja, 0)
    fe = (np.abs(en - me).max(3) < 14).mean(0); fj = (np.abs(ja - mj).max(3) < 14).mean(0)
    u = (np.abs(en - ja).sum(3) > 45).mean(0) > 0.5
    dl = me.mean(2) - mj.mean(2)
    ce, cj = fe > 0.9, fj > 0.9
    m_en = u & ((ce & ~cj) | (ce & cj & (dl > 20)))
    m_ja = u & ((cj & ~ce) | (ce & cj & (dl < -20)))
    ambas = u & ce & cj & (np.abs(dl) <= 20)
    m_en |= ambas; m_ja |= ambas
    nucleo = m_en & ~ambas
    return m_en, m_ja, nucleo, me


def estilo(nucleo, color):
    filas = np.where(nucleo.any(1))[0]
    lum = color.mean(2)
    cuerpo = nucleo & (lum > np.percentile(lum[nucleo], 40))    # relleno (sin el borde oscuro)
    grad = {}
    for y in filas:
        s = cuerpo[y]
        if s.sum() >= 2: grad[y] = np.median(color[y][s], 0)
    ys = sorted(grad); g = np.array([grad[y] for y in ys])
    borde = np.median(color[nucleo & ~cuerpo], 0) if (nucleo & ~cuerpo).sum() > 5 else g.mean(0) * 0.3
    cols = np.where(nucleo.any(0))[0]
    return dict(arriba=ys[0], abajo=ys[-1], grad=(np.array(ys), g), borde=borde, derecha=int(cols[-1]))


def mascara_texto(texto, alto_cap, ancho_max):
    f = ImageFont.truetype(FUENTE, 200); hcap = -f.getbbox('H', anchor='ls')[1]
    bb = f.getbbox(texto, anchor='ls')
    im = Image.new('L', (bb[2] - bb[0] + 40, bb[3] - bb[1] + 40), 0)
    ImageDraw.Draw(im).text((20 - bb[0], 20 - bb[1]), texto, font=f, fill=255, anchor='ls')
    base = 20 - bb[1]                                            # fila de la línea base en im
    im = im.filter(ImageFilter.MinFilter(7))                     # trazo más fino
    k = alto_cap / hcap; caja = im.getbbox(); im = im.crop(caja); base -= caja[1]
    w, h = max(1, round(im.width * k)), max(1, round(im.height * k))
    if w > ancho_max: w = ancho_max
    return im.resize((w, h), Image.LANCZOS), round(base * k)


def etiqueta(texto, st, H, W):
    """Capa RGBA (H x W de la zona) con la palabra en español."""
    alto = st['abajo'] - st['arriba'] + 1
    m, base = mascara_texto(texto, alto * (1.0 if len(texto) <= 4 else 0.9), st['derecha'] - (X_IZQ - X0))
    lienzo = Image.new('L', (W, H), 0)
    x = st['derecha'] - m.width + 1; y = st['abajo'] + 1 - base
    lienzo.paste(m, (x, y))
    mk = np.asarray(lienzo, np.float32) / 255
    borde = np.asarray(lienzo.filter(ImageFilter.MaxFilter(3)), np.float32) / 255
    sombra = np.asarray(lienzo.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.5)), np.float32) / 255
    ys, g = st['grad']
    filas = np.clip(np.arange(H), ys[0], ys[-1])
    rgb = np.stack([np.interp(filas, ys, g[:, c]) for c in range(3)], 1)[:, None, :].repeat(W, 1)
    # degradado suave: recta ajustada al color medido por fila (sin franjas)
    coef = [np.polyfit(ys, g[:, c], 1) for c in range(3)]
    rgb = np.stack([np.polyval(coef[c], filas) for c in range(3)], 1)[:, None, :].repeat(W, 1)
    rgb = np.clip(rgb * 1.08, 0, 255)
    fuera = np.clip(np.maximum(borde, sombra * 0.8) - mk, 0, 1)
    color = rgb * mk[..., None] + st['borde'] * (1 - mk[..., None])
    alfa = np.clip(mk + fuera, 0, 1)
    return color, alfa


def limpiar(p, tono, m_en, m_ja):
    """Fondo sin etiquetas: donde solo está la inglesa se toma la japonesa y al revés; donde se pisan, relleno
    (inpaint). Lo demás que difiera se resuelve con el píxel más oscuro y lo que aún parezca etiqueta se rellena."""
    en = cargar(p); ja = cargar(p, True)
    ze, zj = en[Y0:, X0:, :3], ja[Y0:, X0:, :3]
    k = np.ones((3, 3), np.uint8)
    u = cv2.dilate((np.abs(ze - zj).sum(2) > 45).astype(np.uint8), k, iterations=2) > 0
    re_ = cv2.dilate(m_en.astype(np.uint8), k, iterations=1) > 0; rj = cv2.dilate(m_ja.astype(np.uint8), k, iterations=2) > 0
    b = np.where((zj.mean(2) < ze.mean(2))[..., None], zj, ze)
    b[re_ & ~rj] = zj[re_ & ~rj]; b[rj & ~re_] = ze[rj & ~re_]
    b[~u & ~re_ & ~rj] = ze[~u & ~re_ & ~rj]
    hsv = cv2.cvtColor(np.ascontiguousarray(b.clip(0, 255).astype(np.uint8)), cv2.COLOR_RGB2HSV)
    h = hsv[..., 0].astype(np.float32) * 2; sat = hsv[..., 1]; val = hsv[..., 2]
    dh = np.minimum(np.abs(h - tono), 360 - np.abs(h - tono))
    queda = (re_ | rj) & (sat > 150) & (val > 110) & (dh < 20)
    hueco = ((cv2.dilate(queda.astype(np.uint8), k, iterations=2) > 0) | (re_ & rj)).astype(np.uint8) * 255
    b = cv2.inpaint(np.ascontiguousarray(b.clip(0, 255).astype(np.uint8)), hueco, 5, cv2.INPAINT_TELEA).astype(np.float32)
    out = en.copy(); out[Y0:, X0:, :3] = b
    return out


def marco(a, p, m_en, m_ja):
    """(21-10) El borrado se llevaba el MARCO azul fino de la tarjeta (columna 251 y fila 195): se devuelve del original
    (de la versión inglesa donde no estaba la etiqueta inglesa; si no, de la japonesa). El español se pinta encima."""
    en, ja = cargar(p), cargar(p, True); H, W = a.shape[:2]
    zona = np.zeros((H, W), bool); zona[Y0:200, 249:254] = True; zona[193:198, X0:254] = True
    me = np.zeros((H, W), bool); me[Y0:, X0:] = cv2.dilate(m_en.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    mj = np.zeros((H, W), bool); mj[Y0:, X0:] = cv2.dilate(m_ja.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    a[zona & ~me] = en[zona & ~me]; a[zona & me & ~mj] = ja[zona & me & ~mj]
    # donde las dos etiquetas tapaban el marco: la línea se rehace con su propio color (mediana de lo visible)
    for x in range(249, 254):
        ok = ~me[Y0:200, x] | ~mj[Y0:200, x]
        if ok.sum() > 5: a[Y0:200, x][~ok] = np.median(a[Y0:200, x][ok], 0)
    for y in range(193, 198):
        ok = ~me[y, X0:254] | ~mj[y, X0:254]
        if ok.sum() > 5: a[y, X0:254][~ok] = np.median(a[y, X0:254][ok], 0)


def main(n_max=None):
    clases = json.load(open(os.path.join(T, 'habilidades_clases.json')))
    atlas_es.TEX = os.path.join(T, 'extraido')
    muestras = []
    for cl, texto in ES.items():
        lista = sorted(k for k, v in clases.items() if v == cl)
        m_en, m_ja, nucleo, color = capas(lista)
        st = estilo(nucleo, color); H, W = m_en.shape
        st.update(arriba=CAJA[0] - Y0, abajo=CAJA[1] - Y0, derecha=CAJA[2] - X0)   # caja medida a mano del original
        tono = float(cv2.cvtColor(np.uint8([[st['grad'][1].mean(0)]]), cv2.COLOR_RGB2HSV)[0, 0, 0]) * 2
        capa_rgb, capa_a = etiqueta(texto, st, H, W)
        print(cl, texto, len(lista), 'filas', st['arriba'], st['abajo'], 'derecha', st['derecha'] + X0)
        for i, p in enumerate(lista[:n_max]):
            a = limpiar(p, tono, m_en, m_ja)
            marco(a, p, m_en, m_ja)
            z = a[Y0:, X0:]
            z[..., :3] = z[..., :3] * (1 - capa_a[..., None]) + capa_rgb * capa_a[..., None]
            img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
            atlas_es.guardar_dds(p[:-4], img)
            if i < 4: muestras.append((cargar(p), np.asarray(img)))
    hoja = Image.new('RGB', (512 * 2, 256 * len(muestras) // 2 + 256), (40, 90, 40))
    for i, (o, n) in enumerate(muestras):
        x = (i % 2) * 512; y = (i // 2) * 256
        hoja.paste(Image.fromarray(o.astype(np.uint8)).convert('RGB'), (x, y)); hoja.paste(Image.fromarray(n).convert('RGB'), (x + 256, y))
    hoja.save(os.path.join(T, 'imagenes', 'habilidades_es.png'))


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
