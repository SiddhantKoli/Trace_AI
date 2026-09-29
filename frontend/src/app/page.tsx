"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Activity, 
  AlertTriangle, 
  Cpu, 
  FileText, 
  ArrowRight, 
  UploadCloud, 
  CheckCircle2, 
  Clock, 
  ShieldAlert,
  BarChart2,
  RefreshCw
} from "lucide-react";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  Cell 
} from "recharts";
import { api, DashboardStats } from "@/lib/api";
import { SeverityBadge } from "@/components/SeverityBadge";
import { CategoryBadge } from "@/components/CategoryBadge";
import { StatusBadge } from "@/components/StatusBadge";

export default function OverviewPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStats = async () => {
    try {
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchStats();
  };

  const handleQuickLoad = async (sampleName: string) => {
    setLoading(true);
    try {
      await api.loadSample(sampleName);
      await fetchStats();
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  if (loading && !stats) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin" />
        <p className="text-sm text-slate-400 font-mono">Aggregating telemetry and incident metrics...</p>
      </div>
    );
  }

  const hasData = stats && stats.total_entries_analysed > 0;

  // Prepare severity chart data
  const severityChartData = stats?.severity_distribution
    ? Object.entries(stats.severity_distribution).map(([name, count]) => ({
        name,
        count,
        fill:
          name === "CRITICAL"
            ? "#ef4444"
            : name === "ERROR"
            ? "#f87171"
            : name === "WARNING"
            ? "#f59e0b"
            : name === "INFO"
            ? "#10b981"
            : "#64748b",
      }))
    : [];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#222731]">
        <div>
          <h1 className="text-xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
            System Investigation Overview
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time telemetry, Isolation Forest anomaly distribution, and Jev incident syntheses.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 bg-[#161920] border border-[#272d38] rounded-md hover:bg-[#1d222b] transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-emerald-400" : ""}`} />
            Refresh
          </button>
          <Link
            href="/upload"
            className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 rounded-md transition shadow-sm"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            Upload Logs
          </Link>
        </div>
      </div>

      {!hasData ? (
        /* Empty State */
        <div className="bg-[#12151a] border border-[#242933] rounded-lg p-10 text-center max-w-2xl mx-auto my-8">
          <div className="w-12 h-12 rounded-full bg-slate-800/80 text-emerald-400 flex items-center justify-center mx-auto mb-4 border border-slate-700">
            <UploadCloud className="w-6 h-6" />
          </div>
          <h2 className="text-base font-semibold text-slate-100 mb-1">No Ingested Logs Yet</h2>
          <p className="text-xs text-slate-400 max-w-md mx-auto mb-6">
            Upload your application log files (.log, .txt, .csv) or test the pipeline instantly with a pre-packaged incident scenario.
          </p>

          <div className="space-y-3">
            <Link
              href="/upload"
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-medium text-white bg-emerald-600 hover:bg-emerald-500 rounded-md transition"
            >
              <UploadCloud className="w-4 h-4" /> Go to Log Ingestion
            </Link>
            <div className="text-xs text-slate-400 font-mono my-2">&mdash; or load a labelled sample scenario &mdash;</div>
            <div className="flex flex-wrap items-center justify-center gap-2">
              <button
                onClick={() => handleQuickLoad("database")}
                className="px-3 py-1.5 text-xs text-slate-300 bg-[#191d24] hover:bg-[#222731] border border-[#2d3442] rounded transition"
              >
                Database Pool Exhaustion
              </button>
              <button
                onClick={() => handleQuickLoad("http_500")}
                className="px-3 py-1.5 text-xs text-slate-300 bg-[#191d24] hover:bg-[#222731] border border-[#2d3442] rounded transition"
              >
                HTTP 500 Spike
              </button>
              <button
                onClick={() => handleQuickLoad("memory")}
                className="px-3 py-1.5 text-xs text-slate-300 bg-[#191d24] hover:bg-[#222731] border border-[#2d3442] rounded transition"
              >
                High Memory OOM
              </button>
              <button
                onClick={() => handleQuickLoad("network")}
                className="px-3 py-1.5 text-xs text-slate-300 bg-[#191d24] hover:bg-[#222731] border border-[#2d3442] rounded transition"
              >
                Network Cascade
              </button>
            </div>
          </div>
        </div>
      ) : (
        <>
          {/* KPI Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-[#12151b] border border-[#222733] rounded-lg p-4">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-medium">Total Entries Analysed</span>
                <FileText className="w-4 h-4 text-slate-400" />
              </div>
              <div className="text-2xl font-bold text-slate-100 font-mono">
                {stats.total_entries_analysed.toLocaleString()}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">Parsed and vectorized records</p>
            </div>

            <div className="bg-[#12151b] border border-[#222733] rounded-lg p-4">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-medium">Anomalies Flagged</span>
                <Cpu className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold text-amber-400 font-mono">
                {stats.total_anomalies_detected.toLocaleString()}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">Isolation Forest outliers (score &gt; 0.7)</p>
            </div>

            <div className="bg-[#12151b] border border-[#222733] rounded-lg p-4">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-medium">Incidents Identified</span>
                <ShieldAlert className="w-4 h-4 text-rose-400" />
              </div>
              <div className="text-2xl font-bold text-rose-400 font-mono">
                {stats.total_incidents_identified.toLocaleString()}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">Correlated clusters investigated</p>
            </div>

            <div className="bg-[#12151b] border border-[#222733] rounded-lg p-4">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-medium">Critical Event Volume</span>
                <AlertTriangle className="w-4 h-4 text-rose-500" />
              </div>
              <div className="text-2xl font-bold text-slate-100 font-mono">
                {(stats.severity_distribution["CRITICAL"] || 0) + (stats.severity_distribution["ERROR"] || 0)}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">High-severity error logs recorded</p>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Timeline chart */}
            <div className="lg:col-span-2 bg-[#12151b] border border-[#222733] rounded-lg p-4 flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Error & Warning Frequency Timeline</h3>
                  <p className="text-[11px] text-slate-400">Sequential event distribution across log timeline</p>
                </div>
                <div className="flex items-center gap-3 text-[11px] font-mono">
                  <span className="flex items-center gap-1 text-rose-400">
                    <span className="w-2 h-2 rounded-full bg-rose-500" /> Errors
                  </span>
                  <span className="flex items-center gap-1 text-amber-400">
                    <span className="w-2 h-2 rounded-full bg-amber-500" /> Warnings
                  </span>
                  <span className="flex items-center gap-1 text-emerald-400">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" /> Info
                  </span>
                </div>
              </div>

              <div className="h-64 w-full">
                {stats.error_frequency_timeline && stats.error_frequency_timeline.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={stats.error_frequency_timeline} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1f2530" />
                      <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#161a22",
                          borderColor: "#2c3442",
                          fontSize: "12px",
                          borderRadius: "4px",
                        }}
                      />
                      <Area type="monotone" dataKey="errors" stackId="1" stroke="#f43f5e" fill="#f43f5e" fillOpacity={0.4} />
                      <Area type="monotone" dataKey="critical" stackId="1" stroke="#e11d48" fill="#e11d48" fillOpacity={0.6} />
                      <Area type="monotone" dataKey="warnings" stackId="1" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.3} />
                      <Area type="monotone" dataKey="info" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.1} />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-xs text-slate-400 font-mono">
                    Insufficient time points to display timeline
                  </div>
                )}
              </div>
            </div>

            {/* Severity Distribution */}
            <div className="bg-[#12151b] border border-[#222733] rounded-lg p-4 flex flex-col">
              <h3 className="text-sm font-semibold text-slate-200 mb-1">Severity Distribution</h3>
              <p className="text-[11px] text-slate-400 mb-4">Volume breakdown across log severity classes</p>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={severityChartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2530" />
                    <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 10 }} />
                    <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#161a22",
                        borderColor: "#2c3442",
                        fontSize: "12px",
                        borderRadius: "4px",
                      }}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {severityChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Recent Incidents Table */}
          <div className="bg-[#12151b] border border-[#222733] rounded-lg overflow-hidden">
            <div className="px-5 py-3.5 border-b border-[#222733] flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-200">Recent Identified Incidents</h3>
                <p className="text-[11px] text-slate-400">Clusters classified with Jev AI decision engine</p>
              </div>
              <Link
                href="/incidents"
                className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 font-medium transition"
              >
                View all incidents <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {stats.recent_incidents && stats.recent_incidents.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#161a22] text-slate-400 font-medium border-b border-[#222733]">
                    <tr>
                      <th className="py-2.5 px-4">Severity</th>
                      <th className="py-2.5 px-4">Category</th>
                      <th className="py-2.5 px-4">Incident Title</th>
                      <th className="py-2.5 px-4">AI Diagnosis Cause</th>
                      <th className="py-2.5 px-4">Confidence</th>
                      <th className="py-2.5 px-4">Status</th>
                      <th className="py-2.5 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1e232d]">
                    {stats.recent_incidents.map((inc) => (
                      <tr key={inc.id} className="hover:bg-[#161922] transition">
                        <td className="py-3 px-4">
                          <SeverityBadge severity={inc.severity} />
                        </td>
                        <td className="py-3 px-4">
                          <CategoryBadge category={inc.category} />
                        </td>
                        <td className="py-3 px-4 font-medium text-slate-200">
                          {inc.title}
                        </td>
                        <td className="py-3 px-4 text-slate-300">
                          {inc.diagnosis?.possible_cause || "Analyzing..."}
                        </td>
                        <td className="py-3 px-4 font-mono text-emerald-400">
                          {Math.round(inc.confidence * 100)}%
                        </td>
                        <td className="py-3 px-4">
                          <StatusBadge status={inc.status} />
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Link
                            href={`/incidents/${inc.id}`}
                            className="inline-flex items-center gap-1 text-slate-300 hover:text-white px-2 py-1 bg-[#1d222b] hover:bg-[#262c38] rounded border border-[#2d3442] transition"
                          >
                            Investigate <ArrowRight className="w-3 h-3" />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-slate-400">
                No incidents identified in current telemetry.
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
