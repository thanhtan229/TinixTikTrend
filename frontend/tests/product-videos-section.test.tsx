import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ProductVideosSection } from "@/components/ProductVideosSection";
import { addProductVideo, fetchProductVideos } from "@/lib/api";

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    addProductVideo: vi.fn(),
    detachProductVideo: vi.fn(),
    fetchProductVideos: vi.fn(),
    refreshProductVideo: vi.fn(),
  };
});

describe("ProductVideosSection", () => {
  beforeEach(() => {
    vi.mocked(fetchProductVideos).mockResolvedValue([]);
    vi.mocked(addProductVideo).mockResolvedValue();
  });

  it("discloses attribution limits, attaches a manual URL, and renders missing counters", async () => {
    vi.mocked(fetchProductVideos)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([{
        video_id: "12345",
        url: "https://www.tiktok.com/@maker/video/12345",
        creator_handle: "maker",
        creator_name: null,
        description: null,
        thumbnail_url: null,
        refresh_status: "unavailable",
        refresh_message: "Số liệu không khả dụng.",
        last_attempt_at: null,
        associated_at: "2026-10-07T00:00:00Z",
        snapshots: [],
        content_metrics: { velocities: {}, anomalies: {}, engagement_rate: null },
      }]);
    render(<ProductVideosSection productId={21} />);

    expect(await screen.findByText(/không xác nhận video thực sự/i)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Liên kết video TikTok"), {
      target: { value: "https://www.tiktok.com/@maker/video/12345" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Gắn video" }));

    expect(await screen.findByText("@maker")).toBeInTheDocument();
    expect(screen.getAllByText("Chưa có dữ liệu").length).toBeGreaterThan(0);
    await waitFor(() => expect(addProductVideo).toHaveBeenCalledWith(21, "https://www.tiktok.com/@maker/video/12345"));
  });
});
