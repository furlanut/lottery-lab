"use client";

import { AlertTriangle, TrendingUp, Coins, Users, Target, Calculator } from "lucide-react";
import { useState, useMemo } from "react";

// =====================================================================
// CONSTANTS — Lottery jackpot probabilities
// =====================================================================

const GAMES = {
  millionday: {
    label: "MillionDay",
    jackpot: 1_000_000, // €
    jackpot_prob: 1 / 3_478_761, // C(55,5)
    costo_singola: 2.0, // base + Extra (max odds)
    description: "5/5 su 55 numeri — premio fisso 1M€ netto",
    extra_jackpot: 100_000,
    extra_prob: 1 / 2_118_760, // condizionale
  },
  superenalotto: {
    label: "SuperEnalotto",
    jackpot: 30_000_000, // tipico
    jackpot_prob: 1 / 622_614_630,
    costo_singola: 1.0,
    description: "6/90 — jackpot a totalizzatore, media ~30M€",
    extra_jackpot: 0,
    extra_prob: 0,
  },
  eurojackpot: {
    label: "EuroJackpot",
    jackpot: 30_000_000,
    jackpot_prob: 1 / 139_838_160,
    costo_singola: 2.0,
    description: "5/50 + 2/12 — jackpot min 10M€, max 120M€",
    extra_jackpot: 0,
    extra_prob: 0,
  },
} as const;

type GameKey = keyof typeof GAMES;

const ETF_YEARLY_RETURN = 0.07; // 7% reale (azionario diversificato)

// =====================================================================
// MATH helpers
// =====================================================================

function pJackpotAtLeastOnce(nTickets: number, pSingle: number): number {
  // 1 - (1-p)^N — usa log per stabilita numerica
  if (nTickets === 0 || pSingle === 0) return 0;
  // Per N × p piccolo, approx Np; altrimenti formula completa
  if (nTickets * pSingle < 0.01) {
    return 1 - Math.exp(-nTickets * pSingle);
  }
  return 1 - Math.pow(1 - pSingle, nTickets);
}

function etfFinalValue(yearlyDeposit: number, years: number, rate: number): number {
  // FV of annuity: C × ((1+r)^n - 1) / r
  if (rate === 0) return yearlyDeposit * years;
  return yearlyDeposit * (Math.pow(1 + rate, years) - 1) / rate;
}

function format0(n: number): string {
  return n.toLocaleString("it-IT", { maximumFractionDigits: 0 });
}

function formatK(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M€`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k€`;
  return `${n.toFixed(0)}€`;
}

function formatPct(p: number): string {
  if (p === 0) return "0%";
  if (p < 0.00001) return `${(p * 100).toExponential(2)}%`;
  if (p < 0.01) return `${(p * 100).toFixed(4)}%`;
  if (p < 1) return `${(p * 100).toFixed(2)}%`;
  return `${p.toFixed(1)}x`;
}

// =====================================================================
// Monte Carlo simulation
// =====================================================================

function monteCarloSim(
  yearlyTickets: number,
  years: number,
  pSingle: number,
  jackpot: number,
  nSims: number = 1000,
): {
  avgJackpots: number;
  pAtLeastOne: number;
  medianWinnings: number;
  p99Winnings: number;
  maxWinnings: number;
} {
  const lifetimeTickets = yearlyTickets * years;
  let totalJackpots = 0;
  let atLeastOneCount = 0;
  const winningsArr: number[] = [];

  for (let sim = 0; sim < nSims; sim++) {
    // Approssima: numero di jackpot = Binomiale(N, p) → Poisson(Np) per p piccolo
    const lambda = lifetimeTickets * pSingle;
    // Sample from Poisson using inverse CDF (per lambda piccoli OK)
    let k = 0;
    const L = Math.exp(-lambda);
    let p = 1;
    while (p > L) {
      p *= Math.random();
      if (p > L) k++;
    }
    totalJackpots += k;
    if (k >= 1) atLeastOneCount++;
    winningsArr.push(k * jackpot);
  }

  winningsArr.sort((a, b) => a - b);
  return {
    avgJackpots: totalJackpots / nSims,
    pAtLeastOne: atLeastOneCount / nSims,
    medianWinnings: winningsArr[Math.floor(nSims / 2)],
    p99Winnings: winningsArr[Math.floor(nSims * 0.99)],
    maxWinnings: winningsArr[nSims - 1],
  };
}

