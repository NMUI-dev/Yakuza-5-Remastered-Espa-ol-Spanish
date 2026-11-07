#!/bin/bash
# (07-11-2026, claude2) Mete las 7 texturas de imagenes_v110.py («Pistola» -> «Bala») en 2dpar/ui_en.par de entrega_v110:
# la de surfboard/pjd_omiyage.par (un .par dentro del .par: primero el interior) y las 6 de tex_common/common.
# Comprueba al final extrayendo que las 7 quedaron dentro iguales a las nuevas.
set -e
Y=/c/Mods/yakuza5; PT="$Y/herramientas/partool/ParTool.exe"; W="$Y/trabajo/v110_ui"; N="$Y/trabajo/imagenes/es_v110/2dpar/ui_en.par_x"
UI="$Y/entrega_v110/archivos/data/2dpar/ui_en.par"
rm -rf "$W"; mkdir -p "$W/add/surfboard" "$W/add/tex_common/common" "$W/out"
cp "$UI" "$W/ui_antes.par"
"$PT" extract "$W/ui_antes.par" "$W/ext" < /dev/null > /dev/null
"$PT" add "$W/ext/surfboard/pjd_omiyage.par" "$N/surfboard/pjd_omiyage.par" "$W/add/surfboard/pjd_omiyage.par" < /dev/null > "$W/out/omiyage.log" 2>&1
cp "$N"/tex_common/common/*.dds "$W/add/tex_common/common/"
"$PT" add "$W/ui_antes.par" "$W/add" "$W/out/ui_en.par" < /dev/null > "$W/out/ui_en.log" 2>&1
cp "$W/out/ui_en.par" "$UI"
# comprobación
rm -rf "$W/check"; "$PT" extract "$UI" "$W/check" -r < /dev/null > /dev/null
m=0
for f in $(cd "$N" && find . -name "*.dds"); do cmp -s "$N/$f" "$W/check/$f" || { echo "NO ENTRÓ $f"; m=$((m+1)); }; done
echo "texturas nuevas dentro de ui_en.par: $((7-m))/7"; [ $m = 0 ]
