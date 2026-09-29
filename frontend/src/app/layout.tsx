import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "TRACE AI - AI-Powered Log Analysis & Incident Platform",
  description: "Transform raw application logs into structured, evidence-based incident reports using machine learning and Jev AI.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full">
      <body className={`${inter.className} min-h-full flex flex-col bg-[#0d0f12] text-slate-100`}>
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </main>
        <footer className="border-t border-[#1e2229] py-4 bg-[#0a0c0e] text-center text-xs text-slate-400">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
            <div>TRACE AI &bull; AI-Powered Log Analysis & Incident Investigation Platform</div>
            <div className="font-mono text-[11px] text-slate-400">
              PRD v1.0 &bull; Isolation Forest &bull; TypeSafe Jev System One
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
