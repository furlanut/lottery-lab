"""Test validazione dati — Lotto Convergent."""

from datetime import date

import pytest
from lotto_predictor.ingestor.validator import (
    ValidationError,
    valida_concorso,
    valida_data,
    valida_numeri,
    valida_ruota,
)


class TestValidaNumeri:
    """Test validazione numeri estrazione."""

    def test_numeri_validi(self):
        valida_numeri([1, 45, 67, 23, 89])

    def test_troppi_numeri(self):
        with pytest.raises(ValidationError, match="Attesi 5"):
            valida_numeri([1, 2, 3, 4, 5, 6])

    def test_pochi_numeri(self):
        with pytest.raises(ValidationError, match="Attesi 5"):
            valida_numeri([1, 2, 3])

    def test_fuori_range(self):
        with pytest.raises(ValidationError, match="fuori range"):
            valida_numeri([0, 1, 2, 3, 4])

    def test_fuori_range_alto(self):
        with pytest.raises(ValidationError, match="fuori range"):
            valida_numeri([1, 2, 3, 4, 91])

    def test_duplicati(self):
        with pytest.raises(ValidationError, match="non distinti"):
            valida_numeri([1, 1, 2, 3, 4])


class TestValidaRuota:
    """Test validazione ruota."""

    def test_ruote_valide(self):
        for ruota in [
            "BARI",
            "CAGLIARI",
            "FIRENZE",
            "GENOVA",
            "MILANO",
            "NAPOLI",
            "PALERMO",
            "ROMA",
            "TORINO",
            "VENEZIA",
        ]:
            assert valida_ruota(ruota) == ruota

    def test_case_insensitive(self):
        assert valida_ruota("bari") == "BARI"
        assert valida_ruota("Firenze") == "FIRENZE"

    def test_ruota_non_valida(self):
        with pytest.raises(ValidationError, match="non valida"):
            valida_ruota("NAZIONALE")

    def test_ruota_vuota(self):
        with pytest.raises(ValidationError):
            valida_ruota("")


class TestValidaData:
    """Test validazione data."""

    def test_data_valida(self):
        assert valida_data("31/12/2025") == date(2025, 12, 31)

    def test_data_non_valida(self):
        with pytest.raises(ValidationError, match="non valida"):
            valida_data("32/13/2025")

    def test_formato_errato(self):
        with pytest.raises(ValidationError):
            valida_data("2025-12-31")


class TestValidaConcorso:
    """Test validazione numero concorso."""

    def test_concorso_valido(self):
        assert valida_concorso(208) == 208
        assert valida_concorso("208") == 208

    def test_concorso_zero(self):
        with pytest.raises(ValidationError, match="positivo"):
            valida_concorso(0)

    def test_concorso_non_numerico(self):
        with pytest.raises(ValidationError):
            valida_concorso("abc")
