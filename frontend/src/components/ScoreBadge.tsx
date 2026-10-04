import React from "react";

interface ScoreBadgeProps {
  score: number;
  size?: "sm" | "md" | "lg";
  hasMomentumEvidence?: boolean;
}

export const ScoreBadge: React.FC<ScoreBadgeProps> = ({ score, size = "md", hasMomentumEvidence = true }) => {
  let colorClass = "bg-slate-800 text-slate-300 border-slate-700";
  if (score >= 80) {
    colorClass = "bg-rose-500/20 text-rose-400 border-rose-500/40 font-bold shadow-sm shadow-rose-500/20";
  } else if (score >= 60) {
    colorClass = "bg-amber-500/20 text-amber-400 border-amber-500/40 font-semibold";
  } else if (score >= 40) {
    colorClass = "bg-blue-500/20 text-blue-400 border-blue-500/30";
  }

  const sizeClass = {
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-2.5 py-1",
    lg: "text-base px-3.5 py-1.5 font-bold",
  }[size];

  return (
    <span title={hasMomentumEvidence ? "Điểm xu hướng dựa trên lịch sử bán và đánh giá đã thu thập." : "Chưa có lịch sử đủ để tính tín hiệu xu hướng bán hàng."}
      aria-label={hasMomentumEvidence ? `Điểm xu hướng ${score.toFixed(1)}` : "Chưa đủ dữ liệu xu hướng"}
      className={`inline-flex items-center gap-1 rounded-md border ${sizeClass} ${colorClass}`}>
      <span className="opacity-70 text-[10px] tracking-wider uppercase">Score</span>
      <span>{score.toFixed(1)}</span>
    </span>
  );
};
