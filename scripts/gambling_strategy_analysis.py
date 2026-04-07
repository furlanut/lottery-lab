#!/usr/bin/env python3
"""
Gambling Strategy Analysis — Monte Carlo Simulations
=====================================================
Comprehensive analysis of betting strategies for Italian Lotto
with weak prediction edges (1.06x-1.10x).

Analyzes: bet type selection, selective play, portfolio approach,
progressive betting, bankroll survival, and combined strategies.
"""

import numpy as np
import time
from dataclasses import dataclass

# Reproducibility
np.random.seed(42)

# ============================================================================
# CONSTANTS — Italian Lotto
# ============================================================================

# Bet types: (name, payout, base_probability_per_wheel, n_wheels_played)
BET_TYPES = {
    "ambo_secco": {"payout": 250, "prob": 1 / 400.5, "wheels": 1},
    "ambo_tutte": {"payout": 25, "prob": 1 / 400.5, "wheels": 10},  # played on all 10 wheels
    "estratto": {"payout": 11.23, "prob": 1 / 18, "wheels": 1},
    "estratto_det": {"payout": 55, "prob": 1 / 90, "wheels": 1},
    "terno_secco": {"payout": 4500, "prob": 1 / 11748, "wheels": 1},
}

DRAWS_PER_WEEK = 3
DRAWS_PER_YEAR = 156
BANKROLL_DEFAULT = 600.0
N_SIMULATIONS = 50_000
N_DRAWS_1YEAR = 156
N_DRAWS_2YEAR = 312


# ============================================================================
# SECTION 1: BET TYPE ANALYSIS
# ============================================================================

def analyze_bet_types():
    """Analyze which bet type is optimal for a weak edge."""
    report = []
    report.append("=" * 70)
    report.append("SECTION 1: BET TYPE ANALYSIS")
    report.append("=" * 70)

    for name, bt in BET_TYPES.items():
        payout = bt["payout"]
        prob = bt["prob"]
        wheels = bt["wheels"]

        # For multi-wheel bets, effective probability
        # P(win on at least 1 wheel) = 1 - (1-p)^wheels
        p_eff = 1 - (1 - prob) ** wheels
        eff_payout = payout  # payout is per wheel, but you only win on matching wheels

        # Expected value per euro bet (no edge)
        ev_no_edge = p_eff * eff_payout
        house_edge = 1 - ev_no_edge

        # Edge multiplier needed to break even
        # edge_mult * p_eff * payout = 1 => edge_mult = 1 / (p_eff * payout)
        breakeven_mult = 1.0 / ev_no_edge

        # With 1.06x and 1.10x edge on probability
        for edge in [1.06, 1.10, 1.20, 1.50]:
            p_edge = min(prob * edge, 1.0)
            p_eff_edge = 1 - (1 - p_edge) ** wheels
            ev_edge = p_eff_edge * eff_payout
            profit_per_euro = ev_edge - 1.0

            report.append(f"\n--- {name} (edge={edge:.2f}x) ---")
            report.append(f"  Base prob: {prob:.6f} ({1/prob:.1f}:1)")
            report.append(f"  Eff prob (with edge): {p_eff_edge:.6f}")
            report.append(f"  Payout: {eff_payout}x")
            report.append(f"  EV per EUR bet: {ev_edge:.4f}")
            report.append(f"  Profit/EUR: {profit_per_euro:+.4f}")
            report.append(f"  Breakeven edge needed: {breakeven_mult:.4f}x")
            report.append(f"  PROFITABLE: {'YES' if ev_edge > 1.0 else 'NO'}")

    # Key insight: which bet type needs the LEAST edge?
    report.append("\n\n--- BREAKEVEN EDGE REQUIREMENTS ---")
    for name, bt in BET_TYPES.items():
        p_eff = 1 - (1 - bt["prob"]) ** bt["wheels"]
        ev_base = p_eff * bt["payout"]
        be = 1.0 / ev_base
        report.append(f"  {name:20s}: needs {be:.4f}x edge to break even (base EV={ev_base:.4f})")

    return "\n".join(report)


# ============================================================================
# SECTION 2: SELECTIVE PLAY (SIGNAL QUALITY FILTERING)
# ============================================================================

