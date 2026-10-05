import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { WatchButton } from '@/components/WatchButton';
import { ProductCard } from '@/components/ProductCard';
import { AlertRuleModal } from '@/components/AlertRuleModal';
import { AlertCenter } from '@/components/AlertCenter';
import DashboardPage from '@/app/page';
import * as api from '@/lib/api';
import type { AlertRule, AlertEvent, TrendMetrics } from '@/types';

vi.mock('@/lib/api');
vi.mock('@/components/CrawlerControl', () => ({
  CrawlerControl: () => <div data-testid="crawler-control" />,
}));

const mockProduct: TrendMetrics = {
  product_id: 101,
  external_product_id: 'ext-101',
  title: 'Tai nghe Bluetooth không dây F9',
  shop_name: 'TechStore VN',
  category: 'Điện tử & Công nghệ',
  first_seen_at: '2026-10-01T00:00:00Z',
  last_seen_at: '2026-10-05T00:00:00Z',
  trend_score: 82,
  deltas: {
    latest_price: 150000,
    latest_sold_count: 520,
    sold_delta_24h: 85,
    sold_delta_7d: 310,
    sales_velocity_24h: 85.0,
    sales_acceleration: 15.0,
    latest_rating: 4.8,
  },
};

const mockRule: AlertRule = {
  id: 1,
  product_id: 101,
  rule_type: 'sales_velocity_above',
  threshold: 50,
  direction: null,
  cooldown_minutes: 60,
  is_active: true,
  last_condition_met: false,
  last_triggered_at: null,
  last_evaluated_snapshot_id: 10,
  created_at: '2026-10-05T00:00:00Z',
  updated_at: '2026-10-05T00:00:00Z',
};

const mockEvent: AlertEvent = {
  id: 1,
  rule_id: 1,
  product_id: 101,
  triggering_snapshot_id: 12,
  event_type: 'price_change_pct',
  threshold: 10,
  trigger_value: -15.5,
  direction: 'either',
  actual_direction: 'down',
  message: 'Giá giảm 15.5% (vượt ngưỡng 10.0%)',
  is_read: false,
  triggered_at: '2026-10-05T01:00:00Z',
  product_title: 'Tai nghe Bluetooth không dây F9',
};

