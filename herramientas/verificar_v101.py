# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) Comprueba la v1.0.1 armada: extrae cada .par de trabajo/salida_img/data con ParTool (también los
anidados de ui_en) y abre TODAS las .dds; compara las de es_final con lo extraído (deben ser idénticas byte a byte)."""
import os, sys, subprocess, shutil, hashlib, tempfile
from PIL import Image
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
PT = os.path.join(R, 'herramientas', 'partool', 'ParTool.exe')
SAL = os.path.join(T, 'salida_img', 'data'); FIN = os.path.join(T, 'imagenes', 'es_final')
TMP = os.path.join(T, 'verif_v101'); shutil.rmtree(TMP, ignore_errors=True)
RAIZ = {'2dpar/ui_en.par': ['ui_en', '2dpar_ui_en'], '2dpar/sprite_en.par': ['sprite_en', '2dpar_sprite_en'],
        'pausepar/pause_en.par': ['pausepar_pause_en'], 'bootpar/boot_en.par': ['bootpar_boot_en'],
        'pausepar/idol_work_en.par': ['pausepar_idol_work_en'], 'pausepar/movie_en.par': ['pausepar_movie_en'],
        'pausepar/taxi_en.par': ['pausepar_taxi_en'], 'pausepar/title_menu_en.par': ['pausepar_title_menu_en'],
        'pausepar/tougijyo_en.par': ['pausepar_tougijyo_en']}
md5 = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
malas = ok = dif = 0
for par, raices in RAIZ.items():
    d = os.path.join(TMP, par.replace('/', '_'))
    r = subprocess.run([PT, 'extract', os.path.join(SAL, par), d, '-r'], stdin=subprocess.DEVNULL, capture_output=True)
    if r.returncode: print('ERROR al extraer', par, r.returncode, r.stderr[-600:]); malas += 1; continue
    for dp, _, fs in os.walk(d):
        for f in fs:
            if not f.endswith('.dds'): continue
            try: Image.open(os.path.join(dp, f)).load(); ok += 1
            except Exception as e: print('NO ABRE', os.path.join(dp, f), e); malas += 1
    for raiz in raices:
        b = os.path.join(FIN, raiz)
        if not os.path.isdir(b): continue
        for dp, _, fs in os.walk(b):
            for f in fs:
                rel = os.path.relpath(os.path.join(dp, f), b)
                cand = [os.path.join(d, rel), os.path.join(d, rel.replace('.par' + os.sep, '.par.unpack' + os.sep))]
                hit = [c for c in cand if os.path.exists(c)]
                if not hit: continue
                if md5(hit[0]) != md5(os.path.join(dp, f)): dif += 1; print('DISTINTA', raiz, rel)
print('texturas que abren', ok, '| no abren', malas, '| distintas a es_final', dif)
