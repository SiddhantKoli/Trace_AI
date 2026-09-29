"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Activity, 
  UploadCloud, 
  Cpu, 
  AlertTriangle, 
  Settings as SettingsIcon, 
  ShieldCheck, 
  FileText,
  BarChart3
} from "lucide-react";
import { api } from "@/lib/api";

export const Navbar = () => {
  const pathname = usePathname();
  const [health, setHealth] = useState<{ status: string; demo_mode: boolean; jev_configured: boolean } | null>(null);

  useEffect(() => {
    api.checkHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: "disconnected", demo_mode: true, jev_configured: false }));
  }, [pathname]);

  const navLinks = [
    { href: "/", label: "Overview", icon: Activity },
    { href: "/upload", label: "Upload Logs", icon: UploadCloud },
    { href: "/analysis", label: "Analysis", icon: Cpu },
    { href: "/incidents", label: "Incidents", icon: AlertTriangle },
    { href: "/evaluation", label: "Evaluation", icon: BarChart3 },
    { href: "/settings", label: "Settings", icon: SettingsIcon },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#0f1115]/95 backdrop-blur border-b border-[#222731]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Logo & Brand */}
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="w-8 h-8 rounded bg-gradient-to-br from-emerald-500 to-sky-600 flex items-center justify-center font-bold text-white shadow-sm shadow-emerald-500/20">
                T
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-base tracking-wide text-slate-100 flex items-center gap-1.5">
                  TRACE <span className="text-emerald-400 font-mono text-xs px-1 py-0.2 bg-emerald-950/60 border border-emerald-800/60 rounded">AI</span>
                </span>
                <span className="text-[10px] text-slate-400 font-mono -mt-0.5">
                  Log Anomaly & Incident Platform
                </span>
              </div>
            </Link>

            {/* Nav tabs */}
            <nav className="hidden md:flex items-center gap-1">
              {navLinks.map((link) => {
                const Icon = link.icon;
                const isActive = pathname === link.href || (link.href !== "/" && pathname.startsWith(link.href));
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                      isActive
                        ? "bg-[#1c212a] text-slate-100 border border-[#2d3442]"
                        : "text-slate-400 hover:text-slate-200 hover:bg-[#14171d]"
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${isActive ? "text-emerald-400" : "text-slate-400"}`} />
                    {link.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Right Status Indicators */}
          <div className="flex items-center gap-3">
            {/* Mode badge */}
            {health && (
              <span
                className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-mono border ${
                  health.demo_mode
                    ? "bg-amber-950/40 text-amber-300 border-amber-800/50"
                    : "bg-emerald-950/40 text-emerald-300 border-emerald-800/50"
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    health.demo_mode ? "bg-amber-400" : "bg-emerald-400"
                  }`}
                />
                {health.demo_mode ? "DEMO MODE (MOCK)" : "LIVE JEV API"}
              </span>
            )}

            {/* Health status */}
            <div className="flex items-center gap-1.5 text-[11px] text-slate-400 font-mono bg-[#14171d] px-2.5 py-1 rounded border border-[#222731]">
              <span
                className={`w-2 h-2 rounded-full ${
                  health?.status === "healthy" ? "bg-emerald-500" : "bg-rose-500"
                }`}
              />
              <span className="hidden sm:inline">Backend:</span>
              <span className={health?.status === "healthy" ? "text-emerald-400" : "text-rose-400"}>
                {health?.status === "healthy" ? "Online" : "Connecting"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
