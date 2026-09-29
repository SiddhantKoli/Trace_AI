import React from "react";

interface SeverityBadgeProps {
  severity: string;
  size?: "sm" | "md";
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity, size = "sm" }) => {
  const sev = (severity || "INFO").toUpperCase();

  let colorClasses = "bg-slate-800/80 text-slate-300 border-slate-700";
  let dotColor = "bg-slate-400";

  if (sev === "CRITICAL" || sev === "FATAL") {
    colorClasses = "bg-rose-950/40 text-rose-300 border-rose-800/60";
    dotColor = "bg-rose-500 animate-pulse";
  } else if (sev === "ERROR") {
    colorClasses = "bg-red-950/30 text-red-300 border-red-800/50";
    dotColor = "bg-red-500";
  } else if (sev === "WARNING" || sev === "WARN") {
    colorClasses = "bg-amber-950/30 text-amber-300 border-amber-800/50";
    dotColor = "bg-amber-500";
  } else if (sev === "INFO") {
    colorClasses = "bg-emerald-950/20 text-emerald-300 border-emerald-800/40";
    dotColor = "bg-emerald-500";
  } else if (sev === "DEBUG") {
    colorClasses = "bg-zinc-800/60 text-zinc-400 border-zinc-700/50";
    dotColor = "bg-zinc-500";
  }

  const sizeClasses = size === "md" ? "px-2.5 py-1 text-xs" : "px-2 py-0.5 text-[11px]";

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium font-mono uppercase tracking-wider rounded border ${sizeClasses} ${colorClasses}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      {sev}
    </span>
  );
};
