import { Resend } from "resend";

const apiKey = process.env.RESEND_API_KEY;
const fromEmail = process.env.FROM_EMAIL ?? "onboarding@resend.dev";

export interface ContactSubmission {
  siteName: string;
  publishedUrl: string;
  visitorName: string;
  visitorEmail: string;
  visitorPhone: string;
  message: string;
}

export async function forwardSubmission(
  toEmail: string,
  submission: ContactSubmission,
): Promise<{ ok: boolean; error?: string }> {
  if (!apiKey) {
    return { ok: false, error: "RESEND_API_KEY not configured" };
  }

  const resend = new Resend(apiKey);

  const subject = `[${submission.siteName}] Nuovo contatto da: ${submission.visitorName || submission.visitorEmail || "anonimo"}`;

  const text = [
    `Hai ricevuto un nuovo contatto dal tuo sito ${submission.publishedUrl}:`,
    "",
    `Nome: ${submission.visitorName || "(non fornito)"}`,
    `Email: ${submission.visitorEmail || "(non fornita)"}`,
    `Telefono: ${submission.visitorPhone || "(non fornito)"}`,
    "",
    "Messaggio:",
    submission.message || "(vuoto)",
    "",
    "--",
    `Inviato automaticamente da agentsplatform`,
  ].join("\n");

  const html = `
    <div style="font-family: ui-sans-serif, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px;">
      <h2 style="font-family: serif; color: #1F2937;">Nuovo contatto dal tuo sito</h2>
      <p style="color: #6B7280;">Da <a href="${submission.publishedUrl}">${submission.publishedUrl}</a></p>
      <hr style="margin: 24px 0; border: 0; border-top: 1px solid #E5E7EB;">
      <p><strong>Nome:</strong> ${escapeHtml(submission.visitorName) || "(non fornito)"}</p>
      <p><strong>Email:</strong> ${escapeHtml(submission.visitorEmail) || "(non fornita)"}</p>
      <p><strong>Telefono:</strong> ${escapeHtml(submission.visitorPhone) || "(non fornito)"}</p>
      <h3 style="margin-top: 24px;">Messaggio</h3>
      <p style="white-space: pre-wrap; padding: 16px; background: #F9FAFB; border-left: 3px solid #5B4FCF; border-radius: 4px;">${escapeHtml(submission.message)}</p>
      <p style="font-size: 12px; color: #9CA3AF; margin-top: 32px;">
        Inviato automaticamente da agentsplatform.
      </p>
    </div>
  `;

  try {
    const { data, error } = await resend.emails.send({
      from: fromEmail,
      to: toEmail,
      subject,
      text,
      html,
    });
    if (error) return { ok: false, error: error.message };
    return { ok: !!data?.id };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : "unknown" };
  }
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
