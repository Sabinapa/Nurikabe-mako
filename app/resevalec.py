"""
Reševalec ugank Nurikabe: propagacija omejitev + sestopanje (backtracking).
"""

import sys
import time
from collections import deque

try:
    from logika import NEZNANO, OTOK, VODA, preveri_resitev
except ImportError:  # zagon iz korena projekta (import app.resevalec)
    from app.logika import NEZNANO, OTOK, VODA, preveri_resitev

# Interne oznake celic (vrednosti >= 0 pomenijo indeks otoka)
NEZ = -1   # neznana celica
VOD = -2   # voda
BEL = -3   # bela celica (otok), ki še nima določenega lastnika


class Protislovje(Exception):
    """Stanje krši pravila Nurikabe - vejo iskanja je treba opustiti."""

class PotekCasa(Exception):
    """Časovna omejitev reševanja je potekla."""

class _Naloga:
    """Nespremenljivi podatki o uganki: dimenzije, sosedje, številke."""

    def __init__(self, uganka):
        self.V = uganka.vrstice
        self.S = uganka.stolpci
        self.N = self.V * self.S
        self.velikosti = []   # zahtevana velikost vsakega otoka
        self.zacetki = []     # indeks celice s številko za vsak otok
        for r, c, n in uganka.seznam_stevilk():
            self.zacetki.append(r * self.S + c)
            self.velikosti.append(n)
        self.skupaj_otok = sum(self.velikosti)
        self.skupaj_voda = self.N - self.skupaj_otok
        # vnaprej izračunani seznami ortogonalnih sosedov
        self.sos = []
        for r in range(self.V):
            for c in range(self.S):
                s = []
                if r > 0:
                    s.append((r - 1) * self.S + c)
                if r < self.V - 1:
                    s.append((r + 1) * self.S + c)
                if c > 0:
                    s.append(r * self.S + c - 1)
                if c < self.S - 1:
                    s.append(r * self.S + c + 1)
                self.sos.append(tuple(s))
        # vsi kvadrati 2x2 (četverke indeksov)
        self.kvadrati = []
        for r in range(self.V - 1):
            for c in range(self.S - 1):
                i = r * self.S + c
                self.kvadrati.append((i, i + 1, i + self.S, i + self.S + 1))


class _Stanje:
    """Spremenljivo stanje mreže med reševanjem."""

    __slots__ = ('nal', 'mreza', 'celice')

    def __init__(self, nal):
        self.nal = nal
        self.mreza = [NEZ] * nal.N
        self.celice = [set() for _ in nal.velikosti]  # celice vsakega otoka

    def kopiraj(self):
        novo = _Stanje.__new__(_Stanje)
        novo.nal = self.nal
        novo.mreza = self.mreza[:]
        novo.celice = [set(c) for c in self.celice]
        return novo

    # -- osnovne nastavitve celic (z zaznavo protislovij) -------------------

    def voda(self, i):
        v = self.mreza[i]
        if v == VOD:
            return False
        if v != NEZ:
            raise Protislovje  # celica je že bela/otok
        self.mreza[i] = VOD
        return True

    def bela(self, i):
        v = self.mreza[i]
        if v == VOD:
            raise Protislovje
        if v != NEZ:
            return False  # že bela ali že dodeljena otoku
        self.mreza[i] = BEL
        return True

    def otok(self, i, k):
        v = self.mreza[i]
        if v == k:
            return False
        if v == VOD or v >= 0:
            raise Protislovje  # voda ali že last drugega otoka
        self.mreza[i] = k
        self.celice[k].add(i)
        if len(self.celice[k]) > self.nal.velikosti[k]:
            raise Protislovje  # otok je prevelik
        return True



# Pravila propagacije (vsako vrne True, če je kaj spremenilo)

def _lastniki_sosedov(st):
    """Za vsako celico izračuna lastnika sosednjih otoških celic:
    -1 = noben sosed ni otok, k >= 0 = vsi otoški sosedi pripadajo otoku k,
    -9 = sosedje pripadajo vsaj dvema različnima otokoma."""

    nal = st.nal
    last = [-1] * nal.N
    mreza = st.mreza
    for i in range(nal.N):
        k = mreza[i]
        if k >= 0:
            for j in nal.sos[i]:
                l = last[j]
                if l == -1:
                    last[j] = k
                elif l != k:
                    last[j] = -9
    return last


