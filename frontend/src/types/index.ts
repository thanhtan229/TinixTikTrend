export interface HealthStatus {
  status: string;
  app_name: string;
  environment: string;
  region: string;
  database: string;
  timestamp: string;
}

export interface Product {
  id: number;
  platform: string;
  external_product_id: string;
  title: string;
  url?: string | null;
  image_url?: string | null;
  shop_id?: string | null;
  shop_name?: string | null;
  category?: string | null;
  first_seen_at: string;
  last_seen_at: string;
  created_at: string;
  updated_at: string;
}

export interface ProductSnapshot {
  id: number;
  product_id: number;
  captured_at: string;
  price?: number | null;
  original_price?: number | null;
  sold_count?: number | null;
  review_count?: number | null;
  rating?: number | null;
  stock_count?: number | null;
  rank_position?: number | null;
  creator_count?: number | null;
  video_count?: number | null;
  commission_rate?: number | null;
  is_partial?: boolean;
}

export interface DeltaMetrics {
  latest_sold_count?: number | null;
  latest_review_count?: number | null;
  latest_rating?: number | null;
  latest_price?: number | null;
  latest_commission_rate?: number | null;
  
  sold_delta_6h?: number | null;
  sold_delta_12h?: number | null;
  sold_delta_24h?: number | null;
  sold_delta_7d?: number | null;
  
  review_delta_24h?: number | null;
  review_delta_7d?: number | null;
  
  sales_velocity_24h?: number | null;
  sales_acceleration?: number | null;
  is_anomaly?: boolean;
  is_stale?: boolean;
  velocity_is_estimated?: boolean;
  has_24h_window?: boolean;
  has_7d_window?: boolean;
  primary_elapsed_hours?: number | null;
  last_observed_at?: string | null;
}

export interface PrimarySignalInterval {
  elapsed_hours?: number | null;
  is_estimated: boolean;
}

export interface TrendEvidence {
  observation_count: number;
  observation_span_hours: number;
  latest_observation_age_hours: number;
  ranking_state: "eligible" | "stale" | "insufficient_measured_signal";
  confidence: "low" | "medium" | "high";
  primary_signal_interval?: PrimarySignalInterval | null;
  signals: Record<string, "measured" | "estimated" | "missing">;
  has_24h_window: boolean;
  has_7d_window: boolean;
  missing_metrics: string[];
}

export interface TrendReason {
  reason_code: "sales_velocity_up" | "sales_acceleration_up" | "review_velocity_up" | string;
  contribution: number;
  value: number;
  formatted_text: string;
}

export interface TrendMetrics {
  product_id: number;
  external_product_id: string;
  title: string;
  url?: string | null;
  image_url?: string | null;
  shop_id?: string | null;
  shop_name?: string | null;
  category?: string | null;
  first_seen_at: string;
  last_seen_at: string;
  
  deltas: DeltaMetrics;
  trend_score: number;
  evidence?: TrendEvidence | null;
  reasons?: TrendReason[];
}

export interface WatchlistItem {
  product_id: number;
  notes?: string | null;
  created_at: string;
  product?: Product | null;
  analysis?: TrendMetrics | null;
}

export interface WatchlistResponse {
  items: WatchlistItem[];
  total: number;
}

export interface WatchStatus {
  product_id: number;
  is_watched: boolean;
  notes?: string | null;
  created_at?: string | null;
}

export interface AlertRule {
  id: number;
  product_id: number;
  rule_type: "sales_velocity_above" | "trend_score_above" | "price_change_pct";
  threshold: number;
  direction?: "up" | "down" | "either" | null;
  cooldown_minutes: number;
  is_active: boolean;
  last_condition_met: boolean;
  last_triggered_at?: string | null;
  last_evaluated_snapshot_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface AlertRuleCreate {
  product_id: number;
  rule_type: "sales_velocity_above" | "trend_score_above" | "price_change_pct";
  threshold: number;
  direction?: "up" | "down" | "either" | null;
  cooldown_minutes?: number;
  is_active?: boolean;
}

export interface AlertRuleUpdate {
  threshold?: number;
  direction?: "up" | "down" | "either" | null;
  cooldown_minutes?: number;
  is_active?: boolean;
}

export interface AlertEvent {
  id: number;
  rule_id: number;
  product_id: number;
  triggering_snapshot_id: number;
  event_type: string;
  threshold: number;
  trigger_value: number;
  direction?: "up" | "down" | "either" | null;
  actual_direction?: "up" | "down" | null;
  message: string;
  is_read: boolean;
  triggered_at: string;
  product_title?: string | null;
}

export interface SystemDiagnosticsData {
  system: {
    environment: string;
    region: string;
    version: string;
    server_time_utc: string;
  };
  database: {
    relative_path: string;
    size_bytes: number;
    table_counts: Record<string, number>;
  };
  crawler: {
    is_running: boolean;
    last_run_id?: number | null;
    last_run_status?: string | null;
    last_run_finished_at?: string | null;
    quarantined_count: number;
  };
  scheduler: {
    is_running: boolean;
    jobs: Array<{ id: string; name: string; next_run_time?: string | null }>;
  };
  tiktok_session: {
    status: "available" | "missing" | "invalid";
    redacted: boolean;
    notes: string;
  };
}

export interface DeepDiagnosticsResult {
  status: "ok" | "issues_found" | "error";
  integrity_check: string;
  foreign_key_check: string | string[];
  checked_at?: string;
  message?: string;
}

