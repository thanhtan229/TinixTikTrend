import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TikTok Shop Affiliate Trend Hunter",
  description: "Phát hiện và xếp hạng sản phẩm tiềm năng TikTok Shop cho Affiliate Marketing",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className="dark">
      <body className="antialiased bg-slate-950 text-slate-100 min-h-screen">
        <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-rose-500 to-amber-500 flex items-center justify-center font-bold text-white shadow-lg shadow-rose-500/20">
                TT
              </div>
              <div>
                <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                  TikTok Trend Hunter
                </span>
                <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  VN Affiliate
                </span>
              </div>
            </div>
            <div className="hidden sm:flex items-center space-x-4 text-sm text-slate-400">
              <span className="flex items-center">
                <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></span>
                Hệ thống Cục bộ
              </span>
            </div>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
