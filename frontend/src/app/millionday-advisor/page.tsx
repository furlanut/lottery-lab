import { fetchAPI, MillionDayAdvisorStatus } from "@/lib/api";
import NumberBall from "@/components/NumberBall";
import { TrendingUp, Target, AlertTriangle, Zap, Coins } from "lucide-react";
import NextDrawCountdown from "./NextDrawCountdown";

async function getData() {
  try {
    const status = await fetchAPI<MillionDayAdvisorStatus>(
      "/millionday/advisor/status"
    );
    return { status, error: false };
  } catch {
    return { status: null, error: true };
  }
}

export const dynamic = "force-dynamic";
export const revalidate = 0;

const COLOR_MAP: Record<
  string,
  { border: string; gradient: string; text: string; bg: string }
> = {
  amber: {
    border: "border-lotto-amber/40",
    gradient: "from-lotto-amber to-yellow-400",
    text: "text-lotto-amber",
    bg: "bg-lotto-amber/10",
  },
  blue: {
    border: "border-lotto-blue/40",
    gradient: "from-lotto-blue to-lotto-purple",
    text: "text-lotto-blue",
    bg: "bg-lotto-blue/10",
  },
  green: {
    border: "border-lotto-green/40",
    gradient: "from-lotto-green to-lotto-teal",
    text: "text-lotto-green",
    bg: "bg-lotto-green/10",
  },
  red: {
    border: "border-lotto-red/40",
    gradient: "from-lotto-red to-lotto-amber",
    text: "text-lotto-red",
    bg: "bg-lotto-red/10",
  },
  purple: {
    border: "border-lotto-purple/40",
    gradient: "from-lotto-purple to-lotto-blue",
    text: "text-lotto-purple",
    bg: "bg-lotto-purple/10",
  },
};

