import type { ContactsContent } from "@/types/site";

interface ContactBlockProps extends ContactsContent {
  variant?: "simple" | "form" | "map";
}

export function ContactBlock({
  phone,
  email,
  address,
  opening_hours,
  variant = "simple",
}: ContactBlockProps) {
  if (!phone && !email && !address) return null;

  return (
    <section
      className="py-16 px-6"
      style={{ backgroundColor: "var(--site-primary)", color: "white" }}
    >
      <div className="max-w-3xl mx-auto text-center">
        <h2 className="text-3xl font-bold mb-6">Contatti</h2>
        <div className="space-y-3 text-lg">
          {phone && (<div><a href={`tel:${phone}`} className="hover:underline">📞 {phone}</a></div>)}
          {email && (<div><a href={`mailto:${email}`} className="hover:underline">✉️ {email}</a></div>)}
          {address && <div>📍 {address}</div>}
          {opening_hours && <div>🕐 {opening_hours}</div>}
        </div>
        {variant === "form" && (
          <p className="mt-6 text-sm opacity-80">Form di contatto disponibile presto.</p>
        )}
      </div>
    </section>
  );
}
