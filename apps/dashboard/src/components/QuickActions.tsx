"use client";

interface QuickActionsProps { onTriggerAll: () => void; }

export function QuickActions({ onTriggerAll }: QuickActionsProps) {
  return (
    <div className="bg-black/30 border border-border/60 rounded-xl p-4 space-y-2">
      <button onClick={onTriggerAll} className="w-full py-2 border border-accent/30 bg-accent/10 text-accent-light rounded-lg text-xs font-medium hover:bg-accent/25 hover:border-accent transition-colors cursor-pointer">▶ Trigger All Agents</button>
      <button className="w-full py-2 border border-red-500/30 bg-red-500/10 text-red-400 rounded-lg text-xs font-medium hover:bg-red-500/20 transition-colors cursor-pointer">⏸ Pause All</button>
      <button className="w-full py-2 border border-zinc-500/30 bg-zinc-500/10 text-zinc-400 rounded-lg text-xs font-medium hover:bg-zinc-500/20 transition-colors cursor-pointer">📊 Export Report</button>
    </div>
  );
}
