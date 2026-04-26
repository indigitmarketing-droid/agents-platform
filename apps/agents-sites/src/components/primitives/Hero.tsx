import type { HeroContent } from "@/types/site";

interface HeroProps extends HeroContent {
  variant?: "centered-text" | "image-bg";
}

export function Hero({
  headline,
  subheadline,
  cta_text,
  cta_link,
  image_url,
  variant = "centered-text",
}: HeroProps) {
  if (!headline) return null;

  const ctaHref = cta_link ?? "#contact";

  if (variant === "image-bg" && image_url) {
    return (
      <section
        className="relative min-h-[80vh] flex items-center justify-center text-white overflow-hidden"
        style={{
          backgroundImage: `linear-gradient(135deg, rgba(0,0,0,0.65), rgba(0,0,0,0.4)), url(${image_url})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      >
        <div className="text-center max-w-3xl px-6 section-fade-in">
          <h1 className="font-display text-5xl sm:text-7xl font-bold mb-6 leading-tight">{headline}</h1>
          {subheadline && <p className="text-xl sm:text-2xl mb-10 opacity-95 max-w-2xl mx-auto leading-relaxed">{subheadline}</p>}
          {cta_text && (
            <a
              href={ctaHref}
              className="cta-btn inline-block px-8 py-4 rounded-lg font-semibold text-lg"
              style={{ backgroundColor: "var(--site-primary)", color: "white" }}
            >
              {cta_text}
            </a>
          )}
        </div>
      </section>
    );
  }

  return (
    <section
      className="relative min-h-[70vh] flex items-center justify-center px-6 py-24 overflow-hidden"
      style={{
        background: `linear-gradient(180deg, var(--site-bg) 0%, color-mix(in srgb, var(--site-accent) 8%, var(--site-bg)) 100%)`,
      }}
    >
      <div className="text-center max-w-3xl section-fade-in">
        <h1 className="font-display text-5xl sm:text-7xl font-bold mb-6 leading-tight" style={{ color: "var(--site-primary)" }}>
          {headline}
        </h1>
        {subheadline && <p className="text-xl sm:text-2xl mb-10 opacity-80 leading-relaxed">{subheadline}</p>}
        {cta_text && (
          <a
            href={ctaHref}
            className="cta-btn inline-block px-8 py-4 rounded-lg font-semibold text-lg"
            style={{ backgroundColor: "var(--site-primary)", color: "white" }}
          >
            {cta_text}
          </a>
        )}
      </div>
    </section>
  );
}
