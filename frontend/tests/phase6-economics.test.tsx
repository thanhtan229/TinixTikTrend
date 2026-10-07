import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ProductEconomicsSection } from '@/components/ProductEconomicsSection';
import { CollectionsWorkspace } from '@/components/CollectionsWorkspace';
import { CompareModal } from '@/components/CompareModal';
import * as api from '@/lib/api';
import type {
  EconomicsScenario,
  Collection,
  CollectionItem,
  CompareResponse,
  ComparedProduct,
} from '@/types';

vi.mock('@/lib/api');

const mockScenario1: EconomicsScenario = {
  id: 1,
  product_id: 101,
  name: 'Kịch bản cơ sở',
  commission_rate_bps: 1000, // 10.00%
  commission_base_vnd: 200_000,
  commission_base_source: 'observed_price_proxy',
  commission_base_observed_at: '2026-10-06T10:00:00Z',
  sample_cost_vnd: 50_000,
  content_cost_vnd: 150_000,
  promotion_cost_vnd: 100_000,
  variable_cost_per_attributed_order_vnd: 5_000,
  expected_attributed_orders: 50,
  is_default: true,
  created_at: '2026-10-06T10:00:00Z',
  updated_at: '2026-10-06T10:00:00Z',
  derived: {
    commission_per_order_vnd: 20_000,
    fixed_campaign_cost_vnd: 300_000,
    contribution_per_order_vnd: 15_000,
    break_even_orders: 20,
    expected_commission_vnd: 1_000_000,
    expected_variable_cost_vnd: 250_000,
    expected_contribution_vnd: 450_000,
    return_on_cost_ratio: 0.8182,
  },
};

const mockScenario2: EconomicsScenario = {
  id: 2,
  product_id: 101,
  name: 'Kịch bản độc quyền',
  commission_rate_bps: 1500, // 15.00%
  commission_base_vnd: 220_000,
  commission_base_source: 'user_entered',
  commission_base_observed_at: null,
  sample_cost_vnd: 0,
  content_cost_vnd: 100_000,
  promotion_cost_vnd: 50_000,
  variable_cost_per_attributed_order_vnd: 3_000,
  expected_attributed_orders: null,
  is_default: false,
  created_at: '2026-10-06T11:00:00Z',
  updated_at: '2026-10-06T11:00:00Z',
  derived: {
    commission_per_order_vnd: 33_000,
    fixed_campaign_cost_vnd: 150_000,
    contribution_per_order_vnd: 30_000,
    break_even_orders: 5,
    expected_commission_vnd: null,
    expected_variable_cost_vnd: null,
    expected_contribution_vnd: null,
    return_on_cost_ratio: null,
  },
};

describe('Phase 6 — Product Economics Section Frontend (P6-AC-32)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.fetchProductEconomicsScenarios).mockResolvedValue([mockScenario1, mockScenario2]);
  });

  it('renders scenarios, default star badge, provenance badges, and disclaimer banner', async () => {
    render(
      <ProductEconomicsSection
        productId={101}
        productTitle="Tai nghe Bluetooth Pro"
        latestPriceVnd={200_000}
      />
    );

    // Section title
    expect(await screen.findByText(/Kế hoạch Kinh tế Affiliate/)).toBeInTheDocument();

    // Commercial disclaimer banner
    expect(
      screen.getByText(/Lưu ý thương mại:/)
    ).toBeInTheDocument();

    // Tabs for scenarios
    expect(screen.getAllByText('Kịch bản cơ sở').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Kịch bản độc quyền')).toBeInTheDocument();

    // Provenance badge for scenario 1 (observed price proxy)
    expect(screen.getByText(/Giá sàn đóng băng/)).toBeInTheDocument();

    // Unit economics metrics
    expect(screen.getByText('20.000 ₫')).toBeInTheDocument(); // commission/order
    expect(screen.getByText('15.000 ₫')).toBeInTheDocument(); // contribution/order
    expect(screen.getByText('20 đơn')).toBeInTheDocument(); // break even orders
  });

  it('handles empty state when product has no scenarios', async () => {
    vi.mocked(api.fetchProductEconomicsScenarios).mockResolvedValue([]);

    render(
      <ProductEconomicsSection
        productId={102}
        productTitle="Sản phẩm chưa có kịch bản"
      />
    );

    expect(
      await screen.findByText('Sản phẩm này chưa có kịch bản kinh tế nào.')
    ).toBeInTheDocument();
    expect(screen.getByText('Tạo kịch bản đầu tiên')).toBeInTheDocument();
  });

  it('switches between scenarios on tab click', async () => {
    render(
      <ProductEconomicsSection
        productId={101}
        productTitle="Tai nghe Bluetooth Pro"
      />
    );

    expect((await screen.findAllByText('Kịch bản cơ sở')).length).toBeGreaterThanOrEqual(1);

    // Click on Scenario 2
    fireEvent.click(screen.getByText('Kịch bản độc quyền'));

    // Should display scenario 2 metrics
    expect(await screen.findByText('Giả định người dùng')).toBeInTheDocument();
    expect(screen.getByText('33.000 ₫')).toBeInTheDocument();
    expect(screen.getByText('5 đơn')).toBeInTheDocument();
  });

  it('allows promoting non-default scenario to default', async () => {
    vi.mocked(api.setDefaultEconomicsScenario).mockResolvedValue({
      ...mockScenario2,
      is_default: true,
    });

    render(
      <ProductEconomicsSection
        productId={101}
        productTitle="Tai nghe Bluetooth Pro"
      />
    );

    // Switch to Scenario 2 (non-default)
    expect((await screen.findAllByText('Kịch bản cơ sở')).length).toBeGreaterThanOrEqual(1);
    fireEvent.click(screen.getByText('Kịch bản độc quyền'));

    // Click "Đặt mặc định"
    const setDefaultBtn = screen.getByText('Đặt mặc định');
    fireEvent.click(setDefaultBtn);

    await waitFor(() => {
      expect(api.setDefaultEconomicsScenario).toHaveBeenCalledWith(101, 2);
    });
  });
});

