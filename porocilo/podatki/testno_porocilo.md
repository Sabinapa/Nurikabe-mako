# Testno poročilo — aplikacija Nurikabe

Datum testiranja: 6. 7. 2026
Okolje: Windows 11, Python 3.10 (`.venv`), tkinter, Pillow

Testirane komponente: `app/logika.py`, `app/resevalec.py`, `app/vmesnik.py`,
`app/testiraj_primere.py`, `app/naredi_slike.py`.

## 1. Reševalec (`app/testiraj_primere.py`)

Skripta je bila zagnana trikrat zapored. V vseh treh zagonih je bilo vseh
8 ugank iz mape `example/` uspešno rešenih, vsaka rešitev je prestala
`logika.preveri_resitev` (stolpec »Veljavna« = da). Časi so med zagoni
stabilni; shranjena datoteka `rezultati.json` ustreza 3. zagonu.

| Datoteka             | Velikost | Št. številk | Čas 1 [s] | Čas 2 [s] | Čas 3 [s] | Veljavna |
|----------------------|----------|-------------|-----------|-----------|-----------|----------|
| 1.txt                | 5x5      | 3           | 0.0011    | 0.0011    | 0.0011    | da       |
| Nurikabe1-10x10.txt  | 10x10    | 14          | 0.0126    | 0.0133    | 0.0136    | da       |
| Nurikabe2-10x10.txt  | 10x10    | 14          | 0.0455    | 0.0479    | 0.0443    | da       |
| Nurikabe4-10x10.txt  | 10x10    | 15          | 0.0071    | 0.0078    | 0.0076    | da       |
| Nurikabe5-10x10      | 10x10    | 16          | 0.0181    | 0.0205    | 0.0199    | da       |
| nurikabe-primer1.txt | 18x10    | 24          | 0.0246    | 0.0276    | 0.0258    | da       |
| nurikabe-primer2.txt | 24x14    | 37          | 0.2196    | 0.2267    | 0.2136    | da       |
| nurikabe-primer3.txt | 24x14    | 38          | 1.4443    | 1.5376    | 1.5028    | da       |

Najzahtevnejši primer (nurikabe-primer3, 24x14) se reši v približno 1,5 s,
vsi ostali pod 0,25 s. Rešitve so shranjene v `porocilo/podatki/<ime>_resitev.txt`
(8 datotek).

**Rezultat: USPEŠNO (8/8 ugank veljavno rešenih v vseh treh zagonih).**

## 2. Slike rešitev (`app/naredi_slike.py`)

Skripta je ustvarila PNG sliko za vseh 8 rešenih primerov. Vsaka slika je
bila programsko odprta s Pillow in preverjena: dimenzije se natančno ujemajo
s pričakovano velikostjo (stolpci·36 + 16, vrstice·36 + 16 pikslov) in slike
niso prazne (vsebujejo vodna, otoška polja in številke).

| Slika                | Dimenzije | Pričakovano | Stanje |
|----------------------|-----------|-------------|--------|
| 1.png                | 196x196   | 196x196     | OK     |
| Nurikabe1-10x10.png  | 376x376   | 376x376     | OK     |
| Nurikabe2-10x10.png  | 376x376   | 376x376     | OK     |
| Nurikabe4-10x10.png  | 376x376   | 376x376     | OK     |
| Nurikabe5-10x10.png  | 376x376   | 376x376     | OK     |
| nurikabe-primer1.png | 376x664   | 376x664     | OK     |
| nurikabe-primer2.png | 520x880   | 520x880     | OK     |
| nurikabe-primer3.png | 520x880   | 520x880     | OK     |

**Rezultat: USPEŠNO (8/8 slik).**

## 3. Funkcijski testi grafičnega vmesnika

Pravi tkinter vmesnik (`vmesnik.Aplikacija`) je bil voden programsko
(zanka `root.update()`, generiranje miškinih dogodkov na platnu, zamenjani
`messagebox`/`filedialog` za beleženje klicev). Vseh 26 testov je uspelo:

