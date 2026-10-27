# -*- coding: utf-8 -*-
"""(claude2, 25-10-2026) Revisión de TODAS las imágenes traducidas de la v1.0 (para la v1.0.1). La revisión local con gemma4
del 21-10 dio por buenas páginas MAL (2d_jm_tougi_okite: 3 de 4 renglones en inglés; rule_darts_cricket_05: texto encima
del marcador), así que se repite con dos filtros:
  ocr     OCR (RapidOCR, local) del ESPAÑOL de cada textura distinta: marca inglés sobrante (palabras inglesas comunes que
          no estaban en la traducción) -> revision_v101/ocr.json
  vision  Gemini flash (gratis; si se agota, OpenRouter gemma-4 :free) mira original | español y marca fallos de
          maquetación -> revision_v101/vision.json. Solo texturas con texto de verdad (>= 1 renglón en el OCR original).
  hoja    hojas de ~8 marcadas (original | español) para que Claude las mire -> revision_v101/hojas/hoja_NN.png
Retoma si se corta.  python -u herramientas/revisar_v101.py ocr|vision|hoja
"""
import os, sys, json, hashlib, re, time, io, base64, urllib.request
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocr_imagenes import origen
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo')
ES = os.path.join(T, 'imagenes', 'es'); SAL = os.path.join(T, 'imagenes', 'revision_v101'); os.makedirs(SAL, exist_ok=True)
OCR_ORIG = json.load(open(os.path.join(T, 'imagenes', 'ocr.json'), encoding='utf-8'))

INGLES = set('the of and to is are your you for with this that will be by can from on in it its not when if or as at all '
             'press hold use get into more each have has their them while which who what once players player game number '
             'points score closed hits overview rules rule win victory round start select back next skip cancel'.split())


def lista():
    """texturas traducidas distintas (por md5), con su ruta relativa a imagenes/es"""
    vis, out = set(), []
    for dp, _, fs in os.walk(ES):
        for f in sorted(fs):
            if not f.endswith('.dds'): continue
            p = os.path.join(dp, f); r = os.path.relpath(p, ES).replace(os.sep, '/')
            h = hashlib.md5(open(p, 'rb').read()).hexdigest()
            if h not in vis: vis.add(h); out.append(r)
    return out


def sobre_negro(im):
    b = Image.new('RGBA', im.size, (0, 0, 0, 255)); b.alpha_composite(im.convert('RGBA')); return b.convert('RGB')


def orig(ruta):
    p = origen(ruta)
    if not os.path.exists(p) and ruta.startswith('sprite_en/'): p = os.path.join(T, 'extraido', '2dpar_' + ruta)
    return p


def par(ruta, alto=None):
    """original | español, uno al lado del otro, sobre negro"""
    o = sobre_negro(Image.open(orig(ruta))); e = sobre_negro(Image.open(os.path.join(ES, ruta)))
    W, H = o.size; v = Image.new('RGB', (W * 2 + 12, H), (200, 0, 200)); v.paste(o, (0, 0)); v.paste(e, (W + 12, 0))
    if alto: v = v.resize((int(v.width * alto / v.height), alto), Image.LANCZOS)
    return v


def palabras(t): return re.findall(r"[a-záéíóúñü']+", t.lower())


def cmd_ocr():
    from rapidocr_onnxruntime import RapidOCR
    f = os.path.join(SAL, 'ocr.json'); hecho = json.load(open(f, encoding='utf-8')) if os.path.exists(f) else {}
    ocr = RapidOCR(); L = lista()
    for i, ruta in enumerate(L):
        if ruta in hecho: continue
        try:
            r, _ = ocr(np.asarray(sobre_negro(Image.open(os.path.join(ES, ruta)))))
            textos = [t for _, t, s in (r or []) if s > 0.6]
            ing = sorted({w for t in textos for w in palabras(t) if w in INGLES})
            orig_ing = {w for l in OCR_ORIG.get(ruta, []) for w in palabras(l[4]) if w in INGLES}
            hecho[ruta] = {'textos': textos, 'ingles': ing, 'en_original': len(orig_ing)}
        except Exception as e: hecho[ruta] = {'error': str(e)[:120]}
        if i % 25 == 0:
            json.dump(hecho, open(f, 'w', encoding='utf-8'), ensure_ascii=False); print(f'{len(hecho)}/{len(L)}', flush=True)
    json.dump(hecho, open(f, 'w', encoding='utf-8'), ensure_ascii=False)
    malos = [k for k, v in hecho.items() if len(v.get('ingles', [])) >= 2]
    print('fin', len(hecho), 'con inglés sobrante (>= 2 palabras):', len(malos))


