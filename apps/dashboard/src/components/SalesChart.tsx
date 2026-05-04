"use client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";
import type { AgentEvent } from "@/types/events";

interface SalesChartProps { events: AgentEvent[]; }

interface WeekBucket {
  name: string;
  weekStart: Date;
  accepted: number;
  rejected: number;
  pending: number;
}

function getWeekStart(d: Date): Date {
  const date = new Date(d);
  date.setHours(0, 0, 0, 0);
  const day = date.getDay();
  const diff = date.getDate() - day + (day === 0 ? -6 : 1); // Monday-start week
  return new Date(date.setDate(diff));
}

function buildWeekBuckets(): WeekBucket[] {
  const now = new Date();
  const buckets: WeekBucket[] = [];
  for (let i = 3; i >= 0; i--) {
    const weekStart = getWeekStart(new Date(now.getTime() - i * 7 * 24 * 3600 * 1000));
    buckets.push({
      name: i === 0 ? "Settimana corr." : `${i} sett. fa`,
      weekStart,
      accepted: 0,
      rejected: 0,
      pending: 0,
    });
  }
  return buckets;
}

export function SalesChart({ events }: SalesChartProps) {
  // Real event types from F1+D-Phase2 pipeline:
  // - customer.onboarded → vendita conclusa (paid)
  // - setting.call_rejected → cold call rejected
  // - setting.payment_link_sent → SMS Stripe link sent (waiting for payment)
  const sales = events.filter((e) => e.type === "customer.onboarded");
  const rejected = events.filter((e) => e.type === "setting.call_rejected");
  const linksSent = events.filter((e) => e.type === "setting.payment_link_sent");
  // pending = links sent but not yet paid
  const paidSiteIds = new Set(sales.map((e) => (e.payload as Record<string, unknown>)?.site_id));
  const pending = linksSent.filter((e) => !paidSiteIds.has((e.payload as Record<string, unknown>)?.site_id));

  // Conversion rate: vendite / sales calls fatti
  const totalSalesCalls = events.filter((e) => e.type === "setting.sales_call_initiated").length;
  const conversionRate = totalSalesCalls > 0 ? Math.round((sales.length / totalSalesCalls) * 100) : 0;

  // Build weekly buckets and assign each event
  const buckets = buildWeekBuckets();
  const assignToBucket = (event: AgentEvent, key: "accepted" | "rejected" | "pending") => {
    if (!event.created_at) return;
    const eventTime = new Date(event.created_at).getTime();
    for (const bucket of buckets) {
      const start = bucket.weekStart.getTime();
      const end = start + 7 * 24 * 3600 * 1000;
      if (eventTime >= start && eventTime < end) {
        bucket[key]++;
        return;
      }
    }
  };
  sales.forEach((e) => assignToBucket(e, "accepted"));
  rejected.forEach((e) => assignToBucket(e, "rejected"));
  pending.forEach((e) => assignToBucket(e, "pending"));

  const chartData = buckets.map(({ name, accepted, rejected, pending }) => ({ name, accepted, rejected, pending }));

  return (
    <div className="bg-gradient-to-br from-surface to-black/30 border border-border rounded-xl p-5">
      <div className="flex justify-between items-start mb-4">
        <div>
          <div className="text-sm font-semibold">Vendite Concluse</div>
          <div className="text-[22px] font-bold text-accent-light">{sales.length} vendite</div>
          <div className="text-[11px] text-muted mt-0.5">Conversion rate: <span className="text-green-500 font-semibold">{conversionRate}%</span> ({sales.length}/{totalSalesCalls} sales call)</div>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={chartData}>
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#52525b" }} axisLine={false} tickLine={false} />
          <YAxis hide />
          <Tooltip contentStyle={{ background: "#1a1a2e", border: "1px solid rgba(139,92,246,0.3)", borderRadius: "8px", fontSize: "12px" }} />
          <Legend wrapperStyle={{ fontSize: 10 }} />
          <Bar dataKey="accepted" stackId="a" fill="#22c55e" name="Venduti" />
          <Bar dataKey="rejected" stackId="a" fill="#ef4444" name="Rifiutati" />
          <Bar dataKey="pending" stackId="a" fill="#a78bfa" radius={[3, 3, 0, 0]} name="In attesa pagamento" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
