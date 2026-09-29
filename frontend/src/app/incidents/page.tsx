"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { 
  AlertTriangle, 
  Search, 
  Filter, 
  ArrowRight, 
  Calendar, 
  Layers, 
  ShieldCheck, 
  Activity, 
  FileText,
  RefreshCw
} from "lucide-react";
import { api, Incident } from "@/lib/api";
import { SeverityBadge } from "@/components/SeverityBadge";
import { CategoryBadge } from "@/components/CategoryBadge";
import { StatusBadge } from "@/components/StatusBadge";

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("ALL");
  const [category, setCategory] = useState("ALL");
  const [status, setStatus] = useState("ALL");

  const fetchIncidents = async () => {
    try {
      const data = await api.getIncidents({
        search: search || undefined,
        severity: severity !== "ALL" ? severity : undefined,
        category: category !== "ALL" ? category : undefined,
        status: status !== "ALL" ? status : undefined,
      });
      setIncidents(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, [severity, category, status]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchIncidents();
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-[#222731]">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            Identified Incidents & Clusters
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Correlated error groups evaluated with TypeSafe Jev AI decision primitives.
          </p>
        </div>

        <button
          onClick={fetchIncidents}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-300 bg-[#161a22] border border-[#272d38] rounded-md hover:bg-[#1d222b] transition"
        >
          <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
          Refresh
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-[#12151b] border border-[#222733] rounded-lg p-3.5 flex flex-wrap items-center justify-between gap-3">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 flex-1 min-w-[240px]">
          <Search className="w-3.5 h-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search incident title, symptom, or service..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-[#161a22] border border-[#272d39] rounded px-3 py-1.5 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-emerald-500"
          />
        </form>

        {/* Dropdowns */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {/* Severity */}
          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            className="bg-[#161a22] border border-[#272d39] text-slate-300 px-2.5 py-1.5 rounded focus:outline-none"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="ERROR">Error</option>
            <option value="WARNING">Warning</option>
            <option value="INFO">Info</option>
          </select>

          {/* Category */}
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="bg-[#161a22] border border-[#272d39] text-slate-300 px-2.5 py-1.5 rounded focus:outline-none"
          >
            <option value="ALL">All Categories</option>
            <option value="database">Database</option>
            <option value="networking">Networking</option>
            <option value="resource_exhaustion">Resource Exhaustion</option>
            <option value="application">Application</option>
          </select>

          {/* Status */}
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="bg-[#161a22] border border-[#272d39] text-slate-300 px-2.5 py-1.5 rounded focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="RESOLVED">Resolved</option>
            <option value="MANUAL_REVIEW">Manual Review</option>
          </select>
        </div>
      </div>

      {/* Incidents Grid / Cards */}
      {loading ? (
        <div className="flex items-center justify-center p-12">
          <RefreshCw className="w-6 h-6 text-emerald-400 animate-spin" />
        </div>
      ) : incidents.length > 0 ? (
        <div className="grid grid-cols-1 gap-4">
          {incidents.map((inc) => (
            <div
              key={inc.id}
              className="bg-[#12151b] border border-[#222733] hover:border-[#323a4b] rounded-lg p-5 transition flex flex-col justify-between"
            >
              <div>
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2.5">
                  <div className="flex items-center gap-2">
                    <SeverityBadge severity={inc.severity} size="md" />
                    <CategoryBadge category={inc.category} />
                    <StatusBadge status={inc.status} />
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    {inc.detected_time ? new Date(inc.detected_time).toLocaleString() : "N/A"}
                  </div>
                </div>

                <h3 className="text-base font-bold text-slate-100 mb-1">
                  {inc.title}
                </h3>

                <p className="text-xs text-slate-300 mb-3">
                  {inc.summary}
                </p>

                {/* AI Diagnosis Preview Box */}
                {inc.diagnosis && (
                  <div className="bg-[#161a22] p-3 rounded border border-[#262c38] mb-3">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-semibold text-slate-200">
                        Evidence-based hypothesis: <span className="text-amber-300">{inc.diagnosis.possible_cause}</span>
                      </span>
                      <span className="font-mono text-emerald-400 font-bold">
                        {(inc.diagnosis.confidence * 100).toFixed(0)}% Confidence
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-2">
                      {inc.diagnosis.explanation}
                    </p>
                  </div>
                )}
              </div>

              {/* Bottom Card Footer */}
              <div className="flex items-center justify-between pt-3 border-t border-[#1e232d] text-xs">
                <span className="text-slate-400 font-mono text-[11px]">
                  Correlated Evidence: <strong className="text-slate-200">{inc.evidence.length} events</strong>
                </span>

                <Link
                  href={`/incidents/${inc.id}`}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1d222b] hover:bg-[#272e3a] text-slate-200 font-medium rounded border border-[#2d3544] transition"
                >
                  Investigate Details & Export <ArrowRight className="w-3.5 h-3.5 text-emerald-400" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-[#12151b] border border-[#222733] rounded-lg p-10 text-center">
          <AlertTriangle className="w-8 h-8 text-slate-400 mx-auto mb-2" />
          <p className="text-xs text-slate-300 font-medium">No incidents matched your search or filters.</p>
          <p className="text-[11px] text-slate-400 mt-1">Try resetting the severity or category dropdowns.</p>
        </div>
      )}
    </div>
  );
}
