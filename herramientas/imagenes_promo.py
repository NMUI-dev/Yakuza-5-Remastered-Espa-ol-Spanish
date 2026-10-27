# (Claude, 24-10-2026) 4 imágenes de presentación del mod (1920x1080) a partir de capturas REALES del juego traducido.
# Uso: python imagenes_promo.py  -> C:\Mods\yakuza5\promo\
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = r"C:\Mods\yakuza5"
OUT = os.path.join(BASE, "promo"); os.makedirs(OUT, exist_ok=True)
W, H = 1920, 1080
ROJO = (196, 22, 28)
F = r"C:\Windows\Fonts"
def fuente(n, t): return ImageFont.truetype(os.path.join(F, n), t)

def fondo(ruta):
    im = Image.open(ruta).convert("RGB")
    return im.resize((W, H), Image.LANCZOS) if im.size != (W, H) else im

def texto_sombra(d, xy, s, f, color=(255, 255, 255), sombra=6, anchor="la"):
    x, y = xy
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            d.text((x + dx, y + dy + sombra // 2), s, font=f, fill=(0, 0, 0), anchor=anchor)
    d.text((x, y), s, font=f, fill=color, anchor=anchor)

def franja(im, titulo, sub, arriba=True):
    """franja oscura con borde rojo y los textos; arriba o abajo"""
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
    alto = 190
    y0 = 0 if arriba else H - alto
    d.rectangle([0, y0, W, y0 + alto], fill=(0, 0, 0, 240))
    d.rectangle([0, y0 + alto - 8 if arriba else y0, W, y0 + alto if arriba else y0 + 8], fill=ROJO + (255,))
    im = Image.alpha_composite(im.convert("RGBA"), capa)
    d = ImageDraw.Draw(im)
    texto_sombra(d, (70, y0 + 28), titulo, fuente("impact.ttf", 88))
    d.text((74, y0 + 128), sub, font=fuente("segoeuib.ttf", 38), fill=(235, 235, 235))
    return im

def sello(im, s="MOD GRATIS · PC STEAM", y=None):
    d = ImageDraw.Draw(im); f = fuente("ariblk.ttf", 30)
    w = d.textlength(s, font=f) + 50
    y = H - 90 if y is None else y
    d.rectangle([W - w - 40, y, W - 40, y + 54], fill=ROJO)
    d.text((W - 40 - w / 2, y + 27), s, font=f, fill="white", anchor="mm")
    return im

def guardar(im, n):
    # guía de Steam: JPG ligero (menos de 1 MB) para que se suba sin problema
    p = os.path.join(OUT, n); im.convert("RGB").save(p, quality=88, optimize=True); print(p, os.path.getsize(p) // 1024, "KB")

# 1) PORTADA: menú de título en español
im = fondo(os.path.join(BASE, r"entrega\capturas\3_menu_titulo.png"))
capa = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
d.rectangle([0, 0, 1060, 470], fill=(0, 0, 0, 170))
im = Image.alpha_composite(im.convert("RGBA"), capa); d = ImageDraw.Draw(im)
texto_sombra(d, (70, 50), "YAKUZA 5", fuente("impact.ttf", 170))
texto_sombra(d, (76, 235), "REMASTERED", fuente("impact.ttf", 74), color=(230, 230, 230))
d.rectangle([70, 335, 1000, 420], fill=ROJO)
d.text((535, 377), "TRADUCCIÓN AL ESPAÑOL", font=fuente("ariblk.ttf", 52), fill="white", anchor="mm")
guardar(sello(im, "MOD GRATIS · PC STEAM · ESPAÑOL LATINO", y=40), "1_portada.jpg")   # arriba: abajo tapa «OK / Atrás»

# 2) DIÁLOGOS: escena con subtítulos
im = franja(fondo(os.path.join(BASE, r"trabajo\capturas\piloto_29.png")),
            "HISTORIA Y DIÁLOGOS EN ESPAÑOL", "Más de 63.000 textos: escenas, subtítulos, misiones y correos")
guardar(sello(im), "2_dialogos.jpg")

# 3) MENÚS Y OBJETOS
im = franja(fondo(os.path.join(BASE, r"trabajo\capturas\t6.png")),
            "MENÚS, OBJETOS Y OPCIONES", "Todo el juego con tildes, ñ, ¿ y ¡")   # arriba: abajo tapa la descripción
guardar(sello(im), "3_menus.jpg")

# 4) IMÁGENES TRADUCIDAS: antes / después (cartel del juego)
im = Image.new("RGB", (W, H), (14, 14, 16))
cartel = Image.open(os.path.join(BASE, r"trabajo\capturas\mail_es.png")).convert("RGB")
cw = cartel.width // 4
en, es = cartel.crop((0, 0, cw, cartel.height)), cartel.crop((cw, 0, cw * 2, cartel.height))
alto, y0 = 610, 340
for i, (pieza, etiqueta, color) in enumerate([(en, "ORIGINAL (INGLÉS)", (90, 90, 95)), (es, "CON EL MOD", ROJO)]):
    p = pieza.resize((int(pieza.width * alto / pieza.height), alto), Image.LANCZOS)
    x = 320 + i * 760; y = y0
    im.paste(p, (x, y))
    d = ImageDraw.Draw(im)
    d.rectangle([x, y - 70, x + p.width, y - 10], fill=color)
    d.text((x + p.width / 2, y - 40), etiqueta, font=fuente("ariblk.ttf", 34), fill="white", anchor="mm")
d = ImageDraw.Draw(im)
cx, cy = 320 + p.width + (760 - p.width) / 2, y0 + alto / 2   # centro del hueco entre las dos
d.polygon([(cx - 60, cy - 22), (cx + 10, cy - 22), (cx + 10, cy - 55), (cx + 65, cy), (cx + 10, cy + 55), (cx + 10, cy + 22), (cx - 60, cy + 22)], fill=ROJO)   # flecha (la fuente no trae «➜»)
texto_sombra(d, (W / 2, 70), "TAMBIÉN LAS IMÁGENES CON TEXTO", fuente("impact.ttf", 92), anchor="ma")
d.text((W / 2, 185), "Carteles, títulos de capítulo, minijuegos y menús dibujados: 396 de 399 imágenes",
       font=fuente("segoeuib.ttf", 38), fill=(220, 220, 220), anchor="ma")
guardar(sello(im), "4_imagenes.jpg")

# 5) PORTADA CUADRADA de la guía (Steam la muestra pequeña): Kiryu del menú de título + rótulo
im = fondo(os.path.join(BASE, r"entrega\capturas\3_menu_titulo.png")).crop((1000, 60, 1920, 980)).resize((512, 512), Image.LANCZOS)
capa = Image.new("RGBA", (512, 512), (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
d.rectangle([0, 330, 512, 512], fill=(0, 0, 0, 190))
im = Image.alpha_composite(im.convert("RGBA"), capa); d = ImageDraw.Draw(im)
texto_sombra(d, (256, 338), "YAKUZA 5", fuente("impact.ttf", 78), anchor="ma")
d.rectangle([20, 432, 492, 492], fill=ROJO)
d.text((256, 462), "EN ESPAÑOL", font=fuente("ariblk.ttf", 40), fill="white", anchor="mm")
guardar(im, "0_portada_guia_cuadrada.jpg")
