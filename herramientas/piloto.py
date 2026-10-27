# -*- coding: utf-8 -*-
"""(Claude Code, 20-10-2026) Piloto del laboratorio de Yakuza 5: mira la pantalla antes de cada tecla.
Estados: TITULO (barra turquesa del menú) -> E; MENU (pantallas de nueva partida/regalos: fondo casi negro) -> E;
ESCENA (cualquier otra cosa) -> Esc; si aparece la pausa de escena (icono «Paused» en el centro) -> E (omitir);
si tras Esc NO aparece la pausa de escena, estamos JUGANDO: se cierra el menú con Esc y se para.
  python herramientas/piloto.py [pasos]      (el juego del laboratorio tiene que estar abierto)
Capturas en trabajo/capturas/piloto_NN.png. Imprime el estado de cada paso y «JUGANDO» / «CERRADO».
"""
import os, subprocess, sys, time
import numpy as np
from PIL import Image
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); C = os.path.join(R, 'trabajo', 'capturas')
UM = 'um'

def foto(n):
    p = os.path.join(C, f'piloto_{n:02d}.png')
    subprocess.run([UM, 'win', 'shot', '--exe', 'Yakuza5.exe', p], capture_output=True, timeout=30)
    return np.asarray(Image.open(p).convert('RGB').resize((1280, 720))).astype(int) if os.path.exists(p) else None

def tecla(*vk):
    cmds = ['focus', 'scanmode on']
    for k in vk: cmds += [f'hold {k} 180', 'sleep 1200']
    subprocess.run([UM, 'win', 'drive', '--proc', 'Yakuza5', *cmds], capture_output=True, timeout=60)

def abierto():
    return 'Yakuza5' in subprocess.run([UM, 'win', 'ps', 'Yakuza5'], capture_output=True, text=True).stdout

def estado(a):
    barra = a[338:368, 160:400]
    if ((barra[..., 1] - barra[..., 0] > 30) & (barra[..., 1] > 70)).mean() > 0.3: return 'TITULO'
    if a.mean() > 150: return 'PULSA'                     # «PRESS ANY BUTTON» (fondo blanco)
    centro = a[330:362, 624:656]
    pausa = a.mean() < 90 and (centro.min(2) > 120).mean() > 0.08 and a[370:395, 600:680].max() > 180 and a[595:630, 1050:1130].max() > 200
    if pausa: return 'PAUSA_ESCENA'
    if a.mean() < 12: return 'MENU' if (a.max(2) > 180).sum() > 300 else 'NEGRO'
    if a[:, :, :].mean() < 35 and (a[300:420, 400:880].max(2) > 200).mean() > 0.003: return 'MENU'
    return 'ESCENA'

def main(pasos):
    os.makedirs(C, exist_ok=True); visto_titulo = False
    for n in range(pasos):
        if not abierto(): print('CERRADO', n); return 'CERRADO'
        a = foto(n)
        if a is None: time.sleep(3); continue
        e = estado(a); print(n, e, flush=True)
        if e == 'TITULO': visto_titulo = True
        if e == 'TITULO' and os.environ.get('PARAR_EN_TITULO'): print('EN TITULO', n); return 'TITULO'
        if not visto_titulo and e not in ('TITULO',): tecla('0x45'); time.sleep(2); continue
        if e in ('TITULO', 'MENU', 'PULSA'): tecla('0x45'); time.sleep(2)
        elif e == 'PAUSA_ESCENA': tecla('0x45'); time.sleep(4)
        elif e == 'NEGRO': time.sleep(4)
        elif os.environ.get('PARAR_EN_ESCENA') and visto_titulo:
            print('EN ESCENA', n); return 'ESCENA'
        else:
            tecla('0x1B'); time.sleep(1.5); b = foto(n + 100)
            if b is None: continue
            e2 = estado(b); print('   tras Esc:', e2, flush=True)
            if e2 == 'PAUSA_ESCENA': tecla('0x45'); time.sleep(4)
            elif e2 == 'ESCENA':           # abrió el menú del juego: estamos jugando
                tecla('0x1B'); print('JUGANDO', n); return 'JUGANDO'
    return 'FIN'

if __name__ == '__main__': main(int(sys.argv[1]) if len(sys.argv) > 1 else 60)
