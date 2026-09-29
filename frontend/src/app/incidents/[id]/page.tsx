"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Download, 
  FileText, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  ShieldAlert, 
  Cpu, 
  Layers, 
  Info,
  Calendar,
  Share2,
  RefreshCw,
  ExternalLink
} from "lucide-react";
import { api, Incident } from "@/lib/api";
import { SeverityBadge } from "@/components/SeverityBadge";
import { CategoryBadge } from "@/components/CategoryBadge";
import { StatusBadge } from "@/components/StatusBadge";

export default function IncidentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);
  const [updatingStatus, setUpdatingStatus] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.getIncident(id)
      .then(setIncident)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  const handleStatusChange = async (newStatus: string) => {
    if (!incident) return;
    setUpdatingStatus(true);
    try {
      const updated = await api.updateIncidentStatus(incident.id, newStatus);
      setIncident(updated);
    } catch (err) {
      console.error(err);
    } finally {
      setUpdatingStatus(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] gap-3">
        <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin" />
        <span className="text-xs text-slate-400 font-mono">Retrieving incident telemetry & evidence...</span>
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="p-10 text-center bg-[#12151b] border border-[#222733] rounded-lg">
        <p className="text-sm text-slate-300 font-semibold mb-2">Incident not found</p>
        <Link href="/incidents" className="text-xs text-emerald-400 hover:underline">
          Return to incidents list
        </Link>
      </div>
    );
  }

  const diag = incident.diagnosis;
  const isDemo = diag?.is_demo_mode;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Back button and Export Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-[#222731]">
        <Link
          href="/incidents"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Incidents
        </Link>

        {/* Report Export Buttons */}
        <div className="flex items-center gap-2">
          <a
            href={api.getPdfReportUrl(incident.id)}
            download
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 rounded-md transition shadow-sm"
          >
            <Download className="w-3.5 h-3.5" /> Export PDF Report
          </a>
          <a
            href={api.getJsonReportUrl(incident.id)}
            download
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 bg-[#161a22] hover:bg-[#1f2430] border border-[#2a313f] rounded-md transition"
          >
            <FileText className="w-3.5 h-3.5" /> JSON Export
          </a>
        </div>
      </div>

      {/* Main Incident Summary Card */}
      <div className="bg-[#12151b] border border-[#222733] rounded-lg p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <SeverityBadge severity={incident.severity} size="md" />
            <CategoryBadge category={incident.category} />
            <StatusBadge status={incident.status} />
          </div>

          {/* Status selector */}
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400">Update Status:</span>
            <select
              value={incident.status}
              disabled={updatingStatus}
              onChange={(e) => handleStatusChange(e.target.value)}
              className="bg-[#161a22] border border-[#2c3444] text-slate-200 px-2.5 py-1 rounded text-xs focus:outline-none"
            >
              <option value="INVESTIGATING">INVESTIGATING</option>
              <option value="CONFIRMED">CONFIRMED</option>
              <option value="RESOLVED">RESOLVED</option>
              <option value="MANUAL_REVIEW">MANUAL_REVIEW</option>
            </select>
          </div>
        </div>

        <h1 className="text-xl font-bold text-slate-100 mb-2">
          {incident.title}
        </h1>

        <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 mb-4 font-mono">
          <span className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            {incident.detected_time ? new Date(incident.detected_time).toLocaleString() : "N/A"}
          </span>
          <span>&bull;</span>
          <span>Incident ID: {incident.id.substring(0, 12)}...</span>
          <span>&bull;</span>
          <span>Run ID: {incident.run_id.substring(0, 12)}...</span>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed bg-[#161a22] p-3.5 rounded border border-[#252b38]">
          {incident.summary}
        </p>
      </div>

      {/* AI Diagnosis (Jev Decision Engine) */}
      <div className="bg-[#12151b] border border-[#222733] rounded-lg p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#222733]">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-emerald-400" />
                AI Root Cause Diagnosis & Synthesis
              </h2>
              {isDemo && (
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-950/40 text-amber-300 border border-amber-800/50">
                  DEMO MODE (Deterministic Mock)
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Structured evaluation performed by TypeSafe Jev System One decision primitive
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <span className="text-[11px] text-slate-400 block">Model Confidence</span>
              <span className="text-base font-mono font-bold text-emerald-400">
                {Math.round(incident.confidence * 100)}%
              </span>
            </div>
          </div>
        </div>

        {diag ? (
          <div className="space-y-4 text-xs">
            {/* Probable Cause */}
            <div className="bg-[#161a22] p-4 rounded-md border border-[#252b38]">
              <span className="text-[11px] text-slate-400 font-mono block uppercase">Probable Root Cause</span>
              <p className="text-sm font-bold text-amber-300 mt-0.5">
                {diag.possible_cause}
              </p>
              <p className="text-slate-300 mt-2 text-xs leading-relaxed">
                {diag.explanation}
              </p>
            </div>

            {/* Uncertainty Flag */}
            <div className="bg-[#181c25] p-3 rounded-md border border-slate-700/60 flex items-start gap-2.5">
              <Info className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-200">Uncertainty Assessment:</span>
                <span className="text-slate-300 ml-1.5">{diag.uncertainty || "Manual verification recommended."}</span>
              </div>
            </div>

            {/* Recommended Action Steps */}
            {diag.recommended_steps && diag.recommended_steps.length > 0 && (
              <div>
                <h3 className="text-xs font-bold text-slate-200 mb-2 uppercase tracking-wide">
                  Recommended Investigation & Remediation Steps
                </h3>
                <div className="space-y-2">
                  {diag.recommended_steps.map((step, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-2.5 bg-[#161a22] p-2.5 rounded border border-[#232936]"
                    >
                      <span className="w-5 h-5 rounded-full bg-[#1e2430] text-emerald-400 font-mono text-[11px] flex items-center justify-center shrink-0 border border-[#2f384a]">
                        {idx + 1}
                      </span>
                      <span className="text-slate-300 text-xs font-mono">{step}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-xs text-slate-400 p-4">No diagnosis record attached to this incident.</div>
        )}
      </div>

      {/* Event Sequence & Causation Disclaimer */}
      <div className="bg-[#12151b] border border-[#222733] rounded-lg p-6 space-y-4">
        <div>
          <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Clock className="w-4 h-4 text-sky-400" />
            Chronological Supporting Event Sequence ({incident.evidence.length} Events)
          </h2>
          <div className="mt-2 p-2.5 bg-amber-950/20 border border-amber-800/40 rounded text-[11px] text-amber-300/90 leading-relaxed">
            <strong>Methodology Note:</strong> Events below are ordered chronologically by recorded timestamp.
            Per PRD Section 4.4, temporal correlation demonstrates related service impact during the incident window,
            but temporal sequence alone must not be treated as proof of causation without root-cause validation.
          </div>
        </div>

        {/* Timeline Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#161a22] text-slate-400 font-medium border-b border-[#222733]">
              <tr>
                <th className="py-2.5 px-3 w-16">Time</th>
                <th className="py-2.5 px-3 w-32">Service</th>
                <th className="py-2.5 px-3 w-24">Severity</th>
                <th className="py-2.5 px-3">Log Message</th>
                <th className="py-2.5 px-3 w-32">Evidence Role</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e232d] font-mono text-[11px]">
              {incident.evidence.map((ev, idx) => {
                const log = ev.log;
                const timeStr = log?.timestamp ? log.timestamp.substring(11, 19) : "N/A";
                return (
                  <tr key={ev.id || idx} className="hover:bg-[#161a22] transition">
                    <td className="py-2 px-3 text-slate-400 whitespace-nowrap">
                      {timeStr}
                    </td>
                    <td className="py-2 px-3 text-slate-300 font-sans">
                      <span className="px-1.5 py-0.5 bg-[#181d26] rounded border border-[#272f3d] text-[10px]">
                        {log?.service || "system"}
                      </span>
                    </td>
                    <td className="py-2 px-3">
                      <SeverityBadge severity={log?.severity || "INFO"} />
                    </td>
                    <td className="py-2 px-3 text-slate-200 font-sans text-xs">
                      {log?.message || ev.description}
                    </td>
                    <td className="py-2 px-3 text-slate-400 text-[10px]">
                      <span className="px-1.5 py-0.5 rounded bg-[#161a22] border border-[#252b38]">
                        {ev.evidence_type}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