def _pravilo_sosedstva(st):
    """
    Celica ob dveh različnih otokih je voda;
    bela celica ob natanko enem
    otoku se temu otoku pridruži;
    dotik dveh otokov je protislovje.
    """

    sprem = False
    last = _lastniki_sosedov(st)
    for i in range(st.nal.N):
        v = st.mreza[i]
        if v == NEZ:
            if last[i] == -9:
                sprem |= st.voda(i)
        elif v == BEL:
            if last[i] == -9:
                raise Protislovje  # bela celica bi povezala dva otoka
            if last[i] >= 0:
                if st.otok(i, last[i]):
                    # lastništvo se je spremenilo -> tabela last ni več
                    # veljavna, zato pravilo takoj prekinemo
                    return True
        elif v >= 0:
            if last[i] == -9 or (last[i] >= 0 and last[i] != v):
                raise Protislovje  # dva otoka se dotikata
    return sprem


def _pravilo_otokov(st):
    """Dokončan otok obda z vodo; nedokončan otok z eno samo možnostjo
    širitve se razširi tja, brez možnosti je protislovje."""

    sprem = False
    nal = st.nal
    last = _lastniki_sosedov(st)
    for k, cel in enumerate(st.celice):
        if len(cel) == nal.velikosti[k]:
            # dokončan otok: vsi sosedje so voda
            for i in cel:
                for j in nal.sos[i]:
                    v = st.mreza[j]
                    if v == NEZ:
                        sprem |= st.voda(j)
                    elif v == BEL or (v >= 0 and v != k):
                        raise Protislovje
        else:
            kandidati = set()
            for i in cel:
                for j in nal.sos[i]:
                    v = st.mreza[j]
                    if (v == NEZ or v == BEL) and last[j] in (-1, k):
                        kandidati.add(j)
            if not kandidati:
                raise Protislovje  # otok se nima kam širiti
            if len(kandidati) == 1:
                if st.otok(kandidati.pop(), k):
                    return True  # tabela last ni več veljavna
    return sprem


def _pravilo_2x2(st):
    """Če so v kvadratu 2x2 tri celice voda, četrta ne sme biti voda."""

    sprem = False
    m = st.mreza
    for stiri in st.nal.kvadrati:
        vode = 0
        prosta = -1
        for i in stiri:
            if m[i] == VOD:
                vode += 1
            elif m[i] == NEZ:
                prosta = i
        if vode == 4:
            raise Protislovje
        if vode == 3 and prosta >= 0:
            sprem |= st.bela(prosta)
    return sprem


def _pravilo_stevil(st):
    """Štetje celic: skupno število vode in otoških celic je znano vnaprej,
    zato lahko preostale neznane celice včasih določimo v celoti."""

    nal = st.nal
    m = st.mreza
    voda = 0
    neznane = 0
    for v in m:
        if v == VOD:
            voda += 1
        elif v == NEZ:
            neznane += 1
    beli = nal.N - voda - neznane
    if voda > nal.skupaj_voda or beli > nal.skupaj_otok:
        raise Protislovje
    sprem = False
    if neznane:
        if voda == nal.skupaj_voda:
            for i in range(nal.N):
                if m[i] == NEZ:
                    sprem |= st.bela(i)
        elif beli == nal.skupaj_otok:
            for i in range(nal.N):
                if m[i] == NEZ:
                    sprem |= st.voda(i)
    return sprem


def _pravilo_dosegljivosti(st):
    """
    Večizvorna dosegljivost: celica, ki je noben nedokončan otok ne more
    doseči v okviru preostalega proračuna, mora biti voda.

    Bela celica, ki je nedosegljiva, je protislovje.

    Otok, ki ne more doseči dovolj celic za svojo velikost, je protislovje."""

    nal = st.nal
    m = st.mreza
    last = _lastniki_sosedov(st)
    doseg = [False] * nal.N
    for k, cel in enumerate(st.celice):
        ostane = nal.velikosti[k] - len(cel)
        if ostane <= 0:
            continue
        globina = dict.fromkeys(cel, 0)
        vrsta = deque(cel)
        while vrsta:
            i = vrsta.popleft()
            g = globina[i]
            if g == ostane:
                continue
            for j in nal.sos[i]:
                if j in globina:
                    continue
                v = m[j]
                # širitev le v celice, ki niso ob drugem otoku
                if (v == NEZ or v == BEL) and (last[j] == -1 or last[j] == k):
                    globina[j] = g + 1
                    doseg[j] = True
                    vrsta.append(j)
        nove = len(globina) - len(cel)
        if nove < ostane:
            raise Protislovje  # otok ne more doseči dovolj celic
        if nove == ostane:
            # otok mora zasesti VSE dosegljive celice; pridružimo tiste
            # neposredno ob otoku, ostale pridejo v naslednjih krogih
            for j, g in globina.items():
                if g == 1 and st.otok(j, k):
                    return True  # lastništvo spremenjeno, last ni veljaven
    sprem = False
    for i in range(nal.N):
        if not doseg[i]:
            v = m[i]
            if v == NEZ:
                sprem |= st.voda(i)
            elif v == BEL:
                raise Protislovje  # bele celice ne more posvojiti noben otok
    return sprem


