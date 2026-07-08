# Možna stanja posamezne celice v mreži
NEZNANO = '.'   # celica še ni določena
OTOK = 'I'      # celica pripada otoku (belo polje)
VODA = 'W'      # celica pripada vodi (črno polje)


class Uganka:
    """Predstavlja uganko Nurikabe: dimenzije mreže in podane številke."""

    def __init__(self, stevilke):
        # stevilke: 2D seznam celih števil (0 = brez številke)
        self.stevilke = stevilke
        self.vrstice = len(stevilke)
        self.stolpci = len(stevilke[0]) if stevilke else 0

    def prazna_mreza(self):
        """Vrne novo mrežo stanj, kjer so vse celice neznane."""
        return [[NEZNANO] * self.stolpci for _ in range(self.vrstice)]

    def seznam_stevilk(self):
        """Vrne seznam (vrstica, stolpec, vrednost) za vse podane številke."""
        rezultat = []
        for r in range(self.vrstice):
            for c in range(self.stolpci):
                if self.stevilke[r][c] > 0:
                    rezultat.append((r, c, self.stevilke[r][c]))
        return rezultat


def nalozi_uganko(pot):
    """Prebere uganko iz txt datoteke. Vrne objekt Uganka.

    Sproži ValueError, če datoteka ni v veljavnem formatu.
    """
    stevilke = []
    with open(pot, 'r', encoding='utf-8') as f:
        for vrstica in f:
            vrstica = vrstica.strip()
            if not vrstica or vrstica.startswith('#'):
                continue  # preskoči komentarje in prazne vrstice
            deli = vrstica.split()
            try:
                stevilke.append([int(x) for x in deli])
            except ValueError:
                raise ValueError(
                    "Neveljaven format uganke: vrstica '%s' ne vsebuje samo števil." % vrstica)
    if not stevilke:
        raise ValueError("Datoteka ne vsebuje nobene uganke.")
    sirina = len(stevilke[0])
    if any(len(v) != sirina for v in stevilke):
        raise ValueError("Vse vrstice uganke morajo biti enako dolge.")
    return Uganka(stevilke)


def shrani_uganko(pot, uganka):
    """Zapiše uganko v txt datoteko v enotnem formatu."""
    with open(pot, 'w', encoding='utf-8') as f:
        f.write("# Nurikabe uganka %dx%d\n" % (uganka.vrstice, uganka.stolpci))
        for vrstica in uganka.stevilke:
            f.write(' '.join(str(x) for x in vrstica) + '\n')


def nalozi_resitev(pot):
    """Prebere rešitev (mrežo znakov I/W) iz txt datoteke."""
    mreza = []
    with open(pot, 'r', encoding='utf-8') as f:
        for vrstica in f:
            vrstica = vrstica.strip()
            if not vrstica or vrstica.startswith('#'):
                continue
            deli = vrstica.upper().split()
            if any(d not in (OTOK, VODA, NEZNANO) for d in deli):
                raise ValueError(
                    "Neveljaven format rešitve: dovoljeni so samo znaki I, W in '.'.")
            mreza.append(deli)
    if not mreza:
        raise ValueError("Datoteka ne vsebuje nobene rešitve.")
    sirina = len(mreza[0])
    if any(len(v) != sirina for v in mreza):
        raise ValueError("Vse vrstice rešitve morajo biti enako dolge.")
    return mreza


def shrani_resitev(pot, mreza):
    """Zapiše rešitev (mrežo stanj) v txt datoteko v enotnem formatu."""
    with open(pot, 'w', encoding='utf-8') as f:
        f.write("# Nurikabe rešitev %dx%d\n" % (len(mreza), len(mreza[0])))
        f.write("# I = Otok, W = Voda\n")
        for vrstica in mreza:
            f.write(' '.join(vrstica) + '\n')


def _sosedje(r, c, vrstice, stolpci):
    """Vrne ortogonalne sosede celice (r, c) znotraj mreže."""
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < vrstice and 0 <= nc < stolpci:
            yield nr, nc


def preveri_resitev(uganka, mreza):
    """Preveri, ali mreza predstavlja veljavno rešitev uganke.

    Vrne par (veljavna, sporocilo). Če rešitev ni veljavna, sporocilo
    opiše prvo najdeno kršitev pravil.
    """
    V, S = uganka.vrstice, uganka.stolpci
    if len(mreza) != V or any(len(vr) != S for vr in mreza):
        return False, "Dimenzije rešitve se ne ujemajo z uganko."

    # 1. Vse celice morajo biti določene (otok ali voda)
    for r in range(V):
        for c in range(S):
            if mreza[r][c] not in (OTOK, VODA):
                return False, "Celica (%d, %d) še ni določena." % (r + 1, c + 1)

    # 2. Celice s številkami morajo biti otoki
    for r, c, n in uganka.seznam_stevilk():
        if mreza[r][c] != OTOK:
            return False, "Celica s številko %d na (%d, %d) ni otok." % (n, r + 1, c + 1)

    # 3. Nobeno 2x2 območje ne sme biti v celoti voda
    for r in range(V - 1):
        for c in range(S - 1):
            if (mreza[r][c] == VODA and mreza[r][c + 1] == VODA and
                    mreza[r + 1][c] == VODA and mreza[r + 1][c + 1] == VODA):
                return False, "Voda tvori kvadrat 2x2 pri (%d, %d)." % (r + 1, c + 1)

    # 4. Vsak otok (povezana skupina celic I) mora vsebovati natanko eno
    #    številko in imeti točno toliko celic, kot pove ta številka.
    obiskano = [[False] * S for _ in range(V)]
    for r in range(V):
        for c in range(S):
            if mreza[r][c] == OTOK and not obiskano[r][c]:
                # poplavno iskanje povezane skupine otoka
                skupina = [(r, c)]
                obiskano[r][c] = True
                i = 0
                while i < len(skupina):
                    cr, cc = skupina[i]
                    i += 1
                    for nr, nc in _sosedje(cr, cc, V, S):
                        if mreza[nr][nc] == OTOK and not obiskano[nr][nc]:
                            obiskano[nr][nc] = True
                            skupina.append((nr, nc))
                stevilke_v_skupini = [uganka.stevilke[cr][cc]
                                      for cr, cc in skupina
                                      if uganka.stevilke[cr][cc] > 0]
                if len(stevilke_v_skupini) == 0:
                    return False, "Otok pri (%d, %d) nima številke." % (r + 1, c + 1)
                if len(stevilke_v_skupini) > 1:
                    return False, "Otok pri (%d, %d) vsebuje več številk." % (r + 1, c + 1)
                if stevilke_v_skupini[0] != len(skupina):
                    return False, ("Otok pri (%d, %d) ima %d celic, "
                                   "moral bi jih imeti %d." %
                                   (r + 1, c + 1, len(skupina), stevilke_v_skupini[0]))

    # 5. Vsa voda mora biti povezana v eno samo območje
    vodne = [(r, c) for r in range(V) for c in range(S) if mreza[r][c] == VODA]
    if vodne:
        obiskano_v = set()
        vrsta = [vodne[0]]
        obiskano_v.add(vodne[0])
        while vrsta:
            cr, cc = vrsta.pop()
            for nr, nc in _sosedje(cr, cc, V, S):
                if mreza[nr][nc] == VODA and (nr, nc) not in obiskano_v:
                    obiskano_v.add((nr, nc))
                    vrsta.append((nr, nc))
        if len(obiskano_v) != len(vodne):
            return False, "Voda ni povezana v eno samo območje."

    return True, "Rešitev je pravilna!"
