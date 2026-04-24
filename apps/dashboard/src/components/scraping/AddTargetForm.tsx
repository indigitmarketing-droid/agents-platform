"use client";

import { useState } from "react";
import { SCRAPING_CATEGORIES } from "@/lib/scraping-categories";
import {
  COMMON_COUNTRIES,
  COMMON_TIMEZONES,
  suggestTimezone,
} from "@/lib/timezone-lookup";

interface AddTargetFormProps {
  onAdd: (input: {
    category: string;
    category_type: string;
    city: string;
    country_code: string;
    timezone: string;
  }) => Promise<void>;
}

export function AddTargetForm({ onAdd }: AddTargetFormProps) {
  const [categoryIdx, setCategoryIdx] = useState(0);
  const [city, setCity] = useState("");
  const [country, setCountry] = useState("IT");
  const [timezone, setTimezone] = useState("Europe/Rome");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onCityBlur = () => {
    if (city) setTimezone(suggestTimezone(city, country));
  };
  const onCountryChange = (newCountry: string) => {
    setCountry(newCountry);
    setTimezone(suggestTimezone(city, newCountry));
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!city.trim()) {
      setError("Inserisci una città");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const cat = SCRAPING_CATEGORIES[categoryIdx];
      await onAdd({
        category: cat.value,
        category_type: cat.type,
        city: city.trim(),
        country_code: country,
        timezone,
      });
      setCity("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore sconosciuto");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={submit}
      className="bg-surface border border-border rounded-xl p-4 space-y-3"
    >
      <h3 className="text-sm font-semibold">➕ Aggiungi Target</h3>
      <div className="grid grid-cols-4 gap-3">
        <select
          value={categoryIdx}
          onChange={(e) => setCategoryIdx(Number(e.target.value))}
          className="bg-black/40 border border-border rounded-md px-3 py-2 text-sm"
        >
          {SCRAPING_CATEGORIES.map((c, i) => (
            <option key={c.value} value={i}>
              {c.label}
            </option>
          ))}
        </select>
        <input
          value={city}
          onChange={(e) => setCity(e.target.value)}
          onBlur={onCityBlur}
          placeholder="Città (es. Milano)"
          className="bg-black/40 border border-border rounded-md px-3 py-2 text-sm"
        />
        <select
          value={country}
          onChange={(e) => onCountryChange(e.target.value)}
          className="bg-black/40 border border-border rounded-md px-3 py-2 text-sm"
        >
          {COMMON_COUNTRIES.map((c) => (
            <option key={c.code} value={c.code}>
              {c.label}
            </option>
          ))}
        </select>
        <select
          value={timezone}
          onChange={(e) => setTimezone(e.target.value)}
          className="bg-black/40 border border-border rounded-md px-3 py-2 text-sm"
        >
          {COMMON_TIMEZONES.map((tz) => (
            <option key={tz.value} value={tz.value}>
              {tz.label}
            </option>
          ))}
        </select>
      </div>
      {error && <div className="text-xs text-red-400">{error}</div>}
      <button
        type="submit"
        disabled={submitting}
        className="w-full py-2 border border-accent/30 bg-accent/10 text-accent-light rounded-lg text-sm font-medium hover:bg-accent/25 hover:border-accent transition-colors cursor-pointer disabled:opacity-50"
      >
        {submitting ? "Salvataggio..." : "+ Aggiungi"}
      </button>
    </form>
  );
}
