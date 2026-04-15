"use client";

import { useState, useMemo } from "react";
import NumberBall from "@/components/NumberBall";
import { PaperTradingRecord } from "@/lib/api";

const GAME_CONFIG: Record<
  string,
  { label: string; colorClass: string; bgClass: string; borderClass: string }
> = {
  lotto: {
    label: "Lotto",
    colorClass: "text-lotto-blue",
    bgClass: "bg-lotto-blue/10",
    borderClass: "border-lotto-blue/20",
  },
  vincicasa: {
    label: "VinciCasa",
    colorClass: "text-lotto-green",
    bgClass: "bg-lotto-green/10",
    borderClass: "border-lotto-green/20",
  },
  diecielotto: {
    label: "10eLotto",
    colorClass: "text-lotto-amber",
    bgClass: "bg-lotto-amber/10",
    borderClass: "border-lotto-amber/20",
  },
};

const GAMES = [
  { key: "all", label: "Tutti", color: "text-lotto-text" },
  { key: "lotto", label: "Lotto", color: "text-lotto-blue" },
  { key: "vincicasa", label: "VinciCasa", color: "text-lotto-green" },
  { key: "diecielotto", label: "10eLotto", color: "text-lotto-amber" },
];

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("it-IT", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

function formatCurrency(v: number): string {
  return `${v >= 0 ? "+" : ""}${v.toFixed(2)}€`;
}

export default function PaperTradingHistory({
  records,
}: {
  records: PaperTradingRecord[];
}) {
  const [selectedGame, setSelectedGame] = useState("all");

  const filtered = useMemo(() => {
    if (selectedGame === "all") return records;
    return records.filter((r) => r.gioco === selectedGame);
  }, [records, selectedGame]);

  // Group by game for display
  const gameKeys = useMemo(() => {
    if (selectedGame === "all") return ["lotto", "vincicasa", "diecielotto"];
    return [selectedGame];
  }, [selectedGame]);

  return (
    <div className="space-y-4">
      {/* Filter tabs */}
      <div className="flex gap-2 flex-wrap">
        {GAMES.map((g) => (
          <button
            key={g.key}
            onClick={() => setSelectedGame(g.key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wide transition-all ${
              selectedGame === g.key
                ? `${g.color} bg-white/10 border border-white/20`
                : "text-lotto-muted hover:text-lotto-text bg-[rgba(255,255,255,0.03)] border border-transparent"
            }`}
          >
            {g.label}
          </button>
        ))}
      </div>

      {/* Per-game sections */}
      <div className="space-y-8">
        {gameKeys.map((gameKey) => {
          const gameRecords = filtered.filter((r) => r.gioco === gameKey);
          if (gameRecords.length === 0) return null;
          const config = GAME_CONFIG[gameKey] ?? GAME_CONFIG.lotto;
          let cumPnl = 0;

          return (
            <div key={gameKey}>
              {/* Game header */}
              <div className="flex items-center gap-3 mb-3">
                <span
                  className={`text-xs font-bold uppercase tracking-widest ${config.colorClass}`}
                >
                  {config.label}
                </span>
                <div className="flex-1 h-px bg-[rgba(255,255,255,0.06)]" />
                <span className="text-[10px] text-lotto-muted">
                  {gameRecords.length} giocate
                </span>
              </div>

              {/* Records */}
              <div className="space-y-2">
                {gameRecords.map((r, idx) => {
                  const net = r.vincita - r.costo;
                  cumPnl += net;
                  const isWin = r.stato === "VINTA";

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
                        {/* Left: info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-xs font-mono text-lotto-muted">
                              {formatDate(r.data)}
                              {r.ora ? ` ${r.ora}` : ""}
                            </span>
                            <span
                              className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded border ${config.bgClass} ${config.colorClass} ${config.borderClass}`}
                            >
                              {config.label}
                            </span>
                            <span
                              className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded border ${
                                isWin
                                  ? "bg-lotto-green/10 text-lotto-green border-lotto-green/20"
                                  : r.stato === "ATTIVA"
                                    ? "bg-lotto-amber/10 text-lotto-amber border-lotto-amber/20"
                                    : "bg-lotto-red/10 text-lotto-red border-lotto-red/20"
                              }`}
                            >
                              {r.stato}
                            </span>
                          </div>

                          {/* Previsione */}
                          <div className="mb-1.5">
                            <span className="text-[10px] text-lotto-muted uppercase">
                              Prev
                              {r.previsione.ruota ? ` · ${r.previsione.ruota}` : ""}
                              :{" "}
                            </span>
                            <span className="inline-flex gap-1 flex-wrap">
                              {r.previsione.numeri.map((n, i) => {
                                const matched = (r.estrazione.numeri ?? []).includes(n);
                                return (
                                  <span
                                    key={i}
                                    className={
                                      matched
                                        ? "ring-2 ring-lotto-green rounded-full"
                                        : ""
                                    }
                                  >
                                    <NumberBall number={n} size="sm" glow={matched} />
                                  </span>
                                );
                              })}
                            </span>
                          </div>

                          {/* Estrazione */}
                          {r.estrazione.numeri && r.estrazione.numeri.length > 0 && (
                            <div className="text-[10px] text-lotto-muted">
                              Estratti:{" "}
                              {r.estrazione.numeri.slice(0, 10).join("·")}
                              {(r.estrazione.numeri.length > 10) && "..."}
                              {r.estrazione.numero_oro && (
                                <span className="ml-1 text-yellow-400">
                                  Oro:{r.estrazione.numero_oro}
                                </span>
                              )}
                            </div>
                          )}
                        </div>

                        {/* Right: P&L */}
                        <div className="flex md:flex-col items-center md:items-end gap-2 flex-shrink-0">
                          <span className="text-[10px] text-lotto-muted">
                            -{r.costo.toFixed(2)}€
                          </span>
                          <span
                            className={`text-sm font-black ${
                              net >= 0 ? "text-lotto-green" : "text-lotto-red"
                            }`}
                          >
                            {formatCurrency(net)}
                          </span>
                          <span
                            className={`text-[10px] font-bold ${
                              cumPnl >= 0 ? "text-lotto-green" : "text-lotto-red"
                            }`}
                          >
                            Cum: {formatCurrency(cumPnl)}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
