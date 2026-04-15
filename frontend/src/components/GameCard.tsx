import Link from "next/link";
import { ArrowRight } from "lucide-react";

interface GameCardProps {
  title: string;
  href: string;
  icon: React.ReactNode;
  estrazioniTotali: number;
  ultimaEstrazione: string | null;
  previsioniAttive?: number;
  hitRate?: number;
  accentColor: string;
}

export default function GameCard({
  title,
  href,
  icon,
  estrazioniTotali,
  ultimaEstrazione,
  previsioniAttive,
  hitRate,
  accentColor,
}: GameCardProps) {
  return (
    <Link href={href} className="block group">
      <div className="bg-lottery-card rounded-xl p-6 border border-gray-800 hover:border-gray-600 hover:bg-lottery-card-hover">
        <div className="flex items-center gap-3 mb-4">
          <div className={`p-2 rounded-lg ${accentColor}`}>{icon}</div>
          <h3 className="text-xl font-bold text-white">{title}</h3>
          <ArrowRight className="ml-auto w-5 h-5 text-gray-500 group-hover:text-white group-hover:translate-x-1 transition-transform" />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">
              Estrazioni
            </p>
            <p className="text-2xl font-bold text-white">
              {estrazioniTotali.toLocaleString("it-IT")}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">
              Ultima estrazione
            </p>
            <p className="text-sm font-medium text-gray-200">
              {ultimaEstrazione ?? "N/D"}
            </p>
          </div>
          {previsioniAttive !== undefined && (
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wide">
                Previsioni attive
              </p>
              <p className="text-2xl font-bold text-lottery-blue">
                {previsioniAttive}
              </p>
            </div>
          )}
          {hitRate !== undefined && (
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wide">
                Hit Rate
              </p>
              <p className="text-2xl font-bold text-lottery-green">
                {(hitRate * 100).toFixed(1)}%
              </p>
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
