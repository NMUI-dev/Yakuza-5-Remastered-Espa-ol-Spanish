# -*- coding: utf-8 -*-
"""(01-11-2026, claude1) Aplica a los lotes los cambios ELEGIDOS de cambios_v103.json (terminos_v103.py): textos que
dejamos en inglés y la saga traduce. Se descartan nombres de personajes, interjecciones de estilo, marcas reales y los
lotes de IMÁGENES (311-325, 368-369: eso es redibujar, va aparte). Deja la lista aplicada en trabajo/saga/aplicados_v103.json.
  python herramientas/aplicar_v103.py"""
import json, os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(R, 'trabajo'); L = os.path.join(T, 'lotes')
SI = {   # inglés -> español (el oficial, retocado si hacía falta: espacio normal en vez de duro)
    'Devil Killer': 'Asesino demoníaco', 'Beginner': 'Principiante', "The Premium Malt's Draft": "The Premium Malt's de barril",
    'The Kaku Highball': 'Whisky soda con Kaku', 'Suntory Old Whisky': 'Whisky Suntory Old', 'Espresso': 'Expreso',
    'Marlin': 'Marlín', '500 Yen': '500 yenes', '1,000 Yen': '1,000 yenes', '5,000 Yen': '5,000 yenes',
    '10,000 Yen': '10,000 yenes', '30,000 Yen': '30,000 yenes', 'Triple Ron': 'Ron triple', 'Triple Yakuman': 'Yakuman triple',
    '4x Yakuman': 'Yakuman cuádruple', '5x Yakuman': 'Yakuman quíntuple', '6x Yakuman': 'Yakuman séxtuple',
    '7x Yakuman': 'Yakuman séptuple', 'Dragon Palace': 'Palacio del Dragón', 'Hide': 'Ocultar', 'Battle': 'Combate',
    'Bartender': 'Cantinero', 'Mama': 'Mamá', '*hic*': '¡Hip!', 'Date': 'Fecha', 'M Store Kamurocho': 'Tienda M Kamurocho',
    'M Store Sotenbori': 'Tienda M Sotenbori', 'M Store Shofukucho': 'Tienda M Shofukucho', 'Mach Bowl': 'Bolos Mach',
    'Le Marche': 'Le Marché', 'Little Asia': 'Pequeña Asia'}
IMAGENES = set(range(311, 326)) | {368, 369}


def main():
    cambios = json.load(open(os.path.join(T, 'saga', 'cambios_v103.json'), encoding='utf-8'))
    por = {}
    for c in cambios:
        k = c['en'].strip()
        if k in SI and c['lote'] not in IMAGENES: por.setdefault(c['lote'], []).append((c['id'], c['antes'], SI[k], k))
    hechos = []
    for n, lst in sorted(por.items()):
        p = os.path.join(L, f'lote_{n:03d}_es.json'); es = json.load(open(p, encoding='utf-8'))
        for i, antes, despues, en in lst:
            if es.get(str(i), '').strip() != antes.strip(): continue                    # cambió por otro lado: no tocar
            fin = es[str(i)][len(es[str(i)].rstrip()):]                                 # mismos espacios al final
            es[str(i)] = despues + fin; hechos.append({'lote': n, 'id': i, 'en': en, 'antes': antes, 'despues': despues})
        json.dump(es, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    json.dump(hechos, open(os.path.join(T, 'saga', 'aplicados_v103.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('aplicados', len(hechos), 'en', len(por), 'lotes; sin usar de la lista:', sorted(set(SI) - {h['en'] for h in hechos}))


if __name__ == '__main__': main()
