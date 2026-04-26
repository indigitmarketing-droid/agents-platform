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

export function ServiceTemplate({ content, siteId }: Props) {
  return (
    <>
      <Hero {...(content.hero ?? {})} variant="centered-text" />
      <Problem {...(content.problem ?? {})} />
      <Benefits {...(content.benefits ?? {})} />
      <Solution {...(content.solution ?? {})} />
      <ServicesList items={content.services} variant="list-with-prices" />
      <ContactForm {...(content.contacts ?? {})} siteId={siteId} />
    </>
  );
}
