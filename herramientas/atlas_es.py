# -*- coding: utf-8 -*-
"""(Claude Code, 20-10-2026, copiado del de Yakuza 6) Traduce texto dentro de los atlas de imagen de Yakuza 5 (menú principal, pausa, etc.).
Cada palabra/frase inglesa ocupa una caja del atlas; el juego recorta esa zona. Para no salirse nunca, el español se
dibuja DENTRO de la misma caja: mismo alto (calibrado con el inglés original en la misma fuente) y, si es más largo,
se estrecha en horizontal (hasta 62 %) y después se achica. Copia el color y el brillo (halo) del original.
Especificación: trabajo/imagenes/atlas_es.json (nombre = ruta de la textura dentro de trabajo/extraido_r, sin .dds)
  {"nombre_textura": {"fuente": "georgiaz.ttf", "items": [{"caja": [x0,y0,x1,y1], "en": "Stats", "es": "Atributos",
                       "alin": "izq|centro|der" (opcional), "efecto": "auto|brillo|nada" (opcional)}]}}
  python herramientas/atlas_es.py [nombre ...]   -> trabajo/imagenes_ui/es/<nombre>.dds (+ .png para revisar)
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(R, 'trabajo', 'extraido_r')
SAL = os.path.join(R, 'trabajo', 'imagenes', 'es')
FUENTES = ['C:/mods/yakuza6/herramientas/fuentes_img', 'C:/Windows/Fonts']


def fuente(nombre, tam):
    for d in FUENTES:
        p = os.path.join(d, nombre)
        if os.path.exists(p): return ImageFont.truetype(p, tam)
    raise FileNotFoundError(nombre)


def tinta(f, t):
    """caja de tinta (anchor ls: arriba negativo) de un texto."""
    return f.getbbox(t, anchor='ls')


def calibrar(nf, en, alto_obj):
    """tamaño de letra con el que el inglés 'en' mide alto_obj px de tinta en la fuente nf."""
    tam = 40
    for _ in range(6):
        f = fuente(nf, tam); bb = tinta(f, en); h = bb[3] - bb[1]
        tam = min(300, max(6, int(round(tam * alto_obj / max(1, h)))))   # (21-10) tope: un tamaño disparado tumbaba FreeType
    return tam


def mascara(nf, t, tam, en, ancho_max):
    """Máscara L del texto t con la fuente nf al tamaño tam (se estrecha/achica si no cabe en ancho_max)."""
    f = fuente(nf, tam)
    bb_en = tinta(f, en); bb = tinta(f, t)
    img = Image.new('L', (bb[2] - bb[0] + 8, max(bb[3], bb_en[3]) - min(bb[1], bb_en[1]) + 8), 0)
    arriba = min(bb[1], bb_en[1])
    ImageDraw.Draw(img).text((4 - bb[0], 4 - arriba), t, font=f, fill=255, anchor='ls')
    base = 4 - arriba                                   # fila de la línea base dentro de img
    sup_en = base + bb_en[1]                             # fila donde empieza la tinta del inglés
    ancho = bb[2] - bb[0]
    if ancho > ancho_max:
        k = ancho_max / ancho
        if k >= 0.62: img = img.resize((max(1, int(img.width * k)), img.height), Image.LANCZOS)
        else:
            img = img.resize((max(1, int(img.width * 0.62)), img.height), Image.LANCZOS)
            k2 = ancho_max / max(1, ancho * 0.62)
            img = img.resize((max(1, int(img.width * k2)), max(1, int(img.height * k2))), Image.LANCZOS)
            base = int(base * k2); sup_en = int(sup_en * k2)
    return img, sup_en


def medir_estilo(zona):
    """(21-10) Estilo del rótulo original (rótulos de minijuegos con degradado y contorno): color de relleno arriba y
    abajo, contorno (color y grosor en px) y brillo exterior. zona = RGBA de la casilla original."""
    import cv2
    op = (zona[..., 3] > 200).astype(np.uint8); rgb = zona[..., :3].astype(np.int16)
    if op.sum() < 15: return {'arriba': [255, 255, 255], 'abajo': [255, 255, 255], 'contorno': None, 'brillo': None}
    def med(m): return np.median(rgb[m.astype(bool)], 0) if m.sum() > 5 else None
    capas = [op]
    for k in range(1, 6): capas.append(cv2.erode(op, np.ones((3, 3), np.uint8), iterations=k))
    borde = med(capas[0] - capas[1]); nucleo = None; w = 0
    for k in range(5, 0, -1):
        if capas[k].sum() > 20: nucleo_m = capas[k]; break
    else: nucleo_m = op
    nucleo = med(nucleo_m)
    if borde is not None and nucleo is not None and np.abs(borde - nucleo).sum() > 120:
        for k in range(1, 5):                  # grosor: anillos que siguen pareciéndose al borde
            anillo = med(capas[k - 1] - capas[k])
            if anillo is None or np.abs(anillo - borde).sum() > np.abs(anillo - nucleo).sum(): break
            w = k
    interior = capas[w] if w else op
    f = np.where(interior.any(1))[0]
    if len(f) >= 3:
        t = len(f) // 3; arr = np.zeros_like(interior); arr[f[0]:f[0] + max(1, t)] = 1; aba = np.zeros_like(interior); aba[f[-1] - max(1, t) + 1:f[-1] + 1] = 1
        c_arr, c_aba = med(interior & arr), med(interior & aba)
    else: c_arr = c_aba = None
    c_arr = nucleo if c_arr is None else c_arr; c_aba = nucleo if c_aba is None else c_aba
    # brillo exterior: tinta suave LEJOS de la letra (el suavizado del borde no cuenta)
    lejos = (zona[..., 3] > 15) & (cv2.dilate(op, np.ones((3, 3), np.uint8), iterations=2) == 0)
    brillo = med(lejos) if lejos.sum() > 0.6 * op.sum() else None
    lista = lambda v: None if v is None else [int(x) for x in v]
    return {'arriba': lista(c_arr), 'abajo': lista(c_aba), 'contorno': [lista(borde), int(w)] if w else None, 'brillo': lista(brillo)}


def componer_estilo(nuevo, capa, est, alto):
    """Dibuja el rótulo (máscara capa) con el estilo medido: brillo, contorno y relleno en degradado vertical."""
    import cv2
    m = np.asarray(capa); filas = np.where(m.max(1) > 60)[0]
    if not len(filas): return nuevo
    H, W = m.shape
    if est.get('brillo'):
        g = cv2.GaussianBlur(cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=2), (0, 0), max(2, alto / 8))
        g = np.clip(g.astype(np.float32) * 1.6, 0, 255).astype(np.uint8)
        im = Image.new('RGBA', (W, H), tuple(est['brillo']) + (0,)); im.putalpha(Image.fromarray(g)); nuevo.alpha_composite(im)
    if est.get('contorno'):
        col, w = est['contorno']
        d = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * w + 1, 2 * w + 1)))
        im = Image.new('RGBA', (W, H), tuple(col) + (0,)); im.putalpha(Image.fromarray(d)); nuevo.alpha_composite(im)
    y0, y1 = filas[0], filas[-1] + 1; t = np.zeros((H, 1), np.float32); t[y0:y1, 0] = np.linspace(0, 1, y1 - y0)
    t[y1:] = 1
    a, b = np.array(est['arriba'], np.float32), np.array(est['abajo'], np.float32)
    rgb = (a[None, None] * (1 - t[..., None]) + b[None, None] * t[..., None]).repeat(W, 1).clip(0, 255).astype(np.uint8)
    rgba = np.dstack([rgb, m]); nuevo.alpha_composite(Image.fromarray(rgba, 'RGBA'))
    return nuevo


_LAMA = None
def borrar_lama(arr, caja, umbral=90, dila=2):
    """Casilla con fondo OPACO (botón, cartel): en vez de vaciar el alfa, LaMa borra solo la tinta del texto (píxeles
    lejos del color del borde de la casilla) rellenando el fondo. Devuelve el array cambiado."""
    global _LAMA
    import cv2
    if _LAMA is None:
        from simple_lama_inpainting import SimpleLama
        _LAMA = SimpleLama()
    x0, y0, x1, y1 = caja; z = arr[y0:y1, x0:x1, :3].astype(np.int16)
    borde = np.concatenate([z[0], z[-1], z[:, 0], z[:, -1]]); fondo = np.median(borde, 0)
    m = (np.abs(z - fondo).sum(2) > umbral).astype(np.uint8); m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=dila)
    p = 8; X0, Y0, X1, Y1 = max(0, x0 - p), max(0, y0 - p), min(arr.shape[1], x1 + p), min(arr.shape[0], y1 + p)
    full = np.zeros(arr.shape[:2], np.uint8); full[y0:y1, x0:x1] = m
    trozo = Image.fromarray(arr[Y0:Y1, X0:X1, :3].astype(np.uint8))
    lleno = np.asarray(_LAMA(trozo, Image.fromarray(full[Y0:Y1, X0:X1] * 255)).resize(trozo.size))
    out = arr.copy(); out[y0:y1, x0:x1, :3] = lleno[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0]
    return out


def zona_texto(a, it):
    """RGBA de la casilla; en casillas opacas (fondo «lama») el alfa se sustituye por la máscara del texto (píxeles
    lejos del color del borde), para medir alto, color y estilo del rótulo y no del fondo."""
    x0, y0, x1, y1 = it['caja']; z = a[y0:y1, x0:x1].copy()
    if it.get('fondo') in ('lama', 'fila'):
        c = z[..., :3].astype(np.int16); borde = np.concatenate([c[0], c[-1], c[:, 0], c[:, -1]])
        z[..., 3] = np.where(np.abs(c - np.median(borde, 0)).sum(2) > 90, 255, 0)
    return z


def traducir(nombre, spec):
    orig = Image.open(os.path.join(TEX, nombre + '.dds')).convert('RGBA')
    a = np.asarray(orig).copy()
    nuevo = Image.fromarray(a)
    tams = []
    for it in spec['items']:
        x0, y0, x1, y1 = it['caja']; op = zona_texto(a, it)[..., 3] > 200; filas = np.where(op.any(1))[0]
        alto = int(filas[-1] - filas[0] + 1) if len(filas) else (y1 - y0)
        tams.append(calibrar(it.get('fuente', spec['fuente']), it['en'], it.get('alto', alto)))
    for i, it in enumerate(spec['items']):
        grupo = [tams[j] for j, o in enumerate(spec['items']) if o.get('fuente', spec['fuente']) == it.get('fuente', spec['fuente'])
                 and (spec.get('mediana') == 'todos' or abs(o['caja'][0] - it['caja'][0]) < 40)]   # (21-10) «todos»: misma letra, cualquier x
        it['_tam'] = int(np.median(grupo)) if it.get('mediana', spec.get('mediana', True)) else tams[i]
        if it.get('tam', spec.get('tam')): it['_tam'] = int(it.get('tam', spec.get('tam')))   # (21-10) cuerpo FIJO: serie uniforme (no depende de colas del inglés)
    for it in spec['items']:
        x0, y0, x1, y1 = it['caja']
        zona = zona_texto(a, it)
        op = zona[..., 3] > 200
        color = tuple(int(v) for v in np.median(zona[..., :3][op], axis=0)) if op.sum() > 10 else (255, 255, 255)
        medio = ((zona[..., 3] > 15) & (zona[..., 3] <= 200)).sum()
        efecto = it.get('efecto', 'auto')
        if efecto == 'auto': efecto = 'brillo' if medio > 1.2 * max(1, op.sum()) else 'nada'
        # alto de tinta del original: filas con alfa alto
        filas = np.where(op.any(1))[0]
        alto = it.get('alto') or (int(filas[-1] - filas[0] + 1) if len(filas) else (y1 - y0))
        if it.get('alto'): filas = np.array([(y1 - y0 - alto) // 2])
        top = y0 + (filas[0] if len(filas) else 0)
        cols = np.where(op.any(0))[0]
        ix0 = x0 + (cols[0] if len(cols) else 0); ix1 = x0 + (cols[-1] + 1 if len(cols) else x1 - x0)
        m = it.get('margen', spec.get('margen', 3 if efecto == 'nada' else 6))
        nuevo_a = np.asarray(nuevo).copy()
        if it.get('fondo') == 'lama': nuevo_a = borrar_lama(nuevo_a, it['caja'], it.get('lama_umbral', 60), it.get('lama_dila', 3))   # (21-10) botones opacos
        elif it.get('fondo') == 'fila':   # (21-10) bocadillos con degradado VERTICAL: se mezcla el color de fondo de encima y de debajo
            H_, W_ = nuevo_a.shape[:2]; ya, yb = max(0, y0 - m), min(H_, y1 + m)
            def fondo_en(yy, paso):
                for _ in range(12):
                    if not 0 <= yy < H_: break
                    f = nuevo_a[yy, x0:x1]; f = f[(f[:, 3] > 250) & (f[:, :3].max(1) > 150) & (f[:, :3].min(1) < 245)]   # solo el color claro del bocadillo (no contornos)
                    if len(f) > (x1 - x0) // 3: return np.median(f, 0)
                    yy += paso
                return None
            ca, cb = fondo_en(ya - 1, -1), fondo_en(yb, 1)
            if ca is None: ca = cb
            if cb is None: cb = ca
            if ca is not None:   # solo se pinta donde había LETRA (blanco o contorno oscuro): el borde del bocadillo queda intacto
                xa_, xb_ = max(0, x0 - m), min(W_, x1 + m); z = nuevo_a[ya:yb, xa_:xb_].astype(int)
                letra = ((z[..., :3].min(2) > 185) | (z[..., :3].max(2) < 110)) & (z[..., 3] > 30)
                fuera = (z[..., 3] < 250)          # transparente = fuera del bocadillo
                import cv2 as _cv
                letra = _cv.dilate(letra.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=it.get('fila_dila', 4)).astype(bool) & ~fuera
                for j, yy in enumerate(range(ya, yb)):
                    k = j / max(1, yb - ya - 1); fila = nuevo_a[yy, xa_:xb_]
                    fila[letra[j]] = np.append((ca[:3] * (1 - k) + cb[:3] * k), 255).astype(np.uint8)
        else: nuevo_a[max(0, y0 - m):y1 + m, max(0, x0 - m):x1 + m] = 0
        nuevo = Image.fromarray(nuevo_a)
        am = it.get('ancho_max', spec.get('ancho_max', ix1 - ix0))
        if efecto in ('brillo', 'estilo', 'borroso') and m: am = min(am, (x1 - x0) - 2 * m)   # (21-10) que el halo quepa sin cortar
        img, sup = mascara(it.get('fuente', spec['fuente']), it['es'], it['_tam'], it['en'], am)
        alin = it.get('alin') or spec.get('alin') or ('izq' if x0 < 12 else 'centro')
        if alin == 'izq': px = x0 + it.get('sangria', 4) if spec.get('ceñido') else ix0
        elif alin == 'der': px = ix1 - img.width
        else: px = int(round((ix0 + ix1) / 2 - img.width / 2))
        py = top - sup
        # (21-10, aviso de claude1/fable3) tildes de MAYÚSCULAS (Á É) cortadas arriba: si la tinta empieza antes de la
        # casilla, se baja; si así se sale por abajo, se achica lo justo para que quepa entera
        filas_m = np.where(np.asarray(img).max(1) > 40)[0]
        if len(filas_m) and py + filas_m[0] < y0:
            py = y0 - filas_m[0]
            if py + filas_m[-1] >= y1:
                k = (y1 - y0 - 1) / max(1, filas_m[-1] - filas_m[0] + 1)
                img = img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))), Image.LANCZOS)
                filas_m = np.where(np.asarray(img).max(1) > 40)[0]; py = y0 - (filas_m[0] if len(filas_m) else 0)
                if alin == 'der': px = ix1 - img.width
                elif alin != 'izq': px = int(round((ix0 + ix1) / 2 - img.width / 2))
        capa = Image.new('L', orig.size, 0); capa.paste(img, (px - 4 if alin == 'izq' else px, py))
        if efecto == 'brillo':
            halo = capa.filter(ImageFilter.GaussianBlur(float(max(2, alto / 9))))
            halo = Image.fromarray(np.clip(np.asarray(halo, np.float32) * 1.7, 0, 255).astype(np.uint8))
            capa = Image.fromarray(np.maximum(np.asarray(capa), np.asarray(halo)))
        if efecto == 'borroso':                         # versión desenfocada del mismo rótulo (para el brillo del juego)
            capa = capa.filter(ImageFilter.GaussianBlur(float(it.get('radio', max(2, alto / 10)))))
            capa = Image.fromarray(np.clip(np.asarray(capa, np.float32) * 1.25, 0, 255).astype(np.uint8))
        # que nada (halo incluido) se salga de la franja de su fila: si no, aparece en el recorte de la fila vecina
        recorte = np.zeros((orig.size[1], orig.size[0]), np.uint8); recorte[max(0, y0 - 2):y1 + 2, :] = 1
        if spec.get('ceñido'): recorte[:] = 0; recorte[y0:y1, x0:x1] = 1   # atlas sin huecos: nada fuera del rectángulo
        capa = Image.fromarray(np.asarray(capa) * recorte)
        if efecto == 'estilo':                         # (21-10) degradado + contorno + brillo medidos del original
            nuevo = componer_estilo(nuevo, capa, it.get('estilo') or medir_estilo(zona), alto); continue
        if it.get('color'): color = tuple(it['color'])
        color_img = Image.new('RGBA', orig.size, color + (0,)); color_img.putalpha(capa)
        nuevo.alpha_composite(color_img)
    return orig, nuevo


def guardar_dds(nombre, img):
    os.makedirs(SAL, exist_ok=True)
    o = open(os.path.join(TEX, nombre + '.dds'), 'rb').read()
    fmt = {b'DXT1': 'DXT1', b'DXT5': 'DXT5', b'DXT3': 'DXT3'}.get(o[84:88])
    ruta = os.path.join(SAL, nombre + '.dds'); os.makedirs(os.path.dirname(ruta), exist_ok=True)
    import io, struct
    if o[84:88] == b'DX10' and struct.unpack('<I', o[128:132])[0] in (98, 99):   # (21-10) BC7: con texconv de Microsoft
        import subprocess, tempfile
        mips = max(1, struct.unpack('<I', o[28:32])[0])
        with tempfile.TemporaryDirectory() as tmp:
            png = os.path.join(tmp, 'x.png'); img.save(png)
            subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)), 'texconv', 'texconv.exe'), '-nologo', '-y',
                            '-f', 'BC7_UNORM_SRGB' if struct.unpack('<I', o[128:132])[0] == 99 else 'BC7_UNORM',
                            '-m', str(mips), '-dx10', '-o', tmp, png], check=True, stdout=subprocess.DEVNULL)
            nuevo = open(os.path.join(tmp, 'x.dds'), 'rb').read()
        assert len(nuevo) == len(o), (nombre, len(nuevo), len(o))
        open(ruta, 'wb').write(o[:148] + nuevo[148:])    # cabecera original (128 + 20 de DX10)
        return ruta
    if o[84:88] == b'\0\0\0\0' and struct.unpack('<I', o[88:92])[0] == 32:      # (21-10) sin comprimir, 32 bits
        import numpy as np
        mascaras = struct.unpack('<4I', o[92:108]); mips = max(1, struct.unpack('<I', o[28:32])[0]); W, H = img.size; datos = b''
        for nivel in range(mips):
            im = img if nivel == 0 else img.resize((max(1, W >> nivel), max(1, H >> nivel)), Image.LANCZOS)
            a = np.asarray(im, dtype=np.uint32); px = np.zeros(a.shape[:2], np.uint32)
            for canal, m in enumerate(mascaras):
                if m: px |= (a[..., canal] << ((m & -m).bit_length() - 1)) & m
            datos += px.astype('<u4').tobytes()
        assert len(datos) == len(o) - 128, (nombre, len(datos), len(o) - 128)
        open(ruta, 'wb').write(o[:128] + datos)
        return ruta
    if fmt is None: raise ValueError(f'{nombre}: formato DDS no previsto {o[84:88]}')
    if os.environ.get('DXT_PILLOW') is None:   # (25-10, claude2) el compresor de Pillow estropea el texto fino y los iconos de
        import subprocess, tempfile             # color (bloques de 2 colores mal elegidos): se usa texconv de Microsoft
        mips = max(1, struct.unpack('<I', o[28:32])[0])
        with tempfile.TemporaryDirectory() as tmp:
            png = os.path.join(tmp, 'x.png'); img.save(png)
            subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)), 'texconv', 'texconv.exe'), '-nologo', '-y',
                            '-f', {'DXT1': 'BC1_UNORM', 'DXT3': 'BC2_UNORM', 'DXT5': 'BC3_UNORM'}[fmt], '-m', str(mips),
                            '-bc', 'x', '-o', tmp, png], check=True, stdout=subprocess.DEVNULL)
            nuevo = open(os.path.join(tmp, 'x.dds'), 'rb').read()
        if len(nuevo) == len(o):
            open(ruta, 'wb').write(o[:128] + nuevo[128:]); return ruta
    mips = max(1, struct.unpack('<I', o[28:32])[0]); W, H = img.size; datos = b''
    for nivel in range(mips):                              # cada nivel de mipmap comprimido por separado
        im = img if nivel == 0 else img.resize((max(1, W >> nivel), max(1, H >> nivel)), Image.LANCZOS)
        if im.width < 4 or im.height < 4:                  # los bloques DXT son de 4x4: los niveles diminutos van en un bloque
            im = im.resize((max(4, im.width), max(4, im.height)), Image.LANCZOS)
        b = io.BytesIO(); im.save(b, format='DDS', pixel_format=fmt); datos += b.getvalue()[128:]
    datos = datos[:len(o) - 128]
    assert len(datos) == len(o) - 128, (nombre, len(datos), len(o) - 128)
    open(ruta, 'wb').write(o[:128] + datos)             # cabecera original (mismo tamaño, banderas y mipmaps)
    return ruta


if __name__ == '__main__':
    spec = json.load(open(os.path.join(R, 'trabajo', 'imagenes', 'atlas_es.json'), encoding='utf-8'))
    for nombre in (sys.argv[1:] or list(spec)):
        orig, nuevo = traducir(nombre, spec[nombre])
        guardar_dds(nombre, nuevo)
        W, H = orig.size; v = Image.new('RGBA', (W * 2, H), (40, 90, 40, 255))
        v.alpha_composite(orig, (0, 0)); v.alpha_composite(nuevo, (W, 0)); v.convert('RGB').save(os.path.join(SAL, nombre + '.png'))
        print('ok', nombre)
