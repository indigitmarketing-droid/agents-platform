import { NextRequest, NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { createClient } from "@supabase/supabase-js";

const SYSTEM_PROMPTS: Record<string, string> = {
  scraping:
    "Sei l'Agente Web Scraping. Trovi lead B2B (aziende senza sito web). Rispondi in italiano, conciso e professionale.",
  setting:
    "Sei l'Agente Setting. Contatti lead, proponi siti web gratuiti, gestisci follow-up WhatsApp. Rispondi in italiano, conciso e professionale.",
  builder:
    "Sei l'Agente Website Builder. Analizzi target, crei copy e generi siti web. Rispondi in italiano, conciso e professionale.",
};

function getSupabaseServer() {
  const url =
    process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const key = process.env.SUPABASE_SERVICE_KEY!;
  return createClient(url, key);
}

export async function POST(req: NextRequest) {
  try {
    const { agent_id, message } = await req.json();

    if (!agent_id || !message) {
      return NextResponse.json(
        { error: "Missing agent_id or message" },
        { status: 400 }
      );
    }

    const supabase = getSupabaseServer();

    // Load last 20 messages for context
    const { data: history } = await supabase
      .from("messages")
      .select("role, content")
      .eq("agent_id", agent_id)
      .order("created_at", { ascending: false })
      .limit(20);

    const historyMessages = (history ?? [])
      .reverse()
      .map((m: { role: string; content: string }) => ({
        role: m.role as "user" | "assistant",
        content: m.content,
      }));

    // Save user message
    await supabase.from("messages").insert({
      agent_id,
      role: "user",
      content: message,
    });

    const anthropic = new Anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY,
    });

    const systemPrompt =
      SYSTEM_PROMPTS[agent_id] ??
      "Sei un agente AI. Rispondi in italiano, conciso e professionale.";

    const response = await anthropic.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 1024,
      system: systemPrompt,
      messages: [
        ...historyMessages,
        { role: "user", content: message },
      ],
    });

    const assistantText =
      response.content[0]?.type === "text" ? response.content[0].text : "";

    // Save assistant response
    await supabase.from("messages").insert({
      agent_id,
      role: "assistant",
      content: assistantText,
    });

    return NextResponse.json({ response: assistantText });
  } catch (err) {
    console.error("[chat/route] error:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
