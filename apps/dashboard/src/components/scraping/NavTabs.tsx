"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { href: "/", label: "Dashboard" },
  { href: "/scraping-config", label: "🎯 Scraping Config" },
];

export function NavTabs() {
  const pathname = usePathname();
  return (
    <nav className="flex gap-1 px-6 py-2 border-b border-border bg-black/30">
      {tabs.map((tab) => {
        const active = pathname === tab.href;
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              active
                ? "bg-accent/20 text-accent-light"
                : "text-muted hover:text-zinc-200 hover:bg-surface"
            }`}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
