# -*- coding: utf-8 -*-
"""
Izriše rešene uganke v slike PNG za poročilo.

Za vsako datoteko porocilo/podatki/<ime>_resitev.txt poišče izvorno uganko
v mapi example/ in nariše mrežo (voda temna, otoki svetli, številke) v
porocilo/podatki/<ime>.png. Zahteva knjižnico Pillow.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logika

# Barvna shema (usklajena z aplikacijo)
BARVA_OTOK = (255, 248, 231)    # krem
BARVA_VODA = (58, 58, 58)       # temno siva
BARVA_CRTA = (176, 176, 176)    # svetlo siva
BARVA_STEV = (0, 0, 0)          # črna
CELICA = 36                      # velikost celice v pikslih
ROB = 8                          # zunanji rob slike


def narisi(uganka, mreza, pot_slike):
    """Nariše uganko z rešitvijo in jo shrani kot PNG."""
    sirina = uganka.stolpci * CELICA + 2 * ROB
    visina = uganka.vrstice * CELICA + 2 * ROB
    slika = Image.new('RGB', (sirina, visina), (255, 255, 255))
    risar = ImageDraw.Draw(slika)
    try:
        pisava = ImageFont.truetype('arial.ttf', int(CELICA * 0.55))
    except OSError:
        pisava = ImageFont.load_default()

    for r in range(uganka.vrstice):
        for c in range(uganka.stolpci):
            x0 = ROB + c * CELICA
            y0 = ROB + r * CELICA
            barva = BARVA_VODA if mreza[r][c] == logika.VODA else BARVA_OTOK
            risar.rectangle([x0, y0, x0 + CELICA, y0 + CELICA],
                            fill=barva, outline=BARVA_CRTA)
            n = uganka.stevilke[r][c]
            if n > 0:
                risar.text((x0 + CELICA / 2, y0 + CELICA / 2), str(n),
                           fill=BARVA_STEV, font=pisava, anchor='mm')
    slika.save(pot_slike)


def main():
    koren = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mapa_primeri = os.path.join(koren, 'example')
    mapa_podatki = os.path.join(koren, 'porocilo', 'podatki')

    for datoteka in sorted(os.listdir(mapa_podatki)):
        if not datoteka.endswith('_resitev.txt'):
            continue
        ime = datoteka[:-len('_resitev.txt')]
        # poišči izvorno uganko (z ali brez končnice .txt)
        pot_uganke = os.path.join(mapa_primeri, ime + '.txt')
        if not os.path.exists(pot_uganke):
            pot_uganke = os.path.join(mapa_primeri, ime)
        if not os.path.exists(pot_uganke):
            print('Ni izvorne uganke za %s, preskočim.' % ime)
            continue
        uganka = logika.nalozi_uganko(pot_uganke)
        mreza = logika.nalozi_resitev(os.path.join(mapa_podatki, datoteka))
        pot_slike = os.path.join(mapa_podatki, ime + '.png')
        narisi(uganka, mreza, pot_slike)
        print('Narisano:', pot_slike)


if __name__ == '__main__':
    main()
