import { NextResponse } from "next/server";
import Stripe from "stripe";
import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import crypto from "crypto";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

function getStripe(): Stripe {
  const key = process.env.STRIPE_SECRET_KEY;
  if (!key) throw new Error("STRIPE_SECRET_KEY not set");
  return new Stripe(key);
}

function getSupabase(): SupabaseClient {
  const url = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_KEY;
  if (!url || !key) throw new Error("Supabase env vars not set");
  return createClient(url, key);
}

function generateRandomPassword(length = 14): string {
  return crypto.randomBytes(length).toString("base64url").slice(0, length);
}

async function sendWelcomeEmail(opts: {
  email: string;
  companyName: string;
  password: string;
  dashboardUrl: string;
  siteUrl: string;
}): Promise<boolean> {
  const resendKey = process.env.RESEND_API_KEY;
  if (!resendKey) return false;
  const html = `<!doctype html><html><body style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px">
<h1>Your website is live, ${opts.companyName}!</h1>
<p>Your website is published at: <a href="${opts.siteUrl}">${opts.siteUrl}</a></p>
<h2>Dashboard access</h2>
<p>URL: <a href="${opts.dashboardUrl}">${opts.dashboardUrl}</a><br>
Email: <code>${opts.email}</code><br>
Temporary password: <code>${opts.password}</code></p>
<p style="color:#666;font-size:14px">You'll be required to set a new password on your first login.</p>
</body></html>`;
  const text = `Your website is live, ${opts.companyName}!\n\nWebsite: ${opts.siteUrl}\nDashboard: ${opts.dashboardUrl}\nEmail: ${opts.email}\nTemporary password: ${opts.password}\n\nYou'll be required to set a new password on your first login.`;

  const resp = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${resendKey}`,
    },
    body: JSON.stringify({
      from: "onboarding@resend.dev",
      to: [opts.email],
      subject: `Your ${opts.companyName} website is ready`,
      html,
      text,
    }),
  });
  return resp.ok;
}

export async function POST(req: Request) {
  const body = await req.text();
  const signature = req.headers.get("stripe-signature");
  if (!signature) {
    return NextResponse.json({ error: "missing signature" }, { status: 401 });
  }

  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!webhookSecret) {
    return NextResponse.json({ error: "webhook secret not configured" }, { status: 500 });
  }

  const stripe = getStripe();

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
  } catch {
    return NextResponse.json({ error: "invalid signature" }, { status: 401 });
  }

  const supabase = getSupabase();

  const { data: existing } = await supabase
    .from("stripe_events")
    .select("id")
    .eq("stripe_event_id", event.id)
    .maybeSingle();
  if (existing) {
    return NextResponse.json({ ok: true, deduped: true });
  }

  const { error: insertEventErr } = await supabase
    .from("stripe_events")
    .insert({
      stripe_event_id: event.id,
      event_type: event.type,
      payload: event.data as unknown as Record<string, unknown>,
    });
  if (insertEventErr && !insertEventErr.message.includes("duplicate")) {
    return NextResponse.json({ error: insertEventErr.message }, { status: 500 });
  }

  if (event.type === "checkout.session.completed") {
    return await handleCheckoutCompleted(
      event.data.object as Stripe.Checkout.Session,
      event.id,
      supabase,
    );
  }

  if (event.type === "charge.refunded") {
    return NextResponse.json({ ok: true, deferred: "F1.1 refund handler" });
  }

  return NextResponse.json({ ok: true, ignored: event.type });
}

async function handleCheckoutCompleted(
  session: Stripe.Checkout.Session,
  eventId: string,
  supabase: SupabaseClient,
) {
  const siteId = session.metadata?.site_id;
  if (!siteId) {
    return NextResponse.json({ error: "no site_id metadata" }, { status: 400 });
  }

  const { data: sites } = await supabase
    .from("sites")
    .update({
      payment_status: "paid",
      paid_at: new Date().toISOString(),
      stripe_payment_intent_id: session.payment_intent as string,
      stripe_customer_id: session.customer as string,
    })
    .eq("id", siteId)
    .eq("payment_status", "unpaid")
    .select("id, slug, lead_id");

  if (!sites || sites.length === 0) {
    return NextResponse.json({ ok: true, already_processed: true });
  }
  const site = sites[0];

  const { data: leads } = await supabase
    .from("leads")
    .select("id, email, company_name")
    .eq("id", site.lead_id)
    .limit(1);
  const lead = leads?.[0];
  if (!lead || !lead.email) {
    return NextResponse.json({ error: "lead has no email" }, { status: 400 });
  }

  const password = generateRandomPassword();
  let authUserId: string | undefined;

  const { data: created, error: createErr } =
    await supabase.auth.admin.createUser({
      email: lead.email,
      password,
      email_confirm: true,
      user_metadata: {
        lead_id: lead.id,
        site_id: siteId,
        company_name: lead.company_name,
        password_changed: false,
        onboarded_at: new Date().toISOString(),
        stripe_customer_id: session.customer,
        paid_at: new Date().toISOString(),
      },
    });

  if (createErr) {
    if (createErr.message?.includes("already registered") || createErr.message?.includes("already exists")) {
      const { data: list } = await supabase.auth.admin.listUsers();
      authUserId = list?.users?.find((u) => u.email === lead.email)?.id;
    } else {
      return NextResponse.json({ error: createErr.message }, { status: 500 });
    }
  } else {
    authUserId = created?.user?.id;
  }

  if (!authUserId) {
    return NextResponse.json({ error: "could not resolve auth user" }, { status: 500 });
  }

  await supabase.from("sites").update({ owner_user_id: authUserId }).eq("id", siteId);

  const dashboardUrl = process.env.CUSTOMER_DASHBOARD_URL ||
    "https://customer-dashboard-ashen.vercel.app";
  const sitesBaseUrl = "https://agents-sites.vercel.app";
  const emailSent = await sendWelcomeEmail({
    email: lead.email,
    companyName: lead.company_name,
    password,
    dashboardUrl,
    siteUrl: `${sitesBaseUrl}/s/${site.slug}`,
  });

  await supabase.from("stripe_events").update({
    processed_at: new Date().toISOString(),
    site_id: siteId,
  }).eq("stripe_event_id", eventId);

  await supabase.from("events").insert({
    type: "customer.onboarded",
    source_agent: "dashboard",
    payload: {
      site_id: siteId,
      auth_user_id: authUserId,
      email: lead.email,
      paid_at: new Date().toISOString(),
      email_sent: emailSent,
    },
    status: "pending",
  });

  return NextResponse.json({ ok: true, onboarded: authUserId, email_sent: emailSent });
}
