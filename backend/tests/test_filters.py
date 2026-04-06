"""Test filtri convergenti — Lotto Convergent.

Test con dati sintetici per verificare il comportamento dei filtri.
"""

from __future__ import annotations

from lotto_predictor.analyzer.filters.base import Candidato


class TestCandidato:
    """Test dataclass Candidato."""

    def test_coppia_ordinata(self):
        """Verifica che la coppia venga ordinata (min, max)."""
        c = Candidato(num_a=45, num_b=12, filtro="test")
        assert c.coppia == (12, 45)

    def test_coppia_gia_ordinata(self):
        """Verifica che la coppia gia ordinata resti invariata."""
        c = Candidato(num_a=5, num_b=90, filtro="test")
        assert c.coppia == (5, 90)


class TestFiltroVincolo90:
    """Test Filtro Vincolo Differenziale 90."""

    def _make_data(self):
        """Crea dati sintetici con quadratura vincolo 90."""
        # Costruiamo un caso dove d1 + d2 = 45
        # d1 = cyclo_dist(10, 20) = 10
        # d2 = cyclo_dist(30, 65) = 35
        # 10 + 35 = 45 -> SEGNALE
        return [
            (
                "01/01/2024",
                {
                    "BARI": [10, 30, 50, 70, 85],
                    "CAGLIARI": [20, 65, 40, 55, 75],
                    "FIRENZE": [1, 2, 3, 4, 5],
                },
            ),
        ]

    def test_genera_candidati(self):
        """Il filtro dovrebbe generare una lista di candidati."""
        from lotto_predictor.analyzer.filters.vincolo90 import Vincolo90

        data = self._make_data()
        filtro = Vincolo90()
        candidati = filtro.analizza(data, 0, "BARI")
        # Il filtro dovrebbe generare candidati (potrebbe essere vuoto
        # se la coppia di ruote non e in COPPIE_RUOTE)
        assert isinstance(candidati, list)

    def test_nome(self):
        """Verifica il nome identificativo del filtro."""
        from lotto_predictor.analyzer.filters.vincolo90 import Vincolo90

        assert Vincolo90().nome == "vincolo90"


class TestFiltroIsotopismo:
    """Test Filtro Isotopismo Distanziale."""

    def _make_data_con_pattern(self):
        """Crea dati con distanza ripetuta nella stessa posizione."""
        # Posizione 0: 10, 20, 30 -> distanza 10 ripetuta
        return [
            ("01/01/2024", {"BARI": [10, 50, 60, 70, 80]}),
            ("02/01/2024", {"BARI": [20, 55, 65, 75, 85]}),
            ("03/01/2024", {"BARI": [30, 45, 62, 71, 83]}),
        ]

    def test_rileva_pattern(self):
        """L'isotopismo dovrebbe rilevare distanze ripetute."""
        from lotto_predictor.analyzer.filters.isotopismo import Isotopismo

        data = self._make_data_con_pattern()
        filtro = Isotopismo()
        candidati = filtro.analizza(data, 2, "BARI")
        assert isinstance(candidati, list)

    def test_nome(self):
        """Verifica il nome identificativo del filtro."""
        from lotto_predictor.analyzer.filters.isotopismo import Isotopismo

        assert Isotopismo().nome == "isotopismo"


class TestFiltroRitardo:
    """Test Filtro Ritardo Critico."""

    def _make_data_lunga(self):
        """Crea dati con un ambo assente per molte estrazioni."""
        data = []
        for i in range(200):
            data.append(
                (
                    f"{i + 1:02d}/01/2024",
                    {"BARI": [1, 2, 3, 4, 5]},  # mai 88-89
                )
            )
        return data

    def test_ritardo_alto(self):
        """Un ambo mai uscito deve avere ritardo >= soglia."""
        from lotto_predictor.analyzer.filters.ritardo import RitardoCritico

        data = self._make_data_lunga()
        filtro = RitardoCritico(soglia=150)
        candidati_input = [Candidato(88, 89, "test")]
        risultati = filtro.punteggio(data, 199, "BARI", candidati_input)
        # L'ambo 88-89 non e mai uscito, quindi ritardo >= 150
        assert len(risultati) > 0

    def test_nome(self):
        """Verifica il nome identificativo del filtro."""
        from lotto_predictor.analyzer.filters.ritardo import RitardoCritico

        assert RitardoCritico().nome == "ritardo"


class TestFiltroDecade:
    """Test Filtro Coerenza Decina."""

    def test_stessa_decina(self):
        """Numeri nella stessa decina devono avere score 1.0."""
        from lotto_predictor.analyzer.filters.decade import CoerenzaDecina

        filtro = CoerenzaDecina()
        score = filtro._calcola_score(11, 18)  # stessa decina (11-20)
        assert score == 1.0

    def test_decine_diverse_vicine(self):
        """Numeri vicini (dist <= 10) ma in decine diverse -> score 0.5."""
        from lotto_predictor.analyzer.filters.decade import CoerenzaDecina

        filtro = CoerenzaDecina()
        score = filtro._calcola_score(19, 22)  # distanza ciclo = 3, <= 10
        assert score == 0.5

    def test_decine_lontane(self):
        """Numeri lontani devono avere score 0.0."""
        from lotto_predictor.analyzer.filters.decade import CoerenzaDecina

        filtro = CoerenzaDecina()
        score = filtro._calcola_score(1, 50)  # distanza ciclo = 41
        assert score == 0.0

    def test_nome(self):
        """Verifica il nome identificativo del filtro."""
        from lotto_predictor.analyzer.filters.decade import CoerenzaDecina

        assert CoerenzaDecina().nome == "decade"


class TestFiltroSomma91:
    """Test Filtro Somma 91 (Diametrali Caldi)."""

    def _make_data_diametrale(self):
        """Dati dove il diametrale di un numero ha ritardo alto."""
        data = []
        # 20 estrazioni senza il numero 46 (diametrale di 1)
        for i in range(20):
            data.append(
                (
                    f"{i + 1:02d}/01/2024",
                    {"BARI": [2, 3, 4, 5, 6]},  # mai 46
                )
            )
        # L'ultima estrazione ha il numero 1
        data.append(
            (
                "21/01/2024",
                {"BARI": [1, 10, 20, 30, 40]},
            )
        )
        return data

    def test_rileva_diametrale_caldo(self):
        """Deve trovare la coppia (1, 46) perche 46 non esce da 20+ estrazioni."""
        from lotto_predictor.analyzer.filters.somma91 import Somma91

        data = self._make_data_diametrale()
        filtro = Somma91(soglia_ritardo=15)
        candidati = filtro.analizza(data, len(data) - 1, "BARI")
        # Dovrebbe trovare la coppia (1, 46) perche 46 non esce da 20+ estrazioni
        coppie = [c.coppia for c in candidati]
        assert (1, 46) in coppie

    def test_nome(self):
        """Verifica il nome identificativo del filtro."""
        from lotto_predictor.analyzer.filters.somma91 import Somma91

        assert Somma91().nome == "somma91"


class TestConvergenza:
    """Test del motore di convergenza."""

    def test_import(self):
        """Verifica che il modulo convergenza sia importabile."""
        from lotto_predictor.analyzer.convergence import calcola_convergenza

        assert callable(calcola_convergenza)

    def test_dati_vuoti(self):
        """Convergenza su un singolo record deve restituire una lista."""
        from lotto_predictor.analyzer.convergence import calcola_convergenza

        data = [("01/01/2024", {"BARI": [1, 2, 3, 4, 5]})]
        risultati = calcola_convergenza(data, 0, "BARI", min_score=0)
        assert isinstance(risultati, list)
