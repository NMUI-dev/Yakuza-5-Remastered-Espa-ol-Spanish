# -*- coding: utf-8 -*-
"""(05-11-2026) v1.0.5: restos de inglés en imágenes que la revisión por OCR del paquete final encontró (imagenes_final_ocr.py):
medallas de la carrera de gallos, concurso de idol, karaoke («Next»), web Macsiv y tutoriales de idol.
Cada caja: se borran los píxeles de la letra inglesa (los que se apartan del fondo del borde de la caja) con inpaint y se
escribe el español centrado, del color de la letra original y del mayor tamaño que quepa. Términos = los del texto del juego.
Parte de la textura YA traducida del paquete (trabajo/img_final/es/...) y guarda DDS con el mismo formato (texconv).
  python imagenes_v105.py           -> trabajo/imagenes/es_v105/<ruta>.dds + hojas antes|después en trabajo/imagenes/es_v105/hoja_*.png
"""
import os, sys, subprocess, shutil
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dds_formato import formato

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(R, 'trabajo', 'img_final', 'es')
SAL = os.path.join(R, 'trabajo', 'imagenes', 'es_v105')
TEXCONV = os.path.join(R, 'herramientas', 'texconv', 'texconv.exe')
ARIALB = 'C:/Windows/Fonts/arialbd.ttf'
UI = '2dpar/ui_en.par_x/surfboard/'
# textura -> [(x0, y0, x1, y1, español, ancho máximo extra a cada lado)]
CAJAS = {
    UI + 'pjd_mg_kochin.par/texlist/2d_yk_kochin_00.dds': [
        (193, 330, 272, 354, 'Novato', 4, {'letra': (255, 255, 255), 'trazo': (40, 40, 40)}), (304, 330, 383, 353, 'Retador', 4, {'letra': (255, 255, 255), 'trazo': (40, 40, 40)}), (417, 331, 490, 352, 'Contendiente', 4, {'letra': (255, 255, 255), 'trazo': (40, 40, 40)}),
        (195, 441, 270, 463, 'Campeón', 4, {'letra': (255, 255, 255), 'trazo': (40, 40, 40)}), (306, 441, 383, 465, 'Conquistador', 4, {'letra': (255, 255, 255), 'trazo': (40, 40, 40)}), (418, 134, 468, 157, 'Oscuro', 12)],
    UI + 'pjd_sstory_h_quiz.par/texlist/2d_yk_h_quiz.dds': [
        (0, 812, 70, 842, 'Aciertos', 0, {'letra': (255, 255, 255), 'trazo': (214, 80, 140)}), (0, 842, 94, 879, 'Preguntas', 0, {'letra': (255, 255, 255), 'trazo': (60, 60, 60)}), (82, 880, 141, 909, 'Aciertos', 0, {'letra': (255, 255, 255), 'trazo': (214, 80, 140)}), (233, 878, 312, 909, 'Preguntas', 0, {'letra': (255, 255, 255), 'trazo': (40, 170, 200)})],
    UI + 'pjd_mg_karaoke_window.par/texlist/2d_jm_mg_karaoke01.dds': [(531, 634, 600, 669, 'Sig.', 0, {'letra': (231, 60, 8), 'trazo': (255, 255, 255)})],
    UI + 'pjd_tenkei_macsiv.par/texlist/2d_yk_macsiv.dds': [
        (851, 26, 968, 41, 'Inicio | Condiciones', 0), (883, 46, 932, 65, 'Entrar', 0)],
    UI + 'pjd_sstory_h_tutorial.par/Texlist_0001/2d_yk_h_tutorial.dds': [
        (206, 58, 295, 75, 'HEAT DE IDOL', 0), (428, 60, 505, 78, 'Nivel de agencia', 0), (426, 106, 492, 125, 'Habilidad de idol', 0),
        (525, 137, 559, 148, 'Canto', 0, {'letra': (255, 255, 255), 'trazo': None}), (438, 214, 463, 226, 'Encanto', 4), (523, 291, 560, 300, 'Actuación', 2, {'letra': (255, 255, 255), 'trazo': None}),
        (613, 214, 649, 222, 'Técnica', 0, {'letra': (255, 255, 255), 'trazo': None}), (160, 260, 210, 282, 'Rango', 0, {'letra': (255, 255, 255), 'trazo': (40, 36, 33)})],
    UI + 'pjd_sstory_h_tutorial_l.par/Texlist_0001/2d_yk_h_tutorial_l.dds': [(1, 0, 80, 13, 'LECCIÓN', 0, {'letra': (255, 255, 255), 'trazo': None})],
    UI + 'pjd_sstory_h_tutorial_l.par/Texlist_0001/2d_yk_h_tutorial_l00.dds': [
        (116, 16, 140, 26, 'Canto', 0, {'letra': (255, 255, 255), 'trazo': None}),
        (19, 93, 56, 101, 'Encanto', 0, {'letra': (255, 255, 255), 'trazo': None}),
        (109, 169, 146, 177, 'Actuación', 0, {'letra': (255, 255, 255), 'trazo': None})],
}


