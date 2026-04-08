"use client";
import { useState } from "react";
import { Header } from "@/components/Header";
import { MetricsBar } from "@/components/MetricsBar";
import { AgentCard } from "@/components/AgentCard";
import { AgentChat } from "@/components/AgentChat";
import { EventLog } from "@/components/EventLog";
import { RevenueChart } from "@/components/RevenueChart";
import { SalesChart } from "@/components/SalesChart";
import { RevenueSummary } from "@/components/RevenueSummary";
import { PipelineStatus } from "@/components/PipelineStatus";
import { QuickActions } from "@/components/QuickActions";
import { useRealtimeEvents } from "@/hooks/useRealtimeEvents";
import { useAgentStatus } from "@/hooks/useAgentStatus";

export default function DashboardPage() {
  const { events, isConnected, triggerAgent } = useRealtimeEvents(100);
  const { agents } = useAgentStatus();
  const onlineAgents = agents.filter((a) => a.status !== "offline").length;
  const handleTriggerAll = () => { for (const agent of agents) { triggerAgent(agent.id); } };
  const [chatAgent, setChatAgent] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-background">
      <Header agentCount={onlineAgents} isConnected={isConnected} />
      <div className="grid grid-cols-[1fr_380px] min-h-[calc(100vh-69px)]">
        <div className="p-6 space-y-6 overflow-y-auto">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[1.2px] text-accent mb-4">Overview</div>
            <MetricsBar events={events} />
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[1.2px] text-accent mb-4">Analytics</div>
            <div className="grid grid-cols-2 gap-4">
              <RevenueChart events={events} />
              <SalesChart events={events} />
            </div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[1.2px] text-accent mb-4">Agents</div>
            <div className="grid grid-cols-3 gap-4">
              {agents.length > 0 ? agents.map((agent) => (
                <AgentCard key={agent.id} agent={agent} events={events} onTrigger={triggerAgent} onChat={setChatAgent} />
              )) : ["scraping", "setting", "builder"].map((id) => (
                <AgentCard key={id} agent={{ id, status: "offline", last_heartbeat: null, current_task_id: null, metadata: {} }} events={events} onTrigger={triggerAgent} onChat={setChatAgent} />
              ))}
            </div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[1.2px] text-accent mb-4">Event Log — Live</div>
            <EventLog events={events} />
          </div>
        </div>
        <div className="bg-surface/40 border-l border-border/60 p-6 space-y-4 overflow-y-auto">
          <div className="text-[11px] font-semibold uppercase tracking-[1.2px] text-accent mb-2">Revenue</div>
          <RevenueSummary events={events} />
          <div className="text-[11px] font-semibold uppercase tracking-[1.2px] text-accent mb-2 mt-4">Pipeline Status</div>
          <PipelineStatus events={events} />
          <div className="text-[11px] font-semibold uppercase tracking-[1.2px] text-accent mb-2 mt-4">Azioni Rapide</div>
          <QuickActions onTriggerAll={handleTriggerAll} />
        </div>
      </div>
      {chatAgent && (
        <AgentChat agentId={chatAgent} onClose={() => setChatAgent(null)} />
      )}
    </div>
  );
}