def _pravilo_vode(st):
    """
    Povezanost vode: vsa voda mora biti povezljiva skozi celice, ki niso
    otok. Območja brez vode, odrezana od vode, morajo biti bela; vodna
    komponenta z eno samo prosto sosedo se mora razširiti skoznjo."""

    nal = st.nal
    m = st.mreza
    sprem = False

    # 1) komponente POTENCIALNE vode (voda ali neznano)
    komp = [-1] * nal.N
    st_komp = 0
    ima_vodo = []   # ali komponenta vsebuje vsaj eno vodno celico
    velikost = []   # število celic komponente
    for z in range(nal.N):
        if (m[z] == VOD or m[z] == NEZ) and komp[z] == -1:
            komp[z] = st_komp
            vrsta = [z]
            voda_tu = False
            cel = 0
            while vrsta:
                i = vrsta.pop()
                cel += 1
                if m[i] == VOD:
                    voda_tu = True
                for j in nal.sos[i]:
                    if komp[j] == -1 and (m[j] == VOD or m[j] == NEZ):
                        komp[j] = st_komp
                        vrsta.append(j)
            ima_vodo.append(voda_tu)
            velikost.append(cel)
            st_komp += 1

    vodnih_komp = [k for k in range(st_komp) if ima_vodo[k]]
    if len(vodnih_komp) > 1:
        raise Protislovje  # voda v dveh nepovezljivih območjih
    if vodnih_komp:
        if velikost[vodnih_komp[0]] < nal.skupaj_voda:
            raise Protislovje  # premalo prostora za vso vodo
        # neznane celice v komponentah brez vode ne morejo biti voda
        for i in range(nal.N):
            if m[i] == NEZ and not ima_vodo[komp[i]]:
                sprem |= st.bela(i)
        # členitvene točke: neznana celica, katere odstranitev bi ločila
        # dva dela z vodo, mora biti voda (voda se mora povezati skoznjo)
        if _clenitvene_vode(st, komp, vodnih_komp[0]):
            return True  # nova voda spremeni komponente

    # 2) komponente DEJANSKE vode in njihove proste sosede
    obisk = [False] * nal.N
    for z in range(nal.N):
        if m[z] == VOD and not obisk[z]:
            obisk[z] = True
            vrsta = [z]
            cel = 0
            proste = set()
            while vrsta:
                i = vrsta.pop()
                cel += 1
                for j in nal.sos[i]:
                    if m[j] == VOD:
                        if not obisk[j]:
                            obisk[j] = True
                            vrsta.append(j)
                    elif m[j] == NEZ:
                        proste.add(j)
            if cel < nal.skupaj_voda:
                # komponenta mora zrasti oz. se povezati z ostalo vodo
                if not proste:
                    raise Protislovje
                if len(proste) == 1:
                    if st.voda(proste.pop()):
                        # nova voda spremeni komponente -> takoj prekinemo,
                        # da jih fiksna točka izračuna znova
                        return True
    return sprem


