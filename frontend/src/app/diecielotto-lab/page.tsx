"use client";

import { useState, useEffect, useCallback } from "react";
import NumberBall from "@/components/NumberBall";
import { DiecieLottoRecord } from "@/lib/api";
import { FlaskConical } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

interface Previsione {
  numeri: number[];
  metodo: string;
  configurazione: number;
  costo: number;
  he: number;
  dettagli: string;
}

export default function DiecieLottoLabPage() {
  const [k, setK] = useState(6);
  const [previsione, setPrevisione] = useState<Previsione | null>(null);
  const [storico, setStorico] = useState<DiecieLottoRecord[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async (numK: number) => {
    setLoading(true);
    try {
      const [prevRes, storRes] = await Promise.all([
        fetch(`${API_BASE}/diecielotto-k/previsione?k=${numK}`),
        fetch(`${API_BASE}/diecielotto-k/storico?k=${numK}&limit=100`),
      ]);
      if (prevRes.ok) setPrevisione(await prevRes.json());
      if (storRes.ok) setStorico(await storRes.json());
    } catch {
      /* ignore */
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData(k);
  }, [k, fetchData]);

  // P&L summary
  let cumPnl = 0;
  const withCum = [...storico].reverse().map((r) => {
    const pnl = r.estrazione?.pnl ?? -r.costo;
    cumPnl += pnl;
    return { ...r, cumPnl };
  });
  withCum.reverse();

  const totalCost = storico.length * 2;
  const totalWon = storico.reduce(
    (s, r) => s + (r.estrazione?.vincita_totale ?? 0),
    0
  );
  const totalPnl = totalWon - totalCost;
  const wins = storico.filter(
    (r) => (r.estrazione?.vincita_totale ?? 0) > 0
  ).length;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-1 flex items-center gap-4">
          <span className="gradient-amber">10eLotto</span>
          <span className="text-lotto-text text-2xl">Lab</span>
          <FlaskConical className="w-8 h-8 text-lotto-amber opacity-60" />
        </h1>
        <p className="text-lotto-muted text-sm">
          Confronto K=1-10 numeri + Extra · Backtest retroattivo
        </p>
      </div>

      {/* K selector tabs */}
      <div className="flex gap-1.5 flex-wrap">
        {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
          <button
            key={n}
            onClick={() => setK(n)}
            className={`w-10 h-10 rounded-lg text-sm font-black transition-all ${
              k === n
                ? "bg-lotto-amber text-white shadow-lg shadow-lotto-amber/30"
                : "bg-[rgba(255,255,255,0.05)] text-lotto-muted hover:text-lotto-text hover:bg-[rgba(255,255,255,0.08)] border border-[rgba(255,255,255,0.08)]"
            }`}
          >
            {n}
          </button>
        ))}
        <span className="self-center text-xs text-lotto-muted ml-2">
          numeri giocati
        </span>
      </div>

      {loading ? (
        <div className="glass p-10 text-center">
          <div className="w-8 h-8 border-2 border-lotto-amber border-t-transparent rounded-full spin mx-auto" />
          <p className="text-lotto-muted text-sm mt-3">Caricamento K={k}...</p>
        </div>
      ) : (
        <>
          {/* Previsione */}
          {previsione && (
            <div className="glass p-6 relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-amber to-yellow-400" />
              <div className="flex flex-wrap items-center justify-between mb-4">
                <div>
                  <p className="text-[11px] text-lotto-muted uppercase tracking-widest mb-1">
                    Previsione {k} numeri + Extra
                  </p>
                  <span className="text-xs px-2 py-0.5 rounded bg-lotto-amber/10 border border-lotto-amber/20 text-lotto-amber font-bold">
                    HE {previsione.he}%
                  </span>
                </div>
                <span className="text-xs text-lotto-muted">
                  Costo: <b className="text-lotto-amber">EUR 2.00</b>
                </span>
              </div>
              <div className="flex gap-2 flex-wrap">
                {previsione.numeri.map((n) => (
                  <NumberBall key={n} number={n} size="lg" glow />
                ))}
              </div>
            </div>
          )}

          {/* Summary */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="glass p-3 text-center">
              <p className="text-[10px] text-lotto-muted uppercase">Giocate</p>
              <p className="text-lg font-black text-lotto-text">{storico.length}</p>
            </div>
            <div className="glass p-3 text-center">
              <p className="text-[10px] text-lotto-muted uppercase">Vinte</p>
              <p className="text-lg font-black text-lotto-green">{wins}</p>
            </div>
            <div className="glass p-3 text-center">
              <p className="text-[10px] text-lotto-muted uppercase">Investito</p>
              <p className="text-lg font-black text-lotto-text">{totalCost}€</p>
            </div>
            <div className="glass p-3 text-center">
              <p className="text-[10px] text-lotto-muted uppercase">Vinto</p>
              <p className="text-lg font-black text-lotto-text">{totalWon.toFixed(0)}€</p>
            </div>
            <div className="glass p-3 text-center">
              <p className="text-[10px] text-lotto-muted uppercase">P&L</p>
              <p className={`text-lg font-black ${totalPnl >= 0 ? "text-lotto-green" : "text-lotto-red"}`}>
                {totalPnl >= 0 ? "+" : ""}{totalPnl.toFixed(2)}€
              </p>
            </div>
          </div>

          {/* Storico */}
          <div className="space-y-2">
            {withCum.slice(0, 50).map((r, idx) => {
              const e = r.estrazione;
              const vincita = e?.vincita_totale ?? 0;
              const pnl = e?.pnl ?? -r.costo;
              const isWin = vincita > 0;
              const azzBase = new Set(e?.numeri_azzeccati ?? []);
              const azzExtra = new Set(e?.numeri_azzeccati_extra ?? []);

              return (
                <div
                  key={idx}
                  className={`glass p-3 relative overflow-hidden ${isWin ? "border-lotto-green/20" : ""}`}
                >
                  {isWin && (
                    <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-green to-lotto-teal" />
                  )}

                  {/* Header */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-lotto-muted">
                        {e?.data} {e?.ora}
                      </span>
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
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-black ${pnl >= 0 ? "text-lotto-green" : "text-lotto-red"}`}>
                        {pnl >= 0 ? "+" : ""}{pnl.toFixed(2)}€
                      </span>
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        r.cumPnl >= 0 ? "bg-lotto-green/10 text-lotto-green" : "bg-lotto-red/10 text-lotto-red"
                      }`}>
                        {r.cumPnl >= 0 ? "+" : ""}{r.cumPnl.toFixed(0)}€
                      </span>
                    </div>
                  </div>

                  {/* Previsione */}
                  <div className="mb-2">
                    <span className="text-[10px] text-lotto-muted uppercase">Prev: </span>
                    <span className="inline-flex gap-1 flex-wrap">
                      {r.previsione.numeri.map((n, i) => (
                        <div key={i} className="flex flex-col items-center gap-0.5">
                          <NumberBall number={n} size="sm" />
                          {(azzBase.has(n) || azzExtra.has(n)) && (
                            <div className="w-1.5 h-1.5 rounded-full bg-lotto-green dot-pulse" />
                          )}
                        </div>
                      ))}
                    </span>
                  </div>

                  {/* Estrazione compatta */}
                  {e?.numeri && (
                    <div className="text-[10px] text-lotto-muted">
                      <span>Base({e.match_base}/{k}): </span>
                      <span className="font-mono">
                        {e.numeri.map((n, i) => (
                          <span key={i} className={azzBase.has(n) ? "text-lotto-green font-bold" : ""}>
                            {n}{i < 19 ? " " : ""}
                          </span>
                        ))}
                      </span>
                      {e.numero_oro && (
                        <span className="ml-1 text-yellow-400">Oro:{e.numero_oro}</span>
                      )}
                      {e.match_extra !== undefined && e.match_extra > 0 && (
                        <span className="ml-1">Extra({e.match_extra})</span>
                      )}
                      {vincita > 0 && (
                        <span className="ml-1 text-lotto-green font-bold">+{vincita.toFixed(2)}€</span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
