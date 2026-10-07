"use client";

import React, { useCallback, useEffect, useState } from "react";
import { EconomicsScenario, EconomicsScenarioCreate, EconomicsScenarioUpdate } from "@/types";
import {
  fetchProductEconomicsScenarios,
  createEconomicsScenario,
  updateEconomicsScenario,
  deleteEconomicsScenario,
  setDefaultEconomicsScenario,
  duplicateEconomicsScenario,
  rebasePriceEconomicsScenario,
} from "@/lib/api";
import { formatCurrency, formatNumber, formatDate } from "@/lib/utils";
import {
  Calculator,
  Plus,
  Copy,
  Edit2,
  Trash2,
  Star,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  Coins,
  Receipt,
  Scale,
  Sparkles,
  Info,
} from "lucide-react";

interface ProductEconomicsSectionProps {
  productId: number;
  productTitle: string;
  latestPriceVnd?: number | null;
}

export const ProductEconomicsSection: React.FC<ProductEconomicsSectionProps> = ({
  productId,
  productTitle,
  latestPriceVnd,
}) => {
  const [scenarios, setScenarios] = useState<EconomicsScenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Modal states
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDuplicateOpen, setIsDuplicateOpen] = useState(false);

  // Form states
  const [formName, setFormName] = useState("");
  const [formCommissionPct, setFormCommissionPct] = useState<string>("");
  const [formCommissionBase, setFormCommissionBase] = useState<string>("");
  const [formUseObservedPrice, setFormUseObservedPrice] = useState(false);
  const [formSampleCost, setFormSampleCost] = useState<string>("");
  const [formContentCost, setFormContentCost] = useState<string>("");
  const [formPromotionCost, setFormPromotionCost] = useState<string>("");
  const [formVariableCost, setFormVariableCost] = useState<string>("");
  const [formExpectedOrders, setFormExpectedOrders] = useState<string>("");
  const [duplicateName, setDuplicateName] = useState("");

  const loadScenarios = useCallback(async () => {
    setLoading(true);
    setError(null);
    let active = true;
    try {
      const data = await fetchProductEconomicsScenarios(productId);
      if (active) {
        setScenarios(data);
        setSelectedScenarioId((prev) => {
          if (prev && data.some((s) => s.id === prev)) return prev;
          const def = data.find((s) => s.is_default);
          return def ? def.id : data.length > 0 ? data[0].id : null;
        });
      }
    } catch (err: any) {
      if (active) setError(err.message || "Không thể tải kịch bản kinh tế");
    } finally {
      if (active) setLoading(false);
    }
    return () => {
      active = false;
    };
  }, [productId]);

  useEffect(() => {
    loadScenarios();
  }, [loadScenarios]);

  const activeScenario = scenarios.find((s) => s.id === selectedScenarioId) || null;

  // Clear notifications after timeout
  useEffect(() => {
    if (actionSuccess || actionError) {
      const t = setTimeout(() => {
        setActionSuccess(null);
        setActionError(null);
      }, 4000);
      return () => clearTimeout(t);
    }
  }, [actionSuccess, actionError]);

  const resetForm = () => {
    setFormName("");
    setFormCommissionPct("");
    setFormCommissionBase("");
    setFormUseObservedPrice(false);
    setFormSampleCost("");
    setFormContentCost("");
    setFormPromotionCost("");
    setFormVariableCost("");
    setFormExpectedOrders("");
  };

  const openCreateModal = () => {
    resetForm();
    if (scenarios.length === 0) {
      setFormName("Kịch bản mặc định");
    } else {
      setFormName(`Kịch bản ${scenarios.length + 1}`);
    }
    setFormUseObservedPrice(!!latestPriceVnd);
    if (!latestPriceVnd) {
      setFormCommissionBase("");
    }
    setIsCreateOpen(true);
  };

  const openEditModal = () => {
    if (!activeScenario) return;
    setFormName(activeScenario.name);
    setFormCommissionPct(
      activeScenario.commission_rate_bps !== null
        ? (activeScenario.commission_rate_bps / 100).toString()
        : ""
    );
    setFormCommissionBase(
      activeScenario.commission_base_vnd !== null
        ? activeScenario.commission_base_vnd.toString()
        : ""
    );
    setFormUseObservedPrice(activeScenario.commission_base_source === "observed_price_proxy");
    setFormSampleCost(
      activeScenario.sample_cost_vnd !== null ? activeScenario.sample_cost_vnd.toString() : ""
    );
    setFormContentCost(
      activeScenario.content_cost_vnd !== null ? activeScenario.content_cost_vnd.toString() : ""
    );
    setFormPromotionCost(
      activeScenario.promotion_cost_vnd !== null ? activeScenario.promotion_cost_vnd.toString() : ""
    );
    setFormVariableCost(
      activeScenario.variable_cost_per_attributed_order_vnd !== null
        ? activeScenario.variable_cost_per_attributed_order_vnd.toString()
        : ""
    );
    setFormExpectedOrders(
      activeScenario.expected_attributed_orders !== null
        ? activeScenario.expected_attributed_orders.toString()
        : ""
    );
    setIsEditOpen(true);
  };

  const openDuplicateModal = () => {
    if (!activeScenario) return;
    setDuplicateName(`${activeScenario.name} (Bản sao)`);
    setIsDuplicateOpen(true);
  };

  // Convert percentage string to basis points and validate whole bps
  const parseCommissionRateBps = (pctStr: string): number | null => {
    if (!pctStr.trim()) return null;
    const num = parseFloat(pctStr.trim());
    if (isNaN(num) || num < 0 || num > 100) {
      throw new Error("Tỷ lệ hoa hồng phải từ 0% đến 100%");
    }
    const bps = Math.round(num * 100);
    // Reject fractional basis points (more than 2 decimal places in %)
    if (Math.abs(num * 100 - bps) > 1e-4) {
      throw new Error("Tỷ lệ hoa hồng không được chứa phần thập phân nhỏ hơn 0.01% (1 bps)");
    }
    return bps;
  };

  const parseMoneyVnd = (valStr: string, fieldName: string): number | null => {
    if (!valStr.trim()) return null;
    const num = parseInt(valStr.trim(), 10);
    if (isNaN(num) || num < 0) {
      throw new Error(`${fieldName} phải là số nguyên không âm (VND)`);
    }
    if (num > 100_000_000_000) {
      throw new Error(`${fieldName} không được vượt quá 100 tỷ VND`);
    }
    return num;
  };

  const parseOrders = (valStr: string): number | null => {
    if (!valStr.trim()) return null;
    const num = parseInt(valStr.trim(), 10);
    if (isNaN(num) || num < 0) {
      throw new Error("Số đơn dự kiến phải là số nguyên không âm");
    }
    if (num > 1_000_000) {
      throw new Error("Số đơn dự kiến không được vượt quá 1.000.000 đơn");
    }
    return num;
  };

  const handleCreateScenario = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionError(null);
    try {
      if (!formName.trim()) throw new Error("Tên kịch bản không được để trống");
      const bps = parseCommissionRateBps(formCommissionPct);
      const sampleCost = parseMoneyVnd(formSampleCost, "Chi phí mẫu");
      const contentCost = parseMoneyVnd(formContentCost, "Chi phí nội dung");
      const promotionCost = parseMoneyVnd(formPromotionCost, "Chi phí quảng bá");
      const variableCost = parseMoneyVnd(formVariableCost, "Chi phí biến đổi trên đơn");
      const expectedOrders = parseOrders(formExpectedOrders);

      const payload: EconomicsScenarioCreate = {
        name: formName.trim(),
        commission_rate_bps: bps,
        sample_cost_vnd: sampleCost,
        content_cost_vnd: contentCost,
        promotion_cost_vnd: promotionCost,
        variable_cost_per_attributed_order_vnd: variableCost,
        expected_attributed_orders: expectedOrders,
      };

      if (formUseObservedPrice) {
        payload.use_observed_price = true;
      } else {
        payload.use_observed_price = false;
        payload.commission_base_vnd = parseMoneyVnd(formCommissionBase, "Cơ sở tính hoa hồng");
      }

      const created = await createEconomicsScenario(productId, payload);
      setScenarios((prev) => [...prev, created]);
      setSelectedScenarioId(created.id);
      setIsCreateOpen(false);
      setActionSuccess(`Đã tạo kịch bản "${created.name}" thành công`);
    } catch (err: any) {
      setActionError(err.message || "Lỗi khi tạo kịch bản kinh tế");
    }
  };

  const handleUpdateScenario = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeScenario) return;
    setActionError(null);
    try {
      if (!formName.trim()) throw new Error("Tên kịch bản không được để trống");
      const bps = parseCommissionRateBps(formCommissionPct);
      const baseVnd = parseMoneyVnd(formCommissionBase, "Cơ sở tính hoa hồng");
      const sampleCost = parseMoneyVnd(formSampleCost, "Chi phí mẫu");
      const contentCost = parseMoneyVnd(formContentCost, "Chi phí nội dung");
      const promotionCost = parseMoneyVnd(formPromotionCost, "Chi phí quảng bá");
      const variableCost = parseMoneyVnd(formVariableCost, "Chi phí biến đổi trên đơn");
      const expectedOrders = parseOrders(formExpectedOrders);

      const payload: EconomicsScenarioUpdate = {
        name: formName.trim(),
        commission_rate_bps: bps,
        commission_base_vnd: baseVnd,
        sample_cost_vnd: sampleCost,
        content_cost_vnd: contentCost,
        promotion_cost_vnd: promotionCost,
        variable_cost_per_attributed_order_vnd: variableCost,
        expected_attributed_orders: expectedOrders,
      };

      const updated = await updateEconomicsScenario(productId, activeScenario.id, payload);
      setScenarios((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
      setIsEditOpen(false);
      setActionSuccess(`Đã cập nhật kịch bản "${updated.name}" thành công`);
    } catch (err: any) {
      setActionError(err.message || "Lỗi khi cập nhật kịch bản kinh tế");
    }
  };

  const handleDeleteScenario = async () => {
    if (!activeScenario) return;
    if (!confirm(`Bạn có chắc muốn xóa kịch bản "${activeScenario.name}"?`)) return;
    setActionError(null);
    try {
      await deleteEconomicsScenario(productId, activeScenario.id);
      setActionSuccess(`Đã xóa kịch bản "${activeScenario.name}"`);
      // Reload scenarios to reflect atomic promotion if default was deleted
      const updatedList = await fetchProductEconomicsScenarios(productId);
      setScenarios(updatedList);
      const def = updatedList.find((s) => s.is_default);
      setSelectedScenarioId(def ? def.id : updatedList.length > 0 ? updatedList[0].id : null);
    } catch (err: any) {
      setActionError(err.message || "Lỗi khi xóa kịch bản kinh tế");
    }
  };

  const handleSetDefault = async () => {
    if (!activeScenario || activeScenario.is_default) return;
    setActionError(null);
    try {
      const updated = await setDefaultEconomicsScenario(productId, activeScenario.id);
      setScenarios((prev) =>
        prev.map((s) => ({
          ...s,
          is_default: s.id === updated.id,
        }))
      );
      setActionSuccess(`Đã đặt "${updated.name}" làm kịch bản mặc định`);
    } catch (err: any) {
      setActionError(err.message || "Lỗi khi đặt kịch bản mặc định");
    }
  };

  const handleDuplicate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeScenario) return;
    setActionError(null);
    try {
      if (!duplicateName.trim()) throw new Error("Tên kịch bản bản sao không được để trống");
      const cloned = await duplicateEconomicsScenario(productId, activeScenario.id, duplicateName.trim());
      setScenarios((prev) => [...prev, cloned]);
      setSelectedScenarioId(cloned.id);
      setIsDuplicateOpen(false);
      setActionSuccess(`Đã nhân bản kịch bản "${cloned.name}" thành công`);
    } catch (err: any) {
      setActionError(err.message || "Lỗi khi nhân bản kịch bản kinh tế");
    }
  };

  const handleRebasePrice = async () => {
    if (!activeScenario) return;
    setActionError(null);
    try {
      const updated = await rebasePriceEconomicsScenario(productId, activeScenario.id);
      setScenarios((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
      setActionSuccess(`Đã cập nhật lại giá thị trường quan sát cho kịch bản "${updated.name}"`);
    } catch (err: any) {
      setActionError(err.message || "Lỗi khi cập nhật lại giá quan sát");
    }
  };

  return (
    <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-6">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Calculator className="h-5 w-5 text-rose-500" />
            <h2 className="text-base font-bold text-white">
              Kế hoạch Kinh tế Affiliate &amp; Điểm Hòa vốn
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Mô phỏng bài toán kinh tế thủ công theo đơn vị VND; độc lập hoàn toàn với tín hiệu nhu cầu thị trường.
          </p>
        </div>

        <button
          onClick={openCreateModal}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-sm transition-colors self-start sm:self-auto"
        >
          <Plus className="h-4 w-4" />
          <span>Tạo kịch bản mới</span>
        </button>
      </div>

      {/* Notifications */}
      {actionSuccess && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-950/60 border border-emerald-800/80 text-emerald-400 text-xs">
          <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}
      {actionError && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-rose-950/60 border border-rose-800/80 text-rose-400 text-xs">
          <AlertTriangle className="h-4 w-4 flex-shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Commercial Disclaimer Banner */}
      <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-slate-400 text-[11px] leading-relaxed">
        <Info className="h-4 w-4 text-cyan-400 flex-shrink-0 mt-0.5" />
        <div>
          <strong className="text-slate-300">Lưu ý thương mại:</strong> Các chỉ số kinh tế là ước tính theo kịch bản giả định. Hoa hồng thực tế từ TikTok Shop có thể thay đổi phụ thuộc vào giá người mua thực trả, mã giảm giá, hoàn hàng, hủy đơn và điều kiện hợp tác cụ thể.
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="py-12 text-center text-xs text-slate-500 space-y-2">
          <RefreshCw className="h-6 w-6 animate-spin text-rose-500 mx-auto" />
          <p>Đang tải dữ liệu kịch bản kinh tế...</p>
        </div>
      ) : error ? (
        <div className="py-12 text-center space-y-3">
          <p className="text-xs text-rose-400">{error}</p>
          <button
            onClick={loadScenarios}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs"
          >
            Thử tải lại
          </button>
        </div>
      ) : scenarios.length === 0 ? (
        <div className="py-12 text-center border border-dashed border-slate-800 rounded-xl space-y-3">
          <Calculator className="h-8 w-8 text-slate-600 mx-auto" />
          <div className="text-xs text-slate-400">Sản phẩm này chưa có kịch bản kinh tế nào.</div>
          <p className="text-[11px] text-slate-500 max-w-md mx-auto">
            Hãy thiết lập kịch bản đầu tiên để tính toán hoa hồng ước tính, chi phí chiến dịch và số đơn hàng cần thiết để hòa vốn.
          </p>
          <button
            onClick={openCreateModal}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>Tạo kịch bản đầu tiên</span>
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Scenario Tabs & Action Bar */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800/60 pb-3">
            {/* Tabs */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 max-w-full">
              {scenarios.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setSelectedScenarioId(s.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors border ${
                    s.id === selectedScenarioId
                      ? "bg-slate-800 text-white border-rose-500/50 shadow-sm"
                      : "bg-slate-950/60 text-slate-400 border-slate-800 hover:text-slate-200 hover:bg-slate-800/40"
                  }`}
                >
                  {s.is_default && (
                    <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400 flex-shrink-0" />
                  )}
                  <span>{s.name}</span>
                </button>
              ))}
            </div>

            {/* Actions for Active Scenario */}
            {activeScenario && (
              <div className="flex items-center gap-1.5 flex-wrap">
                {!activeScenario.is_default && (
                  <button
                    onClick={handleSetDefault}
                    title="Đặt kịch bản này làm mặc định"
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-400 text-xs font-medium border border-slate-700 transition-colors"
                  >
                    <Star className="h-3.5 w-3.5" />
                    <span>Đặt mặc định</span>
                  </button>
                )}
                {activeScenario.commission_base_source === "observed_price_proxy" && (
                  <button
                    onClick={handleRebasePrice}
                    title="Cập nhật lại cơ sở hoa hồng theo giá quan sát mới nhất"
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-medium border border-slate-700 transition-colors"
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                    <span>Cập nhật giá sàn</span>
                  </button>
                )}
                <button
                  onClick={openDuplicateModal}
                  title="Nhân bản kịch bản"
                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
                >
                  <Copy className="h-3.5 w-3.5" />
                  <span>Nhân bản</span>
                </button>
                <button
                  onClick={openEditModal}
                  title="Chỉnh sửa tham số kịch bản"
                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
                >
                  <Edit2 className="h-3.5 w-3.5" />
                  <span>Sửa</span>
                </button>
                <button
                  onClick={handleDeleteScenario}
                  title="Xóa kịch bản"
                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 text-rose-400 text-xs font-medium border border-rose-800/60 transition-colors"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  <span>Xóa</span>
                </button>
              </div>
            )}
          </div>

          {activeScenario && (
            <div className="space-y-6">
              {/* Provenance & Assumptions Banner */}
              <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/60 pb-2.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-200">
                      {activeScenario.name}
                    </span>
                    {activeScenario.is_default && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full">
                        <Star className="h-3 w-3 fill-amber-400" /> Kịch bản mặc định
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 text-[11px]">
                    <span className="text-slate-400">Nguồn cơ sở hoa hồng:</span>
                    {activeScenario.commission_base_source === "observed_price_proxy" ? (
                      <span className="inline-flex items-center gap-1 text-cyan-400 bg-cyan-950/50 border border-cyan-800/60 px-2 py-0.5 rounded-md font-mono">
                        Giá sàn đóng băng ({formatDate(activeScenario.commission_base_observed_at)})
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-slate-300 bg-slate-800/60 border border-slate-700/60 px-2 py-0.5 rounded-md">
                        Giả định người dùng
                      </span>
                    )}
                  </div>
                </div>

                {/* Grid of Key Inputs */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
                    <div className="text-[11px] text-slate-400">Tỷ lệ hoa hồng</div>
                    <div className="font-semibold text-rose-400 text-sm mt-0.5">
                      {activeScenario.commission_rate_bps !== null
                        ? `${(activeScenario.commission_rate_bps / 100).toFixed(2)}%`
                        : "—"}
                    </div>
                  </div>

                  <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
                    <div className="text-[11px] text-slate-400">Cơ sở tính hoa hồng</div>
                    <div className="font-semibold text-slate-200 text-sm mt-0.5">
                      {activeScenario.commission_base_vnd !== null
                        ? formatCurrency(activeScenario.commission_base_vnd)
                        : "—"}
                    </div>
                  </div>

                  <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
                    <div className="text-[11px] text-slate-400">Chi phí cố định chiến dịch</div>
                    <div className="font-semibold text-slate-200 text-sm mt-0.5">
                      {activeScenario.derived.fixed_campaign_cost_vnd !== null
                        ? formatCurrency(activeScenario.derived.fixed_campaign_cost_vnd)
                        : "—"}
                    </div>
                  </div>

                  <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
                    <div className="text-[11px] text-slate-400">Chi phí biến đổi/đơn</div>
                    <div className="font-semibold text-slate-200 text-sm mt-0.5">
                      {activeScenario.variable_cost_per_attributed_order_vnd !== null
                        ? formatCurrency(activeScenario.variable_cost_per_attributed_order_vnd)
                        : "—"}
                    </div>
                  </div>
                </div>
              </div>

              {/* Core Economics Metric Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* 1. Unit Economics */}
                <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 space-y-3">
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-300">
                    <Coins className="h-4 w-4 text-emerald-400" />
                    <span>Kinh tế Đơn vị (Unit Economics)</span>
                  </div>

                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                      <span className="text-slate-400">Hoa hồng ước tính/đơn:</span>
                      <span className="font-semibold text-emerald-400">
                        {activeScenario.derived.commission_per_order_vnd !== null
                          ? formatCurrency(activeScenario.derived.commission_per_order_vnd)
                          : "—"}
                      </span>
                    </div>

                    <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                      <span className="text-slate-400">Chi phí biến đổi/đơn:</span>
                      <span className="font-semibold text-slate-300">
                        {activeScenario.variable_cost_per_attributed_order_vnd !== null
                          ? formatCurrency(activeScenario.variable_cost_per_attributed_order_vnd)
                          : "—"}
                      </span>
                    </div>

                    <div className="flex justify-between items-center pt-1">
                      <span className="font-semibold text-slate-200">Lợi nhuận đóng góp/đơn:</span>
                      <span
                        className={`font-bold text-sm ${
                          activeScenario.derived.contribution_per_order_vnd !== null
                            ? activeScenario.derived.contribution_per_order_vnd >= 0
                              ? "text-emerald-400"
                              : "text-rose-400"
                            : "text-slate-500"
                        }`}
                      >
                        {activeScenario.derived.contribution_per_order_vnd !== null
                          ? formatCurrency(activeScenario.derived.contribution_per_order_vnd)
                          : "—"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* 2. Break-Even Analysis */}
                <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 space-y-3">
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-300">
                    <Scale className="h-4 w-4 text-cyan-400" />
                    <span>Điểm Hòa Vốn Chiến Dịch</span>
                  </div>

                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                      <span className="text-slate-400">Tổng chi phí cố định:</span>
                      <span className="font-semibold text-slate-300">
                        {activeScenario.derived.fixed_campaign_cost_vnd !== null
                          ? formatCurrency(activeScenario.derived.fixed_campaign_cost_vnd)
                          : "—"}
                      </span>
                    </div>

                    <div className="flex justify-between items-center pt-1">
                      <span className="font-semibold text-slate-200">Đơn hàng cần để hòa vốn:</span>
                      <span className="font-bold text-sm text-cyan-400">
                        {activeScenario.derived.break_even_orders !== null ? (
                          `${formatNumber(activeScenario.derived.break_even_orders)} đơn`
                        ) : activeScenario.derived.contribution_per_order_vnd !== null &&
                          activeScenario.derived.contribution_per_order_vnd <= 0 ? (
                          <span className="text-rose-400 text-xs font-normal">Không thể hòa vốn (Đóng góp ≤ 0)</span>
                        ) : (
                          "—"
                        )}
                      </span>
                    </div>

                    <p className="text-[10px] text-slate-500 pt-1 leading-normal">
                      Bao gồm chi phí sản phẩm mẫu, chi phí quay dựng nội dung và chi phí quảng bá.
                    </p>
                  </div>
                </div>

                {/* 3. Campaign Projections (if orders provided) */}
                <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 space-y-3">
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-300">
                    <TrendingUp className="h-4 w-4 text-amber-400" />
                    <span>Dự phóng Chiến dịch</span>
                  </div>

                  {activeScenario.expected_attributed_orders !== null ? (
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                        <span className="text-slate-400">Số đơn dự kiến:</span>
                        <span className="font-semibold text-slate-200">
                          {formatNumber(activeScenario.expected_attributed_orders)} đơn
                        </span>
                      </div>

                      <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                        <span className="text-slate-400">Doanh thu hoa hồng dự kiến:</span>
                        <span className="font-semibold text-emerald-400">
                          {activeScenario.derived.expected_commission_vnd !== null
                            ? formatCurrency(activeScenario.derived.expected_commission_vnd)
                            : "—"}
                        </span>
                      </div>

                      <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                        <span className="font-semibold text-slate-200">Lợi nhuận ròng dự kiến:</span>
                        <span
                          className={`font-bold text-sm ${
                            activeScenario.derived.expected_contribution_vnd !== null
                              ? activeScenario.derived.expected_contribution_vnd >= 0
                                ? "text-emerald-400"
                                : "text-rose-400"
                              : "text-slate-500"
                          }`}
                        >
                          {activeScenario.derived.expected_contribution_vnd !== null
                            ? formatCurrency(activeScenario.derived.expected_contribution_vnd)
                            : "—"}
                        </span>
                      </div>

                      <div className="flex justify-between items-center pt-1">
                        <span className="text-slate-400">Tỷ suất lợi nhuận (Return on Cost):</span>
                        <span className="font-bold text-amber-400">
                          {activeScenario.derived.return_on_cost_ratio !== null
                            ? `${(activeScenario.derived.return_on_cost_ratio * 100).toFixed(1)}%`
                            : "—"}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="py-4 text-center text-xs text-slate-500 space-y-2">
                      <p>Chưa nhập số đơn hàng dự kiến.</p>
                      <button
                        onClick={openEditModal}
                        className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]"
                      >
                        Thêm số đơn dự kiến
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* CREATE SCENARIO MODAL */}
      {isCreateOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base">Tạo Kịch bản Kinh tế Mới</h3>
              <button
                onClick={() => setIsCreateOpen(false)}
                className="text-slate-400 hover:text-white text-xs font-semibold"
              >
                Đóng
              </button>
            </div>

            <form onSubmit={handleCreateScenario} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Tên kịch bản <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ví dụ: Kịch bản tiêu chuẩn, Hợp tác độc quyền..."
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-rose-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Tỷ lệ hoa hồng (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="100"
                    placeholder="Ví dụ: 12.5"
                    value={formCommissionPct}
                    onChange={(e) => setFormCommissionPct(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-rose-500 font-mono"
                  />
                  <span className="text-[10px] text-slate-500 mt-0.5 block">Tối đa 2 số thập phân (1 bps = 0.01%)</span>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Nguồn cơ sở tính hoa hồng
                  </label>
                  <label className="flex items-center gap-2 p-2 rounded-lg bg-slate-950 border border-slate-800 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formUseObservedPrice}
                      onChange={(e) => setFormUseObservedPrice(e.target.checked)}
                      className="rounded border-slate-700 text-rose-500 focus:ring-0"
                    />
                    <span className="text-slate-300 text-[11px]">Dùng giá thị trường hiện tại</span>
                  </label>
                </div>
              </div>

              {!formUseObservedPrice && (
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Cơ sở tính hoa hồng (VND)
                  </label>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    placeholder="Ví dụ: 250000"
                    value={formCommissionBase}
                    onChange={(e) => setFormCommissionBase(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-rose-500 font-mono"
                  />
                </div>
              )}

              <div className="border-t border-slate-800 pt-3">
                <span className="text-slate-400 font-semibold block mb-2">Chi phí cố định chiến dịch (VND)</span>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <div>
                    <label className="block text-slate-400 text-[11px] mb-1">Chi phí mẫu</label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      placeholder="0"
                      value={formSampleCost}
                      onChange={(e) => setFormSampleCost(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-100 focus:outline-none focus:border-rose-500 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 text-[11px] mb-1">Sản xuất nội dung</label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      placeholder="0"
                      value={formContentCost}
                      onChange={(e) => setFormContentCost(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-100 focus:outline-none focus:border-rose-500 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 text-[11px] mb-1">Quảng bá / Ads</label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      placeholder="0"
                      value={formPromotionCost}
                      onChange={(e) => setFormPromotionCost(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-100 focus:outline-none focus:border-rose-500 font-mono"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 border-t border-slate-800 pt-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Chi phí biến đổi / đơn (VND)
                  </label>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    placeholder="Ví dụ: bao bì, ship mẫu..."
                    value={formVariableCost}
                    onChange={(e) => setFormVariableCost(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-rose-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Số đơn dự kiến (tùy chọn)
                  </label>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    placeholder="Ví dụ: 100"
                    value={formExpectedOrders}
                    onChange={(e) => setFormExpectedOrders(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-rose-500 font-mono"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs"
                >
                  Lưu kịch bản
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EDIT SCENARIO MODAL */}
      {isEditOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base">Chỉnh Sửa Kịch bản Kinh tế</h3>
              <button
                onClick={() => setIsEditOpen(false)}
                className="text-slate-400 hover:text-white text-xs font-semibold"
              >
                Đóng
              </button>
            </div>

            <form onSubmit={handleUpdateScenario} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Tên kịch bản <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-rose-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Tỷ lệ hoa hồng (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="100"
                    value={formCommissionPct}
                    onChange={(e) => setFormCommissionPct(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-rose-500 font-mono"
                  />
                  <span className="text-[10px] text-slate-500 mt-0.5 block">Tối đa 2 số thập phân (1 bps = 0.01%)</span>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Cơ sở tính hoa hồng (VND)
                  </label>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    value={formCommissionBase}
                    onChange={(e) => setFormCommissionBase(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-rose-500 font-mono"
                  />
                  <span className="text-[10px] text-slate-500 mt-0.5 block">Nhập tay sẽ chuyển nguồn sang &quot;Giả định người dùng&quot;</span>
                </div>
              </div>

              <div className="border-t border-slate-800 pt-3">
                <span className="text-slate-400 font-semibold block mb-2">Chi phí cố định chiến dịch (VND)</span>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <div>
                    <label className="block text-slate-400 text-[11px] mb-1">Chi phí mẫu</label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      value={formSampleCost}
                      onChange={(e) => setFormSampleCost(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-100 focus:outline-none focus:border-rose-500 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 text-[11px] mb-1">Sản xuất nội dung</label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      value={formContentCost}
                      onChange={(e) => setFormContentCost(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-100 focus:outline-none focus:border-rose-500 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 text-[11px] mb-1">Quảng bá / Ads</label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      value={formPromotionCost}
                      onChange={(e) => setFormPromotionCost(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-100 focus:outline-none focus:border-rose-500 font-mono"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 border-t border-slate-800 pt-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Chi phí biến đổi / đơn (VND)
                  </label>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    value={formVariableCost}
                    onChange={(e) => setFormVariableCost(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-rose-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Số đơn dự kiến (tùy chọn)
                  </label>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    value={formExpectedOrders}
                    onChange={(e) => setFormExpectedOrders(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-rose-500 font-mono"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsEditOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs"
                >
                  Cập nhật kịch bản
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DUPLICATE MODAL */}
      {isDuplicateOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base">Nhân Bản Kịch bản</h3>
              <button
                onClick={() => setIsDuplicateOpen(false)}
                className="text-slate-400 hover:text-white text-xs font-semibold"
              >
                Đóng
              </button>
            </div>

            <form onSubmit={handleDuplicate} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Tên kịch bản mới <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={duplicateName}
                  onChange={(e) => setDuplicateName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-rose-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsDuplicateOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs"
                >
                  Tạo bản sao
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
