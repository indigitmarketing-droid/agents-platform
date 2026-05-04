"use client";
import type { AgentEvent } from "@/types/events";

interface PipelineStatusProps { events: AgentEvent[]; }

export function PipelineStatus({ events }: PipelineStatusProps) {
  const leadsFound = events.filter((e) => e.type === "scraping.lead_found").length;
  const coldCalled = events.filter((e) => e.type === "setting.call_initiated").length;
  const coldAccepted = events.filter((e) => e.type === "setting.call_accepted").length;
  const coldRejected = events.filter((e) => e.type === "setting.call_rejected").length;
  const sitesBuilt = events.filter((e) => e.type === "builder.website_ready").length;
  const salesCalled = events.filter((e) => e.type === "setting.sales_call_initiated").length;
  const linksSent = events.filter((e) => e.type === "setting.payment_link_sent").length;
  const onboarded = events.filter((e) => e.type === "customer.onboarded").length;
  const pendingPayment = Math.max(0, linksSent - onboarded);
  const sitesDeleted = events.filter((e) => e.type === "site.deleted_unpaid").length;

  return (
    <div className="bg-black/30 border border-border/60 rounded-xl p-4">
      <h4 className="text-[13px] font-semibold text-accent-lighter mb-2.5">Flusso Lead Attivo</h4>
      <div className="text-xs leading-[2.2]">
        <div className="flex items-center gap-2"><span className="text-blue-500">●</span><span>{leadsFound} lead trovati</span></div>
        <div className="ml-3 border-l-2 border-accent/20 pl-3">
          <div className="flex items-center gap-2"><span className="text-yellow-500">●</span><span>{coldCalled} cold call</span></div>
          <div className="ml-3 border-l-2 border-accent/20 pl-3">
            <div className="flex items-center gap-2"><span className="text-green-500">●</span><span>{coldAccepted} accettati</span></div>
            <div className="flex items-center gap-2"><span className="text-red-500">●</span><span>{coldRejected} rifiutati</span></div>
          </div>
        </div>
        <div className="flex items-center gap-2 mt-1"><span className="text-purple-500">●</span><span>{sitesBuilt} siti costruiti</span></div>
        <div className="ml-3 border-l-2 border-accent/20 pl-3">
          <div className="flex items-center gap-2"><span className="text-orange-500">●</span><span>{salesCalled} sales call</span></div>
          <div className="flex items-center gap-2"><span className="text-pink-500">●</span><span>{linksSent} link Stripe inviati</span></div>
          <div className="flex items-center gap-2 text-muted"><span>○</span><span>{pendingPayment} in attesa pagamento</span></div>
        </div>
        <div className="flex items-center gap-2 mt-1"><span className="text-emerald-500">★</span><span className="text-emerald-400 font-semibold">{onboarded} clienti paganti</span></div>
        {sitesDeleted > 0 && (
          <div className="flex items-center gap-2 text-muted text-[10px]"><span>×</span><span>{sitesDeleted} siti eliminati (48h scaduti)</span></div>
        )}
      </div>
    </div>
  );
}