def _clenitvene_vode(st, komp, ciljna):
    """
    V potencialni vodni komponenti (celice VOD/NEZ) poišče členitvene
    točke (iterativni Tarjanov obhod).

    Neznana celica, katere odstranitev
    bi ločila dva dela z vodo, mora biti voda, saj se mora vsa voda
    povezati skoznjo. Vrne True, če je bila kakšna celica določena.
    """

    nal = st.nal
    m = st.mreza
    koren = -1
    skupna = 0  # število vodnih celic v komponenti
    for i in range(nal.N):
        if komp[i] == ciljna:
            if koren < 0:
                koren = i
            if m[i] == VOD:
                skupna += 1
    if koren < 0 or skupna == 0:
        return False

    disc = {koren: 0}
    low = {koren: 0}
    voda_pod = {koren: 1 if m[koren] == VOD else 0}
    prisilne = set()
    koren_otroci_z_vodo = 0
    cas = 1
    sklad = [(koren, -1, iter(nal.sos[koren]))]
    while sklad:
        u, oce, it = sklad[-1]
        napredek = False
        for v in it:
            if komp[v] != ciljna:
                continue
            if v not in disc:
                disc[v] = low[v] = cas
                cas += 1
                voda_pod[v] = 1 if m[v] == VOD else 0
                sklad.append((v, u, iter(nal.sos[v])))
                napredek = True
                break
            if v != oce and disc[v] < low[u]:
                low[u] = disc[v]
        if not napredek:
            sklad.pop()
            if oce == -1:
                continue
            if low[u] < low[oce]:
                low[oce] = low[u]
            if oce == koren:
                if voda_pod[u] > 0:
                    koren_otroci_z_vodo += 1
            elif (low[u] >= disc[oce] and voda_pod[u] > 0 and
                    skupna - voda_pod[u] - (1 if m[oce] == VOD else 0) > 0 and
                    m[oce] == NEZ):
                prisilne.add(oce)
            voda_pod[oce] += voda_pod[u]
    if m[koren] == NEZ and koren_otroci_z_vodo >= 2:
        prisilne.add(koren)

    sprem = False
    for i in prisilne:
        sprem |= st.voda(i)
    return sprem


def _propagiraj(st):
    """Vsa pravila ponavlja do fiksne točke; cenejša pravila imajo
    prednost, dražja (dosegljivost, voda) pridejo na vrsto šele, ko se
    cenejša umirijo."""

    while True:
        if _pravilo_sosedstva(st):
            continue
        if _pravilo_otokov(st):
            continue
        if _pravilo_2x2(st):
            continue
        if _pravilo_stevil(st):
            continue
        if _pravilo_dosegljivosti(st):
            continue
        if _pravilo_vode(st):
            continue
        return



# Iskanje s sestopanjem

def _preizkusi_kandidate(st, rok):
    """Enonivojsko preizkušanje (failed literal): za vsako kandidatno
    celico ob nedokončanem otoku preizkusi obe možnosti (voda / otok).

    Če ena od njiju po propagaciji takoj vodi v protislovje, se v stanju
    uveljavi druga.

    Kandidat ob otoku k je lahko le voda ali del otoka k,
    zato je sklepanje zanesljivo. Ponavlja, dokler kaj prisili."""

    nal = st.nal
    while True:
        last = _lastniki_sosedov(st)
        pari = []
        for k, cel in enumerate(st.celice):
            if len(cel) == nal.velikosti[k]:
                continue
            for i in cel:
                for j in nal.sos[i]:
                    if st.mreza[j] == NEZ and (last[j] == -1 or last[j] == k):
                        pari.append((j, k))
        napredek = False
        for j, k in pari:
            if rok is not None and time.perf_counter() > rok:
                raise PotekCasa
            if st.mreza[j] != NEZ:
                continue  # med preizkušanjem že določena
            # 1) poskusi celico kot vodo
            poskus = st.kopiraj()
            try:
                poskus.voda(j)
                _propagiraj(poskus)
            except Protislovje:
                # voda odpade -> bela celica ob otoku k pripada otoku k
                st.otok(j, k)
                _propagiraj(st)
                napredek = True
                continue
            # 2) poskusi celico kot del otoka k
            poskus = st.kopiraj()
            try:
                poskus.otok(j, k)
                _propagiraj(poskus)
            except Protislovje:
                # otok odpade -> celica je voda
                st.voda(j)
                _propagiraj(st)
                napredek = True
        if not napredek:
            return


