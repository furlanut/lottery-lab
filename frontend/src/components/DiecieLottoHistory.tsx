"use client";

import { useState, useMemo } from "react";
import NumberBall from "@/components/NumberBall";
import { DiecieLottoRecord } from "@/lib/api";

const PERIOD_OPTIONS = [
  { key: "today", label: "Oggi" },
  { key: "3d", label: "3 giorni" },
  { key: "7d", label: "7 giorni" },
  { key: "all", label: "Tutto" },
];

function isWithinDays(dateStr: string, days: number): boolean {
  const d = new Date(dateStr);
  const now = new Date();
  const diff = (now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24);
  return diff <= days;
}

function isToday(dateStr: string): boolean {
  const d = new Date(dateStr);
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

export default function DiecieLottoHistory({
  records,
}: {
  records: DiecieLottoRecord[];
}) {
  const [period, setPeriod] = useState("all");

  const filtered = useMemo(() => {
    return records.filter((r) => {
      const dateStr = r.estrazione?.data;
      if (!dateStr) return period === "all";
      if (period === "today") return isToday(dateStr);
      if (period === "3d") return isWithinDays(dateStr, 3);
      if (period === "7d") return isWithinDays(dateStr, 7);
      return true;
    });
  }, [records, period]);

  // Calculate cumulative P&L
  let cumPnl = 0;
  const withCum = filtered.map((r) => {
    const pnl = r.estrazione?.pnl ?? -r.costo;
    cumPnl += pnl;
    return { ...r, cumPnl };
  });

  // Summary stats
  const totalCost = filtered.length * 2;
  const totalWon = filtered.reduce(
    (s, r) => s + (r.estrazione?.vincita_totale ?? 0),
    0
  );
  const totalPnl = totalWon - totalCost;
  const wins = filtered.filter(
    (r) => (r.estrazione?.vincita_totale ?? 0) > 0
  ).length;

  return (
    <div className="space-y-4">
      {/* Period filter + summary */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-2">
          {PERIOD_OPTIONS.map((opt) => (
            <button
              key={opt.key}
              onClick={() => setPeriod(opt.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wide transition-all ${
                period === opt.key
                  ? "text-lotto-amber bg-lotto-amber/15 border border-lotto-amber/30"
                  : "text-lotto-muted hover:text-lotto-text bg-[rgba(255,255,255,0.03)] border border-transparent"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <div className="flex gap-4 text-xs">
          <span className="text-lotto-muted">
            Giocate: <b className="text-lotto-text">{filtered.length}</b>
          </span>
          <span className="text-lotto-muted">
            Vinte: <b className="text-lotto-green">{wins}</b>
          </span>
          <span className="text-lotto-muted">
            Investito: <b className="text-lotto-text">{totalCost.toFixed(0)}€</b>
          </span>
          <span
            className={`font-bold ${totalPnl >= 0 ? "text-lotto-green" : "text-lotto-red"}`}
          >
            P&L: {totalPnl >= 0 ? "+" : ""}
            {totalPnl.toFixed(2)}€
          </span>
        </div>
      </div>

      {/* Records */}
      <div className="space-y-2">
        {withCum.map((r, idx) => {
          const e = r.estrazione;
          const hasEstrazione = e && e.numeri && e.numeri.length > 0;
          const vincita = e?.vincita_totale ?? 0;
          const pnl = e?.pnl ?? -r.costo;
          const isWin = vincita > 0;

          return (
            <div
              key={idx}
              className={`glass p-3 relative overflow-hidden ${
                isWin ? "border-lotto-green/20" : ""
              }`}
            >
              {isWin && (
                <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-green to-lotto-teal" />
              )}

              <div className="flex flex-col md:flex-row md:items-start gap-3">
                {/* Left: estrazione info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-mono text-lotto-muted">
                      {e?.data ?? "?"} {e?.ora ?? ""}
                    </span>
                    {e?.concorso && (
                      <span className="text-[10px] text-lotto-muted">
                        #{e.concorso}
                      </span>
                    )}
                    <span
                      className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded border ${
                        isWin
                          ? "bg-lotto-green/10 text-lotto-green border-lotto-green/20"
                          : "bg-lotto-red/10 text-lotto-red border-lotto-red/20"
                      }`}
                    >
                      {isWin ? "VINTA" : "PERSA"}
                    </span>
                  </div>

                  {/* Previsione */}
                  <div className="mb-1.5">
                    <span className="text-[10px] text-lotto-muted uppercase tracking-wide">
                      Previsione:{" "}
                    </span>
                    <span className="inline-flex gap-1 flex-wrap">
                      {r.previsione.numeri.map((n, i) => {
                        const matched =
                          e?.numeri_azzeccati?.includes(n) ||
                          e?.numeri_azzeccati_extra?.includes(n);
                        return (
                          <span
                            key={i}
                            className={
                              matched ? "ring-2 ring-lotto-green rounded-full" : ""
                            }
                          >
                            <NumberBall number={n} size="sm" glow={matched} />
                          </span>
                        );
                      })}
                    </span>
                  </div>

                  {/* Estrazione reale */}
                  {hasEstrazione && (
                    <div className="mb-1">
                      <span className="text-[10px] text-lotto-muted uppercase tracking-wide">
                        Estratti:{" "}
                      </span>
                      <span className="inline-flex gap-0.5 flex-wrap">
                        {e.numeri!.slice(0, 20).map((n, i) => (
                          <span
                            key={i}
                            className="text-[10px] font-mono text-lotto-muted"
                          >
                            {n}
                            {i < 19 ? "·" : ""}
                          </span>
                        ))}
                      </span>
                      {e.numero_oro && (
                        <span className="ml-2 text-[10px]">
                          <span className="text-yellow-400">
                            Oro:{e.numero_oro}
                          </span>{" "}
                          <span className="text-lotto-amber">
                            DOro:{e.doppio_oro}
                          </span>
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Right: P&L */}
                <div className="flex md:flex-col items-center md:items-end gap-3 md:gap-1 flex-shrink-0 md:min-w-[120px] md:text-right">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-lotto-muted">
                      B:{e?.match_base ?? 0}/6
                    </span>
                    <span className="text-[10px] text-lotto-muted">
                      E:{e?.match_extra ?? 0}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-lotto-muted">
                      -2.00€ →{" "}
                    </span>
                    <span
                      className={`text-sm font-black ${
                        pnl >= 0 ? "text-lotto-green" : "text-lotto-red"
                      }`}
                    >
                      {pnl >= 0 ? "+" : ""}
                      {pnl.toFixed(2)}€
                    </span>
                  </div>
                  <span
                    className={`text-[10px] font-bold ${
                      r.cumPnl >= 0 ? "text-lotto-green" : "text-lotto-red"
                    }`}
                  >
                    Cum: {r.cumPnl >= 0 ? "+" : ""}
                    {r.cumPnl.toFixed(2)}€
                  </span>
                </div>
              </div>
            </div>
          );
        })}

        {withCum.length === 0 && (
          <div className="glass p-8 text-center">
            <p className="text-lotto-muted">
              Nessuna giocata nel periodo selezionato
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
