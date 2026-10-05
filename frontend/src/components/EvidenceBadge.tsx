"use client";

import React from "react";
import { TrendEvidence } from "@/types";
import { ShieldCheck, ShieldAlert, Shield, Clock } from "lucide-react";

interface EvidenceBadgeProps {
  evidence?: TrendEvidence | null;
  size?: "sm" | "md";
}

export const EvidenceBadge: React.FC<EvidenceBadgeProps> = ({ evidence, size = "md" }) => {
  if (!evidence) return null;

  const { confidence, ranking_state, observation_count, observation_span_hours, latest_observation_age_hours, primary_signal_interval } = evidence;

  // Render specific state when stale or insufficient
  if (ranking_state === "stale") {
    return (
      <span
        title={`Dữ liệu cũ: quan sát gần nhất cách đây ${latest_observation_age_hours}h (> 8h). Cần quét lại để cập nhật.`}
        className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30"
      >
        <Clock className="h-3 w-3" />
        <span>Dữ liệu cũ ({latest_observation_age_hours}h)</span>
      </span>
    );
  }

  if (ranking_state === "insufficient_measured_signal") {
    return (
      <span
        title="Chưa có dữ liệu đo lường 2 chu kỳ để tính tốc độ thay đổi. Cần quét tiếp."
        className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-[10px] font-medium bg-slate-800 text-slate-400 border border-slate-700"
      >
        <ShieldAlert className="h-3 w-3 text-slate-500" />
        <span>Chờ thêm dữ liệu</span>
      </span>
    );
  }

  const isHigh = confidence === "high";
  const isMed = confidence === "medium";

  const colorClass = isHigh
    ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
    : isMed
    ? "bg-sky-500/15 text-sky-400 border-sky-500/30"
    : "bg-slate-800/80 text-slate-400 border-slate-700/60";

  const label = isHigh ? "Tin cậy Cao" : isMed ? "Tin cậy Vừa" : "Dữ liệu ban đầu";

  const tooltip = `Độ tin cậy: ${confidence.toUpperCase()}
• Số lần quan sát: ${observation_count} (${observation_span_hours}h)
• Chu kỳ chính: ${primary_signal_interval?.elapsed_hours ? `${primary_signal_interval.elapsed_hours}h` : "—"} ${primary_signal_interval?.is_estimated ? "(ước tính)" : "(đo lường chuẩn)"}
• Cập nhật: ${latest_observation_age_hours}h trước`;

  const sizeClass = size === "sm" ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-0.5 text-[11px]";

  return (
    <span
      title={tooltip}
      className={`inline-flex items-center gap-1 rounded font-medium border ${sizeClass} ${colorClass} cursor-help transition-colors`}
    >
      {isHigh ? (
        <ShieldCheck className="h-3 w-3 text-emerald-400" />
      ) : isMed ? (
        <Shield className="h-3 w-3 text-sky-400" />
      ) : (
        <ShieldAlert className="h-3 w-3 text-slate-400" />
      )}
      <span>{label}</span>
    </span>
  );
};
