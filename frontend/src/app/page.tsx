import { fetchAPI, DashboardData, LottoPrevisione, VinciCasaPrevisione, DiecieLottoStatus, PaperTradingRiepilogo } from "@/lib/api";
import LivePredictions from "@/components/LivePredictions";
import { format, addDays, setHours, setMinutes, setSeconds, setMilliseconds } from "date-fns";
import { it } from "date-fns/locale";

// Calculate next draw datetime for Lotto (Tue/Thu/Sat at 20:00 Rome time)
// We approximate Rome time as UTC+2 (CEST, valid Apr-Oct)
function nextLottoDraw(): string {
  const now = new Date();
  // Lotto days: 2=Tue, 4=Thu, 6=Sat
  const lottoDays = [2, 4, 6];
  const drawHour = 20; // 20:00 Rome ≈ 18:00 UTC in summer

  for (let i = 0; i <= 7; i++) {
    const candidate = addDays(now, i);
    const day = candidate.getDay();
    if (lottoDays.includes(day)) {
      // Set to 20:00 local
      const dt = setMilliseconds(setSeconds(setMinutes(setHours(candidate, drawHour), 0), 0), 0);
      if (dt > now) return dt.toISOString();
    }
  }
  // Fallback: next Saturday
  return addDays(now, 7).toISOString();
}

// VinciCasa is daily at 20:00
function nextVinciCasaDraw(): string {
  const now = new Date();
  const drawHour = 20;
  let candidate = setMilliseconds(setSeconds(setMinutes(setHours(now, drawHour), 0), 0), 0);
  if (candidate <= now) {
    candidate = addDays(candidate, 1);
  }
  return candidate.toISOString();
}

async function getData() {
  try {
    const [dashboard, lottoPrevisione, vcPrevisione, diecieLottoStatus, paperTrading] =
      await Promise.allSettled([
        fetchAPI<DashboardData>("/dashboard"),
        fetchAPI<LottoPrevisione>("/lotto/previsione"),
        fetchAPI<VinciCasaPrevisione>("/vincicasa/previsione"),
        fetchAPI<DiecieLottoStatus>("/diecielotto/status"),
        fetchAPI<PaperTradingRiepilogo>("/paper-trading/riepilogo"),
      ]);

    return {
      dashboard: dashboard.status === "fulfilled" ? dashboard.value : null,
      lotto: lottoPrevisione.status === "fulfilled" ? lottoPrevisione.value : null,
      vincicasa: vcPrevisione.status === "fulfilled" ? vcPrevisione.value : null,
      diecielotto: diecieLottoStatus.status === "fulfilled" ? diecieLottoStatus.value : null,
      paperTrading: paperTrading.status === "fulfilled" ? paperTrading.value : null,
    };
  } catch {
    return { dashboard: null, lotto: null, vincicasa: null, diecielotto: null, paperTrading: null };
  }
}

