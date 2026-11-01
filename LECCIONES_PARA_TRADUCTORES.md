# Lecciones para traductores de Yakuza (lo que aprendimos con el Yakuza 5)

Lecciones de la traducción al español del *Yakuza 5 Remastered*, para la comunidad. El detalle de cada versión está
en `entrega/Herramientas para traduccion/PASO_A_PASO.txt`; cómo compilarla, en [COMPILAR.md](COMPILAR.md).


## A. Dónde guarda texto el juego (no te saltes ninguno)

1. Diálogos .msg (wdr_par_en/wdr.par y common.par): además de los REGISTROS de diálogo, cada .msg tiene al final una
   TABLA DE NOMBRES (u16 con el número en 0x0E, tabla de punteros big endian en 0x10). Ahí van el nombre de quien habla,
   las OPCIONES de respuesta e incluso las PREGUNTAS del concurso de preguntas. Es fácil no verla.
2. Subtítulos de escena (auth/subtitle.par, CSV en UTF-16): hay filas con un salto de línea DENTRO de las comillas. Si
   se lee el CSV renglón a renglón, esas filas se parten en dos y no se traducen. Las comillas de dentro van como "".
3. Tablas ARMP de db.devil/en: msg.bin (mensajes del sistema) y msg_replacer.bin (carteles de zona al entrar, objetos,
   enemigos, comentarios de los dardos). Las cadenas con salto de línea (\n) también son texto del jugador. Si se filtran
   con «isprintable», se pierden.
4. Tablas .bin de boot, pause, scenario y minijuegos: menús, correos, misiones y reglas.
5. Imágenes .dds dentro de los .par: menús, carteles, títulos de capítulo, rótulos de fecha y lugar de las escenas,
   letras del karaoke, reglas de los minijuegos.
6. Vídeos .usm (data/mvstm): las presentaciones de personaje («TADASHI MADARAME / PATRIARCH...») van DIBUJADAS dentro
   del vídeo. Sus subtítulos sí salen de subtitle.par. Cambiar lo dibujado obliga a reeditar los vídeos: 69 vídeos,
   5,7 GB.
7. El ejecutable lleva «PRESS ANY BUTTON». No hace falta tocar el .exe para nada más.

## B. Imágenes

8. No te fíes de una sola revisión. Si buscas «las texturas en inglés que son distintas de las japonesas», te saltas
   las que no tienen versión japonesa (auth_telop_en: los rótulos de escena). Pasa el OCR a TODAS las texturas _en.
9. Los nombres de archivo cambian dentro de un mismo grupo: las letras del karaoke son 2d_jm_ok_* Y 2d_yk_ok_*
   («Kamurocho Lullaby»). Filtra por carpeta, no por prefijo.
10. En los textos de una sola línea sobre fondo transparente (rótulos, letras del karaoke) es mejor REHACER la textura entera, con una letra parecida medida sobre el original, que borrar el inglés a trozos: el OCR parte las líneas y quedan restos.
11. Comprueba a ojo, en una hoja de contacto, TODAS las imágenes de inicio de capítulo.

## C. Meter los textos sin romper el juego

12. Si buscas un puntero por su VALOR (los 4 bytes del offset de la cadena), puede salir un dato que solo vale lo mismo por casualidad. A nosotros, un valor de la cabecera de una subtabla coincidía con la posición del texto «Po» y el juego se cerraba al arrancar. Solución: no toques lo que no cambia, y exige que el u32 de al lado también apunte a una cadena (un puntero de verdad está en una tabla de punteros).
13. Si el juego se cierra, busca la causa partiendo la lista de cambios por la mitad: con 3.672 cadenas bastaron 12 arranques.
14. Busca la traducción primero por la frase EXACTA. Una búsqueda «parecida» (sin etiquetas ni espacios) puede traer etiquetas de color o espacios que el original no lleva.
15. Un trozo de inglés dentro de una frase ya traducida se puede cambiar en su sitio, si ocupa los mismos bytes.
16. Prueba siempre en una COPIA del juego. Ojo: si las carpetas de la copia son enlaces (junction) a las de Steam, copiar ahí escribe en Steam.

## D. Antes de publicar

17. Busca el inglés en lo ARMADO, no en el original. En los .bin, la cadena inglesa vieja sigue en el archivo aunque ya no se use. Cuenta solo las cadenas a las que todavía apunta un puntero.
18. Compara con el juego ORIGINAL: misma lista de archivos dentro de cada .par, mismas imágenes y del mismo tamaño, mismos nombres en cada .msg, mismas filas de subtítulos. Así sabes que no se perdió nada (herramientas/comparar_original.py del proyecto).
19. Si publicas herramientas para que otros corrijan, comprueba que sin cambios dan EXACTAMENTE el mismo texto que tu paquete. Si no, quien las use deshace tu versión.
20. Deja por escrito lo que queda en inglés y por qué: carpetas numeradas por formato (imágenes, textos, vídeos).

## E. Coherencia con el español oficial de la saga

21. Algunos relanzamientos traen español LATINOAMERICANO oficial: Yakuza Kiwami y Kiwami 2 (versión nueva, no «Legacy»), Yakuza Kiwami 3 & Dark Ties y Yakuza 0 Director's Cut. Like a Dragon, Infinite Wealth, Lost Judgment y Pirate Yakuza solo traen español de España.
22. Para sacar términos oficiales hay que emparejar inglés y español del mismo juego, solo leyendo, sin modificarlo. - Kiwami R y Yakuza 0 DC: carpetas wdr_par_<letra> (c = inglés, l = latino, s = España) y tablas en db.nex/en|ls|es (Yakuza 0: db.gld). Los .msg se emparejan registro a registro. - Kiwami 2 R: db.par/<idioma>/ (en, esl = latino, ese = España). - Kiwami 3: db.bis.en.par / db.bis.esl.par.
23. Las TABLAS no se pueden emparejar por el orden de las cadenas: el orden cambia entre idiomas (salía «Baseball» -> «Salero»). Léelas con reARMP y empareja por FILA y COLUMNA. Ojo: reARMP guarda el .json en la carpeta desde la que se ejecuta.
24. Lo que dice lo oficial: - se dejan en inglés los modos de dardos («Cricket», «Count-Up») y las marcas («Don Quijote», «Club SEGA»); - «Heat» es «adrenalina»; - «UFO catcher» es «máquina de regalos»; - «Hostess/Host» es «Acompañante». Cambia solo TÉRMINOS (oficios de los NPC, minijuegos, menús, objetos, sistema de combate). El estilo de los diálogos es de cada traducción.

