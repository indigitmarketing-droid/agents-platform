"use client";

interface HeaderProps {
  agentCount: number;
  isConnected: boolean;
}

export function Header({ agentCount, isConnected }: HeaderProps) {
  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-gradient-to-r from-[#1a0a2e] to-[#0d0d1a]">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent to-purple-500 flex items-center justify-center font-bold text-white text-sm">A</div>
        <h1 className="text-lg font-semibold text-zinc-100">Agent Command Center</h1>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-xs text-accent-light">
          <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-success shadow-[0_0_8px_rgba(34,197,94,0.5)] animate-pulse" : "bg-error"}`} />
          <span>{isConnected ? `${agentCount} agents online` : "Connecting..."}</span>
        </div>
      </div>
    </header>
  );
}
