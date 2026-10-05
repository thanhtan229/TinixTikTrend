"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Server,
  Database,
  ShieldCheck,
  Calendar,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Terminal,
} from "lucide-react";
import {
  fetchDiagnostics,
  fetchDeepDiagnostics,
} from "@/lib/api";
import { SystemDiagnosticsData, DeepDiagnosticsResult } from "@/types";

interface SystemDiagnosticsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SystemDiagnosticsModal: React.FC<SystemDiagnosticsModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [data, setData] = useState<SystemDiagnosticsData | null>(null);
  const [deepResult, setDeepResult] = useState<DeepDiagnosticsResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [deepLoading, setDeepLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"diagnostics" | "backup_restore">("diagnostics");

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const diag = await fetchDiagnostics();
      setData(diag);
    } catch (e: any) {
      setError(e.message || "Lỗi khi tải thông tin hệ thống");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadData();
      setDeepResult(null);
    }
  }, [isOpen]);

  const handleRunDeep = async () => {
    setDeepLoading(true);
    try {
      const res = await fetchDeepDiagnostics();
      setDeepResult(res);
    } catch (e: any) {
      setError(e.message || "Lỗi kiểm tra toàn vẹn");
    } finally {
      setDeepLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl max-h-[90vh] flex flex-col bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/50">
          <div className="flex items-center space-x-2">
            <Server className="h-5 w-5 text-indigo-400" />
            <h2 className="text-lg font-bold text-white">Chẩn đoán & Quản trị Hệ thống</h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Đóng modal"
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tab selection */}
        <div className="flex border-b border-slate-800 bg-slate-950/40 px-6 pt-2">
          <button
            onClick={() => setActiveTab("diagnostics")}
            className={`px-4 py-2 text-xs font-semibold border-b-2 transition-all ${
              activeTab === "diagnostics"
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Tổng quan & Toàn vẹn
          </button>
          <button
            onClick={() => setActiveTab("backup_restore")}
            className={`px-4 py-2 text-xs font-semibold border-b-2 transition-all ${
              activeTab === "backup_restore"
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Sao lưu & Phục hồi
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-center space-x-2 text-rose-400 text-xs">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 space-y-3">
              <RefreshCw className="h-8 w-8 text-indigo-400 animate-spin" />
              <p className="text-xs text-slate-400">Đang tải chẩn đoán hệ thống...</p>
            </div>
          ) : activeTab === "diagnostics" ? (
            <div className="space-y-6">
              {/* System and Database Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Database Info Card */}
                <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl space-y-3">
                  <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
                    <Database className="h-4 w-4 text-emerald-400" />
                    <span>Cơ sở dữ liệu SQLite</span>
                  </div>
                  <div className="space-y-1.5 text-xs text-slate-400">
                    <div className="flex justify-between">
                      <span>Tập tin:</span>
                      <span className="font-mono text-slate-200">{data?.database.relative_path || "affiliate.db"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Dung lượng:</span>
                      <span className="text-slate-200">
                        {data?.database.size_bytes ? (data.database.size_bytes / 1024 / 1024).toFixed(2) : "0"} MB
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Phiên bản tương thích:</span>
                      <span className="text-emerald-400 font-mono">v1</span>
                    </div>
                  </div>
                </div>

                {/* Session & Security Card */}
                <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl space-y-3">
                  <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
                    <ShieldCheck className="h-4 w-4 text-indigo-400" />
                    <span>Phiên làm việc & Bảo mật</span>
                  </div>
                  <div className="space-y-1.5 text-xs text-slate-400">
                    <div className="flex justify-between items-center">
                      <span>Trạng thái TikTok Session:</span>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                          data?.tiktok_session.status === "available"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : data?.tiktok_session.status === "invalid"
                            ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {data?.tiktok_session.status === "available"
                          ? "Khả dụng"
                          : data?.tiktok_session.status === "invalid"
                          ? "Không hợp lệ"
                          : "Chưa cấu hình"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Bảo vệ bí mật:</span>
                      <span className="text-emerald-400">Che giấu 100% (Redacted)</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Môi trường:</span>
                      <span className="font-mono text-slate-200 capitalize">{data?.system.environment}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Table Record Counts */}
              <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl space-y-3">
                <span className="text-xs font-semibold text-slate-300">Số lượng bản ghi trong các bảng</span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-800/80">
                    <span className="text-slate-400 block text-[11px]">Tổng sản phẩm:</span>
                    <span className="font-bold text-slate-100 text-sm">{data?.database.table_counts.products ?? 0}</span>
                  </div>
                  <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-800/80">
                    <span className="text-slate-400 block text-[11px]">Tổng snapshot:</span>
                    <span className="font-bold text-slate-100 text-sm">
                      {data?.database.table_counts.product_snapshots ?? 0}
                    </span>
                  </div>
                  <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-800/80">
                    <span className="text-slate-400 block text-[11px]">Watchlist:</span>
                    <span className="font-bold text-slate-100 text-sm">
                      {data?.database.table_counts.watchlist_items ?? 0}
                    </span>
                  </div>
                  <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-800/80">
                    <span className="text-slate-400 block text-[11px]">Cảnh báo đã kích hoạt:</span>
                    <span className="font-bold text-slate-100 text-sm">
                      {data?.database.table_counts.alert_events ?? 0}
                    </span>
                  </div>
                </div>
              </div>

              {/* Crawler & Scheduler Status */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl space-y-2 text-xs">
                  <div className="flex items-center space-x-2 font-semibold text-slate-300">
                    <RefreshCw className="h-4 w-4 text-cyan-400" />
                    <span>Trạng thái Bộ cào dữ liệu (Crawler)</span>
                  </div>
                  <div className="space-y-1 text-slate-400">
                    <div className="flex justify-between">
                      <span>Đang chạy:</span>
                      <span className={data?.crawler.is_running ? "text-amber-400 font-semibold" : "text-slate-300"}>
                        {data?.crawler.is_running ? "Đang quét dữ liệu" : "Nghỉ"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Lần cào gần nhất:</span>
                      <span className="text-slate-200">
                        {data?.crawler.last_run_finished_at
                          ? new Date(data.crawler.last_run_finished_at).toLocaleString("vi-VN")
                          : "Chưa thực hiện"}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl space-y-2 text-xs">
                  <div className="flex items-center space-x-2 font-semibold text-slate-300">
                    <Calendar className="h-4 w-4 text-purple-400" />
                    <span>Tác vụ Lập lịch (Scheduler)</span>
                  </div>
                  <div className="space-y-1 text-slate-400">
                    <div className="flex justify-between">
                      <span>Trạng thái bộ lập lịch:</span>
                      <span className={data?.scheduler.is_running ? "text-emerald-400" : "text-rose-400"}>
                        {data?.scheduler.is_running ? "Đang hoạt động" : "Tắt"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Số tác vụ định kỳ:</span>
                      <span className="text-slate-200">{data?.scheduler.jobs.length || 0} tác vụ</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* On-Demand Deep Integrity Check Section */}
              <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <ShieldCheck className="h-4 w-4 text-amber-400" />
                    <span className="text-xs font-semibold text-slate-200">Kiểm tra Toàn vẹn Chuyên sâu (On-Demand)</span>
                  </div>
                  <button
                    onClick={handleRunDeep}
                    disabled={deepLoading}
                    className="flex items-center space-x-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white rounded-lg text-xs font-medium transition-colors shadow-sm"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${deepLoading ? "animate-spin" : ""}`} />
                    <span>{deepLoading ? "Đang kiểm tra..." : "Chạy kiểm tra ngay"}</span>
                  </button>
                </div>
                <p className="text-[11px] text-slate-400">
                  Thực hiện trực tiếp <code>PRAGMA integrity_check</code> và <code>PRAGMA foreign_key_check</code> trên cơ sở dữ liệu.
                </p>

                {deepResult && (
                  <div className="mt-3 p-3 bg-slate-900 border border-slate-800 rounded-lg space-y-2 text-xs">
                    <div className="flex items-center space-x-2">
                      {deepResult.status === "ok" ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-amber-400" />
                      )}
                      <span className="font-semibold text-slate-200">
                        {deepResult.status === "ok" ? "Cơ sở dữ liệu hoàn toàn toàn vẹn" : "Phát hiện vấn đề toàn vẹn"}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 pt-1">
                      <div>
                        Integrity Check: <span className="font-mono text-emerald-400">{deepResult.integrity_check}</span>
                      </div>
                      <div>
                        Foreign Key Check:{" "}
                        <span className="font-mono text-emerald-400">
                          {Array.isArray(deepResult.foreign_key_check)
                            ? deepResult.foreign_key_check.length === 0
                              ? "OK (0 vi phạm)"
                              : `${deepResult.foreign_key_check.length} vi phạm`
                            : deepResult.foreign_key_check}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Backup & Restore Guide Tab */
            <div className="space-y-4 text-xs">
              <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl space-y-4">
                {/* Backup workflow */}
                <div className="space-y-2">
                  <div className="flex items-center space-x-2 font-semibold text-slate-200">
                    <Terminal className="h-4 w-4 text-emerald-400" />
                    <span>1. Quy trình Sao lưu Dữ liệu Chuẩn (BACKUP.bat)</span>
                  </div>
                  <p className="text-slate-400 leading-relaxed text-[11px]">
                    Thực hiện sao lưu điểm thời gian bằng API trực tuyến chuẩn SQLite <code>sqlite3.Connection.backup()</code>. Tập tin được kiểm tra toàn vẹn, tương thích và lưu trữ an toàn trong <code>backend/.local/backups/</code>:
                  </p>
                  <pre className="p-3 bg-slate-950 border border-slate-800 rounded-lg font-mono text-[11px] text-emerald-300 select-all overflow-x-auto">
                    .\BACKUP.bat
                  </pre>
                  <p className="text-[11px] text-slate-500">
                    * Sao lưu diễn ra trực tiếp ngay khi hệ thống đang vận hành mà không làm gián đoạn việc cào hay phân tích dữ liệu.
                  </p>
                </div>

                <div className="border-t border-slate-800/80 pt-4 space-y-2">
                  <div className="flex items-center space-x-2 font-semibold text-slate-200">
                    <Terminal className="h-4 w-4 text-indigo-400" />
                    <span>2. Quy trình Phục hồi Ngoại tuyến (RESTORE.bat)</span>
                  </div>
                  <p className="text-slate-400 leading-relaxed text-[11px]">
                    Để đảm bảo an toàn tuyệt đối và tránh lỗi khóa tập tin trên Windows (<code>WinError 32</code>), việc phục hồi cơ sở dữ liệu được thực hiện ngoại tuyến thông qua launcher:
                  </p>
                  <div className="space-y-2">
                    <div className="font-semibold text-slate-300 text-[11px]">Lệnh phục hồi từ tập tin sao lưu:</div>
                    <pre className="p-3 bg-slate-950 border border-slate-800 rounded-lg font-mono text-[11px] text-amber-300 select-all overflow-x-auto">
                      .\RESTORE.bat backend\.local\backups\tinix-affiliate-v1-YYYYMMDDTHHMMSS.ffffffZ.sqlite3
                    </pre>
                    <p className="text-[11px] text-slate-500">
                      * Tập lệnh sẽ tự động kiểm định tập tin ứng viên trước khi dừng dịch vụ, tạo bản sao lưu an toàn tự động, thay thế nguyên tử, khởi động lại và xác thực sức khỏe.
                    </p>

                    <div className="font-semibold text-slate-300 text-[11px] pt-1">Lệnh khắc phục sự cố (Crash Recovery):</div>
                    <pre className="p-3 bg-slate-950 border border-slate-800 rounded-lg font-mono text-[11px] text-cyan-300 select-all overflow-x-auto">
                      .\RESTORE.bat --recover
                    </pre>
                    <p className="text-[11px] text-slate-500">
                      * Nếu quá trình phục hồi trước đó bị gián đoạn, cờ <code>--recover</code> sẽ giải phóng manifest guard và khôi phục hệ thống về trạng thái hoàn tất hoặc rollback an toàn.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950/50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold transition-colors"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
};
