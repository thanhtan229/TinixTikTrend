"use client";

import React, { useEffect, useRef, useState } from "react";
import { fetchCrawlerStatus, triggerCrawlerRun, CrawlerStatus } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Play, Loader2, CheckCircle2, AlertCircle, Globe, Sparkles, ChevronDown, ChevronUp } from "lucide-react";

const MAX_PRODUCT_URLS = 100;

function parseProductUrls(value: string): string[] {
  return Array.from(new Set(value.split(/\r?\n/).map((url) => url.trim()).filter(Boolean)));
}

export const CrawlerControl: React.FC<{ onCrawlCompleted?: () => void }> = ({ onCrawlCompleted }) => {
  const [status, setStatus] = useState<CrawlerStatus | null>(null);
  const [triggering, setTriggering] = useState<boolean>(false);
  const [message, setMessage] = useState<string | null>(null);
  const [showCustomInput, setShowCustomInput] = useState<boolean>(false);
  const [customUrlsText, setCustomUrlsText] = useState<string>("");
  const [customKeyword, setCustomKeyword] = useState<string>("");
  const [connectionError, setConnectionError] = useState(false);
  const callback = useRef(onCrawlCompleted);
  const previous = useRef<CrawlerStatus | null>(null);
  const productUrls = parseProductUrls(customUrlsText);
  const exceedsUrlLimit = productUrls.length > MAX_PRODUCT_URLS;
  useEffect(() => { callback.current = onCrawlCompleted; }, [onCrawlCompleted]);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const next = await fetchCrawlerStatus();
        if (!active) return;
        const prev = previous.current;
        previous.current = next;
        setStatus(next);
        setConnectionError(false);
        if (!next.is_running && prev && (prev.is_running || next.latest_run?.id !== prev.latest_run?.id)) {
          callback.current?.();
          setMessage(null);
        }
      } catch {
        if (active) setConnectionError(true);
      } finally {
        if (active) timer = setTimeout(poll, previous.current?.is_running ? 2000 : 6000);
      }
    };
    poll();
    return () => { active = false; clearTimeout(timer); };
  }, []);

  const handleTrigger = async () => {
    if (exceedsUrlLimit) {
      setMessage(`Mỗi lần quét nhận tối đa ${MAX_PRODUCT_URLS} link sản phẩm.`);
      return;
    }
    setTriggering(true);
    setMessage(null);
    try {
      const payload: { product_urls?: string[]; keywords?: string[] } = {};
      if (productUrls.length > 0) {
        payload.product_urls = productUrls;
      }
      if (customKeyword.trim()) {
        payload.keywords = [customKeyword.trim()];
      }

      await triggerCrawlerRun(payload);
      setMessage("Đang tiến hành quét dữ liệu TikTok Shop VN...");
      setStatus((prev) => (prev ? { ...prev, is_running: true } : null));
      if (previous.current) previous.current = { ...previous.current, is_running: true };
      setCustomUrlsText("");
      setCustomKeyword("");
      setShowCustomInput(false);
    } catch (err: any) {
      setMessage(err.message || "Không thể kích hoạt crawler");
    } finally {
      setTriggering(false);
    }
  };

  const isRunning = status?.is_running;
  const lastRun = status?.latest_run;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className={`p-2.5 rounded-xl ${isRunning ? "bg-amber-500/15 text-amber-400 border border-amber-500/30 animate-pulse" : "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"}`}>
            {isRunning ? <Loader2 className="h-5 w-5 animate-spin" /> : <CheckCircle2 className="h-5 w-5" />}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-semibold text-white">
                {connectionError ? "Không kết nối được backend" : isRunning ? "Crawler đang quét dữ liệu TikTok Shop VN..." : "Hệ thống Crawler Sẵn sàng"}
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                Lịch tự động: {status?.schedule || "08:00, 12:00, 16:00, 20:00, 00:00"}
              </span>
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              Lần quét gần nhất:{" "}
              <span className="text-slate-200 font-medium">
                {lastRun ? formatDate(lastRun.started_at) : "Chưa có"}
              </span>
              {lastRun && (
                <span className="ml-2 text-slate-400">
                  (Tìm thấy: <strong className="text-slate-200">{lastRun.products_found}</strong>, Snapshots: <strong className="text-emerald-400">{lastRun.snapshots_created}</strong>)
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => setShowCustomInput(!showCustomInput)}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
          >
            <Globe className="h-3.5 w-3.5 text-slate-400" />
            <span>Quét theo Link / Từ khóa</span>
            {showCustomInput ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>

          <button
            onClick={handleTrigger}
          disabled={triggering || isRunning || connectionError || exceedsUrlLimit}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-rose-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 text-white text-xs font-semibold shadow-md shadow-rose-600/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {triggering || isRunning ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4 fill-white" />
            )}
            <span>{isRunning ? "Đang quét..." : "Chạy Crawler Ngay"}</span>
          </button>
        </div>
      </div>

      {!isRunning && lastRun && (lastRun.status === "failed" || lastRun.status === "partial") && (
        <div role="alert" className="text-xs text-amber-300 border border-amber-800 rounded-lg p-3">
          {lastRun.status === "partial" ? "Lần quét chỉ thành công một phần." : "Lần quét thất bại."} {lastRun.error_message}
        </div>
      )}
      {!isRunning && lastRun?.status === "partial" && <div role="status" className="text-xs text-slate-400">
        Dữ liệu của sản phẩm đang theo dõi vẫn được cập nhật khi bước khám phá sản phẩm mới gặp lỗi.
      </div>}
      {(status?.quarantined_products ?? 0) > 0 && <div className="text-xs text-amber-300">
        {status?.quarantined_products} bản ghi cũ không xác minh được đã được cách ly; không dùng để xếp hạng. Lịch sử vẫn được giữ.
      </div>}

      {status?.local_session_status && <div className="text-xs text-slate-400">
        {status.local_session_status === "available"
          ? "Đã có phiên TikTok cục bộ. Quyền truy cập sản phẩm sẽ được kiểm tra khi quét."
          : status.local_session_status === "invalid"
            ? "Phiên TikTok đã lưu bị lỗi. Mở CONNECT_TIKTOK.bat để tự đăng nhập và lưu lại phiên."
            : "Chưa có phiên TikTok cục bộ. Nếu gặp Security Check, mở CONNECT_TIKTOK.bat để tự đăng nhập, rồi quét lại."}
      </div>}

      {message && (
        <div className="text-xs text-amber-300 bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-lg flex items-center gap-2">
          <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" />
          <span>{message}</span>
        </div>
      )}

      {/* Custom URL or Keyword input drawer */}
      {showCustomInput && (
        <div className="p-3.5 rounded-lg bg-slate-950/80 border border-slate-800 space-y-3 pt-3">
          <div className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-rose-400" />
            <span>Quét tùy biến sản phẩm TikTok Shop</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label htmlFor="crawl-product-url" className="text-[11px] text-slate-400 block mb-1">Dán link sản phẩm TikTok Shop (mỗi link một dòng):</label>
              <textarea
                id="crawl-product-url"
                rows={3}
                placeholder={'https://shop.tiktok.com/vn/pdp/...\nhttps://shop.tiktok.com/vn/pdp/...'}
                value={customUrlsText}
                onChange={(e) => setCustomUrlsText(e.target.value)}
                aria-describedby="crawl-product-url-count"
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-rose-500 resize-y"
              />
              <div id="crawl-product-url-count" role={exceedsUrlLimit ? "alert" : "status"} aria-live={exceedsUrlLimit ? "assertive" : "polite"} className={`text-[11px] mt-1 ${exceedsUrlLimit ? "text-rose-300" : "text-slate-500"}`}>
                {productUrls.length}/{MAX_PRODUCT_URLS} link duy nhất
              </div>
            </div>
            <div>
              <label htmlFor="crawl-keyword" className="text-[11px] text-slate-400 block mb-1">Từ khóa ngành hàng / Tag (tùy chọn):</label>
              <input
                id="crawl-keyword"
                type="text"
                placeholder="VD: son-moi, vay-nu, gia-dung..."
                value={customKeyword}
                onChange={(e) => setCustomKeyword(e.target.value)}
                className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-rose-500"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
