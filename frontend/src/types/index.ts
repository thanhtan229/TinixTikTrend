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
  last_observed_at?: string | null;
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
}