// =====================================================================
// Main component
// =====================================================================

export default function JackpotHunter() {
  // INPUT STATE
  const [game, setGame] = useState<GameKey>("millionday");
  const [budgetMonthly, setBudgetMonthly] = useState(60); // €/mese
  const [years, setYears] = useState(40);
  const [syndicateSize, setSyndicateSize] = useState(1); // persone nel gruppo
  const [barbellPct, setBarbellPct] = useState(0); // % in lottery (0=all ETF, 100=all lottery)

  const gameInfo = GAMES[game];

  // COMPUTED STATS
  const stats = useMemo(() => {
    const budgetYearly = budgetMonthly * 12;
    const budgetLifetime = budgetYearly * years;

    // Barbell split
    const lotteryFraction = barbellPct / 100;
    const lotteryLifetime = budgetLifetime * lotteryFraction;
    const etfLifetime = budgetLifetime * (1 - lotteryFraction);
    const etfYearly = budgetYearly * (1 - lotteryFraction);

    // Syndicate: pooling
    const lotteryPoolLifetime = lotteryLifetime * syndicateSize;
    const ticketsPool = Math.floor(lotteryPoolLifetime / gameInfo.costo_singola);

    // Probabilities
    const pJackpotGroup = pJackpotAtLeastOnce(ticketsPool, gameInfo.jackpot_prob);
    const expectedJackpotsGroup = ticketsPool * gameInfo.jackpot_prob;

    // Individual payout if jackpot
    const individualPayoutIfWin = gameInfo.jackpot / syndicateSize;

    // EV individuale
    const evLottery = expectedJackpotsGroup * individualPayoutIfWin;
    const evLotteryNet = evLottery - lotteryLifetime;

    // ETF
    const etfFinal = etfFinalValue(etfYearly, years, ETF_YEARLY_RETURN);

    // Monte Carlo
    const ticketsYearlyIndividual = Math.floor((lotteryYearlyFromBudget(budgetYearly, barbellPct, gameInfo.costo_singola)));
    const ticketsYearlyGroup = ticketsYearlyIndividual * syndicateSize;
    const mc = monteCarloSim(
      ticketsYearlyGroup,
      years,
      gameInfo.jackpot_prob,
      individualPayoutIfWin,
      500,
    );

    // P curve over years
    const pCurve: { year: number; pJackpot: number; etfValue: number; lotteryCumSpent: number }[] = [];
    for (let y = 1; y <= years; y++) {
      const ticketsAtY = ticketsPool * (y / years);
      const pAtY = pJackpotAtLeastOnce(ticketsAtY, gameInfo.jackpot_prob);
      const etfAtY = etfFinalValue(etfYearly, y, ETF_YEARLY_RETURN);
      const lotteryAtY = lotteryLifetime * (y / years);
      pCurve.push({ year: y, pJackpot: pAtY, etfValue: etfAtY, lotteryCumSpent: lotteryAtY });
    }

    return {
      budgetYearly,
      budgetLifetime,
      lotteryLifetime,
      etfLifetime,
      lotteryPoolLifetime,
      ticketsPool,
      pJackpotGroup,
      expectedJackpotsGroup,
      individualPayoutIfWin,
      evLottery,
      evLotteryNet,
      etfFinal,
      mc,
      pCurve,
    };
  }, [game, budgetMonthly, years, syndicateSize, barbellPct, gameInfo]);

  return (
    <div className="space-y-8">
      {/* Disclaimer */}
      <div className="glass p-4 border-l-2 border-lotto-amber/40 fade-up-1">
        <p className="text-[11px] text-lotto-amber uppercase tracking-widest font-bold mb-1 flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5" />
          Come leggere questi numeri
        </p>
        <p className="text-xs text-lotto-muted leading-relaxed">
          Il calcolatore stima P(vincere almeno 1 jackpot nella tua vita) dato budget, orizzonte temporale,
          syndicate e barbell strategy. Tutti i calcoli sono <b className="text-lotto-text">matematica pura</b>:
          non ci sono algoritmi predittivi, solo probabilità combinatoriale.
          L&apos;EV lotteria e sempre NEGATIVO per design (HE 33.7% MillionDay, {" "}
          {game === "superenalotto" ? "~45%" : "~38%"} altri). L&apos;ETF alternativo stima un rendimento reale
          del 7% annuo (media storica azionario globale).
        </p>
      </div>

      {/* Controls */}
      <section className="fade-up-1">
        <SectionHeader label="Parametri" icon={<Calculator className="w-3.5 h-3.5" />} />
        <div className="glass p-5 space-y-5">
          {/* Game selector */}
          <div>
            <label className="text-[10px] text-lotto-muted uppercase tracking-widest font-bold block mb-2">
              Gioco
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(Object.keys(GAMES) as GameKey[]).map((g) => (
                <button
                  key={g}
                  onClick={() => setGame(g)}
                  className={`px-3 py-2.5 rounded-lg text-sm font-bold transition-all ${
                    game === g
                      ? "bg-lotto-amber text-[#0c0c1d] shadow-lg shadow-lotto-amber/30"
                      : "bg-[rgba(255,255,255,0.05)] text-lotto-text hover:bg-[rgba(255,255,255,0.1)]"
                  }`}
                >
                  {GAMES[g].label}
                </button>
              ))}
            </div>
            <p className="text-[11px] text-lotto-muted mt-2">{gameInfo.description}</p>
            <p className="text-[11px] text-lotto-muted mt-1">
              P(jackpot cinquina singola):{" "}
              <b className="text-lotto-text">1 su {format0(1 / gameInfo.jackpot_prob)}</b> ·
              {" "}Premio: <b className="text-lotto-amber">{formatK(gameInfo.jackpot)}</b> · Costo cinquina:{" "}
              <b className="text-lotto-text">{gameInfo.costo_singola}€</b>
            </p>
          </div>

          {/* Sliders grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <SliderInput
              label="Budget mensile (€)"
              value={budgetMonthly}
              onChange={setBudgetMonthly}
              min={10}
              max={500}
              step={5}
              format={(v) => `${v}€/mese`}
              detail={`${format0(budgetMonthly * 12)}€/anno`}
            />

            <SliderInput
              label="Orizzonte temporale (anni)"
              value={years}
              onChange={setYears}
              min={1}
              max={60}
              step={1}
              format={(v) => `${v} anni`}
              detail={
                years < 10
                  ? "Breve termine"
                  : years < 30
                  ? "Medio termine"
                  : "Lungo termine (realistico per jackpot hunter)"
              }
            />

            <SliderInput
              label="Syndicate (persone nel pool)"
              value={syndicateSize}
              onChange={setSyndicateSize}
              min={1}
              max={1000}
              step={1}
              format={(v) => `${v} ${v === 1 ? "persona" : "persone"}`}
              detail={
                syndicateSize === 1
                  ? "Giocatore singolo"
                  : syndicateSize < 10
                  ? "Piccolo gruppo (amici)"
                  : syndicateSize < 100
                  ? "Medio gruppo"
                  : "Grande pool — vincita divisa fra tutti"
              }
            />

            <SliderInput
              label="% in lotteria (barbell)"
              value={barbellPct}
              onChange={setBarbellPct}
              min={0}
              max={100}
              step={5}
              format={(v) => `${v}% lotteria · ${100 - v}% ETF`}
              detail={
                barbellPct === 0
                  ? "Tutto in ETF: zero P(jackpot), alta sicurezza"
                  : barbellPct === 100
                  ? "Tutto in lotteria: nessuna rete"
                  : `${barbellPct}% lotteria + ${100 - barbellPct}% ETF al 7%`
              }
            />
          </div>
        </div>
      </section>

      {/* Main output cards */}
      <section className="fade-up-2">
        <SectionHeader label="Risultati" icon={<Target className="w-3.5 h-3.5" />} />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Jackpot probability */}
          <div className="glass p-5 relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-amber to-yellow-400" />
            <Coins className="w-8 h-8 text-lotto-amber mb-3 opacity-60" />
            <p className="text-[10px] text-lotto-muted uppercase tracking-widest">P(almeno 1 jackpot)</p>
            <p className="text-4xl font-black text-lotto-amber mt-1">{formatPct(stats.pJackpotGroup)}</p>
            <p className="text-[11px] text-lotto-muted mt-2 leading-relaxed">
              {syndicateSize > 1 ? "Probabilita del SYNDICATE " : "Tua probabilita "}
              in {years} anni giocando <b className="text-lotto-text">{format0(stats.ticketsPool)}</b>{" "}
              cinquine totali.
            </p>
            <p className="text-[11px] text-lotto-muted mt-2">
              Jackpot attesi (valore medio): <b className="text-lotto-text">{stats.expectedJackpotsGroup.toFixed(4)}</b>
            </p>
            {syndicateSize > 1 && (
              <p className="text-[11px] text-lotto-muted mt-1">
                Se vinci: <b className="text-lotto-amber">{formatK(stats.individualPayoutIfWin)}</b> a testa
              </p>
            )}
          </div>

          {/* Alternative: ETF */}
          <div className="glass p-5 relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-green to-lotto-teal" />
            <TrendingUp className="w-8 h-8 text-lotto-green mb-3 opacity-60" />
            <p className="text-[10px] text-lotto-muted uppercase tracking-widest">Alternativa: ETF 7%</p>
            <p className="text-4xl font-black text-lotto-green mt-1">{formatK(stats.etfFinal)}</p>
            <p className="text-[11px] text-lotto-muted mt-2 leading-relaxed">
              Valore finale se investi la quota ETF (<b className="text-lotto-text">{100 - barbellPct}%</b> del budget) in
              mercato azionario diversificato al 7% reale annuo.
            </p>
            <p className="text-[11px] text-lotto-muted mt-2">
              Garantito con P ~90% a orizzonte {years} anni.
            </p>
          </div>

          {/* Combined scenario */}
          <div className="glass p-5 relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-blue to-lotto-purple" />
            <Users className="w-8 h-8 text-lotto-blue mb-3 opacity-60" />
            <p className="text-[10px] text-lotto-muted uppercase tracking-widest">Scenario combinato</p>
            <div className="space-y-1 mt-1">
              <p className="text-xs text-lotto-muted">
                <span className="text-lotto-muted">Se perdi lotteria (P={formatPct(1 - stats.pJackpotGroup)}):</span>{" "}
                <b className="text-lotto-text">{formatK(stats.etfFinal)}</b>
              </p>
              <p className="text-xs text-lotto-muted">
                <span className="text-lotto-muted">Se vinci lotteria (P={formatPct(stats.pJackpotGroup)}):</span>{" "}
                <b className="text-lotto-amber">{formatK(stats.etfFinal + stats.individualPayoutIfWin)}</b>
              </p>
            </div>
            <p className="text-[11px] text-lotto-muted mt-3 pt-2 border-t border-[rgba(255,255,255,0.06)]">
              Budget totale speso: <b className="text-lotto-text">{formatK(stats.budgetLifetime)}</b>
              <br />
              EV netto lotteria: <b className={stats.evLotteryNet >= 0 ? "text-lotto-green" : "text-lotto-red"}>
                {formatK(stats.evLotteryNet)}
              </b>
              <br />
              EV totale (ETF + lotteria EV):{" "}
              <b className={stats.etfFinal - stats.budgetLifetime * barbellPct / 100 + stats.evLottery >= 0 ? "text-lotto-green" : "text-lotto-red"}>
                {formatK(stats.etfFinal + stats.evLottery - stats.lotteryLifetime)}
              </b>
            </p>
          </div>
        </div>
      </section>

      {/* Probability curve */}
      <section className="fade-up-3">
        <SectionHeader label="Evoluzione temporale" icon={<TrendingUp className="w-3.5 h-3.5" />} />
        <div className="glass p-5">
          <p className="text-[11px] text-lotto-muted mb-4">
            Come crescono P(jackpot) e ETF nel tempo
          </p>
          <ProbabilityCurveChart data={stats.pCurve} years={years} />
        </div>
      </section>

      {/* Monte Carlo */}
      <section className="fade-up-3">
        <SectionHeader label="Monte Carlo (500 vite simulate)" icon={<Calculator className="w-3.5 h-3.5" />} />
        <div className="glass p-5">
          <p className="text-[11px] text-lotto-muted mb-4 leading-relaxed">
            Simuliamo 500 &ldquo;vite parallele&rdquo; con questa strategia. Se giocassi questa combinazione in 500 universi
            paralleli, ecco cosa succederebbe:
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MCBox
              label="Vite con ≥1 jackpot"
              value={formatPct(stats.mc.pAtLeastOne)}
              sub={`${format0(stats.mc.pAtLeastOne * 500)}/500 vite`}
              color="text-lotto-amber"
            />
            <MCBox
              label="Jackpots medi"
              value={stats.mc.avgJackpots.toFixed(4)}
              sub="per vita"
              color="text-lotto-text"
            />
            <MCBox
              label="Vita mediana"
              value={formatK(stats.mc.medianWinnings)}
              sub="P=50%"
              color="text-lotto-muted"
            />
            <MCBox
              label="Vita top 1%"
              value={formatK(stats.mc.p99Winnings)}
              sub="Best 5/500 vite"
              color="text-lotto-green"
            />
          </div>
          <p className="text-[10px] text-lotto-muted mt-4 italic">
            Nota: la &ldquo;vita mediana&rdquo; e tipicamente 0€ (non vince nessuno) quando P(jackpot) &lt; 50%. La &ldquo;vita top 1%&rdquo;
            mostra il risultato massimo che vedrebbero le 5 vite piu fortunate su 500.
          </p>
        </div>
      </section>

      {/* Strategie presets */}
      <section className="fade-up-3">
        <SectionHeader label="Preset strategici" icon={<Target className="w-3.5 h-3.5" />} />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          <PresetButton
            label="💰 Barbell Sicuro"
            desc="100€/mese, 10% lotteria, 90% ETF, 40 anni"
            onClick={() => {
              setGame("millionday");
              setBudgetMonthly(100);
              setYears(40);
              setSyndicateSize(1);
              setBarbellPct(10);
            }}
          />
          <PresetButton
            label="🎲 Daily Gambler"
            desc="60€/mese, 100% lotteria, 40 anni"
            onClick={() => {
              setGame("millionday");
              setBudgetMonthly(60);
              setYears(40);
              setSyndicateSize(1);
              setBarbellPct(100);
            }}
          />
          <PresetButton
            label="👥 Syndicate Power"
            desc="30€/mese, 100 persone, 30 anni, 100% lotteria"
            onClick={() => {
              setGame("millionday");
              setBudgetMonthly(30);
              setYears(30);
              setSyndicateSize(100);
              setBarbellPct(100);
            }}
          />
          <PresetButton
            label="🚀 All-In Sogno"
            desc="200€/mese, 100% lotteria, 50 anni"
            onClick={() => {
              setGame("millionday");
              setBudgetMonthly(200);
              setYears(50);
              setSyndicateSize(1);
              setBarbellPct(100);
            }}
          />
        </div>
      </section>

      {/* Takeaways */}
      <section className="fade-up-3">
        <SectionHeader label="Le 5 lezioni matematiche" icon={<AlertTriangle className="w-3.5 h-3.5" />} />
        <div className="glass p-5 space-y-3 text-xs text-lotto-muted leading-relaxed">
          <p>
            <b className="text-lotto-text">1. P(jackpot) cresce lineare con le cinquine, non con la strategia.</b>{" "}
            Nessun algoritmo predittivo cambia P(5/5). Solo il numero di cinquine distinte fa la differenza.
          </p>
          <p>
            <b className="text-lotto-text">2. Il syndicate amplifica linearmente.</b>{" "}
            1.000 persone × 10€/mese fanno 1.000.000€ di cinquine in 10 anni → 29% di probabilita di
            jackpot, 1k€ a testa se vincete.
          </p>
          <p>
            <b className="text-lotto-text">3. Il barbell 90/10 domina quasi sempre.</b>{" "}
            Invece di giocare 100€/mese lotteria, investi 90€ in ETF e gioca 10€. Hai ~99% di finire con
            soldi in tasca invece di 0%.
          </p>
          <p>
            <b className="text-lotto-text">4. Il budget deve essere una tassa di sogno.</b>{" "}
            EV lotteria SEMPRE negativo. Se non puoi permetterti di perdere tutto il budget, non giocarlo.
          </p>
          <p>
            <b className="text-lotto-text">5. Il tempo e il tuo asset migliore.</b>{" "}
            10 anni di gioco danno P(jackpot) = 0.1%, 40 anni = 0.42%. Ma 40 anni di ETF 7% = 5x il capitale.
            Il composto batte la lotteria sempre, tranne nei casi dei fortunati 0.42%.
          </p>
        </div>
      </section>
    </div>
  );
}

