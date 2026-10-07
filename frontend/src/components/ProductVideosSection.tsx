"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  addProductVideo,
  detachProductVideo,
  fetchProductVideos,
  ProductVideo,
  refreshProductVideo,
} from "@/lib/api";

function VideoThumbnail({ src }: { src?: string | null }) {
  const [failed, setFailed] = useState(false);
  return (
    <div className="flex h-20 w-32 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-slate-800 text-xs font-semibold text-slate-400">
      {src && !failed ? (
        <img
          src={src}
          alt=""
          loading="lazy"
          referrerPolicy="no-referrer"
          onError={() => setFailed(true)}
          className="h-full w-full object-cover"
        />
      ) : "TikTok"}
    </div>
  );
}

function displayCount(value: number | null | undefined): string {
  return value == null ? "Chưa có dữ liệu" : new Intl.NumberFormat("vi-VN").format(value);
}

export function ProductVideosSection({ productId }: { productId: number }) {
  const [items, setItems] = useState<ProductVideo[]>([]);
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  async function load() {
    setItems(await fetchProductVideos(productId));
  }

  useEffect(() => {
    let active = true;
    fetchProductVideos(productId)
      .then((videos) => { if (active) setItems(videos); })
      .catch((err: Error) => { if (active) setError(err.message); });
    return () => { active = false; };
  }, [productId]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy("add");
    setError(null);
    try {
      await addProductVideo(productId, url);
      setUrl("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể gắn video.");
    } finally {
      setBusy(null);
    }
  }

  async function runAction(key: string, action: () => Promise<void>) {
    setBusy(key);
    setError(null);
    try {
      await action();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Thao tác không thành công.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-5">
      <div>
        <h2 className="text-base font-bold text-white">Video TikTok liên quan</h2>
        <p className="mt-1 text-xs text-slate-400">
          Liên kết do bạn gắn, không xác nhận video thực sự quảng bá sản phẩm. Lượt tương tác không phải doanh số hay hoa hồng.
        </p>
      </div>

      <form onSubmit={submit} className="flex flex-col sm:flex-row gap-2">
        <label className="sr-only" htmlFor="product-video-url">Liên kết video TikTok</label>
        <input
          id="product-video-url"
          type="url"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="https://www.tiktok.com/@creator/video/..."
          className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white placeholder:text-slate-500"
        />
        <button disabled={busy !== null || !url.trim()} className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">
          {busy === "add" ? "Đang gắn…" : "Gắn video"}
        </button>
      </form>

      {error && <p role="alert" className="text-sm text-rose-300">{error}</p>}

      {items.length === 0 ? (
        <p className="rounded-lg border border-dashed border-slate-700 p-4 text-center text-sm text-slate-500">
          Chưa có video được gắn.
        </p>
      ) : (
        <div className="space-y-3">
          {items.map((video) => (
            <article key={video.video_id} className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex min-w-0 gap-3">
                  <VideoThumbnail src={video.thumbnail_url} />
                  <div className="min-w-0">
                    <a href={video.url} target="_blank" rel="noopener noreferrer" className="text-sm font-semibold text-cyan-300 hover:text-cyan-200">
                      {video.creator_name || (video.creator_handle ? `@${video.creator_handle}` : `Video ${video.video_id}`)}
                    </a>
                    {video.description && <p className="mt-1 line-clamp-2 text-sm text-slate-300">{video.description}</p>}
                    <p className="mt-2 text-xs text-slate-500">
                      Nguồn metadata: TikTok oEmbed · {video.refresh_message || "Chưa làm mới metadata."}
                    </p>
                    {video.last_attempt_at && (
                      <p className="mt-1 text-[11px] text-slate-500">
                        Làm mới lần cuối: {new Date(video.last_attempt_at).toLocaleString("vi-VN")}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex shrink-0 gap-2">
                  <button
                    type="button"
                    disabled={busy !== null}
                    onClick={() => runAction(`refresh-${video.video_id}`, () => refreshProductVideo(productId, video.video_id))}
                    className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-800 disabled:opacity-50"
                  >
                    {busy === `refresh-${video.video_id}` ? "Đang tải…" : "Làm mới"}
                  </button>
                  <button
                    type="button"
                    disabled={busy !== null}
                    onClick={() => runAction(`detach-${video.video_id}`, () => detachProductVideo(productId, video.video_id))}
                    className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs font-semibold text-slate-400 hover:text-rose-300 disabled:opacity-50"
                  >
                    Gỡ
                  </button>
                </div>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs sm:grid-cols-5">
                {[
                  ["Lượt xem", "view_count"],
                  ["Thích", "like_count"],
                  ["Bình luận", "comment_count"],
                  ["Chia sẻ", "share_count"],
                  ["Lưu", "collect_count"],
                ].map(([label, key]) => (
                  <div key={key} className="rounded-lg bg-slate-900 px-3 py-2">
                    <div className="text-slate-500">{label}</div>
                    <div className="mt-1 font-semibold text-slate-200">
                      {displayCount(video.snapshots[0]?.[key as keyof ProductVideo["snapshots"][number]] as number | null | undefined)}
                    </div>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-[11px] text-slate-500">
                {video.snapshots.length
                  ? `Nguồn: ${video.snapshots[0].source} · Quan sát gần nhất: ${new Date(video.snapshots[0].captured_at).toLocaleString("vi-VN")}`
                  : "Chưa có nguồn đo lường tương tác công khai khả dụng."}
              </p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
