"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  ArrowRight, 
  Sliders, 
  Database, 
  Cpu, 
  Layers, 
  Network, 
  Activity, 
  Bug
} from "lucide-react";
import { api, AnalysisRun, SampleCatalogItem } from "@/lib/api";

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [resultRun, setResultRun] = useState<AnalysisRun | null>(null);

  // Advanced ML settings
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [contamination, setContamination] = useState(0.08);
  const [correlationWindow, setCorrelationWindow] = useState(120);

  // Sample catalogue
  const [samples, setSamples] = useState<SampleCatalogItem[]>([]);
  const [sampleLoadingId, setSampleLoadingId] = useState<string | null>(null);

  useEffect(() => {
    api.getSamples().then(setSamples).catch(console.error);
  }, []);

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (f: File) => {
    const ext = f.name.substring(f.name.lastIndexOf(".")).toLowerCase();
    if (![".log", ".txt", ".csv"].includes(ext)) {
      setErrorMessage(`Unsupported file format '${ext}'. Please upload a .log, .txt, or .csv file.`);
      setFile(null);
      return;
    }
    if (f.size > 25 * 1024 * 1024) {
      setErrorMessage("File exceeds the 25MB maximum limit.");
      setFile(null);
      return;
    }
    setErrorMessage(null);
    setFile(f);
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setIsProcessing(true);
    setErrorMessage(null);
    setResultRun(null);

    try {
      const run = await api.uploadFile(file, contamination, correlationWindow);
      setResultRun(run);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to process log file");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleLoadSample = async (sampleId: string) => {
    setSampleLoadingId(sampleId);
    setErrorMessage(null);
    setResultRun(null);

    try {
      const run = await api.loadSample(sampleId);
      setResultRun(run);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to load sample log");
    } finally {
      setSampleLoadingId(null);
    }
  };

  const getSampleIcon = (id: string) => {
    switch (id) {
      case "database": return Database;
      case "memory": return Cpu;
      case "http_500": return Layers;
      case "network": return Network;
      case "baseline": return Activity;
      case "malformed": return Bug;
      default: return FileText;
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Title */}
      <div className="border-b border-[#222731] pb-3">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          Log Ingestion & Anomaly Pipeline
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Ingest raw logs (.log, .txt, .csv), parse timestamps and severity, run Isolation Forest ML anomaly detection, and formulate incidents.
        </p>
      </div>

      {/* Error Alert */}
      {errorMessage && (
        <div className="p-3.5 bg-rose-950/40 border border-rose-800/60 rounded-md text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Ingestion Results Card */}
      {resultRun && (
        <div className="bg-[#12151b] border border-emerald-800/60 rounded-lg p-5 shadow-lg">
          <div className="flex items-center justify-between pb-3 border-b border-[#222733] mb-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <div>
                <h3 className="text-sm font-semibold text-slate-100">
                  Ingestion & Processing Complete: {resultRun.filename}
                </h3>
                <p className="text-[11px] text-slate-400 font-mono">Run ID: {resultRun.id}</p>
              </div>
            </div>
            <span className="px-2 py-0.5 text-xs font-mono font-medium rounded bg-emerald-950/50 text-emerald-300 border border-emerald-800/60">
              {resultRun.status}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
            <div className="bg-[#171a22] p-3 rounded border border-[#262c37]">
              <span className="text-[11px] text-slate-400 block">Total Entries</span>
              <span className="text-lg font-mono font-bold text-slate-100">{resultRun.total_entries}</span>
            </div>
            <div className="bg-[#171a22] p-3 rounded border border-[#262c37]">
              <span className="text-[11px] text-emerald-400 block">Parsed Valid Entries</span>
              <span className="text-lg font-mono font-bold text-emerald-400">{resultRun.parsed_count}</span>
            </div>
            <div className="bg-[#171a22] p-3 rounded border border-[#262c37]">
              <span className="text-[11px] text-rose-400 block">Rejected / Malformed</span>
              <span className="text-lg font-mono font-bold text-rose-400">{resultRun.rejected_count}</span>
            </div>
            <div className="bg-[#171a22] p-3 rounded border border-[#262c37]">
              <span className="text-[11px] text-amber-400 block">Identified Incidents</span>
              <span className="text-lg font-mono font-bold text-amber-400">{resultRun.incident_count}</span>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              onClick={() => router.push(`/analysis?run_id=${resultRun.id}`)}
              className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium text-slate-200 bg-[#1d222c] hover:bg-[#262c39] border border-[#2e3646] rounded transition"
            >
              Inspect Anomaly Features <ArrowRight className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => router.push(`/incidents?run_id=${resultRun.id}`)}
              className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium text-white bg-emerald-600 hover:bg-emerald-500 rounded transition shadow-sm"
            >
              Investigate Incidents ({resultRun.incident_count}) <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Main Upload Form */}
      <form onSubmit={handleUploadSubmit} className="space-y-4">
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleFileDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-all ${
            dragOver
              ? "border-emerald-500 bg-emerald-950/10"
              : "border-[#272d39] bg-[#12151b] hover:border-[#3a4354]"
          }`}
        >
          <input
            type="file"
            id="fileInput"
            className="hidden"
            accept=".log,.txt,.csv"
            onChange={handleFileChange}
          />
          <label htmlFor="fileInput" className="cursor-pointer block">
            <div className="w-12 h-12 rounded-full bg-[#1b2029] text-emerald-400 flex items-center justify-center mx-auto mb-3 border border-[#2b3342]">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div className="text-sm font-semibold text-slate-200">
              {file ? file.name : "Click to select or drag and drop log file"}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Supports standard syslog, application .log, raw .txt, or structured .csv up to 25MB
            </p>
            {file && (
              <p className="text-xs font-mono text-emerald-400 mt-2">
                Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </p>
            )}
          </label>
        </div>

        {/* Advanced Settings Toggle */}
        <div className="border border-[#222731] rounded-lg bg-[#12151a] overflow-hidden">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full px-4 py-2.5 flex items-center justify-between text-xs text-slate-300 font-medium hover:bg-[#161a22] transition"
          >
            <span className="flex items-center gap-2">
              <Sliders className="w-3.5 h-3.5 text-slate-400" /> Advanced ML & Correlation Tuning
            </span>
            <span className="text-[11px] text-slate-400 font-mono">
              {showAdvanced ? "Hide Options" : "Show Options"}
            </span>
          </button>

          {showAdvanced && (
            <div className="p-4 border-t border-[#222731] grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">
                  Isolation Forest Contamination Rate: <span className="font-mono text-emerald-400">{(contamination * 100).toFixed(0)}%</span>
                </label>
                <input
                  type="range"
                  min="0.01"
                  max="0.25"
                  step="0.01"
                  value={contamination}
                  onChange={(e) => setContamination(parseFloat(e.target.value))}
                  className="w-full accent-emerald-500 cursor-pointer"
                />
                <span className="text-[11px] text-slate-400 block mt-1">
                  Expected proportion of outliers in the input logs. Default is 8%.
                </span>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">
                  Incident Sliding Window: <span className="font-mono text-emerald-400">{correlationWindow}s</span>
                </label>
                <input
                  type="range"
                  min="30"
                  max="600"
                  step="30"
                  value={correlationWindow}
                  onChange={(e) => setCorrelationWindow(parseInt(e.target.value))}
                  className="w-full accent-emerald-500 cursor-pointer"
                />
                <span className="text-[11px] text-slate-400 block mt-1">
                  Maximum time delta between anomalous events to cluster them into a single incident.
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!file || isProcessing}
            className={`flex items-center gap-2 px-5 py-2 rounded-md text-xs font-semibold text-white transition ${
              !file || isProcessing
                ? "bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700"
                : "bg-emerald-600 hover:bg-emerald-500 shadow-sm"
            }`}
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Parsing & Running ML Models...
              </>
            ) : (
              <>
                <UploadCloud className="w-4 h-4" />
                Process & Run Investigation
              </>
            )}
          </button>
        </div>
      </form>

      {/* Sample Scenarios Catalogue */}
      <div className="space-y-4 pt-4 border-t border-[#222731]">
        <div>
          <h2 className="text-base font-semibold text-slate-200">
            Quick-Load Evaluation & Demo Datasets
          </h2>
          <p className="text-xs text-slate-400">
            One-click instant analysis runs on the labelled failure scenarios defined in PRD Section 12.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {samples.map((s) => {
            const Icon = getSampleIcon(s.id);
            const isLoading = sampleLoadingId === s.id;
            return (
              <div
                key={s.id}
                className="bg-[#12151b] border border-[#222733] hover:border-[#31394a] rounded-lg p-4 flex flex-col justify-between transition"
              >
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-7 h-7 rounded bg-[#1c212a] border border-[#2d3544] flex items-center justify-center text-emerald-400">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <span className="text-xs font-bold text-slate-100">{s.title}</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mb-3">{s.description}</p>
                  <div className="text-[10px] text-slate-400 font-mono mb-3 bg-[#161a22] p-1.5 rounded border border-[#222731]">
                    {s.recommended_for}
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => handleLoadSample(s.id)}
                  disabled={isLoading || isProcessing}
                  className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 text-xs font-medium text-slate-200 bg-[#1b2029] hover:bg-[#252c38] border border-[#2c3444] rounded transition"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400" />
                      Analyzing...
                    </>
                  ) : (
                    <>Load & Ingest Scenario</>
                  )}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
