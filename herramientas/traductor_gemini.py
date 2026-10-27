# -*- coding: utf-8 -*-
"""(Claude Code, 19-10-2026) Traductor con la API gratuita de Gemini (clave en GEMINI_API_KEY).
Reclama lotes libres (reclamar_lote.sh), manda guía + glosario + lote, recibe {"id": "texto"}, valida con validar_lote.py
y si hay errores le devuelve solo esas frases con el error (hasta 3 rondas). Si un modelo se queda sin cuota (429) pasa al
siguiente de la lista.
  python herramientas/traductor_gemini.py NOMBRE [máx_lotes]
"""
import json, os, re, subprocess, sys, time
from google import genai
from google.genai import types

Y = 'C:/mods/yakuza5'; L = f'{Y}/trabajo/lotes'
MODELOS = os.environ.get('GEMINI_MODELOS', 'gemini-4-argon gemini-3.8-flash gemini-3.7-flash gemini-3.5-flash gemini-2.5-flash '
    'or:google/gemma-4-31b-it:free or:nvidia/nemotron-3-ultra-550b-a55b:free or:minimax/minimax-m3.1-flash:free').split()
# (19-10) «or:» = modelos gratis de OpenRouter (clave en OPENROUTER_API_KEY) cuando se acaba la cuota diaria de Gemini
QUIEN = sys.argv[1] if len(sys.argv) > 1 else 'gemini'
MAXL = int(sys.argv[2]) if len(sys.argv) > 2 else 999
cli = genai.Client()
# (19-10) cuotas aprendidas: tareas/gemini/cuotas.json guarda por modelo cuántas peticiones aguantó cada día y cuándo se
# agotó; un modelo agotado se salta hasta el reinicio diario (medianoche del Pacífico = 07:00 UTC) en TODOS los hilos
import datetime
CUOTAS = f'{Y}/tareas/gemini/cuotas.json'
def dia():  # día de cuota (reinicia a las 07:00 UTC)
    return (datetime.datetime.utcnow() - datetime.timedelta(hours=7)).strftime('%Y-%m-%d')
def cuotas():
    try: return json.load(open(CUOTAS, encoding='utf-8'))
    except Exception: return {}
def anotar(m, agotado=False):
    c = cuotas(); d = c.setdefault(m, {}).setdefault(dia(), {'peticiones': 0})
    if agotado: d['agotado'] = time.strftime('%H:%M')
    else: d['peticiones'] += 1
    json.dump(c, open(CUOTAS, 'w', encoding='utf-8'), indent=1)
class SinCuota:
    def __contains__(self, m): return 'agotado' in cuotas().get(m, {}).get(dia(), {}) or m in no_hay
    def add(self, m): anotar(m, agotado=True)
    def __len__(self): return sum(1 for m in MODELOS if m in self)
no_hay = set()   # modelos inexistentes (404)
sin_cuota = SinCuota()

def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)

def openrouter(m, prompt):
    import urllib.request
    q = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', headers={
        'Authorization': 'Bearer ' + os.environ['OPENROUTER_API_KEY'], 'Content-Type': 'application/json'},
        data=json.dumps({'model': m, 'temperature': 0.4, 'response_format': {'type': 'json_object'},
                         'messages': [{'role': 'user', 'content': prompt}]}).encode())
    try: t = json.load(urllib.request.urlopen(q, timeout=600))['choices'][0]['message']['content']
    except urllib.error.HTTPError as e: raise Exception(f'{e.code} {e.read()[:200]}')
    t = re.sub(r'^```(?:json)?|```$', '', t.strip()).strip()
    return json.loads(t)

def pedir(prompt):
    for m in MODELOS:
        if m in sin_cuota: continue
        for intento in range(3):
            try:
                if m.startswith('or:'): r = openrouter(m[3:], prompt); anotar(m); return r, m
                r = cli.models.generate_content(model=m, contents=prompt, config=types.GenerateContentConfig(
                    response_mime_type='application/json', temperature=0.4))
                anotar(m); return json.loads(r.text), m
            except Exception as e:
                s = str(e)
                if '429' in s or 'RESOURCE_EXHAUSTED' in s:
                    if 'PerDay' in s or 'per day' in s.lower() or intento == 2: sin_cuota.add(m); log(f'{m}: sin cuota'); break
                    time.sleep(40); continue
                if '404' in s or 'not found' in s.lower(): no_hay.add(m); log(f'{m}: no disponible'); break
                log(f'{m}: error {s[:150]}'); time.sleep(10)
    return None, None

