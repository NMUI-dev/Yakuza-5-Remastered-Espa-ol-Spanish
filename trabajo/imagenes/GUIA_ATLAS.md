# GUÍA DEL KIT DE ATLAS — Yakuza 5 (y después Yakuza 6)

Escrita por claude2 el 21-10-2026. Para claude1 y sus asistentes Fable. **claude2 verifica todo** antes de que entre al juego.

## Qué es un «atlas» y qué hay que hacer
Un atlas es una textura (.dds) con muchos rótulos sueltos (palabras de menús, botones, minijuegos). El juego recorta
cada rótulo con un rectángulo («casilla») sacado de su diseño .sbb. Hay que cambiar el texto inglés de cada casilla por
el español, **con la misma letra, el mismo tamaño, color, degradado, contorno y brillo, sin salirse nunca de la casilla**.
Son unos 200 atlas pendientes (los de páginas, el menú de pausa, el celular, el título y los carteles ya están hechos).

**Regla principal del usuario: que no quede nada feo.** Si un rótulo no se puede dejar bien, se deja en inglés
(«dejar»: true) y se apunta en el aviso al terminar. Es mejor un rótulo en inglés que uno roto.

## Flujo por atlas (todo desde C:\mods\yakuza5, con Git Bash)
```
python -X utf8 herramientas/atlas_probar.py reclamar <tu_nombre>   # te da el <id> del siguiente atlas libre
python -X utf8 herramientas/atlas_borrador.py hacer <id>            # borrador automático (gemma4 + OCR), ~1 min
#   -> trabajo/imagenes/atlas_borradores/<id>.json            (lo que editas)
#   -> trabajo/imagenes/atlas_borradores/<id>_casillas.png    (casillas numeradas; ROJO = revisar)
python -X utf8 herramientas/atlas_probar.py probar <id>             # dibuja el borrador
#   -> trabajo/imagenes/atlas_pruebas/<id>.png            (antes | después, la textura entera)
#   -> trabajo/imagenes/atlas_pruebas/<id>_casillas.png   (cada rótulo de cerca: original | español)
#   -> trabajo/imagenes/atlas_pruebas/<id>_gemma.json     (lo que gemma4 ve mal; orientativo, MIRA TÚ las imágenes)
# editar el .json, volver a probar... hasta que esté bien
python -X utf8 herramientas/atlas_probar.py aceptar <id>            # pasa a atlas_hechos/
python -X utf8 herramientas/atlas_probar.py estado                  # cuántos quedan
```
Al terminar una tanda, escribe en C:\Mods\NOTAS_AGENTES\buzon_claude1.md los <id> aceptados y lo que dejaste en inglés.
claude2 los revisa y los apunta en trabajo/imagenes/atlas_verificados.txt; solo los verificados entran al juego.

## Campos de cada rótulo («items» del .json)
| campo | qué es |
|---|---|
| caja | [x0, y0, x1, y1] la casilla del juego en píxeles. El texto NUNCA sale de aquí. Si el borrador la puso mal (dos rótulos en una casilla, casilla partida) corrígela mirando _casillas.png |
| en | inglés original (tal cual se ve) |
| es | español. Vacío = no se toca |
| fuente | archivo de letra (lista abajo) |
| alin | izq / centro / der (como el original dentro de su casilla) |
| ancho_max | ancho máximo del español en px (si no cabe se estrecha hasta 62 % y luego se achica) |
| efecto | nada (color plano medido) · estilo (degradado + contorno + brillo MEDIDOS del original: para rótulos de colores) · brillo (halo del mismo color) · borroso (copia desenfocada de otro rótulo: usa con «alto» y «radio») |
| fondo | lama = la casilla es opaca (botón, cartel): LaMa borra solo las letras y deja el fondo |
| alto | alto de letra en px (por defecto se mide del inglés; ponlo en casillas opacas o desenfocadas) |
| color | [r, g, b] para forzar el color (efecto nada) |
| mediana | (en el atlas) true = mismo tamaño para todos los rótulos de una columna |
| dejar | true = se deja en inglés (nombres propios, palabras partidas que no se pueden rehacer, imposibles) |
| revisar | nota del borrador: QUÍTALA cuando lo hayas resuelto |

