import {
  fetchAPI,
  MillionDayPrevisione,
  MillionDayStatusData,
} from "@/lib/api";
import NumberBall from "@/components/NumberBall";
import { Coins } from "lucide-react";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "N/D";
  try {
    return format(parseISO(dateStr), "dd/MM/yyyy", { locale: it });
  } catch {
    return dateStr;
  }
}

interface MDRecord {
  data: string;
  ora: string;
  previsione: { numeri: number[]; metodo: string };
  estrazione: { numeri: number[]; extra: number[] };
  match_base: number;
  match_extra: number;
  vincita_base: number;
  vincita_extra: number;
  vincita: number;
  costo: number;
  pnl: number;
  stato: string;
}

async function getData() {
  try {
    const [previsione, status, storico] = await Promise.all([
      fetchAPI<MillionDayPrevisione>("/millionday/previsione"),
      fetchAPI<MillionDayStatusData>("/millionday/status"),
      fetchAPI<MDRecord[]>("/millionday/storico-completo?limit=40"),
    ]);
    return { previsione, status, storico, error: false };
  } catch {
    return { previsione: null, status: null, storico: [], error: true };
  }
}

export default async function MillionDayPage() {
  const { previsione, status, storico, error } = await getData();

  const totalCost = storico.length * 2;
  const totalWon = storico.reduce((s, r) => s + r.vincita, 0);
  const totalPnl = totalWon - totalCost;
  const wins = storico.filter((r) => r.vincita > 0).length;
  const maxWin = Math.max(0, ...storico.map((r) => r.vincita));

  let cumPnl = 0;
  const reversed = [...storico].reverse();
  const cumMap = new Map<number, number>();
  reversed.forEach((r, i) => {
    cumPnl += r.pnl;
    cumMap.set(storico.length - 1 - i, cumPnl);
  });

  return (
    <div className="space-y-10">
      <div className="fade-up">
        <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-1 flex items-center gap-4">
          <span className="gradient-amber">MillionDay</span>
          <Coins className="w-8 h-8 text-lotto-amber opacity-60" />
        </h1>
        <p className="text-lotto-muted text-sm">
          5 numeri su 55 + Extra · 2 estrazioni/giorno (13:00 · 20:30)
        </p>
      </div>

      {error ? (
        <div className="glass p-10 text-center">
          <p className="text-lotto-text font-semibold">Backend non raggiungibile</p>
        </div>
      ) : (
        <>
          {/* Previsione */}
          {previsione && previsione.numeri.length === 5 && (
            <section className="fade-up-1">
              <SectionHeader label="Previsione prossimo turno" />
              <div className="glass p-6 relative overflow-hidden text-center">
                <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-amber to-lotto-red" />
                <div className="flex items-center justify-center gap-4 flex-wrap mb-4">
                  {previsione.numeri.map((n) => (
                    <NumberBall key={n} number={n} size="xl" glow />
                  ))}
                </div>
                <div className="flex justify-center gap-3 text-xs text-lotto-muted flex-wrap">
                  <span>
                    Metodo:{" "}
                    <b className="text-lotto-text">optfreq W={previsione.finestra}</b>
                  </span>
                  <span>
                    Costo: <b className="text-lotto-amber">EUR 2.00</b> (base + Extra)
                  </span>
                  <span className="px-2 py-0.5 rounded bg-lotto-amber/10 border border-lotto-amber/20 text-lotto-amber font-bold">
                    Score {previsione.score.toFixed(2)}x
                  </span>
                  <span className="px-2 py-0.5 rounded bg-lotto-red/10 border border-lotto-red/20 text-lotto-red font-bold">
                    HE {previsione.house_edge.toFixed(1)}%
                  </span>
                </div>
              </div>
            </section>
          )}

          {/* Spiegazione */}
          <div className="glass p-4 border-l-2 border-lotto-amber/40">
            <p className="text-[11px] text-lotto-amber uppercase tracking-widest font-bold mb-1">
              optfreq W=60 (meno-peggio tra ~50 configurazioni)
            </p>
            <p className="text-xs text-lotto-muted leading-relaxed">
              Top 5 numeri con frequenza piu vicina all&apos;attesa (~5.45 in 60 estrazioni), ne troppo caldi ne troppo freddi.
              Ratio validation 1.343x con coerenza discovery 1.404x (p=0.050 borderline, FAIL Bonferroni).
              Sotto il breakeven 1.508x.{" "}
              <b>Il sistema non produce profitto atteso</b> — e la strategia statisticamente piu solida fra quelle testate.
              Premi netti: 2/5=EUR 2, 3/5=EUR 50, 4/5=EUR 1.000, 5/5=EUR 1M. Con Extra: 2/5=EUR 4, 3/5=EUR 100, 4/5=EUR 1.000, 5/5=EUR 100k.
            </p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <div className="glass p-3 text-center">
              <p className="text-[10px] text-lotto-muted uppercase">Estrazioni</p>
              <p className="text-lg font-black text-lotto-amber">
                {status?.estrazioni_totali.toLocaleString()}
              </p>
            </div>
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
              <p className="text-[10px] text-lotto-muted uppercase">P&L</p>
              <p
                className={`text-lg font-black ${
                  totalPnl >= 0 ? "text-lotto-green" : "text-lotto-red"
                }`}
              >
                {totalPnl >= 0 ? "+" : ""}
                {totalPnl.toFixed(2)}€
              </p>
            </div>
            <div className="glass p-3 text-center">
              <p className="text-[10px] text-lotto-muted uppercase">Max vincita</p>
              <p className="text-lg font-black text-lotto-amber">{maxWin.toFixed(2)}€</p>
            </div>
          </div>

          {/* Storico */}
          {storico.length > 0 && (
            <section className="fade-up-3">
              <SectionHeader label="Storico previsioni vs estrazioni" />
              <div className="space-y-2">
                {storico.map((r, idx) => {
                  const isWin = r.vincita > 0;
                  const thisCum = cumMap.get(idx) ?? 0;
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
                      <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-mono text-lotto-muted">
                            {formatDate(r.data)}
                          </span>
                          <span className="text-[10px] text-lotto-amber font-bold">
                            {r.ora}
                          </span>
                          <span
                            className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded border ${
                              isWin
                                ? "bg-lotto-green/10 text-lotto-green border-lotto-green/20"
                                : "bg-lotto-red/10 text-lotto-red border-lotto-red/20"
                            }`}
                          >
                            {r.stato}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-sm font-black ${
                              r.pnl >= 0 ? "text-lotto-green" : "text-lotto-red"
                            }`}
                          >
                            {r.pnl >= 0 ? "+" : ""}
                            {r.pnl.toFixed(2)}€
                          </span>
                          <span
                            className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                              thisCum >= 0
                                ? "bg-lotto-green/10 text-lotto-green"
                                : "bg-lotto-red/10 text-lotto-red"
                            }`}
                          >
                            Cum {thisCum >= 0 ? "+" : ""}
                            {thisCum.toFixed(0)}€
                          </span>
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4">
                        <div>
                          <p className="text-[10px] text-lotto-muted uppercase mb-1">
                            Previsione (5 su 55)
                          </p>
                          <div className="flex gap-2 flex-wrap">
                            {r.previsione.numeri.map((n, i) => {
                              const matchedBase = r.estrazione.numeri.includes(n);
                              const matchedExtra =
                                !matchedBase && r.estrazione.extra.includes(n);
                              return (
                                <div
                                  key={i}
                                  className="flex flex-col items-center gap-0.5"
                                >
                                  <NumberBall
                                    number={n}
                                    size="md"
                                    glow={matchedBase || matchedExtra}
                                  />
                                  {matchedBase && (
                                    <div className="w-1.5 h-1.5 rounded-full bg-lotto-green dot-pulse" />
                                  )}
                                  {matchedExtra && (
                                    <div className="w-1.5 h-1.5 rounded-full bg-lotto-amber dot-pulse" />
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                        <div>
                          <p className="text-[10px] text-lotto-muted uppercase mb-1">
                            Base estratti
                          </p>
                          <div className="flex gap-1.5 flex-wrap">
                            {r.estrazione.numeri.map((n, i) => {
                              const matched = r.previsione.numeri.includes(n);
                              return (
                                <div
                                  key={i}
                                  className={
                                    matched
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
                        <div>
                          <p className="text-[10px] text-lotto-muted uppercase mb-1">
                            Extra (da 50)
                          </p>
                          <div className="flex gap-1.5 flex-wrap">
                            {r.estrazione.extra.map((n, i) => {
                              const matched = r.previsione.numeri.includes(n);
                              return (
                                <div
                                  key={i}
                                  className={
                                    matched
                                      ? "ring-2 ring-lotto-amber ring-offset-1 ring-offset-[#0c0c1d] rounded-full"
                                      : ""
                                  }
                                >
                                  <NumberBall number={n} size="md" />
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          )}
        </>
      )}
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
