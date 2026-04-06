"""Funzioni ciclometriche — Lotto Convergent.

Implementa le operazioni fondamentali della ciclometria di Fabarri:
distanze, diametrali, riduzione fuori 90, decade, cadenza, figura.

I 90 numeri del Lotto sono disposti su una circonferenza.
La distanza ciclometrica e la distanza minima sull'arco (0-45).
"""

RUOTE = [
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
]

COPPIE_RUOTE = [
    ("BARI", "CAGLIARI"),
    ("BARI", "MILANO"),
    ("CAGLIARI", "FIRENZE"),
    ("FIRENZE", "GENOVA"),
    ("GENOVA", "MILANO"),
    ("MILANO", "NAPOLI"),
    ("NAPOLI", "PALERMO"),
    ("PALERMO", "ROMA"),
    ("ROMA", "TORINO"),
    ("TORINO", "VENEZIA"),
    ("BARI", "NAPOLI"),
    ("FIRENZE", "ROMA"),
]


def cyclo_dist(a: int, b: int) -> int:
    """Distanza ciclometrica tra due numeri (0-45).

    La distanza minima sull'arco della circonferenza di 90 numeri.
    Proprieta: cyclo_dist(a, b) == cyclo_dist(b, a)

    Args:
        a: primo numero (1-90)
        b: secondo numero (1-90)

    Returns:
        Distanza ciclometrica (0-45)
    """
    d = abs(a - b)
    return d if d <= 45 else 90 - d


def diametrale(n: int) -> int:
    """Numero diametralmente opposto sulla circonferenza (somma 91).

    Proprieta: diametrale(diametrale(n)) == n

    Args:
        n: numero (1-90)

    Returns:
        Diametrale (1-90)
    """
    r = (n + 45) % 90
    return r if r != 0 else 90


def fuori90(n: int) -> int:
    """Riduzione al range 1-90.

    Applicata dopo operazioni aritmetiche sui numeri del Lotto.

    Args:
        n: numero da ridurre

    Returns:
        Numero nel range 1-90
    """
    n = n % 90
    return n if n != 0 else 90


def decade(n: int) -> int:
    """Decina di appartenenza (0-8).

    0 = 1-10, 1 = 11-20, ..., 8 = 81-90.

    Args:
        n: numero (1-90)

    Returns:
        Indice della decina (0-8)
    """
    return (n - 1) // 10


def cadenza(n: int) -> int:
    """Cadenza — ultima cifra.

    0 per i multipli di 10 (10, 20, ..., 90).

    Args:
        n: numero (1-90)

    Returns:
        Ultima cifra (0-9)
    """
    return n % 10


def figura(n: int) -> int:
    """Figura — radice digitale (somma iterata delle cifre).

    Riduce un numero a una singola cifra (1-9).

    Args:
        n: numero (1-90)

    Returns:
        Radice digitale (1-9)
    """
    while n >= 10:
        n = sum(int(d) for d in str(n))
    return n


def is_valid_number(n: int) -> bool:
    """Verifica che un numero sia nel range valido del Lotto (1-90)."""
    return isinstance(n, int) and 1 <= n <= 90


def is_valid_ambo(a: int, b: int) -> bool:
    """Verifica che una coppia sia un ambo valido."""
    return is_valid_number(a) and is_valid_number(b) and a != b
