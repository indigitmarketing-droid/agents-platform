export interface SiteColors {
  primary?: string;
  accent?: string;
  text?: string;
  background?: string;
}

export interface HeroContent {
  headline?: string;
  subheadline?: string;
  cta_text?: string;
  cta_link?: string;
  image_url?: string;
}

export interface ProblemContent {
  title?: string;
  body?: string;
  bullets?: string[];
}

export interface BenefitItem {
  title?: string;
  description?: string;
  icon?: string;
}

export interface BenefitsContent {
  title?: string;
  items?: BenefitItem[];
}

export interface SolutionContent {
  title?: string;
  body?: string;
  cta_text?: string;
  cta_link?: string;
}

export interface ServiceItem {
  title?: string;
  description?: string;
  price?: string;
}

export interface AboutContent {
  title?: string;
  body?: string;
}

export interface ContactsContent {
  phone?: string;
  email?: string | null;
  address?: string | null;
  opening_hours?: string | null;
}

export interface SiteContent {
  hero?: HeroContent;
  problem?: ProblemContent;
  benefits?: BenefitsContent;
  solution?: SolutionContent;
  services?: ServiceItem[];
  about?: AboutContent;
  contacts?: ContactsContent;
}

export type TemplateKind = "hospitality" | "service" | "generic";

export interface Site {
  id: string;
  lead_id: string;
  slug: string;
  template_kind: TemplateKind;
  category: string;
  colors: SiteColors;
  content: SiteContent;
  published_url: string | null;
  created_at: string;
  updated_at: string;
}
