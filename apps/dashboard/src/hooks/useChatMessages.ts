"use client";

import { useState, useEffect, useCallback } from "react";
import { supabase } from "@/lib/supabase";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export function useChatMessages(agentId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);

  // Load history from Supabase on mount
  useEffect(() => {
    let cancelled = false;

    async function loadHistory() {
      setIsLoadingHistory(true);
      const { data } = await supabase
        .from("messages")
        .select("id, role, content, created_at")
        .eq("agent_id", agentId)
        .order("created_at", { ascending: true })
        .limit(50);

      if (!cancelled) {
        setMessages((data as ChatMessage[]) ?? []);
        setIsLoadingHistory(false);
      }
    }

    loadHistory();
    return () => {
      cancelled = true;
    };
  }, [agentId]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isLoading) return;

      // Optimistic: add user message immediately
      const tempUserMsg: ChatMessage = {
        id: `temp-user-${Date.now()}`,
        role: "user",
        content: text,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempUserMsg]);
      setIsLoading(true);

      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ agent_id: agentId, message: text }),
        });

        const data = await res.json();

        if (!res.ok) throw new Error(data.error ?? "Request failed");

        const assistantMsg: ChatMessage = {
          id: `temp-assistant-${Date.now()}`,
          role: "assistant",
          content: data.response,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        console.error("[useChatMessages] sendMessage error:", err);
        // Remove optimistic message on error
        setMessages((prev) =>
          prev.filter((m) => m.id !== tempUserMsg.id)
        );
      } finally {
        setIsLoading(false);
      }
    },
    [agentId, isLoading]
  );

  return { messages, isLoading, isLoadingHistory, sendMessage };
}
