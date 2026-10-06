"use client";

import React from "react";
import { Scale, X, Trash2, ArrowRight, ShoppingBag } from "lucide-react";

export interface StagedProduct {
  productId: number;
  title: string;
  imageUrl?: string | null;
}

interface CompareTrayProps {
  staged: StagedProduct[];
  onRemove: (productId: number) => void;
  onClear: () => void;
  onOpenCompare: () => void;
}

export const CompareTray: React.FC<CompareTrayProps> = ({
  staged,
  onRemove,
  onClear,
  onOpenCompare,
}) => {
  if (staged.length === 0) return null;

  const canCompare = staged.length >= 2 && staged.length <= 5;

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-40 max-w-4xl w-[95%] bg-slate-900/95 backdrop-blur-md border border-cyan-500/40 rounded-2xl shadow-2xl p-3 text-xs text-white">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Left: Tray status & Clear button */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 font-bold text-cyan-400">
            <Scale className="h-4 w-4" />
            <span>Khay so sánh ({staged.length}/5)</span>
          </div>

          <button
            onClick={onClear}
            className="text-[11px] text-slate-400 hover:text-rose-400 flex items-center gap-1 transition-colors"
          >
            <Trash2 className="h-3 w-3" />
            <span>Xóa tất cả</span>
          </button>
        </div>

        {/* Center: Staged products badges */}
        <div className="flex items-center gap-2 overflow-x-auto py-1 scrollbar-thin">
          {staged.map((p) => (
            <div
              key={p.productId}
              className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 max-w-[160px] flex-shrink-0 group"
            >
              <div className="w-5 h-5 rounded bg-slate-900 overflow-hidden flex-shrink-0 flex items-center justify-center">
                {p.imageUrl ? (
                  <img src={p.imageUrl} alt={p.title} className="w-full h-full object-cover" />
                ) : (
                  <ShoppingBag className="h-3 w-3 text-slate-600" />
                )}
              </div>
              <span className="truncate text-[11px] text-slate-200">{p.title}</span>
              <button
                onClick={() => onRemove(p.productId)}
                className="text-slate-500 hover:text-rose-400 p-0.5 ml-0.5 transition-colors"
                title="Bỏ khỏi so sánh"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>

        {/* Right: Compare Action button */}
        <div className="flex items-center gap-2 self-end sm:self-auto flex-shrink-0">
          {!canCompare && (
            <span className="text-[10px] text-amber-400 hidden md:inline">
              Cần chọn tối thiểu 2 sản phẩm
            </span>
          )}

          <button
            disabled={!canCompare}
            onClick={onOpenCompare}
            className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-xl font-bold text-xs shadow-md transition-all ${
              canCompare
                ? "bg-cyan-500 hover:bg-cyan-400 text-slate-950 cursor-pointer"
                : "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700"
            }`}
          >
            <span>So sánh ngay</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
