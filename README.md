# Nurikabe

Aplikacija za igranje in samodejno reševanje logične uganke Nurikabe, napisana v Pythonu (tkinter).

## Zagon

Aplikacija ne potrebuje nobenih zunanjih knjižnic — deluje s čistim standardnim Pythonom (3.10+) in vgrajenim modulom `tkinter`.

```
python main.py
```

ali v PyCharmu: odpri `main.py` in poženi (Shift+F10).

Ob zagonu se odpre glavni meni z gumboma **Uvozi uganko** in **Ustvari uganko**.

## Pravila igre Nurikabe

Mreža je razdeljena na celice s številkami in prazne celice. Vsako celico je treba označiti kot **otok** (belo) ali **vodo** (črno) po naslednjih pravilih:

1. Vsaka celica je otok ali voda.
2. Vsaka številka pripada natanko enemu otoku, ki ima točno toliko celic, kolikor pove številka.
3. Vsak otok vsebuje natanko eno številko.
4. Otoki se med seboj ne dotikajo vodoravno ali navpično (diagonalno se smejo).
5. Vsa voda je povezana v eno samo območje.
6. Nikjer ni polnega kvadrata 2×2 vode.

## Kako se igra

- **Uvozi uganko** — odpre raziskovalca datotek za izbiro txt datoteke z uganko; ta se izriše v mreži.
- Klik na prazno celico:
  - **levi klik** → otok,
  - **desni klik** → voda,
  - **dvojni klik** → nazaj na prazno (neznano).
- Celice s podanimi številkami niso urejalne.
- Med igranjem teče časovnik; ko je mreža v celoti zapolnjena, se rešitev samodejno preveri in ob pravilnosti se prikaže čestitka.
- Na voljo so gumbi:
  - **Namig** — popravi napačno označeno celico ali razkrije eno neznano celico,
  - **Počisti** — povrne začetno stanje uganke,
  - **Reši takoj** — samodejno reši celotno uganko (reševanje teče v ozadju) in izpiše čas reševanja,
  - **Uvozi rešitev** / **Izvozi rešitev** — nalaganje in shranjevanje rešitve v txt,
  - **Nazaj** — vrnitev na glavni meni.
- **Ustvari uganko** — izbereš dimenzije mreže, jo ustvariš in vpišeš svoje številke; uganko lahko izvoziš v txt ali jo takoj zaigraš.

## Format datotek

**Uganka (txt):** vrstice s celimi števili, ločenimi s presledki; `0` pomeni prazno celico, drugo število pomeni zahtevano velikost otoka. Vrstice, ki se začnejo z `#`, so komentarji.

```
# Nurikabe uganka 5x5
0 0 0 0 0
0 0 0 0 0
0 0 3 0 0
0 0 0 3 0
4 0 0 0 0
```

**Rešitev (txt):** enaka oblika, le da so vrednosti `I` (otok) in `W` (voda).

```
# Nurikabe rešitev 5x5
W W W W W
I W I I W
I W I W W
I W W I W
I W I I W
```

## Zasnova reševalnika

Reševalnik (`app/resevalec.py`) združuje **propagacijo omejitev** in **sestopanje (backtracking)**.

**Propagacija omejitev** iz že znanega stanja mreže po pravilih igre sproti izpelje vse celice, katerih vrednost je logično nujna (npr. okolica dokončanega otoka je voda, celica med dvema otokoma je voda, celica, ki je noben otok ne more doseči, je voda, kvadrat 2×2 ne sme biti ves voda, voda mora ostati povezana ...). Pravila se ponavljajo, dokler se karkoli še spreminja.

Ko propagacija ne najde več novih sklepov, program uporabi **sestopanje**: predpostavi vrednost neke celice in nadaljuje, ob protislovju pa se vrne nazaj in poskusi drugače. Pred vejitvijo se uporabi poskusno preverjanje (če ena vrednost pripelje do protislovja, je nasprotna dokazano pravilna), veja pa se po otoku z najmanj možnostmi širitve. Vsaka najdena rešitev se pred vrnitvijo še enkrat preveri z vsemi šestimi pravili.

Funkcija za namige uporabi isti reševalnik in si rešitev predpomni glede na vsebino uganke.

## Struktura projekta

```
main.py                 – vstopna točka, zažene grafični vmesnik
app/logika.py           – model uganke, branje/pisanje txt, preverjanje pravil
app/resevalec.py        – reševalnik (propagacija + sestopanje) in namigi
app/vmesnik.py          – grafični vmesnik (tkinter): meni, igranje, ustvarjanje
app/testiraj_primere.py – reši vse primere iz example/ in izmeri čase
example/                – testne uganke (txt)
porocilo/               – poročilo in podatki za oddajo
```

## Testiranje

```
python app/testiraj_primere.py
```

Skripta reši vse uganke v mapi `example/`, preveri pravilnost vsake rešitve in zapiše čase v `porocilo/podatki/rezultati.json`.