Letras disponibles (C:\Windows\Fonts y C:\mods\yakuza6\herramientas\fuentes_img):
serif: times, timesi, timesbd, timesbi, georgia, georgiai, georgiab, georgiaz · sans: segoeui, segoeuii, segoeuib,
segoeuiz, verdana, verdanai, verdanab, verdanaz, tahoma, tahomabd, trebuc, trebucit, trebucbd, trebucbi, calibri… ·
seguisb (Segoe UI Semibold), consola/consolab (Consolas, monoespaciada: créditos), cour/courbd (Courier New) · gruesas: impact, Oswald, Bangers-Regular, LilitaOne-Regular · pincel: Knewave-Regular, CaveatBrush-Regular,
PermanentMarker-Regular · **NO uses arial*.ttf**: en este PC tumba a FreeType (se cierra Python).
Elige la que más se parezca al original mirando _casillas.png: grosor, cursiva, ancho de letra, serifas.

## Reglas de traducción
- Español NEUTRO latinoamericano (como todo el juego). Al jugador se le habla de tú. «Presiona», no «Pulsa».
- Usa la MISMA palabra que el texto del juego (el borrador ya la trae de las traducciones del juego: no la cambies sin
  motivo; si la cambias, que sea coherente en todos los atlas). Nombres propios, marcas y títulos de canciones: igual.
- Títulos de CANCIONES, de episodios con nombre propio y marcas se quedan en inglés («Love to See You Smile»,
  «Running Girl»): «dejar»: true. Nada de mezclas como «Carrera Girl».
- Las PÁGINAS marcadas (portadas, carteles con foto) también llegan al kit: casillas = renglones del OCR; casi siempre
  necesitan «fondo»: «lama» y «efecto»: «estilo».
- Mayúsculas como el original (si el inglés va en MAYÚSCULAS, el español también). Nada de «Lista De Misiones».
- Si no cabe, busca una versión más corta antes que estrechar demasiado (p. ej. «¡TE PASAS!» mejor que «¡TE PASASTE!»).
- Palabras partidas en varias casillas («ABI|LITY», «STRIKE A»): mira cómo las junta el juego; si no se puede
  rehacer bien, «dejar»: true en todas sus piezas.

## Lo que NO se toca
- Los atlas hechos a mano (trabajo/imagenes/atlas_es.json, textos_menu_es.py, manuales.txt): el kit ya los salta.
- trabajo/lotes (traducción de textos), trabajo/salida, D:\Y5_lab (laboratorio), el juego de Steam, nada de Yakuza 6.
- Solo escribes en: atlas_borradores/, atlas_pruebas/, atlas_reclamados/, atlas_hechos/ y el buzón.

## GPU y ayudantes
- gemma4:12b (Ollama, local, gratis) ocupa ~10 GB de GPU. Varios a la vez funciona pero va más lento; máx. 3 a la vez.
  Si claude2 avisa de prueba en el laboratorio (juego abierto), parar el kit hasta que termine.
- Las traducciones que falten: escríbelas tú (o con los ayudantes gratuitos del manual EQUIPO_GRATUITO.md, avisando en
  el buzón antes de usar GEMINI_API_KEY u OPENROUTER_API_KEY).

## Ejemplo resuelto
ui_en__surfboard__pjd_sstory_taxi_result.par__texlist_0001__2d_jm_taxi_result02: el borrador juntaba «Total Time» y
«Mission» en una casilla; las filas reales son de 24 px (0-24, 24-48 … 144-168): 7 rótulos, letra sans cursiva,
mediana true, efecto estilo (sale plano blanco porque el original no tiene contorno).

## Coherencia (verificación de claude2, 21-10)
- La MISMA textura aparece en varios .par (darts_sentaku en darts_anm y darts_menu, billiards_06 en billiards01 y 02):
  mismas palabras en todas. Términos fijados: Beginner = Novato, Intermediate = Intermedio, Advanced = Avanzado,
  Expert = Experto, HIDDEN = OCULTO, Games Left = Te quedan, More Time(s) = partida(s), Select a Game = Elige una partida,
  Left (bolas/tiros restantes) = Restantes.

