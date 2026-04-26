import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { forwardSubmission } from "@/lib/email";

const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY!;
const adminFallbackEmail = process.env.ADMIN_FALLBACK_EMAIL ?? "indigit.marketing@gmail.com";

interface RequestBody {
  site_id?: string;
  visitor_name?: string;
  visitor_email?: string;
  visitor_phone?: string;
  message?: string;
}

export async function POST(req: Request) {
  let body: RequestBody;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const { site_id, visitor_name, visitor_email, visitor_phone, message } = body;

  if (!site_id || !message || message.trim().length === 0) {
    return NextResponse.json(
      { error: "site_id and message are required" },
      { status: 400 },
    );
  }

  const supabase = createClient(supabaseUrl, supabaseServiceKey);

  const { data: site, error: siteError } = await supabase
    .from("sites")
    .select("id, slug, lead_id, content, published_url")
    .eq("id", site_id)
    .maybeSingle();

  if (siteError || !site) {
    return NextResponse.json({ error: "Site not found" }, { status: 404 });
  }

  const { data: lead } = await supabase
    .from("leads")
    .select("email, company_name")
    .eq("id", site.lead_id)
    .maybeSingle();

  const ownerEmail = lead?.email ?? adminFallbackEmail;
  const siteName =
    lead?.company_name ??
    (typeof site.content === "object" && site.content && "hero" in site.content
      ? (site.content as { hero?: { headline?: string } }).hero?.headline
      : null) ??
    site.slug;

  const result = await forwardSubmission(ownerEmail, {
    siteName: String(siteName),
    publishedUrl: site.published_url ?? `https://agents-sites.vercel.app/s/${site.slug}`,
    visitorName: visitor_name ?? "",
    visitorEmail: visitor_email ?? "",
    visitorPhone: visitor_phone ?? "",
    message,
  });

  await supabase.from("site_submissions").insert({
    site_id: site.id,
    visitor_name: visitor_name || null,
    visitor_email: visitor_email || null,
    visitor_phone: visitor_phone || null,
    message,
    forwarded_to_email: ownerEmail,
    forwarded_at: result.ok ? new Date().toISOString() : null,
    forward_error: result.ok ? null : result.error ?? "unknown",
  });

  await supabase.from("events").insert({
    type: "site.lead_received",
    source_agent: "agents-sites",
    target_agent: null,
    payload: {
      site_id: site.id,
      lead_id: site.lead_id,
      forwarded: result.ok,
    },
    status: "completed",
  });

  if (!result.ok) {
    return NextResponse.json(
      { ok: false, error: result.error ?? "forward failed" },
      { status: 500 },
    );
  }

  return NextResponse.json({ ok: true });
}
