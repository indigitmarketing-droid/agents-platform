import type { SolutionContent } from "@/types/site";

export function Solution({ title, body, cta_text, cta_link }: SolutionContent) {
  if (!title && !body) return null;

  return (
    <section className="section-fade-in py-24 px-6 max-w-3xl mx-auto text-center">
      {title && (
        <h2 className="font-display text-4xl sm:text-5xl font-bold mb-8" style={{ color: "var(--site-primary)" }}>
          {title}
        </h2>
      )}
      {body && (
        <p className="text-lg sm:text-xl leading-relaxed opacity-85 mb-10">
          {body}
        </p>
      )}
      {cta_text && (
        <a
          href={cta_link ?? "#contact"}
          className="cta-btn inline-block px-8 py-4 rounded-lg font-semibold text-base"
          style={{ backgroundColor: "var(--site-primary)", color: "white" }}
        >
          {cta_text}
        </a>
      )}
    </section>
  );
}
