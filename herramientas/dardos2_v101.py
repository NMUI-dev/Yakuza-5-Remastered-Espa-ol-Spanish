# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) v1.0.1: TODAS las páginas de reglas de dardos con marcador (rule_darts_*) rehechas desde el
ORIGINAL con un estilo único (la v1.0 y los arreglos sueltos mezclaban letras, tamaños y dejaban restos):
  título   (píldora de color arriba): cada fila de la píldora se rellena con su propio color y se escribe el título
           en Segoe UI Semibold blanco, centrado y del mismo alto en todas las páginas
  bocadillo/leyenda (recuadros blancos): cada fila se rellena con su blanco y se escribe en gris oscuro, centrado
  cabecera «...» y párrafo del panel de abajo: se borran (inpaint) y se escriben centrados, mismo tamaño en todas las
           páginas, con el color de su tinta original (blanco, cian, rojo)
Lo que es del marcador (SINGLE 18, DOUBLE, BULL, nombres, números, DARTSLIVE) se queda como en el original.
  python herramientas/dardos2_v101.py [filtro]
"""
import os, sys, re, statistics
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_es
import paginas_v101 as PV
import paginas_es as P
SB, SR = 'C:/Windows/Fonts/seguisb.ttf', 'C:/Windows/Fonts/segoeui.ttf'
PIC = 'pausepar_pause_en/picture/'
TITULOS = {'01gamerule': 'REGLAS DEL JUEGO 01', 'countuprule': 'REGLAS DE COUNT-UP', 'cricketgamerule': 'REGLAS DEL CRICKET'}
CABECERAS = {'howtowin': '«Cómo ganar»', 'gameoverview': '«Resumen del juego»', 'countup': '«Count-Up»', 'note': '«Nota»',
             '01game': '«Juego 01»', 'standardcricket': '«Cricket estándar»', 'randomcricket': '«Cricket aleatorio»',
             'hiddencricket': '«Cricket oculto»'}
BOCADILLOS = {'youwinatzeropoints': 'Ganas al llegar a cero puntos.', 'thehigherscorewins': 'Gana la puntuación más alta.',
              '1hit': '1 acierto', '2hits': '2 aciertos', '3hits': '3 aciertos', 'closed': 'Cerrado', 'open': 'Abierto',
              '1hitopenbonus': '1 acierto + bono', 'bust': None}
PARRAFOS = {
    'trytoreduceyourscoretoexactlyzero': 'Intenta reducir tu puntuación exactamente a cero.',
    'bethefirsttoreduceyourscoretoexactlyzero': 'Sé el primero en reducir tu puntuación exactamente a cero.',
    'goingbelowzeroisknownasgoingbust': 'Quedar por debajo de cero se llama «pasarse».',
    'thegameusesthenumbers15to20andthebullseye': 'Se juega con los números del 15 al 20 y la diana.',
    'thegameusesthebullseyeisixrandomlyselectednumbers': 'Se juega con la diana y {seis números elegidos al azar}.',
    'thegameusesthebullseyeandisixrandomlyselectednumbers': 'Se juega con la diana y {seis números elegidos al azar}.',
    'thisgameusessevenhiddennumbers': 'Se juega con {siete números ocultos}.',
    'befirsttoreduceyourscoretoexactlyzero': 'Sé el primero en reducir tu puntuación exactamente a cero.',
    'yourscoreisresettoitsstartingvalueandplaycontinueswiththenextplayer': 'Tu puntuación vuelve a su valor inicial y la partida sigue con el siguiente jugador.',
    'startingfromzeropointscompeteforthehighestpointtotalinapredeterminednumberofrounds': 'Empezando desde cero, compite por la puntuación total más alta en un número fijo de rondas.',
    'playerwiththehighestscorewins': 'Gana el jugador con la puntuación más alta.',
    'standardplayerwiththehighestscorewins': 'ESTÁNDAR: gana el jugador con la puntuación más alta.',
    'playerstrytohitnumbersthreetimestoclosethemascoreboardisusedtoshowthenumberofhitsforeachnumber': 'Los jugadores intentan acertar tres veces cada número para cerrarlo. Un marcador muestra los aciertos de cada número.',
    'hitsonaclosednumberscorepointsanumbernolongeryieldspointsifallplayershaveclosedit': 'Los aciertos en un número cerrado suman puntos. Un número deja de sumar si todos los jugadores lo han cerrado.',
    'hittinganumberthreetimeswillcloseithittingahiddennumberforthefirsttimewillearnyouabonus': 'Acertar tres veces un número lo cierra. Acertar por primera vez un número oculto da un bono.',
    'hittingaclosednumberscorespointsanumbernolongeryieldspointsifbothplayershaveclosedit': 'Acertar un número cerrado suma puntos. Un número deja de sumar si los dos jugadores lo han cerrado.',
}


def n(s): return re.sub(r'[^a-z0-9]', '', s.lower())


def rellenar_filas(a, caja, pred):
    """cada fila de la caja: los píxeles que no cumplen pred (fondo) toman la mediana de los que sí"""
    x0, y0, x1, y1 = caja
    for y in range(max(0, y0), min(a.shape[0], y1)):
        f = a[y, x0:x1, :3]; ok = pred(f)
        if ok.sum() > 3:   # solo entre el primer y el último píxel de fondo de la fila (si no, la píldora redonda sale rectángulo)
            xs = np.where(ok)[0]; den = np.zeros_like(ok); den[xs[0]:xs[-1] + 1] = True
            f[den & ~ok] = np.median(f[ok], 0).astype(np.uint8)


def ancho_fondo(a, l, pred):
    """extiende la caja del OCR a todo el recuadro de fondo (blanco/píldora) en esa fila"""
    ym = (l[1] + l[3]) // 2; x0, x1 = l[0], l[2]; W = a.shape[1]
    while x0 > 1 and pred(a[ym:ym + 1, x0 - 1:x0, :3])[0, 0]: x0 -= 1
    while x1 < W - 1 and pred(a[ym:ym + 1, x1:x1 + 1, :3])[0, 0]: x1 += 1
    return [x0, l[1], x1, l[3]]


def centrar(d, cx, cy, t, ruta, tam, ancho, col):
    while tam > 8 and ImageFont.truetype(ruta, tam).getlength(t) > ancho: tam -= 1
    d.text((cx, cy), t, font=ImageFont.truetype(ruta, tam), fill=col, anchor='mm')


def rehacer(ruta):
    a = np.array(Image.open(PV.origen(ruta)).convert('RGBA')); o = a.copy(); H, W = a.shape[:2]
    ls = sorted(PV.ocr2x(ruta), key=lambda l: l[1])
    blanco = lambda f: f.min(-1) > 175
    dib = []
    # título: primer renglón con texto de título
    for l in ls:
        k = n(l[4]); t = next((v for kk, v in TITULOS.items() if kk in k), None)
        if t and l[1] < 0.15 * H:
            col_p = o[(l[1] + l[3]) // 2, l[0] - 4, :3].astype(int)
            pild = lambda f, c=col_p: np.abs(f.astype(int) - c).max(-1) < 60
            caja = [l[0] - 70, l[1] - 4, l[2] + 70, l[3] + 4]   # (la fila solo se rellena dentro de la píldora)
            rellenar_filas(a, caja, pild)
            for y in range(caja[1], caja[3]):   # el contorno del título inglés se parece al color de la píldora y quedaba como
                f = a[y, :, :3]; ok = pild(o[y, :, :3]); xs = np.where(ok[max(0, l[0] - 140):min(W, l[2] + 140)])[0] + max(0, l[0] - 140)   # fantasma: la franja
                if len(xs) > 3:                                                                        # del texto se pinta entera
                    f[max(xs[0] + 14, l[0] - 40):min(xs[-1] - 14, l[2] + 40)] = np.median(o[y, xs, :3], 0).astype(np.uint8)
                z = f[max(0, l[0] - 20):l[2] + 8]; br = z.min(-1) > 150   # lo blanco que queda de las letras (la barra
                if br.any() and (~br).sum() > 10: z[br] = np.median(z[~br], 0).astype(np.uint8)   # de la «E» de RULE)
            dib.append(('titulo', caja, t, (255, 255, 255, 255))); break
    # bocadillos (recuadros blancos)
    usados = set()
    for i, l in enumerate(ls):
        k = n(l[4])
        if k in BOCADILLOS and BOCADILLOS[k] and blanco(o[(l[1] + l[3]) // 2:(l[1] + l[3]) // 2 + 1, max(0, l[0] - 3):l[0] - 1, :3]).all():
            caja = ancho_fondo(o, l, blanco); caja = [caja[0] + 2, l[1] - 2, caja[2] - 2, l[3] + 2]
            e = 30 if k == '1hitopenbonus' else 4; rellenar_filas(a, [caja[0] - e, caja[1] - 2, caja[2] + e, caja[3] + 2], blanco)
            for y in range(caja[1] - 2, caja[3] + 2):   # el recuadro va en degradado: cada fila se repinta con su recta de color
                e2 = e if e > 4 else 0; xs = np.arange(caja[0] - e2, caja[2] + e2); xs = xs[(xs >= 0) & (xs < W)]; f = o[y, xs, :3].astype(float)
                ok = f.min(1) > 150
                if ok.sum() > 20:
                    xi = xs[ok]; xi0, xi1 = xi.min(), xi.max(); dd = (xs >= xi0) & (xs <= xi1)
                    for ch in range(3):
                        m, b0 = np.polyfit(xi, f[ok, ch], 1); a[y, xs[dd], ch] = np.clip(m * xs[dd] + b0, 0, 255).astype(np.uint8)   # (+12: restos; más pisaba el nombre de al lado)
            dib.append(('bocadillo', caja, BOCADILLOS[k], (50, 50, 55, 255))); usados.add(i)
    # «2» + «Hits» partidos por el OCR
    for i, l in enumerate(ls):
        if i in usados or n(l[4]) not in ('2', '3'): continue
        if not blanco(o[(l[1] + l[3]) // 2:(l[1] + l[3]) // 2 + 1, max(0, l[0] - 3):l[0] - 1, :3]).all(): continue
        h = [j for j, m in enumerate(ls) if j not in usados and n(m[4]) == 'hits' and abs(m[1] - l[1]) < 8 and -6 < m[0] - l[2] < 30]
        if h:
            m = ls[h[0]]; ll = [l[0], min(l[1], m[1]), m[2], max(l[3], m[3])]
            caja = ancho_fondo(o, ll, blanco); caja = [caja[0] + 2, ll[1] - 2, caja[2] - 2, ll[3] + 2]
            rellenar_filas(a, caja, blanco); dib.append(('bocadillo', caja, BOCADILLOS[n(l[4]) + 'hits'], (50, 50, 55, 255)))
            usados |= {i, h[0]}
    # panel de abajo: cabecera «...» y su párrafo
    cab = next((l for l in ls if l[4].strip()[:1] in '《«' and l[1] > 0.6 * H), None)
    if cab:
        resto = [l for l in ls if l[1] > cab[3] - 2 and l[0] > 0.07 * W and l[2] < 0.93 * W and not (len(n(l[4])) <= 10 and re.search(r'dar|live|ve2|daf|art', n(l[4])))]
        resto.sort(key=lambda l: (round(l[1] / 10), l[0])); k = n(' '.join(x[4] for x in resto)); par = PARRAFOS.get(k)
        if par is None and not k: par = ''
        if par is None: raise SystemExit(f'{ruta}: párrafo sin traducción: {k}')
        ccab = CABECERAS[n(cab[4])]
        m, _ = P.mascara_tinta(o, resto[0][:4]); colp = P.color_tinta(o, m)
        a = P.borrar(a, [[cab[0] - 4, cab[1], cab[2] + 4, cab[3]]] + [[x[0] - 4, x[1], x[2] + 4, x[3]] for x in resto])
        dib.append(('cabecera', cab, ccab, (255, 255, 255, 255))); hcab = cab[3] - cab[1]
        rojo = P.color_tinta(o, P.mascara_tinta(o, resto[-1][:4])[0]) if '{' in par else None
        dib.append(('parrafo', resto, par, colp + (255,)))
    img = Image.fromarray(a); d = ImageDraw.Draw(img)
    for tipo, c, t, col in dib:
        if tipo == 'titulo': centrar(d, (c[0] + c[2]) / 2, (c[1] + c[3]) / 2 + 1, t, SB, 30, c[2] - c[0] - 20, col)
        elif tipo == 'bocadillo': centrar(d, (c[0] + c[2]) / 2, (c[1] + c[3]) / 2, t, SR, round((c[3] - c[1]) * 0.78), c[2] - c[0] - 6, col)
        elif tipo == 'cabecera': centrar(d, W / 2, (c[1] + c[3]) / 2, t, SR, 30, 0.8 * W, col)   # mismo tamaño en todas
        else:   # mismo alto de letra que el original (antes salía a ~70 %); {...} va en el rojo del original
            hp = statistics.median(x[3] - x[1] for x in c); plano = t.replace('{', '').replace('}', '')
            for tam in range(27, 11, -1):   # (25-10) del tamaño del original (claude1: salía pequeño)
                f = ImageFont.truetype(SR, tam); rs = P.partir(plano, f, 0.88 * W)
                if len(rs) <= 2: break
            if len(rs) == 2:   # partir por la mitad (sin renglón huérfano), como el original
                pal = plano.split(); mejor = min(range(1, len(pal)), key=lambda i: max(f.getlength(' '.join(pal[:i])), f.getlength(' '.join(pal[i:]))))
                rs = [' '.join(pal[:mejor]), ' '.join(pal[mejor:])]
            rojos = set(); k = 0; dentro = False
            for ch in t:
                if ch == '{': dentro = True; continue
                if ch == '}': dentro = False; continue
                if dentro: rojos.add(k)
                k += 1
            paso = tam * 1.3; yc = (c[0][1] + max(x[3] for x in c)) / 2 - (len(rs) - 1) * paso / 2; k = 0
            for j, x in enumerate(rs):
                k = plano.index(x, k); xx = W / 2 - f.getlength(x) / 2
                for q, ch in enumerate(x):
                    d.text((xx, yc + j * paso), ch, font=f, fill=(rojo + (255,)) if (k + q) in rojos and rojo else col, anchor='lm')
                    xx += f.getlength(x[:q + 1]) - f.getlength(x[:q])
                k += len(x)
    atlas_es.TEX = os.path.join(PV.T, 'extraido'); atlas_es.SAL = PV.SAL; atlas_es.guardar_dds(ruta[:-4], img)
    v = Image.new('RGBA', (W * 2 + 12, H), (40, 40, 44, 255)); v.alpha_composite(Image.fromarray(o)); v.alpha_composite(img, (W + 12, 0))
    v.convert('RGB').save(os.path.join(PV.REV, 'D_' + ruta.split('/')[-1][:-4] + '.png'))


if __name__ == '__main__':
    fs = sorted(f for f in os.listdir(os.path.join(PV.T, 'extraido', 'pausepar_pause_en', 'picture')) if f.startswith('rule_darts_'))
    for f in fs:
        if len(sys.argv) > 1 and not any(x in f for x in sys.argv[1:]): continue
        rehacer(PIC + f); print('ok', f, flush=True)
