"use client";
import type { AgentEvent } from "@/types/events";

interface PipelineStatusProps { events: AgentEvent[]; }

export function PipelineStatus({ events }: PipelineStatusProps) {
  const leadsFound = events.filter((e) => e.type === "scraping.lead_found").length;
  const called = events.filter((e) => e.type === "setting.call_started").length;
  const accepted = events.filter((e) => e.type === "setting.call_accepted").length;
  const rejected = events.filter((e) => e.type === "setting.call_rejected").length;
  const pending = leadsFound - called;

  return (
    <div className="bg-black/30 border border-border/60 rounded-xl p-4">
      <h4 className="text-[13px] font-semibold text-accent-lighter mb-2.5">Flusso Lead Attivo</h4>
      <div className="text-xs leading-[2.2]">
        <div className="flex items-center gap-2"><span className="text-blue-500">●</span><span>{leadsFound} lead trovati</span></div>
        <div className="ml-3 border-l-2 border-accent/20 pl-3">
          <div className="flex items-center gap-2"><span className="text-yellow-500">●</span><span>{called} chiamati</span></div>
          <div className="ml-3 border-l-2 border-accent/20 pl-3">
            <div className="flex items-center gap-2"><span className="text-green-500">●</span><span>{accepted} accettati → builder</span></div>
            <div className="flex items-center gap-2"><span className="text-red-500">●</span><span>{rejected} rifiutati</span></div>
          </div>
          <div className="flex items-center gap-2 text-muted"><span>○</span><span>{Math.max(0, pending)} in attesa</span></div>
        </div>
      </div>
    </div>
  );
}
