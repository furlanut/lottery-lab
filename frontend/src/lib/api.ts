// Server-side (SSR): use internal Docker URL to reach backend container
// Client-side (browser): use relative /api/v1 (proxied by NPM)
const isServer = typeof window === 'undefined';
const API_BASE = isServer
  ? (process.env.API_URL_INTERNAL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1')
  : (process.env.NEXT_PUBLIC_API_URL || '/api/v1');

export async function fetchAPI<T>(endpoint: string): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    cache: 'no-store',
    headers: { 'Accept': 'application/json' },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// Types — aligned with backend Pydantic models

export interface DashboardData {
  lotto: LottoStatusData;
  vincicasa: VinciCasaStatusData;
  prossime_estrazioni: CalendarioEntry[];
}

export interface LottoStatusData {
  estrazioni_totali: number;
  data_prima: string | null;
  data_ultima: string | null;
  previsioni_attive: number;
  previsioni_vinte: number;
  previsioni_perse: number;
}

export interface VinciCasaStatusData {
  estrazioni_totali: number;
  data_prima: string | null;
  data_ultima: string | null;
}

export interface Estrazione {
  id: number;
  concorso: number;
  data: string;
  ruota?: string;
  numeri: number[];
  created_at: string;
}

export interface LottoPrevisione {
  ambo_secco: {
    ambo: [number, number];
    ruota: string;
    score: number;
    metodo: string;
    tipo_giocata: string;
    frequenza: number;
    ritardo: number;
    dettagli: string;
  } | null;
  ambetti: Array<{
    ambo: [number, number];
    ruota: string;
    score: number;
    metodo: string;
    tipo_giocata: string;
    frequenza: number;
    ritardo: number;
    dettagli: string;
  }>;
  costo_estrazione: number;
  costo_ciclo: number;
  testo: string;
}

export interface VinciCasaPrevisione {
  numeri: number[];
  frequenze: Record<string, number>;
  data_generazione: string;
  finestra: number;
  dettagli: string;
  testo: string;
}

// MillionDay types (5/55 + 5 Extra, 2 estrazioni/giorno)
export interface MillionDayStatusData {
  estrazioni_totali: number;
  data_prima: string | null;
  data_ultima: string | null;
}

export interface MillionDayPrevisione {
  numeri: number[];
  frequenze: Record<string, number>;
  expected: number;
  data_generazione: string;
  finestra: number;
  dettagli: string;
  testo: string;
  score: number;
  house_edge: number;
}

export interface MillionDayEstrazione {
  id: number;
  data: string;
  ora: string;
  numeri: number[];
  extra: number[];
  created_at: string;
}

export interface CalendarioEntry {
  gioco: string;
  data: string;
  giorno: string;
  ora: string;
}

export type StatusData = LottoStatusData | VinciCasaStatusData;

// 10eLotto types
export interface DiecieLottoEstrazione {
  id: number;
  concorso: number;
  data: string;
  ora: string;
  numeri: number[];
  numero_oro: number;
  doppio_oro: number;
  numeri_extra: number[];
}

export interface DiecieLottoPrevisione {
  numeri: number[];
  metodo: string;
  score: number;
  costo: number;
  configurazione: number;
  dettagli: string;
  testo: string;
}

export interface DiecieLottoStatus {
  estrazioni_totali: number;
  data_prima: string | null;
  data_ultima: string | null;
}

// Paper Trading types
// 10eLotto storico completo
export interface DiecieLottoRecord {
  previsione: {
    numeri: number[];
    metodo: string;
    score: number;
    stato: string;
  };
  estrazione: {
    concorso?: number;
    data?: string;
    ora?: string;
    numeri?: number[];
    numero_oro?: number;
    doppio_oro?: number;
    numeri_extra?: number[];
    match_base?: number;
    match_extra?: number;
    numeri_azzeccati?: number[];
    numeri_azzeccati_extra?: number[];
    vincita_base?: number;
    vincita_extra?: number;
    vincita_totale?: number;
    pnl?: number;
  };
  costo: number;
}

export interface PaperTradingRiepilogo {
  giochi: Record<string, GamePnL>;
  totale: {
    totale_giocato: number;
    totale_vinto: number;
    pnl: number;
    roi: number;
  };
}

export interface GamePnL {
  giocate: number;
  attive: number;
  vinte: number;
  perse: number;
  totale_giocato: number;
  totale_vinto: number;
  pnl: number;
  hit_rate: number;
}

export interface DiecieLottoCompareMetodo {
  giocate: number;
  vinte: number;
  perse: number;
  big_wins: number;
  totale_giocato: number;
  totale_vinto: number;
  pnl: number;
  hit_rate: number;
  roi: number;
  avg_vincita: number;
  ratio_vs_ev: number;
  match_base_dist: Record<string, number>;
  match_extra_dist: Record<string, number>;
}

export interface DiecieLottoCompare {
  dataset_size: number;
  window: number;
  per_metodo: Record<string, DiecieLottoCompareMetodo>;
}

// Strategy Advisor types
export interface HotNumber {
  numero: number;
  frequenza: number;
  attesa: number;
  deviazione: number;
}

export interface StrategyInfo {
  id: string;
  label: string;
  obiettivo: string;
  desc: string;
  numeri: number[];
  p_win_any_osservata: number;
  p_win_10plus_osservata: number;
  p_win_100plus_osservata: number;
  ratio_backtest: number;
  note: string;
}

export interface SpecialTimeInfo {
  in_corso: boolean;
  prossima_start_iso: string;
  secondi_a_inizio: number;
  he_normale: number;
  he_special_time: number;
  vantaggio_pp: number;
}

export interface EVAnalitico {
  ev_base: number;
  ev_extra: number;
  ev_totale: number;
  house_edge: number;
  breakeven: number;
  p_base: Record<string, number>;
  p_win_qualsiasi: number;
}

export interface StrategyAdvisorStatus {
  dataset: {
    finestra_estrazioni: number;
    W: number;
    ultima_estrazione: {
      data: string;
      ora: string;
      numeri: number[];
      numero_oro: number;
      numeri_extra: number[];
    } | null;
    totale_db: number;
  };
  hot_numbers: HotNumber[];
  cold_numbers: HotNumber[];
  strategies: StrategyInfo[];
  special_time: SpecialTimeInfo;
  ev_analitico: EVAnalitico;
  invarianti: {
    p_vincita_qualsiasi_media: number;
    note_invariante: string;
    he_base: number;
    breakeven_base: number;
  };
}

// MillionDay Advisor types
export interface MDHotNumber {
  numero: number;
  frequenza: number;
  attesa: number;
  deviazione: number;
}

export interface MDStrategy {
  id: string;
  label: string;
  subtitle: string;
  window_size: number;
  obiettivo: string;
  desc: string;
  numeri: number[];
  ratio_val_robust: number;
  ratio_disc_robust: number;
  p_value: number;
  big_wins_val: number;
  regime_b_ratio_avg: number;
  regime_b_bucket_sopra_be: string;
  note: string;
  colore: "amber" | "blue" | "green" | "red" | "purple";
}

export interface MillionDayAdvisorStatus {
  dataset: {
    finestra_visualizzazione: number;
    totale_db: number;
    ultima_estrazione: {
      data: string;
      ora: string;
      numeri: number[];
      extra: number[];
    } | null;
  };
  hot_numbers: MDHotNumber[];
  cold_numbers: MDHotNumber[];
  strategies: MDStrategy[];
  prossima_estrazione: {
    iso: string;
    ora: string;
    secondi_a_estrazione: number;
    frequenza_giorno: number;
    orari: string[];
  };
  ev_analitico: {
    ev_base: number;
    ev_extra: number;
    ev_totale: number;
    house_edge: number;
    breakeven: number;
  };
  avvertimenti: {
    multiple_testing: string;
    regime_bifase: string;
    he_reale: string;
  };
}

export interface SimulateResult {
  input: {
    numeri: number[];
    costo: number;
  };
  ev_analitico: EVAnalitico;
  backtest: {
    estrazioni_testate: number;
    vincite_1plus: number;
    vincite_10plus: number;
    vincite_100plus: number;
    p_1plus_oss: number;
    p_10plus_oss: number;
    p_100plus_oss: number;
    totale_vinto: number;
    totale_giocato: number;
    pnl: number;
    roi: number;
    ratio_vs_ev: number;
    match_base_dist: Record<string, number>;
  };
}

export interface PaperTradingRecord {
  data: string;
  ora?: string;
  gioco: string;
  previsione: { numeri: number[]; metodo?: string; ruota?: string; tipo?: string };
  estrazione: {
    numeri?: number[];
    ruota?: string;
    numero_oro?: number;
    doppio_oro?: number;
    numeri_extra?: number[];
  };
  match: number;
  match_extra?: number;
  stato: string;
  costo: number;
  vincita: number;
}