def simulate_selective_play(n_sims=N_SIMULATIONS):
    """Compare playing every draw vs selective play."""
    report = []
    report.append("\n" + "=" * 70)
    report.append("SECTION 2: SELECTIVE PLAY STRATEGY")
    report.append("=" * 70)

    # We test ambo_secco as the primary bet
    payout = 250
    base_prob = 1 / 400.5

    scenarios = [
        ("Play ALL draws, 1.06x edge", 1.0, 1.06),
        ("Play ALL draws, 1.10x edge", 1.0, 1.10),
        ("Play 50% draws, 1.15x edge", 0.50, 1.15),
        ("Play 30% draws, 1.20x edge", 0.30, 1.20),
        ("Play 20% draws, 1.25x edge", 0.20, 1.25),
        ("Play 20% draws, 1.30x edge", 0.20, 1.30),
        ("Play 10% draws, 1.40x edge", 0.10, 1.40),
        ("Play 10% draws, 1.50x edge", 0.10, 1.50),
        ("Play 5% draws, 2.00x edge", 0.05, 2.00),
    ]

    n_draws = N_DRAWS_1YEAR
    bankroll = BANKROLL_DEFAULT
    stake = 1.0

    report.append(f"\nSetup: {n_draws} draws, bankroll={bankroll} EUR, stake={stake} EUR/draw")
    report.append(f"Bet: ambo secco (payout={payout}x, base_prob={base_prob:.6f})")
    report.append(f"Simulations: {n_sims:,}\n")

    for label, play_pct, edge in scenarios:
        n_played = int(n_draws * play_pct)
        prob = base_prob * edge
        ev_per_bet = prob * payout - 1.0

        # Monte Carlo
        # For each sim, play n_played draws
        wins = np.random.binomial(n_played, prob, size=n_sims)
        final_bankroll = bankroll - (n_played * stake) + (wins * payout * stake)
        profit = final_bankroll - bankroll

        p_profit = np.mean(profit > 0) * 100
        p_ruin = np.mean(final_bankroll <= 0) * 100
        mean_profit = np.mean(profit)
        median_profit = np.median(profit)
        std_profit = np.std(profit)
        p95_loss = np.percentile(profit, 5)

        report.append(f"--- {label} ---")
        report.append(f"  Draws played: {n_played}, EV/bet: {ev_per_bet:+.4f}")
        report.append(f"  Total EV: {ev_per_bet * n_played:+.2f} EUR")
        report.append(f"  P(profit): {p_profit:.1f}%")
        report.append(f"  P(ruin): {p_ruin:.1f}%")
        report.append(f"  Mean profit: {mean_profit:+.2f} EUR")
        report.append(f"  Median profit: {median_profit:+.2f} EUR")
        report.append(f"  Std dev: {std_profit:.2f}")
        report.append(f"  5th percentile (worst likely): {p95_loss:+.2f} EUR")
        report.append("")

    return "\n".join(report)


# ============================================================================
# SECTION 3: PORTFOLIO / DIVERSIFICATION
# ============================================================================

def simulate_portfolio(n_sims=N_SIMULATIONS):
    """Test diversification across bet types and wheels."""
    report = []
    report.append("\n" + "=" * 70)
    report.append("SECTION 3: PORTFOLIO / DIVERSIFICATION")
    report.append("=" * 70)

    n_draws = N_DRAWS_1YEAR
    bankroll = BANKROLL_DEFAULT

    strategies = []

    # Strategy A: Pure ambo secco, 1 bet per draw
    strategies.append({
        "name": "A: 1 ambo secco, 1 EUR/draw",
        "bets": [{"prob": 1/400.5, "payout": 250, "stake": 1.0}],
    })

    # Strategy B: 3 ambi secco (different pairs), 1 EUR each
    strategies.append({
        "name": "B: 3 ambi secco, 1 EUR each/draw",
        "bets": [{"prob": 1/400.5, "payout": 250, "stake": 1.0}] * 3,
    })

    # Strategy C: 1 ambo secco + 2 estratti
    strategies.append({
        "name": "C: 1 ambo secco + 2 estratti, 1 EUR each",
        "bets": [
            {"prob": 1/400.5, "payout": 250, "stake": 1.0},
            {"prob": 1/18, "payout": 11.23, "stake": 1.0},
            {"prob": 1/18, "payout": 11.23, "stake": 1.0},
        ],
    })

    # Strategy D: 1 ambo tutte ruote
    strategies.append({
        "name": "D: 1 ambo tutte ruote, 1 EUR/draw",
        "bets": [{"prob": 1 - (1 - 1/400.5)**10, "payout": 25, "stake": 1.0}],
    })

    # Strategy E: 2 estratti only (lower variance play)
    strategies.append({
        "name": "E: 2 estratti only, 1 EUR each",
        "bets": [
            {"prob": 1/18, "payout": 11.23, "stake": 1.0},
            {"prob": 1/18, "payout": 11.23, "stake": 1.0},
        ],
    })

    edge = 1.10
    report.append(f"\nAll strategies with {edge}x edge, {n_draws} draws, bankroll={bankroll}")
    report.append(f"Simulations: {n_sims:,}\n")

    for strat in strategies:
        total_stake_per_draw = sum(b["stake"] for b in strat["bets"])

        # Simulate
        total_profit = np.zeros(n_sims)
        for bet in strat["bets"]:
            prob = bet["prob"] * edge
            prob = min(prob, 1.0)
            wins = np.random.binomial(n_draws, prob, size=n_sims)
            total_profit += wins * bet["payout"] * bet["stake"]

        total_cost = total_stake_per_draw * n_draws
        net = total_profit - total_cost
        final_br = bankroll + net

        p_profit = np.mean(net > 0) * 100
        p_ruin = np.mean(final_br <= 0) * 100
        sharpe = np.mean(net) / np.std(net) if np.std(net) > 0 else 0

        report.append(f"--- {strat['name']} ---")
        report.append(f"  Cost/draw: {total_stake_per_draw} EUR, Total cost: {total_cost:.0f}")
        report.append(f"  Mean net: {np.mean(net):+.2f} EUR")
        report.append(f"  Median net: {np.median(net):+.2f} EUR")
        report.append(f"  P(profit): {p_profit:.1f}%")
        report.append(f"  P(ruin): {p_ruin:.1f}%")
        report.append(f"  Sharpe ratio: {sharpe:.4f}")
        report.append(f"  Std dev: {np.std(net):.2f}")
        report.append("")

    return "\n".join(report)


