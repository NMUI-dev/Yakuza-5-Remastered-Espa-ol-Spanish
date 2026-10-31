# Cómo compilar la traducción de Yakuza 5 Remastered desde el código

Esto es para quien quiera **rehacer o revisar** la traducción. **Para jugar no hace falta:** descarga el zip de
[Releases](https://github.com/NMUI-dev/Yakuza-5-Remastered-Espa-ol-Spanish/releases/latest), descomprímelo y abre
`INSTALAR o QUITAR.bat`.

## Lo que necesitas

- Windows 10/11 y *Yakuza 5 Remastered* de Steam (en inglés, la versión actual de Steam) **sin la traducción
  instalada** (si la tienes, quítala con `INSTALAR o QUITAR.bat`, opción 2: los scripts se niegan a trabajar con ella puesta).
- [Git para Windows](https://git-scm.com/download/win) (trae **Git Bash**, donde se escriben los comandos de abajo).
- Todo lo demás lo baja **`PREPARAR TODO.bat`** (paso 2).

## 1. Descargar el código

Ponlo en `C:\Mods\yakuza5`. En Git Bash:

```bash
mkdir -p /c/Mods && cd /c/Mods
git -c core.longpaths=true clone https://github.com/NMUI-dev/Yakuza-5-Remastered-Espa-ol-Spanish.git yakuza5
cd yakuza5
```

(`core.longpaths` hace falta porque algunos nombres de archivo son largos. Sin Git: botón verde **Code → Download ZIP**
y descomprímelo como `C:\Mods\yakuza5`.)

## 2. Descargar todo lo necesario de una vez

Doble clic en **`PREPARAR TODO.bat`**. Hace esto solo, comprobando la SHA-256 de cada archivo:

| Qué | De dónde | Dónde lo deja |
|---|---|---|
| Python 3.12 (si no lo tienes, te pregunta si lo instala con winget) | python.org | el sistema |
| Paquetes de Python: numpy; y si dices que sí, los de imágenes (pillow, opencv, rapidocr, simple-lama-inpainting; unos 3 GB) | PyPI | el sistema |
| ParTool 1.3.4 (Kaplas80) | GitHub de ParManager | `herramientas/partool/` |
| reARMP (Ret-HZ, GPL-2.0) | copia incluida en `entrega/.../programas/reARMP` | `herramientas/reARMP/` |
| texconv may2026 (Microsoft DirectXTex, MIT) | GitHub de DirectXTex | `herramientas/texconv/` |
| 16 fuentes (Bangers, Oswald, Permanent Marker...) | Google Fonts | `herramientas/fuentes_img/` |

Puedes abrirlo las veces que quieras: lo que ya está bien no se vuelve a bajar. Con
`PREPARAR TODO.bat -SoloTexto` instala solo lo necesario para el texto (sin los 3 GB de imágenes).

## 3. Copiar y desempaquetar los archivos del juego

Di dónde está la carpeta `main/data` de tu juego (cámbiala si tu biblioteca de Steam está en otro sitio). Los scripts
la leen de la variable `Y5_JUEGO` y **solo leen** de ella: nunca escriben en Steam.

```bash
export Y5_JUEGO="C:/Program Files (x86)/Steam/steamapps/common/Yakuza 5/main/data"
J="$Y5_JUEGO"; PT=herramientas/partool/ParTool.exe
mkdir -p trabajo/extraido trabajo/extraido_r trabajo/originales trabajo/fuente
while read n p; do
  "$PT" extract "$(cygpath -w "$J/$p")" "$(cygpath -w trabajo/extraido/$n)" < /dev/null
  mkdir -p "trabajo/originales/$(dirname $p)" && cp "$J/$p" "trabajo/originales/$p"
done <<'EOF'
wdr_par_en_wdr wdr_par_en/wdr.par
wdr_par_en_common wdr_par_en/common.par
staypar_stay_en staypar/stay_en.par
bootpar_boot_en bootpar/boot_en.par
auth_subtitle auth/subtitle.par
2dpar_ui_en 2dpar/ui_en.par
2dpar_sprite_en 2dpar/sprite_en.par
pausepar_pause_en pausepar/pause_en.par
pausepar_title_menu_en pausepar/title_menu_en.par
pausepar_movie_en pausepar/movie_en.par
pausepar_kigae_en pausepar/kigae_en.par
pausepar_idol_work_en pausepar/idol_work_en.par
pausepar_snowball_en pausepar/snowball_en.par
pausepar_staffroll_en pausepar/staffroll_en.par
pausepar_taxi_en pausepar/taxi_en.par
pausepar_tougijyo_en pausepar/tougijyo_en.par
pausepar_book_en pausepar/book_en.par
minigame_en_karaoke minigame_en/karaoke.par
minigame_en_karaoke_e minigame_en/karaoke_e.par
font_font_hd_en fontpar/font_hd_en.par
EOF
# carpetas que en el juego son archivos sueltos
cp -r "$J/scenario_en" "$J/minigame_en" trabajo/extraido/
# ui_en desempaquetado entero (con los .par de dentro), para las texturas de menú
"$PT" extract -r "$(cygpath -w "$J/2dpar/ui_en.par")" "$(cygpath -w trabajo/extraido_r/ui_en)" < /dev/null
# mensajes del sistema
mkdir -p trabajo/originales/db.devil/en && cp "$J/db.devil/en/msg.bin" trabajo/originales/db.devil/en/
python herramientas/extraer.py
python herramientas/devil.py extraer
```

(Si a tu juego le falta alguno de esos `.par`, ParTool avisa y se sigue con el resto.)

## 4. Fuente

La fuente con `¿ ¡ í Í` redibujadas parte de una hoja del juego modificada, que no va en el repositorio (es imagen del
juego). Sácala del zip de la versión: copia `archivos/data/fontpar/font_hd_en.par` del zip de
[Releases](https://github.com/NMUI-dev/Yakuza-5-Remastered-Espa-ol-Spanish/releases/latest) a
`trabajo/fuente/font_hd_en.par`. Es exactamente la que usa la compilación.

## 5. Texturas con texto

Necesita los paquetes de imágenes del paso 2.

```bash
python herramientas/atlas_probar.py aplicar        # atlas de menús (trabajo/imagenes/atlas_hechos/*.json)
python herramientas/imagenes_es.py                 # páginas (reglas, capítulos, objetos)
python herramientas/paginas_es.py
python herramientas/acciones_es.py; python herramientas/habilidades_es.py; python herramientas/firstload_es.py
python herramientas/takara_es.py; python herramientas/textos_menu_es.py
bash herramientas/regenerar_v101.sh                # arreglos de la v1.0.1
python herramientas/mgs_v101.py; python herramientas/bacara_v101.py
```

Cómo funciona el kit de texturas: `trabajo/imagenes/GUIA_ATLAS.md`.

## 6. Texto, fuente y empaquetado

```bash
python herramientas/aplicar.py          # textos + fuente + texturas -> trabajo/salida/data
python herramientas/devil.py aplicar    # mensajes del sistema (siempre después de aplicar.py)
python herramientas/armar_v101.py       # junta todo y rehace los .par -> entrega_v101/archivos/data
python herramientas/verificar_v101.py   # vuelve a desempaquetar el resultado y lo compara
```

La traducción está en `trabajo/lotes/lote_NNN_es.json`; `herramientas/validar_lote.py` revisa cada lote.

## 7. Armar el mod

La carpeta `entrega_v101/archivos/data` junto con los archivos de `entrega/` (dentro, `archivos/data`) es el mod:
`INSTALAR o QUITAR.bat` lo instala en el juego (guarda antes los originales) y lo quita.
