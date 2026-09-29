"use client";

import React, { useEffect, useState, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { 
  Cpu, 
  Search, 
  Filter, 
  AlertTriangle, 
  ChevronLeft, 
  ChevronRight, 
  FileText, 
  Info,
  Sliders,
  CheckCircle2,
  RefreshCw
} from "lucide-react";
import { 
  ScatterChart, 
  Scatter, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer
} from "recharts";
import { api, AnalysisRun, LogEntry, Anomaly } from "@/lib/api";
import { SeverityBadge } from "@/components/SeverityBadge";

export default function AnalysisPage() {
  return (
    <Suspense fallback={
      <div className="flex flex-col items-center justify-center min-h-[50vh] gap-3">
        <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin" />
        <span className="text-xs text-slate-400 font-mono">Loading anomaly analysis...</span>
      </div>
    }>
      <AnalysisContent />
    </Suspense>
  );
}

function AnalysisContent() {
  const searchParams = useSearchParams();
  const queryRunId = searchParams.get("run_id");

  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>("");
  const [loading, setLoading] = useState(true);

  // Log explorer state
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [totalLogs, setTotalLogs] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize] = useState(30);

  // Filters
  const [selectedSeverity, setSelectedSeverity] = useState("ALL");
  const [onlyAnomalies, setOnlyAnomalies] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Anomalies for charts
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);

  useEffect(() => {
    api.getRuns()
      .then((data) => {
        setRuns(data);
        if (data.length > 0) {
          const targetId = queryRunId && data.some((r) => r.id === queryRunId) ? queryRunId : data[0].id;
          setSelectedRunId(targetId);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [queryRunId]);

  // Fetch logs whenever selectedRunId or filters change
  useEffect(() => {
    if (!selectedRunId) return;

    api.getRunLogs(
      selectedRunId,
      page,
      pageSize,
      selectedSeverity !== "ALL" ? selectedSeverity : undefined,
      onlyAnomalies ? true : undefined,
      searchQuery || undefined
    )
      .then((res) => {
        setLogs(res.items);
        setTotalLogs(res.total);
        setTotalPages(res.total_pages);
      })
      .catch(console.error);

    // Fetch anomalies for chart
    api.getRun(selectedRunId)
      .then((runDetail) => {
        setAnomalies(runDetail.anomalies || []);
      })
      .catch(console.error);
  }, [selectedRunId, page, selectedSeverity, onlyAnomalies, searchQuery]);

  const currentRun = useMemo(() => {
    return runs.find((r) => r.id === selectedRunId);
  }, [runs, selectedRunId]);

  // Chart data: map anomalies to (line_number, anomaly_score)
  const chartPoints = useMemo(() => {
    return anomalies.map((a) => ({
      line: a.log?.line_number || 0,
      score: a.anomaly_score,
      service: a.log?.service || "system",
      severity: a.log?.severity || "INFO",
      driver: a.feature_contributions?.primary_driver || "Statistical deviation",
    }));
  }, [anomalies]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] gap-3">
        <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin" />
        <span className="text-xs text-slate-400 font-mono">Loading anomaly analysis models...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-[#222731]">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            Isolation Forest Anomaly Detection
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Statistical scoring, feature vector contributions, and raw log verification.
          </p>
        </div>

        {/* Run Selector */}
        {runs.length > 0 && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400">Analysis Run:</span>
            <select
              value={selectedRunId}
              onChange={(e) => {
                setSelectedRunId(e.target.value);
                setPage(1);
              }}
              className="bg-[#151921] border border-[#2b3342] text-slate-200 px-3 py-1.5 rounded-md font-mono text-xs focus:outline-none focus:border-emerald-500"
            >
              {runs.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.filename} ({r.total_entries} logs &bull; {r.anomaly_count} anom)
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {!currentRun ? (
        <div className="p-8 text-center bg-[#12151b] border border-[#222733] rounded-lg">
          <p className="text-xs text-slate-400">No analysis runs available. Please upload a log file first.</p>
        </div>
      ) : (
        <>
          {/* Run Summary Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-[#12151b] border border-[#222733] p-4 rounded-lg">
            <div>
              <span className="text-[11px] text-slate-400 block">Analyzed File</span>
              <span className="text-sm font-semibold text-slate-200 truncate block">{currentRun.filename}</span>
            </div>
            <div>
              <span className="text-[11px] text-slate-400 block">Parsed / Rejected</span>
              <span className="text-sm font-mono font-medium text-slate-200">
                <span className="text-emerald-400">{currentRun.parsed_count}</span> /{" "}
                <span className="text-rose-400">{currentRun.rejected_count}</span>
              </span>
            </div>
            <div>
              <span className="text-[11px] text-slate-400 block">Flagged Anomalies</span>
              <span className="text-sm font-mono font-bold text-amber-400">
                {currentRun.anomaly_count} ({Math.round((currentRun.anomaly_count / Math.max(1, currentRun.total_entries)) * 100)}%)
              </span>
            </div>
            <div>
              <span className="text-[11px] text-slate-400 block">Incidents Formulated</span>
              <span className="text-sm font-mono font-bold text-rose-400">
                {currentRun.incident_count}
              </span>
            </div>
          </div>

          {/* Anomaly Distribution Chart */}
          <div className="bg-[#12151b] border border-[#222733] rounded-lg p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-slate-200">
                  Isolation Forest Relative Score Spectrum
                </h3>
                <p className="text-[11px] text-slate-400">
                  Scores rank each log within this uploaded file; they are not probabilities. The model flag is shown in the log table.
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-400" /> Outlier
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 ml-2" /> Baseline
              </div>
            </div>

            <div className="h-56 w-full">
              {chartPoints.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: -20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2530" />
                    <XAxis 
                      type="number" 
                      dataKey="line" 
                      name="Line Number" 
                      stroke="#64748b" 
                      tick={{ fontSize: 10 }}
                    />
                    <YAxis 
                      type="number" 
                      dataKey="score" 
                      domain={[0, 1]} 
                      name="Score" 
                      stroke="#64748b" 
                      tick={{ fontSize: 10 }}
                    />
                    <Tooltip 
                      cursor={{ strokeDasharray: "3 3" }}
                      content={({ payload }) => {
                        if (!payload || !payload.length) return null;
                        const data = payload[0].payload;
                        return (
                          <div className="bg-[#161a22] border border-[#2c3442] p-2.5 rounded text-xs text-slate-200 shadow-md">
                            <p className="font-bold text-slate-100">Line #{data.line} &bull; {data.service}</p>
                            <p className="text-amber-400 font-mono text-[11px]">Relative score: {data.score}</p>
                            <p className="text-slate-400 text-[11px] mt-1">{data.driver}</p>
                          </div>
                        );
                      }}
                    />
                    <Scatter 
                      name="Anomalies" 
                      data={chartPoints} 
                      fill="#f59e0b"
                    />
                  </ScatterChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-400 font-mono">
                  No anomaly points recorded for this run.
                </div>
              )}
            </div>
          </div>

          {/* Interactive Log Explorer Table */}
          <div className="bg-[#12151b] border border-[#222733] rounded-lg overflow-hidden space-y-0">
            {/* Filter Bar */}
            <div className="p-3.5 bg-[#161a22] border-b border-[#222733] flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2 flex-1 max-w-sm">
                <Search className="w-3.5 h-3.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Filter message or service..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setPage(1);
                  }}
                  className="bg-[#12151a] border border-[#252c38] rounded px-2.5 py-1 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-emerald-500 w-full"
                />
              </div>

              <div className="flex items-center gap-3">
                {/* Severity filter */}
                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                  <span>Severity:</span>
                  <select
                    value={selectedSeverity}
                    onChange={(e) => {
                      setSelectedSeverity(e.target.value);
                      setPage(1);
                    }}
                    className="bg-[#12151a] border border-[#252c38] text-slate-200 px-2 py-1 rounded text-xs focus:outline-none"
                  >
                    <option value="ALL">All Severities</option>
                    <option value="CRITICAL">Critical</option>
                    <option value="ERROR">Error</option>
                    <option value="WARNING">Warning</option>
                    <option value="INFO">Info</option>
                  </select>
                </div>

                {/* Only Anomalies Toggle */}
                <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={onlyAnomalies}
                    onChange={(e) => {
                      setOnlyAnomalies(e.target.checked);
                      setPage(1);
                    }}
                    className="accent-emerald-500 rounded cursor-pointer"
                  />
                  <span>Anomalies Only</span>
                </label>
              </div>
            </div>

            {/* Logs Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#141820] text-slate-400 font-medium border-b border-[#222733]">
                  <tr>
                    <th className="py-2.5 px-3 w-14">Line</th>
                    <th className="py-2.5 px-3 w-24">Timestamp</th>
                    <th className="py-2.5 px-3 w-24">Severity</th>
                    <th className="py-2.5 px-3 w-32">Service</th>
                    <th className="py-2.5 px-3">Message</th>
                    <th className="py-2.5 px-3 w-28 text-right">Relative Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1e232d] font-mono text-[11px]">
                  {logs.length > 0 ? (
                    logs.map((log) => {
                      const score = log.anomaly_score ?? 0;
                      const isHighAnom = score >= 0.70;
                      return (
                        <tr 
                          key={log.id} 
                          className={`hover:bg-[#161a22] transition ${
                            isHighAnom ? "bg-amber-950/10" : ""
                          }`}
                        >
                          <td className="py-2 px-3 text-slate-400">
                            #{log.line_number}
                          </td>
                          <td className="py-2 px-3 text-slate-400 whitespace-nowrap">
                            {log.timestamp ? log.timestamp.substring(11, 19) : "N/A"}
                          </td>
                          <td className="py-2 px-3">
                            <SeverityBadge severity={log.severity} />
                          </td>
                          <td className="py-2 px-3 text-slate-300 font-sans">
                            <span className="px-1.5 py-0.5 bg-[#181d26] rounded border border-[#272f3d] text-[10px]">
                              {log.service}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-slate-200 max-w-xl font-sans text-xs">
                            <div className="line-clamp-2" title={log.message}>
                              {log.message}
                            </div>
                            {log.feature_contributions?.primary_driver && (
                              <div className="text-[10px] text-amber-400/80 font-mono mt-0.5">
                                Reason: {log.feature_contributions.primary_driver}
                              </div>
                            )}
                          </td>
                          <td className="py-2 px-3 text-right">
                            <span
                              className={`px-2 py-0.5 rounded font-mono text-[11px] font-bold border ${
                                score >= 0.7
                                  ? "bg-rose-950/40 text-rose-300 border-rose-800/60"
                                  : score >= 0.5
                                  ? "bg-amber-950/40 text-amber-300 border-amber-800/60"
                                  : "bg-slate-900 text-slate-400 border-slate-800"
                              }`}
                            >
                              {(score * 100).toFixed(0)}%
                            </span>
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-400 font-sans">
                        No logs matching the current filter criteria.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="p-3 bg-[#141820] border-t border-[#222733] flex items-center justify-between text-xs text-slate-400">
              <div>
                Showing page <span className="text-slate-200 font-medium">{page}</span> of{" "}
                <span className="text-slate-200 font-medium">{totalPages}</span> ({totalLogs} total entries)
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="p-1 rounded bg-[#1b202a] border border-[#2b3342] text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#252c3a] transition"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="p-1 rounded bg-[#1b202a] border border-[#2b3342] text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#252c3a] transition"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
