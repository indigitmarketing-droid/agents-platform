"use client";

import type { ScrapingTarget } from "@/hooks/useScrapingTargets";
import { SCRAPING_CATEGORIES } from "@/lib/scraping-categories";

interface TargetRowProps {
  target: ScrapingTarget;
  onToggle: (id: string, enabled: boolean) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

export function TargetRow({ target, onToggle, onDelete }: TargetRowProps) {
  const cat = SCRAPING_CATEGORIES.find(
    (c) => c.value === target.category && c.type === target.category_type
  );
  const label = cat?.label || `${target.category_type}=${target.category}`;
  const lastRun = target.last_run_at
    ? new Date(target.last_run_at).toLocaleString("it-IT", {
        dateStyle: "short",
        timeStyle: "short",
      })
    : "mai";

  return (
    <tr className="border-b border-white/[0.03] text-sm hover:bg-surface/40">
      <td className="px-3 py-2">
        <button
          onClick={() => onToggle(target.id, !target.enabled)}
          className={`text-xs px-2 py-0.5 rounded-full font-medium ${
            target.enabled
              ? "bg-green-500/20 text-green-400"
              : "bg-zinc-700/50 text-zinc-400"
          }`}
        >
          {target.enabled ? "✅ ON" : "⏸ OFF"}
        </button>
      </td>
      <td className="px-3 py-2">{label}</td>
      <td className="px-3 py-2">{target.city}</td>
      <td className="px-3 py-2 text-muted text-xs">{target.country_code}</td>
      <td className="px-3 py-2 text-xs">{lastRun}</td>
      <td className="px-3 py-2 text-right text-accent-lighter font-semibold">
        {target.total_leads_found}
      </td>
      <td className="px-3 py-2 text-right">
        <button
          onClick={() => {
            if (confirm(`Eliminare target "${label} - ${target.city}"?`)) {
              onDelete(target.id);
            }
          }}
          className="text-red-400 hover:text-red-300 text-sm"
          title="Elimina"
        >
          🗑️
        </button>
      </td>
    </tr>
  );
}
