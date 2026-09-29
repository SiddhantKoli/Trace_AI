import React from "react";
import { Database, Network, Cpu, Layers, AlertCircle } from "lucide-react";

interface CategoryBadgeProps {
  category: string;
}

export const CategoryBadge: React.FC<CategoryBadgeProps> = ({ category }) => {
  const cat = (category || "unknown").toLowerCase();

  let label = "Unknown";
  let Icon = AlertCircle;
  let styleClasses = "bg-slate-900 text-slate-300 border-slate-700/60";

  if (cat === "database") {
    label = "Database";
    Icon = Database;
    styleClasses = "bg-indigo-950/40 text-indigo-300 border-indigo-800/50";
  } else if (cat === "networking") {
    label = "Networking";
    Icon = Network;
    styleClasses = "bg-cyan-950/40 text-cyan-300 border-cyan-800/50";
  } else if (cat === "resource_exhaustion") {
    label = "Resource Exhaustion";
    Icon = Cpu;
    styleClasses = "bg-orange-950/40 text-orange-300 border-orange-800/50";
  } else if (cat === "application") {
    label = "Application";
    Icon = Layers;
    styleClasses = "bg-violet-950/40 text-violet-300 border-violet-800/50";
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium rounded border ${styleClasses}`}
    >
      <Icon className="w-3.5 h-3.5" />
      {label}
    </span>
  );
};
