"use client";

import { useState } from "react";
import { ProductSnapshot } from "@/types";
import { formatCurrency, formatDate } from "@/lib/utils";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

const ranges = { "24h": 24, "7d": 168, "30d": 720, "Tất cả": Infinity };
type Range = keyof typeof ranges;
const timestamp = (value: number | string) => new Intl.DateTimeFormat("vi-VN", {
  day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit",
}).format(new Date(value));
const count = (value: number | null | undefined) => value == null ? "—" : value.toLocaleString("vi-VN");

export function ProductHistory({ snapshots }: { snapshots: ProductSnapshot[] }) {
  const [range, setRange] = useState<Range>("24h");
  const now = Date.now();
  const visible = snapshots.filter(s => {
    const time = Date.parse(s.captured_at);
    return Number.isFinite(time) && (range === "Tất cả" || (time >= now - ranges[range] * 3600000 && time <= now));
  }).sort((a, b) => Date.parse(a.captured_at) - Date.parse(b.captured_at));
  const chartData = visible.map(s => ({ time: Date.parse(s.captured_at), sold: s.sold_count ?? null, reviews: s.review_count ?? null }));

  return <section className="space-y-4" aria-label="Lịch sử sản phẩm">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <h2 className="text-sm font-semibold text-white">Lịch sử sản phẩm ({visible.length} snapshots)</h2>
      <div className="flex flex-wrap gap-2" role="group" aria-label="Khoảng thời gian lịch sử">
        {(Object.keys(ranges) as Range[]).map(value => <button key={value} aria-pressed={range === value}
          onClick={() => setRange(value)} className={`rounded-lg border px-3 py-1.5 text-xs ${range === value ? "border-rose-500 text-rose-300 bg-rose-500/10" : "border-slate-700 text-slate-300 bg-slate-900"}`}>{value}</button>)}
      </div>
    </div>
    <p className="text-xs text-slate-400">Chỉ hiển thị những lần thu thập đã lưu. Chỉ số tăng trưởng cần lịch sử đủ thời gian; ô “—” là chưa có dữ liệu.</p>
    {visible.length === 0 ? <p role="status" className="rounded-xl border border-slate-800 p-6 text-sm text-slate-400">Chưa có snapshot trong khoảng thời gian này.</p> : <>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {([['sold', 'Lượng bán tích lũy', '#10b981'], ['reviews', 'Số lượt đánh giá', '#06b6d4']] as const).map(([key, label, color]) =>
          <div key={key} className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
            <h3 className="text-sm font-semibold text-white mb-4">{label}</h3>
            {!chartData.some(s => s[key] != null) ? <p className="text-sm text-slate-400">Chưa có số liệu {label.toLowerCase()}.</p> :
              <div className="h-64"><ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="time" type="number" scale="time" domain={['dataMin', 'dataMax']} tickFormatter={v => formatDate(new Date(v).toISOString())} stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip labelFormatter={v => timestamp(Number(v))} contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px" }} />
                  <Line type="linear" dataKey={key} name={label} stroke={color} strokeWidth={2.5} dot={{ r: 4 }} connectNulls={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer></div>}
          </div>)}
      </div>
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 overflow-hidden">
        <h3 className="text-sm font-semibold text-white mb-4">Bảng dữ liệu snapshots theo thời gian</h3>
        <div className="overflow-x-auto"><table className="w-full text-xs text-left text-slate-300">
          <thead className="text-slate-400 border-b border-slate-800"><tr>{['Thời điểm chụp', 'Giá hiển thị', 'Lượng bán', 'Đánh giá', 'Rating', 'Hoa hồng'].map(label => <th key={label} scope="col" className="py-2.5 px-3">{label}</th>)}</tr></thead>
          <tbody className="divide-y divide-slate-800/60">{visible.map(s => <tr key={s.id}>
            <td className="py-2.5 px-3 whitespace-nowrap">{timestamp(s.captured_at)}</td>
            <td className="py-2.5 px-3 whitespace-nowrap">{formatCurrency(s.price)}</td>
            <td className="py-2.5 px-3">{count(s.sold_count)}</td>
            <td className="py-2.5 px-3">{count(s.review_count)}</td>
            <td className="py-2.5 px-3">{s.rating == null ? "—" : s.rating.toFixed(1)}</td>
            <td className="py-2.5 px-3">{s.commission_rate == null ? "—" : `${s.commission_rate}%`}</td>
          </tr>)}</tbody>
        </table></div>
      </div>
    </>}
  </section>;
}
