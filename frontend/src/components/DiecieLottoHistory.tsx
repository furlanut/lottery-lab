"use client";

import { useState, useMemo, useEffect } from "react";
import NumberBall from "@/components/NumberBall";
import { DiecieLottoRecord } from "@/lib/api";
import { useRouter } from "next/navigation";

const PERIOD_OPTIONS = [
  { key: "today", label: "Oggi" },
  { key: "3d", label: "3 giorni" },
  { key: "7d", label: "7 giorni" },
  { key: "all", label: "Tutto" },
];

function isWithinDays(dateStr: string, days: number): boolean {
  const d = new Date(dateStr);
  const now = new Date();
  return (now.getTime() - d.getTime()) / 86400000 <= days;
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

// Countdown to next 5-minute extraction
function NextDrawTimer() {
  const [secondsLeft, setSecondsLeft] = useState(0);
  const router = useRouter();

  useEffect(() => {
    function calc() {
      const now = new Date();
      const min = now.getMinutes();
      const sec = now.getSeconds();
      const nextMin = Math.ceil((min + 1) / 5) * 5;
      const diff = (nextMin - min) * 60 - sec;
      setSecondsLeft(diff > 0 ? diff : 300);
    }
    calc();
    const iv = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          // Wait 15s for backend to scrape, then hard reload
          setTimeout(() => window.location.reload(), 15000);
          return 300;
        }
        return prev - 1;
      });
    }, 1000);
    // Hard reload every 90s as backup
    const poll = setInterval(() => window.location.reload(), 90000);
    return () => {
      clearInterval(iv);
      clearInterval(poll);
    };
  }, [router]);

  const mins = Math.floor(secondsLeft / 60);
  const secs = secondsLeft % 60;
  const isClose = secondsLeft <= 30;

  return (
    <div className="flex items-center gap-2">
      <div
        className={`w-2 h-2 rounded-full ${isClose ? "bg-lotto-green dot-pulse" : "bg-lotto-amber"}`}
      />
      <span className={`font-mono text-sm font-bold ${isClose ? "text-lotto-green" : "text-lotto-amber"}`}>
        {mins}:{secs.toString().padStart(2, "0")}
      </span>
      <span className="text-[10px] text-lotto-muted">prossima estrazione</span>
    </div>
  );
}

// Number with green blinking dot underneath when matched
function MatchableNumber({
  number,
  matched,
  size = "md",
}: {
  number: number;
  matched: boolean;
  size?: "sm" | "md" | "lg";
}) {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <NumberBall number={number} size={size} />
      {matched && (
        <div className="w-1.5 h-1.5 rounded-full bg-lotto-green dot-pulse" />
      )}
    </div>
  );
}

