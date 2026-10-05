"use client";

import React, { useState } from "react";
import { Star } from "lucide-react";
import { addToWatchlist, removeFromWatchlist } from "@/lib/api";

interface WatchButtonProps {
  productId: number;
  isWatched: boolean;
  onToggle?: (watched: boolean) => void;
  size?: "sm" | "md" | "lg";
  showText?: boolean;
}

export const WatchButton: React.FC<WatchButtonProps> = ({
  productId,
  isWatched: initialWatched,
  onToggle,
  size = "md",
  showText = false,
}) => {
  const [watched, setWatched] = useState<boolean>(initialWatched);
  const [loading, setLoading] = useState<boolean>(false);

  // Synchronize if prop changes
  React.useEffect(() => {
    setWatched(initialWatched);
  }, [initialWatched]);

  const handleToggle = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (loading) return;

    const nextState = !watched;
    setWatched(nextState); // optimistic
    setLoading(true);

    try {
      if (nextState) {
        await addToWatchlist(productId);
      } else {
        await removeFromWatchlist(productId);
      }
      onToggle?.(nextState);
    } catch (err) {
      // rollback
      setWatched(!nextState);
      console.error("Failed to toggle watch status:", err);
    } finally {
      setLoading(false);
    }
  };

  const iconSizes = {
    sm: "h-3.5 w-3.5",
    md: "h-4 w-4",
    lg: "h-5 w-5",
  };

  return (
    <button
      type="button"
      onClick={handleToggle}
      disabled={loading}
      aria-label={watched ? "Bỏ theo dõi sản phẩm" : "Theo dõi sản phẩm"}
      title={watched ? "Đang theo dõi (bấm để hủy)" : "Theo dõi sản phẩm"}
      className={`inline-flex items-center gap-1.5 rounded-lg border transition-all duration-150 ${
        watched
          ? "bg-amber-500/10 border-amber-500/30 text-amber-400 hover:bg-amber-500/20 hover:border-amber-500/50"
          : "bg-slate-800/80 border-slate-700/80 text-slate-400 hover:text-amber-400 hover:bg-slate-800 hover:border-slate-600"
      } ${
        size === "sm"
          ? "px-2 py-1 text-xs"
          : size === "lg"
          ? "px-3.5 py-2 text-sm font-semibold"
          : "px-2.5 py-1.5 text-xs font-medium"
      } ${loading ? "opacity-60 cursor-not-allowed" : ""}`}
    >
      <Star
        className={`${iconSizes[size]} transition-transform ${
          watched ? "fill-amber-400 text-amber-400 scale-110" : ""
        }`}
      />
      {showText && (
        <span>{watched ? "Đang theo dõi" : "Theo dõi"}</span>
      )}
    </button>
  );
};