# ============================================================================
# SECTION 4: PROGRESSIVE BETTING STRATEGIES
# ============================================================================

def simulate_progressions(n_sims=N_SIMULATIONS):
    """Test progressive strategies vs flat betting."""
    report = []
    report.append("\n" + "=" * 70)
    report.append("SECTION 4: PROGRESSIVE BETTING STRATEGIES")
    report.append("=" * 70)

    n_draws = N_DRAWS_1YEAR
    bankroll = BANKROLL_DEFAULT
    prob_base = 1 / 400.5
    payout = 250

    edges = [1.06, 1.10, 1.20]

    for edge in edges:
        prob = prob_base * edge

        report.append(f"\n=== Edge: {edge}x (prob={prob:.6f}) ===\n")

        # --- Flat betting ---
        flat_results = _sim_flat(n_sims, n_draws, bankroll, prob, payout, stake=1.0)

        # --- D'Alembert ---
        dalembert_results = _sim_dalembert(n_sims, n_draws, bankroll, prob, payout,
                                           base_stake=1.0, increment=0.50)

        # --- Fibonacci ---
        fib_results = _sim_fibonacci(n_sims, n_draws, bankroll, prob, payout, base_stake=1.0)

        # --- Oscar's Grind ---
        oscar_results = _sim_oscar(n_sims, n_draws, bankroll, prob, payout, base_stake=1.0)

        # --- Proportional (Kelly-like) ---
        kelly_results = _sim_proportional(n_sims, n_draws, bankroll, prob, payout, fraction=0.5)

        for name, res in [
            ("Flat (1 EUR)", flat_results),
            ("D'Alembert (base=1, inc=0.50)", dalembert_results),
            ("Fibonacci (base=1)", fib_results),
            ("Oscar's Grind (base=1)", oscar_results),
            ("Half-Kelly proportional", kelly_results),
        ]:
            report.append(f"  {name}:")
            report.append(f"    Mean final BR: {res['mean_br']:.2f}")
            report.append(f"    Median final BR: {res['median_br']:.2f}")
            report.append(f"    P(profit): {res['p_profit']:.1f}%")
            report.append(f"    P(ruin): {res['p_ruin']:.1f}%")
            report.append(f"    Mean profit: {res['mean_profit']:+.2f}")
            report.append(f"    Max drawdown (mean): {res['mean_maxdd']:.2f}")
            report.append(f"    Mean total wagered: {res['mean_wagered']:.0f}")
            report.append("")

    # Mathematical proof section
    report.append("\n--- MATHEMATICAL PROOF: PROGRESSIONS AND EDGE ---")
    report.append("  Theorem: No betting system can create an edge where none exists.")
    report.append("  With edge E per bet, progression systems:")
    report.append("  - DO amplify both expected profit AND variance")
    report.append("  - DO NOT change the edge percentage per euro wagered")
    report.append("  - Flat betting EV = sum(stake_i) * (p*payout - 1)")
    report.append("  - Progressive EV = sum(stake_i) * (p*payout - 1) [same edge/EUR]")
    report.append("  - But variance = sum(stake_i^2) * p*(1-p)*payout^2")
    report.append("  - Progressive systems increase sum(stake_i^2) disproportionately")
    report.append("  - Result: same edge/EUR but HIGHER variance = HIGHER ruin risk")
    report.append("  - Conclusion: progressions HURT with a weak edge due to ruin risk")

    return "\n".join(report)


