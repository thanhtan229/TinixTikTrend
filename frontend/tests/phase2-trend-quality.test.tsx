import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { EvidenceBadge } from '@/components/EvidenceBadge';
import { ProductCard } from '@/components/ProductCard';
import { fetchTrends } from '@/lib/api';
import type { TrendEvidence, TrendMetrics, TrendReason } from '@/types';


describe('Phase 2 EvidenceBadge Component', () => {
  it('renders High confidence correctly', () => {
    const evidence: TrendEvidence = {
      observation_count: 6,
      observation_span_hours: 24.5,
      latest_observation_age_hours: 1.2,
      ranking_state: 'eligible',
      confidence: 'high',
      primary_signal_interval: { elapsed_hours: 24.1, is_estimated: false },
      signals: { sales_velocity: 'measured', sales_acceleration: 'measured', review_velocity: 'measured' },
      has_24h_window: true,
      has_7d_window: false,
      missing_metrics: [],
    };

    render(<EvidenceBadge evidence={evidence} />);
    expect(screen.getByText('Tin cậy Cao')).toBeInTheDocument();
  });

  it('renders Medium confidence correctly', () => {
    const evidence: TrendEvidence = {
      observation_count: 3,
      observation_span_hours: 10.0,
      latest_observation_age_hours: 2.0,
      ranking_state: 'eligible',
      confidence: 'medium',
      primary_signal_interval: { elapsed_hours: 6.0, is_estimated: true },
      signals: { sales_velocity: 'estimated', sales_acceleration: 'missing', review_velocity: 'missing' },
      has_24h_window: false,
      has_7d_window: false,
      missing_metrics: ['sales_acceleration', 'review_delta_24h'],
    };

    render(<EvidenceBadge evidence={evidence} />);
    expect(screen.getByText('Tin cậy Vừa')).toBeInTheDocument();
  });

  it('renders Stale data warning when state is stale', () => {
    const evidence: TrendEvidence = {
      observation_count: 3,
      observation_span_hours: 12.0,
      latest_observation_age_hours: 9.5,
      ranking_state: 'stale',
      confidence: 'low',
      primary_signal_interval: null,
      signals: { sales_velocity: 'missing', sales_acceleration: 'missing', review_velocity: 'missing' },
      has_24h_window: false,
      has_7d_window: false,
      missing_metrics: [],
    };

    render(<EvidenceBadge evidence={evidence} />);
    expect(screen.getByText(/Dữ liệu cũ/)).toBeInTheDocument();
  });

  it('renders Insufficient signal warning when not enough intervals', () => {
    const evidence: TrendEvidence = {
      observation_count: 1,
      observation_span_hours: 0.0,
      latest_observation_age_hours: 0.5,
      ranking_state: 'insufficient_measured_signal',
      confidence: 'low',
      primary_signal_interval: null,
      signals: { sales_velocity: 'missing', sales_acceleration: 'missing', review_velocity: 'missing' },
      has_24h_window: false,
      has_7d_window: false,
      missing_metrics: [],
    };

    render(<EvidenceBadge evidence={evidence} />);
    expect(screen.getByText('Chờ thêm dữ liệu')).toBeInTheDocument();
  });
});

describe('Phase 2 ProductCard with Reasons & Evidence', () => {
  it('renders deterministic why-trending reasons in ProductCard', () => {
    const reasons: TrendReason[] = [
      {
        reason_code: 'sales_velocity_up',
        contribution: 28.5,
        value: 120.0,
        formatted_text: 'Tăng +120 đơn trong ~24h (đo lường 24.1h)',
      },
      {
        reason_code: 'sales_acceleration_up',
        contribution: 8.2,
        value: 35.0,
        formatted_text: 'Gia tốc bán hàng tăng +35 đơn/ngày so với chu kỳ trước',
      },
    ];

    const productWithReasons: TrendMetrics = {
      product_id: 101,
      external_product_id: 'ext_101',
      title: 'Áo thun nam trending',
      category: 'Thời trang & Phụ kiện',
      first_seen_at: '2026-10-01T10:00:00Z',
      last_seen_at: '2026-10-05T10:00:00Z',
      trend_score: 82.5,
      deltas: {
        latest_price: 150000,
        latest_sold_count: 520,
        sold_delta_24h: 120,
        sales_velocity_24h: 120,
        sales_acceleration: 35,
      },
      evidence: {
        observation_count: 6,
        observation_span_hours: 24.5,
        latest_observation_age_hours: 1.0,
        ranking_state: 'eligible',
        confidence: 'high',
        primary_signal_interval: { elapsed_hours: 24.1, is_estimated: false },
        signals: { sales_velocity: 'measured', sales_acceleration: 'measured', review_velocity: 'missing' },
        has_24h_window: true,
        has_7d_window: false,
        missing_metrics: ['review_delta_24h'],
      },
      reasons,
    };

    render(<ProductCard product={productWithReasons} rank={1} />);

    expect(screen.getByText('Tin cậy Cao')).toBeInTheDocument();
    expect(screen.getByText('Lý do xu hướng')).toBeInTheDocument();
    expect(screen.getByText('Tăng +120 đơn trong ~24h (đo lường 24.1h)')).toBeInTheDocument();
    expect(screen.getByText('Gia tốc bán hàng tăng +35 đơn/ngày so với chu kỳ trước')).toBeInTheDocument();
  });
});

describe('Phase 2 API Client Filter & Sort Query Construction', () => {
  it('constructs correct query parameters with category and trend controls', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    });
    const originalFetch = global.fetch;
    global.fetch = fetchMock;

    try {
      await fetchTrends('trending', {
        category: 'Thời trang & Phụ kiện',
        trend_state: 'eligible',
        confidence: 'high',
        evidence: 'measured_only',
        sort_by: 'sales_velocity',
        order: 'desc',
      });

      expect(fetchMock).toHaveBeenCalledOnce();
      const calledUrl = fetchMock.mock.calls[0][0] as string;
      expect(calledUrl).toContain('/trends?');
      expect(calledUrl).toContain('category=Th%E1%BB%9Di+trang+%26+Ph%E1%BB%A5+ki%E1%BB%87n');
      expect(calledUrl).toContain('trend_state=eligible');
      expect(calledUrl).toContain('confidence=high');
      expect(calledUrl).toContain('evidence=measured_only');
      expect(calledUrl).toContain('sort_by=sales_velocity');
      expect(calledUrl).toContain('order=desc');
    } finally {
      global.fetch = originalFetch;
    }
  });

  it('omits empty or undefined category filter', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    });
    const originalFetch = global.fetch;
    global.fetch = fetchMock;

    try {
      await fetchTrends('trending', {
        category: undefined,
        sort_by: 'trend_score',
      });

      expect(fetchMock).toHaveBeenCalledOnce();
      const calledUrl = fetchMock.mock.calls[0][0] as string;
      expect(calledUrl).not.toContain('category=');
      expect(calledUrl).toContain('sort_by=trend_score');
    } finally {
      global.fetch = originalFetch;
    }
  });
});

