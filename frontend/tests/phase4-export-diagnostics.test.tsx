import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { ProductHistory } from '@/components/ProductHistory';
import { SystemDiagnosticsModal } from '@/components/SystemDiagnosticsModal';
import { AlertCenter } from '@/components/AlertCenter';
import * as api from '@/lib/api';
import { ProductSnapshot, SystemDiagnosticsData } from '@/types';

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  LineChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
  CartesianGrid: () => null,
}));

const mockDiagnostics: SystemDiagnosticsData = {
  system: {
    environment: 'development',
    region: 'VN',
    version: '1.0.0',
    server_time_utc: '2026-10-05T12:00:00Z',
  },
  database: {
    relative_path: 'backend/affiliate.db',
    size_bytes: 1048576,
    table_counts: {
      products: 25,
      product_snapshots: 150,
      crawl_runs: 10,
      quarantined_products: 0,
      watchlist_items: 5,
      alert_rules: 3,
      alert_events: 12,
    },
  },
  crawler: {
    is_running: false,
    last_run_id: 10,
    last_run_status: 'completed',
    last_run_finished_at: '2026-10-05T11:55:00Z',
    quarantined_count: 0,
  },
  scheduler: {
    is_running: true,
    jobs: [
      { id: 'tiktok_scheduled_crawl', name: 'Định kỳ quét TikTok Shop', next_run_time: '2026-10-05T16:00:00Z' },
    ],
  },
  tiktok_session: {
    status: 'available',
    redacted: true,
    notes: 'Toàn bộ cookie, token và dữ liệu phiên được che giấu tuyệt đối vì lý do bảo mật.',
  },
};

