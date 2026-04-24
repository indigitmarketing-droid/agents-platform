"use client";

import { useEffect, useState, useCallback } from "react";
import { supabase } from "@/lib/supabase";

export interface ScrapingTarget {
  id: string;
  category: string;
  category_type: string;
  city: string;
  country_code: string;
  timezone: string;
  enabled: boolean;
  last_run_at: string | null;
  total_leads_found: number;
  created_at: string;
}

export function useScrapingTargets() {
  const [targets, setTargets] = useState<ScrapingTarget[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const { data } = await supabase
        .from("scraping_targets")
        .select("*")
        .order("created_at", { ascending: false });
      if (data) setTargets(data as ScrapingTarget[]);
      setLoading(false);
    };
    load();

    const channel = supabase
      .channel("scraping-targets-realtime")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "scraping_targets" },
        (p) => setTargets((prev) => [p.new as ScrapingTarget, ...prev])
      )
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "scraping_targets" },
        (p) => {
          const updated = p.new as ScrapingTarget;
          setTargets((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
        }
      )
      .on(
        "postgres_changes",
        { event: "DELETE", schema: "public", table: "scraping_targets" },
        (p) => {
          const deleted = p.old as { id: string };
          setTargets((prev) => prev.filter((t) => t.id !== deleted.id));
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  const addTarget = useCallback(async (input: {
    category: string;
    category_type: string;
    city: string;
    country_code: string;
    timezone: string;
  }) => {
    const res = await fetch("/api/scraping/targets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Failed to create target");
    }
  }, []);

  const updateTarget = useCallback(
    async (id: string, updates: Partial<Pick<ScrapingTarget, "enabled">>) => {
      const res = await fetch(`/api/scraping/targets/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
      });
      if (!res.ok) throw new Error("Failed to update");
    },
    []
  );

  const deleteTarget = useCallback(async (id: string) => {
    const res = await fetch(`/api/scraping/targets/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to delete");
  }, []);

  const runNow = useCallback(async () => {
    const res = await fetch("/api/scraping/run-now", { method: "POST" });
    if (!res.ok) throw new Error("Failed to trigger");
  }, []);

  return { targets, loading, addTarget, updateTarget, deleteTarget, runNow };
}
