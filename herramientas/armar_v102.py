# -*- coding: utf-8 -*-
"""(01-11-2026, claude1) Arma la v1.0.2 = v1.0.1 (entrega_v101/archivos/data) + lo nuevo, en trabajo/salida_v102/data:
  - textos: aplicar_extra.py (wdr.par, auth/subtitle.par, db.devil/en/msg_replacer.bin) -> ya escritos ahí antes
  - títulos de capítulo (capitulos_v102.py) -> pausepar/pause_en.par (partiendo del de la v1.0.1)
  - rótulos de escena (telops_es.py) -> auth_telop/auth_telop_en.par
  - letras del karaoke (karaoke_letras_es.py) -> minigame_en/karaoke_e.par
  - dardos (imagenes_extra_es.py) -> minigame_en/darts/darts_tex.par y los sueltos de minigame_en/darts/darts_tex/
Los .par que la v1.0.1 no traía salen del juego: Steam NO lleva esos archivos cambiados (no están en el respaldo de la
instalación), solo se leen. Cada textura nueva debe medir lo mismo que la original.
  python herramientas/armar_v102.py"""
import os, sys, glob, shutil, subprocess
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
PT = os.path.join(R, 'herramientas', 'partool', 'ParTool.exe')
JUEGO = os.environ.get('Y5_JUEGO', 'D:/SteamLibrary/steamapps/common/Yakuza 5/main/data')   # otra carpeta: variable de entorno Y5_JUEGO
V101 = os.path.join(R, 'entrega_v101', 'archivos', 'data')
SAL = os.path.join(T, 'salida_v102', 'data')
EX = os.path.join(T, 'imagenes', 'es_extra', 'barrido_3110', 'x')
ORIG = os.path.join(T, 'barrido_3110', 'x')
PARES = [   # (.par de salida, .par base, carpeta con lo nuevo = raíz de dentro del .par, carpeta de los originales extraídos)
    ('pausepar/pause_en.par', os.path.join(V101, 'pausepar/pause_en.par'),
     os.path.join(T, 'imagenes', 'es_v102', 'pausepar_pause_en'), os.path.join(T, 'extraido', 'pausepar_pause_en')),
    ('auth_telop/auth_telop_en.par', os.path.join(JUEGO, 'auth_telop/auth_telop_en.par'),
     os.path.join(EX, 'auth_telop/auth_telop_en.par_par'), os.path.join(ORIG, 'auth_telop/auth_telop_en.par_par')),
    ('minigame_en/karaoke_e.par', os.path.join(JUEGO, 'minigame_en/karaoke_e.par'),
     os.path.join(EX, 'minigame_en/karaoke_e.par_par'), os.path.join(ORIG, 'minigame_en/karaoke_e.par_par')),
    ('minigame_en/darts/darts_tex.par', os.path.join(JUEGO, 'minigame_en/darts/darts_tex.par'),
     os.path.join(EX, 'minigame_en/darts/darts_tex.par_par'), os.path.join(ORIG, 'minigame_en/darts/darts_tex.par_par'))]
SUELTOS = [('minigame_en/darts/darts_tex', os.path.join(EX, 'minigame_en/darts/darts_tex'), os.path.join(ORIG, 'minigame_en/darts/darts_tex'))]


def mismas_medidas(nuevo, orig):
    n = 0
    for p in glob.glob(os.path.join(nuevo, '**', '*.dds'), recursive=True):
        o = os.path.join(orig, os.path.relpath(p, nuevo))
        assert os.path.getsize(p) == os.path.getsize(o), (p, os.path.getsize(p), os.path.getsize(o))
        n += 1
    return n


def main():
    if os.path.exists(os.path.join(JUEGO, 'traduccion_es_version.txt')):
        # los .par de JUEGO que se usan de base no los cambia el instalador: comprobar que siguen siendo los del respaldo
        resp = os.path.join(T, 'respaldos', 'respaldo_original_y5_steam_2510')
        for sal, base, _, _ in PARES:
            if base.startswith(JUEGO): assert not os.path.exists(os.path.join(resp, sal)), sal
    for sal, base, nuevo, orig in PARES:
        n = mismas_medidas(nuevo, orig)
        o = os.path.join(SAL, sal); os.makedirs(os.path.dirname(o), exist_ok=True)
        if os.path.exists(o): os.remove(o)
        r = subprocess.run([PT, 'add', base, nuevo, o], stdin=subprocess.DEVNULL, capture_output=True)
        if r.returncode != 0 or b'ERROR' in r.stdout.upper(): sys.exit(f'ParTool {sal}: {r.stdout[-300:]!r}')
        print(sal, n, 'texturas', os.path.getsize(base), '->', os.path.getsize(o))
    for sal, nuevo, orig in SUELTOS:
        n = mismas_medidas(nuevo, orig)
        for p in glob.glob(os.path.join(nuevo, '*.dds')):
            d = os.path.join(SAL, sal, os.path.basename(p)); os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copy2(p, d)
        print(sal, n, 'sueltas')


if __name__ == '__main__': main()
