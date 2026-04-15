"use client";

import { useEffect, useState, useCallback } from "react";

interface CountdownTimerProps {
  nextDrawDate: string; // ISO string — the next extraction datetime at 20:00 Rome time
  game?: "Lotto" | "VinciCasa";
  onDrawPassed?: () => void;
}

function getTimeLeft(targetISO: string): {
  total: number;
  hours: number;
  minutes: number;
  seconds: number;
  days: number;
} {
  const now = Date.now();
  const target = new Date(targetISO).getTime();
  const total = Math.max(0, target - now);

  const seconds = Math.floor((total / 1000) % 60);
  const minutes = Math.floor((total / (1000 * 60)) % 60);
  const hours = Math.floor((total / (1000 * 60 * 60)) % 24);
  const days = Math.floor(total / (1000 * 60 * 60 * 24));

  return { total, hours, minutes, seconds, days };
}

export default function CountdownTimer({
  nextDrawDate,
  onDrawPassed,
}: CountdownTimerProps) {
  const [timeLeft, setTimeLeft] = useState(() => getTimeLeft(nextDrawDate));
  const [hasPassed, setHasPassed] = useState(false);
  const [passedCalled, setPassedCalled] = useState(false);

  const tick = useCallback(() => {
    const t = getTimeLeft(nextDrawDate);
    setTimeLeft(t);
    if (t.total === 0 && !passedCalled) {
      setHasPassed(true);
      setPassedCalled(true);
      onDrawPassed?.();
    }
  }, [nextDrawDate, onDrawPassed, passedCalled]);

  useEffect(() => {
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [tick]);

  if (hasPassed) {
    return (
      <div className="flex items-center gap-2 text-amber-400">
        <svg
          className="w-4 h-4 spin"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
        </svg>
        <span className="text-sm font-medium">Verifica in corso...</span>
      </div>
    );
  }

  const { total, days, hours, minutes, seconds } = timeLeft;
  const isWarning = total > 0 && total < 5 * 60 * 1000; // < 5 min
  const isLive = total > 0 && total < 30 * 60 * 1000; // < 30 min → show LIVE badge

  const pad = (n: number) => String(n).padStart(2, "0");

  let display: string;
  if (days > 0) {
    display = `${days}g ${pad(hours)}:${pad(minutes)}`;
  } else {
    display = `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
  }

  return (
    <div className="flex items-center gap-2">
      {isLive && (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-lotto-red/20 border border-lotto-red/30">
          <span className="w-1.5 h-1.5 rounded-full bg-lotto-red dot-pulse" />
          <span className="text-[10px] font-bold text-lotto-red uppercase tracking-wide">
            LIVE
          </span>
        </span>
      )}
      <span
        className={`text-sm font-mono font-semibold ${
          isWarning
            ? "countdown-warning"
            : isLive
              ? "text-amber-400"
              : "text-lotto-muted"
        }`}
      >
        {display}
      </span>
    </div>
  );
}