describe('Phase 4 — Frontend Export & Diagnostics (P4-AC-27, P4-AC-28, P4-AC-32)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe('Product History Export CSV (P4-AC-03, P4-AC-27)', () => {
    const snapshots: ProductSnapshot[] = [
      { id: 1, product_id: 42, captured_at: new Date().toISOString(), sold_count: 10, review_count: 2, rating: 4.8, price: 100000, commission_rate: 10 },
    ];

    it('renders enabled Export CSV button for 24h, 7d, and 30d with correct URLs', () => {
      render(<ProductHistory snapshots={snapshots} productId={42} />);

      // Default is 24h
      const exportLink = screen.getByRole('link', { name: /Xuất CSV/i });
      expect(exportLink).toBeInTheDocument();
      expect(exportLink).toHaveAttribute('href', expect.stringContaining('/products/42/export-history?range=24h'));
      expect(exportLink).not.toHaveClass('pointer-events-none');

      // Switch to 7d
      fireEvent.click(screen.getByRole('button', { name: '7d' }));
      expect(screen.getByRole('link', { name: /Xuất CSV/i })).toHaveAttribute(
        'href',
        expect.stringContaining('/products/42/export-history?range=7d')
      );

      // Switch to 30d
      fireEvent.click(screen.getByRole('button', { name: '30d' }));
      expect(screen.getByRole('link', { name: /Xuất CSV/i })).toHaveAttribute(
        'href',
        expect.stringContaining('/products/42/export-history?range=30d')
      );
    });

    it('locks and disables Export CSV button when range is "Tất cả" with explanation tooltip', () => {
      render(<ProductHistory snapshots={snapshots} productId={42} />);

      // Click "Tất cả"
      fireEvent.click(screen.getByRole('button', { name: 'Tất cả' }));

      const exportBtn = screen.getByRole('button', { name: /Xuất CSV/i });
      expect(exportBtn).toBeDisabled();
      expect(
        screen.getByText(/Khoảng thời gian "Tất cả" chỉ hỗ trợ xem trực quan trên giao diện/i)
      ).toBeInTheDocument();
    });
  });

  describe('System Diagnostics Modal (P4-AC-25, P4-AC-26, P4-AC-28)', () => {
    it('loads and renders allowlisted system diagnostics, database info, and session status', async () => {
      vi.spyOn(api, 'fetchDiagnostics').mockResolvedValue(mockDiagnostics);

      render(<SystemDiagnosticsModal isOpen={true} onClose={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByText('backend/affiliate.db')).toBeInTheDocument();
        expect(screen.getByText('Khả dụng')).toBeInTheDocument();
      });

      // Verifies table counts render
      expect(screen.getByText('Tổng sản phẩm:')).toBeInTheDocument();
      expect(screen.getByText('25')).toBeInTheDocument();
      expect(screen.getByText('Tổng snapshot:')).toBeInTheDocument();
      expect(screen.getByText('150')).toBeInTheDocument();
    });

    it('navigates tabs to Operator Backup & Restore Guide with command instructions', async () => {
      vi.spyOn(api, 'fetchDiagnostics').mockResolvedValue(mockDiagnostics);

      render(<SystemDiagnosticsModal isOpen={true} onClose={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByText('backend/affiliate.db')).toBeInTheDocument();
      });

      // Switch to Backup & Restore tab
      fireEvent.click(screen.getByRole('button', { name: /Sao lưu & Phục hồi/i }));
      expect(screen.getByText(/\.\\BACKUP\.bat/i)).toBeInTheDocument();
      expect(screen.getByText(/\.\\RESTORE\.bat --recover/i)).toBeInTheDocument();
      expect(screen.getByText(/backend\\\.local\\backups\\/i)).toBeInTheDocument();

      // Verify NO browser backup create button or download links exist
      expect(screen.queryByRole('button', { name: /Tạo bản sao lưu ngay/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /Tải về/i })).not.toBeInTheDocument();
    });

    it('executes manual on-demand deep diagnostics check', async () => {
      vi.spyOn(api, 'fetchDiagnostics').mockResolvedValue(mockDiagnostics);
      vi.spyOn(api, 'fetchDeepDiagnostics').mockResolvedValue({
        status: 'ok',
        integrity_check: 'ok',
        foreign_key_check: [],
        checked_at: '2026-10-05T12:00:00Z',
      });

      render(<SystemDiagnosticsModal isOpen={true} onClose={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByText('backend/affiliate.db')).toBeInTheDocument();
      });

      const deepBtn = screen.getByRole('button', { name: /Chạy kiểm tra ngay/i });
      fireEvent.click(deepBtn);

      await waitFor(() => {
        expect(screen.getByText(/Cơ sở dữ liệu hoàn toàn toàn vẹn/i)).toBeInTheDocument();
        expect(screen.getByText(/OK \(0 vi phạm\)/i)).toBeInTheDocument();
      });
    });
    it('displays error banner when fetchDiagnostics fails', async () => {
      vi.spyOn(api, 'fetchDiagnostics').mockRejectedValue(new Error('Mất kết nối máy chủ'));

      render(<SystemDiagnosticsModal isOpen={true} onClose={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByText('Mất kết nối máy chủ')).toBeInTheDocument();
      });
    });
  });

  describe('Alert Center Export CSV', () => {
    it('surfaces Xuất CSV link in the alert center popover', async () => {
      vi.spyOn(api, 'fetchUnreadAlertCount').mockResolvedValue(0);
      vi.spyOn(api, 'fetchAlertEvents').mockResolvedValue([]);

      render(<AlertCenter />);

      // Open popover
      const bellButton = screen.getByRole('button', { name: /Thông báo cảnh báo/i });
      fireEvent.click(bellButton);

      await waitFor(() => {
        const exportLink = screen.getByRole('link', { name: /Xuất CSV cảnh báo/i });
        expect(exportLink).toBeInTheDocument();
        expect(exportLink).toHaveAttribute('href', expect.stringContaining('/alerts/events/export'));
      });
    });
  });

  describe('Trends and Watchlist Export URL Generation (P4-AC-01, P4-AC-02, P4-AC-27)', () => {
    it('constructs correct Trends CSV export URLs with filters and pagination parameters', () => {
      const url = api.getExportTrendsUrl({
        category: 'Thực phẩm & Đồ uống',
        trend_state: 'eligible',
        confidence: 'high',
        evidence: 'measured_only',
        sort_by: 'trend_score',
        order: 'desc',
        limit: 50,
        offset: 100,
      });

      expect(url).toContain('/trends/export?');
      expect(url).toContain('category=Th%E1%BB%B1c+ph%E1%BA%A9m+%26+%C4%90%E1%BB%93+u%E1%BB%91ng');
      expect(url).toContain('trend_state=eligible');
      expect(url).toContain('confidence=high');
      expect(url).toContain('evidence=measured_only');
      expect(url).toContain('sort_by=trend_score');
      expect(url).toContain('order=desc');
      expect(url).toContain('limit=50');
      expect(url).toContain('offset=100');
    });

    it('constructs correct Watchlist CSV export URLs with filters and pagination parameters', () => {
      const url = api.getExportWatchlistUrl({
        category: 'Gia dụng',
        trend_state: 'all',
        sort_by: 'sales_velocity',
        order: 'asc',
        limit: 25,
        skip: 50,
      });

      expect(url).toContain('/watchlist/export?');
      expect(url).toContain('category=Gia+d%E1%BB%A5ng');
      expect(url).toContain('trend_state=all');
      expect(url).toContain('sort_by=sales_velocity');
      expect(url).toContain('order=asc');
      expect(url).toContain('limit=25');
      expect(url).toContain('skip=50');
    });
  });
});
