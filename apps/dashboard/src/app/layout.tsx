import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agent Command Center",
  description: "Control dashboard for AI agent orchestrator",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="it">
      <body className="antialiased">{children}</body>
    </html>
  );
}
