import type { SiteContent } from "@/types/site";
import { Hero } from "@/components/primitives/Hero";
import { Problem } from "@/components/primitives/Problem";
import { Benefits } from "@/components/primitives/Benefits";
import { Solution } from "@/components/primitives/Solution";
import { ServicesList } from "@/components/primitives/ServicesList";
import { ContactForm } from "@/components/primitives/ContactForm";

interface Props {
  content: SiteContent;
  siteId: string;
}

export function HospitalityTemplate({ content, siteId }: Props) {
  return (
    <>
      <Hero {...(content.hero ?? {})} variant="image-bg" />
      <Problem {...(content.problem ?? {})} />
      <Benefits {...(content.benefits ?? {})} />
      <Solution {...(content.solution ?? {})} />
      <ServicesList items={content.services} variant="grid" />
      <ContactForm {...(content.contacts ?? {})} siteId={siteId} />
    </>
  );
}
