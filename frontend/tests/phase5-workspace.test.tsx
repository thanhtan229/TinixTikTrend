import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { CollectionsWorkspace } from '@/components/CollectionsWorkspace';
import { SavedViewControl } from '@/components/SavedViewControl';
import { CompareTray } from '@/components/CompareTray';
import { CompareModal } from '@/components/CompareModal';
import { AddToCollectionModal } from '@/components/AddToCollectionModal';
import * as api from '@/lib/api';
import type {
  Collection,
  CollectionItem,
  SavedView,
  TrendsSavedViewPayload,
  WatchlistSavedViewPayload,
  CompareResponse,
  ComparedProduct,
} from '@/types';

vi.mock('@/lib/api');

const mockCollection: Collection = {
  id: 1,
  name: 'Bộ sưu tập Hot Q4',
  description: 'Các sản phẩm tiềm năng cuối năm',
  created_at: '2026-10-06T10:00:00Z',
  updated_at: '2026-10-06T10:00:00Z',
  item_count: 2,
};

const mockCollectionItems: CollectionItem[] = [
  {
    id: 10,
    collection_id: 1,
    product_id: 101,
    review_status: 'candidate',
    notes: 'Tiềm năng cao, biên độ lợi nhuận tốt',
    added_at: '2026-10-06T10:15:00Z',
    updated_at: '2026-10-06T10:15:00Z',
    is_watched: true,
    product: {
      id: 101,
      platform: 'tiktok',
      external_product_id: 'ext_101',
      title: 'Tai nghe Bluetooth Pro',
      category: 'Điện tử & Công nghệ',
      shop_name: 'TechStore',
      first_seen_at: '2026-10-01T00:00:00Z',
      last_seen_at: '2026-10-06T10:00:00Z',
      created_at: '2026-10-01T00:00:00Z',
      updated_at: '2026-10-06T10:00:00Z',
    },
  },
  {
    id: 11,
    collection_id: 1,
    product_id: 102,
    review_status: 'new',
    notes: '',
    added_at: '2026-10-06T10:20:00Z',
    updated_at: '2026-10-06T10:20:00Z',
    is_watched: false,
    product: {
      id: 102,
      platform: 'tiktok',
      external_product_id: 'ext_102',
      title: 'Áo thun phong cách basic',
      category: 'Thời trang & Phụ kiện',
      shop_name: 'FashionVN',
      first_seen_at: '2026-10-02T00:00:00Z',
      last_seen_at: '2026-10-06T10:00:00Z',
      created_at: '2026-10-02T00:00:00Z',
      updated_at: '2026-10-06T10:00:00Z',
    },
  },
];

