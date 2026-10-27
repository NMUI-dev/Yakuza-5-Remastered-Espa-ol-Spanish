# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Aviso del mando al arrancar («REAL YAKUZA USE A GAMEPAD»), con letra de pincel como el
original (CaveatBrush, OFL): se borra el inglés (inpaint) y se escribe «LOS YAKUZA DE VERDAD JUEGAN CON MANDO» del mismo ancho.
Hecha a mano: está en trabajo/imagenes/manuales.txt, imagenes_es.py no la toca.
  python herramientas/firstload_es.py
"""
import os, sys
os.environ.update(ROT_FUENTE='CaveatBrush-Regular.ttf', ROT_GROSOR='3', ROT_ESTRECHO='0.92', ROT_ANCHO_ORIG='1')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rotulos, atlas_es
from PIL import Image
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = 'pausepar_pause_en/picture/firstload/firstload_yakuza_pad'
atlas_es.TEX = os.path.join(R, 'trabajo', 'extraido')
o = Image.open(os.path.join(atlas_es.TEX, RUTA + '.dds')).convert('RGBA')
atlas_es.guardar_dds(RUTA, rotulos.sobre_fondo(o, (240, 680, 1810, 820), ['LOS YAKUZA DE VERDAD JUEGAN CON MANDO']))
print('ok', RUTA)