PROMPT = ('Left half: ORIGINAL English texture from the video game Yakuza 5. Right half (after the magenta bar): the same '
          'texture after a fan translation into Spanish. Be STRICT. Report a problem if, in the Spanish half: any sentence or '
          'line is still in English (proper names, brand names, DARTSLIVE scoreboard terms and song titles may stay); some '
          'lines are Spanish and others English; Spanish text overlaps other text, icons, frames or scoreboard elements; text '
          'goes outside its box/panel or is cut off; letters are garbled, doubled, smeared or leftover English ink is visible '
          'behind; fonts are clearly mixed within one block; a line is missing. Answer ONLY JSON: '
          '{"ok": true/false, "problem": "none|english_left|mixed|overlap|outside|cut|garbled|ghost|font_mix|missing|other", '
          '"detail": "short, in Spanish"}')


def b64(im):
    im = im.copy(); im.thumbnail((1600, 800)); buf = io.BytesIO(); im.save(buf, 'PNG'); return base64.b64encode(buf.getvalue()).decode()


def gemini(img, prompt=None, modelos=('gemini-3.8-flash', 'gemini-3.7-flash', 'gemini-3.5-flash')):
    from google import genai
    from google.genai import types
    cli = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
    for m in modelos:
        if m in AGOTADOS: continue
        try:
            r = cli.models.generate_content(model=m, contents=[types.Part.from_bytes(data=base64.b64decode(b64(img)), mime_type='image/png'), prompt or PROMPT],
                                            config=types.GenerateContentConfig(response_mime_type='application/json', temperature=0))
            return json.loads(r.text), m
        except Exception as e:
            s = str(e)
            if '429' in s or 'RESOURCE_EXHAUSTED' in s or 'quota' in s.lower(): AGOTADOS.add(m); print('agotado', m, flush=True)
            elif '503' in s: time.sleep(10)
            else: print('error', m, s[:150], flush=True)
    return None, None


def openrouter(img, prompt=None, modelos=('nvidia/nemotron-3.5-super-vl:free', 'google/gemma-4-31b-it:free', 'google/gemma-4-26b-a4b-it:free')):
    for m in modelos:
        if m in AGOTADOS: continue
        cuerpo = {'model': m, 'messages': [{'role': 'user', 'content': [
            {'type': 'text', 'text': prompt or PROMPT}, {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + b64(img)}}]}]}
        for _ in range(2):
            try:
                q = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', json.dumps(cuerpo).encode(),
                                           {'Authorization': 'Bearer ' + os.environ['OPENROUTER_API_KEY'], 'Content-Type': 'application/json'})
                t = json.load(urllib.request.urlopen(q, timeout=300))['choices'][0]['message']['content']
                return json.loads(re.search(r'\{.*\}', t, re.S).group(0)), m
            except urllib.error.HTTPError as e:
                print('OpenRouter', m, e.code, flush=True)
                if e.code == 429 or e.code >= 500: time.sleep(30); continue
                AGOTADOS.add(m); break
            except Exception as e: print('error', m, str(e)[:120], flush=True); time.sleep(5)
    return None, None


AGOTADOS = set()


