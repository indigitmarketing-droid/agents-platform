export interface TimezoneOption {
  value: string;
  label: string;
}

const CITY_TO_TIMEZONE: Record<string, string> = {
  "milano|IT": "Europe/Rome",
  "roma|IT": "Europe/Rome",
  "napoli|IT": "Europe/Rome",
  "torino|IT": "Europe/Rome",
  "firenze|IT": "Europe/Rome",
  "bologna|IT": "Europe/Rome",
  "venezia|IT": "Europe/Rome",
  "palermo|IT": "Europe/Rome",
  "paris|FR": "Europe/Paris",
  "lyon|FR": "Europe/Paris",
  "london|GB": "Europe/London",
  "berlin|DE": "Europe/Berlin",
  "madrid|ES": "Europe/Madrid",
  "barcelona|ES": "Europe/Madrid",
  "new york|US": "America/New_York",
  "los angeles|US": "America/Los_Angeles",
  "chicago|US": "America/Chicago",
  "san francisco|US": "America/Los_Angeles",
  "tokyo|JP": "Asia/Tokyo",
  "sydney|AU": "Australia/Sydney",
};

const COUNTRY_DEFAULT_TIMEZONE: Record<string, string> = {
  IT: "Europe/Rome",
  FR: "Europe/Paris",
  GB: "Europe/London",
  DE: "Europe/Berlin",
  ES: "Europe/Madrid",
  US: "America/New_York",
  JP: "Asia/Tokyo",
  AU: "Australia/Sydney",
};

export function suggestTimezone(city: string, countryCode: string): string {
  const key = `${city.toLowerCase().trim()}|${countryCode.toUpperCase()}`;
  return (
    CITY_TO_TIMEZONE[key] ??
    COUNTRY_DEFAULT_TIMEZONE[countryCode.toUpperCase()] ??
    "Europe/Rome"
  );
}

export const COMMON_TIMEZONES: TimezoneOption[] = [
  { value: "Europe/Rome", label: "Europe/Rome (CET)" },
  { value: "Europe/Paris", label: "Europe/Paris (CET)" },
  { value: "Europe/London", label: "Europe/London (GMT)" },
  { value: "Europe/Berlin", label: "Europe/Berlin (CET)" },
  { value: "Europe/Madrid", label: "Europe/Madrid (CET)" },
  { value: "America/New_York", label: "America/New_York (EST)" },
  { value: "America/Los_Angeles", label: "America/Los_Angeles (PST)" },
  { value: "America/Chicago", label: "America/Chicago (CST)" },
  { value: "Asia/Tokyo", label: "Asia/Tokyo (JST)" },
  { value: "Australia/Sydney", label: "Australia/Sydney (AEST)" },
];

export const COMMON_COUNTRIES = [
  { code: "IT", label: "Italia" },
  { code: "FR", label: "Francia" },
  { code: "GB", label: "Regno Unito" },
  { code: "DE", label: "Germania" },
  { code: "ES", label: "Spagna" },
  { code: "US", label: "Stati Uniti" },
  { code: "JP", label: "Giappone" },
  { code: "AU", label: "Australia" },
];
