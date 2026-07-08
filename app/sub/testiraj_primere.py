# -*- coding: utf-8 -*-
"""
Skripta, ki reši vse testne primere iz mape example/ in izmeri čase.

Za vsako datoteko (razen datotek z rešitvami, ki imajo v imenu 'resitev'):
 - naloži uganko,
 - jo reši z resevalec.resi in izmeri čas (time.perf_counter),
 - rešitev preveri z logika.preveri_resitev,
 - rešitev shrani v porocilo/podatki/<ime>_resitev.txt.

Na koncu izpiše tabelo rezultatov in jih zapiše v
porocilo/podatki/rezultati.json.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logika
import resevalec

KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPA_PRIMEROV = os.path.join(KOREN, 'example')
MAPA_PODATKOV = os.path.join(KOREN, 'porocilo', 'podatki')


def main():
    os.makedirs(MAPA_PODATKOV, exist_ok=True)

    datoteke = sorted(
        d for d in os.listdir(MAPA_PRIMEROV)
        if 'resitev' not in d.lower()
        and os.path.isfile(os.path.join(MAPA_PRIMEROV, d)))

    rezultati = []
    glava = "%-24s %10s %12s %10s %10s" % (
        "Datoteka", "Velikost", "St. stevilk", "Cas [s]", "Veljavna")
    print(glava)
    print("-" * len(glava))

    for d in datoteke:
        pot = os.path.join(MAPA_PRIMEROV, d)
        uganka = logika.nalozi_uganko(pot)
        stevilke = len(uganka.seznam_stevilk())

        zacetek = time.perf_counter()
        mreza = resevalec.resi(uganka)
        cas = time.perf_counter() - zacetek

        if mreza is None:
            veljavna = False
            oznaka = "ni resitve"
        else:
            veljavna, _ = logika.preveri_resitev(uganka, mreza)
            oznaka = "da" if veljavna else "NE"
            # rešitev shranimo v porocilo/podatki/<ime>_resitev.txt
            ime = d[:-4] if d.lower().endswith('.txt') else d
            logika.shrani_resitev(
                os.path.join(MAPA_PODATKOV, ime + '_resitev.txt'), mreza)

        rezultati.append({
            'datoteka': d,
            'vrstice': uganka.vrstice,
            'stolpci': uganka.stolpci,
            'stevilo_stevilk': stevilke,
            'cas_s': round(cas, 4),
            'veljavna': veljavna,
        })
        print("%-24s %10s %12d %10.4f %10s" % (
            d, "%dx%d" % (uganka.vrstice, uganka.stolpci),
            stevilke, cas, oznaka))

    pot_json = os.path.join(MAPA_PODATKOV, 'rezultati.json')
    with open(pot_json, 'w', encoding='utf-8') as f:
        json.dump(rezultati, f, ensure_ascii=False, indent=2)
    print("\nRezultati zapisani v %s" % pot_json)

    if all(r['veljavna'] for r in rezultati):
        print("Vse uganke uspesno resene in veljavne.")
    else:
        neuspele = [r['datoteka'] for r in rezultati if not r['veljavna']]
        print("OPOZORILO: neuspesne uganke: %s" % ", ".join(neuspele))


if __name__ == '__main__':
    main()
