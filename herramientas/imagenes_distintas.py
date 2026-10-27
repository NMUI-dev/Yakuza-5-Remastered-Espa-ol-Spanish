# -*- coding: utf-8 -*-
"""(Claude Code, 20-10-2026) Texturas de la versión inglesa que NO son iguales a la japonesa (= llevan texto en inglés).
Salida: trabajo/imagenes_distintas.txt + trabajo/imagenes/png/<ruta>.png y hojas de miniaturas trabajo/imagenes/hoja_NN.png."""
import os, hashlib, collections
from PIL import Image, ImageDraw
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
PARES = {'2dpar_ui_en': '2dpar_ui_ja', '2dpar_sprite_en': '2dpar_sprite_ja', 'pausepar_pause_en': 'pausepar_pause_ja',
         'pausepar_title_menu_en': 'pausepar_title_menu_ja', 'pausepar_movie_en': 'pausepar_movie_ja',
         'pausepar_idol_work_en': 'pausepar_idol_work_ja', 'pausepar_tougijyo_en': 'pausepar_tougijyo_ja',
         'pausepar_taxi_en': 'pausepar_taxi_ja', 'pausepar_kigae_en': 'pausepar_kigae_ja',
         'pausepar_snowball_en': 'pausepar_snowball_ja', 'bootpar_boot_en': 'bootpar_boot_ja'}

def h(p): return hashlib.md5(open(p, 'rb').read()).hexdigest()

tot = collections.Counter(); lista = []
for en, ja in PARES.items():
    jah = {}
    for dp, _, fs in os.walk(os.path.join(T, 'extraido_ja', ja)):
        for f in fs:
            if f.lower().endswith('.dds'): jah[f.lower()] = h(os.path.join(dp, f))
    for dp, _, fs in os.walk(os.path.join(T, 'extraido', en)):
        for f in fs:
            if not f.lower().endswith('.dds'): continue
            p = os.path.join(dp, f)
            if jah.get(f.lower()) != h(p):
                tot[en] += 1; lista.append(os.path.relpath(p, os.path.join(T, 'extraido')).replace(os.sep, '/'))
print(dict(tot), sum(tot.values()))
open(os.path.join(T, 'imagenes_distintas.txt'), 'w', encoding='utf-8').write('\n'.join(lista))
# miniaturas
I = os.path.join(T, 'imagenes'); os.makedirs(I, exist_ok=True)
mins = []
for r in lista:
    try: im = Image.open(os.path.join(T, 'extraido', r)).convert('RGBA')
    except Exception: continue
    b = Image.new('RGBA', im.size, (40, 90, 40, 255)); b.alpha_composite(im); b = b.convert('RGB'); b.thumbnail((240, 120))
    c = Image.new('RGB', (250, 140), (20, 20, 20)); c.paste(b, (5, 0)); ImageDraw.Draw(c).text((3, 125), r.split('/')[-1][:40], fill=(255, 255, 0))
    mins.append(c)
for k in range(0, len(mins), 40):
    hoja = Image.new('RGB', (250 * 5, 140 * 8), (0, 0, 0))
    for i, c in enumerate(mins[k:k + 40]): hoja.paste(c, ((i % 5) * 250, (i // 5) * 140))
    hoja.save(os.path.join(I, f'hoja_{k // 40:02d}.png'))
print('hojas', (len(mins) + 39) // 40)
