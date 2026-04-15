import { fetchAPI, DiecieLottoRecord } from "@/lib/api";
import NumberBall from "@/components/NumberBall";
import { Timer } from "lucide-react";
import DiecieLottoHistory from "@/components/DiecieLottoHistory";

interface Prev10 {
  numeri: number[];
  metodo: string;
  score: number;
  costo: number;
  configurazione: number;
  dettagli: string;
}

async function getData() {
  try {
    const [previsione, storico] = await Promise.all([
      fetchAPI<Prev10>("/diecielotto10/previsione"),
      fetchAPI<DiecieLottoRecord[]>("/diecielotto10/storico-completo?limit=100"),
    ]);
    return { previsione, storico, error: false };
  } catch {
    return { previsione: null, storico: [], error: true };
  }
}

export default async function DiecieLotto10Page() {
  const { previsione, storico, error } = await getData();

  return (
    <div className="space-y-10">
      <div className="fade-up">
        <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-1 flex items-center gap-4">
          <span className="gradient-amber">10eLotto</span>
          <span className="text-lotto-text text-2xl">10 numeri</span>
          <Timer className="w-8 h-8 text-lotto-amber opacity-60" />
        </h1>
        <p className="text-lotto-muted text-sm">
          10 numeri + Extra · HE 34.29%
        </p>
      </div>

      {error ? (
        <div className="glass p-10 text-center">
          <p className="text-lotto-text font-semibold mb-1">Backend non raggiungibile</p>
        </div>
      ) : (
        <>
          {previsione && (
            <section className="fade-up-1">
              <div className="flex items-center gap-3 mb-4">
                <h2 className="text-xs font-bold uppercase tracking-widest text-lotto-muted">
                  Previsione corrente
                </h2>
                <div className="flex-1 h-px bg-[rgba(255,255,255,0.05)]" />
              </div>
              <div className="glass p-6 relative overflow-hidden text-center">
                <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-amber to-yellow-400" />
                <div className="flex items-center justify-center gap-3 flex-wrap mb-4">
                  {previsione.numeri.map((n) => (
                    <NumberBall key={n} number={n} size="lg" glow />
                  ))}
                </div>
                <div className="flex justify-center gap-4 text-xs text-lotto-muted">
                  <span>
                    Metodo: <b className="text-lotto-text">{previsione.metodo}</b>
                  </span>
                  <span>
                    Costo: <b className="text-lotto-amber">EUR {previsione.costo.toFixed(2)}</b>
                  </span>
                  <span className="px-2 py-0.5 rounded bg-lotto-amber/10 border border-lotto-amber/20 text-lotto-amber font-bold">
                    10 numeri + Extra · HE 34.29%
                  </span>
                </div>
              </div>
            </section>
          )}

          {storico.length > 0 && (
            <section className="fade-up-2">
              <div className="flex items-center gap-3 mb-4">
                <h2 className="text-xs font-bold uppercase tracking-widest text-lotto-muted">
                  Storico estrazioni + previsioni (10 numeri)
                </h2>
                <div className="flex-1 h-px bg-[rgba(255,255,255,0.05)]" />
              </div>
              <DiecieLottoHistory records={storico} />
            </section>
          )}
        </>
      )}
    </div>
  );
}
