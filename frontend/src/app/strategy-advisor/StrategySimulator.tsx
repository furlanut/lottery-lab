"use client";

import { fetchAPI, SimulateResult } from "@/lib/api";
import NumberBall from "@/components/NumberBall";
import { Calculator, Loader2 } from "lucide-react";
import { useState } from "react";

export default function StrategySimulator() {
  const [selected, setSelected] = useState<number[]>([]);
  const [result, setResult] = useState<SimulateResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleNumber(n: number) {
    setResult(null);
    setError(null);
    if (selected.includes(n)) {
      setSelected(selected.filter((x) => x !== n));
    } else if (selected.length < 6) {
      setSelected([...selected, n].sort((a, b) => a - b));
    }
  }

  function clearSelection() {
    setSelected([]);
    setResult(null);
    setError(null);
  }

  function randomSelection() {
    const pool = Array.from({ length: 90 }, (_, i) => i + 1);
    const shuffled = pool.sort(() => Math.random() - 0.5);
    setSelected(shuffled.slice(0, 6).sort((a, b) => a - b));
    setResult(null);
    setError(null);
  }

  async function runSimulation() {
    if (selected.length !== 6) {
      setError("Seleziona esattamente 6 numeri");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const csv = selected.join(",");
      const res = await fetchAPI<SimulateResult>(
        `/strategy-advisor/simulate?numeri=${csv}&backtest_limit=2000`
      );
      setResult(res);
    } catch (e) {
      setError("Errore nella simulazione");
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="glass p-5 space-y-5">
      <div>
        <p className="text-xs text-lotto-muted mb-3">
          Clicca fino a 6 numeri per creare la tua cinquina, poi simula sulle ultime 2.000 estrazioni reali.
        </p>

        {/* Current selection */}
        <div className="mb-4 min-h-[60px] flex items-center gap-3 flex-wrap">
          <span className="text-[11px] text-lotto-muted uppercase">Selezione:</span>
          {selected.length === 0 ? (
            <span className="text-xs text-lotto-muted italic">nessun numero selezionato</span>
          ) : (
            selected.map((n) => (
              <button
                key={n}
                onClick={() => toggleNumber(n)}
                className="transition-transform hover:scale-110"
              >
                <NumberBall number={n} size="md" glow />
              </button>
            ))
          )}
          <span className="text-xs text-lotto-muted ml-auto">
            {selected.length}/6
          </span>
        </div>

        {/* Number grid */}
        <div className="grid grid-cols-10 gap-1.5">
          {Array.from({ length: 90 }, (_, i) => i + 1).map((n) => {
            const isSelected = selected.includes(n);
            const isDisabled = !isSelected && selected.length >= 6;
            return (
              <button
                key={n}
                onClick={() => toggleNumber(n)}
                disabled={isDisabled}
                className={`
                  aspect-square rounded-lg text-xs font-bold transition-all
                  ${
                    isSelected
                      ? "bg-lotto-amber text-[#0c0c1d] shadow-lg shadow-lotto-amber/30 scale-105"
                      : isDisabled
                      ? "bg-[rgba(255,255,255,0.02)] text-lotto-muted/50 cursor-not-allowed"
                      : "bg-[rgba(255,255,255,0.05)] text-lotto-text hover:bg-[rgba(255,255,255,0.1)]"
                  }
                `}
              >
                {n}
              </button>
            );
          })}
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-2 mt-4">
          <button
            onClick={runSimulation}
            disabled={selected.length !== 6 || loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-lotto-blue text-white font-bold text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:bg-lotto-blue/90 transition"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Calculator className="w-4 h-4" />
            )}
            Simula
          </button>
          <button
            onClick={randomSelection}
            className="px-4 py-2 rounded-lg bg-[rgba(255,255,255,0.05)] text-lotto-text font-bold text-sm hover:bg-[rgba(255,255,255,0.1)] transition"
          >
            Random 6
          </button>
          <button
            onClick={clearSelection}
            disabled={selected.length === 0}
            className="px-4 py-2 rounded-lg bg-[rgba(255,255,255,0.02)] text-lotto-muted font-bold text-sm disabled:opacity-40 hover:bg-[rgba(255,255,255,0.08)] transition"
          >
            Reset
          </button>
        </div>

        {error && (
          <div className="mt-3 px-3 py-2 rounded-md bg-lotto-red/10 border border-lotto-red/20 text-lotto-red text-xs">
            {error}
          </div>
        )}
      </div>

      {/* Risultato */}
      {result && (
        <div className="pt-5 border-t border-[rgba(255,255,255,0.06)] space-y-4">
          <h3 className="text-sm font-black text-lotto-text">Risultato simulazione</h3>

          {/* EV analitico */}
          <div>
            <p className="text-[10px] text-lotto-muted uppercase tracking-widest mb-2">
              EV analitico (teorico, valido per qualsiasi cinquina)
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <MetricBox
                label="EV totale"
                value={`${result.ev_analitico.ev_totale.toFixed(4)}€`}
                sub="su 2€ giocati"
              />
              <MetricBox
                label="House edge"
                value={`${result.ev_analitico.house_edge.toFixed(2)}%`}
                sub="ineluttabile"
                color="text-lotto-red"
              />
              <MetricBox
                label="Breakeven"
                value={`${result.ev_analitico.breakeven.toFixed(3)}x`}
                sub="ratio necessario"
              />
              <MetricBox
                label="P(vincita)"
                value={`${(result.ev_analitico.p_win_qualsiasi * 100).toFixed(1)}%`}
                sub="qualsiasi premio"
                color="text-lotto-green"
              />
            </div>
          </div>

          {/* Backtest */}
          <div>
            <p className="text-[10px] text-lotto-muted uppercase tracking-widest mb-2">
              Backtest osservato (ultime {result.backtest.estrazioni_testate.toLocaleString()} estrazioni)
            </p>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <MetricBox
                label="P(≥1€) oss"
                value={`${result.backtest.p_1plus_oss.toFixed(2)}%`}
                color="text-lotto-text"
              />
              <MetricBox
                label="P(≥10€) oss"
                value={`${result.backtest.p_10plus_oss.toFixed(2)}%`}
                color="text-lotto-amber"
              />
              <MetricBox
                label="P(≥100€) oss"
                value={`${result.backtest.p_100plus_oss.toFixed(2)}%`}
                color="text-lotto-green"
              />
              <MetricBox
                label="P&L"
                value={`${result.backtest.pnl >= 0 ? "+" : ""}${result.backtest.pnl.toFixed(0)}€`}
                color={result.backtest.pnl >= 0 ? "text-lotto-green" : "text-lotto-red"}
                sub={`ROI ${result.backtest.roi.toFixed(1)}%`}
              />
              <MetricBox
                label="Ratio osservato"
                value={`${result.backtest.ratio_vs_ev.toFixed(3)}x`}
                color={
                  result.backtest.ratio_vs_ev >= 1.11
                    ? "text-lotto-green"
                    : result.backtest.ratio_vs_ev >= 1.0
                    ? "text-lotto-amber"
                    : "text-lotto-red"
                }
                sub={result.backtest.ratio_vs_ev >= 1.11 ? "> BE" : "< BE"}
              />
            </div>
          </div>

          {/* Match distribution */}
          <div>
            <p className="text-[10px] text-lotto-muted uppercase tracking-widest mb-2">
              Distribuzione match base (sui {result.backtest.estrazioni_testate} test)
            </p>
            <div className="flex gap-1">
              {[0, 1, 2, 3, 4, 5, 6].map((mb) => {
                const count = result.backtest.match_base_dist[mb.toString()] ?? 0;
                const pct = (count / result.backtest.estrazioni_testate) * 100;
                const color =
                  mb >= 5
                    ? "bg-lotto-green/30"
                    : mb >= 3
                    ? "bg-lotto-amber/20"
                    : "bg-[rgba(255,255,255,0.04)]";
                return (
                  <div key={mb} className={`flex-1 ${color} rounded p-2 text-center`}>
                    <p className="text-[10px] text-lotto-muted">{mb}/6</p>
                    <p className="text-xs font-black text-lotto-text">{count}</p>
                    <p className="text-[9px] text-lotto-muted">{pct.toFixed(1)}%</p>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="text-[11px] text-lotto-muted italic">
            Nota: con N={result.backtest.estrazioni_testate} estrazioni, l&apos;intervallo 95% del ratio e ~±
            {(0.03 * Math.sqrt(34700 / result.backtest.estrazioni_testate)).toFixed(3)}. Tutto in [0.95, 1.10] e rumore statistico.
          </div>
        </div>
      )}
    </div>
  );
}

function MetricBox({
  label,
  value,
  sub,
  color = "text-lotto-text",
}: {
  label: string;
  value: string;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="glass p-3">
      <p className="text-[10px] text-lotto-muted uppercase tracking-wide mb-0.5">{label}</p>
      <p className={`text-base font-black ${color}`}>{value}</p>
      {sub && <p className="text-[10px] text-lotto-muted mt-0.5">{sub}</p>}
    </div>
  );
}
