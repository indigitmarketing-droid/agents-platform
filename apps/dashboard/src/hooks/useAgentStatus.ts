"use client";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import type { Agent } from "@/types/events";

const OFFLINE_THRESHOLD_MS = 90_000;

export function useAgentStatus() {
  const [agents, setAgents] = useState<Agent[]>([]);

  useEffect(() => {
    const loadAgents = async () => {
      const { data } = await supabase.from("agents").select("*");
      if (data) setAgents(data as Agent[]);
    };
    loadAgents();

    const channel = supabase
      .channel("agents-realtime")
      .on("postgres_changes", { event: "UPDATE", schema: "public", table: "agents" }, (payload) => {
        const updated = payload.new as Agent;
        setAgents((prev) => prev.map((a) => (a.id === updated.id ? updated : a)));
      })
      .subscribe();

    const interval = setInterval(() => {
      setAgents((prev) => prev.map((agent) => {
        if (!agent.last_heartbeat) return { ...agent, status: "offline" };
        const elapsed = Date.now() - new Date(agent.last_heartbeat).getTime();
        if (elapsed > OFFLINE_THRESHOLD_MS && agent.status !== "offline") {
          return { ...agent, status: "offline" };
        }
        return agent;
      }));
    }, 30_000);

    return () => { supabase.removeChannel(channel); clearInterval(interval); };
  }, []);

  return { agents };
}
