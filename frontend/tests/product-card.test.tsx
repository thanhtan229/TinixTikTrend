import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ProductCard } from '@/components/ProductCard';
import { formatSignedNumber } from '@/lib/utils';
import type { TrendMetrics } from '@/types';

const product: TrendMetrics = {
  product_id: 21,
  external_product_id: '1737036472084039604',
  title: 'Sản phẩm kiểm thử',
  first_seen_at: '2026-10-03T10:00:00Z',
  last_seen_at: '2026-10-03T10:00:00Z',
  trend_score: 0,
  deltas: {
    latest_price: 12000,
    latest_sold_count: 80,
    sold_delta_24h: -3,
    sold_delta_7d: 0,
  },
};

describe('ProductCard delta formatting', () => {
  it('shows negative and zero changes without adding a misleading plus sign', () => {
    render(<ProductCard product={product} />);

    expect(screen.getByText('Chênh lệch 24h').parentElement).toHaveTextContent('Chênh lệch 24h-3');
    expect(screen.getByText('Chênh lệch 7d').parentElement).toHaveTextContent('Chênh lệch 7d0');
    expect(screen.queryByText('+-3')).not.toBeInTheDocument();
  });

  it('formats large positive and negative deltas symmetrically', () => {
    expect(formatSignedNumber(1250)).toBe('+1.3K');
    expect(formatSignedNumber(-1250)).toBe('-1.3K');
  });
});
