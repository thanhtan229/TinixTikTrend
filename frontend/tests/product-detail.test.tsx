import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import ProductDetailPage from '@/app/products/[id]/page';
import { fetchProductDetail } from '@/lib/api';

vi.mock('next/navigation', () => ({ useParams: () => ({ id: '21' }), useRouter: () => ({ push: vi.fn() }) }));
vi.mock('@/lib/api', () => ({ fetchProductDetail: vi.fn() }));
vi.mock('@/components/ScoreBadge', () => ({ ScoreBadge: ({ score }: { score: number }) => <span>Score {score}</span> }));

const product = {
  id: 21,
  platform: 'tiktok_shop',
  external_product_id: '1737036472084039604',
  title: 'Sản phẩm kiểm thử',
  url: null,
  image_url: null,
  shop_id: null,
  shop_name: 'Shop test',
  category: null,
  first_seen_at: '2026-10-03T10:00:00Z',
  last_seen_at: '2026-10-03T10:00:00Z',
  analysis: {
    product_id: 21,
    external_product_id: '1737036472084039604',
    title: 'Sản phẩm kiểm thử',
    first_seen_at: '2026-10-03T10:00:00Z',
    last_seen_at: '2026-10-03T10:00:00Z',
    deltas: {
      latest_rating: 0,
      latest_review_count: 0,
      latest_price: 0,
      sales_velocity_24h: 176.00056432516746,
      velocity_is_estimated: true,
    },
    trend_score: 0,
  },
  snapshots: [],
};

describe('product detail recovery', () => {
  beforeEach(() => vi.resetAllMocks());

  it('retries a failed detail request and preserves verified zero values', async () => {
    vi.mocked(fetchProductDetail).mockRejectedValueOnce(new Error('network lost')).mockResolvedValueOnce(product);
    render(<ProductDetailPage />);
    expect(await screen.findByText('network lost')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Thử tải lại' }));
    expect(await screen.findByRole('heading', { name: 'Sản phẩm kiểm thử' })).toBeInTheDocument();
    expect(screen.getByText('0.00 (0 đánh giá)')).toBeInTheDocument();
    expect(screen.getByText(value => value.includes('0') && value.includes('₫'))).toBeInTheDocument();
    expect(screen.getByText('+176,0')).toBeInTheDocument();
    expect(screen.getByText('Ước tính / ngày từ lịch sử hiện có')).toBeInTheDocument();
    await waitFor(() => expect(fetchProductDetail).toHaveBeenCalledTimes(2));
  });

  it('shows negative estimated sales and review deltas with a single minus sign', async () => {
    const decliningProduct = {
      ...product,
      analysis: {
        ...product.analysis,
        deltas: {
          ...product.analysis.deltas,
          sales_velocity_24h: -3.5,
          review_delta_24h: -2,
        },
      },
    };
    vi.mocked(fetchProductDetail).mockResolvedValue(decliningProduct);
    render(<ProductDetailPage />);

    expect(await screen.findByRole('heading', { name: 'Sản phẩm kiểm thử' })).toBeInTheDocument();
    expect(screen.getByText('-3,5')).toBeInTheDocument();
    expect(screen.getByText('-2')).toBeInTheDocument();
    expect(screen.queryByText('+-3,5')).not.toBeInTheDocument();
  });
});
