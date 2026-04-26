import type { ServiceItem } from "@/types/site";

interface ServicesListProps {
  items?: ServiceItem[];
  variant?: "grid" | "list-with-prices";
}

export function ServicesList({ items, variant = "grid" }: ServicesListProps) {
  if (!items || items.length === 0) return null;

  if (variant === "list-with-prices") {
    return (
      <section className="py-16 px-6 max-w-4xl mx-auto">
        <h2 className="text-3xl font-bold mb-8 text-center" style={{ color: "var(--site-primary)" }}>
          Servizi
        </h2>
        <div className="space-y-4">
          {items.map((item, i) => (
            item.title ? (
              <div key={i} className="flex justify-between items-start border-b pb-4" style={{ borderColor: "var(--site-accent)" }}>
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{item.title}</h3>
                  {item.description && <p className="opacity-70 text-sm mt-1">{item.description}</p>}
                </div>
                {item.price && (
                  <span className="font-bold ml-4" style={{ color: "var(--site-accent)" }}>
                    {item.price}
                  </span>
                )}
              </div>
            ) : null
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="py-16 px-6 max-w-6xl mx-auto">
      <h2 className="text-3xl font-bold mb-8 text-center" style={{ color: "var(--site-primary)" }}>
        I nostri servizi
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {items.map((item, i) => (
          item.title ? (
            <div key={i} className="p-6 rounded-lg border" style={{ borderColor: "var(--site-accent)" }}>
              <h3 className="font-semibold text-lg mb-2">{item.title}</h3>
              {item.description && <p className="opacity-70">{item.description}</p>}
            </div>
          ) : null
        ))}
      </div>
    </section>
  );
}
