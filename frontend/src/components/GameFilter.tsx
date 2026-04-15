"use client";
import { useState } from "react";

interface GameFilterProps {
  children: (selectedGame: string) => React.ReactNode;
}

const games = [
  { key: "all", label: "Tutti", color: "text-lotto-text" },
  { key: "lotto", label: "Lotto", color: "text-lotto-blue" },
  { key: "vincicasa", label: "VinciCasa", color: "text-lotto-green" },
  { key: "diecielotto", label: "10eLotto", color: "text-lotto-amber" },
];

export default function GameFilter({ children }: GameFilterProps) {
  const [selected, setSelected] = useState("all");

  return (
    <div>
      <div className="flex gap-2 mb-4 flex-wrap">
        {games.map((g) => (
          <button
            key={g.key}
            onClick={() => setSelected(g.key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wide transition-all ${
              selected === g.key
                ? `${g.color} bg-white/10 border border-white/20`
                : "text-lotto-muted hover:text-lotto-text bg-white/[0.03] border border-transparent"
            }`}
          >
            {g.label}
          </button>
        ))}
      </div>
      {children(selected)}
    </div>
  );
}