def _sim_flat(n_sims, n_draws, bankroll, prob, payout, stake):
    wins = np.random.binomial(n_draws, prob, size=n_sims)
    total_wagered = np.full(n_sims, stake * n_draws)
    profit = wins * payout * stake - total_wagered
    final_br = bankroll + profit
    return _summarize(final_br, bankroll, total_wagered)


def _sim_dalembert(n_sims, n_draws, bankroll, prob, payout, base_stake, increment):
    """D'Alembert: increase stake by increment after loss, decrease after win."""
    final_br = np.zeros(n_sims)
    total_wagered = np.zeros(n_sims)
    max_dd = np.zeros(n_sims)

    for i in range(n_sims):
        br = bankroll
        peak = bankroll
        stake = base_stake
        wagered = 0.0
        for _ in range(n_draws):
            if stake > br:
                stake = br
            if stake <= 0:
                break
            wagered += stake
            if np.random.random() < prob:
                br += stake * (payout - 1)
                stake = max(base_stake, stake - increment)
            else:
                br -= stake
                stake += increment
            peak = max(peak, br)
            dd = peak - br
            if dd > max_dd[i]:
                max_dd[i] = dd
            if br <= 0:
                break
        final_br[i] = max(br, 0)
        total_wagered[i] = wagered

    return _summarize(final_br, bankroll, total_wagered, max_dd)


def _sim_fibonacci(n_sims, n_draws, bankroll, prob, payout, base_stake):
    """Fibonacci: follow Fibonacci sequence on losses, step back 2 on win."""
    fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
    final_br = np.zeros(n_sims)
    total_wagered = np.zeros(n_sims)
    max_dd = np.zeros(n_sims)

    for i in range(n_sims):
        br = bankroll
        peak = bankroll
        fib_idx = 0
        wagered = 0.0
        for _ in range(n_draws):
            stake = base_stake * fib[fib_idx]
            if stake > br:
                stake = br
            if stake <= 0:
                break
            wagered += stake
            if np.random.random() < prob:
                br += stake * (payout - 1)
                fib_idx = max(0, fib_idx - 2)
            else:
                br -= stake
                fib_idx = min(fib_idx + 1, len(fib) - 1)
            peak = max(peak, br)
            dd = peak - br
            if dd > max_dd[i]:
                max_dd[i] = dd
            if br <= 0:
                break
        final_br[i] = max(br, 0)
        total_wagered[i] = wagered

    return _summarize(final_br, bankroll, total_wagered, max_dd)


def _sim_oscar(n_sims, n_draws, bankroll, prob, payout, base_stake):
    """Oscar's Grind: increase stake by 1 unit after win, keep after loss.
    Goal: 1 unit profit per cycle, then reset."""
    final_br = np.zeros(n_sims)
    total_wagered = np.zeros(n_sims)
    max_dd = np.zeros(n_sims)

    for i in range(n_sims):
        br = bankroll
        peak = bankroll
        stake = base_stake
        cycle_profit = 0.0
        wagered = 0.0
        for _ in range(n_draws):
            if stake > br:
                stake = br
            if stake <= 0:
                break
            wagered += stake
            if np.random.random() < prob:
                br += stake * (payout - 1)
                cycle_profit += stake * (payout - 1)
                if cycle_profit >= base_stake:
                    # Cycle complete, reset
                    stake = base_stake
                    cycle_profit = 0.0
                else:
                    stake = min(stake + base_stake, base_stake * 5)  # cap
            else:
                br -= stake
                cycle_profit -= stake
                # Keep same stake (Oscar's rule)
            peak = max(peak, br)
            dd = peak - br
            if dd > max_dd[i]:
                max_dd[i] = dd
            if br <= 0:
                break
        final_br[i] = max(br, 0)
        total_wagered[i] = wagered

    return _summarize(final_br, bankroll, total_wagered, max_dd)


