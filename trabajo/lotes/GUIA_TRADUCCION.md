# Guía de traducción — Yakuza 5 Remastered (inglés oficial → español)

Proyecto del usuario (Claude Code, 20-10-2026). Se traduce desde el INGLÉS OFICIAL del juego, igual que Yakuza 6.

## Formato de trabajo
- Entrada: `lote_NNN.json` = lista de `{"id", "en", "ctx"}`. `ctx` dice dónde sale el texto:
  `diálogo uidXXXX` = conversación (las líneas seguidas del mismo uid son UNA conversación, en orden);
  `subtítulo de escena` = escenas de la historia; `tabla item|NAME` = nombre de objeto, `…|EXPLANATION` = descripción;
  `tabla ability|…` = habilidades; `menú/texto string_tbl` = menús e interfaz; `ai_popup` = frases cortas de combate;
  `mail` = correos del celular; `shop…/restaurant…/bar…` = tiendas, restaurantes y bares; `frase de acompañante` = lo que
  dice Haruka u otro acompañante al pasear.
- Salida: `lote_NNN_es.json` = objeto `{"id": "traducción"}` con TODOS los id del lote (claves como texto).
- Validar SIEMPRE: `python C:/mods/yakuza5/herramientas/validar_lote.py NNN` → tiene que decir OK.

## Reglas técnicas (las comprueba el validador)
1. Copiar EXACTAS todas las marcas: `<Color:8>` … `<Color:Default>`, `<Color:255,200,200,255>`, `<Italic>` … `</Italic>`,
   `%s`, `%d`, `%02d`. Pueden cambiar de sitio dentro de la frase si el español lo pide, pero no se traducen ni se tocan.
   Lo que va DENTRO de un par de color (`<Color:8>Staminan Spark<Color:Default>`) sí se traduce si es una palabra normal.
2. Mismo número de saltos de línea (`\n`) que el inglés. Repartir el texto para que los renglones queden parecidos.
   (Los diálogos casi nunca llevan salto: el juego corta solo.)
3. Los números se dejan como están (5,000). «yen» igual que en el original.
4. Solo caracteres de Latin-1 (español completo: á é í ó ú ü ñ Á É Í Ó Ú Ü Ñ ¿ ¡). Nada de emojis ni comillas raras.
   Usar SOLO comillas inglesas "…" (nada de « »); puntos suspensivos como "..." (como el original). Si el inglés trae
   caracteres japoneses o símbolos (♪, ☆, 　), se copian igual.
5. Respetar espacios al principio/fin y el espacio japonés ancho (`　`) si el original lo tiene.
6. Términos de juegos de mesa japoneses (mahjong: Pon, Chi, Kan, Riichi, Ron, Tsumo; koi-koi, oicho-kabu, cho-han,
   shogi) y siglas cortas de minijuegos se dejan como en el original.
7. `max` (solo algunas frases cortas de guion): el texto en UTF-8 no puede pasar de esos bytes (á é í ó ú ñ ü ¿ ¡
   cuentan 2). Si no cabe, abreviar o decirlo de otra forma.
8. Entre paréntesis = pensamiento del protagonista: `(I should come back later.)` → `(Debería volver más tarde.)`.

## Estilo
- Español NEUTRO latinoamericano (el usuario es de Latinoamérica). Al jugador se le habla de TÚ. «Presiona», no «Pulsa».
- Menús e interfaz: cortos, como el original. Mayúsculas igual que el original (títulos en MAYÚSCULAS se quedan en
  MAYÚSCULAS; «Title Case» inglés → solo la primera palabra con mayúscula, salvo nombres propios).
- Diálogos: naturales, con la personalidad de cada uno. Kiryu seco, serio y educado; Saejima rudo y de pocas palabras;
  Akiyama relajado y bromista; Haruka amable y joven; Shinada simpático y desafortunado; Majima excéntrico. Los matones
  vulgares. Las groserías con la misma fuerza que el inglés, en registro neutro (maldito, carajo, idiota, desgraciado...).
