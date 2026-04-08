"use client";
import type { AgentEvent } from "@/types/events";

const DOT_COLORS: Record<string, string> = {
  scraping: "bg-blue-500",
  setting: "bg-yellow-500",
  builder: "bg-emerald-500",
  dashboard: "bg-zinc-500",
  system: "bg-zinc-500",
};

interface EventLogProps { events: AgentEvent[]; }

export function EventLog({ events }: EventLogProps) {
  const formatTime = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  };

  const getEventDetail = (event: AgentEvent): string => {
    const p = event.payload as Record<string, unknown>;
    const lead = p?.lead as Record<string, string> | undefined;
    const leadName = lead?.name || (p?.lead_id as string) || "";
    switch (event.type) {
      case "scraping.lead_found": return `Nuovo lead: "${leadName}" ${lead?.phone || ""}`;
      case "setting.call_accepted": return `"${leadName}" ha accettato la proposta`;
      case "setting.call_rejected": return `"${leadName}" — ${(p?.reason as string) || "non interessato"}`;
      case "setting.sale_completed": return `Vendita conclusa €${p?.amount || 0}`;
      case "builder.website_ready": return `Sito completato: ${p?.site_url || ""}`;
      case "builder.build_started": return `Costruzione sito avviata`;
      case "setting.call_started": return `Chiamata in corso`;
      default: return JSON.stringify(p).slice(0, 80);
    }
  };

  return (
    <div className="bg-black/40 border border-border/60 rounded-xl overflow-hidden">
      <div className="flex justify-between items-center px-4 py-3 bg-surface/60 border-b border-border/60">
        <h3 className="text-[13px] font-semibold">Eventi in tempo reale</h3>
        <div className="flex items-center gap-1.5 text-[10px] px-2 py-0.5 rounded-full bg-red-500/20 text-red-400">
          <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />LIVE
        </div>
      </div>
      <div className="max-h-[400px] overflow-y-auto">
        {events.map((event) => (
          <div key={event.id} className="grid grid-cols-[auto_1fr_auto] gap-3 items-center px-4 py-2.5 border-b border-white/[0.03] text-xs hover:bg-surface/40">
            <div className={`w-2 h-2 rounded-full ${DOT_COLORS[event.source_agent] || DOT_COLORS.system}`} />
            <div>
              <span className="font-medium text-zinc-300">{event.type}</span>{" "}
              <span className="text-muted">— {getEventDetail(event)}</span>
            </div>
            <div className="text-zinc-600 font-mono text-[11px]">{formatTime(event.created_at)}</div>
          </div>
        ))}
        {events.length === 0 && (
          <div className="px-4 py-8 text-center text-muted text-sm">
            Nessun evento ancora. Clicca &quot;Trigger&quot; su un agente per iniziare.
          </div>
        )}
      </div>
    </div>
  );
}
