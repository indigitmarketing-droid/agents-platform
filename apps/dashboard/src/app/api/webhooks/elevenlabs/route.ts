import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import crypto from "crypto";

const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY!;
const webhookSecret = process.env.ELEVENLABS_WEBHOOK_SECRET ?? "";

interface WebhookPayload {
  conversation_id?: string;
  agent_id?: string;
  status?: string;
  transcript?: string;
  duration_seconds?: number;
  audio_url?: string;
}

function verifyHmac(body: string, signature: string | null): boolean {
  if (!signature || !webhookSecret) return false;
  const computed = crypto
    .createHmac("sha256", webhookSecret)
    .update(body)
    .digest("hex");
  const sigBuf = Buffer.from(signature, "utf8");
  const cmpBuf = Buffer.from(computed, "utf8");
  if (sigBuf.length !== cmpBuf.length) return false;
  return crypto.timingSafeEqual(sigBuf, cmpBuf);
}

function extractTranscriptText(raw: unknown): string {
  if (typeof raw === "string") return raw;
  if (Array.isArray(raw)) {
    return raw
      .map((turn) => {
        if (typeof turn === "object" && turn !== null) {
          const t = turn as { role?: string; message?: string };
          return `${t.role ?? "speaker"}: ${t.message ?? ""}`;
        }
        return String(turn);
      })
      .join("\n");
  }
  return "";
}

export async function POST(req: Request) {
  const body = await req.text();
  const signature = req.headers.get("x-elevenlabs-signature");

  if (!verifyHmac(body, signature)) {
    return NextResponse.json({ error: "invalid signature" }, { status: 401 });
  }

  let payload: WebhookPayload;
  try {
    const parsed = JSON.parse(body);
    payload = parsed.data ?? parsed;
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400 });
  }

  const conversationId = payload.conversation_id;
  if (!conversationId) {
    return NextResponse.json({ error: "missing conversation_id" }, { status: 400 });
  }

  const supabase = createClient(supabaseUrl, supabaseServiceKey);

  // Dedupe guard
  const existing = await supabase
    .from("events")
    .select("id")
    .eq("type", "setting.call_completed")
    .filter("payload->>conversation_id", "eq", conversationId)
    .maybeSingle();

  if (existing.data) {
    return NextResponse.json({ ok: true, deduped: true });
  }

  const transcriptText = extractTranscriptText(payload.transcript);

  // UPDATE call_logs and capture lead_id
  const { data: callLog, error: updateErr } = await supabase
    .from("call_logs")
    .update({
      status: "completed",
      transcript: transcriptText,
      duration_seconds: payload.duration_seconds ?? null,
      audio_url: payload.audio_url ?? null,
      ended_at: new Date().toISOString(),
    })
    .eq("conversation_id", conversationId)
    .select("lead_id")
    .maybeSingle();

  if (updateErr || !callLog) {
    return NextResponse.json(
      { error: "call_log not found", details: updateErr?.message },
      { status: 404 },
    );
  }

  // INSERT event for Setting Agent worker
  const { error: insertErr } = await supabase.from("events").insert({
    type: "setting.call_completed",
    source_agent: "dashboard",
    target_agent: "setting",
    payload: {
      lead_id: callLog.lead_id,
      conversation_id: conversationId,
      transcript: transcriptText,
      duration_seconds: payload.duration_seconds ?? 0,
      audio_url: payload.audio_url ?? null,
    },
    status: "pending",
  });

  if (insertErr) {
    return NextResponse.json(
      { error: "event insert failed", details: insertErr.message },
      { status: 500 },
    );
  }

  return NextResponse.json({ ok: true });
}
