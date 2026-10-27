# -*- coding: utf-8 -*-
"""(claude1, 25-10-2026) v1.0.1: traducción de los renglones de las 78 guías de controles (2d_*_mgs_*), revisada a mano.
Clave = texto inglés normalizado (minúsculas, solo letras/números y / + ( ) ), como lo leyó el OCR (a veces sin espacios).
Botones: «Botón X» con su símbolo; «Panel táctil»; «Stick izq./der.» (corto: cabe en la columna)."""
import re


def clave(t):
    t = t.replace('（', '(').replace('）', ')').replace('ldol', 'Idol').replace('lnterject', 'Interject')
    return re.sub(r'[^a-z0-9/+()△]', '', t.lower())


# columnas de botones (el símbolo se dibuja con Segoe UI Symbol)
BOTONES = {
    'l1button': 'Botón L1', 'l2button': 'Botón L2', 'r1button': 'Botón R1', 'r2button': 'Botón R2', 'l3button': 'Botón L3',
    'r3button': 'Botón R3', 'optionsbutton': 'Botón OPTIONS', 'touchpadbutton': 'Panel táctil', 'leftstick': 'Stick izq.',
    'rightstick': 'Stick der.', 'obutton': 'Botón ○', 'xbutton': 'Botón ✕', '△button': 'Botón △', 'button': 'Botón □',
    'upbutton': 'Arriba', 'directional': '', 'buttons': 'Cruceta', 'l1+l2': 'L1+L2', 'r1+r2': 'R1+R2',
}