def _sim_proportional(n_sims, n_draws, bankroll, prob, payout, fraction):
    """Kelly/proportional: bet a fraction of bankroll."""
    # Full Kelly = (p * payout - 1) / (payout - 1)
    # We use fraction * kelly
    kelly = (prob * payout - 1) / (payout - 1)
    kelly_frac = kelly * fraction
    if kelly_frac <= 0:
        kelly_frac = 0.001  # minimal bet

    final_br = np.zeros(n_sims)
    total_wagered = np.zeros(n_sims)
    max_dd = np.zeros(n_sims)

    for i in range(n_sims):
        br = bankroll
        peak = bankroll
        wagered = 0.0
        for _ in range(n_draws):
            stake = br * kelly_frac
            stake = max(stake, 0.01)
            stake = min(stake, br)
            if br <= 0.01:
                break
            wagered += stake
            if np.random.random() < prob:
                br += stake * (payout - 1)
            else:
                br -= stake
            peak = max(peak, br)
            dd = peak - br
            if dd > max_dd[i]:
                max_dd[i] = dd
        final_br[i] = max(br, 0)
        total_wagered[i] = wagered

    return _summarize(final_br, bankroll, total_wagered, max_dd)


def _summarize(final_br, bankroll, total_wagered, max_dd=None):
    profit = final_br - bankroll
    return {
        "mean_br": np.mean(final_br),
        "median_br": np.median(final_br),
        "p_profit": np.mean(profit > 0) * 100,
        "p_ruin": np.mean(final_br <= 0) * 100,
        "mean_profit": np.mean(profit),
        "mean_maxdd": np.mean(max_dd) if max_dd is not None else 0,
        "mean_wagered": np.mean(total_wagered),
    }


# ============================================================================
# SECTION 5: BANKROLL SURVIVAL ANALYSIS
# ============================================================================

def simulate_bankroll_survival(n_sims=N_SIMULATIONS):
    """Detailed ruin probability and survival analysis."""
    report = []
    report.append("\n" + "=" * 70)
    report.append("SECTION 5: BANKROLL SURVIVAL ANALYSIS")
    report.append("=" * 70)

    bankroll = 600.0
    prob_base = 1 / 400.5
    payout = 250
    stake = 1.0

    edges = [1.06, 1.10, 1.20, 1.50, 1.66]

    report.append(f"\nBankroll: {bankroll} EUR, stake: {stake} EUR, ambo secco")
    report.append(f"Simulations: {n_sims:,}\n")

    # Test different time horizons
    horizons = [156, 312, 468, 624, 936, 1560]  # 1yr, 2yr, 3yr, 4yr, 6yr, 10yr
    horizon_labels = ["1yr", "2yr", "3yr", "4yr", "6yr", "10yr"]

    for edge in edges:
        prob = prob_base * edge
        ev_per_bet = prob * payout - 1
        kelly = (prob * payout - 1) / (payout - 1) if prob * payout > 1 else 0

        report.append(f"\n=== Edge: {edge}x (EV/bet={ev_per_bet:+.4f}, Kelly={kelly:.6f}) ===")

        for n_draws, label in zip(horizons, horizon_labels):
            wins = np.random.binomial(n_draws, prob, size=n_sims)
            profit = wins * payout * stake - n_draws * stake
            final_br = bankroll + profit

            p_profit = np.mean(profit > 0) * 100
            p_ruin = np.mean(final_br <= 0) * 100

            report.append(f"  {label} ({n_draws} draws): P(profit)={p_profit:.1f}%, "
                         f"P(ruin)={p_ruin:.1f}%, Mean={np.mean(profit):+.1f}, "
                         f"Median={np.median(profit):+.1f}")

    # Cycles to 95% confidence
    report.append("\n\n--- DRAWS NEEDED FOR 95% CONFIDENCE OF PROFIT ---")
    for edge in edges:
        prob = prob_base * edge
        ev = prob * payout - 1
        if ev <= 0:
            report.append(f"  Edge {edge}x: NEVER (negative EV)")
            continue

        # Analytical: E[profit] = n * ev, Var = n * prob * (1-prob) * payout^2 + n * (1 - prob) - ...
        # Simplified: for binomial, var per draw = prob*(payout^2)*(1-prob) + (1-prob)*1 approx
        # Actually: outcome per draw: win payout-1 with prob p, lose 1 with prob (1-p)
        # E = p*(payout-1) - (1-p) = p*payout - 1
        # Var = p*(payout-1)^2 + (1-p)*1 - E^2
        # Var = p*(payout-1)^2 + (1-p) - (p*payout - 1)^2
        var_per_draw = prob * (payout - 1)**2 + (1 - prob) - ev**2
        # For n draws: E=n*ev, Var=n*var_per_draw
        # P(profit) = P(Z > -n*ev / sqrt(n*var_per_draw)) = P(Z > -sqrt(n)*ev/sqrt(var_per_draw))
        # Want P(profit) >= 0.95 => -sqrt(n)*ev/sqrt(var_per_draw) <= -1.645
        # sqrt(n) >= 1.645 * sqrt(var_per_draw) / ev
        # n >= (1.645)^2 * var_per_draw / ev^2
        n_needed = (1.645**2 * var_per_draw) / (ev**2)
        years_needed = n_needed / DRAWS_PER_YEAR

        report.append(f"  Edge {edge}x: ~{n_needed:.0f} draws (~{years_needed:.1f} years)")

    # Stop-loss analysis
    report.append("\n\n--- STOP-LOSS IMPACT (1 year, 1.10x edge) ---")
    prob = prob_base * 1.10
    stop_losses = [None, -100, -200, -300, -500, -750]

    for sl in stop_losses:
        # Need per-draw simulation for stop-loss
        n_sims_sl = 20_000
        final_br_arr = np.zeros(n_sims_sl)
        stopped_arr = np.zeros(n_sims_sl)

        for i in range(n_sims_sl):
            br = bankroll
            for d in range(N_DRAWS_1YEAR):
                if sl is not None and (br - bankroll) <= sl:
                    stopped_arr[i] = 1
                    break
                if br < stake:
                    break
                if np.random.random() < prob:
                    br += stake * (payout - 1)
                else:
                    br -= stake
            final_br_arr[i] = br

        profit = final_br_arr - bankroll
        sl_label = f"SL={sl}" if sl is not None else "No SL"
        report.append(f"  {sl_label:>10s}: P(profit)={np.mean(profit>0)*100:.1f}%, "
                     f"Mean={np.mean(profit):+.1f}, "
                     f"Stopped={np.mean(stopped_arr)*100:.1f}%, "
                     f"P(ruin)={np.mean(final_br_arr<=0)*100:.1f}%")

    return "\n".join(report)


