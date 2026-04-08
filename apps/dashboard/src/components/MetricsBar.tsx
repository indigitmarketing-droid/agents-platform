"use client";
import type { AgentEvent } from "@/types/events";

interface MetricsBarProps { events: AgentEvent[]; }

export function MetricsBar({ events }: MetricsBarProps) {
  const today = new Date().toISOString().split("T")[0];
  const todayEvents = events.filter((e) => e.created_at?.startsWith(today));
  const metrics = [
    { label: "Events Today", value: todayEvents.length },
    { label: "Leads Found", value: events.filter((e) => e.type === "scraping.lead_found").length },
    { label: "Calls Made", value: events.filter((e) => e.type === "setting.call_started").length },
    { label: "Sites Built", value: events.filter((e) => e.type === "builder.website_ready").length },
  ];

  return (
    <div className="grid grid-cols-4 gap-3">
      {metrics.map((m) => (
        <div key={m.label} className="bg-surface border border-border rounded-xl px-4 py-3.5 text-center">
          <div className="text-2xl font-bold text-accent-light">{m.value}</div>
          <div className="text-[10px] text-muted uppercase tracking-wider mt-0.5">{m.label}</div>
        </div>
      ))}
    </div>
  );
}
