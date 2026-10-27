#!/bin/bash
# (Claude Code, 20-10-2026, de Yakuza 6) Reparto de lotes entre varios traductores a la vez (Fable y OpenCode).
# Imprime el siguiente lote libre (NNN) y lo deja reservado con mkdir (atómico); nada si no quedan.
#   bash herramientas/reclamar_lote.sh QUIEN
L=/c/mods/yakuza5/trabajo/lotes
for f in $(ls $L | grep -E "^lote_[0-9]{3}.json$"); do i=${f:5:3}
    [ -f "$L/lote_${i}_es.json" ] && python /c/mods/yakuza5/herramientas/validar_lote.py $i >/dev/null 2>&1 && continue
    if mkdir "$L/reclamados/$i" 2>/dev/null; then echo "$1" > "$L/reclamados/$i/quien"; echo $i; exit 0; fi
done