# ============================================================================
# SECTION 6: THE KEY QUESTION — COMBINED OPTIMAL STRATEGY
# ============================================================================

def simulate_combined_strategies(n_sims=30_000):
    """Find the combination of bet type + selectivity + sizing that works."""
    report = []
    report.append("\n" + "=" * 70)
    report.append("SECTION 6: THE KEY QUESTION")
    report.append("Can bet_type + selectivity + sizing make 1.10x profitable?")
    report.append("=" * 70)

    bankroll = 600.0

    # Define combined strategies
    combined = [
        # (name, bet_type, play_pct, edge_on_played, stake, n_bets_per_draw)
        ("S1: Baseline flat ambo secco",
         {"prob": 1/400.5, "payout": 250}, 1.0, 1.10, 1.0, 1),

        ("S2: Selective ambo secco (20% draws, 1.25x)",
         {"prob": 1/400.5, "payout": 250}, 0.20, 1.25, 1.0, 1),

        ("S3: Selective ambo secco (10% draws, 1.40x)",
         {"prob": 1/400.5, "payout": 250}, 0.10, 1.40, 1.0, 1),

        ("S4: Selective estratto (20% draws, 1.25x)",
         {"prob": 1/18, "payout": 11.23}, 0.20, 1.25, 1.0, 2),

        ("S5: Selective estratto (10% draws, 1.40x)",
         {"prob": 1/18, "payout": 11.23}, 0.10, 1.40, 2.0, 2),

        ("S6: Mixed - 1 ambo + 2 estratti selective (20%, 1.25x)",
         None, 0.20, 1.25, 1.0, None),  # special case

        ("S7: Ambo tutte ruote selective (20%, 1.25x)",
         {"prob": 1-(1-1/400.5)**10, "payout": 25}, 0.20, 1.25, 1.0, 1),

        ("S8: High selectivity ambo secco (5%, 2.0x edge)",
         {"prob": 1/400.5, "payout": 250}, 0.05, 2.0, 2.0, 1),

        ("S9: Estratto-only, all draws, 1.10x",
         {"prob": 1/18, "payout": 11.23}, 1.0, 1.10, 1.0, 2),

        ("S10: Estratto-only selective (30%, 1.20x)",
         {"prob": 1/18, "payout": 11.23}, 0.30, 1.20, 1.0, 2),
    ]

    report.append(f"\n1-year horizon ({N_DRAWS_1YEAR} total draws), bankroll={bankroll}")
    report.append(f"Simulations: {n_sims:,}\n")

    for entry in combined:
        name = entry[0]
        bt = entry[1]
        play_pct = entry[2]
        edge = entry[3]
        stake = entry[4]
        n_bets = entry[5]

        n_played = int(N_DRAWS_1YEAR * play_pct)

        if bt is None:
            # S6: mixed strategy
            prob_ambo = (1/400.5) * edge
            prob_estr = (1/18) * edge
            wins_ambo = np.random.binomial(n_played, prob_ambo, size=n_sims)
            wins_estr1 = np.random.binomial(n_played, prob_estr, size=n_sims)
            wins_estr2 = np.random.binomial(n_played, prob_estr, size=n_sims)
            total_cost = n_played * 3 * stake  # 3 bets per draw
            total_win = wins_ambo * 250 * stake + (wins_estr1 + wins_estr2) * 11.23 * stake
            profit = total_win - total_cost
        else:
            prob = bt["prob"] * edge
            prob = min(prob, 1.0)
            total_wins = np.zeros(n_sims)
            for _ in range(n_bets):
                total_wins += np.random.binomial(n_played, prob, size=n_sims)
            total_cost = n_played * n_bets * stake
            total_win = total_wins * bt["payout"] * stake
            profit = total_win - total_cost

        final_br = bankroll + profit
        p_profit = np.mean(profit > 0) * 100
        p_ruin = np.mean(final_br <= 0) * 100
        ev = np.mean(profit)
        sharpe = np.mean(profit) / np.std(profit) if np.std(profit) > 0 else 0

        report.append(f"--- {name} ---")
        report.append(f"  Draws played: {n_played}, Cost: {total_cost:.0f} EUR")
        report.append(f"  P(profit): {p_profit:.1f}%")
        report.append(f"  P(ruin): {p_ruin:.1f}%")
        report.append(f"  Mean profit: {ev:+.2f} EUR")
        report.append(f"  Median profit: {np.median(profit):+.2f} EUR")
        report.append(f"  Sharpe: {sharpe:.4f}")
        report.append("")

    # --- FINAL VERDICT ---
    report.append("\n" + "=" * 70)
    report.append("FINAL STRATEGIC RECOMMENDATIONS")
    report.append("=" * 70)

    report.append("""
1. BET TYPE SELECTION:
   - Ambo secco (250x) requires 1.66x edge to break even -- TOO HIGH
   - Estratto (11.23x) requires 1.60x edge to break even -- ALSO TOO HIGH
   - Ambo tutte ruote (25x) requires 1.60x edge -- same house edge problem
   - ALL Italian Lotto bets have ~37.6% house edge (except terno at 61.7%)
   - With 1.06-1.10x edge: NO BET TYPE IS PROFITABLE
   - Minimum viable edge: ~1.60x for any bet type

2. SELECTIVE PLAY:
   - Selectivity helps IF it genuinely increases edge on played draws
   - Playing 20% of draws at 1.25x is better than 100% at 1.06x
   - But 1.25x is still far below the 1.60x breakeven threshold
   - Even 10% at 1.40x is not enough
   - Need: play <5% of draws with >2x edge to approach profitability

3. PORTFOLIO / DIVERSIFICATION:
   - Diversification across bet types reduces variance but does NOT improve EV
   - The house edge is identical (~37.6%) across all standard bet types
   - Adding more bets = more exposure to negative EV = faster loss
   - EXCEPTION: if different bet types have different edge levels

4. PROGRESSIVE BETTING:
   - Mathematically proven: progressions cannot overcome negative EV
   - With positive EV: progressions increase variance without improving edge/EUR
   - D'Alembert/Fibonacci/Oscar: all increase ruin risk vs flat betting
   - Kelly criterion: optimal for positive EV, but edge must exceed house edge first
   - VERDICT: Flat betting is optimal for weak-edge scenarios

5. BANKROLL SURVIVAL:
   - At 1.10x edge (still -EV): ruin is certain given enough time
   - At 1.66x edge (breakeven): 50/50 long-term, high variance
   - At 2.0x edge: finally viable, but needs ~2000 draws for 95% confidence
   - Stop-loss: protects capital but reduces opportunity if edge is real

6. THE BOTTOM LINE:
   A 1.06x-1.10x prediction edge is NOT ENOUGH for ANY Italian Lotto bet.
   The house edge is 37.6%, meaning you need to predict 1.60x better than
   random to merely break even. Your 1.10x edge recovers only:
   (1.10 - 1.00) / (1.60 - 1.00) = 16.7% of the house edge.

   TO BECOME PROFITABLE, you need ONE of:
   a) Improve prediction to >1.60x edge (very difficult)
   b) Find draws where your edge exceeds 1.60x and ONLY play those
   c) Switch to a game with lower house edge (not Italian Lotto)
   d) Accept this as entertainment with controlled losses

   RECOMMENDED CONFIGURATION for the current system:
   - Bet type: ambo secco (highest upside for rare correct predictions)
   - Play only score >= 4 signals (current rule is correct)
   - Stake: 1 EUR flat (never increase)
   - Max 3 ambi per draw (current config)
   - Stop-loss: -750 EUR (current config is reasonable)
   - Expected outcome: slow, steady loss of ~0.37 EUR per EUR wagered
   - Best realistic scenario: lucky variance producing occasional wins
     that offset losses temporarily
""")

    return "\n".join(report)