TEXTOS = {
    'controls': 'Controles', 'exitminigame': 'Salir del minijuego', 'cancel': 'Cancelar', 'movecursor': 'Mover cursor',
    'confirm': 'Confirmar', 'movecamera': 'Mover cámara', 'timinginput': 'Toca a tiempo', 'displayitemscreen': 'Ver objetos',
    'help': 'Ayuda', 'displayrules': 'Ver reglas', 'adjustspin/': 'Ajustar efecto/', 'selectball': 'Elegir bola',
    'answer': 'Responder', 'swing': 'Batear', 'returntotitle': 'Volver al título', 'move': 'Mover', 'changeview': 'Cambiar vista',
    'movetheswingcursor': 'Mover cursor de bateo', 'move/jump/crouch': 'Mover/Saltar/Agacharse', 'pose': 'Posar',
    'preselectframe': 'Elegir marco', 'beatrim(left)': 'Borde (izq.)', 'beatrim(right)': 'Borde (der.)', 'brake': 'Frenar',
    'accelerator': 'Acelerar', 'accelerate': 'Acelerar', 'decelerate': 'Desacelerar', 'toggleblinkers': 'Intermitentes',
    'horn': 'Claxon', 'resulttablecontrols': 'Tabla de resultados', 'standingposition/': 'Posición/',
    'confirmdirectionandpower': 'Confirmar dirección y fuerza', 'ok/sendmessage': 'Aceptar/Enviar mensaje', 'back': 'Atrás',
    'changeposition': 'Cambiar posición', 'wavehands': 'Saludar', 'choosefreeaction': 'Acción libre',
    'pullrod/confirm': 'Tirar de la caña/Confirmar', 'beatfront(right)': 'Centro (der.)', 'beatfront(left)': 'Centro (izq.)',
    'movetaxileft/right': 'Mover taxi izq./der.', 'reposition': 'Recolocar', 'selectaction': 'Elegir acción',
    'display/hideinfo': 'Ver/Ocultar info', 'quickstep': 'Paso rápido', 'sidestepleft': 'Paso lateral izq.',
    '(+withleftstick)': '(+ stick izq.)', 'sidestepright': 'Paso lateral der.', 'jump': 'Saltar', 'changedarts': 'Cambiar dardos',
    'displaylistofhands': 'Ver jugadas', 'staremode': 'Modo mirada', 'slowmode': 'Modo lento',
    'heatsmash(inheatmode)': 'Impacto Heat (modo Heat)', 'controlmallet/': 'Mover mazo/', 'controlperspective': 'Mover cámara',
    'hit': 'Golpear', 'avoid': 'Evitar', 'swing/confirm': 'Batear/Confirmar', 'swing/cancel': 'Batear/Cancelar', 'run': 'Correr',
    'guard': 'Cubrirse', 'dodge': 'Esquivar', 'pose/confirm': 'Posar/Confirmar', 'pose/cancel': 'Posar/Cancelar',
    'removenoodles': 'Sacar fideos', 'replenishsnowballs': 'Recargar bolas', 'throwscattershot': 'Lanzar ráfaga',
    'throwsnowball': 'Lanzar bola de nieve', 'tackle': 'Placaje', '(+leftstick)': '(+ stick izq.)',
    'movecharacter': 'Mover personaje', 'beatfront(right)/cancel': 'Centro (der.)/Cancelar', 'dragheatactions': 'Acciones Heat',
    'drift': 'Derrapar', 'taunt': 'Provocar', 'turbo': 'Turbo', 'select': 'Elegir', 'squeeze': 'Apretar', 'changebet': 'Cambiar apuesta',
    'confirm/choosediscard': 'Confirmar/Descartar', 'supertakeback': 'Súper deshacer', 'movepointer': 'Mover puntero',
    'takeback': 'Deshacer', 'reverseleftstickcontrols': 'Invertir stick izq.', 'resetcamera': 'Restablecer cámara',
    'displayballnumber': 'Ver número de bola', 'entershotmode': 'Modo tiro', 'adjusthittingangle/': 'Ajustar ángulo/',
    'positioncueball': 'Colocar bola blanca', 'returntoviewmode': 'Volver a modo vista', 'adjustimpactpoint': 'Ajustar punto de impacto',
    'shoot': 'Tirar', 'display10frames': 'Ver 10 cuadros', 'dropkick': 'Patada voladora', 'attack': 'Atacar',
    'onerolltriple': 'Triple de una tirada', 'displayrollhistory': 'Ver historial', 'cancel/closedisplayscreen': 'Cancelar/Cerrar',
    'displayscores': 'Mostrar puntajes', 'adjustthrowstrength': 'Ajustar fuerza', 'releasereel(doublespeed)': 'Soltar sedal (x2)', 'l1+l2releasereel(doublespeed)': 'L1+L2 Soltar sedal (x2)', 'r1+r2windreel(doublespeed)': 'R1+R2 Recoger sedal (x2)', '三': '',
    'windreel(doublespeed)': 'Recoger sedal (x2)', 'releasereel': 'Soltar sedal', 'reelin': 'Recoger sedal',
    'movecursor/manipulaterod': 'Mover cursor/caña', 'changedirection': 'Cambiar dirección', 'shoot/confirm': 'Disparar/Confirmar',
    'shout/interject': 'Gritar/Intervenir', 'maracas': 'Maracas', 'controls/stop': 'Controles/Parar', 'givenegative': 'Responder que no',
    'movecamera(firstpersononly)': 'Mover cámara (1.ª persona)', 'confirmdiscardtiles': 'Confirmar descarte', 'display/': 'Mostrar/',
    'hideactioncommands': 'Ocultar comandos', 'selecttile': 'Elegir ficha', 'shootbeam': 'Disparar rayo', 'movecrane/confirm': 'Mover grúa/Confirmar',
    'insertcoin(s)': 'Insertar moneda', 'hit/confirm': 'Golpear/Confirmar', 'hit/cancel': 'Golpear/Cancelar', 'heatmode': 'Modo Heat',
    'flashawaitasecsmile': 'Sonrisa «¡Un momento!»', 'shakehands': 'Dar la mano', 'idolheat': 'Heat de ídolo', 'climaxheat': 'Clímax Heat',
    'raiseocard': 'Levantar carta ○', 'raisexcard': 'Levantar carta ✕', 'longrangeattack': 'Ataque a distancia',
    'loveshineattack': 'Ataque Love Shine', 'closerangeattack': 'Ataque cuerpo a cuerpo', 'stance': 'Postura', 'finishingblow': 'Golpe final',
    'grab': 'Agarrar', 'rushcombo': 'Combo rápido', 'eggon/confirm': 'Animar/Confirmar', 'removenoodles/confirm': 'Sacar fideos/Confirmar',
    'removenoodles/cancel': 'Sacar fideos/Cancelar', 'run(doubletaptododge)': 'Correr (2 toques: esquivar)', 'peekleft/right': 'Asomarse izq./der.',
    'beatfront(right)/confirm': 'Centro (der.)/Confirmar', 'movecartleft/right': 'Mover carrito izq./der.', 'commandnpc': 'Dar órdenes',
    'reload': 'Recargar', 'aim': 'Apuntar', 'strafemove/shoot': 'Moverse/Disparar', 'meleeattack': 'Ataque cuerpo a cuerpo',
    'throwoutbearbait': 'Lanzar cebo para osos', 'crouch': 'Agacharse', 'firegun': 'Disparar', 'throwweapon': 'Lanzar arma',
    'rollforward': 'Rodar hacia adelante', 'confirmbet/rolldice': 'Apostar/Tirar dados', 'viewrules': 'Ver reglas',
    'tambourine/confirm': 'Pandereta/Confirmar', 'clap/cancel': 'Aplaudir/Cancelar', 'tambourine/cancel': 'Pandereta/Cancelar',
    'clap/confirm': 'Aplaudir/Confirmar', 'change/skipovertopic': 'Cambiar/Saltar tema', 'giveaffirmative/confirm': 'Decir que sí/Confirmar',
    'closemenu': 'Cerrar menú', 'giveaffirmative/closemenu': 'Decir que sí/Cerrar', 'moveautomatically': 'Mover solo',
}


def traducir(t):
    k = clave(t)
    if k in BOTONES: return BOTONES[k]
    if k in TEXTOS: return TEXTOS[k]
    k2 = k.replace('(', '').replace(')', '')
    for d in (TEXTOS, BOTONES):
        for a, b in d.items():
            if a.replace('(', '').replace(')', '') == k2: return b
    return None
