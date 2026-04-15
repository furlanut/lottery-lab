import {
  fetchAPI,
  VinciCasaPrevisione,
  Estrazione,
  VinciCasaStatusData,
} from "@/lib/api";
import NumberBall from "@/components/NumberBall";
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

async function getVinciCasaData() {
  try {
    const [previsione, estrazioni, status] = await Promise.all([
      fetchAPI<VinciCasaPrevisione>("/vincicasa/previsione"),
      fetchAPI<Estrazione[]>("/vincicasa/estrazioni?limit=10"),
      fetchAPI<VinciCasaStatusData>("/vincicasa/status"),
    ]);
    return { previsione, estrazioni, status, error: false };
  } catch {
    return { previsione: null, estrazioni: [], status: null, error: true };
  }
}

export default async function VinciCasaPage() {
  const { previsione, estrazioni, status, error } = await getVinciCasaData();

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="fade-up">
        <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-1">
          <span className="gradient-green">VinciCasa</span>
        </h1>
        <p className="text-lotto-muted text-sm">Estrazione giornaliera · 5 numeri su 40</p>
      </div>

      {error ? (
        <OfflineState />
      ) : (
        <>
          {/* Previsione */}
          {previsione && (
            <section className="fade-up-1 space-y-5">
              <SectionHeader label="Previsione corrente" />

              {/* Big Numbers Card */}
              <div className="glass p-8 relative overflow-hidden text-center">
                <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-green to-lotto-teal" />
                <div className="absolute -top-20 -right-20 w-64 h-64 bg-lotto-green/5 rounded-full blur-3xl pointer-events-none" />

                <p className="text-[10px] font-bold uppercase tracking-widest text-lotto-muted mb-6">
                  Numeri consigliati
                </p>

                <div className="flex items-center justify-center gap-4 flex-wrap mb-8">
                  {previsione.numeri.map((n) => (
                    <NumberBall key={n} number={n} size="xl" glow />
                  ))}
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 pt-6 border-t border-[rgba(255,255,255,0.06)]">
                  <MiniStat
                    label="Finestra analisi"
                    value={`${previsione.finestra} estrazioni`}
                    color="green"
                  />
                  <MiniStat
                    label="Generata il"
                    value={formatDate(previsione.data_generazione)}
                  />
                  <MiniStat
                    label="Costo giocata"
                    value="EUR 2.00"
                    color="green"
                  />
                </div>

                {previsione.dettagli && (
                  <p className="mt-5 text-xs text-lotto-muted leading-relaxed text-left">
                    {previsione.dettagli}
                  </p>
                )}
              </div>

              {/* Frequency Chart */}
              {Object.keys(previsione.frequenze).length > 0 && (
                <FrequencyChart
                  frequenze={previsione.frequenze}
                  hotNumbers={previsione.numeri}
                />
              )}
            </section>
          )}

          {/* Ultime Estrazioni */}
          {estrazioni.length > 0 && (
            <section className="fade-up-2">
              <SectionHeader label="Ultime estrazioni" />
              <div className="glass overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-[rgba(255,255,255,0.06)]">
                        <th className="px-4 py-3 text-left text-[10px] text-lotto-muted uppercase tracking-widest">
                          Concorso
                        </th>
                        <th className="px-4 py-3 text-left text-[10px] text-lotto-muted uppercase tracking-widest">
                          Data
                        </th>
                        <th className="px-4 py-3 text-left text-[10px] text-lotto-muted uppercase tracking-widest">
                          Numeri
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {estrazioni.map((e, idx) => (
                        <tr
                          key={e.id}
                          className={`border-b border-[rgba(255,255,255,0.04)] last:border-0 hover:bg-[rgba(255,255,255,0.02)] transition-colors ${
                            idx % 2 === 0 ? "" : "bg-[rgba(255,255,255,0.01)]"
                          }`}
                        >
                          <td className="px-4 py-3 text-lotto-muted font-mono text-xs">
                            #{e.concorso}
                          </td>
                          <td className="px-4 py-3 text-lotto-text text-xs">
                            {formatDate(e.data)}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex gap-1.5 flex-wrap">
                              {e.numeri.map((n, i) => (
                                <NumberBall key={i} number={n} size="sm" />
                              ))}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>
          )}

          {/* Stats */}
          {status && (
            <section className="fade-up-3">
              <SectionHeader label="Statistiche" />
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <StatCard
                  label="Estrazioni totali"
                  value={status.estrazioni_totali.toLocaleString("it-IT")}
                  color="green"
                />
                <StatCard
                  label="Prima estrazione"
                  value={formatDate(status.data_prima)}
                />
                <StatCard
                  label="Ultima estrazione"
                  value={formatDate(status.data_ultima)}
                />
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function FrequencyChart({
  frequenze,
  hotNumbers,
}: {
  frequenze: Record<string, number>;
  hotNumbers: number[];
}) {
  const maxFreq = Math.max(...Object.values(frequenze), 1);
  const allNums = Array.from({ length: 40 }, (_, i) => i + 1);
  const hot = new Set(hotNumbers);

  return (
    <div className="glass p-5">
      <div className="flex items-center justify-between mb-4">
        <p className="text-[10px] font-bold uppercase tracking-widest text-lotto-muted">
          Frequenze · 1–40
        </p>
        <div className="flex items-center gap-3 text-[10px] text-lotto-muted">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm bg-lotto-green" /> Hot
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm bg-[rgba(255,255,255,0.15)]" /> Normal
          </span>
        </div>
      </div>

      <div className="flex items-end gap-0.5 h-20">
        {allNums.map((n) => {
          const freq = frequenze[String(n)] ?? 0;
          const heightPct = freq > 0 ? Math.max((freq / maxFreq) * 100, 8) : 4;
          const isHot = hot.has(n);
          return (
            <div
              key={n}
              className="flex-1 flex flex-col items-center justify-end gap-0.5 group"
            >
              <div
                className={`w-full rounded-t-sm freq-bar transition-all ${
                  isHot
                    ? "bg-gradient-to-t from-lotto-green to-lotto-teal shadow-sm shadow-lotto-green/40"
                    : "bg-[rgba(255,255,255,0.12)]"
                }`}
                style={{ height: `${heightPct}%` }}
                title={`${n}: ${freq}`}
              />
            </div>
          );
        })}
      </div>

      {/* Number labels — only show every 5 */}
      <div className="flex items-end gap-0.5 mt-1">
        {allNums.map((n) => (
          <div key={n} className="flex-1 flex justify-center">
            {n % 5 === 0 ? (
              <span className="text-[8px] text-lotto-muted">{n}</span>
            ) : null}
          </div>
        ))}
      </div>

      {/* Hot numbers row */}
      <div className="mt-4 pt-4 border-t border-[rgba(255,255,255,0.06)]">
        <p className="text-[10px] text-lotto-muted uppercase tracking-widest mb-2">
          Numeri in previsione
        </p>
        <div className="flex gap-2 flex-wrap">
          {hotNumbers.map((n) => (
            <div key={n} className="flex flex-col items-center gap-1">
              <NumberBall number={n} size="sm" glow />
              <span className="text-[9px] text-lotto-muted">
                {frequenze[String(n)] ?? 0}x
              </span>
            </div>
          ))}
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

function MiniStat({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: "green" | "blue";
}) {
  const colorMap = { green: "text-lotto-green", blue: "text-lotto-blue" };
  return (
    <div>
      <p className="text-[10px] text-lotto-muted uppercase tracking-wide mb-0.5">{label}</p>
      <p className={`text-sm font-bold ${color ? colorMap[color] : "text-lotto-text"}`}>
        {value}
      </p>
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: "green" | "blue";
}) {
  const colorMap = { green: "text-lotto-green", blue: "text-lotto-blue" };
  return (
    <div className="glass p-4">
      <p className="text-[10px] text-lotto-muted uppercase tracking-widest mb-1">{label}</p>
      <p className={`text-xl font-black ${color ? colorMap[color] : "text-lotto-text"}`}>
        {value}
      </p>
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
