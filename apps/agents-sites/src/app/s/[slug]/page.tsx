import { notFound } from "next/navigation";
import type { CSSProperties } from "react";
import { supabase } from "@/lib/supabase";
import type { Site, TemplateKind } from "@/types/site";
import { HospitalityTemplate } from "@/components/templates/HospitalityTemplate";
import { ServiceTemplate } from "@/components/templates/ServiceTemplate";
import { GenericTemplate } from "@/components/templates/GenericTemplate";

const TEMPLATES: Record<TemplateKind, React.FC<{ content: Site["content"] }>> = {
  hospitality: HospitalityTemplate,
  service: ServiceTemplate,
  generic: GenericTemplate,
};

export const revalidate = 60;

export default async function SitePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const { data, error } = await supabase
    .from("sites")
    .select("*")
    .eq("slug", slug)
    .maybeSingle();

  if (error || !data) {
    notFound();
  }

  const site = data as Site;
  const Template = TEMPLATES[site.template_kind] ?? GenericTemplate;

  const styleVars: CSSProperties = {
    ["--site-primary" as string]: site.colors.primary ?? "#5B4FCF",
    ["--site-accent" as string]: site.colors.accent ?? "#A78BFA",
    ["--site-text" as string]: site.colors.text ?? "#1F2937",
    ["--site-bg" as string]: site.colors.background ?? "#F9FAFB",
  };

  return (
    <main
      style={{
        ...styleVars,
        backgroundColor: "var(--site-bg)",
        color: "var(--site-text)",
        minHeight: "100vh",
      }}
    >
      <Template content={site.content} />
    </main>
  );
}
