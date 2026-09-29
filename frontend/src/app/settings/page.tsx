"use client";

import React, { useEffect, useState } from "react";
import { 
  Key, 
  Sliders, 
  Save, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw,
  Trash2
} from "lucide-react";
import { api, SettingsData } from "@/lib/api";

const API_KEY_STORAGE_KEY = "trace-ai:jev-api-key";

function persistApiKey(value: string) {
  try {
    if (value) {
      window.localStorage.setItem(API_KEY_STORAGE_KEY, value);
    } else {
      window.localStorage.removeItem(API_KEY_STORAGE_KEY);
    }
  } catch {
    // Storage can be unavailable in privacy-restricted browser contexts.
  }
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [modeSaving, setModeSaving] = useState(false);
  const [clearingRealData, setClearingRealData] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState("Configuration saved successfully. System parameters updated.");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form states
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [demoMode, setDemoMode] = useState(true);
  const [contamination, setContamination] = useState(0.08);
  const [correlationWindow, setCorrelationWindow] = useState(120);

  useEffect(() => {
    let timer: number | undefined;

    try {
      const storedApiKey = window.localStorage.getItem(API_KEY_STORAGE_KEY);
      if (storedApiKey) {
        timer = window.setTimeout(() => setApiKeyInput(storedApiKey), 0);
      }
    } catch {
      // Storage can be unavailable in privacy-restricted browser contexts.
    }

    return () => {
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, []);

  useEffect(() => {
    api.getSettings()
      .then((data) => {
        setSettings(data);
        setDemoMode(data.demo_mode);
        setContamination(data.default_contamination);
        setCorrelationWindow(data.default_correlation_window_seconds);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSavedSuccess(false);
    setSuccessMessage("Configuration saved successfully. System parameters updated.");
    setErrorMessage(null);

    try {
      const trimmedApiKey = apiKeyInput.trim();
      const updated = await api.updateSettings({
        jev_api_key: trimmedApiKey !== "" ? trimmedApiKey : undefined,
        demo_mode: demoMode,
        default_contamination: contamination,
        default_correlation_window_seconds: correlationWindow,
      });
      setSettings(updated);
      if (trimmedApiKey) {
        persistApiKey(trimmedApiKey);
      }
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 4000);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to update settings");
    } finally {
      setSaving(false);
    }
  };

  const handleClearApiKey = async () => {
    setSaving(true);
    setSavedSuccess(false);
    setSuccessMessage("Configuration saved successfully. System parameters updated.");
    setErrorMessage(null);

    try {
      const updated = await api.updateSettings({ jev_api_key: "" });
      setSettings(updated);
      setApiKeyInput("");
      persistApiKey("");
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 4000);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to clear API key");
    } finally {
      setSaving(false);
    }
  };

  const handleModeToggle = async () => {
    const nextDemoMode = !demoMode;
    setModeSaving(true);
    setSavedSuccess(false);
    setSuccessMessage("Data source mode changed successfully.");
    setErrorMessage(null);
    setDemoMode(nextDemoMode);

    try {
      const updated = await api.updateSettings({ demo_mode: nextDemoMode });
      setSettings(updated);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 4000);
    } catch (err: unknown) {
      setDemoMode(!nextDemoMode);
      setErrorMessage(err instanceof Error ? err.message : "Failed to change data mode");
    } finally {
      setModeSaving(false);
    }
  };

  const handleClearRealData = async () => {
    if (!window.confirm("Clear all uploaded real data? This removes real-mode runs, logs, anomalies, and incidents. Demo data will not be affected.")) {
      return;
    }

    setClearingRealData(true);
    setSavedSuccess(false);
    setErrorMessage(null);

    try {
      const result = await api.clearRealData();
      setSuccessMessage(`Cleared ${result.deleted.runs} real data run${result.deleted.runs === 1 ? "" : "s"}.`);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 4000);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to clear real data");
    } finally {
      setClearingRealData(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] gap-3">
        <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin" />
        <span className="text-xs text-slate-400 font-mono">Loading configuration...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b border-[#222731] pb-3">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          System Configuration & AI Settings
        </h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Configure TypeSafe Jev API credentials, demo fallback switches, and machine learning hyperparameters.
        </p>
      </div>

      {savedSuccess && (
        <div className="p-3 bg-emerald-950/40 border border-emerald-800/60 rounded-md text-xs text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded-md text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Section 1: Jev AI API Integration */}
        <div className="bg-[#12151b] border border-[#222733] rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#222733]">
            <div className="flex items-center gap-2">
              <Key className="w-4 h-4 text-emerald-400" />
              <h2 className="text-sm font-semibold text-slate-100">
                TypeSafe Jev AI API Integration
              </h2>
            </div>
            <span
              className={`px-2 py-0.5 rounded text-[11px] font-mono border ${
                settings?.demo_mode
                  ? "bg-amber-950/40 text-amber-300 border-amber-800/50"
                  : "bg-emerald-950/40 text-emerald-300 border-emerald-800/50"
              }`}
            >
              {settings?.demo_mode ? "Operating in Demo Data Mode" : "Operating in Real Data Mode"}
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <label htmlFor="jev-api-key" className="block text-xs font-medium text-slate-300 mb-1">
                Jev API Key
              </label>
              <div className="flex items-center gap-2">
                <input
                  id="jev-api-key"
                  type="password"
                  placeholder={
                    settings?.jev_api_key_configured
                      ? `Key active (${settings.jev_api_key_masked}) - Enter new key to override`
                      : "Enter TypeSafe Jev API Key..."
                  }
                  value={apiKeyInput}
                  onChange={(e) => {
                    const value = e.target.value;
                    setApiKeyInput(value);
                    persistApiKey(value.trim());
                  }}
                  className="flex-1 bg-[#161a22] border border-[#282f3c] rounded px-3 py-1.5 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-emerald-500 font-mono"
                />
                <button
                  type="button"
                  onClick={handleClearApiKey}
                  disabled={saving || !apiKeyInput}
                  title="Clear the saved API key"
                  aria-label="Clear the saved API key"
                  className="inline-flex items-center justify-center w-8 h-8 rounded border border-[#282f3c] text-slate-400 hover:text-rose-300 hover:border-rose-700 disabled:opacity-40 disabled:hover:text-slate-400 disabled:hover:border-[#282f3c] transition"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Remembered in this browser so it survives refreshes, then sent to the backend when you save. Use this only on a trusted device.
              </p>
            </div>

            {/* Data Mode Toggle */}
            <div className="pt-2 flex items-center justify-between gap-4">
              <div>
                <span className="text-xs font-semibold text-slate-200 block">
                  Data source mode
                </span>
                <span className="text-[11px] text-slate-400 block mt-0.5">
                  Demo mode shows bundled scenarios. Real mode starts empty and only shows logs you upload.
                </span>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={demoMode}
                aria-label="Toggle between Demo Data and Real Data mode"
                onClick={handleModeToggle}
                disabled={saving || modeSaving}
                className="shrink-0 inline-flex items-center gap-2 rounded-md border border-[#2d3544] bg-[#171c25] px-2.5 py-1.5 text-[11px] font-semibold text-slate-200 transition hover:border-emerald-600 disabled:opacity-50"
              >
                <span
                  className={`relative h-4 w-8 rounded-full transition-colors ${demoMode ? "bg-amber-500/80" : "bg-emerald-500/80"}`}
                >
                  <span
                    className={`absolute left-0.5 top-0.5 h-3 w-3 rounded-full bg-white shadow transition-transform ${demoMode ? "" : "translate-x-4"}`}
                  />
                </span>
                <span>{demoMode ? "Demo Data" : "Real Data"}</span>
              </button>
            </div>

            <div className="bg-[#151922] p-3 rounded border border-[#232936] text-[11px] text-slate-400 font-mono flex items-center justify-between">
              <span>Endpoint: {settings?.jev_api_url}</span>
              <span className="text-emerald-400">Primitive: System One (Choice, Noul, Score)</span>
            </div>

            {!demoMode && (
              <div className="border-t border-[#222733] pt-4 flex items-center justify-between gap-4">
                <div>
                  <span className="text-xs font-semibold text-rose-200 block">Clear uploaded real data</span>
                  <span className="text-[11px] text-slate-400 block mt-0.5">
                    Removes real-mode runs, logs, anomalies, and incidents. Demo data is kept.
                  </span>
                </div>
                <button
                  type="button"
                  onClick={handleClearRealData}
                  disabled={clearingRealData || saving || modeSaving}
                  className="shrink-0 inline-flex items-center gap-2 rounded-md border border-rose-800/70 bg-rose-950/30 px-2.5 py-1.5 text-[11px] font-semibold text-rose-200 transition hover:border-rose-500 hover:bg-rose-950/60 disabled:opacity-50"
                >
                  {clearingRealData ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                  {clearingRealData ? "Clearing..." : "Clear Real Data"}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Section 2: Machine Learning Tuning */}
        <div className="bg-[#12151b] border border-[#222733] rounded-lg p-5 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-[#222733]">
            <Sliders className="w-4 h-4 text-sky-400" />
            <h2 className="text-sm font-semibold text-slate-100">
              Isolation Forest & Correlation Hyperparameters
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Contamination Sensitivity: <span className="font-mono text-emerald-400">{(contamination * 100).toFixed(0)}%</span>
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
                Lower contamination flags only extreme anomalies. Higher contamination flags subtle frequency deviations.
              </span>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Incident Clustering Sliding Window: <span className="font-mono text-emerald-400">{correlationWindow}s</span>
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
                Temporal threshold for grouping cascading cross-service errors into a single candidate incident.
              </span>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-5 py-2 rounded-md text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 transition shadow-sm disabled:opacity-50"
          >
            {saving ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Saving...
              </>
            ) : (
              <>
                <Save className="w-3.5 h-3.5" /> Save Configuration
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
