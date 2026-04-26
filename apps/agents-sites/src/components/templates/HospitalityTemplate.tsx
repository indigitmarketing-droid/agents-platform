import type { SiteContent } from "@/types/site";
import { Hero } from "@/components/primitives/Hero";
import { ServicesList } from "@/components/primitives/ServicesList";
import { About } from "@/components/primitives/About";
import { ContactBlock } from "@/components/primitives/ContactBlock";

interface Props {
  content: SiteContent;
}

export function HospitalityTemplate({ content }: Props) {
  return (
    <>
      <Hero {...(content.hero ?? {})} variant="image-bg" />
      <ServicesList items={content.services} variant="grid" />
      <About {...(content.about ?? {})} />
      <ContactBlock {...(content.contacts ?? {})} variant="map" />
    </>
  );
}
