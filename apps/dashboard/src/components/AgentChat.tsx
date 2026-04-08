"use client";

import { useEffect, useRef, useState } from "react";
import { useChatMessages } from "@/hooks/useChatMessages";

const AGENT_CONFIG: Record<string, { icon: string; label: string }> = {
  scraping: { icon: "🔍", label: "Web Scraping" },
  setting: { icon: "📞", label: "Setting" },
  builder: { icon: "🏗️", label: "Website Builder" },
};

interface AgentChatProps {
  agentId: string;
  onClose: () => void;
}

export function AgentChat({ agentId, onClose }: AgentChatProps) {
  const config = AGENT_CONFIG[agentId] ?? { icon: "🤖", label: agentId };
  const { messages, isLoading, isLoadingHistory, sendMessage } =
    useChatMessages(agentId);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Focus input on open
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || isLoading) return;
    setInput("");
    sendMessage(text);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  }

  return (
    <div className="fixed right-6 bottom-6 w-[400px] max-h-[600px] flex flex-col rounded-2xl border border-border shadow-2xl bg-[#0d0d14] z-50 overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-border bg-surface/60 flex-shrink-0">
        <div className="w-8 h-8 rounded-lg bg-accent/15 flex items-center justify-center text-base">
          {config.icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold text-zinc-100 leading-tight">
            {config.label}
          </div>
          <div className="text-[10px] text-muted">Agente AI</div>
        </div>
        <button
          onClick={onClose}
          className="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-surface-hover text-muted hover:text-zinc-200 transition-colors cursor-pointer text-base"
          aria-label="Chiudi chat"
        >
          ✕
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-0">
        {isLoadingHistory ? (
          <div className="flex justify-center items-center h-16">
            <span className="text-xs text-muted animate-pulse">
              Caricamento…
            </span>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex justify-center items-center h-20">
            <span className="text-xs text-muted text-center px-4">
              Ciao! Sono {config.label}. Come posso aiutarti?
            </span>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[82%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-accent text-white rounded-br-sm"
                    : "bg-[#1a1a2e] text-zinc-200 border border-border/60 rounded-bl-sm"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))
        )}

        {/* Loading dots */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-[#1a1a2e] border border-border/60 rounded-2xl rounded-bl-sm px-4 py-3 flex gap-1 items-center">
              <span
                className="w-1.5 h-1.5 bg-accent-light rounded-full animate-bounce"
                style={{ animationDelay: "0ms" }}
              />
              <span
                className="w-1.5 h-1.5 bg-accent-light rounded-full animate-bounce"
                style={{ animationDelay: "150ms" }}
              />
              <span
                className="w-1.5 h-1.5 bg-accent-light rounded-full animate-bounce"
                style={{ animationDelay: "300ms" }}
              />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="flex gap-2 px-4 py-3 border-t border-border bg-surface/40 flex-shrink-0"
      >
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading || isLoadingHistory}
          placeholder="Scrivi un messaggio…"
          className="flex-1 bg-black/40 border border-border rounded-xl px-3.5 py-2 text-sm text-zinc-100 placeholder-muted focus:outline-none focus:border-accent/60 disabled:opacity-50 transition-colors"
        />
        <button
          type="submit"
          disabled={isLoading || isLoadingHistory || !input.trim()}
          className="w-9 h-9 flex items-center justify-center rounded-xl bg-accent hover:bg-accent-light disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer flex-shrink-0"
          aria-label="Invia"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            className="text-white"
          >
            <path
              d="M14 8L2 2l2.5 6L2 14l12-6z"
              fill="currentColor"
            />
          </svg>
        </button>
      </form>
    </div>
  );
}
