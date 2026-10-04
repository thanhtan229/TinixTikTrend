"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchDashboardSummary, fetchTrends, DashboardData } from "@/lib/api";
import { TrendMetrics } from "@/types";
import { ProductCard } from "@/components/ProductCard";
import { CrawlerControl } from "@/components/CrawlerControl";
import { Flame, TrendingUp, Sparkles, Trophy, Search, Filter, RefreshCw, LayoutGrid, ListFilter } from "lucide-react";

type TabType = "trending" | "rising" | "new" | "best-sellers";

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
  const [loading, setLoading] = useState<boolean>(true);
  const [category, setCategory] = useState<string>("Tất cả danh mục");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [newProductsWindow, setNewProductsWindow] = useState<number>(72);
  const [bestSellersRankBy, setBestSellersRankBy] = useState<string>("total_sold");
  const [minScore, setMinScore] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const requestId = useRef(0);

  const loadData = useCallback(async () => {
    const id = ++requestId.current;
    setLoading(true);
    setError(null);
    try {
      const catParam = category === "Tất cả danh mục" ? undefined : category;
      const [summary, trendList] = await Promise.all([fetchDashboardSummary(), fetchTrends(activeTab, {
        category: catParam,
        rank_by: activeTab === "best-sellers" ? bestSellersRankBy : undefined,
        hours: activeTab === "new" ? newProductsWindow : undefined,
      })]);
      if (id !== requestId.current) return;
      setData(summary);
      setProducts(trendList);
    } catch (e) {
      if (id !== requestId.current) return;
      setError("Không tải được dữ liệu. Kiểm tra kết nối backend và bấm tải lại.");
      setProducts([]);
      setData(null);
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  }, [activeTab, category, newProductsWindow, bestSellersRankBy]);

  useEffect(() => {
    loadData();
    const sequence = requestId;
    return () => { sequence.current++; };
  }, [loadData]);

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
      {error && <div role="alert" className="p-4 rounded-lg border border-rose-800 text-rose-300">
        {error} <button onClick={loadData} className="underline ml-2">Tải lại</button>
      </div>}

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
          <div className="text-xs font-medium text-slate-400">Chi phí Vận hành</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">0đ (Local)</div>
          <div className="text-[11px] text-slate-500 mt-1">Chạy hoàn toàn trên máy tính cá nhân</div>
        </div>
      </div>

      {/* Tabs & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        {/* Navigation Tabs */}
        <div className="flex items-center space-x-1 p-1 rounded-lg bg-slate-900 border border-slate-800 self-start">
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
        </div>
      </div>

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

      {/* Product List Content */}
      {loading ? (
        <div className="text-center py-20 text-slate-500 flex flex-col items-center justify-center space-y-2">
          <RefreshCw className="h-6 w-6 animate-spin text-slate-400" />
          <span>Đang tính toán phân tích dữ liệu...</span>
        </div>
      ) : error ? null : filteredProducts.length === 0 ? (
        <div className="text-center py-20 rounded-xl border border-dashed border-slate-800 bg-slate-900/20 text-slate-400">
          <p className="text-base font-semibold">{activeTab === "trending" ? "Chưa có lịch sử đủ để xếp hạng xu hướng" : "Chưa tìm thấy sản phẩm phù hợp"}</p>
          <p className="text-xs text-slate-500 mt-1">
            {activeTab === "trending" ? "Quét sản phẩm đã theo dõi định kỳ; điểm xu hướng xuất hiện khi có ít nhất hai quan sát trong khoảng phù hợp." : "Hãy thử điều chỉnh bộ lọc hoặc bấm \"Chạy Crawler Ngay\" để quét thêm sản phẩm mới."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredProducts.map((prod, index) => (
            <ProductCard key={prod.product_id} product={prod} rank={index + 1} />
          ))}
        </div>
      )}
    </div>
  );
}