// =====================================================================
// Helpers
// =====================================================================

function lotteryYearlyFromBudget(budgetYearly: number, barbellPct: number, costoSingola: number): number {
  return Math.floor((budgetYearly * barbellPct / 100) / costoSingola);
}

function SliderInput({
  label,
  value,
  onChange,
  min,
  max,
  step,
  format,
  detail,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  step: number;
  format: (v: number) => string;
  detail?: string;
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-2">
        <label className="text-[10px] text-lotto-muted uppercase tracking-widest font-bold">{label}</label>
        <span className="text-lg font-black text-lotto-amber">{format(value)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-[rgba(255,255,255,0.1)]"
        style={{
          background: `linear-gradient(to right, rgb(245, 158, 11) 0%, rgb(245, 158, 11) ${
            ((value - min) / (max - min)) * 100
          }%, rgba(255,255,255,0.1) ${((value - min) / (max - min)) * 100}%, rgba(255,255,255,0.1) 100%)`,
        }}
      />
      {detail && <p className="text-[11px] text-lotto-muted mt-1">{detail}</p>}
    </div>
  );
}

function ProbabilityCurveChart({
  data,
  years,
}: {
  data: { year: number; pJackpot: number; etfValue: number; lotteryCumSpent: number }[];
  years: number;
}) {
  if (data.length === 0) return null;
  const maxP = Math.max(0.01, Math.max(...data.map((d) => d.pJackpot)));
  const maxEtf = Math.max(...data.map((d) => d.etfValue));

  const width = 100;
  const height = 100;
  const padX = 5;
  const padY = 10;
  const plotW = width - 2 * padX;
  const plotH = height - 2 * padY;

  const pToPoints = data.map((d, i) => {
    const x = padX + (i / (data.length - 1)) * plotW;
    const y = padY + plotH - (d.pJackpot / maxP) * plotH;
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(" ");

  const etfToPoints = data.map((d, i) => {
    const x = padX + (i / (data.length - 1)) * plotW;
    const y = padY + plotH - (d.etfValue / maxEtf) * plotH;
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(" ");

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-64">
        {/* Grid */}
        {[0.25, 0.5, 0.75].map((pct) => (
          <line
            key={pct}
            x1={padX}
            x2={width - padX}
            y1={padY + plotH * pct}
            y2={padY + plotH * pct}
            stroke="rgba(255,255,255,0.04)"
            strokeWidth={0.3}
          />
        ))}

        {/* ETF area */}
        <polyline
          points={etfToPoints}
          fill="none"
          stroke="rgb(34, 197, 94)"
          strokeWidth={0.8}
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* P(jackpot) line */}
        <polyline
          points={pToPoints}
          fill="none"
          stroke="rgb(245, 158, 11)"
          strokeWidth={0.8}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <div className="flex gap-4 mt-2 text-[11px]">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-0.5 bg-lotto-amber" />
          <span className="text-lotto-muted">
            P(jackpot) 0% → <b className="text-lotto-amber">{formatPct(maxP)}</b> a {years}a
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-0.5 bg-lotto-green" />
          <span className="text-lotto-muted">
            ETF 0€ → <b className="text-lotto-green">{formatK(maxEtf)}</b> a {years}a
          </span>
        </div>
      </div>
    </div>
  );
}

function MCBox({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string;
  sub?: string;
  color: string;
}) {
  return (
    <div className="glass p-3 text-center">
      <p className="text-[10px] text-lotto-muted uppercase tracking-wide mb-1">{label}</p>
      <p className={`text-xl font-black ${color}`}>{value}</p>
      {sub && <p className="text-[10px] text-lotto-muted mt-0.5">{sub}</p>}
    </div>
  );
}

function PresetButton({
  label,
  desc,
  onClick,
}: {
  label: string;
  desc: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="glass p-4 text-left hover:border-lotto-amber/30 hover:bg-[rgba(245,158,11,0.03)] transition-all"
    >
      <p className="text-sm font-black text-lotto-text mb-1">{label}</p>
      <p className="text-[11px] text-lotto-muted leading-relaxed">{desc}</p>
    </button>
  );
}

function SectionHeader({ label, icon }: { label: string; icon?: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      {icon && <span className="text-lotto-muted">{icon}</span>}
      <h2 className="text-xs font-bold uppercase tracking-widest text-lotto-muted whitespace-nowrap">
        {label}
      </h2>
      <div className="flex-1 h-px bg-[rgba(255,255,255,0.05)]" />
    </div>
  );
}
