"use client";

import React, { useEffect, useState } from "react";
import { Collection, ReviewStatus } from "@/types";
import { fetchCollections, createCollection, addProductToCollection } from "@/lib/api";
import { FolderPlus, Plus, X, Check } from "lucide-react";

interface AddToCollectionModalProps {
  productId: number;
  productTitle: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const AddToCollectionModal: React.FC<AddToCollectionModalProps> = ({
  productId,
  productTitle,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollectionId, setSelectedCollectionId] = useState<number | "new">("new");
  const [newCollectionName, setNewCollectionName] = useState("");
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus>("new");
  const [notes, setNotes] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setError(null);
      setSuccessMsg(null);
      setIsLoading(true);
      fetchCollections()
        .then((cols) => {
          setCollections(cols);
          if (cols.length > 0) {
            setSelectedCollectionId(cols[0].id);
          } else {
            setSelectedCollectionId("new");
          }
        })
        .catch((err) => setError("Không tải được danh sách bộ sưu tập"))
        .finally(() => setIsLoading(false));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setIsSubmitting(true);

    try {
      let targetCollectionId: number;
      if (selectedCollectionId === "new") {
        if (!newCollectionName.trim()) {
          setError("Vui lòng nhập tên bộ sưu tập mới");
          setIsSubmitting(false);
          return;
        }
        const created = await createCollection(newCollectionName.trim());
        targetCollectionId = created.id;
      } else {
        targetCollectionId = Number(selectedCollectionId);
      }

      await addProductToCollection(
        targetCollectionId,
        productId,
        reviewStatus,
        notes.trim() || undefined
      );

      setSuccessMsg("Đã thêm vào bộ sưu tập thành công!");
      onSuccess?.();
      setTimeout(() => {
        onClose();
      }, 1000);
    } catch (err: any) {
      if (err.message && (err.message.includes("already in collection") || err.message.includes("409"))) {
        setError("Sản phẩm đã có trong bộ sưu tập này rồi.");
      } else {
        setError(err.message || "Lỗi khi thêm sản phẩm vào bộ sưu tập");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 max-w-md w-full shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <FolderPlus className="h-4 w-4 text-rose-400" />
            <h3 className="text-sm font-semibold text-white">Thêm vào Bộ sưu tập</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="text-xs text-slate-300 font-medium line-clamp-1">
          {productTitle}
        </div>

        {error && (
          <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
            {error}
          </div>
        )}

        {successMsg && (
          <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
            <Check className="h-4 w-4" />
            <span>{successMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label htmlFor="collection-select" className="block text-slate-400 mb-1">Chọn Bộ sưu tập</label>
            <select
              id="collection-select"
              aria-label="Chọn bộ sưu tập"
              value={selectedCollectionId}
              onChange={(e) => {
                const val = e.target.value === "new" ? "new" : Number(e.target.value);
                setSelectedCollectionId(val);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-rose-500"
            >
              {collections.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.item_count ?? 0} sản phẩm)
                </option>
              ))}
              <option value="new">+ Tạo bộ sưu tập mới...</option>
            </select>
          </div>

          {selectedCollectionId === "new" && (
            <div>
              <label htmlFor="new-collection-name" className="block text-slate-400 mb-1">Tên bộ sưu tập mới</label>
              <input
                id="new-collection-name"
                type="text"
                placeholder="VD: Sản phẩm Tiềm năng Q4"
                value={newCollectionName}
                onChange={(e) => setNewCollectionName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-rose-500"
                required
              />
            </div>
          )}

          <div>
            <label htmlFor="initial-review-status" className="block text-slate-400 mb-1">Trạng thái đánh giá ban đầu</label>
            <select
              id="initial-review-status"
              aria-label="Trạng thái đánh giá ban đầu"
              value={reviewStatus}
              onChange={(e) => setReviewStatus(e.target.value as ReviewStatus)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-rose-500"
            >
              <option value="new">Mới (New)</option>
              <option value="reviewing">Đang xem xét (Reviewing)</option>
              <option value="candidate">Ứng viên tiềm năng (Candidate)</option>
              <option value="rejected">Đã loại (Rejected)</option>
            </select>
          </div>

          <div>
            <label htmlFor="collection-decision-notes" className="block text-slate-400 mb-1">Ghi chú quyết định (Notes)</label>
            <textarea
              id="collection-decision-notes"
              rows={2}
              placeholder="VD: Nhà bán uy tín, biên độ lợi nhuận ước tính > 30%..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-rose-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-lg border border-slate-800 text-slate-400 hover:text-white"
            >
              Hủy
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium disabled:opacity-50"
            >
              {isSubmitting ? "Đang lưu..." : "Thêm vào BST"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
