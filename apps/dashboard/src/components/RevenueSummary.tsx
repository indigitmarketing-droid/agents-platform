"use client";
import type { AgentEvent } from "@/types/events";

interface RevenueSummaryProps { events: AgentEvent[]; }

export function RevenueSummary({ events }: RevenueSummaryProps) {
  const sales = events.filter((e) => e.type === "setting.sale_completed");
  const totalRevenue = sales.reduce((sum, e) => sum + ((e.payload as Record<string, number>)?.amount || 0), 0);
  const avgTicket = sales.length > 0 ? Math.round(totalRevenue / sales.length) : 0;
  const totalCalls = events.filter((e) => e.type === "setting.call_started").length;
  const convRate = totalCalls > 0 ? Math.round((sales.length / totalCalls) * 100) : 0;

  return (
    <div className="bg-gradient-to-br from-accent/12 to-black/30 border border-accent/25 rounded-xl p-4 text-center">
      <div className="text-[28px] font-extrabold bg-gradient-to-r from-accent-light to-accent-lighter bg-clip-text text-transparent">€{totalRevenue.toLocaleString("it-IT")}</div>
      <div className="text-[11px] text-muted mt-0.5">Fatturato totale</div>
      <div className="grid grid-cols-2 gap-2 mt-3">
        {[
          { value: sales.length, label: "Vendite chiuse" },
          { value: `€${avgTicket}`, label: "Ticket medio" },
          { value: `${convRate}%`, label: "Conv. rate" },
          { value: `€${totalRevenue.toLocaleString("it-IT")}`, label: "Totale" },
        ].map((item) => (
          <div key={item.label} className="bg-black/30 rounded-md p-2">
            <div className="text-base font-bold text-accent-lighter">{item.value}</div>
            <div className="text-[9px] text-muted uppercase">{item.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
