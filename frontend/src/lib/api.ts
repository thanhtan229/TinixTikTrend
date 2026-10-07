import {
  HealthStatus,
  Product,
  ProductSnapshot,
  TrendMetrics,
  WatchlistItem,
  WatchlistResponse,
  WatchStatus,
  AlertRule,
  AlertRuleCreate,
  AlertRuleUpdate,
  AlertEvent,
  SystemDiagnosticsData,
  DeepDiagnosticsResult,
  Collection,
  CollectionItem,
  SavedView,
  TrendsSavedViewPayload,
  WatchlistSavedViewPayload,
  CompareResponse,
  ComparedProduct,
  ReviewStatus,
  EconomicsScenario,
  EconomicsScenarioCreate,
  EconomicsScenarioUpdate,
  EconomicsScenarioDuplicate,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface DashboardData {
  stats: {
    total_products: number;
    high_trend_count: number;
  };
  trending: TrendMetrics[];
  rising: TrendMetrics[];
  new_products: TrendMetrics[];
  best_sellers: TrendMetrics[];
}

export interface ProductDetailData {
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
  analysis: TrendMetrics;
  snapshots: ProductSnapshot[];
}

export interface ProductVideo {
  video_id: string;
  url: string;
  creator_handle: string | null;
  creator_name: string | null;
  description: string | null;
  thumbnail_url: string | null;
  refresh_status: string;
  refresh_message: string | null;
  last_attempt_at: string | null;
  associated_at: string;
  snapshots: Array<{
    captured_at: string;
    source: string;
    view_count: number | null;
    like_count: number | null;
    comment_count: number | null;
    share_count: number | null;
    collect_count: number | null;
  }>;
  content_metrics: {
    velocities: Record<string, number | null>;
    anomalies: Record<string, boolean>;
    engagement_rate: number | null;
  };
}

async function videoRequest(url: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(url, init);
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const detail = data?.detail;
    throw new Error(typeof detail === "string" ? detail : detail?.message || `Yêu cầu thất bại (${response.status})`);
  }
  return response;
}

export async function fetchProductVideos(productId: number): Promise<ProductVideo[]> {
  const response = await videoRequest(`${API_BASE_URL}/products/${productId}/videos`, { cache: "no-store" });
  return (await response.json()).items;
}

export async function addProductVideo(productId: number, url: string): Promise<void> {
  await videoRequest(`${API_BASE_URL}/products/${productId}/videos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
}

export async function refreshProductVideo(productId: number, videoId: string): Promise<void> {
  await videoRequest(`${API_BASE_URL}/products/${productId}/videos/${videoId}/refresh`, { method: "POST" });
}

export async function detachProductVideo(productId: number, videoId: string): Promise<void> {
  await videoRequest(`${API_BASE_URL}/products/${productId}/videos/${videoId}`, { method: "DELETE" });
}

export interface CrawlerStatus {
  local_session_status?: "missing" | "available" | "invalid";
  quarantined_products?: number;
  is_running: boolean;
  region: string;
  schedule: string;
  latest_run?: {
    id: number;
    started_at: string;
    finished_at?: string | null;
    status: string;
    source: string;
    products_found: number;
    products_created: number;
    products_updated: number;
    snapshots_created: number;
    error_message?: string | null;
  } | null;
}

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchDashboardSummary(): Promise<DashboardData> {
  const res = await fetch(`${API_BASE_URL}/dashboard`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch dashboard: ${res.statusText}`);
  return res.json();
}

export interface FetchTrendsParams {
  category?: string;
  rank_by?: string;
  hours?: number;
  trend_state?: "eligible" | "all" | "stale" | "insufficient_signal" | string;
  confidence?: "low" | "medium" | "high" | "medium_or_high" | string;
  evidence?: "measured_only" | string;
  sort_by?: "trend_score" | "sales_velocity" | "sales_delta" | "review_delta" | "freshness" | string;
  order?: "desc" | "asc" | string;
}

