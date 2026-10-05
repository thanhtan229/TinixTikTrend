"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Settings } from "lucide-react";
import { AlertCenter } from "./AlertCenter";
import { SystemDiagnosticsModal } from "./SystemDiagnosticsModal";

export const Header: React.FC = () => {
  const [showDiagnostics, setShowDiagnostics] = useState(false);

  return (
    <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-rose-500 to-amber-500 flex items-center justify-center font-bold text-white shadow-lg shadow-rose-500/20 group-hover:scale-105 transition-transform">
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
        </Link>
        <div className="flex items-center space-x-4 text-sm text-slate-400">
          <button
            onClick={() => setShowDiagnostics(true)}
            aria-label="Mở bảng chẩn đoán hệ thống"
            className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg border border-slate-800 bg-slate-950/60 hover:bg-slate-800 text-xs text-slate-300 hover:text-white transition-colors"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="hidden sm:inline font-medium">Hệ thống</span>
            <Settings className="h-3.5 w-3.5 text-slate-400" />
          </button>
          <AlertCenter />
        </div>
      </div>
      <SystemDiagnosticsModal isOpen={showDiagnostics} onClose={() => setShowDiagnostics(false)} />
    </header>
  );
};

