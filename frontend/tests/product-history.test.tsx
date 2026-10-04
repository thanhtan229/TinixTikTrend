import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ProductHistory } from '@/components/ProductHistory';
import { ProductSnapshot } from '@/types';

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  LineChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
  CartesianGrid: () => null,
}));

const now = Date.now();
const snapshots: ProductSnapshot[] = [
  { id: 1, product_id: 21, captured_at: new Date(now - 60_000).toISOString(), sold_count: 0, review_count: 0, rating: 0, price: 0, commission_rate: 0 },
  { id: 2, product_id: 21, captured_at: new Date(now - 2 * 86400_000).toISOString(), sold_count: 10, review_count: 2, rating: 4, price: 100 },
  { id: 3, product_id: 21, captured_at: new Date(now - 10 * 86400_000).toISOString(), sold_count: 50, review_count: 8, rating: 4.5, price: 200 },
  { id: 4, product_id: 21, captured_at: new Date(now - 40 * 86400_000).toISOString(), sold_count: 100, review_count: 20, rating: 5, price: 300 },
];

describe('product history', () => {
  it('filters actual timestamps by the selected history window', () => {
    render(<ProductHistory snapshots={snapshots} />);
    expect(screen.getByText('Lịch sử sản phẩm (1 snapshots)')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '7d' }));
    expect(screen.getByText('Lịch sử sản phẩm (2 snapshots)')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '30d' }));
    expect(screen.getByText('Lịch sử sản phẩm (3 snapshots)')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Tất cả' }));
    expect(screen.getByText('Lịch sử sản phẩm (4 snapshots)')).toBeInTheDocument();
  });

  it('shows verified zeros as zero and explicitly reports an empty window', () => {
    const { rerender } = render(<ProductHistory snapshots={snapshots} />);
    expect(screen.getAllByText('0').length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText(value => value.includes('0') && value.includes('₫'))).toBeInTheDocument();
    rerender(<ProductHistory snapshots={[]} />);
    expect(screen.getByText('Chưa có snapshot trong khoảng thời gian này.')).toBeInTheDocument();
  });
});
