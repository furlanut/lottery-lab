"""Test funzioni ciclometriche — Lotto Convergent.

Verifica le proprieta matematiche fondamentali:
- cyclo_dist: simmetria, range, valori noti
- diametrale: involuzione, somma 91
- fuori90: range, idempotenza
- decade, cadenza, figura: valori noti
"""

from lotto_predictor.analyzer.cyclometry import (
    cadenza,
    cyclo_dist,
    decade,
    diametrale,
    figura,
    fuori90,
    is_valid_ambo,
    is_valid_number,
)


class TestCycloDist:
    """Test distanza ciclometrica."""

    def test_simmetria(self):
        """cyclo_dist(a, b) == cyclo_dist(b, a)"""
        for a in range(1, 91):
            for b in range(a, 91):
                assert cyclo_dist(a, b) == cyclo_dist(b, a)

    def test_range(self):
        """Risultato sempre in 0-45."""
        for a in range(1, 91):
            for b in range(1, 91):
                d = cyclo_dist(a, b)
                assert 0 <= d <= 45

    def test_zero(self):
        """Distanza di un numero da se stesso e 0."""
        for n in range(1, 91):
            assert cyclo_dist(n, n) == 0

    def test_valori_noti(self):
        """Valori calcolati a mano."""
        assert cyclo_dist(1, 46) == 45  # diametrali
        assert cyclo_dist(5, 80) == 15  # |5-80|=75, 90-75=15
        assert cyclo_dist(10, 20) == 10
        assert cyclo_dist(1, 90) == 1  # |1-90|=89, 90-89=1
        assert cyclo_dist(45, 46) == 1

    def test_diametrali_distanza_45(self):
        """Coppie diametrali hanno distanza 45."""
        for n in range(1, 46):
            d = diametrale(n)
            assert cyclo_dist(n, d) == 45


class TestDiametrale:
    """Test funzione diametrale."""

    def test_involuzione(self):
        """diametrale(diametrale(n)) == n"""
        for n in range(1, 91):
            assert diametrale(diametrale(n)) == n

    def test_distanza_45(self):
        """Il diametrale e sempre a distanza ciclometrica 45."""
        for n in range(1, 91):
            assert cyclo_dist(n, diametrale(n)) == 45

    def test_range(self):
        """Risultato sempre in 1-90."""
        for n in range(1, 91):
            d = diametrale(n)
            assert 1 <= d <= 90

    def test_valori_noti(self):
        assert diametrale(1) == 46
        assert diametrale(45) == 90
        assert diametrale(46) == 1
        assert diametrale(90) == 45


class TestFuori90:
    """Test riduzione fuori 90."""

    def test_range(self):
        """Risultato sempre in 1-90."""
        for n in range(-180, 271):
            if n == 0:
                continue
            r = fuori90(n)
            assert 1 <= r <= 90, f"fuori90({n}) = {r}"

    def test_idempotenza(self):
        """fuori90(fuori90(n)) == fuori90(n) per numeri gia nel range."""
        for n in range(1, 91):
            assert fuori90(n) == n

    def test_valori_noti(self):
        assert fuori90(91) == 1
        assert fuori90(180) == 90
        assert fuori90(95) == 5
        assert fuori90(90) == 90
        assert fuori90(1) == 1


class TestDecade:
    """Test funzione decade."""

    def test_range(self):
        for n in range(1, 91):
            d = decade(n)
            assert 0 <= d <= 8

    def test_valori_noti(self):
        assert decade(1) == 0
        assert decade(10) == 0
        assert decade(11) == 1
        assert decade(90) == 8
        assert decade(45) == 4


class TestCadenza:
    """Test funzione cadenza."""

    def test_range(self):
        for n in range(1, 91):
            c = cadenza(n)
            assert 0 <= c <= 9

    def test_valori_noti(self):
        assert cadenza(10) == 0
        assert cadenza(11) == 1
        assert cadenza(90) == 0
        assert cadenza(45) == 5


class TestFigura:
    """Test funzione figura (radice digitale)."""

    def test_range(self):
        for n in range(1, 91):
            f = figura(n)
            assert 1 <= f <= 9

    def test_valori_noti(self):
        assert figura(9) == 9
        assert figura(10) == 1
        assert figura(19) == 1  # 1+9=10, 1+0=1
        assert figura(89) == 8  # 8+9=17, 1+7=8
        assert figura(90) == 9


class TestValidazione:
    """Test funzioni di validazione."""

    def test_numeri_validi(self):
        for n in range(1, 91):
            assert is_valid_number(n) is True

    def test_numeri_non_validi(self):
        assert is_valid_number(0) is False
        assert is_valid_number(91) is False
        assert is_valid_number(-1) is False

    def test_ambo_valido(self):
        assert is_valid_ambo(1, 90) is True
        assert is_valid_ambo(45, 46) is True

    def test_ambo_non_valido(self):
        assert is_valid_ambo(1, 1) is False  # stessi numeri
        assert is_valid_ambo(0, 1) is False  # fuori range
        assert is_valid_ambo(1, 91) is False  # fuori range
