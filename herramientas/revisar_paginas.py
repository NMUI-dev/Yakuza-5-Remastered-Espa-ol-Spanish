# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Verificación de las PÁGINAS de imagen (reglas, capturas, capítulos, objetos) que dibujó
imagenes_es.py: gemma4 (local) compara original y español de cada textura y marca las dudosas; claude2 mira a ojo las
marcadas y una muestra. Salida: trabajo/imagenes/revision_paginas.json {ruta: {"ok":..,"problem":..,"detalle":..}}
  python herramientas/revisar_paginas.py
"""
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_semi as S
from ocr_imagenes import origen
T = S.T; SAL = os.path.join(T, 'revision_paginas.json')
PROMPT = ('Left: original English image from a video game. Right: the same image with the text translated to Spanish. '
          'Answer ONLY JSON {"ok": true/false, "problem": "none|text_outside_box|overlap|unreadable|leftover_english|'
          'garbled|missing_text|other", "detail": "short"}. ok=false if any Spanish text goes outside its box or panel, '
          'overlaps other text or icons, is hard to read or garbled, or English text is still visible where it should be '
          'translated (proper names may stay).')


def png(im, maxlado=768):
    import base64, io
    b = Image.new('RGBA', im.size, (0, 0, 0, 255)); b.alpha_composite(im.convert('RGBA')); b = b.convert('RGB')
    b.thumbnail((maxlado, maxlado)); buf = io.BytesIO(); b.save(buf, 'PNG'); return base64.b64encode(buf.getvalue()).decode()


def main():
    hecho = json.load(open(SAL, encoding='utf-8')) if os.path.exists(SAL) else {}
    es_dir = os.path.join(T, 'es')
    for dp, _, fs in os.walk(es_dir):
        for f in sorted(fs):
            if not f.endswith('.dds'): continue
            ruta = os.path.relpath(os.path.join(dp, f), es_dir).replace(os.sep, '/')
            if ruta.startswith(('ui_en/', '2dpar_ui_en/', 'sprite_en/')) or ruta in hecho: continue
            try: o = Image.open(origen(ruta)); n = Image.open(os.path.join(dp, f))
            except Exception as e: hecho[ruta] = {'ok': False, 'problem': 'error', 'detail': str(e)[:100]}; continue
            r = S.vlm(PROMPT, [png(o), png(n)])
            hecho[ruta] = {'ok': r.get('ok', True), 'problem': r.get('problem'), 'detalle': r.get('detail')}
            json.dump(hecho, open(SAL, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print(ruta, hecho[ruta]['ok'], hecho[ruta]['problem'], flush=True)
    malos = [k for k, v in hecho.items() if not v['ok']]
    print('revisadas', len(hecho), 'marcadas', len(malos))


if __name__ == '__main__':
    main()
