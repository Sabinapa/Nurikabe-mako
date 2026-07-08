# Arhitektura aplikacije Nurikabe

## Struktura datotek
```
main.py                 – vstopna točka (zažene GUI)
app/logika.py           – model uganke, branje/pisanje txt, preverjanje pravil (OBSTAJA, NE SPREMINJAJ)
app/resevalec.py        – reševalec (propagacija + sestopanje) in namigi
app/vmesnik.py          – tkinter GUI (glavni zaslon, igranje, ustvarjanje)
app/testiraj_primere.py – skripta, ki reši vse primere iz example/ in izmeri čase
example/                – testne uganke (txt)
porocilo/podatki/       – rezultati testov, slike za poročilo
```

## Kontrakt: app/logika.py (že implementirano)
- Konstante stanj celic: `NEZNANO = '.'`, `OTOK = 'I'`, `VODA = 'W'`
- `class Uganka`: atributi `stevilke` (2D int, 0=prazno), `vrstice`, `stolpci`;
  metode `prazna_mreza()`, `seznam_stevilk() -> [(r, c, n), ...]`
- `nalozi_uganko(pot) -> Uganka` (ValueError ob napačnem formatu)
- `shrani_uganko(pot, uganka)`
- `nalozi_resitev(pot) -> 2D seznam 'I'/'W'/'.'`
- `shrani_resitev(pot, mreza)`
- `preveri_resitev(uganka, mreza) -> (bool, sporocilo_str)`

## Kontrakt: app/resevalec.py
- `resi(uganka, casovna_omejitev=None) -> mreza ali None`
  (mreza = 2D seznam 'I'/'W'; None če ni rešitve ali potek časa; omejitev v sekundah)
- `namig(uganka, mreza) -> (r, c, vrednost) ali None`
  (najprej popravi napačno celico uporabnika, sicer razkrije eno neznano;
   None če ni rešitve ali je mreža že cela pravilna; rešitev naj se interno
   predpomni glede na vsebino uganke)

## Kontrakt: app/vmesnik.py
- `zazeni()` – odpre glavno okno aplikacije
- `main.py` samo pokliče `vmesnik.zazeni()` (doda app/ v sys.path)

## Barvna shema (preprosto, ena glavna barva)
- Glavna barva:  #2A7F7F (teal) – gumbi, naslovi, poudarki
- Temnejša:      #1F5F5F – hover/aktivno
- Ozadje:        #F5F5F2 – svetlo
- Mreža: bela polja, otok = bela/krem #FFF8E7, voda = temno siva #3A3A3A,
  črte mreže #B0B0B0, številke črne, pisava Arial

## Pravila Nurikabe (za referenco)
1. Vsaka celica je otok (belo) ali voda (črno).
2. Vsaka številka pripada natanko enemu otoku s točno toliko celicami.
3. Vsak otok vsebuje natanko eno številko.
4. Otoki se med seboj ne dotikajo vodoravno/navpično (diagonalno se smejo).
5. Vsa voda je povezana v eno območje.
6. Nikjer ni polnega kvadrata 2x2 vode.

## Zagon
- Python: C:\Users\sabin\FERI\Magisterij\Nurikabe\.venv\Scripts\python.exe
- Aplikacija: `python main.py`
- Testi: `python app/testiraj_primere.py`
