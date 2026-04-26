"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import type { ContactsContent } from "@/types/site";

const schema = z.object({
  visitor_name: z.string().min(2, "Inserisci un nome valido"),
  visitor_email: z.string().email("Email non valida").or(z.literal("")),
  visitor_phone: z.string().optional(),
  message: z.string().min(10, "Scrivi un messaggio (min 10 caratteri)"),
});

type FormData = z.infer<typeof schema>;

interface ContactFormProps extends ContactsContent {
  siteId: string;
}

export function ContactForm({ siteId, phone, email, address, opening_hours }: ContactFormProps) {
  const [status, setStatus] = useState<"idle" | "sending" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setStatus("sending");
    setErrorMsg(null);
    try {
      const res = await fetch("/api/contact-form", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ site_id: siteId, ...data }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error ?? `HTTP ${res.status}`);
      }
      setStatus("success");
      reset();
    } catch (e) {
      setStatus("error");
      setErrorMsg(e instanceof Error ? e.message : "Errore sconosciuto");
    }
  };

  return (
    <section
      id="contact"
      className="section-fade-in py-24 px-6"
      style={{ backgroundColor: "var(--site-primary)", color: "white" }}
    >
      <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
        <div>
          <h2 className="font-display text-4xl sm:text-5xl font-bold mb-6">Contattaci</h2>
          <p className="text-lg opacity-90 mb-8">Compila il form qui a fianco e ti risponderemo entro 24 ore.</p>
          <div className="space-y-3 text-base opacity-95">
            {phone && (<div><a href={`tel:${phone}`} className="hover:underline">📞 {phone}</a></div>)}
            {email && (<div><a href={`mailto:${email}`} className="hover:underline">✉️ {email}</a></div>)}
            {address && <div>📍 {address}</div>}
            {opening_hours && <div>🕐 {opening_hours}</div>}
          </div>
        </div>

        {status === "success" ? (
          <div className="bg-white text-zinc-900 p-8 rounded-2xl">
            <h3 className="font-display text-2xl font-bold mb-2">Grazie!</h3>
            <p className="text-zinc-600">Abbiamo ricevuto il tuo messaggio. Ti ricontatteremo presto.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="bg-white text-zinc-900 p-8 rounded-2xl space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Nome</label>
              <input
                type="text"
                {...register("visitor_name")}
                className="w-full px-4 py-2.5 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-1"
                style={{ outlineColor: "var(--site-primary)" }}
              />
              {errors.visitor_name && (
                <p className="text-red-600 text-xs mt-1">{errors.visitor_name.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <input
                type="email"
                {...register("visitor_email")}
                className="w-full px-4 py-2.5 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2"
              />
              {errors.visitor_email && (
                <p className="text-red-600 text-xs mt-1">{errors.visitor_email.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Telefono (opzionale)</label>
              <input
                type="tel"
                {...register("visitor_phone")}
                className="w-full px-4 py-2.5 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Messaggio</label>
              <textarea
                rows={4}
                {...register("message")}
                className="w-full px-4 py-2.5 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 resize-none"
              />
              {errors.message && (
                <p className="text-red-600 text-xs mt-1">{errors.message.message}</p>
              )}
            </div>
            {errorMsg && (
              <div className="text-red-600 text-sm bg-red-50 p-3 rounded-lg">{errorMsg}</div>
            )}
            <button
              type="submit"
              disabled={status === "sending"}
              className="cta-btn w-full py-3 rounded-lg font-semibold disabled:opacity-50"
              style={{ backgroundColor: "var(--site-primary)", color: "white" }}
            >
              {status === "sending" ? "Invio..." : "Invia messaggio"}
            </button>
          </form>
        )}
      </div>
    </section>
  );
}
