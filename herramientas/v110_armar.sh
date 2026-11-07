#!/bin/bash
# (claude2, 06-11-2026) Arma la v1.0.10 del Y5 con la herramienta pública: copia entrega_v109 -> entrega_v110, pone las
# correcciones (trabajo/revision_0711c/datos_v110.py) y aplica. Luego: trabajo/revision_0711c/comprobar_v110.sh
# Uso: bash herramientas/v110_armar.sh
set -e
Y=/c/Mods/yakuza5; H="$Y/entrega_v110/Herramientas para traduccion"
ORI="C:/Mods/Entregas/Entregas Yakuza 5/Yakuza 5 - Traduccion al espanol v1.0.9/respaldo_original"
[ -d "$Y/entrega_v110/respaldo_original" ] && { echo "ALTO: entrega_v110 está INSTALADA en Steam (tiene respaldo_original). Quítala antes (opción 2) o borrarías los originales."; exit 1; }
rm -rf "$Y/entrega_v110"; cp -r "$Y/entrega_v109" "$Y/entrega_v110"
rm -rf "$H/__pycache__" "$H/salida" "$Y/entrega_v110/respaldo_original"
python -I -X utf8 "$Y/trabajo/revision_0711c/datos_v110.py"
cd "$H"
python -I -X utf8 -u herramienta_traduccion.py aplicar --ingles "$ORI" > "$Y/trabajo/v110_aplicar.log" 2>&1
sed -n 3p "$Y/trabajo/v110_aplicar.log"; sed -n 3p "$Y/trabajo/v109_aplicar.log"
cp -r salida/data/. "$Y/entrega_v110/archivos/data/"
python -I -X utf8 "$Y/trabajo/revision_0711c/version_v110.py"
bash "$Y/herramientas/meter_v110.sh"
echo "armada v1.0.10"
