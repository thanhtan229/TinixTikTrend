import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { CrawlerControl } from '@/components/CrawlerControl';
import DashboardPage from '@/app/page';
import { fetchCrawlerStatus, triggerCrawlerRun, fetchDashboardSummary, fetchTrends, fetchWatchedProductIds, fetchSavedViews } from '@/lib/api';
vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>();
  return {
    ...actual,
    fetchCrawlerStatus: vi.fn(),
    triggerCrawlerRun: vi.fn(),
    fetchDashboardSummary: vi.fn(),
    fetchTrends: vi.fn(),
    fetchWatchedProductIds: vi.fn().mockResolvedValue([]),
    fetchSavedViews: vi.fn().mockResolvedValue([]),
  };
});
vi.mock('@/components/ProductCard', () => ({ ProductCard: ({ product }: {product:{title:string}}) => <div>{product.title}</div> }));
const idle={ is_running:false,region:'VN',schedule:'08:00',latest_run:null };
const summary={stats:{total_products:1,high_trend_count:0},new_products:[],trending:[],rising:[],best_sellers:[]};
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(fetchCrawlerStatus).mockResolvedValue(idle);
  vi.mocked(fetchWatchedProductIds).mockResolvedValue([]);
  vi.mocked(fetchSavedViews).mockResolvedValue([]);
});
describe('production UI recovery', () => {
  it('refreshes once after a triggered crawl stops and displays failure', async () => {
    const completed=vi.fn();
    vi.mocked(triggerCrawlerRun).mockResolvedValue({status:'triggered'});
    render(<CrawlerControl onCrawlCompleted={completed}/>);
    await waitFor(() => expect(fetchCrawlerStatus).toHaveBeenCalledOnce());
    await waitFor(() => expect(screen.getByText('Lần quét gần nhất:')).toBeInTheDocument());
    vi.mocked(fetchCrawlerStatus).mockResolvedValue({...idle,latest_run:{id:1,started_at:'2026-10-03T01:00:00Z',status:'failed',source:'manual',products_found:0,products_created:0,products_updated:0,snapshots_created:0,error_message:'No verified product'}});
    fireEvent.click(screen.getByRole('button',{name:'Chạy Crawler Ngay'}));
    await waitFor(() => expect(triggerCrawlerRun).toHaveBeenCalledOnce());
    await waitFor(() => expect(completed).toHaveBeenCalledOnce(),{timeout:8000});
    expect(screen.getByRole('alert')).toHaveTextContent('No verified product');
  },12000);
  it('explains that tracked products still refresh after partial discovery failure', async () => {
    const partial={...idle,latest_run:{id:2,started_at:'2026-10-03T01:00:00Z',status:'partial',source:'manual',products_found:1,products_created:0,products_updated:1,snapshots_created:1,error_message:'Discovery blocked'}};
    vi.mocked(fetchCrawlerStatus).mockResolvedValue(partial);
    render(<CrawlerControl/>);
    expect(await screen.findByRole('alert')).toHaveTextContent('Discovery blocked');
    expect(screen.getByRole('status')).toHaveTextContent('sản phẩm đang theo dõi vẫn được cập nhật');
  });
  it('submits unique product URLs pasted on separate lines', async () => {
    vi.mocked(triggerCrawlerRun).mockResolvedValue({status:'triggered'});
    render(<CrawlerControl/>);
    fireEvent.click(screen.getByRole('button',{name:'Quét theo Link / Từ khóa'}));
    const url1='https://shop.tiktok.com/vn/pdp/1737036472084039604';
    const url2='https://shop.tiktok.com/vn/pdp/1737036472084039605';
    fireEvent.change(screen.getByLabelText(/Dán link sản phẩm TikTok Shop/),{target:{value:`${url1}\n${url2}\n${url1}`}});
    expect(screen.getByRole('status')).toHaveTextContent('2/100 link duy nhất');
    fireEvent.click(screen.getByRole('button',{name:'Chạy Crawler Ngay'}));
    await waitFor(() => expect(triggerCrawlerRun).toHaveBeenCalledWith({product_urls:[url1,url2]}));
  });
  it('blocks more than the backend URL limit before starting a crawl', async () => {
    vi.mocked(triggerCrawlerRun).mockResolvedValue({status:'triggered'});
    render(<CrawlerControl/>);
    fireEvent.click(screen.getByRole('button',{name:'Quét theo Link / Từ khóa'}));
    const urls=Array.from({length:101},(_,i)=>`https://shop.tiktok.com/vn/pdp/${i+1000}`).join('\n');
    fireEvent.change(screen.getByLabelText(/Dán link sản phẩm TikTok Shop/),{target:{value:urls}});
    expect(screen.getByRole('alert')).toHaveTextContent('101/100 link duy nhất');
    expect(screen.getByRole('button',{name:'Chạy Crawler Ngay'})).toBeDisabled();
    expect(triggerCrawlerRun).not.toHaveBeenCalled();
  });
  it('clears previous results and displays retry on tab fetch failure', async () => {
    vi.mocked(fetchDashboardSummary).mockResolvedValue(summary);
    vi.mocked(fetchTrends).mockResolvedValue([{product_id:1,external_product_id:'123',title:'Original product',first_seen_at:'2026-10-03T01:00:00Z',last_seen_at:'2026-10-03T01:00:00Z',trend_score:10,deltas:{}}]);
    render(<DashboardPage/>);
    expect(await screen.findByText('Original product')).toBeInTheDocument();
    vi.mocked(fetchTrends).mockRejectedValue(new Error('network lost'));
    fireEvent.click(screen.getByRole('button',{name:/Rising/}));
    expect(await screen.findByRole('alert')).toHaveTextContent('Không tải được dữ liệu');
    expect(screen.queryByText('Original product')).not.toBeInTheDocument();
    expect(screen.getByRole('button',{name:'Tải lại'})).toBeInTheDocument();
  });
});