def _isci(st, rok):
    """
    Rekurzivno iskanje: propagacija + preizkušanje, izbira otoka z
    najmanj kandidati, dvojiška vejitev na eni kandidatni celici.

    Vrne končno stanje ali sproži Protislovje.
    """

    if rok is not None and time.perf_counter() > rok:
        raise PotekCasa
    _propagiraj(st)
    _preizkusi_kandidate(st, rok)
    nal = st.nal
    last = _lastniki_sosedov(st)

    # izberi nedokončan otok z najmanjšim številom možnosti širitve
    # (ob izenačenju tistega, ki mu manjka najmanj celic)
    izbrani = -1
    izbrani_kand = None
    izbrani_ostane = 0
    for k, cel in enumerate(st.celice):
        ostane = nal.velikosti[k] - len(cel)
        if ostane == 0:
            continue
        kand = set()
        for i in cel:
            for j in nal.sos[i]:
                v = st.mreza[j]
                if (v == NEZ or v == BEL) and (last[j] == -1 or last[j] == k):
                    kand.add(j)
        if (izbrani_kand is None or len(kand) < len(izbrani_kand) or
                (len(kand) == len(izbrani_kand) and ostane < izbrani_ostane)):
            izbrani, izbrani_kand, izbrani_ostane = k, kand, ostane

    if izbrani_kand is None:
        # vsi otoki dokončani: preostale neznane celice so nujno voda
        for i in range(nal.N):
            v = st.mreza[i]
            if v == NEZ:
                st.voda(i)
            elif v == BEL:
                raise Protislovje  # bela celica brez otoka
        _propagiraj(st)  # končna preverjanja (2x2, povezanost vode)
        return st

    # dvojiška vejitev na enem kandidatu: celica ob otoku je bodisi voda
    # bodisi del tega otoka. Izberemo kandidata z največ vodnimi sosedi
    # in najprej preizkusimo vodo (voda je v mreži pogostejša).
    j = min(izbrani_kand,
            key=lambda x: (-sum(1 for s in nal.sos[x] if st.mreza[s] == VOD), x))
    veja = st.kopiraj()
    try:
        veja.voda(j)
        return _isci(veja, rok)
    except Protislovje:
        pass
    st.otok(j, izbrani)  # izvirno stanje lahko spremenimo, ker prve veje ni
    return _isci(st, rok)



# vmesnik
def resi(uganka, casovna_omejitev=None):
    """Reši uganko Nurikabe.

    Vrne 2D seznam vrednosti 'I'/'W' ali None, če rešitve ni oziroma je
    potekla časovna omejitev (v sekundah)."""
    rok = None
    if casovna_omejitev is not None:
        rok = time.perf_counter() + casovna_omejitev

    nal = _Naloga(uganka)
    if nal.skupaj_otok > nal.N:
        return None

    staro_omejitev = sys.getrecursionlimit()
    sys.setrecursionlimit(max(staro_omejitev, 4 * nal.N + 1000))
    try:
        st = _Stanje(nal)
        for k, i in enumerate(nal.zacetki):
            st.otok(i, k)
        koncno = _isci(st, rok)
    except (Protislovje, PotekCasa):
        return None
    finally:
        sys.setrecursionlimit(staro_omejitev)

    mreza = [[VODA if koncno.mreza[r * nal.S + c] == VOD else OTOK
              for c in range(nal.S)]
             for r in range(nal.V)]
    veljavna, _ = preveri_resitev(uganka, mreza)
    return mreza if veljavna else None


# predpomnilnik rešitev za namige, ključ je vsebina uganke
_predpomnilnik = {}


def namig(uganka, mreza):
    """
    Vrne namig (vrstica, stolpec, vrednost) ali None.

    Najprej popravi celico, ki jo je uporabnik nastavil napačno;
    sicer razkrije eno neznano celico.

    None, če rešitve ni ali je mreža že v celoti pravilna.

    Rešitev se predpomni glede na vsebino uganke.
    """

    kljuc = tuple(tuple(v) for v in uganka.stevilke)
    if kljuc in _predpomnilnik:
        resitev = _predpomnilnik[kljuc]
    else:
        resitev = resi(uganka)
        _predpomnilnik[kljuc] = resitev
    if resitev is None:
        return None

    # 1) napačno nastavljena celica uporabnika
    for r in range(uganka.vrstice):
        for c in range(uganka.stolpci):
            v = mreza[r][c]
            if v in (OTOK, VODA) and v != resitev[r][c]:
                return (r, c, resitev[r][c])
    # 2) razkrij eno neznano celico
    for r in range(uganka.vrstice):
        for c in range(uganka.stolpci):
            if mreza[r][c] == NEZNANO:
                return (r, c, resitev[r][c])
    return None