export default async function DashboardPage() {
  const { dashboard, lotto, vincicasa, diecielotto, paperTrading } = await getData();
  const today = format(new Date(), "EEEE d MMMM yyyy", { locale: it });

  return (
    <div className="space-y-10">
      {/* Hero */}
      <div className="fade-up">
        <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-1">
          <span className="gradient-blue">Lottery</span>{" "}
          <span className="text-lotto-text">Lab</span>
        </h1>
        <p className="text-lotto-muted capitalize text-sm">{today}</p>
      </div>

      {/* Live Predictions */}
      <section className="fade-up-1">
        <SectionHeader
          label="Previsioni prossime estrazioni"
          badge="LIVE"
          badgeColor="blue"
        />
        <LivePredictions
          initialLotto={lotto}
          initialVinciCasa={vincicasa}
          nextLottoDraw={nextLottoDraw()}
          nextVinciCasaDraw={nextVinciCasaDraw()}
        />
      </section>

      {/* Database Stats */}
      {dashboard && (
        <section className="fade-up-2">
          <SectionHeader label="Statistiche database" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatMetric
              label="Estrazioni Lotto"
              value={dashboard.lotto.estrazioni_totali.toLocaleString("it-IT")}
              color="blue"
            />
            <StatMetric
              label="Estrazioni VinciCasa"
              value={dashboard.vincicasa.estrazioni_totali.toLocaleString("it-IT")}
              color="green"
            />
            <StatMetric
              label="Estrazioni 10eLotto"
              value={
                diecielotto
                  ? diecielotto.estrazioni_totali.toLocaleString("it-IT")
                  : "—"
              }
              color="amber"
            />
            <StatMetric
              label="Previsioni vinte"
              value={String(dashboard.lotto.previsioni_vinte)}
              color="purple"
            />
          </div>
        </section>
      )}

      {/* Paper Trading P&L Summary */}
      {paperTrading && (
        <section className="fade-up-2">
          <SectionHeader label="Paper Trading — P&L corrente" />
          <div className="glass p-5 relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-blue via-lotto-green to-lotto-amber" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
              <div>
                <p className="text-[10px] text-lotto-muted uppercase tracking-widest mb-1">
                  Totale giocato
                </p>
                <p className="text-xl font-black text-lotto-text">
                  {paperTrading.totale.totale_giocato.toFixed(2)} EUR
                </p>
              </div>
              <div>
                <p className="text-[10px] text-lotto-muted uppercase tracking-widest mb-1">
                  Totale vinto
                </p>
                <p className="text-xl font-black text-lotto-text">
                  {paperTrading.totale.totale_vinto.toFixed(2)} EUR
                </p>
              </div>
              <div>
                <p className="text-[10px] text-lotto-muted uppercase tracking-widest mb-1">P&amp;L</p>
                <p
                  className={`text-xl font-black ${
                    paperTrading.totale.pnl >= 0 ? "text-lotto-green" : "text-lotto-red"
                  }`}
                >
                  {paperTrading.totale.pnl >= 0 ? "+" : ""}
                  {paperTrading.totale.pnl.toFixed(2)} EUR
                </p>
              </div>
              <div>
                <p className="text-[10px] text-lotto-muted uppercase tracking-widest mb-1">ROI</p>
                <p
                  className={`text-xl font-black ${
                    paperTrading.totale.roi >= 0 ? "text-lotto-green" : "text-lotto-red"
                  }`}
                >
                  {paperTrading.totale.roi.toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Prossime Estrazioni */}
      {dashboard && dashboard.prossime_estrazioni.length > 0 && (
        <section className="fade-up-3">
          <SectionHeader label="Calendario prossime estrazioni" />
          <div className="glass overflow-hidden">
            {dashboard.prossime_estrazioni.map((entry, i) => (
              <div
                key={i}
                className={`flex items-center justify-between px-5 py-3.5 ${
                  i < dashboard.prossime_estrazioni.length - 1
                    ? "border-b border-[rgba(255,255,255,0.05)]"
                    : ""
                } hover:bg-[rgba(255,255,255,0.02)] transition-colors`}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded-md border ${
                      entry.gioco === "Lotto"
                        ? "bg-lotto-blue/10 text-lotto-blue border-lotto-blue/20"
                        : "bg-lotto-green/10 text-lotto-green border-lotto-green/20"
                    }`}
                  >
                    {entry.gioco}
                  </span>
                  <span className="text-sm text-lotto-text capitalize">
                    {entry.giorno} &mdash; {entry.data}
                  </span>
                </div>
                <span className="text-sm text-lotto-muted font-mono">
                  {entry.ora}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* API offline state */}
      {!dashboard && !lotto && !vincicasa && (
        <div className="glass p-10 text-center fade-up-1">
          <div className="w-12 h-12 rounded-full bg-lotto-red/10 border border-lotto-red/20 flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-lotto-red" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M18.364 5.636a9 9 0 010 12.728M5.636 5.636a9 9 0 000 12.728M9 10a3 3 0 100 4 3 3 0 000-4z"/>
            </svg>
          </div>
          <p className="text-lotto-text font-semibold mb-1">Backend non raggiungibile</p>
          <p className="text-lotto-muted text-sm">
            Verifica che il backend sia in esecuzione su{" "}
            <code className="text-lotto-blue bg-lotto-blue/10 px-1.5 py-0.5 rounded text-xs">
              localhost:8000
            </code>
          </p>
        </div>
      )}
    </div>
  );
}

function SectionHeader({
  label,
  badge,
  badgeColor,
}: {
  label: string;
  badge?: string;
  badgeColor?: "blue" | "green";
}) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <h2 className="text-xs font-bold uppercase tracking-widest text-lotto-muted">
        {label}
      </h2>
      {badge && (
        <span
          className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border ${
            badgeColor === "blue"
              ? "bg-lotto-blue/10 text-lotto-blue border-lotto-blue/20"
              : "bg-lotto-green/10 text-lotto-green border-lotto-green/20"
          }`}
        >
          <span className={`w-1 h-1 rounded-full dot-pulse ${badgeColor === "blue" ? "bg-lotto-blue" : "bg-lotto-green"}`} />
          {badge}
        </span>
      )}
      <div className="flex-1 h-px bg-[rgba(255,255,255,0.05)]" />
    </div>
  );
}

function StatMetric({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: "blue" | "green" | "purple" | "amber";
}) {
  const colorMap = {
    blue: "text-lotto-blue",
    green: "text-lotto-green",
    purple: "text-lotto-purple",
    amber: "text-lotto-amber",
  };

  return (
    <div className="glass p-4">
      <p className="text-[10px] text-lotto-muted uppercase tracking-widest mb-1">{label}</p>
      <p className={`text-2xl font-black ${colorMap[color]}`}>{value}</p>
    </div>
  );
}
