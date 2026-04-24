"use client";

import { Header } from "@/components/Header";
import { NavTabs } from "@/components/scraping/NavTabs";
import { StatsBar } from "@/components/scraping/StatsBar";
import { AddTargetForm } from "@/components/scraping/AddTargetForm";
import { TargetsTable } from "@/components/scraping/TargetsTable";
import { useScrapingTargets } from "@/hooks/useScrapingTargets";
import { useState } from "react";

export default function ScrapingConfigPage() {
  const { targets, loading, addTarget, updateTarget, deleteTarget, runNow } =
    useScrapingTargets();
  const [running, setRunning] = useState(false);

  const handleRunNow = async () => {
    setRunning(true);
    try {
      await runNow();
      alert("Trigger inviato! Lo scraping partirà tra qualche secondo.");
    } catch (e) {
      alert("Errore: " + (e instanceof Error ? e.message : "unknown"));
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header agentCount={3} isConnected={true} />
      <NavTabs />
      <div className="p-6 space-y-6 max-w-6xl mx-auto">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[1.2px] text-accent mb-4">
            Overview
          </div>
          <StatsBar targets={targets} />
        </div>

        <AddTargetForm onAdd={addTarget} />

        <div>
          <div className="flex justify-between items-center mb-4">
            <div className="text-[11px] font-semibold uppercase tracking-[1.2px] text-accent">
              Targets configurati
            </div>
            <button
              onClick={handleRunNow}
              disabled={running || targets.filter((t) => t.enabled).length === 0}
              className="py-1.5 px-4 border border-accent/30 bg-accent/10 text-accent-light rounded-lg text-xs font-medium hover:bg-accent/25 hover:border-accent transition-colors cursor-pointer disabled:opacity-50"
            >
              {running ? "Invio..." : "▶ Esegui ora tutti"}
            </button>
          </div>
          {loading ? (
            <div className="text-center text-muted py-4">Caricamento...</div>
          ) : (
            <TargetsTable
              targets={targets}
              onToggle={(id, enabled) => updateTarget(id, { enabled })}
              onDelete={deleteTarget}
            />
          )}
        </div>
      </div>
    </div>
  );
}
