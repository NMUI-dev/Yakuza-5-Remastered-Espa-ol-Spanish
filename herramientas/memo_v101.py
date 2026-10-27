# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) v1.0.1: notas del reportero (2d_yk_sstory_e09_memo0*): la v1.0 tenía 3 de cada 4 tarjetas en
inglés. Cada tarjeta (renglones seguidos con el mismo margen) se borra y se escribe en español en Segoe UI, mismo color,
tamaño del original y como mucho 3 renglones dentro del ancho de la tarjeta."""
import os, re, statistics
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import atlas_es, paginas_v101 as PV, paginas_es as P
ES = {'iarriveattheparlor': 'Llego al salón de anfitrionas justo antes del cierre. Aun así, ella me recibe con calidez.',
      'uponenteringtheroom': 'Al entrar en la habitación, charlamos un poco. No sabe que soy periodista y quiere complacerme pese a la hora.',
      'orshallwesimply': '¿O simplemente nos desvestimos? No: a este precio exijo un estímulo más lento y sabroso. Ah, el nirvana me espera.',
      'myheartracing': 'Con el corazón acelerado por lo que vendrá, esquivo sus insinuaciones. Los veteranos saben saborear este delicado proceso.',
      'butitdidntmatter': 'Pero ya no importaba. Dejando de lado sus dudas, le arrebató con avidez a Toru lo que quedaba del ala de pollo.',
      'kaorihesitated': 'Kaori dudó un momento. Lo que acababa de tragar solo aumentó sus ganas de devorar más de la jugosa ofrenda de Toru.',
      'itssosalty': '«Está muy salado, Toru», susurró. Un pensamiento oscuro cruzó su mente: ¿y si su marido la viera?',
      'nowtellme': '«Dime, ¿a que sabe bien?». La voz de Toru tenía un filo acerado. Era una orden que no admitía réplica.'}
SEG = 'C:/Windows/Fonts/segoeui.ttf'
for f in ('memo01a', 'memo01q', 'memo02a', 'memo02q'):
    r = 'pausepar_pause_en/picture/2d_yk_sstory_e09_' + f
    a = np.array(Image.open(PV.origen(r + '.dds')).convert('RGBA')); W = a.shape[1]
    ls = sorted(PV.ocr2x(r + '.dds'), key=lambda l: (l[0] > W / 2, l[1]))
    tarjetas = []
    for l in ls:
        if tarjetas and abs(l[0] - tarjetas[-1][-1][0]) < 30 and 0 < l[1] - tarjetas[-1][-1][3] < 15: tarjetas[-1].append(l)
        else: tarjetas.append([l])
    tam = round(statistics.median(l[3] - l[1] for l in ls) * 0.95)
    a2 = P.borrar(a, [[l[0] - 3, l[1], l[2] + 3, l[3]] for l in ls]); img = Image.fromarray(a2); d = ImageDraw.Draw(img)
    for t in tarjetas:
        clave = next(k for k in ES if re.sub(r'[^a-z]', '', t[0][4].lower()).startswith(k))
        m, _ = P.mascara_tinta(a, t[0][:4]); col = P.color_tinta(a, m)
        x0 = t[0][0]; ym = (t[0][1] + t[0][3]) // 2; xd = max(l[2] for l in t)
        while xd < W - 1 and a[ym, xd, :3].min() > 200: xd += 1   # borde derecho de la tarjeta blanca
        ancho = xd - x0 - 12
        for k in range(tam, 9, -1):
            fo = ImageFont.truetype(SEG, k); rs = P.partir(ES[clave], fo, ancho)
            if len(rs) <= 3: break
        paso = 28
        for j, x in enumerate(rs): d.text((x0, (t[0][1] + t[0][3]) / 2 + j * paso), x, font=fo, fill=col + (255,), anchor='lm')
    atlas_es.TEX = os.path.join(PV.T, 'extraido'); atlas_es.SAL = PV.SAL; atlas_es.guardar_dds(r, img)
    v = Image.new('RGBA', (W, a.shape[0] * 2 + 8), (40, 40, 44, 255)); v.alpha_composite(Image.fromarray(a)); v.alpha_composite(img, (0, a.shape[0] + 8))
    v.convert('RGB').save(os.path.join(PV.REV, 'M_' + f + '.png')); print('ok', f, tam)
