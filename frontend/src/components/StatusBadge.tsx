import React from "react";
import { Search, CheckCircle2, Eye, AlertTriangle } from "lucide-react";

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const st = (status || "INVESTIGATING").toUpperCase();

  let label = "Investigating";
  let Icon = Search;
  let styleClasses = "bg-sky-950/40 text-sky-300 border-sky-800/50";

  if (st === "CONFIRMED") {
    label = "Confirmed";
    Icon = AlertTriangle;
    styleClasses = "bg-rose-950/40 text-rose-300 border-rose-800/50";
  } else if (st === "RESOLVED") {
    label = "Resolved";
    Icon = CheckCircle2;
    styleClasses = "bg-emerald-950/40 text-emerald-300 border-emerald-800/50";
  } else if (st === "MANUAL_REVIEW") {
    label = "Manual Review";
    Icon = Eye;
    styleClasses = "bg-amber-950/40 text-amber-300 border-amber-800/50";
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-medium rounded-full border ${styleClasses}`}
    >
      <Icon className="w-3 h-3" />
      {label}
    </span>
  );
};