export default async function MillionDayAdvisorPage() {
  const { status, error } = await getData();

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="fade-up">
        <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-1 flex items-center gap-4">
          <span className="gradient-amber">MillionDay</span>{" "}
          <span className="text-lotto-text">Advisor</span>
          <Coins className="w-8 h-8 text-lotto-amber opacity-60" />
        </h1>
        <p className="text-lotto-muted text-sm">
          6 strategie dal window sweep (Appendice L) · ratio robust post-giugno 2024
        </p>
      </div>

      {error || !status ? (
        <div className="glass p-10 text-center">
          <p className="text-lotto-text font-semibold">Backend non raggiungibile</p>
        </div>
      ) : (
        <>
          {/* Disclaimer critico */}
          <div className="glass p-4 border-l-2 border-lotto-red/40 fade-up-1">
            <p className="text-[11px] text-lotto-red uppercase tracking-widest font-bold mb-1 flex items-center gap-2">
              <AlertTriangle className="w-3.5 h-3.5" />
              Importante — leggi prima di giocare
            </p>
            <div className="text-xs text-lotto-muted leading-relaxed space-y-1.5">
              <p>
                <b className="text-lotto-text">Multiple testing</b>:{" "}
                {status.avvertimenti.multiple_testing}
              </p>
              <p>
                <b className="text-lotto-text">Regime bi-fase</b>:{" "}
                {status.avvertimenti.regime_bifase}
              </p>
              <p>
                <b className="text-lotto-text">EV reale</b>:{" "}
                {status.avvertimenti.he_reale}
              </p>
            </div>
          </div>

          {/* Countdown prossima estrazione */}
          <section className="fade-up-1">
            <SectionHeader label="Prossima estrazione" />
            <NextDrawCountdown info={status.prossima_estrazione} />
          </section>

          {/* Ultima estrazione */}
          {status.dataset.ultima_estrazione && (
            <section className="fade-up-1">
              <SectionHeader label="Ultima estrazione" />
              <div className="glass p-4">
                <div className="flex flex-wrap items-center gap-4 md:gap-6">
                  <div>
                    <p className="text-[10px] text-lotto-muted uppercase tracking-widest">
                      {status.dataset.ultima_estrazione.data} — {status.dataset.ultima_estrazione.ora}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="text-[11px] text-lotto-muted uppercase">Base</span>
                    <div className="flex gap-1.5">
                      {status.dataset.ultima_estrazione.numeri.map((n) => (
                        <NumberBall key={n} number={n} size="md" />
                      ))}
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="text-[11px] text-lotto-muted uppercase">Extra</span>
                    <div className="flex gap-1.5">
                      {status.dataset.ultima_estrazione.extra.map((n) => (
                        <NumberBall key={n} number={n} size="md" />
                      ))}
                    </div>
                  </div>
                  <div className="ml-auto text-[11px] text-lotto-muted">
                    Dataset: {status.dataset.totale_db.toLocaleString("it-IT")} estrazioni
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* Hot / Cold Numbers */}
          <section className="fade-up-2">
            <SectionHeader
              label={`Numeri Hot & Cold — ultime ${status.dataset.finestra_visualizzazione} estrazioni`}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="glass p-5 border-t-2 border-lotto-red/40">
                <h3 className="text-base font-black text-lotto-red mb-1 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Hot (top 15)
                </h3>
                <p className="text-[11px] text-lotto-muted mb-3">
                  Attesa: {status.hot_numbers[0]?.attesa.toFixed(1)} per numero
                </p>
                <div className="grid grid-cols-5 gap-2">
                  {status.hot_numbers.map((h) => (
                    <div key={h.numero} className="flex flex-col items-center gap-0.5">
                      <NumberBall number={h.numero} size="md" glow />
                      <span className="text-[9px] text-lotto-muted">{h.frequenza}x</span>
                      <span className={`text-[9px] font-bold ${h.deviazione > 0 ? "text-lotto-red" : "text-lotto-muted"}`}>
                        {h.deviazione > 0 ? "+" : ""}
                        {h.deviazione}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass p-5 border-t-2 border-lotto-blue/40">
                <h3 className="text-base font-black text-lotto-blue mb-1 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 rotate-180" />
                  Cold (bottom 15)
                </h3>
                <p className="text-[11px] text-lotto-muted mb-3">In ritardo sull&apos;attesa</p>
                <div className="grid grid-cols-5 gap-2">
                  {status.cold_numbers.map((h) => (
                    <div key={h.numero} className="flex flex-col items-center gap-0.5">
                      <NumberBall number={h.numero} size="md" />
                      <span className="text-[9px] text-lotto-muted">{h.frequenza}x</span>
                      <span className={`text-[9px] font-bold ${h.deviazione < 0 ? "text-lotto-blue" : "text-lotto-muted"}`}>
                        {h.deviazione > 0 ? "+" : ""}
                        {h.deviazione}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* 6 strategie */}
          <section className="fade-up-3">
            <SectionHeader label="6 strategie dal window sweep — numeri live" />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {status.strategies.map((strat) => {
                const colors = COLOR_MAP[strat.colore] ?? COLOR_MAP.amber;
                const isJackpotSeeker = strat.id === "spread_fasce_W24";
                return (
                  <div key={strat.id} className={`glass p-5 relative overflow-hidden ${isJackpotSeeker ? "border-2 border-lotto-red/30" : ""}`}>
                    <div className={`absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r ${colors.gradient}`} />

                    <div className="flex items-start justify-between gap-2 mb-3">
                      <div className="flex items-start gap-2 flex-1">
                        {isJackpotSeeker ? (
                          <Zap className={`w-5 h-5 ${colors.text} flex-shrink-0 mt-0.5`} />
                        ) : (
                          <Target className={`w-5 h-5 ${colors.text} flex-shrink-0 mt-0.5`} />
                        )}
                        <div>
                          <h3 className={`text-base font-black ${colors.text}`}>{strat.label}</h3>
                          <p className="text-[11px] text-lotto-muted italic mt-0.5">{strat.subtitle}</p>
                        </div>
                      </div>
                      <span
                        className={`text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded-md border whitespace-nowrap ${colors.bg} ${colors.text} ${colors.border}`}
                      >
                        W={strat.window_size}
                      </span>
                    </div>

                    <p className="text-[11px] text-lotto-amber uppercase tracking-wide font-bold mb-1">
                      {strat.obiettivo}
                    </p>
                    <p className="text-[11px] text-lotto-muted leading-relaxed mb-4">{strat.desc}</p>

                    {/* Numeri suggeriti */}
                    <div className="mb-4">
                      <p className="text-[10px] text-lotto-muted uppercase mb-2">
                        Cinquina LIVE (calcolata su {status.dataset.totale_db} estrazioni)
                      </p>
                      <div className="flex gap-2 justify-center">
                        {strat.numeri.map((n) => (
                          <NumberBall key={n} number={n} size="md" glow />
                        ))}
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="pt-3 border-t border-[rgba(255,255,255,0.06)] grid grid-cols-4 gap-2">
                      <Stat label="Ratio val" value={`${strat.ratio_val_robust.toFixed(2)}x`} emphasize />
                      <Stat label="Ratio disc" value={`${strat.ratio_disc_robust.toFixed(2)}x`} />
                      <Stat label="p-value" value={strat.p_value.toFixed(4)} />
                      <Stat label="Big wins" value={strat.big_wins_val.toString()} />
                    </div>

                    <div className="mt-3 pt-2 border-t border-[rgba(255,255,255,0.04)] grid grid-cols-2 gap-3">
                      <div>
                        <p className="text-[10px] text-lotto-muted uppercase">Regime B (2024-06+)</p>
                        <p className={`text-sm font-bold ${colors.text}`}>
                          ratio medio {strat.regime_b_ratio_avg.toFixed(1)}x
                        </p>
                      </div>
                      <div>
                        <p className="text-[10px] text-lotto-muted uppercase">Bucket sopra BE</p>
                        <p className="text-sm font-bold text-lotto-text">{strat.regime_b_bucket_sopra_be}</p>
                      </div>
                    </div>

                    <p className="text-[10px] text-lotto-muted italic mt-2 leading-relaxed">
                      {strat.note}
                    </p>
                  </div>
                );
              })}
            </div>
          </section>

          {/* EV + conclusioni */}
          <section className="fade-up-3">
            <SectionHeader label="EV analitico MillionDay (K=5 + Extra, 2€)" />
            <div className="glass p-5 grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard label="EV base" value={`${status.ev_analitico.ev_base.toFixed(3)}€`} sub="su 1€" />
              <MetricCard label="EV Extra" value={`${status.ev_analitico.ev_extra.toFixed(3)}€`} sub="su 1€" />
              <MetricCard
                label="EV totale"
                value={`${status.ev_analitico.ev_totale.toFixed(4)}€`}
                sub="su 2€"
              />
              <MetricCard
                label="House edge"
                value={`${status.ev_analitico.house_edge.toFixed(2)}%`}
                sub={`BE ${status.ev_analitico.breakeven.toFixed(3)}x`}
                color="text-lotto-red"
              />
            </div>
          </section>

          {/* Raccomandazione */}
          <section className="fade-up-3">
            <SectionHeader label="Come usare questo Advisor" />
            <div className="glass p-5">
              <p className="text-sm text-lotto-text leading-relaxed mb-3">
                <b className="text-lotto-amber">Protocollo proposto</b> per giocare MillionDay con questo advisor:
              </p>
              <ol className="space-y-2 text-xs text-lotto-muted list-decimal list-inside ml-2">
                <li>
                  <b className="text-lotto-text">Scegli UNA strategia</b> (no ensemble): diversificare riduce varianza ma non EV. Se scegli piu strategie, stai solo giocando piu cinquine — HE resta 33.7%.
                </li>
                <li>
                  <b className="text-lotto-text">Attiva sempre l&apos;Extra</b> (+1€): riduce HE marginale dal 35% al 32%.
                </li>
                <li>
                  <b className="text-lotto-text">Raccomandato</b>: <span className="text-lotto-blue">Dual 3B+2E W=103 o W=104</span> — miglior coerenza disc/val (1.27-1.51 disc vs 2.95 val), piu stabile del cold.
                </li>
                <li>
                  <b className="text-lotto-text">⚡ Jackpot Seeker (W=24)</b>: gioca solo se accetti la volatilita estrema. Ratio 1.6x con cap ma ha azzeccato un 5/5 nel backtest. Probabilmente fortuna.
                </li>
                <li>
                  <b className="text-lotto-text">Budget fisso giornaliero</b> (max 4€/giorno = 1 giocata per estrazione). Mai raddoppiare.
                </li>
                <li>
                  <b className="text-lotto-text">Aspettativa</b>: perdita attesa 34% del budget nel lungo termine. Il ratio 3x osservato non e statisticamente confermato.
                </li>
              </ol>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  emphasize,
}: {
  label: string;
  value: string;
  emphasize?: boolean;
}) {
  return (
    <div className="text-center">
      <p className="text-[10px] text-lotto-muted uppercase tracking-wide mb-0.5">{label}</p>
      <p className={`${emphasize ? "text-base" : "text-sm"} font-black text-lotto-text`}>
        {value}
      </p>
    </div>
  );
}

function MetricCard({
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
    <div className="glass p-3 text-center">
      <p className="text-[10px] text-lotto-muted uppercase tracking-wide mb-0.5">{label}</p>
      <p className={`text-lg font-black ${color}`}>{value}</p>
      {sub && <p className="text-[10px] text-lotto-muted mt-0.5">{sub}</p>}
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