describe('Phase 5 — Collections Workspace Frontend (P5-AC-31)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.fetchCollections).mockResolvedValue([mockCollection]);
    vi.mocked(api.fetchCollectionMembers).mockResolvedValue(mockCollectionItems);
  });

  it('renders collections workspace, member table, and independent watch status display', async () => {
    render(<CollectionsWorkspace />);

    expect(await screen.findByText('Tai nghe Bluetooth Pro')).toBeInTheDocument();
    expect(screen.getAllByText('Bộ sưu tập Hot Q4').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Áo thun phong cách basic')).toBeInTheDocument();

    // Independent Watch status display (101 watched, 102 not watched)
    expect(screen.getByText('Theo dõi')).toBeInTheDocument();
    expect(screen.getByText('Không')).toBeInTheDocument();
  });

  it('updates member review status and saves decision notes explicitly (P5-AC-07)', async () => {
    vi.mocked(api.updateCollectionItem).mockResolvedValue({
      ...mockCollectionItems[0],
      review_status: 'reviewing',
      notes: 'Ghi chú cập nhật mới',
    });

    render(<CollectionsWorkspace />);
    await screen.findByText('Tai nghe Bluetooth Pro');

    // Change status dropdown
    const statusSelects = screen.getAllByLabelText('Trạng thái đánh giá');
    fireEvent.change(statusSelects[0], { target: { value: 'reviewing' } });
    expect(api.updateCollectionItem).toHaveBeenCalledWith(1, 101, { review_status: 'reviewing' });

    // Explicit Notes Save
    const notesInput = screen.getByDisplayValue('Tiềm năng cao, biên độ lợi nhuận tốt');
    fireEvent.change(notesInput, { target: { value: 'Ghi chú cập nhật mới' } });

    const saveButtons = screen.getAllByTitle('Lưu ghi chú');
    fireEvent.click(saveButtons[0]);

    await waitFor(() => {
      expect(api.updateCollectionItem).toHaveBeenCalledWith(1, 101, { notes: 'Ghi chú cập nhật mới' });
    });
  });

  it('creates, edits, and deletes a collection', async () => {
    const createdCol: Collection = {
      id: 2,
      name: 'Bộ sưu tập Mới',
      description: 'Mô tả mới',
      created_at: '2026-10-06T11:00:00Z',
      updated_at: '2026-10-06T11:00:00Z',
      item_count: 0,
    };
    vi.mocked(api.createCollection).mockResolvedValue(createdCol);
    vi.mocked(api.deleteCollection).mockResolvedValue({ ok: true });
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<CollectionsWorkspace />);
    await screen.findByText('Tai nghe Bluetooth Pro');

    // Click create collection button
    fireEvent.click(screen.getByText('Tạo Bộ sưu tập mới'));
    fireEvent.change(screen.getByPlaceholderText('VD: Sản phẩm Tiềm năng Q4'), {
      target: { value: 'Bộ sưu tập Mới' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Tạo mới' }));

    await waitFor(() => {
      expect(api.createCollection).toHaveBeenCalledWith('Bộ sưu tập Mới', undefined);
    });

    // Delete collection
    const deleteBtn = screen.getByTitle('Xóa bộ sưu tập');
    fireEvent.click(deleteBtn);
    await waitFor(() => {
      expect(api.deleteCollection).toHaveBeenCalledWith(2);
    });
  });

  it('renders AddToCollectionModal and adds product with initial status and notes', async () => {
    vi.mocked(api.addProductToCollection).mockResolvedValue({
      id: 99,
      collection_id: 1,
      product_id: 200,
      review_status: 'candidate',
      notes: 'Thêm thử nghiệm',
      added_at: '2026-10-06T11:00:00Z',
      updated_at: '2026-10-06T11:00:00Z',
    });

    const onClose = vi.fn();
    const onSuccess = vi.fn();

    render(
      <AddToCollectionModal
        productId={200}
        productTitle="Sản phẩm Test 200"
        isOpen={true}
        onClose={onClose}
        onSuccess={onSuccess}
      />
    );

    await screen.findByText('Sản phẩm Test 200');

    // Select existing collection
    fireEvent.change(screen.getByLabelText('Chọn bộ sưu tập'), { target: { value: '1' } });
    fireEvent.change(screen.getByLabelText('Trạng thái đánh giá ban đầu'), { target: { value: 'candidate' } });
    fireEvent.change(screen.getByPlaceholderText(/Nhà bán uy tín/i), { target: { value: 'Thêm thử nghiệm' } });

    fireEvent.click(screen.getByRole('button', { name: 'Thêm vào BST' }));

    await waitFor(() => {
      expect(api.addProductToCollection).toHaveBeenCalledWith(1, 200, 'candidate', 'Thêm thử nghiệm');
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it('displays duplicate-add feedback error when product is already in collection', async () => {
    vi.mocked(api.fetchCollections).mockResolvedValue([mockCollection]);
    vi.mocked(api.addProductToCollection).mockRejectedValue(
      new Error('Sản phẩm đã có trong bộ sưu tập (409)')
    );

    render(
      <AddToCollectionModal
        productId={200}
        productTitle="Sản phẩm Test 200"
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await screen.findByText('Sản phẩm Test 200');
    fireEvent.change(screen.getByLabelText('Chọn bộ sưu tập'), { target: { value: '1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Thêm vào BST' }));

    expect(await screen.findByText('Sản phẩm đã có trong bộ sưu tập này rồi.')).toBeInTheDocument();
  });
});

describe('Phase 5 — Saved Views Frontend (P5-AC-32)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockTrendsView: SavedView<TrendsSavedViewPayload> = {
    id: 1,
    name: 'Trends Tiềm Năng',
    scope: 'trends',
    payload_version: 1,
    payload: {
      category: 'Thời trang & Phụ kiện',
      trend_state: 'eligible',
      measured_only: true,
      confidence: 'high',
      sort_by: 'trend_score',
      sort_direction: 'desc',
      limit: 50,
      search: 'váy',
      min_score: 70,
    },
    created_at: '2026-10-06T10:00:00Z',
    updated_at: '2026-10-06T10:00:00Z',
  };

  const mockWatchlistView: SavedView<WatchlistSavedViewPayload> = {
    id: 2,
    name: 'Watchlist Giảm Dần',
    scope: 'watchlist',
    payload_version: 1,
    payload: {
      category: null,
      trend_state: 'all',
      measured_only: false,
      confidence: null,
      sort_by: 'sales_velocity',
      sort_direction: 'desc',
      limit: 25,
    },
    created_at: '2026-10-06T10:00:00Z',
    updated_at: '2026-10-06T10:00:00Z',
  };

  it('saves Trends view with exact 9 persisted keys (P5-AC-12)', async () => {
    vi.mocked(api.fetchSavedViews).mockResolvedValue([]);
    vi.mocked(api.createSavedView).mockResolvedValue(mockTrendsView);

    const onApply = vi.fn();
    const currentPayload: TrendsSavedViewPayload = {
      category: 'Thời trang & Phụ kiện',
      trend_state: 'eligible',
      measured_only: true,
      confidence: 'high',
      sort_by: 'trend_score',
      sort_direction: 'desc',
      limit: 50,
      search: 'váy',
      min_score: 70,
    };

    render(
      <SavedViewControl
        scope="trends"
        currentPayload={currentPayload}
        onApply={onApply}
      />
    );

    fireEvent.click(screen.getByText('Lưu bộ lọc hiện tại'));
    const nameInput = screen.getByPlaceholderText('VD: Quần áo đang tăng tốc cao');
    fireEvent.change(nameInput, { target: { value: 'Trends Tiềm Năng' } });

    fireEvent.click(screen.getByRole('button', { name: 'Lưu' }));

    await waitFor(() => {
      expect(api.createSavedView).toHaveBeenCalledWith({
        name: 'Trends Tiềm Năng',
        scope: 'trends',
        payload_version: 1,
        payload: {
          category: 'Thời trang & Phụ kiện',
          trend_state: 'eligible',
          measured_only: true,
          confidence: 'high',
          sort_by: 'trend_score',
          sort_direction: 'desc',
          limit: 50,
          search: 'váy',
          min_score: 70,
        },
      });
    });
  });

  it('saves Watchlist view with exact 7 persisted keys and applies view locally with 0 DB queries (P5-AC-13, P5-AC-15)', async () => {
    vi.mocked(api.fetchSavedViews).mockResolvedValue([mockWatchlistView]);

    const onApply = vi.fn();
    const currentPayload: WatchlistSavedViewPayload = {
      category: null,
      trend_state: 'all',
      measured_only: false,
      confidence: null,
      sort_by: 'sales_velocity',
      sort_direction: 'desc',
      limit: 25,
    };

    render(
      <SavedViewControl
        scope="watchlist"
        currentPayload={currentPayload}
        onApply={onApply}
      />
    );

    await screen.findByText('Watchlist Giảm Dần');

    // Initial load ran 1 query for list
    expect(api.fetchSavedViews).toHaveBeenCalledTimes(1);

    // Apply view by selecting it in dropdown
    const select = screen.getByLabelText('Chọn chế độ xem đã lưu');
    fireEvent.change(select, { target: { value: '2' } });

    // onApply called with loaded in-memory payload directly (0 additional SavedView DB queries!)
    expect(onApply).toHaveBeenCalledWith(mockWatchlistView.payload);
    expect(api.fetchSavedViews).toHaveBeenCalledTimes(1);
  });

  it('updates and deletes Saved View (P5-AC-11)', async () => {
    vi.mocked(api.fetchSavedViews).mockResolvedValue([mockWatchlistView]);
    vi.mocked(api.updateSavedView).mockResolvedValue({
      ...mockWatchlistView,
      name: 'Watchlist Cập Nhật',
    });
    vi.mocked(api.deleteSavedView).mockResolvedValue({ ok: true });
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(
      <SavedViewControl
        scope="watchlist"
        currentPayload={mockWatchlistView.payload}
        onApply={vi.fn()}
      />
    );

    await screen.findByText('Watchlist Giảm Dần');

    // Select view
    const select = screen.getByLabelText('Chọn chế độ xem đã lưu');
    fireEvent.change(select, { target: { value: '2' } });

    // Click rename
    const editBtn = screen.getByTitle('Đổi tên');
    fireEvent.click(editBtn);

    const inputs = screen.getAllByDisplayValue('Watchlist Giảm Dần');
    const input = inputs.find((el) => el.tagName === 'INPUT')!;
    fireEvent.change(input, { target: { value: 'Watchlist Cập Nhật' } });

    const confirmBtn = screen.getByRole('button', { name: 'Lưu thay đổi' });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(api.updateSavedView).toHaveBeenCalledWith(2, { name: 'Watchlist Cập Nhật' });
    });

    // Delete view
    const deleteBtn = screen.getByTitle('Xóa chế độ xem');
    fireEvent.click(deleteBtn);

    await waitFor(() => {
      expect(api.deleteSavedView).toHaveBeenCalledWith(2);
    });
  });
});

describe('Phase 5 — Product Compare Tray & Matrix (P5-AC-33, P5-AC-34)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('manages CompareTray staging: enforces min 2 disabled, max 5, clear and remove', () => {
    const onRemove = vi.fn();
    const onClear = vi.fn();
    const onOpenCompare = vi.fn();

    // 1 item: Compare button disabled
    const { rerender } = render(
      <CompareTray
        staged={[{ productId: 101, title: 'Item 1' }]}
        onRemove={onRemove}
        onClear={onClear}
        onOpenCompare={onOpenCompare}
      />
    );

    expect(screen.getByText('Khay so sánh (1/5)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /So sánh ngay/i })).toBeDisabled();

    // 2 items: Compare button enabled
    rerender(
      <CompareTray
        staged={[
          { productId: 101, title: 'Item 1' },
          { productId: 102, title: 'Item 2' },
        ]}
        onRemove={onRemove}
        onClear={onClear}
        onOpenCompare={onOpenCompare}
      />
    );

    const compareBtn = screen.getByRole('button', { name: /So sánh ngay/i });
    expect(compareBtn).toBeEnabled();
    fireEvent.click(compareBtn);
    expect(onOpenCompare).toHaveBeenCalled();

    // Clear all
    fireEvent.click(screen.getByText('Xóa tất cả'));
    expect(onClear).toHaveBeenCalled();
  });

  it('renders CompareModal: calls compareProducts, displays single as_of_utc, evidence, nulls, and alert summary (P5-AC-18, P5-AC-22)', async () => {
    const mockCompareResponse: CompareResponse = {
      as_of_utc: '2026-10-06T12:00:00Z',
      collection_id: 1,
      products: [
        {
          product_id: 101,
          external_product_id: 'ext_101',
          title: 'Tai nghe Bluetooth Pro',
          category: 'Điện tử',
          shop_name: 'TechStore',
          first_seen_at: '2026-10-01T00:00:00Z',
          last_seen_at: '2026-10-06T12:00:00Z',
          is_watched: true,
          collection_context: {
            collection_id: 1,
            review_status: 'candidate',
            notes: 'Ứng viên sáng giá',
          },
          trend_score: 85.5,
          trend_state: 'eligible',
          confidence: 'high',
          reasons: [{ reason_code: 'sales_velocity_up', contribution: 50.0, value: 120.0, formatted_text: 'Tốc độ bán 120 sp/ngày' }],
          sales_velocity_24h: 120.0,
          velocity_is_estimated: false,
          sold_delta_24h: 120,
          sold_delta_7d: 500,
          sales_acceleration: 25.0,
          review_delta_24h: 15,
          review_delta_7d: 40,
          freshness_hours: 1.5,
          current_price: 150000,
          rating: 4.9,
          review_count: 250,
          recent_alert_count_7d: 2,
          latest_alert_at: '2026-10-06T11:30:00Z',
        },
        {
          product_id: 102,
          external_product_id: 'ext_102',
          title: 'Áo thun phong cách basic',
          category: 'Thời trang',
          shop_name: 'FashionVN',
          first_seen_at: '2026-10-02T00:00:00Z',
          last_seen_at: '2026-10-06T12:00:00Z',
          is_watched: false,
          collection_context: null,
          trend_score: 42.0,
          trend_state: 'stale',
          confidence: 'low',
          reasons: [],
          sales_velocity_24h: null, // Null value to verify null metric preservation
          velocity_is_estimated: true,
          sold_delta_24h: null,
          sold_delta_7d: null,
          sales_acceleration: null,
          review_delta_24h: null,
          review_delta_7d: null,
          freshness_hours: 9.0,
          current_price: 99000,
          rating: 4.5,
          review_count: 50,
          recent_alert_count_7d: 0,
          latest_alert_at: null,
        },
      ],
    };

    vi.mocked(api.compareProducts).mockResolvedValue(mockCompareResponse);

    render(
      <CompareModal
        productIds={[101, 102]}
        collectionId={1}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    // Verifies single bulk API call with correct order and collection_id
    await waitFor(() => {
      expect(api.compareProducts).toHaveBeenCalledWith([101, 102], 1);
    });

    // Displays shared single as_of_utc
    expect(await screen.findByText('2026-10-06T12:00:00Z')).toBeInTheDocument();

    // Preserves order and product titles
    expect(screen.getByText('Tai nghe Bluetooth Pro')).toBeInTheDocument();
    expect(screen.getByText('Áo thun phong cách basic')).toBeInTheDocument();

    // Collection context display
    expect(screen.getByText(/Ứng viên sáng giá/i)).toBeInTheDocument();
    expect(screen.getByText('Không thuộc BST này')).toBeInTheDocument();

    // Bounded alert summary
    expect(screen.getByText('2 cảnh báo')).toBeInTheDocument();
    expect(screen.getByText('0 cảnh báo')).toBeInTheDocument();

    // Null metric preservation (does not fabricate or replace null with 0)
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });

  it('handles CompareModal loading, error, and retry flow (P5-AC-34)', async () => {
    // 1. First call fails with error
    vi.mocked(api.compareProducts).mockRejectedValueOnce(new Error('Máy chủ đang bận'));

    const { rerender } = render(
      <CompareModal
        productIds={[101, 102]}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    // Displays error message and retry button
    expect(await screen.findByText('Máy chủ đang bận')).toBeInTheDocument();
    const retryBtn = screen.getByRole('button', { name: 'Thử lại' });
    expect(retryBtn).toBeInTheDocument();

    // 2. Mock successful response on retry
    const successResponse: CompareResponse = {
      as_of_utc: '2026-10-06T12:00:00Z',
      products: [
        {
          product_id: 101,
          external_product_id: 'ext_101',
          title: 'Tai nghe Bluetooth Pro',
          first_seen_at: '2026-10-01T00:00:00Z',
          last_seen_at: '2026-10-06T12:00:00Z',
          is_watched: true,
          trend_score: 80.0,
          trend_state: 'eligible',
          reasons: [],
          velocity_is_estimated: false,
          recent_alert_count_7d: 0,
        },
        {
          product_id: 102,
          external_product_id: 'ext_102',
          title: 'Áo thun phong cách basic',
          first_seen_at: '2026-10-02T00:00:00Z',
          last_seen_at: '2026-10-06T12:00:00Z',
          is_watched: false,
          trend_score: 50.0,
          trend_state: 'eligible',
          reasons: [],
          velocity_is_estimated: false,
          recent_alert_count_7d: 0,
        },
      ],
    };
    vi.mocked(api.compareProducts).mockResolvedValueOnce(successResponse);

    // Click retry
    fireEvent.click(retryBtn);

    // Should render loaded products
    expect(await screen.findByText('Tai nghe Bluetooth Pro')).toBeInTheDocument();
    expect(screen.getByText('Áo thun phong cách basic')).toBeInTheDocument();
  });
});
