export type WallSummary = {
  side: string;
  wall_price: number;
  wall_qty: number;
  wall_notional: number;
  wall_share: number;
  best_bid: number;
  best_ask: number;
};

export type SymbolState = {
  symbol: string;
  spot_mid: number;
  perp_mark: number;
  perp_mid: number;
  basis_mark: number;
  basis_mid: number;
  zscore: number;
  duration_s: number;
  last_update_ts: number;
  wall?: WallSummary | null;
  last_wall_event?: string | null;
  last_wall_event_ts?: number | null;
  last_basis_event?: string | null;
  last_basis_event_ts?: number | null;
};

export type EventPayload = {
  event_type: string;
  event_reason?: string;
  symbol: string;
  ts: number;
  basis_mark?: number;
  zscore?: number;
  duration_s?: number;
  wall?: WallSummary;
};

export type TimeseriesPoint = {
  ts: number;
  spot_mid: number;
  perp_mark: number;
  basis_mark: number;
  zscore: number;
  duration_s: number;
  wall_notional: number;
  wall_price: number;
};
