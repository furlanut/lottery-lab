"use client";

import { useState, useEffect, useCallback } from "react";
import NumberBall from "@/components/NumberBall";
import { DiecieLottoRecord } from "@/lib/api";
import DiecieLottoHistory from "@/components/DiecieLottoHistory";
import { Timer } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

interface Metodo {
  id: string;
  label: string;
  desc: string;
  spiegazione: string;
}

interface Previsione {
  numeri: number[];
  metodo: string;
  score: number;
  costo: number;
  configurazione: number;
  dettagli: string;
}

interface Status {
  estrazioni_totali: number;
  data_prima: string | null;
  data_ultima: string | null;
}

export default function DiecieLottoPage() {
  const [metodo, setMetodo] = useState("vicinanza");
  const [metodi, setMetodi] = useState<Metodo[]>([]);
  const [previsione, setPrevisione] = useState<Previsione | null>(null);
  const [storico, setStorico] = useState<DiecieLottoRecord[]>([]);
  const [status, setStatus] = useState<Status | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/diecielotto/metodi`)
      .then((r) => r.json())
      .then(setMetodi)
      .catch(() => {});
    fetch(`${API_BASE}/diecielotto/status`)
      .then((r) => r.json())
      .then(setStatus)
      .catch(() => {});
  }, []);

  const fetchData = useCallback(async (m: string) => {
    setLoading(true);
    try {
      const [prevRes, storRes] = await Promise.all([
        fetch(`${API_BASE}/diecielotto/previsione`),
        fetch(`${API_BASE}/diecielotto/storico-completo?metodo=${m}&limit=2000`),
      ]);
      if (prevRes.ok) setPrevisione(await prevRes.json());
      if (storRes.ok) setStorico(await storRes.json());
    } catch {
      /* ignore */
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData(metodo);
  }, [metodo, fetchData]);

  const selectedMetodo = metodi.find((m) => m.id === metodo);

  // P&L
  const totalCost = storico.length * 2;
  const totalWon = storico.reduce(
    (s, r) => s + (r.estrazione?.vincita_totale ?? 0),
    0
  );
  const totalPnl = totalWon - totalCost;
  const wins = storico.filter(
    (r) => (r.estrazione?.vincita_totale ?? 0) > 0
  ).length;
  const maxWin = Math.max(
    0,
    ...storico.map((r) => r.estrazione?.vincita_totale ?? 0)
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-1 flex items-center gap-4">
          <span className="gradient-amber">10eLotto</span>
          <Timer className="w-8 h-8 text-lotto-amber opacity-60" />
        </h1>
        <p className="text-lotto-muted text-sm">
          6 numeri + Extra · Paper Trading
        </p>
      </div>

      {/* Previsione corrente */}
      {previsione && (
        <div className="glass p-6 relative overflow-hidden text-center">
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-amber to-yellow-400" />
          <p className="text-[11px] text-lotto-muted uppercase tracking-widest mb-3">
            Previsione corrente · {previsione.metodo}
          </p>
          <div className="flex items-center justify-center gap-3 flex-wrap mb-4">
            {previsione.numeri.map((n) => (
              <NumberBall key={n} number={n} size="lg" glow />
            ))}
          </div>
          <div className="flex justify-center gap-3 text-xs text-lotto-muted">
            <span>
              Costo: <b className="text-lotto-amber">EUR 2.00</b>
            </span>
            <span className="px-2 py-0.5 rounded bg-lotto-amber/10 border border-lotto-amber/20 text-lotto-amber font-bold">
              6+Extra · HE 9.94%
            </span>
          </div>
        </div>
      )}

      {/* Metodo selector + info */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-end justify-between gap-4">
          {status && (
            <div className="flex gap-4 text-xs text-lotto-muted">
              <span>
                Estrazioni:{" "}
                <b className="text-lotto-text">
                  {status.estrazioni_totali.toLocaleString()}
                </b>
              </span>
              <span>
                Ultima: <b className="text-lotto-text">{status.data_ultima}</b>
              </span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <label className="text-[11px] text-lotto-muted uppercase tracking-widest">
              Metodo:
            </label>
            <select
              value={metodo}
              onChange={(e) => setMetodo(e.target.value)}
              className="bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.12)] text-lotto-text rounded-lg px-3 py-1.5 text-sm focus:border-lotto-amber focus:outline-none"
            >
              {metodi.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label} — {m.desc}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Spiegazione metodo */}
        {selectedMetodo && (
          <div className="glass p-4 border-l-2 border-lotto-blue/40">
            <p className="text-[11px] text-lotto-blue uppercase tracking-widest font-bold mb-1">
              {selectedMetodo.label}
            </p>
            <p className="text-xs text-lotto-muted leading-relaxed">
              {selectedMetodo.spiegazione}
            </p>
          </div>
        )}
      </div>

      {/* P&L Summary + Max Win */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
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
          <p className="text-lg font-black text-lotto-text">
            {totalWon.toFixed(0)}€
          </p>
        </div>
        <div className="glass p-3 text-center">
          <p className="text-[10px] text-lotto-muted uppercase">P&L</p>
          <p
            className={`text-lg font-black ${totalPnl >= 0 ? "text-lotto-green" : "text-lotto-red"}`}
          >
            {totalPnl >= 0 ? "+" : ""}
            {totalPnl.toFixed(2)}€
          </p>
        </div>
        <div className="glass p-3 text-center">
          <p className="text-[10px] text-lotto-muted uppercase">Max vincita</p>
          <p className="text-lg font-black text-lotto-amber">
            {maxWin.toFixed(2)}€
          </p>
        </div>
      </div>

      {/* Storico */}
      {loading ? (
        <div className="glass p-10 text-center">
          <div className="w-8 h-8 border-2 border-lotto-amber border-t-transparent rounded-full spin mx-auto" />
          <p className="text-lotto-muted text-sm mt-3">
            Caricamento {metodo}...
          </p>
        </div>
      ) : storico.length > 0 ? (
        <DiecieLottoHistory records={storico} />
      ) : (
        <div className="glass p-10 text-center">
          <p className="text-lotto-muted">Nessuna giocata disponibile</p>
        </div>
      )}
    </div>
  );
}
