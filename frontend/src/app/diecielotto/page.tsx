import {
  fetchAPI,
  DiecieLottoPrevisione,
  DiecieLottoStatus,
  DiecieLottoRecord,
} from "@/lib/api";
import NumberBall from "@/components/NumberBall";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import { Timer } from "lucide-react";
import DiecieLottoHistory from "@/components/DiecieLottoHistory";

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "N/D";
  try {
    return format(parseISO(dateStr), "dd/MM/yyyy", { locale: it });
  } catch {
    return dateStr;
  }
}

async function getData() {
  try {
    const [previsione, status, storico] = await Promise.all([
      fetchAPI<DiecieLottoPrevisione>("/diecielotto/previsione"),
      fetchAPI<DiecieLottoStatus>("/diecielotto/status"),
      fetchAPI<DiecieLottoRecord[]>("/diecielotto/storico-completo?limit=200"),
    ]);
    return { previsione, status, storico, error: false };
  } catch {
    return { previsione: null, status: null, storico: [], error: true };
  }
}

export default async function DiecieLottoPage() {
  const { previsione, status, storico, error } = await getData();

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="fade-up">
        <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-1 flex items-center gap-4">
          <span className="gradient-amber">10eLotto</span>
          <Timer className="w-8 h-8 text-lotto-amber opacity-60" />
        </h1>
        <p className="text-lotto-muted text-sm">
          5 Minuti · 6 numeri + Extra · Paper Trading
        </p>
      </div>

      {error ? (
        <OfflineState />
      ) : (
        <>
          {/* Previsione corrente */}
          {previsione && (
            <section className="fade-up-1">
              <SectionHeader label="Previsione corrente" />
              <div className="glass p-6 relative overflow-hidden text-center">
                <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-amber to-yellow-400" />
                <div className="flex items-center justify-center gap-4 flex-wrap mb-4">
                  {previsione.numeri.map((n) => (
                    <NumberBall key={n} number={n} size="lg" glow />
                  ))}
                </div>
                <div className="flex justify-center gap-4 text-xs text-lotto-muted">
                  <span>
                    Metodo: <b className="text-lotto-text">{previsione.metodo}</b>
                  </span>
                  <span>
                    Costo: <b className="text-lotto-amber">EUR 2.00</b>
                  </span>
                  <span className="px-2 py-0.5 rounded bg-lotto-amber/10 border border-lotto-amber/20 text-lotto-amber font-bold">
                    6+Extra · HE 9.94%
                  </span>
                </div>
              </div>
            </section>
          )}

          {/* Stats */}
          {status && (
            <section className="fade-up-2">
              <div className="grid grid-cols-3 gap-4">
                <div className="glass p-4">
                  <p className="text-[11px] text-lotto-muted uppercase tracking-widest mb-1">
                    Estrazioni
                  </p>
                  <p className="text-xl font-black text-lotto-amber">
                    {status.estrazioni_totali.toLocaleString("it-IT")}
                  </p>
                </div>
                <div className="glass p-4">
                  <p className="text-[11px] text-lotto-muted uppercase tracking-widest mb-1">
                    Prima
                  </p>
                  <p className="text-sm font-bold text-lotto-text">
                    {formatDate(status.data_prima)}
                  </p>
                </div>
                <div className="glass p-4">
                  <p className="text-[11px] text-lotto-muted uppercase tracking-widest mb-1">
                    Ultima
                  </p>
                  <p className="text-sm font-bold text-lotto-text">
                    {formatDate(status.data_ultima)}
                  </p>
                </div>
              </div>
            </section>
          )}

          {/* Storico con previsioni abbinate */}
          {storico.length > 0 && (
            <section className="fade-up-3">
              <SectionHeader label="Storico estrazioni + previsioni" />
              <DiecieLottoHistory records={storico} />
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

function OfflineState() {
  return (
    <div className="glass p-10 text-center fade-up-1">
      <p className="text-lotto-text font-semibold mb-1">
        Backend non raggiungibile
      </p>
      <p className="text-lotto-muted text-sm">
        Verifica che il backend sia in esecuzione
      </p>
    </div>
  );
}
