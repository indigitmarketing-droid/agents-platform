"use client";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import type { AgentEvent } from "@/types/events";

interface RevenueChartProps { events: AgentEvent[]; }

export function RevenueChart({ events }: RevenueChartProps) {
  const salesEvents = events.filter((e) => e.type === "setting.sale_completed");
  const dailyRevenue = new Map<string, number>();
  let cumulative = 0;
  const dataPoints: { date: string; revenue: number; cumulative: number }[] = [];

  for (let i = 29; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    dailyRevenue.set(d.toISOString().split("T")[0], 0);
  }

  for (const event of salesEvents) {
    const day = event.created_at?.split("T")[0];
    if (day && dailyRevenue.has(day)) {
      const amount = (event.payload as Record<string, number>)?.amount || 0;
      dailyRevenue.set(day, (dailyRevenue.get(day) || 0) + amount);
    }
  }

  for (const [date, revenue] of dailyRevenue) {
    cumulative += revenue;
    dataPoints.push({
      date: new Date(date).toLocaleDateString("it-IT", { day: "numeric", month: "short" }),
      revenue,
      cumulative,
    });
  }

  return (
    <div className="bg-gradient-to-br from-surface to-black/30 border border-border rounded-xl p-5">
      <div className="flex justify-between items-start mb-4">
        <div>
          <div className="text-sm font-semibold">Fatturato Generato</div>
          <div className="text-[22px] font-bold text-accent-light">€{cumulative.toLocaleString("it-IT")}</div>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={160}>
        <AreaChart data={dataPoints}>
          <defs>
            <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#52525b" }} axisLine={false} tickLine={false} interval={6} />
          <YAxis hide />
          <Tooltip contentStyle={{ background: "#1a1a2e", border: "1px solid rgba(139,92,246,0.3)", borderRadius: "8px", fontSize: "12px" }} formatter={(value) => [`€${Number(value).toLocaleString("it-IT")}`, "Cumulativo"]} />
          <Area type="monotone" dataKey="cumulative" stroke="#8b5cf6" strokeWidth={2.5} fill="url(#revenueGrad)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
