"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchDashboardSummary,
  fetchTrends,
  fetchWatchlist,
  fetchWatchedProductIds,
  DashboardData,
  getExportTrendsUrl,
  getExportWatchlistUrl,
} from "@/lib/api";
import { TrendMetrics, TrendsSavedViewPayload, WatchlistSavedViewPayload } from "@/types";
import { ProductCard } from "@/components/ProductCard";
import { CrawlerControl } from "@/components/CrawlerControl";
import { SavedViewControl } from "@/components/SavedViewControl";
import { CollectionsWorkspace } from "@/components/CollectionsWorkspace";
import { CompareTray, StagedProduct } from "@/components/CompareTray";
import { CompareModal } from "@/components/CompareModal";
import { AddToCollectionModal } from "@/components/AddToCollectionModal";
import {
  Flame,
  TrendingUp,
  Sparkles,
  Trophy,
  Star,
  Search,
  RefreshCw,
  Download,
  Folder,
} from "lucide-react";

type TabType = "trending" | "rising" | "new" | "best-sellers" | "watchlist" | "collections";

const CATEGORIES = [
  "Tất cả danh mục",
  "Thời trang & Phụ kiện",
  "Sức khỏe & Làm đẹp",
  "Gia dụng & Đời sống",
  "Điện tử & Công nghệ",
  "Mẹ & Bé",
  "Thực phẩm & Đồ uống",
  "Đồ ăn & Đồ uống",
];

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>("trending");
  const [products, setProducts] = useState<TrendMetrics[]>([]);
  const [watchedProductIds, setWatchedProductIds] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState<boolean>(true);
  const [category, setCategory] = useState<string>("Tất cả danh mục");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [newProductsWindow, setNewProductsWindow] = useState<number>(72);
  const [bestSellersRankBy, setBestSellersRankBy] = useState<string>("total_sold");
  const [trendState, setTrendState] = useState<string>("eligible");
  const [evidenceFilter, setEvidenceFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("trend_score");
  const [sortOrder, setSortOrder] = useState<string>("desc");
  const [minScore, setMinScore] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const requestId = useRef(0);

  // Phase 5: Transient Compare staged products
  const [stagedCompare, setStagedCompare] = useState<StagedProduct[]>([]);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState(false);

  // Phase 5: Add to Collection modal state
  const [collectionModalProduct, setCollectionModalProduct] = useState<{
    id: number;
    title: string;
  } | null>(null);

  const handleAddToCompare = (productId: number, title: string, imageUrl?: string | null) => {
    setStagedCompare((prev) => {
      if (prev.some((p) => p.productId === productId)) return prev;
      if (prev.length >= 5) {
        alert("Khay so sánh hỗ trợ tối đa 5 sản phẩm. Vui lòng bỏ bớt một sản phẩm trước khi thêm.");
        return prev;
      }
      return [...prev, { productId, title, imageUrl }];
    });
  };

  const handleRemoveFromCompare = (productId: number) => {
    setStagedCompare((prev) => prev.filter((p) => p.productId !== productId));
  };

  const handleClearCompare = () => {
    setStagedCompare([]);
  };

  const handleAddToCollection = (productId: number, title: string) => {
    setCollectionModalProduct({ id: productId, title });
  };

  const handleApplyTrendsView = (payload: TrendsSavedViewPayload) => {
    setCategory(payload.category ?? "Tất cả danh mục");
    setTrendState(payload.trend_state);
    if (payload.measured_only) {
      setEvidenceFilter("measured_only");
    } else if (payload.confidence) {
      setEvidenceFilter(payload.confidence);
    } else {
      setEvidenceFilter("all");
    }
    setSortBy(payload.sort_by);
    setSortOrder(payload.sort_direction);
    setSearchQuery(payload.search ?? "");
    setMinScore(payload.min_score ?? 0);
  };

  const handleApplyWatchlistView = (payload: WatchlistSavedViewPayload) => {
    setCategory(payload.category ?? "Tất cả danh mục");
    setTrendState(payload.trend_state);
    if (payload.measured_only) {
      setEvidenceFilter("measured_only");
    } else if (payload.confidence) {
      setEvidenceFilter(payload.confidence);
    } else {
      setEvidenceFilter("all");
    }
    setSortBy(payload.sort_by);
    setSortOrder(payload.sort_direction);
    // Applying Watchlist saved view always resets pagination skip=0
  };

  const loadData = useCallback(async () => {
    const id = ++requestId.current;
    setLoading(true);
    setError(null);
    try {
      const catParam = category === "Tất cả danh mục" ? undefined : category;

      // Always fetch watched IDs concurrently
      const watchedIdsPromise = fetchWatchedProductIds().catch(() => []);

      let listPromise: Promise<TrendMetrics[]>;
      if (activeTab === "collections") {
        listPromise = Promise.resolve([]);
      } else if (activeTab === "watchlist") {
        listPromise = fetchWatchlist({
          category: catParam,
          trend_state: trendState,
          confidence:
            evidenceFilter === "high" || evidenceFilter === "medium_or_high"
              ? evidenceFilter
              : undefined,
          evidence: evidenceFilter === "measured_only" ? "measured_only" : undefined,
          sort_by: sortBy,
          order: sortOrder,
        }).then((res) =>
          res.items.map((item) => {
            if (item.analysis) return item.analysis;
            return {
              product_id: item.product_id,
              external_product_id:
                item.product?.external_product_id || String(item.product_id),
              title: item.product?.title || `Sản phẩm #${item.product_id}`,
              url: item.product?.url,
              image_url: item.product?.image_url,
              shop_id: item.product?.shop_id,
              shop_name: item.product?.shop_name,
              category: item.product?.category,
              first_seen_at: item.product?.first_seen_at || item.created_at,
              last_seen_at: item.product?.last_seen_at || item.created_at,
              deltas: {},
              trend_score: 0,
              evidence: null,
              reasons: [],
            };
          })
        );
      } else {
        listPromise = fetchTrends(activeTab, {
          category: catParam,
          rank_by: activeTab === "best-sellers" ? bestSellersRankBy : undefined,
          hours: activeTab === "new" ? newProductsWindow : undefined,
          trend_state: activeTab === "trending" ? trendState : undefined,
          confidence:
            activeTab === "trending" &&
            (evidenceFilter === "high" || evidenceFilter === "medium_or_high")
              ? evidenceFilter
              : undefined,
          evidence:
            activeTab === "trending" && evidenceFilter === "measured_only"
              ? "measured_only"
              : undefined,
          sort_by: activeTab === "trending" ? sortBy : undefined,
          order: activeTab === "trending" ? sortOrder : undefined,
        });
      }

      const [summary, trendList, watchedIds] = await Promise.all([
        fetchDashboardSummary(),
        listPromise,
        watchedIdsPromise,
      ]);

      if (id !== requestId.current) return;
      setData(summary);
      setProducts(trendList);
      setWatchedProductIds(new Set(watchedIds));
    } catch (e) {
      if (id !== requestId.current) return;
      setError("Không tải được dữ liệu. Kiểm tra kết nối backend và bấm tải lại.");
      setProducts([]);
      setData(null);
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  }, [
    activeTab,
    category,
    newProductsWindow,
    bestSellersRankBy,
    trendState,
    evidenceFilter,
    sortBy,
    sortOrder,
  ]);

  useEffect(() => {
    loadData();
    const sequence = requestId;
    return () => {
      sequence.current++;
    };
  }, [loadData]);

  const handleToggleWatch = (productId: number, watched: boolean) => {
    setWatchedProductIds((prev) => {
      const next = new Set(prev);
      if (watched) {
        next.add(productId);
      } else {
        next.delete(productId);
        if (activeTab === "watchlist") {
          setProducts((cur) => cur.filter((p) => p.product_id !== productId));
        }
      }
      return next;
    });
  };

  // Client side search and min score filter
  const filteredProducts = products.filter((p) => {
    if (minScore > 0 && p.trend_score < minScore) return false;
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      p.title.toLowerCase().includes(q) ||
      (p.shop_name && p.shop_name.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6">
      {/* Top Banner: Crawler Control */}
      <CrawlerControl onCrawlCompleted={loadData} />
      {error && (
        <div role="alert" className="p-4 rounded-lg border border-rose-800 text-rose-300">
          {error} <button onClick={loadData} className="underline ml-2">Tải lại</button>
        </div>
      )}

      {/* KPI Stats Overview */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 shadow-sm">
          <div className="text-xs font-medium text-slate-400">Tổng sản phẩm đã quét</div>
          <div className="text-2xl font-bold text-white mt-1">
            {data?.stats?.total_products ?? "—"}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Được theo dõi tự động</div>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 shadow-sm">
          <div className="text-xs font-medium text-slate-400">Cơ hội Xu hướng Cao (Score ≥ 70)</div>
          <div className="text-2xl font-bold text-rose-400 mt-1">
            {data?.stats?.high_trend_count ?? "—"}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Tăng trưởng & gia tốc tốt</div>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 shadow-sm">
          <div className="text-xs font-medium text-slate-400">Sản phẩm mới phát hiện</div>
          <div className="text-2xl font-bold text-cyan-400 mt-1">
            {data?.new_products?.length ?? "—"}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Trong 72 giờ qua</div>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 shadow-sm">
          <div className="text-xs font-medium text-slate-400">Đang theo dõi (Watchlist)</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">
            {watchedProductIds.size}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Nguồn quét định kỳ tự động</div>
        </div>
      </div>

      {/* Tabs & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        {/* Navigation Tabs */}
        <div className="flex items-center space-x-1 p-1 rounded-lg bg-slate-900 border border-slate-800 self-start flex-wrap gap-y-1">
          <button
            onClick={() => setActiveTab("trending")}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
              activeTab === "trending"
                ? "bg-rose-600 text-white shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Flame className="h-3.5 w-3.5" />
            <span>🔥 Trending</span>
          </button>

          <button
            onClick={() => setActiveTab("rising")}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
              activeTab === "rising"
                ? "bg-amber-600 text-white shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <TrendingUp className="h-3.5 w-3.5" />
            <span>🚀 Rising</span>
          </button>

          <button
            onClick={() => setActiveTab("new")}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
              activeTab === "new"
                ? "bg-cyan-600 text-white shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>🆕 Mới Phát Hiện</span>
          </button>

          <button
            onClick={() => setActiveTab("best-sellers")}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
              activeTab === "best-sellers"
                ? "bg-yellow-600 text-white shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Trophy className="h-3.5 w-3.5" />
            <span>🏆 Bán Chạy Nhất</span>
          </button>

          <button
            onClick={() => setActiveTab("watchlist")}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
              activeTab === "watchlist"
                ? "bg-amber-500 text-slate-950 font-bold shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Star className={`h-3.5 w-3.5 ${activeTab === "watchlist" ? "fill-slate-950" : ""}`} />
            <span>⭐ Watchlist ({watchedProductIds.size})</span>
          </button>

          <button
            onClick={() => setActiveTab("collections")}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
              activeTab === "collections"
                ? "bg-purple-600 text-white font-bold shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Folder className="h-3.5 w-3.5" />
            <span>📁 Bộ sưu tập</span>
          </button>
        </div>

        {/* Tab-specific sub-filters */}
        <div className="flex items-center space-x-3">
          {activeTab === "new" && (
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-slate-400">Thời gian:</span>
              <select
                value={newProductsWindow}
                onChange={(e) => setNewProductsWindow(Number(e.target.value))}
                className="rounded-lg bg-slate-900 border border-slate-800 px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                <option value={24}>24 giờ qua</option>
                <option value={72}>3 ngày qua</option>
                <option value={168}>7 ngày qua</option>
              </select>
            </div>
          )}

          {activeTab === "best-sellers" && (
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-slate-400">Sắp xếp theo:</span>
              <select
                value={bestSellersRankBy}
                onChange={(e) => setBestSellersRankBy(e.target.value)}
                className="rounded-lg bg-slate-900 border border-slate-800 px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-yellow-500"
              >
                <option value="total_sold">Tổng đã bán (Lifetime)</option>
                <option value="sold_delta_24h">Lượng bán 24h</option>
                <option value="sold_delta_7d">Lượng bán 7 ngày</option>
              </select>
            </div>
          )}

          <button
            onClick={loadData}
            aria-label="Tải lại dữ liệu"
            disabled={loading}
            className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>

          {(activeTab === "trending" || activeTab === "watchlist") && (
            <a
              href={
                activeTab === "watchlist"
                  ? getExportWatchlistUrl({
                      category: category === "Tất cả danh mục" ? undefined : category,
                      trend_state: trendState,
                      confidence:
                        evidenceFilter === "high" || evidenceFilter === "medium_or_high"
                          ? evidenceFilter
                          : undefined,
                      evidence: evidenceFilter === "measured_only" ? "measured_only" : undefined,
                      sort_by: sortBy,
                      order: sortOrder,
                    })
                  : getExportTrendsUrl({
                      category: category === "Tất cả danh mục" ? undefined : category,
                      trend_state: trendState,
                      confidence:
                        evidenceFilter === "high" || evidenceFilter === "medium_or_high"
                          ? evidenceFilter
                          : undefined,
                      evidence: evidenceFilter === "measured_only" ? "measured_only" : undefined,
                      sort_by: sortBy,
                      order: sortOrder,
                    })
              }
              download={activeTab === "watchlist" ? "watchlist_export.csv" : "trends_export.csv"}
              aria-label={activeTab === "watchlist" ? "Xuất CSV Watchlist" : "Xuất CSV Xu hướng"}
              className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors text-xs font-medium"
            >
              <Download className="h-3.5 w-3.5 text-slate-400" />
              <span className="hidden sm:inline">Xuất CSV</span>
            </a>
          )}
        </div>
      </div>

      {/* Collections Workspace Tab */}
      {activeTab === "collections" ? (
        <CollectionsWorkspace onAddToCompare={handleAddToCompare} />
      ) : (
        <>
          {/* Saved Views Control on Trending and Watchlist */}
          {(activeTab === "trending" || activeTab === "watchlist") && (
            <div className="flex items-center justify-between gap-3 bg-slate-900/50 border border-slate-800/80 rounded-xl px-4 py-2.5">
              <SavedViewControl
                scope={activeTab === "watchlist" ? "watchlist" : "trends"}
                currentPayload={
                  activeTab === "watchlist"
                    ? {
                        category: category === "Tất cả danh mục" ? null : category,
                        trend_state: trendState,
                        measured_only: evidenceFilter === "measured_only",
                        confidence:
                          evidenceFilter === "high" || evidenceFilter === "medium_or_high"
                            ? evidenceFilter
                            : null,
                        sort_by: sortBy,
                        sort_direction: sortOrder as "asc" | "desc",
                        limit: 50,
                      }
                    : {
                        category: category === "Tất cả danh mục" ? null : category,
                        trend_state: trendState,
                        measured_only: evidenceFilter === "measured_only",
                        confidence:
                          evidenceFilter === "high" || evidenceFilter === "medium_or_high"
                            ? evidenceFilter
                            : null,
                        sort_by: sortBy,
                        sort_direction: sortOrder as "asc" | "desc",
                        limit: 50,
                        search: searchQuery || null,
                        min_score: minScore || null,
                      }
                }
                onApply={
                  activeTab === "watchlist"
                    ? handleApplyWatchlistView
                    : handleApplyTrendsView
                }
              />
            </div>
          )}

          {/* Filter Bar: Category, Search, Min Score */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-4 rounded-xl bg-slate-900/40 border border-slate-800/80">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="text"
                aria-label="Tìm sản phẩm trong kết quả hiện tại"
                placeholder="Tìm theo tên sản phẩm, shop..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-rose-500"
              />
            </div>

            <div>
              <select
                value={category}
                aria-label="Danh mục sản phẩm"
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-rose-500"
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-400 whitespace-nowrap">Điểm tối thiểu:</span>
              <input
                type="range"
                aria-label="Điểm xu hướng tối thiểu"
                min="0"
                max="90"
                step="10"
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-rose-500"
              />
              <span className="text-xs font-semibold text-rose-400 w-8">{minScore}+</span>
            </div>
          </div>

          {/* Decision Controls: Trend State, Evidence/Confidence, Sort Selection */}
          {(activeTab === "trending" || activeTab === "watchlist") && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-4 rounded-xl bg-slate-900/30 border border-slate-800/60 text-xs">
              <div>
                <label htmlFor="trend-state-filter" className="block text-slate-400 font-medium mb-1.5">Trạng thái Dữ liệu:</label>
                <select
                  id="trend-state-filter"
                  aria-label="Trạng thái dữ liệu"
                  value={trendState}
                  onChange={(e) => setTrendState(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-rose-500"
                >
                  <option value="eligible">🔥 Đang có xu hướng (Đủ điều kiện)</option>
                  <option value="all">🌐 Tất cả sản phẩm theo dõi</option>
                  <option value="stale">⚠️ Dữ liệu cũ (&gt; 8h)</option>
                  <option value="insufficient_signal">⏳ Chưa đủ đo lường 2 chu kỳ</option>
                </select>
              </div>

              <div>
                <label htmlFor="evidence-filter" className="block text-slate-400 font-medium mb-1.5">Độ tin cậy & Bằng chứng:</label>
                <select
                  id="evidence-filter"
                  aria-label="Độ tin cậy và bằng chứng"
                  value={evidenceFilter}
                  onChange={(e) => setEvidenceFilter(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-rose-500"
                >
                  <option value="all">Tất cả mức tin cậy</option>
                  <option value="high">🟢 Tin cậy Cao (≥5 quan sát, ~24h chuẩn)</option>
                  <option value="medium_or_high">🔵 Tin cậy Trung bình trở lên</option>
                  <option value="measured_only">📏 Chỉ đo lường chuẩn ~24h (không ước tính)</option>
                </select>
              </div>

              <div>
                <label htmlFor="sort-by" className="block text-slate-400 font-medium mb-1.5">Sắp xếp theo:</label>
                <div className="flex gap-2">
                  <select
                    id="sort-by"
                    aria-label="Sắp xếp danh sách"
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="flex-1 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-rose-500"
                  >
                    <option value="trend_score">Điểm xu hướng (Trend Score)</option>
                    <option value="sales_velocity">Tốc độ bán 24h (Sales Velocity)</option>
                    <option value="sales_delta">Lượng bán 24h thực tế</option>
                    <option value="review_delta">Lượt đánh giá mới 24h</option>
                    <option value="freshness">Cập nhật gần nhất (Freshness)</option>
                  </select>
                  <button
                    type="button"
                    aria-label="Đổi hướng sắp xếp"
                    onClick={() => setSortOrder(sortOrder === "desc" ? "asc" : "desc")}
                    className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700"
                    title={sortOrder === "desc" ? "Giảm dần" : "Tăng dần"}
                  >
                    {sortOrder === "desc" ? "↓" : "↑"}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Product List Content */}
          {loading ? (
            <div className="text-center py-20 text-slate-500 flex flex-col items-center justify-center space-y-2">
              <RefreshCw className="h-6 w-6 animate-spin text-slate-400" />
              <span>Đang tính toán phân tích dữ liệu...</span>
            </div>
          ) : error ? null : filteredProducts.length === 0 ? (
            <div className="text-center py-20 rounded-xl border border-dashed border-slate-800 bg-slate-900/20 text-slate-400">
              <p className="text-base font-semibold">
                {activeTab === "watchlist"
                  ? "Chưa có sản phẩm nào trong Watchlist"
                  : activeTab === "trending"
                  ? "Chưa có lịch sử đủ để xếp hạng xu hướng"
                  : "Chưa tìm thấy sản phẩm phù hợp"}
              </p>
              <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                {activeTab === "watchlist"
                  ? "Bấm vào biểu tượng ngôi sao ⭐ trên bất kỳ thẻ sản phẩm nào hoặc gửi URL sản phẩm để đưa vào danh sách theo dõi định kỳ."
                  : activeTab === "trending"
                  ? "Quét sản phẩm đã theo dõi định kỳ; điểm xu hướng xuất hiện khi có ít nhất hai quan sát trong khoảng phù hợp."
                  : "Hãy thử điều chỉnh bộ lọc hoặc bấm \"Chạy Crawler Ngay\" để quét thêm sản phẩm mới."}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredProducts.map((prod, index) => (
                <ProductCard
                  key={prod.product_id}
                  product={prod}
                  rank={index + 1}
                  isWatched={watchedProductIds.has(prod.product_id)}
                  onToggleWatch={handleToggleWatch}
                  onAddToCompare={handleAddToCompare}
                  onAddToCollection={handleAddToCollection}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Phase 5: Transient Compare Tray */}
      <CompareTray
        staged={stagedCompare}
        onRemove={handleRemoveFromCompare}
        onClear={handleClearCompare}
        onOpenCompare={() => setIsCompareModalOpen(true)}
      />

      {/* Phase 5: Compare Modal */}
      <CompareModal
        productIds={stagedCompare.map((p) => p.productId)}
        isOpen={isCompareModalOpen}
        onClose={() => setIsCompareModalOpen(false)}
      />

      {/* Phase 5: Add to Collection Modal */}
      {collectionModalProduct && (
        <AddToCollectionModal
          productId={collectionModalProduct.id}
          productTitle={collectionModalProduct.title}
          isOpen={true}
          onClose={() => setCollectionModalProduct(null)}
        />
      )}
    </div>
  );
}
