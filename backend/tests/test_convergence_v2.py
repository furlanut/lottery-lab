"""Test motore convergenza V2 — Lotto Convergent.

Verifica il segnale vincitore freq+rit+dec e freq+rit+fig
con dati sintetici controllati.
"""

from __future__ import annotations

from lotto_predictor.analyzer.convergence_v2 import (
    analizza_finestra,
    genera_segnali_v2,
    segnale_freq_rit_dec,
    segnale_freq_rit_fig,
)


def _make_data(n_draws=200):
    """Crea dataset sintetico con pattern controllati.

    Inserisce la coppia (11, 18) — stessa decina — in posizioni specifiche
    per testare che il filtro la rilevi correttamente.
    """
    data = []
    for i in range(n_draws):
        nums_bari = [1, 2, 3, 4, 5]  # default

        # La coppia (11, 18) appare ai draw 50, 80, 120
        # Poi NON appare dal draw 120 in poi
        if i in (50, 80, 120):
            nums_bari = [11, 18, 3, 4, 5]

        data.append(
            (
                f"{(i % 28) + 1:02d}/{(i // 28) % 12 + 1:02d}/2024",
                {"BARI": nums_bari, "CAGLIARI": [21, 32, 43, 54, 65]},
            )
        )
    return data


class TestAnalizzaFinestra:
    """Test analisi features nella finestra."""

    def test_conta_frequenze(self):
        data = _make_data(200)
        ctx = analizza_finestra(data, 190, "BARI", finestra=150)
        # La coppia (11, 18) appare ai draw 50, 80, 120
        # Finestra: draw 40-190, quindi include draw 50, 80, 120
        assert ctx["pair_freq"][(11, 18)] >= 2

    def test_pair_last_seen(self):
        data = _make_data(200)
        ctx = analizza_finestra(data, 190, "BARI", finestra=150)
        # L'ultima apparizione di (11, 18) e' al draw 120
        # back = 190 - 120 = 70
        assert ctx["pair_last_seen"][(11, 18)] == 70

    def test_ruota_mancante(self):
        data = [(f"{i:02d}/01/2024", {"BARI": [1, 2, 3, 4, 5]}) for i in range(100)]
        ctx = analizza_finestra(data, 90, "ROMA", finestra=50)
        assert len(ctx["pair_freq"]) == 0


class TestSegnaleFreqRitDec:
    """Test segnale freq+rit+dec."""

    def test_trova_coppia_intra_decina(self):
        data = _make_data(200)
        segnali = segnale_freq_rit_dec(data, 190, "BARI", finestra=150)
        # (11, 18): freq >= 1, ritardo >= 50 (> 150/3=50), stessa decina (1)
        coppie = [s.ambo for s in segnali]
        assert (11, 18) in coppie

    def test_esclude_extra_decina(self):
        # Crea dati dove (1, 50) appare ma e' extra-decina
        data = []
        for i in range(200):
            if i in (50, 80, 120):
                data.append((f"{i:02d}/01/2024", {"BARI": [1, 50, 3, 4, 5]}))
            else:
                data.append((f"{i:02d}/01/2024", {"BARI": [2, 3, 4, 5, 6]}))

        segnali = segnale_freq_rit_dec(data, 190, "BARI", finestra=150)
        coppie = [s.ambo for s in segnali]
        assert (1, 50) not in coppie  # extra-decina, non deve apparire

    def test_esclude_ritardo_basso(self):
        # Coppia che e' uscita di recente (ritardo basso)
        data = []
        for i in range(200):
            if i in (50, 80, 185):  # 185 e' recente
                data.append((f"{i:02d}/01/2024", {"BARI": [11, 18, 3, 4, 5]}))
            else:
                data.append((f"{i:02d}/01/2024", {"BARI": [2, 3, 4, 5, 6]}))

        segnali = segnale_freq_rit_dec(data, 190, "BARI", finestra=150)
        coppie = [s.ambo for s in segnali]
        # Ritardo = 190-185 = 5, soglia = 150/3 = 50, quindi 5 < 50
        assert (11, 18) not in coppie

    def test_metodo_corretto(self):
        data = _make_data(200)
        segnali = segnale_freq_rit_dec(data, 190, "BARI", finestra=150)
        for s in segnali:
            assert s.metodo == "freq+rit+dec"

    def test_finestra_troppo_corta(self):
        data = _make_data(200)
        segnali = segnale_freq_rit_dec(data, 10, "BARI", finestra=150)
        assert segnali == []


class TestSegnaleFreqRitFig:
    """Test segnale freq+rit+fig."""

    def test_trova_stessa_figura(self):
        # 10 e 19 hanno entrambi figura 1 (1+0=1, 1+9=10->1+0=1)
        data = []
        for i in range(200):
            if i in (50, 80, 120):
                data.append((f"{i:02d}/01/2024", {"BARI": [10, 19, 3, 4, 5]}))
            else:
                data.append((f"{i:02d}/01/2024", {"BARI": [2, 3, 4, 5, 6]}))

        segnali = segnale_freq_rit_fig(data, 190, "BARI", finestra=70)
        coppie = [s.ambo for s in segnali]
        # (10, 19): freq >= 1, ritardo = 70, > 70/3=23, stessa figura (1)
        assert (10, 19) in coppie

    def test_metodo_corretto(self):
        data = []
        for i in range(200):
            if i in (50, 80, 120):
                data.append((f"{i:02d}/01/2024", {"BARI": [10, 19, 3, 4, 5]}))
            else:
                data.append((f"{i:02d}/01/2024", {"BARI": [2, 3, 4, 5, 6]}))
        segnali = segnale_freq_rit_fig(data, 190, "BARI", finestra=70)
        for s in segnali:
            assert s.metodo == "freq+rit+fig"


class TestGeneraSegnaliV2:
    """Test funzione principale di generazione."""

    def test_genera_da_dati(self):
        data = _make_data(200)
        risultati = genera_segnali_v2(data, top_n=50)
        assert isinstance(risultati, list)
        # Deve trovare almeno qualche segnale
        assert len(risultati) > 0

    def test_rispetta_top_n(self):
        data = _make_data(200)
        risultati = genera_segnali_v2(data, top_n=5)
        assert len(risultati) <= 5

    def test_dati_vuoti(self):
        risultati = genera_segnali_v2([], top_n=10)
        assert risultati == []

    def test_struttura_risultato(self):
        data = _make_data(200)
        risultati = genera_segnali_v2(data, top_n=5)
        if risultati:
            r = risultati[0]
            assert "ruota" in r
            assert "ambo" in r
            assert "score" in r
            assert "metodo" in r
            assert "frequenza" in r
            assert "ritardo" in r
