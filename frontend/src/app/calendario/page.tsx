import { fetchAPI, CalendarioEntry } from "@/lib/api";
import { format, parseISO, differenceInSeconds, isToday } from "date-fns";
import { it } from "date-fns/locale";

async function getCalendario(): Promise<CalendarioEntry[] | null> {
  try {
    return await fetchAPI<CalendarioEntry[]>("/calendario");
  } catch {
    return null;
  }
}

function formatRelative(dateStr: string, now: Date): string {
  try {
    const dt = parseISO(dateStr);
    const diff = differenceInSeconds(dt, now);
    if (diff < 0) return "Passata";
    if (diff < 3600) return `tra ${Math.floor(diff / 60)}min`;
    if (diff < 86400) return `tra ${Math.floor(diff / 3600)}h`;
    return `tra ${Math.floor(diff / 86400)}g`;
  } catch {
    return "";
  }
}

export default async function CalendarioPage() {
  const entries = await getCalendario();
  const now = new Date();

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="fade-up">
        <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-1 text-lotto-text">
          Calendario
        </h1>
        <p className="text-lotto-muted text-sm">Prossime estrazioni programmate</p>
      </div>

      {entries === null ? (
        <OfflineState />
      ) : entries.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="fade-up-1 relative">
          {/* Vertical timeline line */}
          <div className="absolute left-[19px] top-4 bottom-4 w-px bg-gradient-to-b from-lotto-blue/40 via-[rgba(255,255,255,0.08)] to-transparent md:left-[23px]" />

          <div className="space-y-3">
            {entries.map((entry, i) => {
              let entryDate: Date | null = null;
              try {
                entryDate = parseISO(entry.data);
              } catch {
                entryDate = null;
              }

              const entryIsToday = entryDate ? isToday(entryDate) : false;
              const isLotto = entry.gioco === "Lotto";
              const relative = formatRelative(entry.data, now);

              return (
                <div key={i} className="flex items-start gap-4 md:gap-5">
                  {/* Timeline dot */}
                  <div className="relative flex-shrink-0 mt-4">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center z-10 relative ${
                        entryIsToday
                          ? isLotto
                            ? "bg-gradient-to-br from-lotto-blue to-lotto-purple shadow-lg shadow-lotto-blue/30"
                            : "bg-gradient-to-br from-lotto-green to-lotto-teal shadow-lg shadow-lotto-green/30"
                          : "bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.08)]"
                      }`}
                    >
                      {isLotto ? (
                        <svg
                          className={`w-4 h-4 ${entryIsToday ? "text-white" : "text-lotto-muted"}`}
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth={2}
                        >
                          <rect x="3" y="3" width="18" height="18" rx="2" />
                          <circle cx="8.5" cy="8.5" r="1.5" fill="currentColor" stroke="none" />
                          <circle cx="15.5" cy="8.5" r="1.5" fill="currentColor" stroke="none" />
                          <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" />
                          <circle cx="8.5" cy="15.5" r="1.5" fill="currentColor" stroke="none" />
                          <circle cx="15.5" cy="15.5" r="1.5" fill="currentColor" stroke="none" />
                        </svg>
                      ) : (
                        <svg
                          className={`w-4 h-4 ${entryIsToday ? "text-white" : "text-lotto-muted"}`}
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth={2}
                        >
                          <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                          <polyline points="9 22 9 12 15 12 15 22" />
                        </svg>
                      )}
                    </div>
                  </div>

                  {/* Content */}
                  <div
                    className={`flex-1 glass p-4 md:p-5 relative overflow-hidden ${
                      entryIsToday
                        ? isLotto
                          ? "glow-blue border-lotto-blue/30"
                          : "glow-green border-lotto-green/30"
                        : ""
                    }`}
                  >
                    {entryIsToday && (
                      <div
                        className={`absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r ${
                          isLotto
                            ? "from-lotto-blue to-lotto-purple"
                            : "from-lotto-green to-lotto-teal"
                        }`}
                      />
                    )}

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5 flex-wrap">
                        <span
                          className={`text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded border ${
                            isLotto
                              ? "bg-lotto-blue/10 text-lotto-blue border-lotto-blue/20"
                              : "bg-lotto-green/10 text-lotto-green border-lotto-green/20"
                          }`}
                        >
                          {entry.gioco}
                        </span>

                        {entryIsToday && (
                          <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-white/5 border border-white/10 text-[10px] font-bold uppercase tracking-wide text-lotto-text">
                            <span
                              className={`w-1.5 h-1.5 rounded-full dot-pulse ${
                                isLotto ? "bg-lotto-blue" : "bg-lotto-green"
                              }`}
                            />
                            OGGI
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-3">
                        <span className="text-xs font-mono text-lotto-muted">
                          {entry.ora}
                        </span>
                        {relative && (
                          <span
                            className={`text-xs font-semibold ${
                              entryIsToday
                                ? isLotto
                                  ? "text-lotto-blue"
                                  : "text-lotto-green"
                                : "text-lotto-muted"
                            }`}
                          >
                            {relative}
                          </span>
                        )}
                      </div>
                    </div>

                    <p className="text-sm text-lotto-text mt-2 capitalize font-medium">
                      {entry.giorno} &mdash;{" "}
                      {entryDate
                        ? format(entryDate, "dd MMMM yyyy", { locale: it })
                        : entry.data}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
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

function EmptyState() {
  return (
    <div className="glass p-10 text-center fade-up-1">
      <div className="w-12 h-12 rounded-full bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.08)] flex items-center justify-center mx-auto mb-4">
        <svg className="w-6 h-6 text-lotto-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
          <line x1="16" y1="2" x2="16" y2="6" />
          <line x1="8" y1="2" x2="8" y2="6" />
          <line x1="3" y1="10" x2="21" y2="10" />
        </svg>
      </div>
      <p className="text-lotto-text font-semibold mb-1">Nessuna estrazione programmata</p>
      <p className="text-lotto-muted text-sm">Il calendario è vuoto al momento.</p>
    </div>
  );
}