export default function DiecieLottoHistory({
  records,
}: {
  records: DiecieLottoRecord[];
}) {
  const [period, setPeriod] = useState("all");

  // 1. Order: most recent first (already DESC from API, but ensure)
  const sorted = useMemo(() => {
    return [...records].sort((a, b) => {
      const da = a.estrazione?.data ?? a.previsione?.metodo ?? "";
      const db = b.estrazione?.data ?? b.previsione?.metodo ?? "";
      const oa = a.estrazione?.ora ?? "";
      const ob = b.estrazione?.ora ?? "";
      return `${db}${ob}`.localeCompare(`${da}${oa}`);
    });
  }, [records]);

  const filtered = useMemo(() => {
    return sorted.filter((r) => {
      const dateStr = r.estrazione?.data;
      if (!dateStr) return period === "all";
      if (period === "today") return isToday(dateStr);
      if (period === "3d") return isWithinDays(dateStr, 3);
      if (period === "7d") return isWithinDays(dateStr, 7);
      return true;
    });
  }, [sorted, period]);

  // Cumulative P&L (from oldest to newest, then display newest first)
  const reversed = [...filtered].reverse();
  let cumPnl = 0;
  const cumMap = new Map<number, number>();
  reversed.forEach((_, i) => {
    const r = reversed[i];
    const pnl = r.estrazione?.pnl ?? -r.costo;
    cumPnl += pnl;
    cumMap.set(filtered.length - 1 - i, cumPnl);
  });

  // Summary
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
      {/* Timer + Period filter + Summary */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-4">
          <NextDrawTimer />
          <div className="flex gap-1.5">
            {PERIOD_OPTIONS.map((opt) => (
              <button
                key={opt.key}
                onClick={() => setPeriod(opt.key)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-bold uppercase tracking-wide transition-all ${
                  period === opt.key
                    ? "text-lotto-amber bg-lotto-amber/15 border border-lotto-amber/30"
                    : "text-lotto-muted hover:text-lotto-text bg-[rgba(255,255,255,0.03)] border border-transparent"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex gap-3 text-xs">
          <span className="text-lotto-muted">
            Giocate: <b className="text-lotto-text">{filtered.length}</b>
          </span>
          <span className="text-lotto-muted">
            Vinte: <b className="text-lotto-green">{wins}</b>
          </span>
          <span className="text-lotto-muted">
            Inv: <b className="text-lotto-text">{totalCost}€</b>
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
      <div className="space-y-3">
        {filtered.map((r, idx) => {
          const e = r.estrazione;
          const hasEstr = e && e.numeri && e.numeri.length > 0;
          const vincita = e?.vincita_totale ?? 0;
          const pnl = e?.pnl ?? -r.costo;
          const isWin = vincita > 0;
          const azzBase = new Set(e?.numeri_azzeccati ?? []);
          const azzExtra = new Set(e?.numeri_azzeccati_extra ?? []);
          const thisCum = cumMap.get(idx) ?? 0;

          return (
            <div
              key={idx}
              className={`glass p-4 relative overflow-hidden ${
                isWin ? "border-lotto-green/20" : ""
              }`}
            >
              {isWin && (
                <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-green to-lotto-teal" />
              )}

              {/* Header: date + concorso + stato + P&L */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-mono text-lotto-muted">
                    {e?.data ?? "?"} {e?.ora ?? ""}
                  </span>
                  {e?.concorso && (
                    <span className="text-[10px] text-lotto-muted/60">
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
                <div className="flex items-center gap-3">
                  <span
                    className={`text-base font-black ${
                      pnl >= 0 ? "text-lotto-green" : "text-lotto-red"
                    }`}
                  >
                    {pnl >= 0 ? "+" : ""}
                    {pnl.toFixed(2)}€
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      thisCum >= 0
                        ? "bg-lotto-green/10 text-lotto-green"
                        : "bg-lotto-red/10 text-lotto-red"
                    }`}
                  >
                    Cum {thisCum >= 0 ? "+" : ""}
                    {thisCum.toFixed(2)}€
                  </span>
                </div>
              </div>

              {/* Previsione — numeri con dot verde se azzeccati */}
              <div className="mb-3">
                <p className="text-[10px] text-lotto-muted uppercase tracking-widest mb-1.5">
                  Previsione · {r.previsione.metodo} · Costo 2.00€
                </p>
                <div className="flex gap-2 flex-wrap">
                  {r.previsione.numeri.map((n, i) => (
                    <MatchableNumber
                      key={i}
                      number={n}
                      matched={azzBase.has(n) || azzExtra.has(n)}
                      size="md"
                    />
                  ))}
                </div>
              </div>

              {/* Estrazione reale — numeri grandi, azzeccati cerchiati */}
              {hasEstr && (
                <div className="pt-3 border-t border-[rgba(255,255,255,0.06)]">
                  {/* 20 numeri base */}
                  <p className="text-[10px] text-lotto-muted uppercase tracking-widest mb-1.5">
                    20 Numeri estratti ·{" "}
                    <span className="text-lotto-text">
                      Match {e.match_base}/6
                    </span>
                  </p>
                  <div className="flex gap-1.5 flex-wrap mb-3">
                    {e.numeri!.map((n, i) => {
                      const isMatched = azzBase.has(n);
                      return (
                        <div
                          key={i}
                          className={
                            isMatched
                              ? "ring-2 ring-lotto-green ring-offset-1 ring-offset-[#0c0c1d] rounded-full"
                              : ""
                          }
                        >
                          <NumberBall number={n} size="md" />
                        </div>
                      );
                    })}
                  </div>

                  {/* Numero Oro + Doppio Oro */}
                  <div className="flex items-center gap-4 mb-3">
                    {e.numero_oro && (
                      <div>
                        <p className="text-[10px] text-yellow-400 uppercase tracking-widest mb-1">
                          Numero Oro
                        </p>
                        <div className="ring-2 ring-yellow-400 ring-offset-1 ring-offset-[#0c0c1d] rounded-full inline-flex shadow-lg shadow-yellow-400/20">
                          <NumberBall number={e.numero_oro} size="lg" glow />
                        </div>
                      </div>
                    )}
                    {e.doppio_oro && (
                      <div>
                        <p className="text-[10px] text-lotto-amber uppercase tracking-widest mb-1">
                          Doppio Oro
                        </p>
                        <div className="ring-2 ring-lotto-amber ring-offset-1 ring-offset-[#0c0c1d] rounded-full inline-flex shadow-lg shadow-lotto-amber/20">
                          <NumberBall number={e.doppio_oro} size="lg" glow />
                        </div>
                      </div>
                    )}
                  </div>

                  {/* 15 Extra */}
                  {e.numeri_extra && e.numeri_extra.length > 0 && (
                    <div>
                      <p className="text-[10px] text-lotto-muted uppercase tracking-widest mb-1.5">
                        Extra (15 numeri) ·{" "}
                        <span className="text-lotto-text">
                          Match {e.match_extra}
                        </span>
                      </p>
                      <div className="flex gap-1.5 flex-wrap">
                        {e.numeri_extra.map((n, i) => {
                          const isMatched = azzExtra.has(n);
                          return (
                            <div
                              key={i}
                              className={
                                isMatched
                                  ? "ring-2 ring-lotto-green ring-offset-1 ring-offset-[#0c0c1d] rounded-full"
                                  : ""
                              }
                            >
                              <NumberBall number={n} size="md" />
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Vincita breakdown */}
                  {isWin && (
                    <div className="mt-2 pt-2 border-t border-[rgba(255,255,255,0.04)] flex gap-4 text-xs text-lotto-muted">
                      {(e.vincita_base ?? 0) > 0 && (
                        <span>
                          Base:{" "}
                          <b className="text-lotto-green">
                            +{e.vincita_base?.toFixed(2)}€
                          </b>
                        </span>
                      )}
                      {(e.vincita_extra ?? 0) > 0 && (
                        <span>
                          Extra:{" "}
                          <b className="text-lotto-green">
                            +{e.vincita_extra?.toFixed(2)}€
                          </b>
                        </span>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {filtered.length === 0 && (
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
