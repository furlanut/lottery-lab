from __future__ import annotations

"""Test validazione dati — VinciCasa.

Verifica le regole di validazione specifiche VinciCasa:
- 5 numeri distinti nel range 1-40
- Date valide (dal luglio 2014 in poi)
- Concorso positivo
"""

from datetime import date

import pytest
from vincicasa.ingestor.validator import (
    VCValidationError,
    valida_concorso,
    valida_data,
    valida_numeri,
)


class TestValidaNumeri:
    """Test validazione numeri estrazione VinciCasa (1-40)."""

    def test_numeri_validi(self):
        """5 numeri validi nel range 1-40 vengono restituiti ordinati."""
        result = valida_numeri([10, 1, 30, 20, 40])
        assert result == [1, 10, 20, 30, 40]

    def test_numeri_validi_bordi(self):
        """Numeri ai limiti del range (1 e 40) sono accettati."""
        result = valida_numeri([40, 2, 3, 4, 1])
        assert result == [1, 2, 3, 4, 40]

    def test_troppi_numeri(self):
        """6 numeri sollevano VCValidationError."""
        with pytest.raises(VCValidationError, match="Attesi 5"):
            valida_numeri([1, 2, 3, 4, 5, 6])

    def test_pochi_numeri(self):
        """3 numeri sollevano VCValidationError."""
        with pytest.raises(VCValidationError, match="Attesi 5"):
            valida_numeri([1, 2, 3])

    def test_lista_vuota(self):
        """Lista vuota solleva VCValidationError."""
        with pytest.raises(VCValidationError, match="Attesi 5"):
            valida_numeri([])

    def test_fuori_range_zero(self):
        """Il numero 0 e fuori range (minimo e 1)."""
        with pytest.raises(VCValidationError, match="fuori range"):
            valida_numeri([0, 1, 2, 3, 4])

    def test_fuori_range_41(self):
        """Il numero 41 e fuori range (massimo e 40)."""
        with pytest.raises(VCValidationError, match="fuori range"):
            valida_numeri([1, 2, 3, 4, 41])

    def test_fuori_range_negativo(self):
        """Numeri negativi sono fuori range."""
        with pytest.raises(VCValidationError, match="fuori range"):
            valida_numeri([-1, 2, 3, 4, 5])

    def test_duplicati(self):
        """Numeri duplicati sollevano VCValidationError."""
        with pytest.raises(VCValidationError, match="non distinti"):
            valida_numeri([1, 1, 2, 3, 4])

    def test_duplicati_multipli(self):
        """Piu duplicati sollevano VCValidationError."""
        with pytest.raises(VCValidationError, match="non distinti"):
            valida_numeri([5, 5, 5, 10, 10])


class TestValidaData:
    """Test validazione data estrazione VinciCasa."""

    def test_data_valida(self):
        """Data valida in formato DD/MM/YYYY viene convertita correttamente."""
        assert valida_data("28/07/2014") == date(2014, 7, 28)

    def test_data_valida_recente(self):
        """Data recente e valida."""
        assert valida_data("01/01/2026") == date(2026, 1, 1)

    def test_data_formato_iso(self):
        """Data in formato ISO YYYY-MM-DD con formato esplicito."""
        assert valida_data("2025-12-31", formato="%Y-%m-%d") == date(2025, 12, 31)

    def test_data_non_valida(self):
        """Data impossibile solleva VCValidationError."""
        with pytest.raises(VCValidationError, match="non valida"):
            valida_data("32/13/2025")

    def test_formato_errato(self):
        """Formato ISO senza specificare il formato solleva errore."""
        with pytest.raises(VCValidationError):
            valida_data("2025-12-31")

    def test_data_vuota(self):
        """Stringa vuota solleva VCValidationError."""
        with pytest.raises(VCValidationError):
            valida_data("")

    def test_data_con_spazi(self):
        """Spazi attorno alla data vengono gestiti correttamente."""
        assert valida_data("  28/07/2014  ") == date(2014, 7, 28)

    def test_data_prima_inizio_vincicasa(self):
        """Data antecedente al luglio 2014 solleva errore."""
        with pytest.raises(VCValidationError, match="antecedente"):
            valida_data("01/01/2010")


class TestValidaConcorso:
    """Test validazione numero concorso VinciCasa."""

    def test_concorso_valido(self):
        """Concorso numerico positivo e accettato."""
        assert valida_concorso(100) == 100

    def test_concorso_stringa(self):
        """Concorso come stringa numerica e convertito."""
        assert valida_concorso("42") == 42

    def test_concorso_zero(self):
        """Concorso zero solleva errore."""
        with pytest.raises(VCValidationError, match="positivo"):
            valida_concorso(0)

    def test_concorso_negativo(self):
        """Concorso negativo solleva errore."""
        with pytest.raises(VCValidationError, match="positivo"):
            valida_concorso(-1)

    def test_concorso_non_numerico(self):
        """Concorso non numerico solleva errore."""
        with pytest.raises(VCValidationError):
            valida_concorso("abc")