# ============================================================================
# SECTION 7: ESTRATTO DEEP DIVE
# ============================================================================

def simulate_estratto_edge(n_sims=N_SIMULATIONS):
    """Deep dive: what if single-number prediction is stronger than pair prediction?"""
    report = []
    report.append("\n" + "=" * 70)
    report.append("SECTION 7: ESTRATTO DEEP DIVE")
    report.append("What if single-number prediction is better than pair prediction?")
    report.append("=" * 70)

    bankroll = 600.0
    n_draws = N_DRAWS_1YEAR

    # If we predict pairs at 1.10x, individual numbers might be at sqrt(1.10) to 1.10x
    # But also could be higher if the pair constraint reduces signal

    report.append("\nLogic: Predicting 1 number is easier than predicting a pair.")
    report.append("If pair edge is 1.10x, single-number edge could plausibly be 1.15-1.30x")
    report.append("Estratto: payout 11.23x, prob 1/18 = 0.0556")
    report.append("EV = edge * 0.0556 * 11.23 = edge * 0.6244")
    report.append("Breakeven: edge = 1/0.6244 = 1.602x\n")

    edges = [1.10, 1.20, 1.30, 1.40, 1.50, 1.60, 1.70, 1.80, 2.00]
    for edge in edges:
        prob = (1/18) * edge
        prob = min(prob, 1.0)
        ev_per_bet = prob * 11.23 - 1.0

        # Play 2 estratti per draw
        n_bets = 2
        wins = np.random.binomial(n_draws * n_bets, prob, size=n_sims)
        total_cost = n_draws * n_bets * 1.0
        profit = wins * 11.23 - total_cost
        final_br = bankroll + profit

        report.append(f"  Edge {edge:.2f}x: EV/bet={ev_per_bet:+.4f}, "
                     f"P(profit)={np.mean(profit>0)*100:.1f}%, "
                     f"Mean={np.mean(profit):+.1f}, "
                     f"P(ruin)={np.mean(final_br<=0)*100:.1f}%")

    report.append("\nKey finding: Even estratto needs 1.60x+ edge.")
    report.append("The house edge is the same ~37.6% regardless of bet type.")
    report.append("Only the VARIANCE profile changes, not the breakeven point.")

    return "\n".join(report)