export async function fetchTrends(
  type: "trending" | "rising" | "new" | "best-sellers",
  params: FetchTrendsParams = {}
): Promise<TrendMetrics[]> {
  const searchParams = new URLSearchParams();
  if (params.category) searchParams.append("category", params.category);
  if (params.rank_by) searchParams.append("rank_by", params.rank_by);
  if (params.hours) searchParams.append("hours", params.hours.toString());
  if (params.trend_state) searchParams.append("trend_state", params.trend_state);
  if (params.confidence) searchParams.append("confidence", params.confidence);
  if (params.evidence) searchParams.append("evidence", params.evidence);
  if (params.sort_by) searchParams.append("sort_by", params.sort_by);
  if (params.order) searchParams.append("order", params.order);

  const endpoint = type === "trending" ? "/trends" : `/trends/${type}`;
  const queryStr = searchParams.toString() ? `?${searchParams.toString()}` : "";

  const res = await fetch(`${API_BASE_URL}${endpoint}${queryStr}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch trends: ${res.statusText}`);
  return res.json();
}

export async function fetchProductDetail(id: number | string): Promise<ProductDetailData> {
  const res = await fetch(`${API_BASE_URL}/products/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch product ${id}: ${res.statusText}`);
  return res.json();
}

export async function fetchCrawlerStatus(): Promise<CrawlerStatus> {
  const res = await fetch(`${API_BASE_URL}/crawler/status`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch crawler status: ${res.statusText}`);
  return res.json();
}

export async function triggerCrawlerRun(payload?: { category_slugs?: string[]; product_urls?: string[]; keywords?: string[] }): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/crawler/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const detail = errorData.detail;
    throw new Error(typeof detail === "string" ? detail : Array.isArray(detail)
      ? detail.map((e: { msg: string }) => e.msg).join("; ") : `Failed to trigger crawler: ${res.statusText}`);
  }
  return res.json();
}

// ==========================================
// Phase 3: Watchlist API
// ==========================================

export interface FetchWatchlistParams {
  category?: string;
  trend_state?: string;
  confidence?: string;
  evidence?: string;
  sort_by?: string;
  order?: string;
  limit?: number;
  offset?: number;
}

export async function fetchWatchlist(params: FetchWatchlistParams = {}): Promise<WatchlistResponse> {
  const searchParams = new URLSearchParams();
  if (params.category) searchParams.append("category", params.category);
  if (params.trend_state) searchParams.append("trend_state", params.trend_state);
  if (params.confidence) searchParams.append("confidence", params.confidence);
  if (params.evidence) searchParams.append("evidence", params.evidence);
  if (params.sort_by) searchParams.append("sort_by", params.sort_by);
  if (params.order) searchParams.append("order", params.order);
  if (params.limit !== undefined) searchParams.append("limit", params.limit.toString());
  if (params.offset !== undefined) searchParams.append("offset", params.offset.toString());

  const queryStr = searchParams.toString() ? `?${searchParams.toString()}` : "";
  const res = await fetch(`${API_BASE_URL}/watchlist${queryStr}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch watchlist: ${res.statusText}`);
  return res.json();
}

export async function addToWatchlist(productId: number, notes?: string): Promise<{ status: string; product_id: number }> {
  const res = await fetch(`${API_BASE_URL}/watchlist/${productId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(notes ? { notes } : {}),
  });
  if (!res.ok) throw new Error(`Failed to add product ${productId} to watchlist: ${res.statusText}`);
  return res.json();
}

export async function removeFromWatchlist(productId: number): Promise<{ status: string; product_id: number }> {
  const res = await fetch(`${API_BASE_URL}/watchlist/${productId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to remove product ${productId} from watchlist: ${res.statusText}`);
  return res.json();
}

export async function fetchWatchStatus(productId: number): Promise<WatchStatus> {
  const res = await fetch(`${API_BASE_URL}/watchlist/status/${productId}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch watch status: ${res.statusText}`);
  return res.json();
}

export async function fetchWatchedProductIds(): Promise<number[]> {
  const res = await fetch(`${API_BASE_URL}/watchlist/ids`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch watched product IDs: ${res.statusText}`);
  const data = await res.json();
  return data.watched_product_ids || [];
}

// ==========================================
// Phase 3: Alerts API
// ==========================================

export async function fetchAlertRules(productId?: number): Promise<AlertRule[]> {
  const queryStr = productId ? `?product_id=${productId}` : "";
  const res = await fetch(`${API_BASE_URL}/alerts/rules${queryStr}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch alert rules: ${res.statusText}`);
  return res.json();
}

export async function createAlertRule(rule: AlertRuleCreate): Promise<AlertRule> {
  const res = await fetch(`${API_BASE_URL}/alerts/rules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rule),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const detail = errorData.detail;
    throw new Error(typeof detail === "string" ? detail : Array.isArray(detail)
      ? detail.map((e: { msg: string }) => e.msg).join("; ") : `Failed to create alert rule: ${res.statusText}`);
  }
  return res.json();
}

