"use client";

import { Clock } from "lucide-react";
import { useEffect, useState } from "react";

function formatDuration(seconds: number): string {
  if (seconds <= 0) return "in corso";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

export default function NextDrawCountdown({
  info,
}: {
  info: {
    iso: string;
    ora: string;
    secondi_a_estrazione: number;
    frequenza_giorno: number;
    orari: string[];
  };
}) {
  const [secondsLeft, setSecondsLeft] = useState(info.secondi_a_estrazione);

  useEffect(() => {
    const interval = setInterval(() => {
      setSecondsLeft((s) => Math.max(0, s - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const urgent = secondsLeft < 900; // meno di 15 minuti

  return (
    <div className="glass p-6 text-center">
      <Clock className={`w-10 h-10 mx-auto mb-3 ${urgent ? "text-lotto-amber" : "text-lotto-muted"}`} />
      <p className="text-[10px] text-lotto-muted uppercase tracking-widest mb-1">
        Prossima estrazione ({info.ora})
      </p>
      <p
        className={`text-3xl font-black mb-2 font-mono ${urgent ? "text-lotto-amber" : "text-lotto-text"}`}
      >
        {formatDuration(secondsLeft)}
      </p>
      <p className="text-xs text-lotto-muted">
        MillionDay estrae <b className="text-lotto-text">2 volte al giorno</b>:{" "}
        {info.orari.map((o, i) => (
          <span key={o}>
            <b className="text-lotto-amber">{o}</b>
            {i < info.orari.length - 1 ? " e " : ""}
          </span>
        ))}
      </p>
    </div>
  );
}
