#!/bin/bash
# (claude1, 21-10-2026) FULL AHORRO: páginas pendientes SIN Fable. Por cada atlas libre: borrador (OCR+gemma4) ->
# probar (gemma4 marca) -> si 0 marcas y 0 casillas «revisar», aceptar; si no, queda en inglés (lista en paginas_auto_dejadas.txt).
# Espera a que no esté abierto Yakuza5.exe (pruebas de claude2). Log: tareas/paginas_auto.log
cd /c/mods/yakuza5
B=trabajo/imagenes/atlas_borradores; P=trabajo/imagenes/atlas_pruebas; D=tareas/paginas_auto_dejadas.txt
while :; do
  while ps -W | grep -qi Yakuza5.exe; do sleep 60; done
  id=$(python herramientas/atlas_probar.py reclamar auto1 2>/dev/null | tail -1)
  [ -z "$id" ] && { echo "FIN $(date +%H:%M)"; break; }
  python herramientas/atlas_borrador.py hacer "$id" >/dev/null 2>&1
  [ -f $B/$id.json ] || { echo "$id sin borrador" | tee -a $D; continue; }
  python herramientas/atlas_probar.py probar "$id" >/dev/null 2>&1
  rev=$(grep -c '"revisar"' $B/$id.json); m=$(python -c "import json;print(len(json.load(open('$P/${id}_gemma.json',encoding='utf-8'))))" 2>/dev/null || echo 99)
  if [ "$rev" = 0 ] && [ "$m" = 0 ]; then python herramientas/atlas_probar.py aceptar "$id" >/dev/null 2>&1; echo "$id ACEPTADO"
  else echo "$id dejado (revisar $rev, gemma $m)" | tee -a $D; fi
done
