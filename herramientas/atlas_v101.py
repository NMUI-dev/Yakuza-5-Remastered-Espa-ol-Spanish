# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) v1.0.1: correcciones de atlas sueltos (grupo F de la revisión y menores). Parte de la especificación
del kit (trabajo/imagenes/atlas_hechos/<id>.json, que NO se toca: claude1 la usa para los grupos A y C), le aplica los
cambios de CAMBIOS y dibuja con atlas_probar.dibujar -> trabajo/imagenes/es_v101/<textura>.dds.
CAMBIOS: id -> lista de (en del item, n.º de aparición, {campos nuevos}) ; en = None añade un item nuevo.
  python herramientas/atlas_v101.py
"""
import copy, json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es, atlas_probar
from atlas_borrador import HECHOS
import paginas_v101 as PV
SI = {'dejar': False}
U = 'ui_en__surfboard__'
CAMBIOS = {
    'pausepar_pause_en__picture__2d_yk_map_yukiyama': [('Snowy', 0, {'es': 'Montaña', 'caja': [36, 46, 223, 97], 'ancho_max': 183, 'tam': 42}), ('Mountain', 0, {'es': 'Nevada', 'tam': 42})],
    U + 'pjd_mg_hanafuda01.par__texlist__2d_jm_mg_hanafuda02': [('Scoring', 0, {'caja': [226, 70, 484, 110], 'en': 'Scoring Combinations', 'es': 'Combinaciones de puntos', 'fuente': 'times.ttf'}),
                                                               ('Combinations', 0, {'borrar': True})],
    U + 'pjd_mg_yukigassen.par__2d_mg_yukigassen_texlist__2d_jm_mg_yukigassen_pt': [
        ('HIT!', 0, dict(SI, es='')), ('to', 0, dict(SI, es='a')), ('PLAYER1', 1, dict(SI, es='JUGADOR1')),
        ('PLAYER2', 1, dict(SI, es='JUGADOR2')), ('PLAYER3', 1, dict(SI, es='JUGADOR3')), ('STRIKE!', 0, {'es': '¡DE LLENO!'})],
    U + 'pjd_mg_yukigassen.par__2d_mg_yukigassen_texlist__2d_jm_mg_yukigassen': [('Remaining', 0, SI), ('snowballs', 0, SI), ('STRIKE', 0, dict(SI, es='DE LLENO'))],
    U + 'pjd_sstory_h_akushu.par__texlist__2d_yk_h_akushu': [('Hold down button', 0, dict(SI, es='Mantén pulsado el botón', efecto='nada', color=[255, 150, 200], ancho_max=180)),
                                                             ('to shake hands', 0, dict(SI, es='para dar la mano', efecto='nada', color=[255, 150, 200], ancho_max=180))],
    U + 'pjd_sstory_taxi_result.par__texlist_0001__2d_jm_taxi_result': [('RESULTS', 0, dict(SI, es='RESULTADOS', efecto='nada', color=[255, 255, 255])),
        ('LEVEL UP', 0, dict(SI, es='SUBES DE NIVEL', caja=[96, 212, 256, 244], fuente='arialbd.ttf', efecto='nada', color=[255, 255, 255], alto=26, ancho_max=158))],
    U + 'pjd_sstory_yakyu_result.par__texlist__2d_yk_yakyu_result': [('Victory', 2, dict(SI, es='Victoria')), ('Victory', 0, {'radio': 1.6})],
    'pausepar_pause_en__picture__puri_button': [('Close Next Page', 0, {'caja': [548, 18, 730, 48], 'es': 'Cerrar   Siguiente', 'efecto': 'nada', 'color': [235, 235, 235]}), ('Previous Page', 0, {'es': 'Anterior'})],
    'pausepar_pause_en__picture__rule_01_0': [('01 GAMES', 0, {'efecto': 'estilo'}), ('Introduction', 0, {'fuente': 'segoeui.ttf'}), ('Note', 0, {'fuente': 'segoeui.ttf'})],
    'pausepar_pause_en__picture__rule_cricket_0': [('Introduction', 0, {'fuente': 'segoeui.ttf'}), ('Note', 0, {'fuente': 'segoeui.ttf'})],
    'pausepar_pause_en__picture__puri_button_bb': [('Previous Page X OK', 0, {'caja': [288, 18, 427, 47], 'en': 'Previous Page', 'es': 'Anterior'}),
                                                   ('Close Next Page', 0, {'es': 'Cerrar      Siguiente'})],
    U + 'pjd_mg_purikura_note.par__2d_mg_purikura_note_texlist__puri_text': [('Choose', 0, {'caja': [0, 0, 397, 32], 'es': 'Elige la foto que quieres cambiar'}),
                                                                             ('photo to replace', 0, {'borrar': True})],
    'pausepar_title_menu_en__title_menu__2d_jm_title_vs_billiards': [('Pool', 0, dict(SI, es='Billar', fuente='segoeuiz.ttf'))],
    U + 'pjd_mg_batting.par__texlist__2d_yk_mg_batting000': [('RESULT', 0, dict(SI, es='RESULTADO', fuente='segoeuiz.ttf')),
        ('Bomb chance', 0, {'es': 'Ocasión de bomba'}), ('Course', 0, {'es': 'Nivel'}),
        ('Number Correct', 1, {'caja': [198, 180, 404, 200], 'es': 'Aciertos restantes', 'ancho_max': 200}), ('Left', 0, {'borrar': True}),
        ('Sinker', 0, dict(SI, es='Hundida'))],
    U + 'pjd_mg_taiko_select.par__texlist_0001__taiko_music_select_02': [('1st Song', 0, dict(SI, es='1.ª canción')), ('2nd Song', 0, dict(SI, es='2.ª canción')),
        ('1st', 0, {'es': '1.°'}), ('2nd', 0, {'es': '2.°'}), ('3rd', 0, {'es': '3.°'})],   # (º salía con rayita debajo)
    U + 'pjd_mg_taiko_common.par__texlist_0001__taiko_music_select_02': [('1st Song', 0, dict(SI, es='1.ª canción')), ('2nd Song', 0, dict(SI, es='2.ª canción')),
        ('1st', 0, {'es': '1.°'}), ('2nd', 0, {'es': '2.°'}), ('3rd', 0, {'es': '3.°'})],   # (º salía con rayita debajo)
    U + 'pjd_mg_taiko_select.par__texlist_0001__taiko_music_select_01': [   # (salía rojo con borde blanco: el original es al revés)
        ('Select Song', 0, {'estilo': {'arriba': [255, 255, 255], 'abajo': [255, 255, 255], 'contorno': [[235, 40, 30], 4], 'brillo': [0, 0, 0]}}), ('Select Difficulty', 0, {'estilo': {'arriba': [255, 255, 255], 'abajo': [255, 255, 255], 'contorno': [[235, 40, 30], 4], 'brillo': [0, 0, 0]}})],
    U + 'pjd_sstory_h_skill.par__texlist_0001__2d_yk_h_skill': [('CLOSED', 0, dict(SI, es='CERRADO', fuente='segoeuisl.ttf', color=[235, 235, 235], fondo='lama'))],
    U + 'pjd_sstory_yuki_mission.par__2d_mg_sstory_yuki_mission_texlist__2d_jm_yuki_mission': [
        ('Select List', 0, {'ancho_max': 84}), ('Skills', 0, {'caja': [0, 96, 64, 127], 'fuente': 'segoeuiz.ttf'}), ('Status', 0, {'caja': [64, 96, 125, 127], 'fuente': 'segoeuiz.ttf'})],
    U + 'pjd_tougi_btl.par__pjd_tougi_btl__2d_jm_tougi_result': [('Results', 1, dict(SI, es='Resultados')),
        ('LEVEL', 0, dict(SI, es='SUBES DE NIVEL', caja=[136, 212, 298, 237], fuente='segoeuib.ttf', efecto='estilo', alin='centro')),
        ('UP', 0, {'borrar': True}), ('Excitement', 0, {'es': 'Nivel de', 'ancho_max': 84}), ('Level', 0, {'es': 'emoción', 'caja': [240, 136, 328, 160], 'ancho_max': 84})],
}


def spec_de(i):
    s = json.load(open(os.path.join(HECHOS, i + '.json'), encoding='utf-8')); s = copy.deepcopy(s)
    for en, n, campos in CAMBIOS[i]:
        cand = [it for it in s['items'] if it['en'] == en]
        if len(cand) <= n:
            print(f'  {i}: no hay «{en}» n.º {n} (hay {len(cand)})'); continue
        cand[n].update(campos)
    s['items'] = [it for it in s['items'] if not it.get('borrar')]
    return s


def rayado(o, nv):
    """taxi_result: la copia rayada de RESULTS (0,48)-(240,96) se rehace con RESULTADOS de arriba y las rayas del original"""
    o, n = np.array(o.convert('RGBA')).astype(float), np.array(nv.convert('RGBA')).astype(float)
    arriba = n[0:48, 0:240].copy()
    ro, rc = o[0:48, 0:240, :3].max(2), o[48:96, 0:240, :3].max(2)
    f = np.clip(rc.sum(1) / np.maximum(ro.sum(1), 1), 0, 1)[:, None]   # brillo de cada fila de la copia / la de arriba
    copia = arriba.copy(); copia[..., :3] *= f[..., None] if f.ndim == 2 else f; copia[..., 3] *= f[:, 0][:, None] if False else 1
    copia[..., 3] = arriba[..., 3] * np.clip(o[48:96, 0:240, 3].sum(1) / np.maximum(o[0:48, 0:240, 3].sum(1), 1), 0, 1)[:, None]
    n[48:96, 0:240] = copia
    return Image.fromarray(n.clip(0, 255).astype(np.uint8))


def mision(o, nv):
    """2d_jm_yuki_mission: la sombra de «Skills Status» asomaba detrás: se rellena la franja con su fondo y se escribe a mano"""
    from PIL import ImageDraw, ImageFont
    a = np.array(nv.convert('RGBA')); ob = np.array(o.convert('RGBA'))
    for y in range(97, 128): a[y, 0:128] = np.median(ob[y, 130:200], 0).astype(np.uint8)
    img = Image.fromarray(a); d = ImageDraw.Draw(img); f = 'C:/Windows/Fonts/segoeuiz.ttf'
    for t, x0, x1 in (('Técnicas', 2, 66), ('Estado', 70, 126)):
        tam = 22
        while ImageFont.truetype(f, tam).getlength(t) > x1 - x0: tam -= 1
        d.text((x0, 112), t, font=ImageFont.truetype(f, tam), fill=(255, 255, 255, 255), anchor='lm')
    # «Elegir lista» y «Armas / Equipo»: el borrado del kit dejaba el contorno negro inglés; se vacía la franja (es transparente)
    # y se escriben blancos con su contorno negro, como el original
    a = np.array(img); a[71:99, 78:342] = 0; img = Image.fromarray(a); d = ImageDraw.Draw(img)
    for t, fu, x0, x1 in (('Elegir lista', 'segoeuii.ttf', 80, 172), ('Armas / Equipo', 'segoeuiz.ttf', 179, 337)):
        tam = 19
        while ImageFont.truetype('C:/Windows/Fonts/' + fu, tam).getlength(t) > x1 - x0 - 4: tam -= 1
        d.text((x0 + 2, 86), t, font=ImageFont.truetype('C:/Windows/Fonts/' + fu, tam), fill=(240, 240, 240, 255), anchor='lm', stroke_width=2, stroke_fill=(0, 0, 0, 255))
    return img


def golpe(o, nv):
    """yukigassen_pt: «¡GOLPE!» en el hueco de «HIT!» (47 px): a la altura de «JUGADOR1», estrechado en horizontal para caber
    sin tocar la columna de nombres (SAEJIMA); azul con brillo, como los demás rótulos de la fila"""
    from PIL import ImageDraw, ImageFont, ImageFilter
    a = np.array(nv.convert('RGBA')); a[146:172, 160:207] = 0; img = Image.fromarray(a)
    f = ImageFont.truetype('C:/Windows/Fonts/verdana.ttf', 17)
    capa = Image.new('L', (120, 40), 0); ImageDraw.Draw(capa).text((4, 20), '¡GOLPE!', font=f, fill=255, anchor='lm')
    capa = capa.crop(capa.getbbox()); capa = capa.resize((41, capa.height), Image.LANCZOS)
    m = Image.new('L', img.size, 0); m.paste(capa, (160, 159 - capa.height // 2))
    halo = m.filter(ImageFilter.GaussianBlur(2.2)).point(lambda v: min(255, int(v * 1.6)))
    img.alpha_composite(Image.merge('RGBA', [Image.new('L', img.size, c) for c in (40, 110, 255)] + [halo]))
    img.alpha_composite(Image.merge('RGBA', [Image.new('L', img.size, c) for c in (170, 205, 255)] + [m]))
    return img


def billar(o):
    """título «Pool» (blanco con contorno negro sobre la foto): se quita con inpaint y se escribe «Billar» con el mismo estilo"""
    import cv2
    from PIL import ImageDraw, ImageFont
    a = np.array(o.convert('RGBA')); x0, y0, x1, y1 = 166, 3, 254, 38
    m = np.zeros(a.shape[:2], np.uint8); z = a[y0:y1, x0:x1, :3]
    m[y0:y1, x0:x1] = (z.min(2) > 170) * 255; m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=3)
    a[..., :3] = cv2.inpaint(np.ascontiguousarray(a[..., :3]), m, 5, cv2.INPAINT_TELEA)
    img = Image.fromarray(a); d = ImageDraw.Draw(img); f = 'C:/Windows/Fonts/segoeuiz.ttf'; tam = 30
    while ImageFont.truetype(f, tam).getlength('Billar') > 84: tam -= 1
    d.text((211, 21), 'Billar', font=ImageFont.truetype(f, tam), fill=(250, 250, 250, 255), anchor='mm', stroke_width=2, stroke_fill=(10, 10, 10, 255))
    return img


TAIKO_V = {
    'ui_en/surfboard/pjd_mg_taiko_common.par/texlist_0001/taiko_common_02': [([39, 79, 76, 212], 'Fácil'), ([235, 77, 281, 218], 'Difícil')],
    'ui_en/surfboard/pjd_mg_taiko_common.par/texlist_0001/taiko_music_select_02': [([40, 80, 76, 211], 'Fácil'), ([237, 80, 280, 218], 'Difícil')],
    'ui_en/surfboard/pjd_mg_taiko_select.par/texlist_0001/taiko_music_select_02': [([40, 80, 76, 211], 'Fácil'), ([237, 80, 280, 218], 'Difícil')],
    'ui_en/surfboard/pjd_mg_taiko_select.par/texlist_0001/taiko_music_select_01': [([310, 152, 343, 262], 'Fácil'), ([326, 745, 359, 842], 'Difícil')],
}


def taiko_vertical():
    """Fácil/Difícil en las tiras verticales de los tambores (letras negras apiladas sobre papel blanco)"""
    from PIL import ImageDraw, ImageFont
    f = 'C:/Windows/Fonts/segoeuib.ttf'
    for r, cajas in TAIKO_V.items():
        p = os.path.join(PV.SAL, r + '.dds')
        base = Image.open(p if r.replace('/', '__') in CAMBIOS else os.path.join(PV.T, 'imagenes', 'es', r + '.dds')).convert('RGBA')
        o = Image.open(PV.origen(r + '.dds')).convert('RGBA'); a = np.array(base)
        import cv2
        fb = 'C:/Windows/Fonts/arialbd.ttf'   # (25-10) letra del tamaño de «Normal» (antes se encogía para caber en la caja inglesa):
        cajas = [((x0, y0, x1, max(y1, y0 + int(round((x1 - x0) * 0.78) * 1.02 * len(t)) + 6)), t) for (x0, y0, x1, y1), t in cajas]   # se alarga sobre los puntos
        for (x0, y0, x1, y1), t in cajas:   # quita las letras inglesas: todo lo que se aparta del color del papel, con relleno
            z = a[y0:y1, x0:x1, :3].astype(int); papel = np.median(z.reshape(-1, 3), 0)
            m = np.zeros(a.shape[:2], np.uint8); m[y0:y1, x0:x1] = (np.abs(z - papel).max(2) > 35)
            m = cv2.dilate(m * 255, np.ones((3, 3), np.uint8), iterations=1)
            a[..., :3] = cv2.inpaint(np.ascontiguousarray(a[..., :3]), m, 3, cv2.INPAINT_TELEA)
        img = Image.fromarray(a); d = ImageDraw.Draw(img)
        for (x0, y0, x1, y1), t in cajas:
            n = len(t); tam = int(round((x1 - x0) * 0.78)); paso = tam * 1.02
            fo = ImageFont.truetype(fb, tam)
            for k, ch in enumerate(t):
                d.text(((x0 + x1) / 2, y0 + paso * (k + 0.5)), ch, font=fo, fill=(15, 15, 15, 255), anchor='mm', stroke_width=1, stroke_fill=(15, 15, 15, 255))
        atlas_es.TEX = os.path.join(PV.T, 'extraido_r'); atlas_es.SAL = PV.SAL; atlas_es.guardar_dds(r, img)
        W, H = o.size; v = Image.new('RGBA', (W * 2 + 12, H), (40, 40, 44, 255)); v.alpha_composite(o); v.alpha_composite(img, (W + 12, 0))
        v.convert('RGB').save(os.path.join(PV.REV, 'F_taikoV_' + r.split('/')[-1] + '_' + r.split('/')[2][4:12] + '.png'))


def puri_text_pausa():
    """pausepar puri_text (sin especificación del kit): misma frase que la de la nota de purikura, centrada"""
    from PIL import ImageDraw, ImageFont
    r = 'pausepar_pause_en/picture/puri_text'
    o = Image.open(PV.origen(r + '.dds')).convert('RGBA'); a = np.array(o)
    a[2:31, 100:440] = np.median(a[2:31, 20:90].reshape(-1, 4), 0).astype(np.uint8)
    img = Image.fromarray(a); d = ImageDraw.Draw(img); t = 'Elige la foto que quieres cambiar'
    tam = 24
    while ImageFont.truetype('C:/Windows/Fonts/times.ttf', tam).getlength(t) > 330: tam -= 1
    d.text((256, 16), t, font=ImageFont.truetype('C:/Windows/Fonts/times.ttf', tam), fill=(240, 240, 240, 255), anchor='mm')
    atlas_es.TEX = os.path.join(PV.T, 'extraido'); atlas_es.SAL = PV.SAL; atlas_es.guardar_dds(r, img)
    W, H = o.size; v = Image.new('RGBA', (W * 2 + 12, H), (40, 40, 44, 255)); v.alpha_composite(o); v.alpha_composite(img, (W + 12, 0))
    v.convert('RGB').save(os.path.join(PV.REV, 'F_puri_text_pausa.png'))


def main(filtro=()):
    atlas_es.SAL = PV.SAL
    for i in CAMBIOS:
        if filtro and not any(f in i for f in filtro): continue
        s = spec_de(i)
        o, nv, items = atlas_probar.dibujar(s)
        if i.endswith('2d_jm_taxi_result'): nv = rayado(o, nv)
        if i.endswith('2d_jm_yuki_mission'): nv = mision(o, nv)
        if i.endswith('2d_jm_title_vs_billiards'): nv = billar(o)
        if i.endswith('2d_jm_mg_yukigassen_pt'): nv = golpe(o, nv)
        atlas_es.guardar_dds(s['textura'], nv)
        W, H = o.size
        v = Image.new('RGBA', (W * 2 + 12, H), (40, 40, 44, 255)); v.alpha_composite(o.convert('RGBA')); v.alpha_composite(nv.convert('RGBA'), (W + 12, 0))
        v.convert('RGB').save(os.path.join(PV.REV, 'F_' + i.split('__')[-1] + '.png'))
        print('ok', i, flush=True)


def hanafuda02():
    """«◆Scoring Combinations◆» -> «◆Combinaciones de puntos◆» (el kit lo calibraba diminuto): fondo transparente, letra
    Times blanca como el original, mismo alto"""
    from PIL import ImageDraw, ImageFont
    r = 'ui_en/surfboard/pjd_mg_hanafuda01.par/texlist/2d_jm_mg_hanafuda02'
    o = Image.open(PV.origen(r + '.dds')).convert('RGBA'); a = np.array(o)
    a[66:114, 204:512] = 0
    img = Image.fromarray(a); d = ImageDraw.Draw(img); t = '◆Combinaciones de puntos◆'
    tam = 34
    while ImageFont.truetype('C:/Windows/Fonts/times.ttf', tam).getlength(t) > 300: tam -= 1
    x = 206
    for ch in ['◆', 'Combinaciones de puntos', '◆']:
        f = ImageFont.truetype('C:/Windows/Fonts/' + ('seguisym.ttf' if ch == '◆' else 'times.ttf'), tam if ch != '◆' else tam - 8)
        d.text((x, 90), ch, font=f, fill=(255, 255, 255, 255), anchor='lm'); x += f.getlength(ch)
    atlas_es.TEX = os.path.join(PV.T, 'extraido_r'); atlas_es.SAL = PV.SAL; atlas_es.guardar_dds(r, img)
    W, H = o.size; v = Image.new('RGBA', (W * 2 + 12, H), (40, 40, 44, 255)); v.alpha_composite(o); v.alpha_composite(img, (W + 12, 0))
    v.convert('RGB').save(os.path.join(PV.REV, 'F_2d_jm_mg_hanafuda02.png'))


if __name__ == '__main__':
    main(sys.argv[1:]); hanafuda02(); puri_text_pausa(); taiko_vertical()

