import type { SiteContent } from "@/types/site";
import { Hero } from "@/components/primitives/Hero";
import { About } from "@/components/primitives/About";
import { ServicesList } from "@/components/primitives/ServicesList";
import { ContactBlock } from "@/components/primitives/ContactBlock";

interface Props {
  content: SiteContent;
}

export function ServiceTemplate({ content }: Props) {
  return (
    <>
      <Hero {...(content.hero ?? {})} variant="centered-text" />
      <About {...(content.about ?? {})} />
      <ServicesList items={content.services} variant="list-with-prices" />
      <ContactBlock {...(content.contacts ?? {})} variant="form" />
    </>
  );
}
