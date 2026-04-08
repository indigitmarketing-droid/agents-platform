"use client";
import type { Agent, AgentEvent } from "@/types/events";

const AGENT_CONFIG: Record<string, { icon: string; label: string; description: string; color: string }> = {
  scraping: { icon: "🔍", label: "Web Scraping", description: "Scansione lead B2B senza sito web", color: "bg-blue-500/15" },
  setting: { icon: "📞", label: "Setting", description: "Chiamate ElevenLabs + WhatsApp follow-up", color: "bg-yellow-500/15" },
  builder: { icon: "🏗️", label: "Website Builder", description: "Analisi target, copy, generazione sito", color: "bg-emerald-500/15" },
};

const STATUS_STYLES: Record<string, string> = {
  idle: "bg-zinc-500/20 text-zinc-400",
  working: "bg-accent/20 text-accent-light",
  error: "bg-error/20 text-error",
  offline: "bg-zinc-800/50 text-zinc-500",
};

interface AgentCardProps { agent: Agent; events: AgentEvent[]; onTrigger: (agentId: string) => void; onChat?: (agentId: string) => void; }

export function AgentCard({ agent, events, onTrigger, onChat }: AgentCardProps) {
  const config = AGENT_CONFIG[agent.id] || { icon: "🤖", label: agent.id, description: "", color: "bg-zinc-500/15" };
  const agentEvents = events.filter((e) => e.source_agent === agent.id || e.target_agent === agent.id);

  return (
    <div className="bg-gradient-to-br from-surface to-black/30 border border-border rounded-xl p-5 hover:border-border-hover transition-colors">
      <div className="flex justify-between items-start mb-3">
        <div className={`w-10 h-10 rounded-lg ${config.color} flex items-center justify-center text-lg`}>{config.icon}</div>
        <span className={`text-[11px] px-2.5 py-0.5 rounded-full font-medium ${STATUS_STYLES[agent.status] || STATUS_STYLES.offline}`}>{agent.status}</span>
      </div>
      <div className="text-[15px] font-semibold mb-1">{config.label}</div>
      <div className="text-xs text-muted mb-4">{config.description}</div>
      <div className="grid grid-cols-2 gap-2 mb-3.5">
        <div className="bg-black/30 rounded-md px-2.5 py-2">
          <div className="text-lg font-bold text-accent-lighter">{agentEvents.length}</div>
          <div className="text-[10px] text-muted uppercase tracking-wide">Eventi</div>
        </div>
        <div className="bg-black/30 rounded-md px-2.5 py-2">
          <div className="text-lg font-bold text-accent-lighter">{agent.status === "working" ? "⚡" : "—"}</div>
          <div className="text-[10px] text-muted uppercase tracking-wide">Attività</div>
        </div>
      </div>
      <div className="flex gap-2">
        <button onClick={() => onTrigger(agent.id)} className="flex-1 py-2 border border-accent/30 bg-accent/10 text-accent-light rounded-lg text-xs font-medium hover:bg-accent/25 hover:border-accent transition-colors cursor-pointer">
          ▶ Trigger Manuale
        </button>
        {onChat && (
          <button onClick={() => onChat(agent.id)} className="flex-1 py-2 border border-accent/30 bg-accent/10 text-accent-light rounded-lg text-xs font-medium hover:bg-accent/25 hover:border-accent transition-colors cursor-pointer">
            💬 Chat
          </button>
        )}
      </div>
    </div>
  );
}
