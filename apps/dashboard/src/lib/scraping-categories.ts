export interface ScrapingCategory {
  type: "amenity" | "shop" | "craft" | "leisure" | "office";
  value: string;
  label: string;
}

export const SCRAPING_CATEGORIES: ScrapingCategory[] = [
  { type: "amenity", value: "restaurant", label: "Ristoranti" },
  { type: "shop", value: "hairdresser", label: "Parrucchieri" },
  { type: "shop", value: "beauty", label: "Estetiste" },
  { type: "amenity", value: "dentist", label: "Dentisti" },
  { type: "leisure", value: "fitness_centre", label: "Palestre" },
  { type: "craft", value: "photographer", label: "Fotografi" },
];
