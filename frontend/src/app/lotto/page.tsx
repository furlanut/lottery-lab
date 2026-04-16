import {
  fetchAPI,
  LottoPrevisione,
  LottoStatusData,
} from "@/lib/api";
import NumberBall from "@/components/NumberBall";
import { Dice1 } from "lucide-react";
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

interface LottoRecord {
  data: string;
  previsione: { numeri: number[]; ruota: string; metodo: string; tipo: string; score: number };
  estrazione: { numeri: number[]; ruota: string };
  match: number;
  vincita: number;
  costo: number;
  pnl: number;
  stato: string;
}

async function getData() {
  try {
    const [previsione, status, storico] = await Promise.all([
      fetchAPI<LottoPrevisione>("/lotto/previsione"),
      fetchAPI<LottoStatusData>("/lotto/status"),
      fetchAPI<LottoRecord[]>("/lotto/storico-completo?limit=50"),
    ]);
    return { previsione, status, storico, error: false };
  } catch {
    return { previsione: null, status: null, storico: [], error: true };
  }
}

export default async function LottoPage() {
  const { previsione, status, storico, error } = await getData();

  // P&L
  const totalCost = storico.reduce((s, r) => s + r.costo, 0);
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
          <span className="gradient-blue">Lotto</span>
          <Dice1 className="w-8 h-8 text-lotto-blue opacity-60" />
        </h1>
        <p className="text-lotto-muted text-sm">Engine V6 · Vicinanza + freq_rit_fib</p>
      </div>

      {error ? (
        <div className="glass p-10 text-center">
          <p className="text-lotto-text font-semibold">Backend non raggiungibile</p>
        </div>
      ) : (
        <>
          {/* Previsione V6 */}
          {previsione?.ambo_secco && (
            <section className="fade-up-1">
              <SectionHeader label="Previsione corrente" />
              <div className="glass p-6 relative overflow-hidden">
                <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-blue to-lotto-purple" />
                <div className="flex items-center gap-6 mb-4">
                  <div className="flex gap-3">
                    <NumberBall number={previsione.ambo_secco.ambo[0]} size="xl" glow />
                    <NumberBall number={previsione.ambo_secco.ambo[1]} size="xl" glow />
                  </div>
                  <div>
                    <p className="text-sm text-lotto-muted">Ruota</p>
                    <p className="text-white font-black uppercase">{previsione.ambo_secco.ruota}</p>
                    <p className="text-xs text-lotto-muted mt-1">{previsione.ambo_secco.metodo}</p>
                  </div>
                  <div className="ml-auto text-right">
                    <span className="text-xs px-2 py-0.5 rounded bg-lotto-blue/10 border border-lotto-blue/20 text-lotto-blue font-bold">
                      Score: {previsione.ambo_secco.score.toFixed(2)}
                    </span>
                    <p className="text-xs text-lotto-muted mt-1">Costo: EUR {previsione.costo_estrazione}</p>
                  </div>
                </div>
                {previsione.ambetti.length > 0 && (
                  <div className="pt-3 border-t border-[rgba(255,255,255,0.06)]">
                    <p className="text-[10px] text-lotto-muted uppercase tracking-widest mb-2">Ambetti</p>
                    <div className="flex gap-4 flex-wrap">
                      {previsione.ambetti.map((a, i) => (
                        <div key={i} className="flex items-center gap-2">
                          <NumberBall number={a.ambo[0]} size="md" />
                          <NumberBall number={a.ambo[1]} size="md" />
                          <span className="text-xs text-lotto-muted uppercase">{a.ruota}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}

          {/* Spiegazione */}
          <div className="glass p-4 border-l-2 border-lotto-blue/40">
            <p className="text-[11px] text-lotto-blue uppercase tracking-widest font-bold mb-1">Engine V6</p>
            <p className="text-xs text-lotto-muted leading-relaxed">
              Ambo secco: freq_rit_fib (W=75) — numeri con rapporto frequenza/ritardo vicino a Fibonacci.
              Ambetto: vicinanza cross-decina |a-b|≤20 (W=125) — coppie di numeri vicini. HE: 37.6%.
            </p>
          </div>

          {/* Stats + P&L */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <div className="glass p-3 text-center">
              <p className="text-[10px] text-lotto-muted uppercase">Estrazioni</p>
              <p className="text-lg font-black text-lotto-blue">{status?.estrazioni_totali.toLocaleString()}</p>
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
              <p className={`text-lg font-black ${totalPnl >= 0 ? "text-lotto-green" : "text-lotto-red"}`}>
                {totalPnl >= 0 ? "+" : ""}{totalPnl.toFixed(0)}€
              </p>
            </div>
            <div className="glass p-3 text-center">
              <p className="text-[10px] text-lotto-muted uppercase">Max vincita</p>
              <p className="text-lg font-black text-lotto-amber">{maxWin.toFixed(0)}€</p>
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
                    <div key={idx} className={`glass p-3 relative overflow-hidden ${isWin ? "border-lotto-green/20" : ""}`}>
                      {isWin && <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-green to-lotto-teal" />}
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono text-lotto-muted">{formatDate(r.data)}</span>
                          <span className="text-[10px] text-lotto-blue font-bold uppercase">{r.previsione.ruota}</span>
                          <span className="text-[10px] text-lotto-muted">{r.previsione.tipo}</span>
                          <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded border ${
                            isWin ? "bg-lotto-green/10 text-lotto-green border-lotto-green/20" : "bg-lotto-red/10 text-lotto-red border-lotto-red/20"
                          }`}>{r.stato}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`text-sm font-black ${r.pnl >= 0 ? "text-lotto-green" : "text-lotto-red"}`}>
                            {r.pnl >= 0 ? "+" : ""}{r.pnl.toFixed(0)}€
                          </span>
                          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${thisCum >= 0 ? "bg-lotto-green/10 text-lotto-green" : "bg-lotto-red/10 text-lotto-red"}`}>
                            Cum {thisCum >= 0 ? "+" : ""}{thisCum.toFixed(0)}€
                          </span>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-[10px] text-lotto-muted uppercase mb-1">Previsione</p>
                          <div className="flex gap-2">
                            {r.previsione.numeri.map((n, i) => {
                              const matched = r.estrazione.numeri.includes(n);
                              return (
                                <div key={i} className="flex flex-col items-center gap-0.5">
                                  <NumberBall number={n} size="md" glow={matched} />
                                  {matched && <div className="w-1.5 h-1.5 rounded-full bg-lotto-green dot-pulse" />}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                        <div>
                          <p className="text-[10px] text-lotto-muted uppercase mb-1">Estratti · {r.estrazione.ruota}</p>
                          <div className="flex gap-1.5">
                            {r.estrazione.numeri.map((n, i) => {
                              const matched = r.previsione.numeri.includes(n);
                              return (
                                <div key={i} className={matched ? "ring-2 ring-lotto-green ring-offset-1 ring-offset-[#0c0c1d] rounded-full" : ""}>
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
      <h2 className="text-xs font-bold uppercase tracking-widest text-lotto-muted whitespace-nowrap">{label}</h2>
      <div className="flex-1 h-px bg-[rgba(255,255,255,0.05)]" />
    </div>
  );
}