def validar(n):
    p = subprocess.run([sys.executable, f'{Y}/herramientas/validar_lote.py', n], capture_output=True, text=True, encoding='utf-8', errors='replace', env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
    return p.returncode == 0, p.stdout

GUIA = open(f'{L}/GUIA_TRADUCCION.md', encoding='utf-8').read()
ENCARGO = """Eres traductor profesional de videojuegos. Traduce al español neutro latinoamericano estos textos de Yakuza 5
(inglés oficial), siguiendo AL PIE DE LA LETRA la guía y los glosarios. Devuelve SOLO un objeto JSON {"t": {"id": "traducción"}, "nota": "..."}
con TODOS los id pedidos en "t" (claves como texto). En "nota" (opcional, una o dos frases) apunta lo que otro traductor
debería saber de este trozo: contexto de la escena o personaje, decisiones de estilo, términos nuevos (o "" si nada). Copia exactas las marcas (<Color:..>, <Italic>, %s), mismo número de \\n. Las líneas seguidas del mismo
"diálogo uid..." son UNA conversación, en orden: tradúcelas con coherencia entre sí. Si un texto trae "max", la traducción
en bytes UTF-8 (tildes y ñ cuentan 2) NO puede pasar de ese número.
"""

NOTAS = f'{L}/NOTAS_TRADUCTORES.txt'
def notas():
    return ''.join(open(NOTAS, encoding='utf-8').readlines()[-80:]) if os.path.exists(NOTAS) else ''

def apuntar(n, r):
    nota = r.get('nota') if isinstance(r, dict) else None
    if isinstance(nota, str) and nota.strip():
        open(NOTAS, 'a', encoding='utf-8').write(f'[{QUIEN} · lote {n}] {nota.strip()}\n')
    return r.get('t', r) if isinstance(r, dict) else {}

def traducir(n):
    lote = json.load(open(f'{L}/lote_{n}.json', encoding='utf-8'))
    glos = open(f'{L}/glosario_vivo.md', encoding='utf-8').read()
    ruta = f'{L}/lote_{n}_es.json'
    es = json.load(open(ruta, encoding='utf-8')) if os.path.exists(ruta) else {}
    falta = [x for x in lote if str(x['id']) not in es]
    for i in range(0, len(falta), 120):        # trozos de 120 frases
        parte = falta[i:i+120]
        r, m = pedir(f'{ENCARGO}\n# GUÍA\n{GUIA}\n# GLOSARIO VIVO\n{glos}\n# NOTAS DE LOS OTROS TRADUCTORES\n{notas()}\n# TEXTOS\n{json.dumps(parte, ensure_ascii=False)}')
        if r is None: return False
        r = apuntar(n, r)
        es.update({str(k): v for k, v in r.items() if str(k) in {str(x['id']) for x in parte} and isinstance(v, str)})
        json.dump(es, open(ruta, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        log(f'lote {n}: {len(es)}/{len(lote)} ({m})')
    for ronda in range(3):
        ok, salida = validar(n)
        if ok: return True
        malos = set(re.findall(r'^\s+(\d+):', salida, re.M))
        if not malos: return False
        errores = '\n'.join(l for l in salida.splitlines() if re.match(r'\s+\d+:', l))
        parte = [x for x in lote if str(x['id']) in malos]
        r, m = pedir(f'{ENCARGO}\n# GUÍA\n{GUIA}\nEstas traducciones fallaron la validación:\n{errores}\n'
                     f'# TRADUCCIÓN ANTERIOR\n{json.dumps({k: es.get(k) for k in malos}, ensure_ascii=False)}\n'
                     f'# ORIGINALES\n{json.dumps(parte, ensure_ascii=False)}\nDevuelve el JSON corregido solo con esos id en "t".')
        if r is None: return False
        r = r.get('t', r)
        es.update({str(k): v for k, v in r.items() if str(k) in malos and isinstance(v, str)})
        json.dump(es, open(ruta, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        log(f'lote {n}: ronda de corrección {ronda+1} ({len(malos)} frases)')
    return validar(n)[0]

if __name__ == '__main__':   # (21-10) importable desde corregir_fallos.py
    hechos = 0
    while hechos < MAXL:
        if len(sin_cuota) >= len(MODELOS):   # todos agotados: dormir hasta el reinicio diario y seguir solo
            log('todos los modelos sin cuota: espero al reinicio diario'); time.sleep(1800); continue
        n = subprocess.run(['C:/Program Files/Git/usr/bin/bash.exe',f'{Y}/herramientas/reclamar_lote.sh', QUIEN], capture_output=True, text=True).stdout.strip()
        if not n: log('sin lotes libres: fin'); break
        log(f'lote {n}: empiezo')
        if traducir(n): log(f'lote {n}: OK'); hechos += 1
        else:
            log(f'lote {n}: FALLÓ (se libera, se conserva lo hecho)')
            subprocess.run(['rm', '-rf', f'{L}/reclamados/{n}'])
