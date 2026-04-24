import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_KEY!;

export async function POST() {
  const supabase = createClient(supabaseUrl, supabaseKey);
  const { data, error } = await supabase
    .from("events")
    .insert({
      type: "scraping.trigger",
      source_agent: "dashboard",
      target_agent: "scraping",
      payload: {},
      status: "pending",
    })
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ event: data });
}
