"use client";

import React, { useCallback, useEffect, useState } from "react";
import { CompareResponse, ComparedProduct } from "@/types";
import { compareProducts } from "@/lib/api";
import { formatCurrency, formatNumber, formatSignedNumber, formatDate } from "@/lib/utils";
import { ScoreBadge } from "./ScoreBadge";
import {
  Scale,
  X,
  RefreshCw,
  ShoppingBag,
  ExternalLink,
  Star,
  CheckCircle2,
  AlertCircle,
  Clock,
  Bell,
  TrendingUp,
  Coins,
  Calculator,
} from "lucide-react";
import Link from "next/link";

interface CompareModalProps {
  productIds: number[];
  collectionId?: number;
  isOpen: boolean;
  onClose: () => void;
}

export const CompareModal: React.FC<CompareModalProps> = ({
  productIds,
  collectionId,
  isOpen,
  onClose,
}) => {
  const [data, setData] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadComparison = useCallback(async () => {
    if (productIds.length < 2 || productIds.length > 5) return;
    setLoading(true);
    setError(null);
    try {
      const res = await compareProducts(productIds, collectionId);
      setData(res);
    } catch (err: any) {
      setError(err.message || "Lỗi khi so sánh sản phẩm");
    } finally {
      setLoading(false);
    }
  }, [productIds, collectionId]);

  useEffect(() => {
    if (isOpen) {
      loadComparison();
    } else {
      setData(null);
      setError(null);
    }
  }, [isOpen, loadComparison]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-3 sm:p-6 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-6xl w-full max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 sm:p-5 border-b border-slate-800 bg-slate-950/60">
          <div>
            <div className="flex items-center gap-2">
              <Scale className="h-5 w-5 text-cyan-400" />
              <h2 className="text-base sm:text-lg font-bold text-white">
                Bảng Đối chiếu So sánh Sản phẩm ({productIds.length} sản phẩm)
              </h2>
            </div>
            {data?.as_of_utc && (
              <div className="flex items-center gap-1.5 text-xs text-slate-400 mt-1">
                <Clock className="h-3.5 w-3.5 text-cyan-400" />
                <span>
                  Đánh giá đồng thời tại mốc thời gian UTC (shared request time):{" "}
                  <strong className="text-slate-200 font-mono">{data.as_of_utc}</strong>
                </span>
              </div>
            )}
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body content */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
          {loading ? (
            <div className="py-24 text-center space-y-3">
              <RefreshCw className="h-8 w-8 animate-spin text-cyan-400 mx-auto" />
              <p className="text-xs text-slate-400">Đang đối chiếu dữ liệu sản phẩm trong một truy vấn duy nhất...</p>
            </div>
          ) : error ? (
            <div className="py-16 text-center space-y-3">
              <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs max-w-md mx-auto">
                <AlertCircle className="h-5 w-5 text-rose-400 mx-auto mb-2" />
                <p className="font-semibold">{error}</p>
              </div>
              <button
                onClick={loadComparison}
                className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs"
              >
                Thử lại
              </button>
            </div>
          ) : !data || data.products.length === 0 ? (
            <div className="py-16 text-center text-xs text-slate-500">
              Không có dữ liệu so sánh.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <tbody>
                  {/* Row 1: Product Header Cards */}
                  <tr className="border-b border-slate-800">
                    <td className="p-3 font-semibold text-slate-400 w-44 min-w-[170px] bg-slate-950/40">
                      Sản phẩm
                    </td>
                    {data.products.map((p) => (
                      <td key={p.product_id} className="p-3 min-w-[200px] align-top">
                        <div className="space-y-2">
                          <div className="w-20 h-20 rounded-lg bg-slate-950 border border-slate-800 overflow-hidden flex items-center justify-center">
                            {p.image_url ? (
                              <img
                                src={p.image_url}
                                alt={p.title}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <ShoppingBag className="h-8 w-8 text-slate-600" />
                            )}
                          </div>
                          <Link
                            href={`/products/${p.product_id}`}
                            className="font-medium text-slate-100 hover:text-cyan-400 line-clamp-2 transition-colors block"
                          >
                            {p.title}
                          </Link>
                          <div className="text-[11px] text-slate-400">
                            {p.shop_name || "TikTok Shop"} • {p.category || "—"}
                          </div>
                        </div>
                      </td>
                    ))}
                  </tr>

                  {/* Row 2: Price & Rating */}
                  <tr className="border-b border-slate-800/60 bg-slate-900/20">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Giá hiện tại & Đánh giá
                    </td>
                    {data.products.map((p) => (
                      <td key={p.product_id} className="p-3">
                        <div className="font-bold text-sm text-white">
                          {p.current_price != null ? formatCurrency(p.current_price) : "—"}
                        </div>
                        <div className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-1">
                          {p.rating != null ? (
                            <span className="flex items-center text-amber-400">
                              <Star className="h-3 w-3 fill-amber-400 mr-0.5" />
                              {p.rating.toFixed(1)}
                            </span>
                          ) : (
                            "—"
                          )}
                          <span>({p.review_count != null ? formatNumber(p.review_count) : "—"} đánh giá)</span>
                        </div>
                      </td>
                    ))}
                  </tr>

                  {/* Row 3: Watch Status */}
                  <tr className="border-b border-slate-800/60">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Theo dõi (Watchlist)
                    </td>
                    {data.products.map((p) => (
                      <td key={p.product_id} className="p-3">
                        {p.is_watched ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full">
                            <Star className="h-3 w-3 fill-amber-400" />
                            <span>Đang theo dõi</span>
                          </span>
                        ) : (
                          <span className="text-slate-500 italic text-[11px]">Chưa theo dõi</span>
                        )}
                      </td>
                    ))}
                  </tr>

                  {/* Row 4: Collection Context (if present) */}
                  {data.collection_id != null && (
                    <tr className="border-b border-slate-800/60 bg-slate-900/20">
                      <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                        Ngữ cảnh Bộ sưu tập
                      </td>
                      {data.products.map((p) => (
                        <td key={p.product_id} className="p-3">
                          {p.collection_context ? (
                            <div className="space-y-1">
                              <span className="inline-block px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-200 border border-slate-700">
                                {p.collection_context.review_status}
                              </span>
                              {p.collection_context.notes && (
                                <p className="text-[11px] text-slate-400 italic">
                                  &quot;{p.collection_context.notes}&quot;
                                </p>
                              )}
                            </div>
                          ) : (
                            <span className="text-slate-500 italic text-[11px]">Không thuộc BST này</span>
                          )}
                        </td>
                      ))}
                    </tr>
                  )}

                  {/* Row 5: Trend Score & State */}
                  <tr className="border-b border-slate-800/60">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Điểm xu hướng & Trạng thái
                    </td>
                    {data.products.map((p) => (
                      <td key={p.product_id} className="p-3">
                        <div className="flex items-center gap-2">
                          <ScoreBadge score={p.trend_score} />
                          <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                            {p.trend_state}
                          </span>
                        </div>
                      </td>
                    ))}
                  </tr>

                  {/* Row 6: Evidence Confidence */}
                  <tr className="border-b border-slate-800/60 bg-slate-900/20">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Độ tin cậy bằng chứng
                    </td>
                    {data.products.map((p) => (
                      <td key={p.product_id} className="p-3">
                        <div className="space-y-1">
                          <span
                            className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                              p.confidence === "high"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : p.confidence === "medium"
                                ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                                : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            }`}
                          >
                            {p.confidence ? `Tin cậy: ${p.confidence}` : "Chưa xác định"}
                          </span>
                          <div>
                            {p.velocity_is_estimated ? (
                              <span className="text-[10px] text-amber-400 italic">
                                Tốc độ ước tính
                              </span>
                            ) : (
                              <span className="text-[10px] text-emerald-400">
                                Đo lường thực tế
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                    ))}
                  </tr>

                  {/* Row 7: Why Trending Reasons */}
                  <tr className="border-b border-slate-800/60">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Lý do xu hướng
                    </td>
                    {data.products.map((p) => (
                      <td key={p.product_id} className="p-3 align-top">
                        {p.reasons && p.reasons.length > 0 ? (
                          <div className="space-y-1">
                            {p.reasons.map((r, i) => (
                              <div key={i} className="text-[11px] text-slate-300 flex items-start gap-1">
                                <span className="text-cyan-400">•</span>
                                <span>{typeof r === "string" ? r : r.formatted_text}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <span className="text-slate-500 text-[11px]">—</span>
                        )}
                      </td>
                    ))}
                  </tr>

                  {/* Row 8: 24h Velocity & Acceleration */}
                  <tr className="border-b border-slate-800/60 bg-slate-900/20">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Tốc độ bán 24h & Gia tốc
                    </td>
                    {data.products.map((p) => (
                      <td key={p.product_id} className="p-3">
                        <div className="font-semibold text-slate-200">
                          {p.sales_velocity_24h != null ? `${formatNumber(Math.round(p.sales_velocity_24h))} sp/ngày` : "—"}
                        </div>
                        <div className="text-[11px] text-slate-400 mt-0.5">
                          Gia tốc: {p.sales_acceleration != null ? `${formatSignedNumber(Math.round(p.sales_acceleration))} sp/ngày²` : "—"}
                        </div>
                      </td>
                    ))}
                  </tr>

                  {/* Row 9: Sales Delta 24h & 7d */}
                  <tr className="border-b border-slate-800/60">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Chênh lệch đã bán (24h / 7d)
                    </td>
                    {data.products.map((p) => (
                      <td key={p.product_id} className="p-3">
                        <div className="font-semibold text-emerald-400">
                          24h: {p.sold_delta_24h != null ? formatSignedNumber(p.sold_delta_24h) : "—"}
                        </div>
                        <div className="text-[11px] text-cyan-400 mt-0.5">
                          7d: {p.sold_delta_7d != null ? formatSignedNumber(p.sold_delta_7d) : "—"}
                        </div>
                      </td>
                    ))}
                  </tr>

                  {/* Row 10: Review Delta 24h & 7d */}
                  <tr className="border-b border-slate-800/60 bg-slate-900/20">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Chênh lệch đánh giá (24h / 7d)
                    </td>
                    {data.products.map((p) => (
                      <td key={p.product_id} className="p-3">
                        <div className="text-slate-300">
                          24h: {p.review_delta_24h != null ? formatSignedNumber(p.review_delta_24h) : "—"}
                        </div>
                        <div className="text-[11px] text-slate-400 mt-0.5">
                          7d: {p.review_delta_7d != null ? formatSignedNumber(p.review_delta_7d) : "—"}
                        </div>
                      </td>
                    ))}
                  </tr>

                  {/* Row 11: Freshness Age */}
                  <tr className="border-b border-slate-800/60">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Độ tươi mới (Freshness)
                    </td>
                    {data.products.map((p) => (
                      <td key={p.product_id} className="p-3 text-slate-300">
                        {p.freshness_hours != null ? `${p.freshness_hours.toFixed(1)} giờ trước` : "—"}
                      </td>
                    ))}
                  </tr>

                  {/* Row 12: Bounded 7d Alert Summary */}
                  <tr className="border-b border-slate-800 bg-slate-900/30">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Cảnh báo 7 ngày qua
                    </td>
                    {data.products.map((p) => (
                      <td key={p.product_id} className="p-3">
                        <div className="flex items-center gap-1.5">
                          <Bell className={`h-3.5 w-3.5 ${p.recent_alert_count_7d > 0 ? "text-amber-400" : "text-slate-500"}`} />
                          <span className="font-semibold text-slate-200">
                            {p.recent_alert_count_7d} cảnh báo
                          </span>
                        </div>
                        {p.latest_alert_at && (
                          <div className="text-[10px] text-slate-400 mt-0.5">
                            Gần nhất: {formatDate(p.latest_alert_at)}
                          </div>
                        )}
                      </td>
                    ))}
                  </tr>

                  {/* Section Divider: Economics Header */}
                  <tr className="border-b border-slate-800 bg-slate-950">
                    <td colSpan={data.products.length + 1} className="py-2.5 px-3">
                      <div className="flex items-center gap-2 text-xs font-bold text-rose-400">
                        <Calculator className="h-4 w-4" />
                        <span>Kinh tế Affiliate (Kịch bản mặc định)</span>
                      </div>
                    </td>
                  </tr>

                  {/* Row 13: Scenario Name */}
                  <tr className="border-b border-slate-800/60">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Kịch bản mặc định
                    </td>
                    {data.products.map((p) => (
                      <td key={p.product_id} className="p-3 text-slate-200 font-medium">
                        {p.default_economics ? (
                          <span className="inline-flex items-center gap-1">
                            <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                            <span>{p.default_economics.name}</span>
                          </span>
                        ) : (
                          <span className="text-slate-500">—</span>
                        )}
                      </td>
                    ))}
                  </tr>

                  {/* Row 14: Commission Rate */}
                  <tr className="border-b border-slate-800/60 bg-slate-900/20">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Tỷ lệ hoa hồng
                    </td>
                    {data.products.map((p) => (
                      <td key={p.product_id} className="p-3 font-semibold text-rose-400">
                        {p.default_economics?.commission_rate_bps != null
                          ? `${(p.default_economics.commission_rate_bps / 100).toFixed(2)}%`
                          : "—"}
                      </td>
                    ))}
                  </tr>

                  {/* Row 15: Commission Base & Source */}
                  <tr className="border-b border-slate-800/60">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Cơ sở tính &amp; Nguồn
                    </td>
                    {data.products.map((p) => (
                      <td key={p.product_id} className="p-3">
                        {p.default_economics?.commission_base_vnd != null ? (
                          <div>
                            <div className="font-semibold text-slate-200">
                              {formatCurrency(p.default_economics.commission_base_vnd)}
                            </div>
                            <div className="text-[10px] text-slate-400 mt-0.5">
                              {p.default_economics.commission_base_source === "observed_price_proxy"
                                ? "Giá sàn quan sát"
                                : "Giả định người dùng"}
                            </div>
                          </div>
                        ) : (
                          <span className="text-slate-500">—</span>
                        )}
                      </td>
                    ))}
                  </tr>

                  {/* Row 16: Commission per Order */}
                  <tr className="border-b border-slate-800/60 bg-slate-900/20">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Hoa hồng ước tính/đơn
                    </td>
                    {data.products.map((p) => (
                      <td key={p.product_id} className="p-3 font-semibold text-emerald-400">
                        {p.default_economics?.derived?.commission_per_order_vnd != null
                          ? formatCurrency(p.default_economics.derived.commission_per_order_vnd)
                          : "—"}
                      </td>
                    ))}
                  </tr>

                  {/* Row 17: Contribution per Order */}
                  <tr className="border-b border-slate-800/60">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Lợi nhuận đóng góp/đơn
                    </td>
                    {data.products.map((p) => {
                      const contrib = p.default_economics?.derived?.contribution_per_order_vnd;
                      return (
                        <td key={p.product_id} className="p-3">
                          {contrib != null ? (
                            <span className={`font-semibold ${contrib >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                              {formatCurrency(contrib)}
                            </span>
                          ) : (
                            <span className="text-slate-500">—</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>

                  {/* Row 18: Break-even Orders */}
                  <tr className="border-b border-slate-800/60 bg-slate-900/20">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Điểm hòa vốn chiến dịch
                    </td>
                    {data.products.map((p) => (
                      <td key={p.product_id} className="p-3 font-semibold text-cyan-400">
                        {p.default_economics?.derived?.break_even_orders != null
                          ? `${formatNumber(p.default_economics.derived.break_even_orders)} đơn`
                          : "—"}
                      </td>
                    ))}
                  </tr>

                  {/* Row 19: Expected Orders & Net Profit */}
                  <tr className="border-b border-slate-800/60">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Đơn dự kiến &amp; Lợi nhuận ròng
                    </td>
                    {data.products.map((p) => {
                      const orders = p.default_economics?.expected_attributed_orders;
                      const expContrib = p.default_economics?.derived?.expected_contribution_vnd;
                      return (
                        <td key={p.product_id} className="p-3">
                          {orders != null ? (
                            <div>
                              <div className="font-semibold text-slate-200">
                                {formatNumber(orders)} đơn
                              </div>
                              <div className={`text-[11px] mt-0.5 ${expContrib != null && expContrib >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                                {expContrib != null ? formatCurrency(expContrib) : "—"}
                              </div>
                            </div>
                          ) : (
                            <span className="text-slate-500">—</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>

                  {/* Row 20: Return on Cost Ratio */}
                  <tr className="border-b border-slate-800 bg-slate-900/30">
                    <td className="p-3 font-semibold text-slate-400 bg-slate-950/40">
                      Tỷ suất lợi nhuận (Return on Cost)
                    </td>
                    {data.products.map((p) => {
                      const roc = p.default_economics?.derived?.return_on_cost_ratio;
                      return (
                        <td key={p.product_id} className="p-3 font-semibold text-amber-400">
                          {roc != null ? `${(roc * 100).toFixed(1)}%` : "—"}
                        </td>
                      );
                    })}
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 flex justify-end bg-slate-950/60">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs"
          >
            Đóng bảng so sánh
          </button>
        </div>
      </div>
    </div>
  );
};
