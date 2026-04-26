import type { ProblemContent } from "@/types/site";

export function Problem({ title, body, bullets }: ProblemContent) {
  if (!title && !body && (!bullets || bullets.length === 0)) return null;

  return (
    <section className="section-fade-in py-24 px-6 max-w-3xl mx-auto">
      {title && (
        <h2 className="font-display text-4xl sm:text-5xl font-bold mb-8 text-center" style={{ color: "var(--site-primary)" }}>
          {title}
        </h2>
      )}
      {body && (
        <p className="text-lg sm:text-xl leading-relaxed opacity-80 mb-8 text-center">
          {body}
        </p>
      )}
      {bullets && bullets.length > 0 && (
        <ul className="space-y-3 max-w-xl mx-auto">
          {bullets.map((b, i) => (
            <li key={i} className="flex items-start gap-3 text-base sm:text-lg">
              <span className="flex-shrink-0 mt-1.5 w-2 h-2 rounded-full" style={{ backgroundColor: "var(--site-accent)" }} />
              <span className="opacity-90">{b}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