- «alto» mide la tinta TOTAL (tildes, ñ, ¡ y colas incluidas): para que una palabra con tilde salga del mismo tamaño que sus vecinas, súbele 3-5 px. Las _casillas.png pueden ir AMPLIADAS: las cajas van en píxeles de la textura real.
- Más términos fijados: Accuracy = Precisión, Design = Diseño, Power = Potencia, Stability = Estabilidad (dardos).
- Golf: Course = Campo (NO «curso»): Campo principiante, Campo intermedio, Campo avanzado, Campo profesional.
- (fableC2a) Con contorno: «alto» = tinta del inglés MENOS el contorno (si no, las palabras cortas sin colas salen grandes).
- (fableC2a) Rótulo blanco plano con sombra: «estilo» lo deja hueco con contorno -> usa «efecto»: «nada» + «color»: [255,255,255].
- (fableC2a) gemma4 marca «leftover_english» casi siempre: NO es fiable; manda lo que ves.
- Hanafuda: Cherry Blossom Viewing = Contemplación de los cerezos (flores, no «cerezas»).

## Páginas de reglas y controles (criba de claude2, 21-10)
- REGLAS (rule_*): párrafos. Una casilla por RENGLÓN del original; reparte el español en el MISMO número de renglones
  (corta tú las frases), misma letra y mismo tamaño en todos («mediana»: true), alineación como el original. Nada de
  etiquetas visibles: «<Victory Conditions>» -> «<Condiciones de victoria>» tal cual se ve en el original (son texto),
  pero sin pegar palabras. Si un renglón no cabe, acorta la frase, no la letra.
- CONTROLES (2d_*_mgs_*): cada fila = un botón. Comprueba fila por fila que el español es la traducción de ESA fila
  (la pasada automática desplazaba filas: «Avoid» salía «No batear»). Conserva los símbolos △○□✕ (Segoe UI Symbol si
  la letra no los tiene). Términos: Button = Botón, Confirm = Confirmar, Cancel = Cancelar, Controls = Controles.
- Títulos de capítulo (syotitle) ya verificados por claude2 salvo syotitle_01 (PARTE 1 borroso: rehacer esa fila).
- (fableC2b) Más términos: High Score = Récord, Back = Atrás, User = Usuario, Hold = Mantén, Rapid = Rápido, Key = Tono,
  GREAT/GOOD/BAD/MISS = ¡GENIAL!/BIEN/MAL/FALLO, Sing = Cantar, Stamina = Resistencia, Condition = Condición,
  Personality = Carácter, Skills = Habilidades, Results = RESULTADOS.
- TAMAÑO IGUAL EN UNA COLUMNA: NO afines «alto» palabra por palabra. Quita «alto» de esos rótulos y pon en la cabecera
  del atlas «mediana»: true: el kit calcula el tamaño de cada uno y usa la MEDIANA para todos los de la misma columna
  (misma letra y x a menos de 40 px). Solo usa «alto» en casillas opacas o desenfocadas.
- (fableC2b) «lama»: la casilla SIEMPRE dentro del marco/píldora (si lo abarca, LaMa rehace el borde). Sin lama la
  casilla se vacía entera: no metas dentro marcos finos que deban quedar. «estilo»+lama suele dar gris: usa «nada» +
  «color».
- «lama» SOLO si la casilla tiene fondo opaco de verdad (el borde de la casilla opaco). En casilla transparente con contorno grueso, LaMa deja el contorno inglés: quítalo (pasó con «Key» -> «Tono» del karaoke).
- (fableC2a) «estilo» explícito funciona: {"arriba":[r,g,b],"abajo":[r,g,b],"contorno":[[r,g,b],grosor],"brillo":null}.
  El medido saca un solo contorno y el degradado apagado (medianas): aclara «arriba» a mano si hace falta; contornos
  blancos y sombras, a mano.
- (fableC2a) Rótulos semitransparentes (alfa < 200): el kit no los ve; pon «alto» y «color» a mano (gris opaco).
- (fableC2a) Botón con degradado (como «King» del mahjong): LaMa deja un parche: mejor «dejar».
- Un atlas YA VERIFICADO no se puede aceptar encima (el kit lo impide): si crees que hay que rehacerlo, avisa.
- Kochin: copas = «Copa X» (Copa Viento, Copa Pollo, Copa Dragón...).
- Póker (como el texto del juego): Little/Big Blind = CIEGA PEQUEÑA/GRANDE, Bet = IR (en panel: APUESTA), Check = PASAR,
  Call = VER, Raise = SUBIR, Fold = NO IR (cortos: caben sin estrechar). Personality = Personalidad (como el texto del juego, no «Carácter»).
