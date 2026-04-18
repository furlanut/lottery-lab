import JackpotHunter from "./JackpotHunter";
import { Gem } from "lucide-react";

export const dynamic = "force-dynamic";

export default function JackpotHunterPage() {
  return (
    <div className="space-y-8">
      <div className="fade-up">
        <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-1 flex items-center gap-4">
          <span className="gradient-amber">Jackpot</span>{" "}
          <span className="text-lotto-text">Hunter</span>
          <Gem className="w-8 h-8 text-lotto-amber opacity-60" />
        </h1>
        <p className="text-lotto-muted text-sm">
          Ottimizza P(vincere il milione) dato budget, tempo, syndicate · Confronto con investimenti
        </p>
      </div>

      <JackpotHunter />
    </div>
  );
}
