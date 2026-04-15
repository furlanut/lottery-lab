"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import NumberBall from "@/components/NumberBall";
import CountdownTimer from "@/components/CountdownTimer";
import type { LottoPrevisione, VinciCasaPrevisione } from "@/lib/api";

interface LivePredictionsProps {
  initialLotto: LottoPrevisione | null;
  initialVinciCasa: VinciCasaPrevisione | null;
  nextLottoDraw: string; // ISO string
  nextVinciCasaDraw: string; // ISO string
}

export default function LivePredictions({
  initialLotto,
  initialVinciCasa,
  nextLottoDraw,
  nextVinciCasaDraw,
}: LivePredictionsProps) {
  const router = useRouter();
  const [lotto] = useState(initialLotto);
  const [vincicasa] = useState(initialVinciCasa);

  const handleDrawPassed = useCallback(() => {
    // Wait 60s then refresh server data
    setTimeout(() => {
      router.refresh();
    }, 60_000);
  }, [router]);

  // Poll every 60s to keep server data fresh
  useEffect(() => {
    const id = setInterval(() => {
      router.refresh();
    }, 60_000);
    return () => clearInterval(id);
  }, [router]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
      {/* VinciCasa */}
      <VinciCasaCard
        previsione={vincicasa}
        nextDraw={nextVinciCasaDraw}
        onDrawPassed={handleDrawPassed}
      />

      {/* Lotto */}
      <LottoCard
        previsione={lotto}
        nextDraw={nextLottoDraw}
        onDrawPassed={handleDrawPassed}
      />
    </div>
  );
}

function VinciCasaCard({
  previsione,
  nextDraw,
  onDrawPassed,
}: {
  previsione: VinciCasaPrevisione | null;
  nextDraw: string;
  onDrawPassed: () => void;
}) {
  return (
    <div className="glass glow-green p-6 fade-up-1 flex flex-col gap-5 relative overflow-hidden">
      {/* Top accent bar */}
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-green to-lotto-teal" />

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-widest gradient-green">
              VinciCasa
            </span>
          </div>
          <p className="text-lotto-muted text-xs">Estrazione giornaliera · 20:00</p>
        </div>
        <CountdownTimer
          nextDrawDate={nextDraw}
          game="VinciCasa"
          onDrawPassed={onDrawPassed}
        />
      </div>

      {/* Numbers */}
      {previsione ? (
        <>
          <div className="flex items-center gap-3 flex-wrap">
            {previsione.numeri.map((n) => (
              <NumberBall key={n} number={n} size="lg" glow />
            ))}
          </div>

          <div className="mt-auto pt-4 border-t border-[rgba(255,255,255,0.06)] flex items-center justify-between">
            <div>
              <p className="text-[10px] text-lotto-muted uppercase tracking-wide mb-0.5">Finestra analisi</p>
              <p className="text-sm font-semibold text-lotto-text">{previsione.finestra} estrazioni</p>
            </div>
            <div className="text-right">
              <p className="text-[10px] text-lotto-muted uppercase tracking-wide mb-0.5">Costo giocata</p>
              <p className="text-sm font-semibold text-lotto-green">EUR 2.00</p>
            </div>
          </div>
        </>
      ) : (
        <EmptyState label="Previsione non disponibile" color="green" />
      )}
    </div>
  );
}

function LottoCard({
  previsione,
  nextDraw,
  onDrawPassed,
}: {
  previsione: LottoPrevisione | null;
  nextDraw: string;
  onDrawPassed: () => void;
}) {
  const ambo = previsione?.ambo_secco;

  return (
    <div className="glass glow-blue p-6 fade-up-2 flex flex-col gap-5 relative overflow-hidden">
      {/* Top accent bar */}
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-lotto-blue to-lotto-purple" />

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-widest gradient-blue">
              Lotto
            </span>
          </div>
          <p className="text-lotto-muted text-xs">Mar · Gio · Sab · 20:00</p>
        </div>
        <CountdownTimer
          nextDrawDate={nextDraw}
          game="Lotto"
          onDrawPassed={onDrawPassed}
        />
      </div>

      {/* Ambo Secco */}
      {ambo ? (
        <>
          <div>
            <p className="text-[10px] text-lotto-muted uppercase tracking-widest mb-3">Ambo Secco</p>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <NumberBall number={ambo.ambo[0]} size="lg" glow />
                <NumberBall number={ambo.ambo[1]} size="lg" glow />
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-[10px] text-lotto-muted uppercase tracking-wide">Ruota</span>
                <span className="text-base font-black text-white uppercase">{ambo.ruota}</span>
              </div>
              <div className="flex flex-col gap-1 ml-auto">
                <span className="text-[10px] text-lotto-muted uppercase tracking-wide">Score</span>
                <span className="text-base font-black gradient-blue">{ambo.score.toFixed(2)}</span>
              </div>
            </div>
          </div>

          <div className="mt-auto pt-4 border-t border-[rgba(255,255,255,0.06)] flex items-center justify-between">
            <div>
              <p className="text-[10px] text-lotto-muted uppercase tracking-wide mb-0.5">Metodo</p>
              <p className="text-sm font-semibold text-lotto-text truncate max-w-[140px]">{ambo.metodo}</p>
            </div>
            <div className="text-right">
              <p className="text-[10px] text-lotto-muted uppercase tracking-wide mb-0.5">Costo/estrazione</p>
              <p className="text-sm font-semibold text-lotto-blue">
                EUR {previsione!.costo_estrazione.toFixed(2)}
              </p>
            </div>
          </div>
        </>
      ) : previsione ? (
        <EmptyState label="Nessun ambo secco attivo" color="blue" />
      ) : (
        <EmptyState label="Previsione non disponibile" color="blue" />
      )}
    </div>
  );
}

function EmptyState({ label, color }: { label: string; color: "blue" | "green" }) {
  const cls = color === "blue" ? "text-lotto-blue" : "text-lotto-green";
  return (
    <div className="flex flex-col items-center justify-center py-8 gap-3">
      <svg
        className={`w-10 h-10 ${cls} opacity-30`}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.5}
      >
        <circle cx="12" cy="12" r="10" />
        <path d="M12 8v4M12 16h.01" />
      </svg>
      <p className="text-sm text-lotto-muted">{label}</p>
    </div>
  );
}