export async function updateAlertRule(ruleId: number, rule: AlertRuleUpdate): Promise<AlertRule> {
  const res = await fetch(`${API_BASE_URL}/alerts/rules/${ruleId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rule),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const detail = errorData.detail;
    throw new Error(typeof detail === "string" ? detail : Array.isArray(detail)
      ? detail.map((e: { msg: string }) => e.msg).join("; ") : `Failed to update alert rule: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteAlertRule(ruleId: number): Promise<{ status: string; rule_id: number }> {
  const res = await fetch(`${API_BASE_URL}/alerts/rules/${ruleId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to delete alert rule: ${res.statusText}`);
  return res.json();
}

export interface FetchAlertEventsParams {
  product_id?: number;
  unread_only?: boolean;
  limit?: number;
  offset?: number;
}

export async function fetchAlertEvents(params: FetchAlertEventsParams = {}): Promise<AlertEvent[]> {
  const searchParams = new URLSearchParams();
  if (params.product_id !== undefined) searchParams.append("product_id", params.product_id.toString());
  if (params.unread_only !== undefined) searchParams.append("unread_only", params.unread_only.toString());
  if (params.limit !== undefined) searchParams.append("limit", params.limit.toString());
  if (params.offset !== undefined) searchParams.append("offset", params.offset.toString());

  const queryStr = searchParams.toString() ? `?${searchParams.toString()}` : "";
  const res = await fetch(`${API_BASE_URL}/alerts/events${queryStr}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch alert events: ${res.statusText}`);
  return res.json();
}

export async function markAlertRead(eventId: number): Promise<{ status: string; event_id: number; is_read: boolean }> {
  const res = await fetch(`${API_BASE_URL}/alerts/events/${eventId}/read`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Failed to mark alert as read: ${res.statusText}`);
  return res.json();
}

export async function markAllAlertsRead(): Promise<{ status: string; marked_read_count: number }> {
  const res = await fetch(`${API_BASE_URL}/alerts/events/read-all`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Failed to mark all alerts as read: ${res.statusText}`);
  return res.json();
}

export async function fetchUnreadAlertCount(): Promise<number> {
  const res = await fetch(`${API_BASE_URL}/alerts/unread-count`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch unread count: ${res.statusText}`);
  const data = await res.json();
  return data.unread_count ?? 0;
}

// ================= Phase 4: Exports, Backups & Diagnostics =================

export function getExportTrendsUrl(params: {
  category?: string;
  trend_state?: string;
  confidence?: string;
  evidence?: string;
  sort_by?: string;
  order?: string;
  limit?: number;
  offset?: number;
} = {}): string {
  const sp = new URLSearchParams();
  if (params.category) sp.append("category", params.category);
  if (params.trend_state) sp.append("trend_state", params.trend_state);
  if (params.confidence) sp.append("confidence", params.confidence);
  if (params.evidence) sp.append("evidence", params.evidence);
  if (params.sort_by) sp.append("sort_by", params.sort_by);
  if (params.order) sp.append("order", params.order);
  if (params.limit !== undefined) sp.append("limit", params.limit.toString());
  if (params.offset !== undefined) sp.append("offset", params.offset.toString());
  return `${API_BASE_URL}/trends/export${sp.toString() ? `?${sp.toString()}` : ""}`;
}

export function getExportWatchlistUrl(params: {
  category?: string;
  trend_state?: string;
  confidence?: string;
  evidence?: string;
  sort_by?: string;
  order?: string;
  limit?: number;
  skip?: number;
} = {}): string {
  const sp = new URLSearchParams();
  if (params.category) sp.append("category", params.category);
  if (params.trend_state) sp.append("trend_state", params.trend_state);
  if (params.confidence) sp.append("confidence", params.confidence);
  if (params.evidence) sp.append("evidence", params.evidence);
  if (params.sort_by) sp.append("sort_by", params.sort_by);
  if (params.order) sp.append("order", params.order);
  if (params.limit !== undefined) sp.append("limit", params.limit.toString());
  if (params.skip !== undefined) sp.append("skip", params.skip.toString());
  return `${API_BASE_URL}/watchlist/export${sp.toString() ? `?${sp.toString()}` : ""}`;
}

export function getExportProductHistoryUrl(productId: number, range: string): string {
  return `${API_BASE_URL}/products/${productId}/export-history?range=${encodeURIComponent(range)}`;
}

export function getExportAlertsUrl(params: {
  product_id?: number;
  is_read?: boolean;
} = {}): string {
  const sp = new URLSearchParams();
  if (params.product_id !== undefined) sp.append("product_id", params.product_id.toString());
  if (params.is_read !== undefined) sp.append("is_read", params.is_read.toString());
  return `${API_BASE_URL}/alerts/events/export${sp.toString() ? `?${sp.toString()}` : ""}`;
}

export async function fetchDiagnostics(): Promise<SystemDiagnosticsData> {
  const res = await fetch(`${API_BASE_URL}/diagnostics`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Lỗi khi lấy thông tin chẩn đoán: ${res.statusText}`);
  return res.json();
}

export async function fetchDeepDiagnostics(): Promise<DeepDiagnosticsResult> {
  const res = await fetch(`${API_BASE_URL}/diagnostics/deep`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Lỗi khi kiểm tra toàn vẹn chuyên sâu: ${res.statusText}`);
  return res.json();
}

// ==========================================
// Phase 5: Collections API
// ==========================================

export async function fetchCollections(): Promise<Collection[]> {
  const res = await fetch(`${API_BASE_URL}/collections`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Lỗi khi tải danh sách bộ sưu tập: ${res.statusText}`);
  return res.json();
}

export async function fetchCollection(collectionId: number): Promise<Collection> {
  const res = await fetch(`${API_BASE_URL}/collections/${collectionId}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Lỗi khi tải bộ sưu tập: ${res.statusText}`);
  return res.json();
}

export async function createCollection(name: string, description?: string): Promise<Collection> {
  const res = await fetch(`${API_BASE_URL}/collections`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Lỗi khi tạo bộ sưu tập: ${res.statusText}`);
  }
  return res.json();
}

export async function updateCollection(
  collectionId: number,
  data: { name?: string; description?: string }
): Promise<Collection> {
  const res = await fetch(`${API_BASE_URL}/collections/${collectionId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Lỗi khi cập nhật bộ sưu tập: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteCollection(collectionId: number): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE_URL}/collections/${collectionId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Lỗi khi xóa bộ sưu tập: ${res.statusText}`);
  return res.json();
}

export async function fetchCollectionMembers(
  collectionId: number,
  reviewStatus?: string
): Promise<CollectionItem[]> {
  const sp = new URLSearchParams();
  if (reviewStatus) sp.append("review_status", reviewStatus);
  const res = await fetch(
    `${API_BASE_URL}/collections/${collectionId}/items${sp.toString() ? `?${sp.toString()}` : ""}`,
    { cache: "no-store" }
  );
  if (!res.ok) throw new Error(`Lỗi khi tải thành viên bộ sưu tập: ${res.statusText}`);
  return res.json();
}

export async function addProductToCollection(
  collectionId: number,
  productId: number,
  reviewStatus: ReviewStatus = "new",
  notes?: string
): Promise<CollectionItem> {
  const res = await fetch(`${API_BASE_URL}/collections/${collectionId}/items`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_id: productId, review_status: reviewStatus, notes }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Lỗi khi thêm sản phẩm vào bộ sưu tập: ${res.statusText}`);
  }
  return res.json();
}

export async function removeProductFromCollection(
  collectionId: number,
  productId: number
): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE_URL}/collections/${collectionId}/items/${productId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Lỗi khi xóa sản phẩm khỏi bộ sưu tập: ${res.statusText}`);
  return res.json();
}

export async function updateCollectionItem(
  collectionId: number,
  productId: number,
  data: { review_status?: ReviewStatus; notes?: string }
): Promise<CollectionItem> {
  const res = await fetch(`${API_BASE_URL}/collections/${collectionId}/items/${productId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Lỗi khi cập nhật sản phẩm trong bộ sưu tập: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchProductCollections(productId: number): Promise<Collection[]> {
  const res = await fetch(`${API_BASE_URL}/collections/product/${productId}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Lỗi khi kiểm tra bộ sưu tập của sản phẩm: ${res.statusText}`);
  return res.json();
}

// ==========================================
// Phase 5: Saved Views API
// ==========================================

export async function fetchSavedViews(scope?: "trends" | "watchlist"): Promise<SavedView[]> {
  const sp = new URLSearchParams();
  if (scope) sp.append("scope", scope);
  const res = await fetch(`${API_BASE_URL}/saved-views${sp.toString() ? `?${sp.toString()}` : ""}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Lỗi khi tải danh sách chế độ xem đã lưu: ${res.statusText}`);
  return res.json();
}

export async function createSavedView<T = any>(data: {
  name: string;
  scope: "trends" | "watchlist";
  payload_version?: number;
  payload: T;
}): Promise<SavedView<T>> {
  const res = await fetch(`${API_BASE_URL}/saved-views`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: data.name,
      scope: data.scope,
      payload_version: data.payload_version ?? 1,
      payload: data.payload,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Lỗi khi lưu chế độ xem: ${res.statusText}`);
  }
  return res.json();
}

export async function updateSavedView<T = any>(
  viewId: number,
  data: { name?: string; payload?: T }
): Promise<SavedView<T>> {
  const res = await fetch(`${API_BASE_URL}/saved-views/${viewId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Lỗi khi cập nhật chế độ xem: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteSavedView(viewId: number): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE_URL}/saved-views/${viewId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Lỗi khi xóa chế độ xem: ${res.statusText}`);
  return res.json();
}

// ==========================================
// Phase 5: Product Compare API
// ==========================================

export async function compareProducts(
  productIds: number[],
  collectionId?: number
): Promise<CompareResponse> {
  const res = await fetch(`${API_BASE_URL}/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      product_ids: productIds,
      collection_id: collectionId,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Lỗi khi so sánh sản phẩm: ${res.statusText}`);
  }
  return res.json();
}

// ==========================================
// Phase 6: Product Economics API
// ==========================================

export async function fetchProductEconomicsScenarios(productId: number): Promise<EconomicsScenario[]> {
  const res = await fetch(`${API_BASE_URL}/products/${productId}/economics`, { cache: "no-store" });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Lỗi khi tải kịch bản kinh tế: ${res.statusText}`);
  }
  return res.json();
}

export async function createEconomicsScenario(
  productId: number,
  data: EconomicsScenarioCreate
): Promise<EconomicsScenario> {
  const res = await fetch(`${API_BASE_URL}/products/${productId}/economics`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const detail = errorData.detail;
    throw new Error(typeof detail === "string" ? detail : Array.isArray(detail)
      ? detail.map((e: { msg: string }) => e.msg).join("; ") : `Lỗi khi tạo kịch bản kinh tế: ${res.statusText}`);
  }
  return res.json();
}

export async function updateEconomicsScenario(
  productId: number,
  scenarioId: number,
  data: EconomicsScenarioUpdate
): Promise<EconomicsScenario> {
  const res = await fetch(`${API_BASE_URL}/products/${productId}/economics/${scenarioId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const detail = errorData.detail;
    throw new Error(typeof detail === "string" ? detail : Array.isArray(detail)
      ? detail.map((e: { msg: string }) => e.msg).join("; ") : `Lỗi khi cập nhật kịch bản kinh tế: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteEconomicsScenario(
  productId: number,
  scenarioId: number
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/products/${productId}/economics/${scenarioId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Lỗi khi xóa kịch bản kinh tế: ${res.statusText}`);
  }
}

export async function setDefaultEconomicsScenario(
  productId: number,
  scenarioId: number
): Promise<EconomicsScenario> {
  const res = await fetch(`${API_BASE_URL}/products/${productId}/economics/${scenarioId}/set-default`, {
    method: "POST",
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Lỗi khi đặt kịch bản mặc định: ${res.statusText}`);
  }
  return res.json();
}

export async function duplicateEconomicsScenario(
  productId: number,
  scenarioId: number,
  name: string
): Promise<EconomicsScenario> {
  const res = await fetch(`${API_BASE_URL}/products/${productId}/economics/${scenarioId}/duplicate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const detail = errorData.detail;
    throw new Error(typeof detail === "string" ? detail : `Lỗi khi nhân bản kịch bản kinh tế: ${res.statusText}`);
  }
  return res.json();
}

export async function rebasePriceEconomicsScenario(
  productId: number,
  scenarioId: number
): Promise<EconomicsScenario> {
  const res = await fetch(`${API_BASE_URL}/products/${productId}/economics/${scenarioId}/rebase-price`, {
    method: "POST",
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const detail = errorData.detail;
    throw new Error(typeof detail === "string" ? detail : `Lỗi khi cập nhật lại giá quan sát: ${res.statusText}`);
  }
  return res.json();
}
