"use client";

import React from "react";
import Link from "next/link";
import { TrendMetrics } from "@/types";
import { formatCurrency, formatNumber, formatSignedNumber, formatDate } from "@/lib/utils";
import { ScoreBadge } from "./ScoreBadge";
import { EvidenceBadge } from "./EvidenceBadge";
import { WatchButton } from "./WatchButton";
import { TrendingUp, ShoppingBag, Star, Sparkles, ExternalLink, ArrowUpRight, FolderPlus, Scale } from "lucide-react";

interface ProductCardProps {
  product: TrendMetrics;
  rank?: number;
  isWatched?: boolean;
  onToggleWatch?: (productId: number, watched: boolean) => void;
  onAddToCollection?: (productId: number, title: string) => void;
  onAddToCompare?: (productId: number, title: string, imageUrl?: string | null) => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({
  product,
  rank,
  isWatched = false,
  onToggleWatch,
  onAddToCollection,
  onAddToCompare,
}) => {
  const deltas = product.deltas || {};
  const sold24h = deltas.sold_delta_24h;
  const sold7d = deltas.sold_delta_7d;
  const review24h = deltas.review_delta_24h;
  const isRisingFast = (deltas.sales_velocity_24h || 0) > 100;
  const hasAcceleration = (deltas.sales_acceleration || 0) > 50;

  return (
    <div className="group rounded-xl border border-slate-800 bg-slate-900/60 p-5 hover:border-slate-700 hover:bg-slate-900/90 transition-all duration-200 shadow-sm flex flex-col justify-between">
      <div>
        {/* Top Header: Rank & Score */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="flex items-center space-x-2 flex-wrap gap-y-1">
            {rank !== undefined && (
              <span className="flex items-center justify-center w-6 h-6 rounded-md bg-slate-800 text-xs font-bold text-slate-300 border border-slate-700">
                #{rank}
              </span>
            )}
            {product.category && (
              <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-slate-800/80 text-slate-400 border border-slate-700/60 truncate max-w-[130px]">
                {product.category}
              </span>
            )}
            <EvidenceBadge evidence={product.evidence} size="sm" />
          </div>
          <div className="flex items-center gap-1.5">
            <WatchButton
              productId={product.product_id}
              isWatched={isWatched}
              onToggle={(watched) => onToggleWatch?.(product.product_id, watched)}
              size="sm"
            />
            <ScoreBadge score={product.trend_score} hasMomentumEvidence={deltas.sales_velocity_24h != null || deltas.sales_acceleration != null || deltas.review_delta_24h != null} />
          </div>
        </div>

        {/* Thumbnail & Title */}
        <div className="flex space-x-4">
          <div className="relative w-20 h-20 rounded-lg bg-slate-950 border border-slate-800 flex-shrink-0 overflow-hidden flex items-center justify-center text-slate-600">
            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.title}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
            ) : (
              <ShoppingBag className="h-8 w-8 opacity-40" />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <Link
              href={`/products/${product.product_id}`}
              className="font-medium text-sm text-slate-100 hover:text-rose-400 line-clamp-2 transition-colors"
            >
              {product.title}
            </Link>
            
            <div className="flex items-center space-x-2 mt-1.5 text-xs text-slate-400">
              <span className="truncate max-w-[150px]">{product.shop_name || "TikTok Shop"}</span>
              {deltas.latest_rating != null && (
                <span className="flex items-center text-amber-400 font-medium">
                  <Star className="h-3 w-3 fill-amber-400 mr-0.5" />
                  {deltas.latest_rating.toFixed(1)}
                </span>
              )}
            </div>

            <div className="mt-2 text-base font-bold text-slate-100">
              {formatCurrency(deltas.latest_price)}
            </div>
          </div>
        </div>

        {/* Sales Momentum Metrics Bar */}
        <div className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-slate-800/60 text-center">
          <div className="p-1.5 rounded-md bg-slate-950/40 border border-slate-800/40">
            <div className="text-[10px] text-slate-400 uppercase tracking-wider">Tổng Đã Bán</div>
            <div className="text-xs font-semibold text-slate-200 mt-0.5">
              {formatNumber(deltas.latest_sold_count)}
            </div>
          </div>

          <div className="p-1.5 rounded-md bg-slate-950/40 border border-slate-800/40">
            <div className="text-[10px] text-slate-400 uppercase tracking-wider">Chênh lệch 24h</div>
            <div className={`text-xs font-bold mt-0.5 ${sold24h && sold24h > 0 ? "text-emerald-400" : "text-slate-400"}`}>
              {formatSignedNumber(sold24h)}
            </div>
          </div>

          <div className="p-1.5 rounded-md bg-slate-950/40 border border-slate-800/40">
            <div className="text-[10px] text-slate-400 uppercase tracking-wider">Chênh lệch 7d</div>
            <div className={`text-xs font-semibold mt-0.5 ${sold7d && sold7d > 0 ? "text-cyan-400" : "text-slate-400"}`}>
              {formatSignedNumber(sold7d)}
            </div>
          </div>
        </div>

        {/* Signals & Badges */}
        <div className="flex flex-wrap gap-1.5 mt-3">
          {deltas.is_stale && <span className="text-xs text-amber-400 font-medium">⚠️ Dữ liệu cũ; cần quét lại</span>}
          {product.evidence?.ranking_state === "insufficient_measured_signal" && (
            <span className="text-xs text-slate-400 italic">Chưa đủ dữ liệu 2 chu kỳ đo lường</span>
          )}
          {hasAcceleration && (
            <span className="inline-flex items-center text-[10px] font-semibold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <TrendingUp className="h-2.5 w-2.5 mr-1" /> Gia tốc mạnh
            </span>
          )}
          {review24h != null && review24h > 10 && (
            <span className="inline-flex items-center text-[10px] font-medium px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
              +{review24h} đánh giá mới
            </span>
          )}
        </div>

        {/* Why Trending Deterministic Reasons */}
        {product.reasons && product.reasons.length > 0 && (
          <div className="mt-3 p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/60 space-y-1">
            <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
              Lý do xu hướng
            </div>
            <div className="space-y-1">
              {product.reasons.map((r, i) => (
                <div key={i} className="flex items-start gap-1.5 text-xs text-slate-300">
                  <span className="text-rose-400 font-bold">•</span>
                  <span>{r.formatted_text}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer Info & Actions */}
      <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
        <div>
          <span>Phát hiện: </span>
          <span className="text-slate-300">{formatDate(product.first_seen_at)}</span>
        </div>
        
        <div className="flex items-center gap-2">
          {onAddToCompare && (
            <button
              onClick={() => onAddToCompare(product.product_id, product.title, product.image_url)}
              title="Thêm vào khay so sánh"
              className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-cyan-400 transition-colors"
            >
              <Scale className="h-3 w-3" />
              <span>So sánh</span>
            </button>
          )}

          {onAddToCollection && (
            <button
              onClick={() => onAddToCollection(product.product_id, product.title)}
              title="Thêm vào Bộ sưu tập"
              className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-rose-400 transition-colors"
            >
              <FolderPlus className="h-3 w-3" />
              <span>BST</span>
            </button>
          )}

          <Link
            href={`/products/${product.product_id}`}
            className="inline-flex items-center gap-1 text-slate-300 hover:text-white font-medium transition-colors ml-1"
          >
            <span>Chi tiết</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
};
