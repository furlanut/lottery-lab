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
