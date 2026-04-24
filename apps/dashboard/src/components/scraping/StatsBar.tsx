"use client";

import type { ScrapingTarget } from "@/hooks/useScrapingTargets";

interface StatsBarProps {
  targets: ScrapingTarget[];
}

export function StatsBar({ targets }: StatsBarProps) {
  const active = targets.filter((t) => t.enabled).length;
  const totalLeads = targets.reduce((sum, t) => sum + (t.total_leads_found || 0), 0);
  const lastRunDate = targets
    .map((t) => (t.last_run_at ? new Date(t.last_run_at).getTime() : 0))
    .reduce((max, ts) => Math.max(max, ts), 0);
  const lastRunLabel = lastRunDate
    ? new Date(lastRunDate).toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" })
    : "—";

  const stats = [
    { value: active, label: "Active targets" },
    { value: totalLeads, label: "Leads totali" },
    { value: targets.length, label: "Target totali" },
    { value: lastRunLabel, label: "Ultimo run" },
  ];

  return (
    <div className="grid grid-cols-4 gap-3">
      {stats.map((s) => (
        <div
          key={s.label}
          className="bg-surface border border-border rounded-xl px-4 py-3.5 text-center"
        >
          <div className="text-2xl font-bold text-accent-light">{s.value}</div>
          <div className="text-[10px] text-muted uppercase tracking-wider mt-0.5">
            {s.label}
          </div>
        </div>
      ))}
    </div>
  );
}
