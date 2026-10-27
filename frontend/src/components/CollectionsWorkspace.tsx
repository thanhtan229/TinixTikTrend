"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Collection, CollectionItem, ReviewStatus } from "@/types";
import {
  fetchCollections,
  createCollection,
  updateCollection,
  deleteCollection,
  fetchCollectionMembers,
  updateCollectionItem,
  removeProductFromCollection,
} from "@/lib/api";
import { formatCurrency, formatNumber, formatDate } from "@/lib/utils";
import {
  Folder,
  FolderPlus,
  Trash2,
  Edit2,
  Plus,
  Save,
  ShoppingBag,
  ExternalLink,
  Star,
  Check,
  Scale,
} from "lucide-react";
import Link from "next/link";

interface CollectionsWorkspaceProps {
  onAddToCompare?: (productId: number, title: string, imageUrl?: string | null) => void;
}

export const CollectionsWorkspace: React.FC<CollectionsWorkspaceProps> = ({
  onAddToCompare,
}) => {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollectionId, setSelectedCollectionId] = useState<number | null>(null);
  const [items, setItems] = useState<CollectionItem[]>([]);
  const [isLoadingCols, setIsLoadingCols] = useState(false);
  const [isLoadingItems, setIsLoadingItems] = useState(false);

  // Notes editing state: Map of productId -> draft notes
  const [notesDrafts, setNotesDrafts] = useState<Record<number, string>>({});
  const [savingNotesId, setSavingNotesId] = useState<number | null>(null);
  const [savedNotesFeedback, setSavedNotesFeedback] = useState<Record<number, boolean>>({});

  // Collection modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newColName, setNewColName] = useState("");
  const [newColDesc, setNewColDesc] = useState("");
  const [editingColId, setEditingColId] = useState<number | null>(null);
  const [editColName, setEditColName] = useState("");
  const [editColDesc, setEditColDesc] = useState("");

  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);

  const loadCollections = useCallback(async () => {
    setIsLoadingCols(true);
    setError(null);
    try {
      const data = await fetchCollections();
      setCollections(data);
      setSelectedCollectionId((prev) => (prev !== null ? prev : data.length > 0 ? data[0].id : null));
    } catch (err: any) {
      setError(err.message || "Không thể tải danh sách bộ sưu tập");
    } finally {
      setIsLoadingCols(false);
    }
  }, []);

  useEffect(() => {
    loadCollections();
  }, [loadCollections]);

  const loadItems = useCallback(async (colId: number, filter?: string) => {
    setIsLoadingItems(true);
    try {
      const stat = filter && filter !== "all" ? filter : undefined;
      const data = await fetchCollectionMembers(colId, stat);
      setItems(data);
      // Initialize notes drafts
      const drafts: Record<number, string> = {};
      data.forEach((it) => {
        drafts[it.product_id] = it.notes || "";
      });
      setNotesDrafts(drafts);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsLoadingItems(false);
    }
  }, []);

  useEffect(() => {
    if (selectedCollectionId) {
      loadItems(selectedCollectionId, statusFilter);
    } else {
      setItems([]);
    }
  }, [selectedCollectionId, statusFilter, loadItems]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newColName.trim()) return;
    try {
      const created = await createCollection(newColName.trim(), newColDesc.trim() || undefined);
      setCollections((prev) => [created, ...prev]);
      setSelectedCollectionId(created.id);
      setNewColName("");
      setNewColDesc("");
      setShowCreateModal(false);
    } catch (err: any) {
      alert(err.message || "Lỗi khi tạo bộ sưu tập");
    }
  };

  const handleUpdateCollection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingColId || !editColName.trim()) return;
    try {
      const updated = await updateCollection(editingColId, {
        name: editColName.trim(),
        description: editColDesc.trim() || undefined,
      });
      setCollections((prev) => prev.map((c) => (c.id === editingColId ? updated : c)));
      setEditingColId(null);
    } catch (err: any) {
      alert(err.message || "Lỗi khi cập nhật bộ sưu tập");
    }
  };

  const handleDeleteCollection = async (colId: number) => {
    if (!window.confirm("Bạn có chắc chắn muốn xóa bộ sưu tập này? Các sản phẩm trong hệ thống vẫn sẽ được giữ nguyên.")) return;
    try {
      await deleteCollection(colId);
      const remaining = collections.filter((c) => c.id !== colId);
      setCollections(remaining);
      setSelectedCollectionId(remaining.length > 0 ? remaining[0].id : null);
    } catch (err: any) {
      alert(err.message || "Lỗi khi xóa bộ sưu tập");
    }
  };

  const handleStatusChange = async (productId: number, newStatus: ReviewStatus) => {
    if (!selectedCollectionId) return;
    try {
      const updated = await updateCollectionItem(selectedCollectionId, productId, {
        review_status: newStatus,
      });
      setItems((prev) =>
        prev.map((it) => (it.product_id === productId ? { ...it, review_status: newStatus } : it))
      );
    } catch (err: any) {
      alert(err.message || "Lỗi khi đổi trạng thái");
    }
  };

  const handleSaveNotes = async (productId: number) => {
    if (!selectedCollectionId) return;
    setSavingNotesId(productId);
    try {
      const text = notesDrafts[productId] ?? "";
      await updateCollectionItem(selectedCollectionId, productId, {
        notes: text,
      });
      setSavedNotesFeedback((prev) => ({ ...prev, [productId]: true }));
      setTimeout(() => {
        setSavedNotesFeedback((prev) => ({ ...prev, [productId]: false }));
      }, 2000);
    } catch (err: any) {
      alert(err.message || "Lỗi khi lưu ghi chú");
    } finally {
      setSavingNotesId(null);
    }
  };

  const handleRemoveProduct = async (productId: number) => {
    if (!selectedCollectionId) return;
    if (!window.confirm("Bỏ sản phẩm này khỏi bộ sưu tập?")) return;
    try {
      await removeProductFromCollection(selectedCollectionId, productId);
      setItems((prev) => prev.filter((it) => it.product_id !== productId));
      setCollections((prev) =>
        prev.map((c) =>
          c.id === selectedCollectionId ? { ...c, item_count: Math.max(0, (c.item_count ?? 1) - 1) } : c
        )
      );
    } catch (err: any) {
      alert(err.message || "Lỗi khi xóa khỏi bộ sưu tập");
    }
  };

  const activeCollection = collections.find((c) => c.id === selectedCollectionId);

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800 rounded-xl p-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Folder className="h-5 w-5 text-rose-400" />
            <span>Bộ sưu tập Quyết định (Opportunity Workspace)</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Tổ chức, đánh giá trạng thái và ghi chú thẩm định sản phẩm độc lập với Watchlist.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-sm transition-colors self-start sm:self-auto"
        >
          <FolderPlus className="h-4 w-4" />
          <span>Tạo Bộ sưu tập mới</span>
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-lg border border-rose-800 bg-rose-950/40 text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* Main layout: Sidebar collection list + Selected collection details */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        {/* Collections List / Selector (Left Column) */}
        <div className="lg:col-span-1 space-y-2 bg-slate-900/40 border border-slate-800 rounded-xl p-3">
          <div className="text-xs font-semibold text-slate-400 px-2 py-1 uppercase tracking-wider">
            Danh sách ({collections.length})
          </div>

          {isLoadingCols ? (
            <div className="text-xs text-slate-500 p-3 text-center">Đang tải...</div>
          ) : collections.length === 0 ? (
            <div className="text-xs text-slate-500 p-4 text-center">
              Chưa có bộ sưu tập nào. Bấm &quot;Tạo Bộ sưu tập mới&quot; để bắt đầu.
            </div>
          ) : (
            <div className="space-y-1">
              {collections.map((c) => {
                const isSelected = c.id === selectedCollectionId;
                return (
                  <button
                    key={c.id}
                    onClick={() => setSelectedCollectionId(c.id)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-all flex items-center justify-between group ${
                      isSelected
                        ? "bg-rose-600/20 text-white border border-rose-500/40 font-semibold"
                        : "text-slate-300 hover:bg-slate-800/60 hover:text-white border border-transparent"
                    }`}
                  >
                    <div className="truncate mr-2">
                      <div className="truncate">{c.name}</div>
                      <div className="text-[10px] text-slate-500 font-normal">
                        {c.item_count ?? 0} sản phẩm
                      </div>
                    </div>
                    {isSelected && (
                      <span className="w-1.5 h-1.5 rounded-full bg-rose-400 flex-shrink-0" />
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Selected Collection View (Right Column) */}
        <div className="lg:col-span-3 space-y-4">
          {activeCollection ? (
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
              {/* Collection Header info & Actions */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-bold text-white">{activeCollection.name}</h3>
                    <button
                      onClick={() => {
                        setEditingColId(activeCollection.id);
                        setEditColName(activeCollection.name);
                        setEditColDesc(activeCollection.description || "");
                      }}
                      className="text-slate-400 hover:text-white p-1"
                      title="Chỉnh sửa bộ sưu tập"
                    >
                      <Edit2 className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => handleDeleteCollection(activeCollection.id)}
                      className="text-slate-400 hover:text-rose-400 p-1"
                      title="Xóa bộ sưu tập"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                  {activeCollection.description && (
                    <p className="text-xs text-slate-400 mt-1">{activeCollection.description}</p>
                  )}
                  <div className="text-[11px] text-slate-500 mt-1">
                    Tạo ngày: {formatDate(activeCollection.created_at)} • {items.length} sản phẩm
                  </div>
                </div>

                {/* Status Filter inside collection */}
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-400">Lọc trạng thái:</span>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none focus:border-rose-500"
                  >
                    <option value="all">Tất cả ({items.length})</option>
                    <option value="new">Mới (New)</option>
                    <option value="reviewing">Đang xem xét (Reviewing)</option>
                    <option value="candidate">Ứng viên (Candidate)</option>
                    <option value="rejected">Đã loại (Rejected)</option>
                  </select>
                </div>
              </div>

              {/* Members Table */}
              {isLoadingItems ? (
                <div className="py-12 text-center text-xs text-slate-500">Đang tải sản phẩm...</div>
              ) : items.length === 0 ? (
                <div className="py-12 text-center space-y-2">
                  <p className="text-xs text-slate-400">Bộ sưu tập chưa có sản phẩm nào phù hợp.</p>
                  <p className="text-[11px] text-slate-500">
                    Bạn có thể bấm &quot;Thêm vào BST&quot; trên các thẻ sản phẩm ở trang Trending, Watchlist hoặc Chi tiết sản phẩm.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                        <th className="py-2.5 px-3">Sản phẩm</th>
                        <th className="py-2.5 px-3">Watch</th>
                        <th className="py-2.5 px-3">Trạng thái đánh giá</th>
                        <th className="py-2.5 px-3">Hoa hồng/đơn</th>
                        <th className="py-2.5 px-3">Đóng góp/đơn</th>
                        <th className="py-2.5 px-3">Đơn hòa vốn</th>
                        <th className="py-2.5 px-3">Ghi chú quyết định</th>
                        <th className="py-2.5 px-3 text-right">Thao tác</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {items.map((item) => {
                        const prod = item.product;
                        const isSaving = savingNotesId === item.product_id;
                        const isSaved = savedNotesFeedback[item.product_id];

                        return (
                          <tr key={item.id} className="hover:bg-slate-800/30 transition-colors">
                            {/* Product Info */}
                            <td className="py-3 px-3 max-w-xs">
                              <div className="flex items-start gap-2.5">
                                <div className="w-10 h-10 rounded-md bg-slate-950 border border-slate-800 flex-shrink-0 overflow-hidden flex items-center justify-center">
                                  {prod?.image_url ? (
                                    <img
                                      src={prod.image_url}
                                      alt={prod.title}
                                      className="w-full h-full object-cover"
                                    />
                                  ) : (
                                    <ShoppingBag className="h-5 w-5 text-slate-600" />
                                  )}
                                </div>
                                <div className="min-w-0">
                                  <Link
                                    href={`/products/${item.product_id}`}
                                    className="font-medium text-slate-200 hover:text-rose-400 line-clamp-1 transition-colors"
                                  >
                                    {prod?.title || `Sản phẩm #${item.product_id}`}
                                  </Link>
                                  <div className="text-[11px] text-slate-400 mt-0.5">
                                    {prod?.category || "Chưa phân loại"} • {prod?.shop_name || "Shop"}
                                  </div>
                                </div>
                              </div>
                            </td>

                            {/* Watch status indicator (read-only decoupled display) */}
                            <td className="py-3 px-3 whitespace-nowrap">
                              {item.is_watched ? (
                                <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full">
                                  <Star className="h-3 w-3 fill-amber-400" />
                                  <span>Theo dõi</span>
                                </span>
                              ) : (
                                <span className="text-[11px] text-slate-500 italic">
                                  Không
                                </span>
                              )}
                            </td>

                            {/* Review status dropdown */}
                            <td className="py-3 px-3 whitespace-nowrap">
                              <select
                                aria-label="Trạng thái đánh giá"
                                value={item.review_status}
                                onChange={(e) =>
                                  handleStatusChange(item.product_id, e.target.value as ReviewStatus)
                                }
                                className={`rounded-md px-2 py-1 text-xs font-semibold focus:outline-none border ${
                                  item.review_status === "candidate"
                                    ? "bg-emerald-950/60 text-emerald-400 border-emerald-800"
                                    : item.review_status === "reviewing"
                                    ? "bg-amber-950/60 text-amber-400 border-amber-800"
                                    : item.review_status === "rejected"
                                    ? "bg-rose-950/60 text-rose-400 border-rose-800"
                                    : "bg-slate-950 text-slate-300 border-slate-800"
                                }`}
                              >
                                <option value="new">Mới</option>
                                <option value="reviewing">Đang xem xét</option>
                                <option value="candidate">Ứng viên</option>
                                <option value="rejected">Đã loại</option>
                              </select>
                            </td>

                            {/* Economics Summary (Phase 6) */}
                            <td className="py-3 px-3 whitespace-nowrap">
                              {item.default_economics?.derived?.commission_per_order_vnd != null ? (
                                <div className="font-semibold text-emerald-400">
                                  {formatCurrency(item.default_economics.derived.commission_per_order_vnd)}
                                </div>
                              ) : (
                                <span className="text-slate-500">—</span>
                              )}
                            </td>
                            <td className="py-3 px-3 whitespace-nowrap">
                              {item.default_economics?.derived?.contribution_per_order_vnd != null ? (
                                <div
                                  className={`font-semibold ${
                                    item.default_economics.derived.contribution_per_order_vnd >= 0
                                      ? "text-emerald-400"
                                      : "text-rose-400"
                                  }`}
                                >
                                  {formatCurrency(item.default_economics.derived.contribution_per_order_vnd)}
                                </div>
                              ) : (
                                <span className="text-slate-500">—</span>
                              )}
                            </td>
                            <td className="py-3 px-3 whitespace-nowrap">
                              {item.default_economics?.derived?.break_even_orders != null ? (
                                <div className="font-semibold text-slate-200">
                                  {formatNumber(item.default_economics.derived.break_even_orders)} đơn
                                </div>
                              ) : (
                                <span className="text-slate-500">—</span>
                              )}
                            </td>

                            {/* Notes with explicit Save button */}
                            <td className="py-3 px-3 min-w-[200px]">
                              <div className="flex items-center gap-1.5">
                                <input
                                  type="text"
                                  placeholder="Thêm ghi chú đánh giá..."
                                  value={notesDrafts[item.product_id] ?? ""}
                                  onChange={(e) =>
                                    setNotesDrafts((prev) => ({
                                      ...prev,
                                      [item.product_id]: e.target.value,
                                    }))
                                  }
                                  className="w-full bg-slate-950 border border-slate-800 rounded-md px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-rose-500"
                                />
                                <button
                                  onClick={() => handleSaveNotes(item.product_id)}
                                  disabled={isSaving}
                                  title="Lưu ghi chú"
                                  className={`p-1 rounded-md border text-xs transition-colors flex-shrink-0 ${
                                    isSaved
                                      ? "bg-emerald-600 text-white border-emerald-500"
                                      : "bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border-slate-700"
                                  }`}
                                >
                                  {isSaved ? (
                                    <Check className="h-3.5 w-3.5" />
                                  ) : (
                                    <Save className="h-3.5 w-3.5" />
                                  )}
                                </button>
                              </div>
                            </td>

                            {/* Actions: Compare & Remove */}
                            <td className="py-3 px-3 text-right whitespace-nowrap">
                              <div className="flex items-center justify-end gap-1.5">
                                {onAddToCompare && (
                                  <button
                                    onClick={() =>
                                      onAddToCompare(
                                        item.product_id,
                                        prod?.title || `Sản phẩm #${item.product_id}`,
                                        prod?.image_url
                                      )
                                    }
                                    title="Thêm vào khay so sánh"
                                    className="p-1 rounded border border-slate-800 hover:border-slate-700 bg-slate-950 hover:bg-slate-800 text-slate-400 hover:text-white"
                                  >
                                    <Scale className="h-3.5 w-3.5 text-cyan-400" />
                                  </button>
                                )}
                                <button
                                  onClick={() => handleRemoveProduct(item.product_id)}
                                  title="Bỏ khỏi bộ sưu tập"
                                  className="p-1 rounded border border-slate-800 hover:border-rose-900 bg-slate-950 hover:bg-rose-950/40 text-slate-400 hover:text-rose-400"
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 bg-slate-900/40 border border-slate-800 rounded-xl">
              Vui lòng chọn hoặc tạo mới một bộ sưu tập.
            </div>
          )}
        </div>
      </div>

      {/* Create Collection Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 max-w-sm w-full shadow-2xl space-y-4">
            <h3 className="text-sm font-semibold text-white">Tạo Bộ sưu tập mới</h3>
            <form onSubmit={handleCreate} className="space-y-3 text-xs">
              <div>
                <label htmlFor="new-workspace-collection-name" className="block text-slate-400 mb-1">Tên bộ sưu tập</label>
                <input
                  id="new-workspace-collection-name"
                  type="text"
                  required
                  placeholder="VD: Sản phẩm Tiềm năng Q4"
                  value={newColName}
                  onChange={(e) => setNewColName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-100 focus:outline-none focus:border-rose-500"
                />
              </div>
              <div>
                <label htmlFor="new-workspace-collection-description" className="block text-slate-400 mb-1">Mô tả (tùy chọn)</label>
                <textarea
                  id="new-workspace-collection-description"
                  rows={2}
                  placeholder="Mô tả mục tiêu của bộ sưu tập..."
                  value={newColDesc}
                  onChange={(e) => setNewColDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-100 focus:outline-none focus:border-rose-500"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 rounded-lg border border-slate-800 text-slate-400 hover:text-white"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium"
                >
                  Tạo mới
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Collection Modal */}
      {editingColId !== null && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 max-w-sm w-full shadow-2xl space-y-4">
            <h3 className="text-sm font-semibold text-white">Chỉnh sửa Bộ sưu tập</h3>
            <form onSubmit={handleUpdateCollection} className="space-y-3 text-xs">
              <div>
                <label htmlFor="edit-workspace-collection-name" className="block text-slate-400 mb-1">Tên bộ sưu tập</label>
                <input
                  id="edit-workspace-collection-name"
                  type="text"
                  required
                  value={editColName}
                  onChange={(e) => setEditColName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-100 focus:outline-none focus:border-rose-500"
                />
              </div>
              <div>
                <label htmlFor="edit-workspace-collection-description" className="block text-slate-400 mb-1">Mô tả</label>
                <textarea
                  id="edit-workspace-collection-description"
                  rows={2}
                  value={editColDesc}
                  onChange={(e) => setEditColDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-100 focus:outline-none focus:border-rose-500"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingColId(null)}
                  className="px-3 py-1.5 rounded-lg border border-slate-800 text-slate-400 hover:text-white"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium"
                >
                  Cập nhật
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
