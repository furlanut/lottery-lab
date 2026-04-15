import {
  fetchAPI,
  PaperTradingRiepilogo,
  PaperTradingRecord,
  GamePnL,
} from "@/lib/api";
import PaperTradingHistory from "@/components/PaperTradingHistory";
import { TrendingUp } from "lucide-react";

function formatCurrency(value: number): string {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)} EUR`;
}

async function getPaperTradingData() {
  try {
    const [riepilogo, storico] = await Promise.all([
      fetchAPI<PaperTradingRiepilogo>("/paper-trading/riepilogo"),
      fetchAPI<PaperTradingRecord[]>("/paper-trading/storico?limit=50"),
    ]);
    return { riepilogo, storico, error: false };
  } catch {
    return { riepilogo: null, storico: [], error: true };
  }
}

const GAME_CONFIG: Record<
  string,
  { label: string; color: "blue" | "green" | "amber"; colorClass: string; bgClass: string; borderClass: string }
> = {
  lotto: {
    label: "Lotto",
    color: "blue",
    colorClass: "text-lotto-blue",
    bgClass: "bg-lotto-blue/10",
    borderClass: "border-lotto-blue/20",
  },
  vincicasa: {
    label: "VinciCasa",
    color: "green",
    colorClass: "text-lotto-green",
    bgClass: "bg-lotto-green/10",
    borderClass: "border-lotto-green/20",
  },
  diecielotto: {
    label: "10eLotto",
    color: "amber",
    colorClass: "text-lotto-amber",
    bgClass: "bg-lotto-amber/10",
    borderClass: "border-lotto-amber/20",
  },
};

export default async function PaperTradingPage() {
  const { riepilogo, storico, error } = await getPaperTradingData();

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="fade-up">
        <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-1 flex items-center gap-4">
          <span className="gradient-blue">Paper</span>{" "}
          <span className="text-lotto-text">Trading</span>
          <TrendingUp className="w-8 h-8 text-lotto-blue opacity-60" />
        </h1>
        <p className="text-lotto-muted text-sm">Tracciamento P&amp;L simulato · Tutti i giochi</p>
      </div>

      {error ? (
        <OfflineState />
      ) : (
        <>
          {/* Game Cards */}
          {riepilogo && (
            <>
              <section className="fade-up-1">
                <SectionHeader label="Performance per gioco" />
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                  {Object.entries(riepilogo.giochi).map(([key, pnl]) => (
                    <GameCard key={key} gameKey={key} pnl={pnl} />
                  ))}
                </div>
              </section>

              {/* Total Card */}
              <section className="fade-up-2">
                <SectionHeader label="Totale aggregato" />
                <TotalCard totale={riepilogo.totale} />
              </section>
            </>
          )}

          {/* Per-game detailed history with filter */}
          {storico.length > 0 && (
            <section className="fade-up-3">
              <SectionHeader label="Storico giocate — dettaglio per estrazione" />
              <PaperTradingHistory records={storico} />
            </section>
          )}

          {!riepilogo && storico.length === 0 && (
            <div className="glass p-10 text-center">
              <p className="text-lotto-muted">Nessuna giocata registrata.</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function GameCard({ gameKey, pnl }: { gameKey: string; pnl: GamePnL }) {
  const config = GAME_CONFIG[gameKey] ?? {
    label: gameKey,
    color: "blue" as const,
    colorClass: "text-lotto-blue",
    bgClass: "bg-lotto-blue/10",
    borderClass: "border-lotto-blue/20",
  };

  const pnlPositive = pnl.pnl >= 0;

  return (
    <div className="glass p-6 relative overflow-hidden">
      <div
        className={`absolute top-0 left-0 right-0 h-0.5 ${
          config.color === "blue"
            ? "bg-gradient-to-r from-lotto-blue to-lotto-purple"
            : config.color === "green"
            ? "bg-gradient-to-r from-lotto-green to-lotto-teal"
            : "bg-gradient-to-r from-lotto-amber to-yellow-400"
        }`}
      />

      {/* Game name + badge */}
      <div className="flex items-center justify-between mb-5">
        <h3 className={`text-base font-black ${config.colorClass}`}>
          {config.label}
        </h3>
        <span
          className={`text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded-md border ${config.bgClass} ${config.colorClass} ${config.borderClass}`}
        >
          {config.label}
        </span>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-3 gap-3 mb-5">
        <div className="text-center">
          <p className="text-[11px] text-lotto-muted uppercase tracking-wide mb-0.5">Giocate</p>
          <p className="text-lg font-black text-lotto-text">{pnl.giocate}</p>
        </div>
        <div className="text-center">
          <p className="text-[11px] text-lotto-muted uppercase tracking-wide mb-0.5">Vinte</p>
          <p className="text-lg font-black text-lotto-green">{pnl.vinte}</p>
        </div>
        <div className="text-center">
          <p className="text-[11px] text-lotto-muted uppercase tracking-wide mb-0.5">Perse</p>
          <p className="text-lg font-black text-lotto-red">{pnl.perse}</p>
        </div>
      </div>

      {/* P&L + ROI */}
      <div className="pt-4 border-t border-[rgba(255,255,255,0.06)] grid grid-cols-2 gap-4">
        <div>
          <p className="text-[11px] text-lotto-muted uppercase tracking-wide mb-0.5">P&amp;L</p>
          <p
            className={`text-xl font-black ${
              pnlPositive ? "text-lotto-green" : "text-lotto-red"
            }`}
          >
            {formatCurrency(pnl.pnl)}
          </p>
        </div>
        <div>
          <p className="text-[11px] text-lotto-muted uppercase tracking-wide mb-0.5">Hit Rate</p>
          <p className="text-sm font-bold text-lotto-text">
            {(pnl.hit_rate * 100).toFixed(1)}%
          </p>
          <p className="text-[11px] text-lotto-muted mt-1">
            ROI{" "}
            <span
              className={`font-bold ${
                pnl.pnl >= 0 ? "text-lotto-green" : "text-lotto-red"
              }`}
            >
              {pnl.totale_giocato > 0
                ? `${((pnl.pnl / pnl.totale_giocato) * 100).toFixed(1)}%`
                : "N/D"}
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}

function TotalCard({
  totale,
}: {
  totale: PaperTradingRiepilogo["totale"];
}) {
  const pnlPositive = totale.pnl >= 0;

  return (
    <div className="glass p-6 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-blue via-lotto-green to-lotto-amber" />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div>
          <p className="text-[11px] text-lotto-muted uppercase tracking-widest mb-1">
            Totale giocato
          </p>
          <p className="text-2xl font-black text-lotto-text">
            {totale.totale_giocato.toFixed(2)} EUR
          </p>
        </div>
        <div>
          <p className="text-[11px] text-lotto-muted uppercase tracking-widest mb-1">
            Totale vinto
          </p>
          <p className="text-2xl font-black text-lotto-text">
            {totale.totale_vinto.toFixed(2)} EUR
          </p>
        </div>
        <div>
          <p className="text-[11px] text-lotto-muted uppercase tracking-widest mb-1">P&amp;L</p>
          <p
            className={`text-2xl font-black ${
              pnlPositive ? "text-lotto-green" : "text-lotto-red"
            }`}
          >
            {formatCurrency(totale.pnl)}
          </p>
        </div>
        <div>
          <p className="text-[11px] text-lotto-muted uppercase tracking-widest mb-1">ROI</p>
          <p
            className={`text-2xl font-black ${
              totale.roi >= 0 ? "text-lotto-green" : "text-lotto-red"
            }`}
          >
            {totale.roi.toFixed(1)}%
          </p>
        </div>
      </div>
    </div>
  );
}

function SectionHeader({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <h2 className="text-xs font-bold uppercase tracking-widest text-lotto-muted whitespace-nowrap">
        {label}
      </h2>
      <div className="flex-1 h-px bg-[rgba(255,255,255,0.05)]" />
    </div>
  );
}

function OfflineState() {
  return (
    <div className="glass p-10 text-center fade-up-1">
      <div className="w-12 h-12 rounded-full bg-lotto-red/10 border border-lotto-red/20 flex items-center justify-center mx-auto mb-4">
        <svg className="w-6 h-6 text-lotto-red" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <path d="M18.364 5.636a9 9 0 010 12.728M5.636 5.636a9 9 0 000 12.728M9 10a3 3 0 100 4 3 3 0 000-4z" />
        </svg>
      </div>
      <p className="text-lotto-text font-semibold mb-1">Backend non raggiungibile</p>
      <p className="text-lotto-muted text-sm">Verifica che il backend sia in esecuzione</p>
    </div>
  );
}