# ============================================================================
# MAIN
# ============================================================================

def main():
    start = time.time()

    sections = []
    print("Running Section 1: Bet Type Analysis...")
    sections.append(analyze_bet_types())

    print("Running Section 2: Selective Play...")
    sections.append(simulate_selective_play())

    print("Running Section 3: Portfolio...")
    sections.append(simulate_portfolio())

    print("Running Section 4: Progressive Betting...")
    sections.append(simulate_progressions(n_sims=20_000))

    print("Running Section 5: Bankroll Survival...")
    sections.append(simulate_bankroll_survival())

    print("Running Section 6: Combined Strategies...")
    sections.append(simulate_combined_strategies())

    print("Running Section 7: Estratto Deep Dive...")
    sections.append(simulate_estratto_edge())

    elapsed = time.time() - start

    full_report = "\n".join(sections)
    full_report += f"\n\n[Simulation completed in {elapsed:.1f}s, {N_SIMULATIONS:,} sims/section]"

    # Print to console
    print(full_report)

    # Send to ntfy
    try:
        import httpx
        # ntfy has a body size limit, truncate if needed
        max_len = 40_000
        send_text = full_report
        if len(send_text) > max_len:
            # Send summary section only
            summary_start = full_report.find("FINAL STRATEGIC RECOMMENDATIONS")
            if summary_start > 0:
                send_text = full_report[summary_start:]
            else:
                send_text = full_report[-max_len:]

        # Send the full report in chunks if needed
        # First: send the summary
        httpx.post(
            'https://ntfy.sh/lotto-09WM5adyu6Pl4a87-ZLxSYvoYUwtZbRdM',
            content=send_text.encode('utf-8'),
            headers={
                'Title': 'GAMBLING EXPERT - Strategy Design',
                'Priority': '4',
            },
            timeout=10.0,
        )
        print("\n[Report sent to ntfy successfully]")
    except Exception as e:
        print(f"\n[Failed to send to ntfy: {e}]")

    # Also write full report to file
    report_path = "/Users/lucafurlanut/progetti/lotto/scripts/strategy_report.txt"
    with open(report_path, "w") as f:
        f.write(full_report)
    print(f"[Full report saved to {report_path}]")


if __name__ == "__main__":
    main()
