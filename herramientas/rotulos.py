# -*- coding: utf-8 -*-
"""(Claude Code, 20-10-2026, copiado de Yakuza 6) Redibuja rótulos de pincel (letra blanca con vetas y halo negro) en español.
Los rótulos son letra blanca de pincel con vetas oscuras y un halo negro difuso sobre fondo transparente.
  1) detecta en el original las líneas de texto (filas con alfa alto) y su caja;
  2) borra todo y escribe cada línea en español en su caja (mismo alto, centrada como el original, sin pasar del ancho);
  3) imita el pincel: vetas horizontales oscuras + bordes ásperos, y el halo negro (desenfoque del alfa).
Fuente: CaveatBrush (OFL, Google Fonts) estrechada en horizontal. Uso: ver rotulos_aplicar.py.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
AQUI = os.path.dirname(os.path.abspath(__file__))
FUENTE = os.path.join(AQUI, 'fuentes_img', os.environ.get('ROT_FUENTE', 'CaveatBrush-Regular.ttf'))
ESTRECHO = float(os.environ.get('ROT_ESTRECHO', '0.86'))


def lineas(a, umbral=230):
    """Cajas (y0, y1, x0, x1) de las líneas de texto de un RGBA (alfa alto = letra)."""
    m = a[..., 3] >= umbral
    filas = m.sum(1) > max(2, m.shape[1] // 400)
    cajas = []; y = 0; H = len(filas)
    while y < H:
        if filas[y]:
            y0 = y
            while y < H and filas[y]: y += 1
            cajas.append([y0, y])
        y += 1
    # unir trozos separados por huecos pequeños (acentos, vetas) y quitar ruido
    unidas = []
    for c in cajas:
        if unidas and c[0] - unidas[-1][1] < 3: unidas[-1][1] = c[1]
        else: unidas.append(c)
    res = []
    for y0, y1 in unidas:
        if y1 - y0 < 6: continue
        cols = np.where(m[y0:y1].any(0))[0]
        res.append((y0, y1, int(cols[0]), int(cols[-1]) + 1))
    return res


def _texto(linea, alto, ancho_max):
    """Máscara L de una línea con la letra de pincel: alto de mayúsculas = alto (px)."""
    tam = max(40, int(alto * 1.25))
    for _ in range(0):   # (21-10) ya NO se achica el cuerpo: dibujar en miniatura y ampliar dejaba letras borrosas y deformes
        f = ImageFont.truetype(FUENTE, tam)
        bb = f.getbbox(linea, anchor='ls')
        w = (bb[2] - bb[0]) * ESTRECHO; hcap = -f.getbbox('H', anchor='ls')[1]
        escala = alto / max(1, hcap)
        if w * escala <= ancho_max or tam < 8: break
        tam = int(tam * 0.95)
    f = ImageFont.truetype(FUENTE, tam)
    bb = f.getbbox(linea, anchor='ls'); hcap = -f.getbbox('H', anchor='ls')[1]
    pad = tam
    img = Image.new('L', (bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad), 0)
    ImageDraw.Draw(img).text((pad - bb[0], pad - bb[1]), linea, font=f, fill=255, anchor='ls')
    # recortar a la tinta y escalar: ancho estrecho, alto de mayúscula = alto
    k = alto / max(1, hcap)
    img = img.crop(img.getbbox())
    nw = max(1, int(img.width * ESTRECHO * k)); nh = max(1, int(img.height * k))
    # (21-10, pedido del usuario: nada cortado ni aplastado) si no cabe: estrechar como mucho un 10 % y, si aún no cabe,
    # bajar el alto en la misma proporción (antes se aplastaba a lo ancho sin límite y salía ilegible)
    if nw > ancho_max:
        s = ancho_max / nw
        if s < 0.9: nh = max(1, int(nh * s / 0.9))
        nw = int(ancho_max)
    return img.resize((nw, nh), Image.LANCZOS), (-bb[1] - (pad - img.getbbox()[1] if False else 0))


def pincel(m, semilla):
    """Vetas oscuras y bordes ásperos sobre la máscara blanca (L, 0-255) -> (relleno L, alfa L)."""
    r = np.random.default_rng(semilla)
    a = np.asarray(m, np.float32) / 255
    h, w = a.shape
    # vetas: ruido estirado en horizontal
    ruido = r.random((max(2, h // 3), max(2, w // 24))).astype(np.float32)
    ruido = np.asarray(Image.fromarray((ruido * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    vetas = np.clip((ruido - 0.80) * 4, 0, 1)                  # zonas oscuras dentro de la letra
    relleno = 1 - 0.85 * vetas
    # bordes ásperos: quitar un poco de alfa en el borde según ruido fino
    fino = r.random((h, w)).astype(np.float32)
    borde = (a > 0.05) & (a < 0.95)
    alfa = a.copy(); alfa[borde] *= (0.55 + 0.45 * fino[borde])
    return Image.fromarray((relleno * 255).astype(np.uint8)), Image.fromarray((np.clip(alfa, 0, 1) * 255).astype(np.uint8))


def dibujar(original, textos, semilla=1):
    """original: RGBA del juego; textos: lista de líneas en español (una por línea detectada). Devuelve RGBA nuevo."""
    a = np.asarray(original.convert('RGBA'))
    return capa_texto(original.size, lineas(a), textos, semilla)


def sobre_fondo(original, zona, textos, semilla=1, umbral=200):
    """Imagen OPACA (texto blanco sobre un dibujo): borra el texto blanco dentro de zona=(x0,y0,x1,y1) rellenando el
    fondo (OpenCV inpaint) y escribe el español en las mismas líneas. Devuelve RGBA."""
    import cv2
    rgb = np.asarray(original.convert('RGB')).copy(); x0, y0, x1, y1 = zona
    lum = rgb.astype(np.int16)
    blanco = (lum.min(2) > umbral)
    m = np.zeros(blanco.shape, np.uint8); m[y0:y1, x0:x1] = blanco[y0:y1, x0:x1]
    falso = np.zeros(rgb.shape[:2] + (4,), np.uint8); falso[..., 3] = m * 255
    cajas = lineas(falso, 128)
    m = cv2.dilate(m, np.ones((9, 9), np.uint8), iterations=2)
    m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=3)          # incluye el halo oscuro del texto
    limpio = cv2.inpaint(rgb[..., ::-1].copy(), m * 255, 9, cv2.INPAINT_TELEA)[..., ::-1]
    base = Image.fromarray(limpio).convert('RGBA')
    base.alpha_composite(capa_texto(original.size, cajas, textos, semilla))
    return base


def capa_texto(tam, cajas, textos, semilla=1):
    cajas = list(cajas)
    while 0 < len(cajas) < len(textos):          # líneas pegadas: partir la caja más alta (a partir de la 2.ª si hay varias)
        i = max(range(len(cajas)), key=lambda j: (cajas[j][1] - cajas[j][0]) * (0.7 if j == 0 and len(cajas) > 1 else 1))
        y0, y1, x0, x1 = cajas[i]; m = (y0 + y1) // 2
        cajas[i:i + 1] = [(y0, m, x0, x1), (m, y1, x0, x1)]
    while len(cajas) > len(textos) > 0:          # sobran líneas: unir las dos más cercanas
        i = min(range(len(cajas) - 1), key=lambda j: cajas[j + 1][0] - cajas[j][1])
        a_, b_ = cajas[i], cajas[i + 1]; cajas[i:i + 2] = [(a_[0], b_[1], min(a_[2], b_[2]), max(a_[3], b_[3]))]
    if len(cajas) != len(textos):
        raise ValueError(f'el original tiene {len(cajas)} líneas y el español {len(textos)}')
    W, H = tam
    mascara = Image.new('L', (W, H), 0); vet = Image.new('L', (W, H), 255)
    for i, ((y0, y1, x0, x1), t) in enumerate(zip(cajas, textos)):
        alto = int((y1 - y0) * 0.88)                            # la caja incluye halo y salientes
        cx = (x0 + x1) / 2; ancho_max = min(W * 0.96, max(x1 - x0, W * 0.9) * 1.0)
        if os.environ.get('ROT_ANCHO_ORIG'): ancho_max = x1 - x0   # (21-10) no pasar del ancho del inglés: fuera se corta en pantalla
        img, _ = _texto(t, alto, ancho_max)
        x = int(round(cx - img.width / 2)); x = max(int(W * 0.02), min(x, W - img.width - int(W * 0.02)))
        y = int(round((y0 + y1) / 2 - img.height / 2))
        mascara.paste(img, (x, y), img)
    grosor = int(os.environ.get('ROT_GROSOR', '0'))
    if grosor: mascara = mascara.filter(ImageFilter.MaxFilter(grosor))
    relleno, alfa = pincel(mascara, semilla)
    halo = mascara.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(max(3, H // 80)))
    halo = Image.fromarray((np.asarray(halo, np.float32) * 0.85).astype(np.uint8))
    sal = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sal.alpha_composite(Image.merge('RGBA', (Image.new('L', (W, H), 8),) * 3 + (halo,)))
    blanco = Image.merge('RGBA', (relleno, relleno, relleno, alfa))
    sal.alpha_composite(blanco)
    return sal
