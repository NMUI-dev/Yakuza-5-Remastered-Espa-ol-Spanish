# -*- coding: utf-8 -*-
"""(Claude Code, 20-10-2026) Mete las texturas traducidas (trabajo/imagenes/es/<raíz>/<ruta>.dds) en los .par del juego.
<raíz> = ui_en (2dpar/ui_en.par, ya extraída con -r en trabajo/extraido_r). Las rutas pueden cruzar .par anidados
(surfboard/pjd_titlemenu.par/Texlist_0001/x.dds): se rearman por capas con ParTool «add» (de dentro hacia fuera).
Si la traducción de textos ya dejó ese .par en trabajo/salida/data (pause_en.par lleva textos E imágenes), se parte de
él; si no, del juego. El resultado va a trabajo/salida_img/data y se copia también a trabajo/salida/data.
aplicar.py lo llama al final, así el orden siempre es textos → imágenes.   python herramientas/imagenes_aplicar.py
"""
import os, re, sys, shutil, subprocess, collections
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
PT = os.path.join(R, 'herramientas', 'partool', 'ParTool.exe')
JUEGO = os.environ.get('Y5_JUEGO', 'D:/SteamLibrary/steamapps/common/Yakuza 5/main/data')   # (30-10) otra carpeta: variable de entorno Y5_JUEGO
# (21-10) si la traducción está INSTALADA en Steam, el «original» ya no lo es: parar (quitarla antes con el instalador)
if os.path.exists(os.path.join(os.environ.get('Y5_JUEGO', 'D:/SteamLibrary/steamapps/common/Yakuza 5/main/data'), 'traduccion_es_version.txt')):
    sys.exit('La traducción está instalada en Steam: quítala (INSTALAR o QUITAR.bat, opción 2) antes de rearmar.')
RAICES = {'ui_en': ('2dpar/ui_en.par', os.path.join(T, 'extraido', '2dpar_ui_en')),
          'sprite_en': ('2dpar/sprite_en.par', os.path.join(T, 'extraido', '2dpar_sprite_en')),
          'pausepar_pause_en': ('pausepar/pause_en.par', os.path.join(T, 'extraido', 'pausepar_pause_en'))}
# el resto de raíces se llaman como su carpeta en trabajo/extraido (salida de paginas_es.py)
for _c, _p in (('2dpar_ui_en', '2dpar/ui_en.par'), ('2dpar_sprite_en', '2dpar/sprite_en.par'), ('bootpar_boot_en', 'bootpar/boot_en.par'),
               ('pausepar_idol_work_en', 'pausepar/idol_work_en.par'), ('pausepar_movie_en', 'pausepar/movie_en.par'),
               ('pausepar_taxi_en', 'pausepar/taxi_en.par'), ('pausepar_title_menu_en', 'pausepar/title_menu_en.par'),
               ('pausepar_tougijyo_en', 'pausepar/tougijyo_en.par')):
    RAICES[_c] = (_p, os.path.join(T, 'extraido', _c))
SAL_TEXTO = os.path.join(T, 'salida')
ES = os.path.join(T, 'imagenes', 'es'); TMP = os.path.join(T, 'salida_img_tmp'); SAL = os.path.join(T, 'salida_img')


def partool(*a):
    r = subprocess.run([PT, *a], stdin=subprocess.DEVNULL, capture_output=True)
    if r.returncode != 0 or b'ERROR' in r.stdout.upper(): raise RuntimeError(f'ParTool {a[0]}: {r.stdout[-300:]!r}')


def main():
    shutil.rmtree(TMP, ignore_errors=True); shutil.rmtree(SAL, ignore_errors=True)
    for raiz, (par_juego, extraido) in RAICES.items():
        base = os.path.join(ES, raiz)
        if not os.path.isdir(base): continue
        anidados = collections.defaultdict(list); sueltos = []
        for dp, _, fs in os.walk(base):
            for f in fs:
                if not f.endswith('.dds'): continue
                rel = os.path.relpath(os.path.join(dp, f), base).replace(os.sep, '/')
                m = re.match(r'(.*?\.par)/(.*)', rel)
                (anidados[m.group(1)].append(m.group(2)) if m else sueltos.append(rel))
        if not sueltos and not anidados: continue          # (21-10) carpeta sin imágenes (todas apartadas)
        add = os.path.join(TMP, raiz, 'add')
        for r in sueltos:
            d = os.path.join(add, r); os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copy(os.path.join(base, r), d)
        for par, internos in anidados.items():
            a2 = os.path.join(TMP, raiz, 'anid', par.replace('/', '_'))
            # (25-10, claude2) las carpetas internas tienen MAYÚSCULAS («Texlist_0001») y las de es/ no: ParTool añadía una
            # carpeta nueva «texlist_0001» y el juego seguía leyendo la original (55 texturas sin traducir en la v1.0)
            real = {}
            for dp2, _, fs2 in os.walk(os.path.join(T, 'extraido_r', 'ui_en', par)):
                for f2 in fs2:
                    rr = os.path.relpath(os.path.join(dp2, f2), os.path.join(T, 'extraido_r', 'ui_en', par)).replace(os.sep, '/')
                    real[rr.lower()] = rr
            for r in internos:
                d = os.path.join(a2, real.get(r.lower(), r)); os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copy(os.path.join(base, par, r), d)
            d = os.path.join(add, par); os.makedirs(os.path.dirname(d), exist_ok=True)
            partool('add', os.path.join(extraido, par), a2, d); print('anidado', par, len(internos))
        out = os.path.join(SAL, 'data', par_juego); os.makedirs(os.path.dirname(out), exist_ok=True)
        con_texto = os.path.join(SAL_TEXTO, 'data', par_juego)
        base = con_texto if os.path.exists(con_texto) else os.path.join(JUEGO, par_juego)
        partool('add', base, add, out); print('par', par_juego, '(sobre los textos)' if base == con_texto else '')
        os.makedirs(os.path.dirname(con_texto), exist_ok=True); shutil.copy(out, con_texto)


if __name__ == '__main__': main()
