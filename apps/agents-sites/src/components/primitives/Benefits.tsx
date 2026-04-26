import type { BenefitsContent } from "@/types/site";

export function Benefits({ title, items }: BenefitsContent) {
  if ((!title) && (!items || items.length === 0)) return null;

  const validItems = (items ?? []).filter((it) => it.title);

  return (
    <section
      className="section-fade-in py-24 px-6"
      style={{ backgroundColor: "color-mix(in srgb, var(--site-primary) 4%, var(--site-bg))" }}
    >
      <div className="max-w-6xl mx-auto">
        {title && (
          <h2 className="font-display text-4xl sm:text-5xl font-bold mb-12 text-center" style={{ color: "var(--site-primary)" }}>
            {title}
          </h2>
        )}
        {validItems.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {validItems.map((it, i) => (
              <div
                key={i}
                className="p-8 rounded-2xl bg-white border"
                style={{ borderColor: "color-mix(in srgb, var(--site-accent) 25%, transparent)" }}
              >
                <h3 className="font-semibold text-xl mb-3" style={{ color: "var(--site-primary)" }}>
                  {it.title}
                </h3>
                {it.description && (
                  <p className="opacity-75 leading-relaxed">{it.description}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
