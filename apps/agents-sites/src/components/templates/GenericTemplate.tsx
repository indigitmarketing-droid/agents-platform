import type { SiteContent } from "@/types/site";
import { Hero } from "@/components/primitives/Hero";
import { About } from "@/components/primitives/About";
import { ContactBlock } from "@/components/primitives/ContactBlock";

interface Props {
  content: SiteContent;
}

export function GenericTemplate({ content }: Props) {
  return (
    <>
      <Hero {...(content.hero ?? {})} variant="centered-text" />
      <About {...(content.about ?? {})} />
      <ContactBlock {...(content.contacts ?? {})} variant="simple" />
    </>
  );
}