- REGLA: antes de traducir un rótulo, busca si el juego ya lo tiene traducido (el borrador lo trae) y usa ESO.
- OJO «mediana»: iguala con las demás de la columna aunque esa casilla sea más baja (ej. «Mostrar» del póker salía cortado). Si una fila es más baja que sus vecinas, pon en ESE rótulo "mediana": false y su «alto».
- Botones opacos con cara metálica degradada (mahjong01): LaMa los deja negros: «dejar» (o a mano). El kit no hace dos renglones («
»): elige un texto de una línea.
- Las cajas deben cubrir las colas del inglés (g, p, y): si no, queda la cola sin borrar.
- Taiko: la marca CLEAR de las barras se deja en inglés en TODAS (coherencia; LaMa no puede con las azules).
- Cajas en FILA (varios rótulos en la misma línea): mide el hueco entre ellos; la caja termina donde acaba la tinta de SU palabra (si no, queda el último carácter inglés: «MARCO033»).
- (fableC2d) «margen» va por rótulo (por defecto 3 con «nada», 6 con otros): con «alin» «der» y margen 0 se corta el contorno.
- (fableC2d) Si la casilla incluye un trozo de barra o gráfico, el «alto» medido se dispara: estrecha la casilla a la tinta.
- (fableC2d) Segoe UI sale más pequeña de x que las letras latinas del juego: verdana/verdanai se parecen más.
- (fableC2a) Bocadillos en dos cajas contiguas: amplía cada caja 4-6 px alrededor de la tinta inglesa y fija «alto» por línea.
- Fondos semitransparentes o con trama fina (píldoras/barras del taiko): LaMa no sirve: «dejar».
- Taiko/ramen: Easy/Normal/Hard = Fácil/Normal/Difícil; Not Cleared = No superado; Select Song = Elige una canción;
  Select Difficulty = Elige dificultad; Dunk/Very Hard/Hard/Reg./Soft/Very Soft/Overcooked = Crudo/Muy duro/Duro/Normal/
  Blando/Muy blando/Pasado. Bolas de nieve: HIT = GOLPE, SHOOT = LANZA, POINT = PUNTOS. Ordinales 1st = 1.º.
- Palabras que el juego ANIMA letra a letra (piezas «STA|GE|CLE|AR|ED!» en la misma textura): si las piezas no se pueden rehacer, deja también en inglés la versión entera, o saldría la animación inglesa y luego el español.
- Haruka (idol): Singing = Canto, Basic Skill = Técnica, Performance = Actuación, Appeal = Encanto (igual en el texto del juego). UFO: PLAY = JUEGO, PLAYS = JUEGOS.
- El kit ya resta el «margen» del ancho disponible cuando hay brillo/estilo/borroso (no hace falta bajar ancho_max a mano).
- Princess League (Haruka): POP >> BAILE >> FINAL, LIVE BATTLE = BATALLA EN VIVO; «Princess League» y títulos de canciones en inglés. Lyrics by = Letra de, Music by = Música de.
- "mediana": "todos" (en la cabecera) iguala el tamaño de TODOS los rótulos con la misma letra, sin mirar la x (créditos, encabezados repartidos). Pendiente con esto: princess_staffroll (cajas ya medidas, marcadas «dejar»).
- Renglones pegados (uno debajo de otro): una palabra con cola (j, g, p) en el de ARRIBA pierde la cola porque el de abajo borra su caja: elige palabras sin cola o deja aire entre cajas.
- Páginas de controles en JAPONÉS dentro del juego inglés (pachi, suro): no se tocan.
- (fableC2b) LaMa en píldoras/botones de menos de ~20 px de alto sobre fondo blanco: rellena mal: «dejar».
- LaMa ajustable por rótulo: "lama_umbral" (por defecto 60; más bajo = borra más tinta suave/halo) y "lama_dila" (por defecto 3; más alto = borra más alrededor). Para restos al final de renglón: umbral 40, dila 4.
