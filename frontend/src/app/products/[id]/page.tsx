"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchProductDetail, ProductDetailData } from "@/lib/api";
import { ScoreBadge } from "@/components/ScoreBadge";
import { formatCurrency, formatNumber, formatSignedNumber, formatSignedRate, formatDate } from "@/lib/utils";
import {
  ArrowLeft,
  ExternalLink,
  ShoppingBag,
  Star,
} from "lucide-react";
import { ProductHistory } from "@/components/ProductHistory";

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const productId = params?.id as string;

  const [product, setProduct] = useState<ProductDetailData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!productId) return;
    setLoading(true);
    setError(null);
    let active = true;
    fetchProductDetail(productId)
      .then((data) => { if (active) setProduct(data); })
      .catch((err) => { if (active) setError(err.message || "Không thể tải thông tin sản phẩm"); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [productId, reloadKey]);

  if (loading) {
    return (
      <div className="py-24 text-center text-slate-400">
        <div className="animate-spin h-8 w-8 border-2 border-rose-500 border-t-transparent rounded-full mx-auto mb-4"></div>
        <span>Đang tải thông tin chi tiết sản phẩm...</span>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="py-16 text-center space-y-4">
        <p className="text-rose-400 font-semibold">{error || "Không tìm thấy sản phẩm"}</p>
        <button
          onClick={() => router.push("/")}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 text-xs font-semibold text-white hover:bg-slate-700"
        >
          <ArrowLeft className="h-4 w-4" /> Quay lại Dashboard
        </button>
        <button onClick={() => setReloadKey(value => value + 1)} className="rounded-lg bg-rose-600 px-4 py-2 text-xs font-semibold text-white hover:bg-rose-500">
          Thử tải lại
        </button>
      </div>
    );
  }

  const analysis = product.analysis;
  const deltas = analysis.deltas || {};
  return (
    <div className="space-y-8">
      {/* Top Breadcrumb & Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => router.push("/")}
          className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Quay lại Dashboard</span>
        </button>

        {product.url && (
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition-colors"
          >
            <span>Mở trên TikTok Shop</span>
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        )}
      </div>

      {/* Main Info Card */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row gap-6">
          <div className="w-32 h-32 md:w-44 md:h-44 rounded-xl bg-slate-950 border border-slate-800 flex-shrink-0 overflow-hidden flex items-center justify-center text-slate-600">
            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.title}
                className="w-full h-full object-cover"
              />
            ) : (
              <ShoppingBag className="h-12 w-12 opacity-30" />
            )}
          </div>

          <div className="flex-1 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center space-x-2">
                {product.category && (
                  <span className="text-xs px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                    {product.category}
                  </span>
                )}
                <span className="text-xs text-slate-500">ID: {product.external_product_id}</span>
              </div>
              <ScoreBadge score={analysis.trend_score} size="lg" hasMomentumEvidence={deltas.sales_velocity_24h != null || deltas.sales_acceleration != null || deltas.review_delta_24h != null} />
            </div>

            <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight leading-snug">
              {product.title}
            </h1>

            <div className="flex flex-wrap items-center gap-6 text-sm text-slate-400">
              <div>
                Shop: <span className="text-slate-200 font-semibold">{product.shop_name || "TikTok Shop"}</span>
              </div>
              {deltas.latest_rating != null && (
                <div className="flex items-center text-amber-400 font-medium">
                  <Star className="h-4 w-4 fill-amber-400 mr-1" />
                  {deltas.latest_rating.toFixed(2)} ({formatNumber(deltas.latest_review_count)} đánh giá)
                </div>
              )}
              <div title="Giá do trang sản phẩm hiển thị; có thể là giá thấp nhất khi có nhiều phân loại. Giá cuối cùng phụ thuộc phân loại và ưu đãi.">
                Giá hiển thị:{" "}
                <span className="text-lg font-bold text-rose-400">
                  {formatCurrency(deltas.latest_price)}
                </span>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800/80 flex flex-wrap gap-4 text-xs text-slate-400">
              <div>
                Phát hiện lần đầu: <span className="text-slate-300">{formatDate(product.first_seen_at)}</span>
              </div>
              <div>
                Cập nhật lần cuối: <span className="text-slate-300">{formatDate(product.last_seen_at)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Analytics Velocity & Acceleration Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
          <div className="text-xs text-slate-400 uppercase tracking-wider">Tốc độ bán/ngày</div>
          <div className={`text-2xl font-bold mt-1 ${(deltas.sales_velocity_24h ?? 0) < 0 ? "text-rose-400" : "text-emerald-400"}`}>
            {formatSignedRate(deltas.sales_velocity_24h)}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">{deltas.is_stale ? "Dữ liệu cũ; cần quét lại" : deltas.velocity_is_estimated ? "Ước tính / ngày từ lịch sử hiện có" : "Đơn vị / ngày"}</div>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
          <div className="text-xs text-slate-400 uppercase tracking-wider">Gia tốc Bán Hàng</div>
          <div className={`text-2xl font-bold mt-1 ${deltas.sales_acceleration && deltas.sales_acceleration > 0 ? "text-rose-400" : "text-slate-400"}`}>
            {deltas.sales_acceleration != null ? (deltas.sales_acceleration > 0 ? `+${deltas.sales_acceleration.toFixed(0)}` : deltas.sales_acceleration.toFixed(0)) : "—"}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">So với chu kỳ trước</div>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
          <div className="text-xs text-slate-400 uppercase tracking-wider">Chênh lệch đánh giá 24h</div>
          <div className={`text-2xl font-bold mt-1 ${(deltas.review_delta_24h ?? 0) < 0 ? "text-rose-400" : "text-cyan-400"}`}>
            {formatSignedNumber(deltas.review_delta_24h)}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Lượt review mới</div>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
          <div className="text-xs text-slate-400 uppercase tracking-wider">Hoa hồng Ước tính</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">
            {deltas.latest_commission_rate != null ? `${deltas.latest_commission_rate}%` : "—"}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Tỷ lệ Affiliate</div>
        </div>
      </div>

      <ProductHistory snapshots={product.snapshots || []} />
    </div>
  );
}
