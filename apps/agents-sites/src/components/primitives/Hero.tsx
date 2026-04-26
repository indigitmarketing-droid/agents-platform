import type { HeroContent } from "@/types/site";

interface HeroProps extends HeroContent {
  variant?: "centered-text" | "image-bg";
}

export function Hero({
  headline,
  subheadline,
  cta_text,
  image_url,
  variant = "centered-text",
}: HeroProps) {
  if (!headline) return null;

  if (variant === "image-bg" && image_url) {
    return (
      <section
        className="relative min-h-[60vh] flex items-center justify-center text-white"
        style={{
          backgroundImage: `linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url(${image_url})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      >
        <div className="text-center max-w-2xl px-6">
          <h1 className="text-4xl sm:text-5xl font-bold mb-4">{headline}</h1>
          {subheadline && <p className="text-lg sm:text-xl mb-6">{subheadline}</p>}
          {cta_text && (
            <button
              className="px-6 py-3 rounded-md font-semibold"
              style={{ backgroundColor: "var(--site-primary)", color: "white" }}
            >
              {cta_text}
            </button>
          )}
        </div>
      </section>
    );
  }

  return (
    <section className="min-h-[50vh] flex items-center justify-center px-6 py-12">
      <div className="text-center max-w-2xl">
        <h1
          className="text-4xl sm:text-5xl font-bold mb-4"
          style={{ color: "var(--site-primary)" }}
        >
          {headline}
        </h1>
        {subheadline && <p className="text-lg sm:text-xl mb-6 opacity-80">{subheadline}</p>}
        {cta_text && (
          <button
            className="px-6 py-3 rounded-md font-semibold"
            style={{ backgroundColor: "var(--site-primary)", color: "white" }}
          >
            {cta_text}
          </button>
        )}
      </div>
    </section>
  );
}
