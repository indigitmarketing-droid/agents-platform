import type { AboutContent } from "@/types/site";

export function About({ title, body }: AboutContent) {
  if (!title && !body) return null;
  return (
    <section className="py-16 px-6 max-w-3xl mx-auto text-center">
      {title && (
        <h2 className="text-3xl font-bold mb-6" style={{ color: "var(--site-primary)" }}>
          {title}
        </h2>
      )}
      {body && <p className="text-lg leading-relaxed opacity-80">{body}</p>}
    </section>
  );
}
