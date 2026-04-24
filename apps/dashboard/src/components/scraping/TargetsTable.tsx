"use client";

import type { ScrapingTarget } from "@/hooks/useScrapingTargets";
import { TargetRow } from "./TargetRow";

interface TargetsTableProps {
  targets: ScrapingTarget[];
  onToggle: (id: string, enabled: boolean) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

export function TargetsTable({ targets, onToggle, onDelete }: TargetsTableProps) {
  if (targets.length === 0) {
    return (
      <div className="bg-black/40 border border-border/60 rounded-xl p-8 text-center text-muted text-sm">
        Nessun target configurato. Aggiungine uno qui sopra.
      </div>
    );
  }

  return (
    <div className="bg-black/40 border border-border/60 rounded-xl overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="text-left text-[11px] uppercase tracking-wider text-muted border-b border-border/60">
            <th className="px-3 py-2">Stato</th>
            <th className="px-3 py-2">Categoria</th>
            <th className="px-3 py-2">Città</th>
            <th className="px-3 py-2">Paese</th>
            <th className="px-3 py-2">Ultimo run</th>
            <th className="px-3 py-2 text-right">Leads</th>
            <th className="px-3 py-2 text-right">Azioni</th>
          </tr>
        </thead>
        <tbody>
          {targets.map((t) => (
            <TargetRow
              key={t.id}
              target={t}
              onToggle={onToggle}
              onDelete={onDelete}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
