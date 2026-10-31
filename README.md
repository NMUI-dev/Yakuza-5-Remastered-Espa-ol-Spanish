# Yakuza 5 Remastered — Spanish translation (source)

## Para jugar / To play

**No descargues el código (botón verde «Code»): no trae la traducción lista.** Descarga el zip de la última versión en **[Releases](https://github.com/NMUI-dev/Yakuza-5-Remastered-Espa-ol-Spanish/releases/latest)** (`Yakuza.5.-.Traduccion.al.espanol.v1.0.1.zip`), descomprímelo en una carpeta, haz doble clic en **`INSTALAR o QUITAR.bat`** y escribe `1` (instalar). El instalador encuentra el juego de Steam solo y guarda una copia de los archivos originales para poder quitarla. Lee el `LEEME.txt` del zip.

*Do not download the source (green «Code» button): it does not contain the ready translation.* Get the zip from **[Releases](https://github.com/NMUI-dev/Yakuza-5-Remastered-Espa-ol-Spanish/releases/latest)**, unzip it into a folder, double-click **`INSTALAR o QUITAR.bat`** and type `1` (install). The installer finds the Steam game by itself and backs up the original files so it can be removed.

The rest of this page is the source code, for people who want to rebuild or check the mod.

Source code and translation data for the fan-made Spanish (Latin American neutral) translation of
*Yakuza 5 Remastered* (Steam, PC). Release v1.0.1.

**This repository contains no game files.** Everything here is our own scripts, the translated text and the
specifications used to redraw in-image text. To build the mod you need your own copy of the game from Steam.

## What the released mod contains

The release zip only replaces files inside the game's `main/data` folder: `.par` archives (SEGA's container format)
and a few `.bin` tables, rebuilt with the Spanish text, fixed font cells and redrawn textures. No executable is
modified and no `.exe`/`.dll` is shipped.

| Part | Built by | From |
|---|---|---|
| Dialogue `.msg`, subtitles, tables, menus, mails, scripts | `herramientas/aplicar.py` | `trabajo/lotes/lote_NNN_es.json` |
| System messages (`db.devil/en/msg.bin`, ARMP) | `herramientas/devil.py aplicar` | translation in `entrega/Herramientas para traduccion/datos/devil.json` |
| Font (`fontpar/font_hd_en.par`) | `herramientas/aplicar.py`, `letra_i.py` | game font + redrawn `¿ ¡ í Í` cells |
| Textures with text (`pausepar/*.par`, `2dpar/*.par`, ...) | `herramientas/imagenes_*.py`, `atlas_*.py`, `paginas_*.py`, `*_v101.py` | specs in `trabajo/imagenes/` |

The installer (`entrega/instalar.ps1`, started by `entrega/INSTALAR o QUITAR.bat`) is a plain PowerShell script: it
finds the game through Steam's `libraryfolders.vdf`, backs up the original files and copies the translated ones;
option 2 restores the backup. It downloads nothing and runs nothing else.

`entrega/Herramientas para traduccion/` is the optional "translation tools" package for people who want to edit the
texts (`herramienta_traduccion.py extraer|aplicar`, all translations in `datos/traducciones.json`). It does **not**
include ParTool: the user downloads it (see below).

## Repository layout

```
herramientas/                 our build scripts (Python 3 + a few bash scripts)
trabajo/lotes/                the translation: lote_NNN.json (English) + lote_NNN_es.json (Spanish), indice.json
                              (where every text lives in the game files), GUIA_TRADUCCION.md, glosario_vivo.md
trabajo/habilidades_clases.json
trabajo/imagenes/*.json       texture specs: OCR boxes, translations, fonts, sizes (atlas_fuentes.json, cortos.json, ...)
trabajo/imagenes/atlas_hechos/   per-texture specs for menu atlases (box, English, Spanish, font, effect)
trabajo/imagenes/GUIA_ATLAS.md   how the texture kit works
trabajo/imagenes/revision_v101/  v1.0.1 review lists (which textures were redone and why)
entrega/                      installer + optional translation tools, as shipped (without third-party .exe)
```

## Requirements

- Windows 10/11, *Yakuza 5 Remastered* from Steam (English, current Steam build).
- Python 3.12 with: `pip install numpy pillow opencv-python rapidocr-onnxruntime simple-lama-inpainting`
  (OCR and LaMa are only needed to regenerate textures).
- Git Bash (for the `.sh` scripts).
- Third-party tools (not included, download them into these folders):
  - **ParTool** (ParManager by Kaplas80) — `herramientas/partool/ParTool.exe`
    <https://github.com/Kaplas80/ParManager/releases/download/v1.3.4/v1.3.4-windows-x64.zip>
    (SHA-256 of ParTool.exe: `b798027a243229c04741e491abb1f92ae4cc7a379c0cba31b81446f9be4e5b3f`)
  - **reARMP** (Ret-HZ, GPL-2.0) — `herramientas/reARMP/reARMP.py` <https://github.com/Ret-HZ/reARMP>
    (a copy with its LICENSE is in `entrega/Herramientas para traduccion/programas/reARMP/`)
  - **texconv** (Microsoft DirectXTex, MIT, for BC7 textures) — `herramientas/texconv/texconv.exe`
    <https://github.com/microsoft/DirectXTex/releases>
  - Fonts for redrawn textures (Google Fonts, OFL/Apache) — `herramientas/fuentes_img/`:
    Bangers, Caveat Brush, Fjalla One, Gochi Hand, Kalam Bold, Knewave, Lilita One, Marck Script, Nanum Brush Script,
    Oswald, Permanent Marker, Rock Salt, Rubik Dirt, Sedgwick Ave Display, Shojumaru, Yuji Syuku
    (<https://fonts.google.com>). Some specs also use standard Windows fonts from `C:\Windows\Fonts` (e.g. Georgia).

## How to build

Clone the repository to `C:\Mods\yakuza5` (several scripts have that working folder hard-coded) and run everything
from there in Git Bash. The game folder is set in `herramientas/aplicar.py` (`JUEGO = .../Yakuza 5/main/data`):
change it if your Steam library is elsewhere. The game must be the **original** (uninstall the translation first:
`aplicar.py` refuses to run if it finds it installed).

### 1. Unpack the original files

Unpack every archive listed in `ARCHIVOS` at the top of `herramientas/aplicar.py` into `trabajo/extraido/<name>`
(e.g. `wdr_par_en/wdr.par` → `trabajo/extraido/wdr_par_en_wdr`), plus the loose folders `scenario_en` and
`minigame_en`, and `fontpar/font_hd_en.par` → `trabajo/extraido/font_font_hd_en`:

```bash
J="/d/SteamLibrary/steamapps/common/Yakuza 5/main/data"
herramientas/partool/ParTool.exe extract "$(cygpath -w "$J/wdr_par_en/wdr.par")" "$(cygpath -w trabajo/extraido/wdr_par_en_wdr)" < /dev/null
# ... same for each entry of ARCHIVOS
python herramientas/extraer.py      # -> trabajo/textos_en.jsonl + trabajo/unicos_en.json (all English text with its location)
python herramientas/devil.py extraer
```

(`extraer.py`, `preparar_lotes.py` and `traductor_gemini.py` are how the English text was extracted, split into the
batches in `trabajo/lotes` and translated; the batches are already in the repo. `validar_lote.py` checks each batch:
tags, line breaks, length limits, characters the font can draw.)

### 2. Textures

```bash
# v1.0 textures -> trabajo/imagenes/es
python herramientas/atlas_probar.py aplicar        # menu atlases from trabajo/imagenes/atlas_hechos/*.json
python herramientas/imagenes_es.py                 # "page" textures (rules, chapters, items) from the OCR specs
python herramientas/paginas_es.py
python herramientas/acciones_es.py; python herramientas/habilidades_es.py; python herramientas/firstload_es.py
python herramientas/takara_es.py; python herramientas/textos_menu_es.py
# v1.0.1 fixes -> trabajo/imagenes/es_v101
bash herramientas/regenerar_v101.sh
python herramientas/mgs_v101.py; python herramientas/bacara_v101.py
```

Each spec lists the English text box, the Spanish text, font, size and effect. The scripts erase the English text
(transparent pixels, or LaMa inpainting on opaque backgrounds), draw the Spanish text copying the original height,
colour, gradient, outline and glow, and save the DDS with the original header and mipmaps (`v101_bloques.py` keeps the
original DXT blocks outside the edited boxes). Details: `trabajo/imagenes/GUIA_ATLAS.md`.

### 3. Text, font and packing

```bash
python herramientas/aplicar.py          # text + font + textures -> trabajo/salida/data (empties trabajo/salida first)
python herramientas/devil.py aplicar    # system messages (must run after aplicar.py)
python herramientas/armar_v101.py       # merges v1.0 + v1.0.1 textures, rebuilds the .par files -> entrega_v101/archivos/data
python herramientas/verificar_v101.py   # unpacks the result again and compares every texture/table
```

`aplicar.py` writes each Spanish text in place (dialogue `.msg` records are rebuilt with new lengths and offsets;
fixed-size slots never overflow — if a line does not fit it uses the short version from `cortas.json`) and repacks the
`.par` archives with `ParTool add`. The folder `entrega_v101/archivos/data` plus the files in `entrega/` is the
released mod.

## Testing

We tested in a separate copy of the game so the Steam install was never modified until the end, then installed with
the installer on the Steam copy and played. That test setup is not part of this repository.

## Credits and licenses

- Our scripts, installer and translation data: MIT (see `LICENSE`). The game, its text and its assets belong to SEGA;
  this is an unofficial fan translation and is not affiliated with SEGA.
- ParTool / ParManager — Kaplas80 (see its repository for the license). reARMP — Ret-HZ (GPL-2.0). texconv —
  Microsoft (MIT). Fonts — their authors (SIL OFL / Apache 2.0).
- Translation made with AI assistance (Claude by Anthropic, Google Gemini and free OpenRouter models) and reviewed.
