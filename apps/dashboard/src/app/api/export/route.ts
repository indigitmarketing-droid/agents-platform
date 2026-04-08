import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import * as XLSX from "xlsx";

const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_KEY!;

export async function GET() {
  try {
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Fetch all leads
    const { data: leads, error: leadsError } = await supabase
      .from("leads")
      .select("*")
      .order("created_at", { ascending: false });

    if (leadsError) {
      return NextResponse.json({ error: leadsError.message }, { status: 500 });
    }

    // Fetch all events for context (sales data)
    const { data: events } = await supabase
      .from("events")
      .select("*")
      .in("type", ["setting.sale_completed", "setting.sale_failed"])
      .order("created_at", { ascending: false });

    // Build a map of lead_id -> sale info
    const salesMap = new Map<string, { amount?: number; result: string }>();
    for (const event of events || []) {
      const leadId = (event.payload as Record<string, unknown>)?.lead_id as string;
      if (leadId && !salesMap.has(leadId)) {
        if (event.type === "setting.sale_completed") {
          salesMap.set(leadId, {
            amount: (event.payload as Record<string, number>).amount,
            result: "Venduto",
          });
        } else {
          salesMap.set(leadId, { result: "Non venduto" });
        }
      }
    }

    // Format data for Excel
    const rows = (leads || []).map((lead) => {
      const sale = salesMap.get(lead.id);
      return {
        "Azienda": lead.company_name,
        "Telefono": lead.phone,
        "Email": lead.email || "",
        "Ha Sito Web": lead.has_website ? "Sì" : "No",
        "Stato": lead.status,
        "Fonte": lead.source,
        "Vendita": sale?.result || "-",
        "Importo (€)": sale?.amount || "",
        "Data": new Date(lead.created_at).toLocaleDateString("it-IT"),
      };
    });

    // Create Excel workbook
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(rows);

    // Set column widths
    ws["!cols"] = [
      { wch: 25 }, // Azienda
      { wch: 18 }, // Telefono
      { wch: 25 }, // Email
      { wch: 12 }, // Ha Sito Web
      { wch: 12 }, // Stato
      { wch: 15 }, // Fonte
      { wch: 14 }, // Vendita
      { wch: 12 }, // Importo
      { wch: 12 }, // Data
    ];

    XLSX.utils.book_append_sheet(wb, ws, "Leads");

    // Generate buffer
    const buf = XLSX.write(wb, { type: "buffer", bookType: "xlsx" });

    const today = new Date().toISOString().split("T")[0];
    return new NextResponse(buf, {
      headers: {
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Content-Disposition": `attachment; filename="leads-${today}.xlsx"`,
      },
    });
  } catch (error) {
    console.error("Export error:", error);
    return NextResponse.json({ error: "Export failed" }, { status: 500 });
  }
}
