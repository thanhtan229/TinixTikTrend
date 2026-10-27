"use client";

import React, { useCallback, useEffect, useState } from "react";
import { AlertRule, AlertRuleCreate } from "@/types";
import { fetchAlertRules, createAlertRule, updateAlertRule, deleteAlertRule } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { X, Bell, Plus, Trash2, Power, AlertTriangle, CheckCircle, TrendingUp, Flame, Percent } from "lucide-react";

interface AlertRuleModalProps {
  productId: number;
  productTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

export const AlertRuleModal: React.FC<AlertRuleModalProps> = ({
  productId,
  productTitle,
  isOpen,
  onClose,
}) => {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // New rule form state
  const [ruleType, setRuleType] = useState<"sales_velocity_above" | "trend_score_above" | "price_change_pct">("sales_velocity_above");
  const [threshold, setThreshold] = useState<string>("50");
  const [direction, setDirection] = useState<"either" | "up" | "down">("either");
  const [cooldownMinutes, setCooldownMinutes] = useState<string>("0");

  const loadRules = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAlertRules(productId);
      setRules(data);
    } catch (err: any) {
      setError(err.message || "Không thể tải danh sách luật cảnh báo");
    } finally {
      setLoading(false);
    }
  }, [productId]);

  useEffect(() => {
    if (isOpen) {
      loadRules();
      setError(null);
      setSuccessMessage(null);
    }
  }, [isOpen, loadRules]);

  // Handle ESC key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    const threshNum = parseFloat(threshold);
    if (isNaN(threshNum) || threshNum <= 0) {
      setError("Ngưỡng giá trị phải là số lớn hơn 0");
      return;
    }

    const cooldownNum = parseInt(cooldownMinutes, 10);
    if (isNaN(cooldownNum) || cooldownNum < 0) {
      setError("Thời gian cooldown phải lớn hơn hoặc bằng 0");
      return;
    }

    const payload: AlertRuleCreate = {
      product_id: productId,
      rule_type: ruleType,
      threshold: threshNum,
      direction: ruleType === "price_change_pct" ? direction : undefined,
      cooldown_minutes: cooldownNum,
      is_active: true,
    };

    setSubmitting(true);
    try {
      await createAlertRule(payload);
      setSuccessMessage("Tạo quy tắc cảnh báo thành công!");
      await loadRules();
      // Reset defaults
      if (ruleType === "sales_velocity_above") setThreshold("50");
      else if (ruleType === "trend_score_above") setThreshold("70");
      else setThreshold("10");
    } catch (err: any) {
      setError(err.message || "Tạo quy tắc cảnh báo thất bại");
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleActive = async (rule: AlertRule) => {
    setError(null);
    try {
      await updateAlertRule(rule.id, { is_active: !rule.is_active });
      await loadRules();
    } catch (err: any) {
      setError(err.message || "Không thể cập nhật trạng thái quy tắc");
    }
  };

  const handleDeleteRule = async (ruleId: number) => {
    if (!confirm("Bạn có chắc chắn muốn xóa quy tắc cảnh báo này?")) return;
    setError(null);
    try {
      await deleteAlertRule(ruleId);
      await loadRules();
    } catch (err: any) {
      setError(err.message || "Không thể xóa quy tắc cảnh báo");
    }
  };

  const getRuleTypeBadge = (type: string) => {
    switch (type) {
      case "sales_velocity_above":
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <TrendingUp className="h-3 w-3" /> Tốc độ bán
          </span>
        );
      case "trend_score_above":
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <Flame className="h-3 w-3" /> Điểm xu hướng
          </span>
        );
      case "price_change_pct":
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Percent className="h-3 w-3" /> Biến động giá
          </span>
        );
      default:
        return <span>{type}</span>;
    }
  };

  const formatRuleCondition = (rule: AlertRule) => {
    if (rule.rule_type === "sales_velocity_above") {
      return `Tốc độ bán vượt ${rule.threshold} đơn/ngày`;
    }
    if (rule.rule_type === "trend_score_above") {
      return `Điểm xu hướng vượt ${rule.threshold} điểm`;
    }
    if (rule.rule_type === "price_change_pct") {
      const dirText =
        rule.direction === "up"
          ? "Tăng giá ≥"
          : rule.direction === "down"
          ? "Giảm giá ≥"
          : "Biến động (tăng/giảm) ≥";
      return `${dirText} ${rule.threshold}%`;
    }
    return `Ngưỡng: ${rule.threshold}`;
  };

  return (
    <div
      role="presentation"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="alert-rules-modal-title"
        className="relative w-full max-w-2xl rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl p-6 space-y-6 max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400">
              <Bell className="h-5 w-5" />
            </div>
            <div>
              <h2 id="alert-rules-modal-title" className="text-lg font-bold text-white">
                Thiết lập Cảnh báo Sản phẩm
              </h2>
              <p className="text-xs text-slate-400 line-clamp-1 max-w-md mt-0.5">
                {productTitle}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Đóng cửa sổ"
            className="p-1.5 rounded-lg border border-slate-800 bg-slate-950 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Alerts & Feedback messages */}
        {error && (
          <div role="alert" className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {successMessage && (
          <div role="status" className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle className="h-4 w-4 flex-shrink-0" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Existing Rules List */}
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
            Quy tắc hiện tại ({rules.length})
          </h3>

          {loading ? (
            <div className="py-6 text-center text-xs text-slate-500">Đang tải quy tắc...</div>
          ) : rules.length === 0 ? (
            <div className="p-4 rounded-xl border border-dashed border-slate-800 bg-slate-950/40 text-center text-xs text-slate-500">
              Chưa có quy tắc cảnh báo nào cho sản phẩm này. Hãy tạo quy tắc mới bên dưới.
            </div>
          ) : (
            <div className="space-y-2.5">
              {rules.map((rule) => (
                <div
                  key={rule.id}
                  className={`p-3.5 rounded-xl border transition-all flex items-center justify-between gap-3 ${
                    rule.is_active
                      ? "bg-slate-950/60 border-slate-800"
                      : "bg-slate-950/20 border-slate-800/40 opacity-60"
                  }`}
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      {getRuleTypeBadge(rule.rule_type)}
                      <span className="text-xs font-semibold text-slate-200">
                        {formatRuleCondition(rule)}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 flex items-center gap-3">
                      <span>Cooldown: {rule.cooldown_minutes} phút</span>
                      <span>•</span>
                      <span>
                        Kích hoạt lần cuối:{" "}
                        {rule.last_triggered_at ? formatDate(rule.last_triggered_at) : "Chưa có"}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      type="button"
                      onClick={() => handleToggleActive(rule)}
                      aria-label={rule.is_active ? "Tạm dừng quy tắc" : "Kích hoạt quy tắc"}
                      title={rule.is_active ? "Đang bật (bấm để tắt)" : "Đang tắt (bấm để bật)"}
                      className={`p-1.5 rounded-lg border text-xs font-medium transition-colors ${
                        rule.is_active
                          ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20"
                          : "bg-slate-800 border-slate-700 text-slate-400 hover:text-white"
                      }`}
                    >
                      <Power className="h-3.5 w-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteRule(rule.id)}
                      aria-label="Xóa quy tắc cảnh báo"
                      className="p-1.5 rounded-lg border border-slate-800 bg-slate-950 text-slate-400 hover:text-rose-400 hover:border-rose-500/40 hover:bg-rose-500/10 transition-colors"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Add Rule Form */}
        <form onSubmit={handleCreateRule} noValidate className="pt-4 border-t border-slate-800 space-y-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Thêm quy tắc cảnh báo mới
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="alert-rule-type" className="block text-xs text-slate-300 font-medium mb-1.5">
                Loại cảnh báo:
              </label>
              <select
                id="alert-rule-type"
                value={ruleType}
                onChange={(e) => {
                  const val = e.target.value as any;
                  setRuleType(val);
                  if (val === "sales_velocity_above") setThreshold("50");
                  else if (val === "trend_score_above") setThreshold("70");
                  else if (val === "price_change_pct") setThreshold("10");
                }}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-rose-500"
              >
                <option value="sales_velocity_above">Tốc độ bán vượt ngưỡng (đơn/ngày)</option>
                <option value="trend_score_above">Điểm xu hướng vượt ngưỡng (0-100)</option>
                <option value="price_change_pct">Biến động giá (%)</option>
              </select>
            </div>

            {ruleType === "price_change_pct" ? (
              <div>
                <label htmlFor="alert-rule-direction" className="block text-xs text-slate-300 font-medium mb-1.5">
                  Chiều biến động giá:
                </label>
                <select
                  id="alert-rule-direction"
                  value={direction}
                  onChange={(e) => setDirection(e.target.value as any)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-rose-500"
                >
                  <option value="either">Cả 2 chiều (± Thay đổi tăng hoặc giảm)</option>
                  <option value="up">Tăng giá (≥)</option>
                  <option value="down">Giảm giá (≥)</option>
                </select>
              </div>
            ) : (
              <div>
                <label htmlFor="alert-rule-unit" className="block text-xs text-slate-300 font-medium mb-1.5">
                  Đơn vị tính:
                </label>
                <input
                  id="alert-rule-unit"
                  type="text"
                  disabled
                  value={ruleType === "sales_velocity_above" ? "đơn / ngày" : "điểm (thang 100)"}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950/50 border border-slate-800 text-xs text-slate-400 cursor-not-allowed"
                />
              </div>
            )}

            <div>
              <label htmlFor="alert-rule-threshold" className="block text-xs text-slate-300 font-medium mb-1.5">
                Ngưỡng kích hoạt ({ruleType === "price_change_pct" ? "%" : ruleType === "sales_velocity_above" ? "đơn/ngày" : "điểm"}):
              </label>
              <input
                id="alert-rule-threshold"
                type="number"
                step="any"
                min="0.01"
                required
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
                placeholder="Ví dụ: 50"
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-rose-500"
              />
            </div>

            <div>
              <label htmlFor="alert-rule-cooldown" className="block text-xs text-slate-300 font-medium mb-1.5">
                Thời gian chờ giãn cách (Cooldown phút):
              </label>
              <input
                id="alert-rule-cooldown"
                type="number"
                min="0"
                step="1"
                required
                value={cooldownMinutes}
                onChange={(e) => setCooldownMinutes(e.target.value)}
                placeholder="0"
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-rose-500"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">
                0 = cảnh báo mỗi khi có snapshot mới vượt ngưỡng.
              </span>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-xs font-semibold text-white transition-colors disabled:opacity-60"
            >
              <Plus className="h-4 w-4" />
              <span>{submitting ? "Đang lưu..." : "Thêm quy tắc"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
