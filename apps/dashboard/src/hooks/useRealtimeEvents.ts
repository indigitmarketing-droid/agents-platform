"use client";
import { useEffect, useState, useCallback } from "react";
import { supabase } from "@/lib/supabase";
import type { AgentEvent } from "@/types/events";

export function useRealtimeEvents(limit: number = 50) {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const loadInitial = async () => {
      const { data } = await supabase
        .from("events")
        .select("*")
        .order("created_at", { ascending: false })
        .limit(limit);
      if (data) setEvents(data as AgentEvent[]);
    };
    loadInitial();

    const channel = supabase
      .channel("events-realtime")
      .on("postgres_changes", { event: "INSERT", schema: "public", table: "events" }, (payload) => {
        const newEvent = payload.new as AgentEvent;
        setEvents((prev) => [newEvent, ...prev].slice(0, limit));
      })
      .on("postgres_changes", { event: "UPDATE", schema: "public", table: "events" }, (payload) => {
        const updated = payload.new as AgentEvent;
        setEvents((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
      })
      .subscribe((status) => { setIsConnected(status === "SUBSCRIBED"); });

    return () => { supabase.removeChannel(channel); };
  }, [limit]);

  const triggerAgent = useCallback(async (agentId: string) => {
    await supabase.from("events").insert({
      type: `${agentId}.trigger`,
      source_agent: "dashboard",
      target_agent: agentId,
      payload: {},
      status: "pending",
    });
  }, []);

  return { events, isConnected, triggerAgent };
}