| # | Test | Rezultat |
|---|------|----------|
| 1–8 | »Reši takoj« za vseh 8 primerov: reševalec teče v niti v ozadju, gumbi se med reševanjem onemogočijo, končna mreža prestane `preveri_resitev`, oznaka »Rešeno v X s« se izpiše | PASS (8/8) |
| 9 | Namig na sveže naloženi uganki spremeni natanko eno celico in ta ustreza rešitvi | PASS |
| 10 | Namig najprej popravi namerno napačno označeno celico uporabnika | PASS |
| 11 | »Počisti« povrne začetno stanje (celice s številkami otok, ostalo neznano), pobriše status in znova zažene časovnik | PASS |
| 12 | Levi klik na platno označi otok (z zakasnitvijo 220 ms zaradi dvojnega klika) | PASS |
| 13 | Desni klik označi vodo | PASS |
| 14 | Dvojni klik pobriše celico in prekliče odloženi enojni klik | PASS |
| 15 | Klik na celico s številko se ignorira (ni urejalna) | PASS |
| 16 | »Izvozi rešitev« ustvari txt datoteko | PASS |
| 17 | Krožna pot izvoz → počisti → uvoz povrne isto mrežo; ob polni pravilni mreži se prikaže čestitka | PASS |
| 18 | Uvoz rešitve napačnih dimenzij (3x3 na 10x10 uganko) prikaže »Dimenzije rešitve se ne ujemajo z uganko.« | PASS |
| 19 | Uvoz vsebinsko neveljavne rešitve prikaže »Neveljaven format rešitve …«; aplikacija se ne sesuje | PASS |
| 20 | Uvoz neveljavne uganke (smeti v txt) prikaže »Neveljaven format uganke …«; aplikacija teče naprej | PASS |
| 21 | Preklic pogovornega okna za uvoz ne naredi ničesar | PASS |
| 22 | Zaslon Ustvari: mreža 5x5 vnosnih polj se ustvari | PASS |
| 23 | Ustvari: vnos številk, »Izvozi txt«, ponovno nalaganje — številke se ujemajo | PASS |
| 24 | Ustvari: neveljavne dimenzije (»abc«) prikažejo napako | PASS |
| 25 | »Igraj to uganko« odpre zaslon igre z ustvarjeno uganko | PASS |
| 26 | Ustvarjena uganka se v zaslonu igre uspešno reši z »Reši takoj« | PASS |

**Rezultat: USPEŠNO (26/26 testov).**

### Robni primeri
- Datoteka s smetmi (nenumerične vsebine) pri uvozu uganke in rešitve: obakrat
  slovensko sporočilo o napaki, brez sesutja.
- Rešitev napačnih dimenzij: pravilno zavrnjena s slovenskim sporočilom.
- Preklic pogovornih oken (prazna pot): brez stranskih učinkov.
- Klik izven urejalnih celic (celice s številkami): pravilno ignoriran.
- Datoteka brez končnice `.txt` (`Nurikabe5-10x10`): pravilno obdelana v
  reševalcu in pri risanju slik.

## 4. Zaslonske slike za poročilo

Zajete s pravim oknom aplikacije (PIL.ImageGrab) in vizualno preverjene
(niso prazne, celotno okno vidno):

| Datoteka | Vsebina | Velikost |
|----------|---------|----------|
| zaslon_meni.png | glavni meni (naslov, gumba Uvozi/Ustvari) | 480x420 |
| zaslon_igra.png | igra z Nurikabe1-10x10, nekaj ročno označenih otokov in vode | 704x681 |
| zaslon_reseno.png | nurikabe-primer2 (24x14) po »Reši takoj« z oznako »Rešeno v 0.217 s« | 704x857 |
| zaslon_ustvari.png | zaslon ustvarjanja z mrežo 10x10 in vpisanimi številkami | 484x526 |

## 5. Najdene napake

Ni najdenih napak.

## Končna ocena

**VSI TESTI USPEŠNI**