describe('Phase 3 Frontend: Watchlist & Alerts Suite', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe('WatchButton Component', () => {
    it('renders watched and unwatched states and calls API on toggle', async () => {
      vi.mocked(api.addToWatchlist).mockResolvedValue({ status: 'watched', product_id: 101 });
      vi.mocked(api.removeFromWatchlist).mockResolvedValue({ status: 'unwatched', product_id: 101 });

      const onToggle = vi.fn();
      const { rerender } = render(
        <WatchButton productId={101} isWatched={false} onToggle={onToggle} showText={true} />
      );

      expect(screen.getByRole('button', { name: 'Theo dõi sản phẩm' })).toHaveTextContent('Theo dõi');

      // Click to watch
      fireEvent.click(screen.getByRole('button', { name: 'Theo dõi sản phẩm' }));
      await waitFor(() => expect(api.addToWatchlist).toHaveBeenCalledWith(101));
      expect(onToggle).toHaveBeenCalledWith(true);

      // Now rerender as watched
      rerender(<WatchButton productId={101} isWatched={true} onToggle={onToggle} showText={true} />);
      expect(screen.getByRole('button', { name: 'Bỏ theo dõi sản phẩm' })).toHaveTextContent('Đang theo dõi');

      // Click to unwatch
      fireEvent.click(screen.getByRole('button', { name: 'Bỏ theo dõi sản phẩm' }));
      await waitFor(() => expect(api.removeFromWatchlist).toHaveBeenCalledWith(101));
      expect(onToggle).toHaveBeenCalledWith(false);
    });

    it('stops event propagation when clicked inside a card', async () => {
      vi.mocked(api.addToWatchlist).mockResolvedValue({ status: 'watched', product_id: 101 });
      const parentClick = vi.fn();

      render(
        <div onClick={parentClick}>
          <WatchButton productId={101} isWatched={false} />
        </div>
      );

      fireEvent.click(screen.getByRole('button', { name: 'Theo dõi sản phẩm' }));
      expect(parentClick).not.toHaveBeenCalled();
    });
  });

  describe('ProductCard Phase 3 Integration', () => {
    it('renders with watch status and triggers onToggleWatch callback', () => {
      const toggleFn = vi.fn();
      render(
        <ProductCard product={mockProduct} isWatched={true} onToggleWatch={toggleFn} />
      );

      const watchBtn = screen.getByRole('button', { name: 'Bỏ theo dõi sản phẩm' });
      expect(watchBtn).toBeInTheDocument();
    });
  });

  describe('Dashboard Watchlist Tab', () => {
    it('switches to Watchlist tab and fetches watchlist data', async () => {
      vi.mocked(api.fetchDashboardSummary).mockResolvedValue({
        stats: { total_products: 10, high_trend_count: 2 },
        trending: [],
        rising: [],
        new_products: [],
        best_sellers: [],
      });
      vi.mocked(api.fetchTrends).mockResolvedValue([]);
      vi.mocked(api.fetchWatchedProductIds).mockResolvedValue([101]);
      vi.mocked(api.fetchWatchlist).mockResolvedValue({
        total: 1,
        items: [
          {
            product_id: 101,
            notes: 'Sản phẩm hot',
            created_at: '2026-10-01T00:00:00Z',
            analysis: mockProduct,
          },
        ],
      });

      render(<DashboardPage />);

      // Wait for initial render
      await waitFor(() => expect(api.fetchDashboardSummary).toHaveBeenCalled());

      // Find and click Watchlist tab
      const watchlistTabBtn = screen.getByRole('button', { name: /Watchlist/i });
      fireEvent.click(watchlistTabBtn);

      await waitFor(() => expect(api.fetchWatchlist).toHaveBeenCalled());
      expect(await screen.findByText('Tai nghe Bluetooth không dây F9')).toBeInTheDocument();
    });

    it('displays helpful empty state when Watchlist has zero items', async () => {
      vi.mocked(api.fetchDashboardSummary).mockResolvedValue({
        stats: { total_products: 5, high_trend_count: 1 },
        trending: [],
        rising: [],
        new_products: [],
        best_sellers: [],
      });
      vi.mocked(api.fetchTrends).mockResolvedValue([]);
      vi.mocked(api.fetchWatchedProductIds).mockResolvedValue([]);
      vi.mocked(api.fetchWatchlist).mockResolvedValue({
        total: 0,
        items: [],
      });

      render(<DashboardPage />);
      await waitFor(() => expect(api.fetchDashboardSummary).toHaveBeenCalled());

      const watchlistTabBtn = screen.getByRole('button', { name: /Watchlist/i });
      fireEvent.click(watchlistTabBtn);

      expect(await screen.findByText('Chưa có sản phẩm nào trong Watchlist')).toBeInTheDocument();
    });
  });

  describe('AlertRuleModal Component', () => {
    it('renders existing rules and submits new rule with validation', async () => {
      vi.mocked(api.fetchAlertRules).mockResolvedValue([mockRule]);
      vi.mocked(api.createAlertRule).mockResolvedValue({
        ...mockRule,
        id: 2,
        rule_type: 'price_change_pct',
        threshold: 15,
        direction: 'down',
      });
      vi.mocked(api.updateAlertRule).mockResolvedValue({ ...mockRule, is_active: false });

      const onClose = vi.fn();
      render(
        <AlertRuleModal
          productId={101}
          productTitle="Tai nghe Bluetooth không dây F9"
          isOpen={true}
          onClose={onClose}
        />
      );

      // Verify modal header and existing rule display
      expect(await screen.findByText('Thiết lập Cảnh báo Sản phẩm')).toBeInTheDocument();
      expect(screen.getByText(/Tốc độ bán vượt 50 đơn\/ngày/)).toBeInTheDocument();

      // Toggle active status
      const toggleBtn = screen.getByRole('button', { name: 'Tạm dừng quy tắc' });
      fireEvent.click(toggleBtn);
      await waitFor(() => expect(api.updateAlertRule).toHaveBeenCalledWith(1, { is_active: false }));

      // Fill out new rule for price_change_pct
      const ruleTypeSelect = screen.getByDisplayValue('Tốc độ bán vượt ngưỡng (đơn/ngày)');
      fireEvent.change(ruleTypeSelect, { target: { value: 'price_change_pct' } });

      // Direction selector should now be visible
      const directionSelect = screen.getByDisplayValue('Cả 2 chiều (± Thay đổi tăng hoặc giảm)');
      fireEvent.change(directionSelect, { target: { value: 'down' } });

      // Submit
      fireEvent.click(screen.getByRole('button', { name: 'Thêm quy tắc' }));
      await waitFor(() =>
        expect(api.createAlertRule).toHaveBeenCalledWith(
          expect.objectContaining({
            product_id: 101,
            rule_type: 'price_change_pct',
            direction: 'down',
            threshold: 10,
          })
        )
      );
    });

    it('rejects invalid threshold input with clear validation error', async () => {
      vi.mocked(api.fetchAlertRules).mockResolvedValue([]);
      render(
        <AlertRuleModal
          productId={101}
          productTitle="Tai nghe Bluetooth không dây F9"
          isOpen={true}
          onClose={vi.fn()}
        />
      );

      await waitFor(() => expect(api.fetchAlertRules).toHaveBeenCalled());

      const thresholdInput = screen.getByPlaceholderText('Ví dụ: 50');
      fireEvent.change(thresholdInput, { target: { value: '-5' } });

      fireEvent.click(screen.getByRole('button', { name: 'Thêm quy tắc' }));
      expect(await screen.findByRole('alert')).toHaveTextContent('Ngưỡng giá trị phải là số lớn hơn 0');
      expect(api.createAlertRule).not.toHaveBeenCalled();
    });
  });

  describe('AlertCenter Notification Component', () => {
    it('displays unread count and opens popover listing alert events', async () => {
      vi.mocked(api.fetchUnreadAlertCount).mockResolvedValue(2);
      vi.mocked(api.fetchAlertEvents).mockResolvedValue([mockEvent]);
      vi.mocked(api.markAlertRead).mockResolvedValue({ status: 'ok', event_id: 1, is_read: true });
      vi.mocked(api.markAllAlertsRead).mockResolvedValue({ status: 'ok', marked_read_count: 1 });

      render(<AlertCenter />);

      // Verify unread badge
      expect(await screen.findByText('2')).toBeInTheDocument();

      // Click bell to open
      const bellBtn = screen.getByRole('button', { name: /Thông báo cảnh báo/i });
      fireEvent.click(bellBtn);

      await waitFor(() => expect(api.fetchAlertEvents).toHaveBeenCalled());
      expect(await screen.findByText(/Giá giảm 15.5%/)).toBeInTheDocument();

      // Semantic rule check: Price alert must NOT be labeled as "Điểm xu hướng" or "trending"
      expect(screen.getByText('Giá giảm')).toBeInTheDocument();

      // Click mark read button
      const markReadBtn = screen.getByRole('button', { name: 'Đánh dấu đã đọc' });
      fireEvent.click(markReadBtn);
      await waitFor(() => expect(api.markAlertRead).toHaveBeenCalledWith(1));

      // Click mark all read
      const markAllBtn = screen.getByRole('button', { name: /Đã đọc tất cả/i });
      fireEvent.click(markAllBtn);
      await waitFor(() => expect(api.markAllAlertsRead).toHaveBeenCalled());
    });
  });
});
