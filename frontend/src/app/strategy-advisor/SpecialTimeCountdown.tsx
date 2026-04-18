"use client";

import { SpecialTimeInfo } from "@/lib/api";
import { Clock, CheckCircle } from "lucide-react";
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

export default function SpecialTimeCountdown({ info }: { info: SpecialTimeInfo }) {
  const [secondsLeft, setSecondsLeft] = useState(info.secondi_a_inizio);
  const [inProgress, setInProgress] = useState(info.in_corso);

  useEffect(() => {
    const interval = setInterval(() => {
      setSecondsLeft((s) => Math.max(0, s - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Recompute inProgress as timer hits zero
  useEffect(() => {
    if (secondsLeft <= 0 && !inProgress) {
      setInProgress(true);
    }
  }, [secondsLeft, inProgress]);

  if (inProgress) {
    return (
      <div className="glass p-6 text-center border-2 border-lotto-green/30 relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-lotto-green to-lotto-teal" />
        <CheckCircle className="w-12 h-12 text-lotto-green mx-auto mb-3" />
        <h3 className="text-2xl font-black text-lotto-green mb-1">SPECIAL TIME IN CORSO</h3>
        <p className="text-sm text-lotto-muted">
          House edge <b className="text-lotto-green">{info.he_special_time}%</b> invece di {info.he_normale}% — e il momento migliore per giocare.
        </p>
        <p className="text-[11px] text-lotto-muted mt-2">Finestra valida fino alle 18:00</p>
      </div>
    );
  }

  const hoursLeft = Math.floor(secondsLeft / 3600);
  const urgent = hoursLeft < 2;
  return (
    <div className="glass p-6 text-center">
      <Clock className={`w-10 h-10 mx-auto mb-3 ${urgent ? "text-lotto-amber" : "text-lotto-muted"}`} />
      <p className="text-[10px] text-lotto-muted uppercase tracking-widest mb-1">Prossimo Special Time tra</p>
      <p className={`text-3xl font-black mb-2 font-mono ${urgent ? "text-lotto-amber" : "text-lotto-text"}`}>
        {formatDuration(secondsLeft)}
      </p>
      <p className="text-xs text-lotto-muted">
        Finestra 16:05 - 18:00 · HE ridotto da{" "}
        <b className="text-lotto-red">{info.he_normale}%</b> a{" "}
        <b className="text-lotto-green">{info.he_special_time}%</b>{" "}
        (+{info.vantaggio_pp.toFixed(1)} pp EV)
      </p>
    </div>
  );
}