- Acentos regionales del inglés (Osaka/Kansai «ya», «gonna», «'em») → español coloquial neutro, sin imitar dialectos.
- Honoríficos japoneses se dejan: -san, -chan, -kun, -sama, -nee, Aniki, Oyaji, Mama (de un bar), Nii-san.
- Nada de explicaciones ni notas dentro del texto. Si una línea es solo un nombre propio o una onomatopeya, se deja o se adapta.
- Coherencia: mismo término siempre. Las decisiones nuevas se apuntan en `glosario_vivo.md` (una línea: inglés → español).

## Glosario fijo
Personajes (no se traducen): Kazuma Kiryu (alias «Taichi Suzuki» de taxista), Taiga Saejima, Shun Akiyama, Haruka
Sawamura, Tatsuo Shinada, Daigo Dojima, Goro Majima, Makoto Date, Tadashi Madarame, Kazuki Aizawa, Kei Morinaga,
Masaru Watase, Jun Oda, Mirei Park, Hana, Kanda, Kurosawa, Morinaga, Baba (Kite), Yasuko, Sakaguchi, Mack (Mack Hikaru)...
Ciudades y barrios (se dejan): Kamurocho (Tokio), Sotenbori (Osaka), Nagasugai (Fukuoka), Tsukimino (Sapporo),
Kineicho (Nagoya), Kansai. Calles: «X Street» → «Calle X»; «X Avenue» → «Avenida X»; «X Alley» → «Callejón X».
Organizaciones: Tojo Clan → Clan Tojo; Omi Alliance → Alianza Omi; Yamagasa Family → Familia Yamagasa;
Hokuto Society → Sociedad Hokuto; Dyna Star → Dyna Star (agencia de idols); Kitakata Family → Familia Kitakata.
Juego: Heat → Heat; Heat Action → Acción Heat; Heat Gauge → barra de Heat; Climax Heat → Climax Heat;
Essence of ... → Esencia de...; EXP → EXP; Health → Vida; Skill → Habilidad; Ability → Habilidad; Equipment → Equipo;
Inventory → Inventario; Item → Objeto; Key Items → Objetos clave; Substory → Subhistoria; Main Story → Historia
principal; Mission → Misión; Reward → Recompensa; Completion List → Lista de logros (del juego); Save → Guardar;
Load → Cargar; Difficulty → Dificultad (Easy → Fácil, Normal → Normal, Hard → Difícil, Legend → Leyenda);
Options → Opciones; Controls → Controles; Chapter → Capítulo; Part → Parte; Finale → Final.
Minijuegos y lugares: Cabaret Club → Club de cabaré; hostess → anfitriona; Taxi Mission → Misión de taxi;
Race Mission → Misión de carrera; Hunting → Caza; Batting Center → Centro de bateo; Karaoke → Karaoke; Darts → Dardos;
Bowling → Bolos; Pool → Billar; Fishing → Pesca; Club SEGA → Club SEGA; Princess League → Princess League;
Street Dance Battle → Batalla de baile callejero; Idol → idol; Fan → fan; Handshake event → evento de apretón de manos.
Locker Keys → llaves de casillero; Revelations → Revelaciones; Toughness/Staminan/Tauriner (bebidas) → se dejan.

## Español NEUTRO LATINO (pedido del usuario)
Nada de España (vosotros, coche, móvil, ordenador, vale, tío, chaval, crío, gafas, zumo, piso, conducir, aparcar, enfadarse,
cabrear, pillar, coger, joder, coño, hostia, gilipollas) ni jerga marcada de un solo país (ahorita, chido, güey, neta,
pinche, órale, che, boludo, pibe, laburo, chévere, parcero, vos). Usar: auto, celular, computadora, está bien/de acuerdo,
amigo, muchacho/niño, lentes, jugo, departamento, manejar, estacionar, enojarse, agarrar/atrapar, tomar, maldición/carajo/
demonios, imbécil.

## Errores vistos en la revisión del 21-10 (NO repetir)
- Toda pregunta o exclamación COMPLETA lleva su signo de apertura: «¿Cómo es posible?», «¡Vamos!». Faltaba en ~2.000 textos.
- Pero si el texto es la CONTINUACIÓN de una frase partida (empieza en minúscula: «inventas!», «bien?»), el ¿ o ¡ va en
  el trozo anterior: no se pone otro en medio.
- Nunca quitar ni cambiar los ? y ! de cierre del original (¿...!? se queda ¿...!?).
- Nada de palabras de España ni de un solo país: coche→auto, gafas→lentes, cabrear→enojar, cutre→de mala muerte,
  desmadre→relajo/caos, móvil (teléfono)→celular, vale→está bien, coger→tomar/agarrar.
- Sin restos en inglés ni palabras a medias («No necesito worrying…»): todo traducido salvo nombres propios, títulos de
  canciones y marcas. Términos técnicos en español: antialiasing→suavizado de bordes, merchandising→mercancía.