describe('Phase 6 — Collections & Compare Integration (P6-AC-33, P6-AC-34)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders default economics summary columns in CollectionsWorkspace (P6-AC-33)', async () => {
    const mockCollection: Collection = {
      id: 1,
      name: 'BST Tiềm năng',
      created_at: '2026-10-06T10:00:00Z',
      updated_at: '2026-10-06T10:00:00Z',
    };

    const mockItems: CollectionItem[] = [
      {
        id: 10,
        collection_id: 1,
        product_id: 101,
        review_status: 'candidate',
        added_at: '2026-10-06T10:00:00Z',
        updated_at: '2026-10-06T10:00:00Z',
        product: {
          id: 101,
          platform: 'tiktok',
          external_product_id: 'ext_101',
          title: 'Sản phẩm có kịch bản',
          created_at: '2026-10-01T00:00:00Z',
          updated_at: '2026-10-01T00:00:00Z',
          first_seen_at: '2026-10-01T00:00:00Z',
          last_seen_at: '2026-10-06T10:00:00Z',
        },
        default_economics: mockScenario1,
      },
      {
        id: 11,
        collection_id: 1,
        product_id: 102,
        review_status: 'new',
        added_at: '2026-10-06T10:00:00Z',
        updated_at: '2026-10-06T10:00:00Z',
        product: {
          id: 102,
          platform: 'tiktok',
          external_product_id: 'ext_102',
          title: 'Sản phẩm không có kịch bản',
          created_at: '2026-10-01T00:00:00Z',
          updated_at: '2026-10-01T00:00:00Z',
          first_seen_at: '2026-10-01T00:00:00Z',
          last_seen_at: '2026-10-06T10:00:00Z',
        },
        default_economics: null,
      },
    ];

    vi.mocked(api.fetchCollections).mockResolvedValue([mockCollection]);
    vi.mocked(api.fetchCollectionMembers).mockResolvedValue(mockItems);

    render(<CollectionsWorkspace />);

    // Check table headers
    expect(await screen.findByText('Hoa hồng/đơn')).toBeInTheDocument();
    expect(screen.getByText('Đóng góp/đơn')).toBeInTheDocument();
    expect(screen.getByText('Đơn hòa vốn')).toBeInTheDocument();

    // Check row 1 with default economics
    expect(screen.getByText('20.000 ₫')).toBeInTheDocument();
    expect(screen.getByText('15.000 ₫')).toBeInTheDocument();
    expect(screen.getByText('20 đơn')).toBeInTheDocument();

    // Check row 2 displays '—' for missing economics
    const dashes = screen.getAllByText('—');
    expect(dashes.length).toBeGreaterThanOrEqual(3);
  });

  it('renders default economics comparison rows in CompareModal (P6-AC-34)', async () => {
    const mockCompareResponse: CompareResponse = {
      as_of_utc: '2026-10-06T12:00:00Z',
      products: [
        {
          product_id: 101,
          external_product_id: 'ext_101',
          title: 'Sản phẩm A',
          first_seen_at: '2026-10-01T00:00:00Z',
          last_seen_at: '2026-10-06T12:00:00Z',
          is_watched: true,
          trend_score: 85,
          trend_state: 'trending',
          reasons: [],
          velocity_is_estimated: false,
          recent_alert_count_7d: 1,
          default_economics: mockScenario1,
        },
        {
          product_id: 102,
          external_product_id: 'ext_102',
          title: 'Sản phẩm B',
          first_seen_at: '2026-10-01T00:00:00Z',
          last_seen_at: '2026-10-06T12:00:00Z',
          is_watched: false,
          trend_score: 70,
          trend_state: 'eligible',
          reasons: [],
          velocity_is_estimated: false,
          recent_alert_count_7d: 0,
          default_economics: null,
        },
      ],
    };

    vi.mocked(api.compareProducts).mockResolvedValue(mockCompareResponse);

    render(
      <CompareModal
        productIds={[101, 102]}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    // Section header
    expect(await screen.findByText('Kinh tế Affiliate (Kịch bản mặc định)')).toBeInTheDocument();

    // Product A default scenario name
    expect(screen.getByText('Kịch bản cơ sở')).toBeInTheDocument();
    expect(screen.getByText('10.00%')).toBeInTheDocument();

    // Product A unit economics
    expect(screen.getByText('20.000 ₫')).toBeInTheDocument();
    expect(screen.getByText('15.000 ₫')).toBeInTheDocument();
    expect(screen.getByText('20 đơn')).toBeInTheDocument();

    // Clean empty indicators for Product B
    const emptyIndicators = screen.getAllByText('—');
    expect(emptyIndicators.length).toBeGreaterThanOrEqual(5);
  });
});