def cmd_vision():
    f = os.path.join(SAL, 'vision.json'); hecho = json.load(open(f, encoding='utf-8')) if os.path.exists(f) else {}
    L = [r for r in lista() if OCR_ORIG.get(r)]   # solo las que tenían texto en el original
    print('con texto:', len(L), 'hechas:', len(hecho), flush=True)
    for ruta in L:
        if ruta in hecho: continue
        img = par(ruta)
        r, m = (None, None) if os.environ.get('SOLO_OR') else gemini(img)
        if r is None: r, m = openrouter(img)
        if r is None: print('SIN CUOTA: paro (retoma mañana)', flush=True); break
        hecho[ruta] = {'ok': bool(r.get('ok', True)), 'problem': r.get('problem'), 'detalle': r.get('detail'), 'modelo': m}
        json.dump(hecho, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        print(ruta, hecho[ruta]['ok'], hecho[ruta]['problem'], m, flush=True)
    print('fin vision', len(hecho), 'marcadas', sum(1 for v in hecho.values() if not v['ok']))


def cmd_hoja():
    marc = []
    fo = os.path.join(SAL, 'ocr.json'); fv = os.path.join(SAL, 'vision.json')
    o = json.load(open(fo, encoding='utf-8')) if os.path.exists(fo) else {}
    v = json.load(open(fv, encoding='utf-8')) if os.path.exists(fv) else {}
    for r in lista():
        motivo = []
        if len(o.get(r, {}).get('ingles', [])) >= 2: motivo.append('OCR inglés: ' + ' '.join(o[r]['ingles'][:6]))
        if r in v and not v[r]['ok']: motivo.append(f"visión: {v[r]['problem']} - {v[r]['detalle']}")
        if motivo: marc.append((r, ' | '.join(motivo)))
    json.dump(marc, open(os.path.join(SAL, 'marcadas.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    os.makedirs(os.path.join(SAL, 'hojas'), exist_ok=True)
    for n in range(0, len(marc), 8):
        filas = []
        for r, motivo in marc[n:n + 8]:
            p = par(r, alto=230); c = Image.new('RGB', (1500, 262), (20, 20, 24)); c.paste(p.crop((0, 0, min(p.width, 1500), 230)), (0, 30))
            ImageDraw.Draw(c).text((6, 6), f'[{marc.index((r, motivo))}] {r}  ->  {motivo}'[:230], fill=(255, 220, 0)); filas.append(c)
        h = Image.new('RGB', (1500, 262 * len(filas))); [h.paste(c, (0, i * 262)) for i, c in enumerate(filas)]
        h.save(os.path.join(SAL, 'hojas', f'hoja_{n // 8:02d}.png'))
    print('marcadas', len(marc), 'hojas', (len(marc) + 7) // 8)


PROMPT_LOTE = ('This image stacks {n} rows labelled {etq}. ' + PROMPT.replace('Answer ONLY JSON: ', 'Judge EACH row separately. Answer ONLY JSON with one key per row label, each value: '))


def cmd_lote(n=3):
    """(25-10) cupo gratis escaso (OpenRouter ~50 peticiones/día): {n} pares por petición, solo las NO verificadas a ojo el
    21-10 (atlas_verificados.txt). Si no hay cupo, duerme 1 h y sigue (se gestiona solo)."""
    f = os.path.join(SAL, 'vision.json'); hecho = json.load(open(f, encoding='utf-8')) if os.path.exists(f) else {}
    av = set(l.split()[0] for l in open(os.path.join(T, 'imagenes', 'atlas_verificados.txt'), encoding='utf-8') if l.strip())
    L = [r for r in lista() if OCR_ORIG.get(r) and r.replace('/', '__')[:-4] not in av and r not in hecho]
    print('pendientes', len(L), flush=True)
    i = 0
    while i < len(L):
        grupo = L[i:i + n]; etq = [chr(65 + k) for k in range(len(grupo))]
        filas = [par(r, alto=300) for r in grupo]; W = max(x.width for x in filas)
        img = Image.new('RGB', (W + 60, sum(x.height + 10 for x in filas)), (0, 0, 0)); y = 0
        for e, x in zip(etq, filas):
            d = ImageDraw.Draw(img); d.rectangle([0, y, 55, y + 55], fill=(255, 255, 0)); d.text((18, y + 15), e, fill=(0, 0, 0), font_size=30)
            img.paste(x, (60, y)); y += x.height + 10
        pr = PROMPT_LOTE.replace('{n}', str(len(grupo))).replace('{etq}', ', '.join(etq))
        AGOTADOS.clear()
        r, m = (None, None) if os.environ.get('SOLO_OR') else gemini(img, pr)
        if r is None: r, m = openrouter(img, pr)
        if r is None: print('sin cupo: espero 1 h', time.strftime('%H:%M'), flush=True); time.sleep(3600); continue
        for e, ruta in zip(etq, grupo):
            v = r.get(e) or {}
            hecho[ruta] = {'ok': bool(v.get('ok', True)), 'problem': v.get('problem'), 'detalle': v.get('detail'), 'modelo': m, 'lote': True}
            print(ruta, hecho[ruta]['ok'], hecho[ruta]['problem'], m, flush=True)
        json.dump(hecho, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        i += n
    print('fin lote', len(hecho), 'marcadas', sum(1 for v in hecho.values() if not v['ok']), flush=True)


if __name__ == '__main__':
    {'ocr': cmd_ocr, 'vision': cmd_vision, 'hoja': cmd_hoja, 'lote': cmd_lote}[sys.argv[1]]()
