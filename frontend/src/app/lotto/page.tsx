import {
  fetchAPI,
  LottoPrevisione,
  Estrazione,
  LottoStatusData,
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

async function getLottoData() {
  try {
    const [previsione, estrazioni, status] = await Promise.all([
      fetchAPI<LottoPrevisione>("/lotto/previsione"),
      fetchAPI<Estrazione[]>("/lotto/estrazioni?limit=50"),
      fetchAPI<LottoStatusData>("/lotto/status"),
    ]);
    return { previsione, estrazioni, status, error: false };
  } catch {
    return { previsione: null, estrazioni: [], status: null, error: true };
  }
}

export default async function LottoPage() {
  const { previsione, estrazioni, status, error } = await getLottoData();

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="fade-up">
        <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-1">
          <span className="gradient-blue">Lotto</span>
        </h1>
        <p className="text-lotto-muted text-sm">Ambo secco · Filtri convergenti</p>
      </div>

      {error ? (
        <OfflineState />
      ) : (
        <>
          {/* Previsione */}
          {previsione && (
            <section className="fade-up-1 space-y-5">
              <SectionHeader label="Previsione corrente" />

              {/* Ambo Secco */}
              {previsione.ambo_secco ? (
                <div className="glass p-6 relative overflow-hidden">
                  <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-blue to-lotto-purple" />

                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-widest text-lotto-muted mb-1">
                        Ambo Secco
                      </p>
                      <p className="text-sm text-lotto-text font-medium">
                        {previsione.ambo_secco.metodo}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="text-right">
                        <p className="text-[10px] text-lotto-muted mb-1 uppercase tracking-wide">Score</p>
                        <p className="text-2xl font-black gradient-blue">
                          {previsione.ambo_secco.score.toFixed(2)}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-end gap-6 mb-6">
                    <div className="flex items-center gap-4">
                      <NumberBall number={previsione.ambo_secco.ambo[0]} size="xl" glow />
                      <NumberBall number={previsione.ambo_secco.ambo[1]} size="xl" glow />
                    </div>
                    <div className="flex flex-col gap-3 pb-1">
                      <div>
                        <p className="text-[10px] text-lotto-muted uppercase tracking-wide mb-0.5">Ruota</p>
                        <p className="text-xl font-black text-white uppercase">{previsione.ambo_secco.ruota}</p>
                      </div>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-[rgba(255,255,255,0.06)] grid grid-cols-2 md:grid-cols-4 gap-4">
                    <MiniStat label="Frequenza" value={String(previsione.ambo_secco.frequenza)} />
                    <MiniStat label="Ritardo" value={String(previsione.ambo_secco.ritardo)} />
                    <MiniStat label="Costo estrazione" value={`${previsione.costo_estrazione.toFixed(2)} EUR`} accent="blue" />
                    <MiniStat label="Costo ciclo" value={`${previsione.costo_ciclo.toFixed(2)} EUR`} />
                  </div>

                  {previsione.ambo_secco.dettagli && (
                    <p className="mt-4 text-xs text-lotto-muted leading-relaxed">
                      {previsione.ambo_secco.dettagli}
                    </p>
                  )}
                </div>
              ) : (
                <div className="glass p-8 text-center">
                  <p className="text-lotto-muted">Nessun ambo secco attivo per questa estrazione.</p>
                </div>
              )}

              {/* Ambetti */}
              {previsione.ambetti.length > 0 && (
                <div className="glass overflow-hidden">
                  <div className="px-5 py-4 border-b border-[rgba(255,255,255,0.06)] flex items-center justify-between">
                    <p className="text-xs font-bold uppercase tracking-widest text-lotto-muted">Ambetti</p>
                    <span className="text-xs text-lotto-muted">{previsione.ambetti.length} ambi</span>
                  </div>
                  <div className="divide-y divide-[rgba(255,255,255,0.04)]">
                    {previsione.ambetti.map((amb, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-4 px-5 py-3.5 hover:bg-[rgba(255,255,255,0.02)] transition-colors"
                      >
                        <span className="text-xs text-lotto-muted w-4">{i + 1}</span>
                        <div className="flex gap-2">
                          <NumberBall number={amb.ambo[0]} size="md" />
                          <NumberBall number={amb.ambo[1]} size="md" />
                        </div>
                        <span className="text-xs font-bold uppercase text-lotto-muted tracking-widest">
                          {amb.ruota}
                        </span>
                        <span className="text-xs text-lotto-muted ml-auto">
                          {amb.metodo}
                        </span>
                        <span className="text-xs font-mono font-bold text-lotto-blue">
                          {amb.score.toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
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
                          Ruota
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
                            <span className="text-[10px] font-bold uppercase tracking-widest text-lotto-muted">
                              {e.ruota ?? "—"}
                            </span>
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
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard
                  label="Estrazioni totali"
                  value={status.estrazioni_totali.toLocaleString("it-IT")}
                  color="blue"
                />
                <StatCard
                  label="Prima estrazione"
                  value={formatDate(status.data_prima)}
                />
                <StatCard
                  label="Ultima estrazione"
                  value={formatDate(status.data_ultima)}
                />
                <StatCard
                  label="Previsioni vinte"
                  value={String(status.previsioni_vinte)}
                  color="green"
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
  accent,
}: {
  label: string;
  value: string;
  accent?: "blue" | "green";
}) {
  const colorMap = { blue: "text-lotto-blue", green: "text-lotto-green" };
  return (
    <div>
      <p className="text-[10px] text-lotto-muted uppercase tracking-wide mb-0.5">{label}</p>
      <p className={`text-sm font-bold ${accent ? colorMap[accent] : "text-lotto-text"}`}>
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
  color?: "blue" | "green";
}) {
  const colorMap = { blue: "text-lotto-blue", green: "text-lotto-green" };
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
