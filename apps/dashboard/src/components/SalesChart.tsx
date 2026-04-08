"use client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import type { AgentEvent } from "@/types/events";

interface SalesChartProps { events: AgentEvent[]; }

export function SalesChart({ events }: SalesChartProps) {
  const totalCalls = events.filter((e) => e.type === "setting.call_started").length;
  const totalSales = events.filter((e) => e.type === "setting.sale_completed").length;
  const conversionRate = totalCalls > 0 ? Math.round((totalSales / totalCalls) * 100) : 0;

  const chartData = [
    { name: "Sett 1", accepted: 2, rejected: 3, pending: 2 },
    { name: "Sett 2", accepted: 3, rejected: 4, pending: 1 },
    { name: "Sett 3", accepted: 5, rejected: 5, pending: 3 },
    { name: "Sett 4", accepted: 8, rejected: 3, pending: 6 },
  ];

  return (
    <div className="bg-gradient-to-br from-surface to-black/30 border border-border rounded-xl p-5">
      <div className="flex justify-between items-start mb-4">
        <div>
          <div className="text-sm font-semibold">Vendite Concluse</div>
          <div className="text-[22px] font-bold text-accent-light">{totalSales} vendite</div>
          <div className="text-[11px] text-muted mt-0.5">Conversion rate: <span className="text-green-500 font-semibold">{conversionRate}%</span></div>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={chartData}>
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#52525b" }} axisLine={false} tickLine={false} />
          <YAxis hide />
          <Tooltip contentStyle={{ background: "#1a1a2e", border: "1px solid rgba(139,92,246,0.3)", borderRadius: "8px", fontSize: "12px" }} />
          <Bar dataKey="accepted" stackId="a" fill="#22c55e" name="Venduti" />
          <Bar dataKey="rejected" stackId="a" fill="#ef4444" name="Rifiutati" />
          <Bar dataKey="pending" stackId="a" fill="#a78bfa" radius={[3, 3, 0, 0]} name="In attesa" />
        </BarChart>
      </ResponsiveContainer>
      <div className="flex gap-3.5 mt-3">
        <div className="flex items-center gap-1.5 text-[10px] text-zinc-400"><div className="w-2 h-2 rounded-sm bg-green-500" /> Venduti</div>
        <div className="flex items-center gap-1.5 text-[10px] text-zinc-400"><div className="w-2 h-2 rounded-sm bg-red-500" /> Rifiutati</div>
        <div className="flex items-center gap-1.5 text-[10px] text-zinc-400"><div className="w-2 h-2 rounded-sm bg-violet-400" /> In attesa</div>
      </div>
    </div>
  );
}
