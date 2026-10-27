# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) v1.0.1: rótulos de pincel (grupo C de la revisión): enemigos/jefes (2d_jm_bc_*), misiones
(2d_jm_ac_*), torneos (2d_jm_gp_*). La v1.0 los dejó estirados a lo alto, borrosos, en letra lisa o mezclados con el inglés.
Se parte del ORIGINAL: se borra cada renglón inglés (su caja del OCR a doble tamaño, alfa a 0, sin tocar el arco ni los
números «321») y se escribe el español en Knewave (la letra de pincel de la serie) blanca con su borde, del alto del original
y estrechado como mucho al 70 % (luego se achica), centrado en la misma caja.
  python herramientas/rotulos_v101.py  -> trabajo/imagenes/es_v101 + revision_v101/rehechas/C_*.png
"""
import os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
import paginas_v101 as PV
KN = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fuentes_img', 'Knewave-Regular.ttf')
CAP, GP = 'pausepar_pause_en/picture/caption/', 'pausepar_tougijyo_en/'
# ruta: [(caja (x0,y0,x1,y1) o índice de renglón del OCR, texto español)]
R = {
    CAP + '2d_jm_ac_321_nigero': [(0, '¡HUYE!')],
    CAP + '2d_jm_ac_321_oe': [(0, '¡PERSÍGUELOS!')],
    CAP + '2d_jm_ac_oe_saigou': [(0, 'PERSIGUE A SAIGO')],
    CAP + '2d_jm_ac_a1_l_oribie': [(0, 'VE A'), (1, 'OLIVIER')],
    CAP + '2d_jm_ac_l_oosakageinou': [((115, 0, 925, 128), 'VE A'), ((115, 128, 925, 256), 'OSAKA TALENT')],
    CAP + '2d_jm_ac_l_skyfainansuhe': [((161, 0, 867, 128), 'VE A'), ((161, 128, 867, 256), 'SKY FINANCE')],
    CAP + '2d_jm_ac_l_tegatawo': [((158, 0, 871, 128), 'CONSIGUE UN PASE'), ((158, 128, 871, 256), 'DEL CASINO')],
    CAP + '2d_jm_bc_boss_katsuya': [(0, 'NAOKI KATSUYA'), (1, 'JEFE DE LA SEDE DE LA ALIANZA OMI')],
    CAP + '2d_jm_bc_boss_kurosawa': [(0, 'HOMBRES DE KUROSAWA')],
    CAP + '2d_jm_bc_boss_yahatabuka': [(0, 'SUBORDINADOS DE YAHATA')],
    CAP + '2d_jm_bc_l_tinpira': [(0, 'PUNKS DE LA CALLE')],
    CAP + '2d_jm_bc_ss_chinpiramachi': [(0, 'PUNKS DE LA CALLE')],
    CAP + '2d_jm_bc_ss_tinpiramachi': [(0, 'PUNKS DE LA CALLE')],
    CAP + '2d_jm_bc_l_yamakasa': [(0, 'FAMILIA YAMAGASA')],
    CAP + '2d_jm_bc_ll_dammy': [(0, 'FAMILIA YAMAGASA')],
    CAP + '2d_jm_bc_s_hosuto': [(0, 'ANFITRIONES')],
    CAP + '2d_jm_bc_s_yamanokami': [(0, 'DIOS DE LA MONTAÑA')],
    CAP + '2d_jm_bc_ss_narikin': [(0, 'RICACHÓN')],
    CAP + '2d_jm_bc_ss_tinpira': [(0, 'MATONES')],
    CAP + '2d_jm_bc_ss_yopparai': [(0, 'BORRACHOS')],
    GP + '2d_jm_gp_1sen': [(0, 'RONDA 1')],
    GP + '2d_jm_gp_2kaisen': [(0, 'RONDA 2')],
    GP + '2d_jm_gp_hdeath': [(0, 'DUELO MORTAL 100')],
    GP + '2d_jm_gp_king': [((205, 80, 825, 178), 'REY DE REYES')],
    GP + '2d_jm_gp_limited': [(0, 'FURIA LIMITADA')],
    GP + '2d_jm_gp_ranker': [(0, 'GRAN PREMIO'), (1, 'DE LA ARENA CLASIFICADA')],
    GP + '2d_jm_gp_street': [(0, 'GRAN PREMIO'), (1, 'DE PELEAS CALLEJERAS')],
}


def tinta(a, caja):
    """la caja de tinta real dentro de la caja del OCR (el OCR la da con margen)"""
    x0, y0, x1, y1 = caja; z = a[y0:y1, x0:x1, 3] > 40
    ys, xs = np.where(z)
    if not len(ys): return caja
    return (x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1)


def escribir(img, caja, texto, borde):
    x0, y0, x1, y1 = caja; W, H = x1 - x0, y1 - y0
    # tamaño: que la altura de la MAYÚSCULA sea la del original
    f100 = ImageFont.truetype(KN, 100); bb = f100.getbbox('H', anchor='ls'); alto100 = bb[3] - bb[1]
    tam = max(10, round(100 * H / alto100 * 0.98))
    f = ImageFont.truetype(KN, tam); sw = max(1, round(tam * 0.05))
    w = f.getlength(texto) + 2 * sw
    capa = Image.new('RGBA', (int(w) + 8, int(tam * 1.5)), (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
    d.text((4 + sw, tam * 1.1), texto, font=f, fill=(255, 255, 255, 255), anchor='ls', stroke_width=sw, stroke_fill=borde)
    capa = capa.crop(capa.getbbox())
    cw, ch = capa.size
    esc_x = min(1.0, W * 0.97 / cw) if len(texto) > 8 or cw > W else 1.0
    if esc_x < 0.7:   # demasiado largo: se estrecha al 70 % y se achica en proporción
        k = W * 0.97 / (cw * 0.7); capa = capa.resize((max(1, int(cw * 0.7 * k)), max(1, int(ch * k))), Image.LANCZOS)
    else: capa = capa.resize((max(1, int(cw * esc_x)), ch), Image.LANCZOS)
    cw, ch = capa.size
    img.alpha_composite(capa, (int(x0 + (W - cw) / 2), int(y0 + (H - ch) / 2)))


def rehacer(r):
    o = np.array(Image.open(PV.origen(r + '.dds')).convert('RGBA')); a = o.copy()
    ls = sorted(PV.ocr2x(r + '.dds'), key=lambda l: l[1])
    trabajos = []
    for c, t in R[r]:
        caja = tuple(ls[c][:4]) if isinstance(c, int) else c
        ti = tinta(o, caja)
        z = o[ti[1]:ti[3], ti[0]:ti[2]]; op = z[z[..., 3] > 200][:, :3]
        borde = tuple(int(v) for v in np.median(op[op.sum(1) < 200], 0)) + (255,) if (op.sum(1) < 200).any() else (0, 0, 0, 255)
        trabajos.append((ti, t, borde))
    for ti, t, borde in trabajos:   # se borra la tinta del renglón (y lo que cuelga de él: halo del pincel)
        m = np.zeros(a.shape[:2], np.uint8); m[ti[1]:ti[3], ti[0]:ti[2]] = 1
        m = cv2.dilate(m, np.ones((7, 7), np.uint8)).astype(bool)
        a[m & (o[..., 3] > 0)] = 0
    img = Image.fromarray(a)
    trabajos.sort(key=lambda w: w[0][1])
    for k in range(len(trabajos) - 1):   # renglones que se solapan (el OCR los da montados): se reparte el alto
        a0, a1 = trabajos[k][0], trabajos[k + 1][0]
        if a1[1] < a0[3]:
            mid = (a0[3] + a1[1]) // 2
            trabajos[k] = ((a0[0], a0[1], a0[2], mid - 2),) + trabajos[k][1:]
            trabajos[k + 1] = ((a1[0], mid + 2, a1[2], a1[3]),) + trabajos[k + 1][1:]
    Wt = o.shape[1]
    for k, (ti, t, borde) in enumerate(trabajos):   # (los rótulos van centrados en la textura: el español puede ser más ancho)
        cx = (ti[0] + ti[2]) / 2; w = max(ti[2] - ti[0], min(Wt - 40, 64 * len(t) * (ti[3] - ti[1]) / 100))
        trabajos[k] = ((int(max(18, cx - w / 2)), ti[1], int(min(Wt - 18, cx + w / 2)), ti[3]), t, borde)
    for ti, t, borde in trabajos: escribir(img, ti, t, borde)
    atlas_es.TEX = os.path.join(PV.T, 'extraido'); atlas_es.SAL = PV.SAL; atlas_es.guardar_dds(r, img)
    H, W = o.shape[:2]
    v = Image.new('RGBA', (W, H * 2 + 8), (40, 40, 44, 255)); v.alpha_composite(Image.fromarray(o)); v.alpha_composite(img, (0, H + 8))
    v.convert('RGB').save(os.path.join(PV.REV, 'C_' + r.split('/')[-1] + '.png'))


def chact_kyukyoku():
    """«ULTIMATE ESSENCE» (blanco con brillo rojo + copia roja borrosa) -> «ESENCIA DEFINITIVA» en la misma letra de pincel
    (Knewave) y sus dos versiones, dentro de la caja del original"""
    from PIL import ImageFilter
    r = 'pausepar_pause_en/picture/chact/2d_jm_chact_kyukyoku'
    o = np.array(Image.open(PV.origen(r + '.dds')).convert('RGBA')); a = o.copy()
    cajas = [(14, 528, 312, 570), (14, 598, 312, 640)]
    for x0, y0, x1, y1 in cajas: a[y0 - 6:y1 + 6, max(0, x0 - 8):x1 + 8] = 0
    img = Image.fromarray(a); t = 'ESENCIA DEFINITIVA'
    for k, (x0, y0, x1, y1) in enumerate(cajas):
        W, H = x1 - x0, y1 - y0 - 8
        capa = Image.new('RGBA', (900, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
        d.text((20, 120), t, font=ImageFont.truetype(KN, 100), fill=(255, 255, 255, 255) if k == 0 else (230, 20, 20, 255), anchor='ls')
        capa = capa.crop(capa.getbbox()); capa = capa.resize((W, H), Image.LANCZOS)
        brillo = Image.new('RGBA', (W + 20, H + 20), (0, 0, 0, 0)); rojo = Image.new('RGBA', capa.size, (230, 0, 0, 255))
        brillo.paste(rojo, (10, 10), capa); brillo = brillo.filter(ImageFilter.GaussianBlur(4))
        for _ in range(3): img.alpha_composite(brillo, (x0 - 10, y0 + 4 - 10))
        if k == 1: capa = capa.filter(ImageFilter.GaussianBlur(1.5))
        img.alpha_composite(capa, (x0, y0 + 4))
    atlas_es.TEX = os.path.join(PV.T, 'extraido'); atlas_es.SAL = PV.SAL; atlas_es.guardar_dds(r, img)
    v = Image.new('RGBA', (680, 140), (60, 60, 60, 255)); v.alpha_composite(Image.fromarray(o).crop((0, 515, 330, 655)), (0, 0)); v.alpha_composite(img.crop((0, 515, 330, 655)), (340, 0))
    v.resize((1360, 280)).save(os.path.join(PV.REV, 'C_2d_jm_chact_kyukyoku.png'))


if __name__ == '__main__':
    for r in R:
        if len(sys.argv) > 1 and not any(x in r for x in sys.argv[1:]): continue
        rehacer(r); print('ok', r, flush=True)
    chact_kyukyoku()