def borrar_y_escribir(img, x0, y0, x1, y1, texto, extra, fijo=None):
    a = np.array(img).astype(np.int16)                 # RGBA
    caja = a[y0:y1, x0:x1]
    borde = np.concatenate([caja[0], caja[-1], caja[:, 0], caja[:, -1]])
    fondo = np.median(borde, axis=0)
    dif = np.abs(caja[:, :, :3] - fondo[:3]).sum(axis=2) + np.abs(caja[:, :, 3] - fondo[3])
    mask = (dif > 70).astype(np.uint8)
    if mask.sum() == 0: return img, None
    px = caja[mask > 0][:, :4]; lum = px[:, :3].mean(axis=1); orden = np.argsort(lum)
    claro = np.median(px[orden[int(len(orden) * 0.75):]], axis=0); oscuro = np.median(px[orden[:max(1, int(len(orden) * 0.25))]], axis=0)
    lum_f = fondo[:3].mean()
    # letra = la parte que más se aparta del fondo; borde = la otra, si se distingue del fondo y de la letra
    if abs(claro[:3].mean() - lum_f) >= abs(oscuro[:3].mean() - lum_f): letra, otro = claro, oscuro
    else: letra, otro = oscuro, claro
    trazo = tuple(int(v) for v in otro[:3]) if (abs(otro[:3].mean() - letra[:3].mean()) > 80 and abs(otro[:3].mean() - lum_f) > 50) else None
    if fijo: letra = np.array(list(fijo['letra']) + [255]); trazo = fijo['trazo']
    m = np.zeros(a.shape[:2], np.uint8); m[y0:y1, x0:x1] = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=2) * 255
    uniforme = np.abs(borde[:, :3] - fondo[:3]).sum(axis=1).mean() < 30
    if uniforme:
        rgb = a[:, :, :3].astype(np.uint8).copy(); rgb[m > 0] = fondo[:3].astype(np.uint8)
    else:
        rgb = cv2.inpaint(np.ascontiguousarray(a[:, :, :3].astype(np.uint8)), m, 4, cv2.INPAINT_TELEA)
    alfa = a[:, :, 3].astype(np.uint8).copy()
    if fondo[3] < 128: alfa[m > 0] = int(fondo[3])                # fondo transparente: la letra se quita del alfa
    out = Image.fromarray(np.dstack([rgb, alfa]), 'RGBA')
    w, h = (x1 - x0) + 2 * extra - 2, (y1 - y0) - 2
    sw = 0
    tam = h + 4
    while tam > 6:
        sw = max(1, round(tam / 12)) if trazo else 0
        f = ImageFont.truetype(ARIALB, tam); bb = f.getbbox(texto, stroke_width=sw)
        if bb[2] - bb[0] <= w and bb[3] - bb[1] <= h: break
        tam -= 1
    capa = Image.new('RGBA', out.size, (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
    bb = f.getbbox(texto, stroke_width=sw); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    d.text((cx - (bb[0] + bb[2]) / 2, cy - (bb[1] + bb[3]) / 2), texto, font=f, fill=tuple(int(v) for v in letra[:3]) + (255,),
           stroke_width=sw, stroke_fill=(trazo + (255,)) if trazo else None)
    out.alpha_composite(capa)
    return out, (tuple(int(v) for v in letra[:3]), trazo, tam, 'liso' if uniforme else 'inpaint')


def guardar_dds(png, ref, dst):
    ancho, alto, mips, fmt, _ = formato(ref)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = os.path.dirname(dst)
    r = subprocess.run([TEXCONV, '-nologo', '-y', '-f', fmt, '-m', str(mips), '-o', tmp, png], capture_output=True, text=True)
    if r.returncode: sys.exit(r.stdout + r.stderr)
    hecho = os.path.join(tmp, os.path.splitext(os.path.basename(png))[0] + '.dds')
    if hecho != dst: shutil.move(hecho, dst)
    assert os.path.getsize(dst) == os.path.getsize(ref), (dst, os.path.getsize(dst), os.path.getsize(ref))


def main():
    os.makedirs(SAL, exist_ok=True); hojas = []
    for rel, cajas in CAJAS.items():
        ref = os.path.join(BASE, rel)
        img = Image.open(ref).convert('RGBA'); antes = img.copy()
        for c in cajas:
            img, info = borrar_y_escribir(img, *c)
            t = c[4]
            print(os.path.basename(rel), t, info)
        png = os.path.join(SAL, os.path.splitext(os.path.basename(rel))[0] + '.png'); img.save(png)
        guardar_dds(png, ref, os.path.join(SAL, rel))
        # hoja antes | después de las zonas tocadas
        xs0 = min(c[0] for c in cajas) - 20; ys0 = min(c[1] for c in cajas) - 20
        xs1 = max(c[2] for c in cajas) + 20; ys1 = max(c[3] for c in cajas) + 20
        caja = (max(0, xs0), max(0, ys0), min(img.width, xs1), min(img.height, ys1))
        par = [Image.alpha_composite(Image.new('RGBA', x.size, (90, 90, 90, 255)), x).crop(caja) for x in (antes, img)]
        h = Image.new('RGB', (par[0].width * 2 + 10, par[0].height), (255, 0, 0))
        h.paste(par[0], (0, 0)); h.paste(par[1], (par[0].width + 10, 0)); hojas.append(h)
    for i, h in enumerate(hojas):
        h.save(os.path.join(SAL, f'hoja_{i}.png'))
    print('listo', len(CAJAS), 'texturas')


if __name__ == '__main__':
    main()
