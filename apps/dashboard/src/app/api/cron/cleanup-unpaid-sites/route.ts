import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(req: Request) {
  const cronSecret = process.env.CRON_SECRET;
  const authHeader = req.headers.get("authorization");
  if (!cronSecret || authHeader !== `Bearer ${cronSecret}`) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY;
  if (!supabaseUrl || !supabaseServiceKey) {
    return NextResponse.json({ error: "supabase env not set" }, { status: 500 });
  }

  const supabase = createClient(supabaseUrl, supabaseServiceKey);
  const cutoff = new Date(Date.now() - 48 * 3600 * 1000).toISOString();

  const { data: expired, error: fetchErr } = await supabase
    .from("sites")
    .select("id, slug, lead_id")
    .eq("payment_status", "unpaid")
    .lt("published_at", cutoff);

  if (fetchErr) {
    return NextResponse.json({ error: fetchErr.message }, { status: 500 });
  }

  let deletedCount = 0;
  for (const site of expired ?? []) {
    const { error: delErr } = await supabase
      .from("sites").delete().eq("id", site.id);
    if (delErr) continue;

    await supabase.from("events").insert({
      type: "site.deleted_unpaid",
      source_agent: "cron",
      payload: {
        site_id: site.id,
        slug: site.slug,
        reason: "48h_grace_expired",
      },
      status: "pending",
    });

    await supabase.from("leads")
      .update({ status: "expired_no_pay" })
      .eq("id", site.lead_id);

    deletedCount++;
  }

  return NextResponse.json({ ok: true, deleted_count: deletedCount });
}

export const GET = POST;
