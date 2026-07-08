
"""
Tkinter grafični vmesnik aplikacije Nurikabe.

Aplikacija uporablja eno samo glavno okno
posamezni zasloni (glavni meni, igranje/uvoz, ustvarjanje uganke) so izvedeni kot okvirji (tk.Frame), ki se
med seboj izmenjujejo.
"""

import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox

import logika
import resevalec


# Barvna shema in skupne nastavitve
BARVA_GLAVNA = '#2A7F7F'   # glavna barva: gumbi, naslovi, poudarki
BARVA_TEMNA = '#1F5F5F'    # temnejša različica za aktivne gumbe
BARVA_OZADJE = '#F5F5F2'   # svetlo ozadje
BARVA_OTOK = '#FFF8E7'     # krem polja otokov in celic s številkami
BARVA_VODA = '#3A3A3A'     # temna vodna polja
BARVA_CRTE = '#B0B0B0'     # črte mreže
BARVA_SIVA = '#808080'     # podnaslovi in manj pomembna besedila
PISAVA = 'Arial'

TIPI_DATOTEK = [("Besedilne datoteke", "*.txt"), ("Vse datoteke", "*.*")]

NAJVECJE_PLATNO = 700      # največja stranica platna v pikslih
NAJMANJSA_CELICA = 22      # najmanjša velikost celice v pikslih
NAJVECJA_CELICA = 52       # največja velikost celice (za majhne uganke)


def _gumb(nadrejeni, besedilo, ukaz, **dodatno):
    """Ustvari ploščat gumb v glavni barvi z belim besedilom."""
    dodatno.setdefault('font', (PISAVA, 11))
    dodatno.setdefault('padx', 14)
    dodatno.setdefault('pady', 6)
    return tk.Button(nadrejeni, text=besedilo, command=ukaz,
                     bg=BARVA_GLAVNA, fg='white',
                     activebackground=BARVA_TEMNA, activeforeground='white',
                     relief='flat', bd=0, cursor='hand2', **dodatno)


class GlavniZaslon(tk.Frame):
    """Glavni meni z naslovom in gumboma za uvoz oz. ustvarjanje uganke."""

    def __init__(self, nadrejeni, app):
        super().__init__(nadrejeni, bg=BARVA_OZADJE)
        tk.Label(self, text="Nurikabe", font=(PISAVA, 40, 'bold'),
                 fg=BARVA_GLAVNA, bg=BARVA_OZADJE).pack(pady=(80, 0))
        tk.Label(self, text="Mako", font=(PISAVA, 14),
                 fg=BARVA_SIVA, bg=BARVA_OZADJE).pack(pady=(0, 50))
        _gumb(self, "Uvozi uganko", app.uvozi_uganko, width=20).pack(pady=8)
        _gumb(self, "Ustvari uganko", app.pokazi_ustvari, width=20).pack(pady=8)


