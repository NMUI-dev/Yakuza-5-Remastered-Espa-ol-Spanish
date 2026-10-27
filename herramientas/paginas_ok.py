# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Páginas que gemma4 marcó pero claude2 revisó a ojo y están BIEN: vuelven de
trabajo/imagenes/descartadas a trabajo/imagenes/es (entran al juego) y en revision_paginas.json quedan ok
(«verificado»: «claude2»), así salen de la cola del kit de atlas.
  python herramientas/paginas_ok.py <filtro> [--menos <filtro2> ...]   (filtro: parte del nombre, p. ej. syotitle_)
"""
import json, os, shutil, sys
T = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'trabajo', 'imagenes')
RP = os.path.join(T, 'revision_paginas.json')
filtro = sys.argv[1]; menos = sys.argv[sys.argv.index('--menos') + 1:] if '--menos' in sys.argv else []
d = json.load(open(RP, encoding='utf-8')); n = 0
for k, v in d.items():
    if v.get('ok', True) or filtro not in k or any(m in k for m in menos): continue
    src, dst = os.path.join(T, 'descartadas', k), os.path.join(T, 'es', k)
    if os.path.exists(src): os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.move(src, dst)
    v.update(ok=True, verificado='claude2'); n += 1
json.dump(d, open(RP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('devueltas al juego', n)
