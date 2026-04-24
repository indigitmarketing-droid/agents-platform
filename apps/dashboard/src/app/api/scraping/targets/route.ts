import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_KEY!;

function client() {
  return createClient(supabaseUrl, supabaseKey);
}

export async function GET() {
  const { data, error } = await client()
    .from("scraping_targets")
    .select("*")
    .order("created_at", { ascending: false });

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ targets: data });
}

export async function POST(req: Request) {
  const body = await req.json();
  const required = ["category", "category_type", "city", "country_code", "timezone"];
  for (const key of required) {
    if (!body[key]) {
      return NextResponse.json({ error: `Missing field: ${key}` }, { status: 400 });
    }
  }

  const { data, error } = await client()
    .from("scraping_targets")
    .insert({
      category: body.category,
      category_type: body.category_type,
      city: body.city,
      country_code: body.country_code,
      timezone: body.timezone,
      enabled: body.enabled ?? true,
    })
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ target: data }, { status: 201 });
}
