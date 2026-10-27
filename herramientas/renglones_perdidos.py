# -*- coding: utf-8 -*-
"""(Claude Code, 21-10-2026) Renglones que el OCR SE SALTÓ en las páginas de reglas/tesoros/correos (quedaban párrafos
enteros en inglés: mjrule5, mjyaku20/23, poker0...). Por cada página:
  1. lee con OCR la versión YA TRADUCIDA (trabajo/imagenes/es o descartadas);
  2. un renglón en INGLÉS cuya zona sigue IGUAL que el original = renglón perdido -> se añade a ocr.json;
  3. rehace los párrafos (paginas_es.bloques) y los que no tienen traducción se piden a los ayudantes gratuitos
     (traductor_gemini.pedir) con los términos fijados (DEALER, HOME RUN...) -> bloques.json + cortos.json;
  4. imagenes_es.py <filtro> vuelve a dibujar la página.
Copia de seguridad de ocr/bloques/cortos en tareas/respaldo_renglones/.   python herramientas/renglones_perdidos.py
"""
import json, os, re, shutil, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rapidocr_onnxruntime import RapidOCR
import paginas_es as P
from ocr_imagenes import origen
from imagenes_lotes import validas, arreglar
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo', 'imagenes')
EN = set('the a an and or of to in on is are be you your it if this that with for at by from as can will not when then each player players card cards points point game win wins round turn hand'.split())
ES = set('el la los las un una y o de del en es son se te tu su si este esta con para por al que no cuando cada jugador jugadores carta cartas puntos gana partida ronda turno mano'.split())


def ingles(t):
    w = re.findall(r"[A-Za-z']+", t.lower()); e = sum(x in EN for x in w); s = sum(x in ES for x in w)
    return len(w) >= 2 and e >= 1 and e > s and not re.search('[áéíóúñ¿¡]', t)


def main():
    H = os.path.join(T, 'atlas_hechos'); rutas = []
    for f in sorted(os.listdir(H)):
        if not any(s in f for s in ('__rule_', '__takara__', '__mail__')): continue
        spec = json.load(open(os.path.join(H, f), encoding='utf-8'))
        if not any(i.get('es') and i.get('es') != i.get('en') and not i.get('dejar') for i in spec['items']):
            rutas.append(spec['textura'].replace(os.sep, '/') + '.dds')
    os.makedirs(os.path.join(R, 'tareas', 'respaldo_renglones'), exist_ok=True)
    for n in ('ocr.json', 'bloques.json', 'cortos.json'):
        d = os.path.join(R, 'tareas', 'respaldo_renglones', n)
        if not os.path.exists(d): shutil.copy(os.path.join(T, n), d)
    ocr = json.load(open(os.path.join(T, 'ocr.json'), encoding='utf-8'))
    blo = json.load(open(os.path.join(T, 'bloques.json'), encoding='utf-8'))
    cor = json.load(open(os.path.join(T, 'cortos.json'), encoding='utf-8'))
    lector = RapidOCR(); nuevos = {}
    from aplicar import traducciones, norm
    gen, _ = traducciones()
    for ruta in rutas:
        es_p = next((os.path.join(T, d, ruta) for d in ('es', 'descartadas') if os.path.exists(os.path.join(T, d, ruta))), None)
        if not es_p or ruta not in ocr: print('sin versión', ruta); continue
        a = np.asarray(Image.open(origen(ruta)).convert('RGBA')).astype(int); b = Image.open(es_p).convert('RGBA')
        fondo = Image.new('RGBA', b.size, (0, 0, 0, 255)); fondo.alpha_composite(b)
        res, _ = lector(np.asarray(fondo.convert('RGB')))
        bb = np.asarray(b).astype(int); add = []
        for caja, txt, conf in (res or []):
            xs = [p[0] for p in caja]; ys = [p[1] for p in caja]; x0, y0, x1, y1 = int(min(xs)), int(min(ys)), int(max(xs)) + 1, int(max(ys)) + 1
            if float(conf) < 0.6 or not ingles(txt): continue
            if np.abs(a[y0:y1, x0:x1] - bb[y0:y1, x0:x1]).mean() > 6: continue          # la zona cambió: ya traducida
            if any(min(x1, l[2]) - max(x0, l[0]) > 0.5 * (x1 - x0) and min(y1, l[3]) - max(y0, l[1]) > 0.5 * (y1 - y0) for l in ocr[ruta]): continue
            add.append([x0, y0, x1, y1, txt, float(conf)])
        if add: ocr[ruta] = ocr[ruta] + add; print(ruta.split('/')[-1], 'renglones perdidos:', [x[4][:40] for x in add])
        # párrafos de nuevo y los que no tengan traducción, a la cola
        aa = np.asarray(Image.open(origen(ruta)).convert('RGBA')).copy()
        def _cc(l):
            l2 = P.quitar_vineta(aa, l); m, _ = P.mascara_tinta(aa, l2[:4]); return list(l2[:6]) + [P.color_tinta(aa, m), l2[0] != l[0]]
        bs = P.bloques([_cc(l) for l in validas(ocr[ruta])], P.modo_de(ruta))   # igual que paginas_es
        nt = lambda t: re.sub(r'\s', '', arreglar(t or '').lower())
        hay = {nt(v['en']) for k, v in blo.items() if k.split('#')[0] == ruta and (k in cor or
               (gen.get(norm(v['juego'])) if v.get('juego') else gen.get(v['en'])))}   # solo los que TIENEN traducción
        for i, x in enumerate(bs):
            if nt(x['texto']) not in hay: nuevos[f'{ruta}#{300 + i}'] = x['texto']
    json.dump(ocr, open(os.path.join(T, 'ocr.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('párrafos nuevos a traducir', len(nuevos))
    if not nuevos: return
    sys.argv = [sys.argv[0], 'renglones']
    import traductor_gemini as TG
    enc = ("Traduce COMPLETO al español neutro latinoamericano cada párrafo de las reglas/textos de un minijuego de Yakuza 5 "
           "(leído por OCR de una imagen: puede venir sin espacios o con letras mal leídas; corrígelo). Traduce TODAS las "
           "frases, sin resumir. Términos fijos: dealer = «dealer» (no crupier), home run = «home run», Melee Match = "
           "«Combate cuerpo a cuerpo», Heat = «Heat», Dance Battle = «Batalla de baile», Hit (dardos) = «acierto», Heat Gauge = «barra de Heat», hostess = «anfitriona», dealer = «dealer». Mayúsculas solo donde toca en español. Devuelve SOLO JSON {\"t\": {\"id\": \"traducción\"}}.\n")
    ids = list(nuevos)
    for i in range(0, len(ids), 15):
        trozo = {str(n): nuevos[k] for n, k in enumerate(ids[i:i + 15])}
        r, m = TG.pedir(enc + json.dumps(trozo, ensure_ascii=False, indent=0))
        t = (r.get('t', r) if isinstance(r, dict) else {}) if r else {}
        for n, k in enumerate(ids[i:i + 15]):
            v = t.get(str(n))
            if isinstance(v, str) and len(v) >= 0.5 * len(nuevos[k]):
                blo[k] = {'en': nuevos[k], 'modo': P.modo_de(k.split('#')[0]), 'juego': None}; cor[k] = ' '.join(v.split())
        json.dump(blo, open(os.path.join(T, 'bloques.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        json.dump(cor, open(os.path.join(T, 'cortos.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        TG.log(f'{min(i + 15, len(ids))}/{len(ids)} ({m})')
    print('traducidos', sum(k in cor for k in ids), 'de', len(ids))


if __name__ == '__main__': main()
