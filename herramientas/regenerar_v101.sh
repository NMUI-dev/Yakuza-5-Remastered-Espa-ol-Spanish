#!/bin/bash
# (claude2, 25-10-2026) Regenera TODAS las texturas de la v1.0.1 de claude2 en es_v101, en el orden correcto (cada paso
# puede partir del anterior). Las 78 guías mgs y las 8 de bacará son de claude1 (mgs_v101.py, bacara_v101.py).
set -e; cd "$(dirname "$0")"; export PYTHONIOENCODING=utf-8 SIN_RED=1
python -u paginas_v101.py $(cat ../trabajo/imagenes/revision_v101/lista_B2.txt)
python dardos2_v101.py
python atlas_v101.py
python dardos_v101.py picture/rule_countup_0.dds picture/rule_cricket_0.dds rule_button   # (rutas exactas: «cricket_0» pisaba rule_darts_cricket_0X)
python cricket0_v101.py
python r01_v101.py
python rotulos_v101.py
python puri_v101.py
python alma_v101.py
python memo_v101.py
python mapa_v101.py
python medidor_v101.py
python blackjack_or_v101.py
python tres_a_mano.py
python botones_puri_v101.py   # (barras del purikura y puri_text de la interfaz; después de atlas_v101)
python intro_dardos_v101.py   # (rule_01_0, rule_cricket_0, rule_countup_0 desde el original: pisa lo anterior de esas 3)
cp ../trabajo/imagenes/es_reserva/pausepar_tougijyo_en/2d_jm_tougi_okite*.dds ../trabajo/imagenes/es_v101/pausepar_tougijyo_en/
python -I reglas_c1_v101.py   # (claude1) sus 38 páginas de reglas: van las últimas porque paginas_v101.py las pisaría
echo REGENERADO_OK
