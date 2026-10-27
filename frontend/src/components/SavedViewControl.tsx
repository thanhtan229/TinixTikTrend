"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  SavedView,
  TrendsSavedViewPayload,
  WatchlistSavedViewPayload,
} from "@/types";
import {
  fetchSavedViews,
  createSavedView,
  updateSavedView,
  deleteSavedView,
} from "@/lib/api";
import { Bookmark, Save, Trash2, Edit2, Check, X } from "lucide-react";

interface SavedViewControlProps {
  scope: "trends" | "watchlist";
  currentPayload: TrendsSavedViewPayload | WatchlistSavedViewPayload;
  onApply: (payload: any) => void;
}

export const SavedViewControl: React.FC<SavedViewControlProps> = ({
  scope,
  currentPayload,
  onApply,
}) => {
  const [views, setViews] = useState<SavedView[]>([]);
  const [selectedViewId, setSelectedViewId] = useState<number | "">("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveName, setSaveName] = useState("");
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [editingViewId, setEditingViewId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [error, setError] = useState<string | null>(null);

  const loadViews = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchSavedViews(scope);
      setViews(Array.isArray(data) ? data : []);
    } catch (err: any) {
      console.error(err);
      setViews([]);
    } finally {
      setIsLoading(false);
    }
  }, [scope]);

  useEffect(() => {
    loadViews();
  }, [loadViews]);

  const handleApply = (view: SavedView) => {
    setSelectedViewId(view.id);
    // Apply local state directly - 0 extra DB query
    onApply(view.payload);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!saveName.trim()) return;
    setIsSaving(true);
    setError(null);
    try {
      let cleanPayload: any;
      if (scope === "trends") {
        const p = currentPayload as TrendsSavedViewPayload;
        cleanPayload = {
          category: p.category ?? null,
          trend_state: p.trend_state,
          measured_only: Boolean(p.measured_only),
          confidence: p.confidence ?? null,
          sort_by: p.sort_by,
          sort_direction: p.sort_direction,
          limit: p.limit,
          search: p.search ?? null,
          min_score: p.min_score != null ? Number(p.min_score) : null,
        };
      } else {
        const p = currentPayload as WatchlistSavedViewPayload;
        cleanPayload = {
          category: p.category ?? null,
          trend_state: p.trend_state,
          measured_only: Boolean(p.measured_only),
          confidence: p.confidence ?? null,
          sort_by: p.sort_by,
          sort_direction: p.sort_direction,
          limit: p.limit,
        };
      }

      const created = await createSavedView({
        name: saveName.trim(),
        scope,
        payload_version: 1,
        payload: cleanPayload,
      });

      setViews((prev) => [created, ...prev]);
      setSelectedViewId(created.id);
      setSaveName("");
      setShowSaveDialog(false);
    } catch (err: any) {
      setError(err.message || "Lỗi khi lưu chế độ xem");
    } finally {
      setIsSaving(false);
    }
  };

  const handleRename = async (viewId: number) => {
    if (!editName.trim()) return;
    try {
      const updated = await updateSavedView(viewId, { name: editName.trim() });
      setViews((prev) => prev.map((v) => (v.id === viewId ? updated : v)));
      setEditingViewId(null);
      setEditName("");
    } catch (err: any) {
      setError(err.message || "Lỗi khi đổi tên");
    }
  };

  const handleDelete = async (viewId: number) => {
    if (!window.confirm("Bạn có chắc muốn xóa chế độ xem này?")) return;
    try {
      await deleteSavedView(viewId);
      setViews((prev) => prev.filter((v) => v.id !== viewId));
      if (selectedViewId === viewId) setSelectedViewId("");
    } catch (err: any) {
      setError(err.message || "Lỗi khi xóa chế độ xem");
    }
  };

  return (
    <div className="flex items-center gap-2 flex-wrap text-xs">
      <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1">
        <Bookmark className="h-3.5 w-3.5 text-slate-400" />
        <span className="text-slate-400 font-medium">Chế độ xem:</span>
        <select
          aria-label="Chọn chế độ xem đã lưu"
          value={selectedViewId}
          onChange={(e) => {
            const id = e.target.value ? Number(e.target.value) : "";
            setSelectedViewId(id);
            if (id !== "") {
              const v = views.find((item) => item.id === id);
              if (v) handleApply(v);
            }
          }}
          className="bg-transparent text-slate-200 font-medium focus:outline-none cursor-pointer max-w-[150px] truncate"
        >
          <option value="" className="bg-slate-900 text-slate-400">
            {(views || []).length === 0 ? "Chưa có lưu" : "-- Chọn chế độ xem --"}
          </option>
          {(views || []).map((v) => (
            <option key={v.id} value={v.id} className="bg-slate-900 text-slate-200">
              {v.name}
            </option>
          ))}
        </select>

        {selectedViewId !== "" && (
          <div className="flex items-center gap-1 ml-1 border-l border-slate-800 pl-1.5">
            <button
              title="Đổi tên"
              onClick={() => {
                const v = views.find((item) => item.id === selectedViewId);
                if (v) {
                  setEditingViewId(v.id);
                  setEditName(v.name);
                }
              }}
              className="text-slate-400 hover:text-white p-0.5"
            >
              <Edit2 className="h-3 w-3" />
            </button>
            <button
              title="Xóa chế độ xem"
              onClick={() => handleDelete(Number(selectedViewId))}
              className="text-slate-400 hover:text-rose-400 p-0.5"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          </div>
        )}
      </div>

      <button
        onClick={() => setShowSaveDialog(true)}
        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
      >
        <Save className="h-3 w-3 text-emerald-400" />
        <span>Lưu bộ lọc hiện tại</span>
      </button>

      {/* Modal / Dialog for Save View */}
      {showSaveDialog && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 max-w-sm w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white">Lưu chế độ xem mới</h3>
              <button
                onClick={() => setShowSaveDialog(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            {error && <div className="text-rose-400 text-xs">{error}</div>}
            <form onSubmit={handleSave} className="space-y-3">
              <div>
                <label htmlFor="saved-view-name" className="block text-xs text-slate-400 mb-1">Tên chế độ xem</label>
                <input
                  id="saved-view-name"
                  type="text"
                  required
                  placeholder="VD: Quần áo đang tăng tốc cao"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-rose-500"
                />
              </div>
              <div className="text-[11px] text-slate-500">
                Lưu lại bộ lọc danh mục, trạng thái xu hướng, độ tin cậy và sắp xếp hiện tại.
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowSaveDialog(false)}
                  className="px-3 py-1.5 rounded-lg border border-slate-800 text-slate-400 hover:text-white"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={isSaving || !saveName.trim()}
                  className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium disabled:opacity-50"
                >
                  {isSaving ? "Đang lưu..." : "Lưu"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal / Dialog for Rename */}
      {editingViewId !== null && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 max-w-sm w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white">Đổi tên chế độ xem</h3>
              <button
                onClick={() => setEditingViewId(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="space-y-3">
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-rose-500"
              />
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setEditingViewId(null)}
                  className="px-3 py-1.5 rounded-lg border border-slate-800 text-slate-400 hover:text-white"
                >
                  Hủy
                </button>
                <button
                  onClick={() => handleRename(editingViewId)}
                  className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium"
                >
                  Lưu thay đổi
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
