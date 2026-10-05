"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { AlertEvent } from "@/types";
import {
  fetchAlertEvents,
  fetchUnreadAlertCount,
  markAlertRead,
  markAllAlertsRead,
  getExportAlertsUrl,
} from "@/lib/api";
import { formatDate } from "@/lib/utils";
import {
  Bell,
  CheckCheck,
  TrendingUp,
  Flame,
  ArrowUpRight,
  ArrowDownRight,
  Percent,
  Check,
  ExternalLink,
  Download,
} from "lucide-react";

export const AlertCenter: React.FC = () => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [events, setEvents] = useState<AlertEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const loadUnreadCount = async () => {
    try {
      const count = await fetchUnreadAlertCount();
      setUnreadCount(count);
    } catch (err) {
      console.warn("Could not fetch unread alert count:", err);
    }
  };

  const loadEvents = async () => {
    setLoading(true);
    try {
      const list = await fetchAlertEvents({ limit: 20 });
      setEvents(Array.isArray(list) ? list : []);
    } catch (err) {
      console.warn("Could not fetch alert events:", err);
    } finally {
      setLoading(false);
    }
  };

  // Poll count periodically (every 30 seconds)
  useEffect(() => {
    loadUnreadCount();
    const interval = setInterval(loadUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  // When opening drawer/dropdown, load full events
  useEffect(() => {
    if (isOpen) {
      loadEvents();
      loadUnreadCount();
    }
  }, [isOpen]);

  // Click outside and ESC key handling
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        panelRef.current &&
        !panelRef.current.contains(e.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const handleMarkRead = async (e: React.MouseEvent, eventId: number) => {
    e.stopPropagation();
    e.preventDefault();
    try {
      await markAlertRead(eventId);
      setEvents((prev) =>
        prev.map((ev) => (ev.id === eventId ? { ...ev, is_read: true } : ev))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (err) {
      console.error("Failed to mark alert as read:", err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllAlertsRead();
      setEvents((prev) => prev.map((ev) => ({ ...ev, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error("Failed to mark all alerts as read:", err);
    }
  };

  const renderEventIcon = (event: AlertEvent) => {
    if (event.event_type === "sales_velocity_above") {
      return (
        <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <TrendingUp className="h-4 w-4" />
        </div>
      );
    }
    if (event.event_type === "trend_score_above") {
      return (
        <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <Flame className="h-4 w-4" />
        </div>
      );
    }
    if (event.event_type === "price_change_pct") {
      if (event.actual_direction === "down") {
        return (
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <ArrowDownRight className="h-4 w-4" />
          </div>
        );
      }
      return (
        <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <ArrowUpRight className="h-4 w-4" />
        </div>
      );
    }
    return (
      <div className="p-2 rounded-lg bg-slate-800 text-slate-400 border border-slate-700">
        <Bell className="h-4 w-4" />
      </div>
    );
  };

  const getEventBadge = (event: AlertEvent) => {
    if (event.event_type === "sales_velocity_above") {
      return (
        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          Tốc độ bán
        </span>
      );
    }
    if (event.event_type === "trend_score_above") {
      return (
        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
          Điểm xu hướng
        </span>
      );
    }
    if (event.event_type === "price_change_pct") {
      const dirText = event.actual_direction === "down" ? "Giá giảm" : "Giá tăng";
      return (
        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
          {dirText}
        </span>
      );
    }
    return <span className="text-[10px] font-semibold text-slate-400">{event.event_type}</span>;
  };

  return (
    <div className="relative">
      {/* Bell Trigger Button */}
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label={`Thông báo cảnh báo (${unreadCount} chưa đọc)`}
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        className="relative p-2 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full bg-rose-600 text-[10px] font-bold text-white shadow-md shadow-rose-600/50 animate-pulse">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Popover / Dropdown Panel */}
      {isOpen && (
        <div
          ref={panelRef}
          role="dialog"
          aria-label="Trung tâm thông báo cảnh báo"
          className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150"
        >
          {/* Header */}
          <div className="p-3.5 px-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-white tracking-wide uppercase">
                Cảnh báo đã kích hoạt
              </span>
              {unreadCount > 0 && (
                <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">
                  {unreadCount} mới
                </span>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <a
                href={getExportAlertsUrl()}
                download="alerts_export.csv"
                aria-label="Xuất CSV cảnh báo"
                className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-400 hover:text-white transition-colors p-1 rounded hover:bg-slate-800"
              >
                <Download className="h-3 w-3" />
                <span>Xuất CSV</span>
              </a>
              {unreadCount > 0 && (
                <button
                  type="button"
                  onClick={handleMarkAllRead}
                  className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-400 hover:text-rose-400 transition-colors"
                >
                  <CheckCheck className="h-3 w-3" />
                  <span>Đã đọc tất cả</span>
                </button>
              )}
            </div>
          </div>


          {/* Events List */}
          <div className="max-h-[420px] overflow-y-auto divide-y divide-slate-800/60">
            {loading ? (
              <div className="py-8 text-center text-xs text-slate-500">Đang tải cảnh báo...</div>
            ) : events.length === 0 ? (
              <div className="py-10 px-4 text-center">
                <Bell className="h-8 w-8 text-slate-700 mx-auto mb-2 opacity-50" />
                <p className="text-xs font-semibold text-slate-400">Không có cảnh báo nào</p>
                <p className="text-[11px] text-slate-600 mt-0.5">
                  Các cảnh báo biến động sản phẩm đã theo dõi sẽ xuất hiện tại đây.
                </p>
              </div>
            ) : (
              events.map((event) => (
                <div
                  key={event.id}
                  className={`p-3.5 hover:bg-slate-800/40 transition-colors flex items-start gap-3 ${
                    !event.is_read ? "bg-slate-950/50" : ""
                  }`}
                >
                  <div className="flex-shrink-0 mt-0.5">{renderEventIcon(event)}</div>

                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center justify-between gap-1">
                      {getEventBadge(event)}
                      <span className="text-[10px] text-slate-500">
                        {formatDate(event.triggered_at)}
                      </span>
                    </div>

                    <p className="text-xs text-slate-200 leading-snug font-medium">
                      {event.message}
                    </p>

                    {event.product_title && (
                      <Link
                        href={`/products/${event.product_id}`}
                        onClick={() => setIsOpen(false)}
                        className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-rose-400 truncate max-w-[240px] transition-colors"
                      >
                        <span className="truncate">{event.product_title}</span>
                        <ExternalLink className="h-2.5 w-2.5 flex-shrink-0" />
                      </Link>
                    )}
                  </div>

                  {!event.is_read && (
                    <button
                      type="button"
                      onClick={(e) => handleMarkRead(e, event.id)}
                      aria-label="Đánh dấu đã đọc"
                      title="Đánh dấu đã đọc"
                      className="p-1 rounded-md text-slate-500 hover:text-white hover:bg-slate-800 flex-shrink-0 mt-1"
                    >
                      <Check className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
