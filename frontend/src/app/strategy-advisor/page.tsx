import { fetchAPI, StrategyAdvisorStatus } from "@/lib/api";
import NumberBall from "@/components/NumberBall";
import { Sparkles, TrendingUp, Target, AlertCircle } from "lucide-react";
import StrategySimulator from "./StrategySimulator";
import SpecialTimeCountdown from "./SpecialTimeCountdown";

async function getData() {
  try {
    const status = await fetchAPI<StrategyAdvisorStatus>(
      "/strategy-advisor/status"
    );
    return { status, error: false };
  } catch {
    return { status: null, error: true };
  }
}

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function StrategyAdvisorPage() {
  const { status, error } = await getData();

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="fade-up">
        <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-1 flex items-center gap-4">
          <span className="gradient-blue">Strategy</span>{" "}
          <span className="text-lotto-text">Advisor</span>
          <Sparkles className="w-8 h-8 text-lotto-amber opacity-60" />
        </h1>
        <p className="text-lotto-muted text-sm">
          Numeri caldi, strategie ottimali, simulatore per il 10eLotto K=6+Extra
        </p>
      </div>

      {error || !status ? (
        <div className="glass p-10 text-center">
          <p className="text-lotto-text font-semibold">Backend non raggiungibile</p>
        </div>
      ) : (
        <>
          {/* Disclaimer onesto */}
          <div className="glass p-4 border-l-2 border-lotto-amber/40 fade-up-1">
            <p className="text-[11px] text-lotto-amber uppercase tracking-widest font-bold mb-1 flex items-center gap-2">
              <AlertCircle className="w-3.5 h-3.5" />
              Realtà statistica
            </p>
            <p className="text-xs text-lotto-muted leading-relaxed">
              <b className="text-lotto-text">
                P(vincita qualsiasi) e ~{status.invarianti.p_vincita_qualsiasi_media}% per
                QUALSIASI strategia
              </b>{" "}
              — il RNG 10eLotto e uniforme (vedi Appendici H, I, J, K del paper). Tutte le
              selezioni di 6 numeri distinti hanno lo stesso EV analitico: {status.ev_analitico.ev_totale.toFixed(4)}€
              su 2€ giocati, house edge {status.ev_analitico.house_edge.toFixed(2)}%, breakeven {status.ev_analitico.breakeven.toFixed(2)}x.
              Le differenze osservate fra strategie sono DOVUTE ALLA COVARIANZA DEI PAYOFF, non a predittivita.
              <br />
              <b className="text-lotto-amber">Leverage reale: Special Time</b> riduce HE dal{" "}
              {status.special_time.he_normale}% al {status.special_time.he_special_time}% (+{status.special_time.vantaggio_pp.toFixed(1)} pp EV).
            </p>
          </div>

          {/* Countdown Special Time */}
          <section className="fade-up-1">
            <SectionHeader label="Special Time — quando giocare" />
            <SpecialTimeCountdown info={status.special_time} />
          </section>

          {/* Hot / Cold Numbers */}
          <section className="fade-up-2">
            <SectionHeader
              label={`Numeri caldi (top 20) — ultime ${status.dataset.finestra_estrazioni} estrazioni`}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="glass p-5 border-t-2 border-lotto-red/40">
                <h3 className="text-base font-black text-lotto-red mb-1 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Piu frequenti (hot)
                </h3>
                <p className="text-[11px] text-lotto-muted mb-3">
                  Attesa: {status.hot_numbers[0]?.attesa.toFixed(1)} per numero. Deviazione = osservato - attesa.
                </p>
                <div className="grid grid-cols-5 md:grid-cols-10 gap-2">
                  {status.hot_numbers.map((h) => (
                    <div key={h.numero} className="flex flex-col items-center gap-0.5">
                      <NumberBall number={h.numero} size="md" glow />
                      <span className="text-[9px] text-lotto-muted">{h.frequenza}x</span>
                      <span className={`text-[9px] font-bold ${h.deviazione > 0 ? "text-lotto-red" : "text-lotto-muted"}`}>
                        {h.deviazione > 0 ? "+" : ""}{h.deviazione}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass p-5 border-t-2 border-lotto-blue/40">
                <h3 className="text-base font-black text-lotto-blue mb-1 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 rotate-180" />
                  Meno frequenti (cold)
                </h3>
                <p className="text-[11px] text-lotto-muted mb-3">
                  In ritardo — ma il RNG non ha memoria, stessa P della media.
                </p>
                <div className="grid grid-cols-5 md:grid-cols-10 gap-2">
                  {status.cold_numbers.map((h) => (
                    <div key={h.numero} className="flex flex-col items-center gap-0.5">
                      <NumberBall number={h.numero} size="md" />
                      <span className="text-[9px] text-lotto-muted">{h.frequenza}x</span>
                      <span className={`text-[9px] font-bold ${h.deviazione < 0 ? "text-lotto-blue" : "text-lotto-muted"}`}>
                        {h.deviazione > 0 ? "+" : ""}{h.deviazione}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* 3 Strategie consigliate */}
          <section className="fade-up-3">
            <SectionHeader label="3 strategie suggerite per obiettivi diversi" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {status.strategies.map((strat, idx) => {
                const ratioColor = strat.ratio_backtest >= 1.05
                  ? "text-lotto-green"
                  : strat.ratio_backtest >= 1.0
                  ? "text-lotto-amber"
                  : "text-lotto-red";
                const gradientClass = idx === 0
                  ? "from-lotto-green to-lotto-teal"
                  : idx === 1
                  ? "from-lotto-blue to-lotto-purple"
                  : "from-lotto-red to-lotto-amber";

                return (
                  <div key={strat.id} className="glass p-5 relative overflow-hidden">
                    <div className={`absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r ${gradientClass}`} />

                    <div className="flex items-start gap-2 mb-3">
                      <Target className="w-4 h-4 text-lotto-text flex-shrink-0 mt-0.5" />
                      <div>
                        <h3 className="text-base font-black text-lotto-text">{strat.label}</h3>
                        <p className="text-[11px] text-lotto-amber uppercase tracking-wide font-bold mt-0.5">
                          {strat.obiettivo}
                        </p>
                      </div>
                    </div>

                    <p className="text-[11px] text-lotto-muted leading-relaxed mb-3">{strat.desc}</p>

                    {/* Numeri suggeriti */}
                    <div className="mb-4">
                      <p className="text-[10px] text-lotto-muted uppercase mb-2">Cinquina suggerita (aggiornata)</p>
                      <div className="flex gap-1.5 flex-wrap justify-center">
                        {strat.numeri.map((n) => (
                          <NumberBall key={n} number={n} size="md" glow />
                        ))}
                      </div>
                    </div>

                    {/* Stats osservate */}
                    <div className="pt-3 border-t border-[rgba(255,255,255,0.06)] grid grid-cols-3 gap-2">
                      <Stat label="P(≥1€)" value={`${strat.p_win_any_osservata.toFixed(1)}%`} />
                      <Stat label="P(≥10€)" value={`${strat.p_win_10plus_osservata.toFixed(2)}%`} />
                      <Stat label="P(≥100€)" value={`${strat.p_win_100plus_osservata.toFixed(2)}%`} />
                    </div>

                    <div className="mt-3 pt-2 border-t border-[rgba(255,255,255,0.04)]">
                      <p className="text-[10px] text-lotto-muted uppercase">Ratio backtest (34K giocate)</p>
                      <p className={`text-xl font-black ${ratioColor}`}>
                        {strat.ratio_backtest.toFixed(3)}x
                      </p>
                    </div>

                    <p className="text-[10px] text-lotto-muted italic mt-2 leading-relaxed">{strat.note}</p>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Simulatore */}
          <section className="fade-up-3">
            <SectionHeader label="Simulatore — inserisci la tua cinquina" />
            <StrategySimulator />
          </section>

          {/* Raccomandazione finale */}
          <section className="fade-up-3">
            <SectionHeader label="Raccomandazione operativa" />
            <div className="glass p-5">
              <p className="text-sm text-lotto-text leading-relaxed mb-3">
                <b className="text-lotto-amber">Protocollo ottimale</b> per massimizzare valore atteso e minimizzare varianza:
              </p>
              <ol className="space-y-2 text-xs text-lotto-muted list-decimal list-inside ml-2">
                <li>
                  <b className="text-lotto-text">Gioca solo durante Special Time</b> (16:05-18:00): HE dal 9.94% al 6.30%.
                </li>
                <li>
                  <b className="text-lotto-text">Sempre K=6 + Extra</b> (2€ per schedina): HE marginale dell&apos;Extra e 10%, migliore del base 38%.
                </li>
                <li>
                  <b className="text-lotto-text">Scegli numeri Vicinanza</b> per obiettivo vincite medie, <b className="text-lotto-text">Spalmati per decina</b> per obiettivo big win.
                </li>
                <li>
                  <b className="text-lotto-text">Budget fisso mensile</b> (es. 30€): mai aumentare dopo perdite, mai raddoppiare.
                </li>
                <li>
                  <b className="text-lotto-text">Aspettativa realistica</b>: perdita attesa ~6% del budget durante Special Time (contro ~10% in orari normali).
                </li>
              </ol>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center">
      <p className="text-[10px] text-lotto-muted uppercase tracking-wide mb-0.5">{label}</p>
      <p className="text-sm font-black text-lotto-text">{value}</p>
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
