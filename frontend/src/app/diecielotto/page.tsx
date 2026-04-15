import {
  fetchAPI,
  DiecieLottoPrevisione,
  DiecieLottoEstrazione,
  DiecieLottoStatus,
} from "@/lib/api";
import NumberBall from "@/components/NumberBall";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import { Timer } from "lucide-react";

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "N/D";
  try {
    return format(parseISO(dateStr), "dd/MM/yyyy", { locale: it });
  } catch {
    return dateStr;
  }
}

async function getDiecieLottoData() {
  try {
    const [previsione, estrazioni, status] = await Promise.all([
      fetchAPI<DiecieLottoPrevisione>("/diecielotto/previsione"),
      fetchAPI<DiecieLottoEstrazione[]>("/diecielotto/estrazioni?limit=10"),
      fetchAPI<DiecieLottoStatus>("/diecielotto/status"),
    ]);
    return { previsione, estrazioni, status, error: false };
  } catch {
    return { previsione: null, estrazioni: [], status: null, error: true };
  }
}

export default async function DiecieLottoPage() {
  const { previsione, estrazioni, status, error } = await getDiecieLottoData();

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="fade-up">
        <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-1 flex items-center gap-4">
          <span className="gradient-amber">10eLotto</span>
          <Timer className="w-8 h-8 text-lotto-amber opacity-60" />
        </h1>
        <p className="text-lotto-muted text-sm">5 Minuti · 20 numeri su 90</p>
      </div>

      {error ? (
        <OfflineState />
      ) : (
        <>
          {/* Previsione */}
          {previsione && (
            <section className="fade-up-1 space-y-5">
              <SectionHeader label="Previsione corrente" />

              <div className="glass p-8 relative overflow-hidden text-center">
                <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-amber to-yellow-400" />
                <div className="absolute -top-20 -right-20 w-64 h-64 bg-lotto-amber/5 rounded-full blur-3xl pointer-events-none" />

                <p className="text-[10px] font-bold uppercase tracking-widest text-lotto-muted mb-2">
                  Numeri consigliati
                </p>

                {/* Badge */}
                <div className="flex justify-center mb-6">
                  <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-lotto-amber/10 border border-lotto-amber/20 text-[10px] font-bold uppercase tracking-widest text-lotto-amber">
                    6 numeri + Extra &bull; HE 9.94%
                  </span>
                </div>

                <div className="flex items-center justify-center gap-4 flex-wrap mb-8">
                  {previsione.numeri.map((n) => (
                    <NumberBall key={n} number={n} size="lg" glow />
                  ))}
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6 border-t border-[rgba(255,255,255,0.06)]">
                  <MiniStat label="Metodo" value={previsione.metodo} />
                  <MiniStat
                    label="Score"
                    value={previsione.score.toFixed(2)}
                    color="amber"
                  />
                  <MiniStat
                    label="Configurazione"
                    value={`${previsione.configurazione} numeri`}
                  />
                  <MiniStat
                    label="Costo giocata"
                    value="EUR 2.00"
                    color="amber"
                  />
                </div>

                {previsione.dettagli && (
                  <p className="mt-5 text-xs text-lotto-muted leading-relaxed text-left">
                    {previsione.dettagli}
                  </p>
                )}
              </div>
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
                        <th className="px-4 py-3 text-left text-[10px] text-lotto-muted uppercase tracking-widest whitespace-nowrap">
                          Concorso
                        </th>
                        <th className="px-4 py-3 text-left text-[10px] text-lotto-muted uppercase tracking-widest">
                          Data
                        </th>
                        <th className="px-4 py-3 text-left text-[10px] text-lotto-muted uppercase tracking-widest">
                          Ora
                        </th>
                        <th className="px-4 py-3 text-left text-[10px] text-lotto-muted uppercase tracking-widest min-w-[320px]">
                          20 Numeri
                        </th>
                        <th className="px-4 py-3 text-left text-[10px] text-lotto-muted uppercase tracking-widest whitespace-nowrap">
                          N. Oro
                        </th>
                        <th className="px-4 py-3 text-left text-[10px] text-lotto-muted uppercase tracking-widest whitespace-nowrap">
                          Doppio Oro
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {estrazioni.map((e, idx) => (
                        <>
                          <tr
                            key={`main-${e.id}`}
                            className={`border-b border-[rgba(255,255,255,0.04)] hover:bg-[rgba(255,255,255,0.02)] transition-colors ${
                              idx % 2 === 0 ? "" : "bg-[rgba(255,255,255,0.01)]"
                            }`}
                          >
                            <td className="px-4 py-3 text-lotto-muted font-mono text-xs whitespace-nowrap">
                              #{e.concorso}
                            </td>
                            <td className="px-4 py-3 text-lotto-text text-xs whitespace-nowrap">
                              {formatDate(e.data)}
                            </td>
                            <td className="px-4 py-3 text-lotto-muted font-mono text-xs whitespace-nowrap">
                              {e.ora}
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex gap-1 flex-wrap">
                                {e.numeri.map((n, i) => (
                                  <NumberBall key={i} number={n} size="sm" />
                                ))}
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="ring-2 ring-yellow-400/60 rounded-full inline-flex shadow-md shadow-yellow-400/20">
                                <NumberBall number={e.numero_oro} size="sm" glow />
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="ring-2 ring-lotto-amber/50 rounded-full inline-flex shadow-md shadow-lotto-amber/15">
                                <NumberBall number={e.doppio_oro} size="sm" glow />
                              </div>
                            </td>
                          </tr>
                          {e.numeri_extra && e.numeri_extra.length > 0 && (
                            <tr
                              key={`extra-${e.id}`}
                              className={`border-b border-[rgba(255,255,255,0.03)] ${
                                idx % 2 === 0 ? "" : "bg-[rgba(255,255,255,0.01)]"
                              }`}
                            >
                              <td colSpan={3} className="px-4 py-1.5 text-[10px] text-lotto-muted uppercase tracking-widest">
                                Extra
                              </td>
                              <td colSpan={3} className="px-4 py-1.5">
                                <div className="flex gap-1 flex-wrap opacity-50">
                                  {e.numeri_extra.map((n, i) => (
                                    <NumberBall key={i} number={n} size="sm" />
                                  ))}
                                </div>
                              </td>
                            </tr>
                          )}
                        </>
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
                  color="amber"
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
  color?: "amber" | "green" | "blue";
}) {
  const colorMap = {
    amber: "text-lotto-amber",
    green: "text-lotto-green",
    blue: "text-lotto-blue",
  };
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
  color?: "amber" | "green" | "blue";
}) {
  const colorMap = {
    amber: "text-lotto-amber",
    green: "text-lotto-green",
    blue: "text-lotto-blue",
  };
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