class ZaslonIgre(tk.Frame):
    """Zaslon za igranje: mreža na platnu, časovnik in gumbi z dejanji."""

    def __init__(self, nadrejeni, app, uganka):
        super().__init__(nadrejeni, bg=BARVA_OZADJE)
        self.app = app
        self.uganka = uganka
        self.mreza = self._zacetna_mreza()
        self.resena = False           # ali je bil konec igre že potrjen
        self.resevanje_tece = False   # ali reševalec teče v ozadju
        self.odlozeni_klik = None     # after-id odloženega levega klika

        # velikost celice izračunamo tako, da cela mreža stane na platno
        najvec = max(uganka.vrstice, uganka.stolpci)
        self.celica = max(NAJMANJSA_CELICA,
                          min(NAJVECJA_CELICA, NAJVECJE_PLATNO // najvec))
        self.odmik = 2

        # vrstica s časovnikom (levo) in statusom reševanja (desno)
        info = tk.Frame(self, bg=BARVA_OZADJE)
        info.pack(fill='x', padx=16, pady=(12, 4))
        self.lbl_cas = tk.Label(info, text="Čas igranja: 00:00",
                                font=(PISAVA, 11), fg=BARVA_TEMNA, bg=BARVA_OZADJE)
        self.lbl_cas.pack(side='left')
        self.lbl_status = tk.Label(info, text="", font=(PISAVA, 11, 'bold'),
                                   fg=BARVA_GLAVNA, bg=BARVA_OZADJE)
        self.lbl_status.pack(side='right')

        sirina = uganka.stolpci * self.celica + 2 * self.odmik
        visina = uganka.vrstice * self.celica + 2 * self.odmik
        self.platno = tk.Canvas(self, width=sirina, height=visina,
                                bg=BARVA_OZADJE, highlightthickness=0)
        self.platno.pack(padx=16, pady=4)
        self.platno.bind('<Button-1>', self._levi_klik)
        self.platno.bind('<Double-Button-1>', self._dvojni_klik)
        self.platno.bind('<Button-3>', self._desni_klik)

        tk.Label(self, text="Levi klik: otok  ·  Desni klik: voda  ·  Dvojni klik: prazno",
                 font=(PISAVA, 10), fg=BARVA_SIVA, bg=BARVA_OZADJE).pack(pady=(2, 0))

        vrstica_gumbov = tk.Frame(self, bg=BARVA_OZADJE)
        vrstica_gumbov.pack(pady=(10, 16))
        self.gumbi = []
        dejanja = [("Namig", self._namig),
                   ("Počisti", self._pocisti),
                   ("Reši takoj", self._resi_takoj),
                   ("Uvozi rešitev", self._uvozi_resitev),
                   ("Izvozi rešitev", self._izvozi_resitev),
                   ("Nazaj", self._nazaj)]
        for besedilo, ukaz in dejanja:
            gumb = _gumb(vrstica_gumbov, besedilo, ukaz,
                         font=(PISAVA, 10), padx=10, pady=5)
            gumb.pack(side='left', padx=4)
            self.gumbi.append(gumb)

        self._narisi_mrezo()

        # časovnik igranja teče od naložitve uganke
        self.zacetek = time.perf_counter()
        self.casovnik_tece = True
        self._utrip_casovnika()

    def _zacetna_mreza(self):
        """Vrne začetno mrežo: celice s številkami so že označene kot otoki."""
        mreza = self.uganka.prazna_mreza()
        for r, c, _ in self.uganka.seznam_stevilk():
            mreza[r][c] = logika.OTOK
        return mreza

    ###### risanje

    def _narisi_mrezo(self):
        """Nariše celotno mrežo glede na trenutno stanje."""
        self.platno.delete('all')
        velikost_pisave = max(10, int(self.celica * 0.45))
        for r in range(self.uganka.vrstice):
            for c in range(self.uganka.stolpci):
                x0 = self.odmik + c * self.celica
                y0 = self.odmik + r * self.celica
                x1, y1 = x0 + self.celica, y0 + self.celica
                stevilka = self.uganka.stevilke[r][c]
                stanje = self.mreza[r][c]

                if stevilka > 0 or stanje == logika.OTOK:
                    barva = BARVA_OTOK
                elif stanje == logika.VODA:
                    barva = BARVA_VODA
                else:
                    barva = 'white'
                self.platno.create_rectangle(x0, y0, x1, y1,
                                             fill=barva, outline=BARVA_CRTE)

                if stevilka > 0:
                    # celica s številko (ne moremo urejati)
                    self.platno.create_text((x0 + x1) // 2, (y0 + y1) // 2,
                                            text=str(stevilka), fill='black',
                                            font=(PISAVA, velikost_pisave, 'bold'))
                elif stanje == logika.OTOK:
                    # majhna pika, da se otok loči od nedotaknjenega belega polja
                    polmer = max(2, self.celica // 8)
                    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
                    self.platno.create_oval(cx - polmer, cy - polmer,
                                            cx + polmer, cy + polmer,
                                            fill=BARVA_GLAVNA, outline='')

    def _poudari_celico(self, r, c):
        """Za kratek čas obrobi celico z glavno barvo (prikaz namiga)."""
        x0 = self.odmik + c * self.celica
        y0 = self.odmik + r * self.celica
        self.platno.create_rectangle(x0 + 2, y0 + 2,
                                     x0 + self.celica - 2, y0 + self.celica - 2,
                                     outline=BARVA_GLAVNA, width=3, tags='poudarek')
        self.after(1200, self._odstrani_poudarek)

    def _odstrani_poudarek(self):
        if self.platno.winfo_exists():
            self.platno.delete('poudarek')

    #### časovnik
    def _utrip_casovnika(self):
        if not self.winfo_exists() or not self.casovnik_tece:
            return
        sekunde = int(time.perf_counter() - self.zacetek)
        self.lbl_cas.config(text="Čas igranja: %02d:%02d" % (sekunde // 60, sekunde % 60))
        self.after(1000, self._utrip_casovnika)

    ### miškini dogodki

    def _celica_iz_tock(self, x, y):
        """Vrne (r, c) celice pod točko ali None, če je zunaj mreže."""
        c = (x - self.odmik) // self.celica
        r = (y - self.odmik) // self.celica
        if 0 <= r < self.uganka.vrstice and 0 <= c < self.uganka.stolpci:
            return r, c
        return None

    def _preklici_odlozeni_klik(self):
        if self.odlozeni_klik is not None:
            self.after_cancel(self.odlozeni_klik)
            self.odlozeni_klik = None

    def _levi_klik(self, dogodek):
        poz = self._celica_iz_tock(dogodek.x, dogodek.y)
        if poz is None:
            return
        # klik odložimo, ker dvojni klik najprej sproži enojnega
        self._preklici_odlozeni_klik()
        self.odlozeni_klik = self.after(
            220, lambda: self._odlozen_otok(poz[0], poz[1]))

    def _odlozen_otok(self, r, c):
        self.odlozeni_klik = None
        self._nastavi_celico(r, c, logika.OTOK)

    def _dvojni_klik(self, dogodek):
        self._preklici_odlozeni_klik()
        poz = self._celica_iz_tock(dogodek.x, dogodek.y)
        if poz is not None:
            self._nastavi_celico(poz[0], poz[1], logika.NEZNANO)

    def _desni_klik(self, dogodek):
        poz = self._celica_iz_tock(dogodek.x, dogodek.y)
        if poz is not None:
            self._nastavi_celico(poz[0], poz[1], logika.VODA)

    def _nastavi_celico(self, r, c, stanje):
        """Nastavi stanje celice (če lahko urejamo) in preveri konec igre."""
        if self.resevanje_tece or self.uganka.stevilke[r][c] > 0:
            return
        self.mreza[r][c] = stanje
        self._narisi_mrezo()
        self._preveri_konec()

    #### konec igre

    def _mreza_polna(self):
        return all(celica != logika.NEZNANO
                   for vrsta in self.mreza for celica in vrsta)

    def _preveri_konec(self):
        """Če je mreža polna in pravilna, čestita in ustavi časovnik."""
        if self.resena or not self._mreza_polna():
            return
        veljavna, _ = logika.preveri_resitev(self.uganka, self.mreza)
        if veljavna:
            self.resena = True
            self.casovnik_tece = False
            messagebox.showinfo("Nurikabe", "Čestitke! Uganka je pravilno rešena.")

    #### gumbi
    def _namig(self):
        rezultat = resevalec.namig(self.uganka, self.mreza)
        if rezultat is None:
            if self._mreza_polna() and logika.preveri_resitev(self.uganka, self.mreza)[0]:
                messagebox.showinfo("Namig", "Uganka je že pravilno rešena.")
            else:
                messagebox.showerror("Napaka", "Namig ni na voljo: uganka ni rešljiva.")
            return
        r, c, vrednost = rezultat
        self.mreza[r][c] = vrednost
        self._narisi_mrezo()
        self._poudari_celico(r, c)
        self._preveri_konec()

    def _pocisti(self):
        """Ponastavi mrežo na začetno stanje in znova zažene časovnik."""
        self.mreza = self._zacetna_mreza()
        self.resena = False
        self.lbl_status.config(text="")
        self._narisi_mrezo()
        self.zacetek = time.perf_counter()
        if not self.casovnik_tece:
            self.casovnik_tece = True
            self._utrip_casovnika()

    def _resi_takoj(self):
        """Zažene reševalec v niti v ozadju, da se vmesnik ne zamrzne."""
        if self.resevanje_tece:
            return
        self.resevanje_tece = True
        for gumb in self.gumbi:
            gumb.config(state='disabled')
        self.lbl_status.config(text="Rešujem ...")

        rezultat = {}

        def delo():
            zacetek = time.perf_counter()
            try:
                rezultat['mreza'] = resevalec.resi(self.uganka)
            except Exception as napaka:
                rezultat['mreza'] = None
                rezultat['napaka'] = str(napaka)
            rezultat['cas'] = time.perf_counter() - zacetek

        nit = threading.Thread(target=delo, daemon=True)
        nit.start()
        self._pocakaj_resevanje(nit, rezultat)

    def _pocakaj_resevanje(self, nit, rezultat):
        """Periodično preverja, ali je nit reševalca končala."""
        if not self.winfo_exists():
            return
        if nit.is_alive():
            self.after(100, lambda: self._pocakaj_resevanje(nit, rezultat))
            return
        self.resevanje_tece = False
        for gumb in self.gumbi:
            gumb.config(state='normal')
        if rezultat.get('mreza') is None:
            self.lbl_status.config(text="")
            messagebox.showerror(
                "Napaka",
                rezultat.get('napaka') or "Reševalcu ni uspelo najti rešitve.")
            return
        self.mreza = [list(vrsta) for vrsta in rezultat['mreza']]
        self.resena = True
        self.casovnik_tece = False
        self._narisi_mrezo()
        self.lbl_status.config(text="Rešeno v %.3f s" % rezultat['cas'])

    def _uvozi_resitev(self):
        pot = filedialog.askopenfilename(title="Uvozi rešitev", filetypes=TIPI_DATOTEK)
        if not pot:
            return
        try:
            mreza = logika.nalozi_resitev(pot)
        except (ValueError, OSError) as napaka:
            messagebox.showerror("Napaka pri uvozu", str(napaka))
            return
        if (len(mreza) != self.uganka.vrstice or
                any(len(vrsta) != self.uganka.stolpci for vrsta in mreza)):
            messagebox.showerror("Napaka", "Dimenzije rešitve se ne ujemajo z uganko.")
            return
        self.mreza = mreza
        self.resena = False
        self.lbl_status.config(text="")
        self._narisi_mrezo()
        self._preveri_konec()

    def _izvozi_resitev(self):
        pot = filedialog.asksaveasfilename(title="Izvozi rešitev",
                                           defaultextension=".txt",
                                           filetypes=TIPI_DATOTEK)
        if not pot:
            return
        try:
            logika.shrani_resitev(pot, self.mreza)
        except OSError as napaka:
            messagebox.showerror("Napaka pri izvozu", str(napaka))

    def _nazaj(self):
        self.casovnik_tece = False
        self.app.pokazi_meni()


class ZaslonUstvari(tk.Frame):
    """Zaslon za ustvarjanje nove uganke z mrežo vnosnih polj."""

    def __init__(self, nadrejeni, app):
        super().__init__(nadrejeni, bg=BARVA_OZADJE)
        self.app = app
        self.vnosi = None  # 2D seznam Entry gradnikov (None, dokler mreže ni)

        tk.Label(self, text="Ustvari uganko", font=(PISAVA, 20, 'bold'),
                 fg=BARVA_GLAVNA, bg=BARVA_OZADJE).pack(pady=(24, 12))

        nastavitve = tk.Frame(self, bg=BARVA_OZADJE)
        nastavitve.pack(pady=4)
        tk.Label(nastavitve, text="Vrstice:", font=(PISAVA, 11),
                 bg=BARVA_OZADJE).pack(side='left')
        self.var_vrstice = tk.StringVar(value='10')
        tk.Spinbox(nastavitve, from_=3, to=30, width=4, justify='center',
                   textvariable=self.var_vrstice,
                   font=(PISAVA, 11)).pack(side='left', padx=(4, 16))
        tk.Label(nastavitve, text="Stolpci:", font=(PISAVA, 11),
                 bg=BARVA_OZADJE).pack(side='left')
        self.var_stolpci = tk.StringVar(value='10')
        tk.Spinbox(nastavitve, from_=3, to=30, width=4, justify='center',
                   textvariable=self.var_stolpci,
                   font=(PISAVA, 11)).pack(side='left', padx=(4, 16))
        _gumb(nastavitve, "Ustvari mrežo", self._ustvari_mrezo,
              font=(PISAVA, 10), padx=10, pady=4).pack(side='left')

        # ob tipkanju dovolimo samo prazno celico ali nenegativno celo število
        self.preveri_vnos = (self.register(lambda p: p == '' or p.isdigit()), '%P')

        self.okvir_mreze = tk.Frame(self, bg=BARVA_OZADJE)
        self.okvir_mreze.pack(pady=12)

        gumbi = tk.Frame(self, bg=BARVA_OZADJE)
        gumbi.pack(pady=(4, 20))
        _gumb(gumbi, "Izvozi txt", self._izvozi).pack(side='left', padx=4)
        _gumb(gumbi, "Igraj to uganko", self._igraj).pack(side='left', padx=4)
        _gumb(gumbi, "Nazaj", app.pokazi_meni).pack(side='left', padx=4)

    def _ustvari_mrezo(self):
        try:
            vrstice = int(self.var_vrstice.get())
            stolpci = int(self.var_stolpci.get())
        except ValueError:
            messagebox.showerror("Napaka", "Vrstice in stolpci morajo biti celi števili.")
            return
        if not (3 <= vrstice <= 30 and 3 <= stolpci <= 30):
            messagebox.showerror("Napaka", "Vrstice in stolpci morajo biti med 3 in 30.")
            return
        for gradnik in self.okvir_mreze.winfo_children():
            gradnik.destroy()
        self.vnosi = []
        for r in range(vrstice):
            vrsta = []
            for c in range(stolpci):
                vnos = tk.Entry(self.okvir_mreze, width=3, justify='center',
                                font=(PISAVA, 10), relief='solid', bd=1,
                                validate='key', validatecommand=self.preveri_vnos)
                vnos.grid(row=r, column=c, padx=1, pady=1)
                vrsta.append(vnos)
            self.vnosi.append(vrsta)

    def _preberi_uganko(self):
        """Sestavi objekt Uganka iz vnosnih polj, ob napaki vrne None."""
        if not self.vnosi:
            messagebox.showerror("Napaka", "Najprej ustvari mrežo.")
            return None
        stevilke = []
        for vrsta in self.vnosi:
            vrstica = []
            for vnos in vrsta:
                besedilo = vnos.get().strip()
                if besedilo == '':
                    vrstica.append(0)  # prazna celica pomeni 0
                else:
                    try:
                        vrstica.append(int(besedilo))
                    except ValueError:
                        messagebox.showerror(
                            "Napaka",
                            "Celice morajo biti prazne ali vsebovati cela števila.")
                        return None
            stevilke.append(vrstica)
        return logika.Uganka(stevilke)

    def _izvozi(self):
        uganka = self._preberi_uganko()
        if uganka is None:
            return
        pot = filedialog.asksaveasfilename(title="Izvozi uganko",
                                           defaultextension=".txt",
                                           filetypes=TIPI_DATOTEK)
        if not pot:
            return
        try:
            logika.shrani_uganko(pot, uganka)
        except OSError as napaka:
            messagebox.showerror("Napaka pri izvozu", str(napaka))

    def _igraj(self):
        uganka = self._preberi_uganko()
        if uganka is not None:
            self.app.pokazi_igro(uganka)


class Aplikacija:
    """Upravlja glavno okno in preklapljanje med zasloni."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Nurikabe")
        self.root.configure(bg=BARVA_OZADJE)
        self.root.minsize(480, 420)
        self.zaslon = None

    def _pokazi(self, zaslon):
        """Zamenja trenutni zaslon z novim."""
        if self.zaslon is not None:
            self.zaslon.destroy()
        self.zaslon = zaslon
        zaslon.pack(fill='both', expand=True)

    def pokazi_meni(self):
        self._pokazi(GlavniZaslon(self.root, self))

    def pokazi_igro(self, uganka):
        self._pokazi(ZaslonIgre(self.root, self, uganka))

    def pokazi_ustvari(self):
        self._pokazi(ZaslonUstvari(self.root, self))

    def uvozi_uganko(self):
        """Odpre pogovorno okno za izbiro datoteke in začne igro."""
        pot = filedialog.askopenfilename(title="Uvozi uganko", filetypes=TIPI_DATOTEK)
        if not pot:
            return
        try:
            uganka = logika.nalozi_uganko(pot)
        except (ValueError, OSError) as napaka:
            messagebox.showerror("Napaka pri uvozu", str(napaka))
            return
        self.pokazi_igro(uganka)


def zazeni():
    """Odpre glavno okno aplikacije Nurikabe."""
    app = Aplikacija()
    app.pokazi_meni()
    app.root.mainloop()
