# Customer Dashboard E1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundation Sub-progetto E1 — a multi-tenant customer dashboard (Next.js) with Supabase Auth + RLS schema. **Scope ridotto rispetto a draft iniziale**: il customer onboarding (auth.user creation + welcome email) è spostato a F1 (Stripe payment webhook).

**Architecture:** New `apps/customer-dashboard/` Next.js app with Supabase SSR auth. Migration `007` aggiunge schema multi-tenant + campi future-proof (`payment_status`, `published_at`) usati da F1. Builder Agent NON viene modificato in E1.

**Tech Stack:** Next.js 16+ App Router, `@supabase/ssr`, Tailwind v4, vitest.

**Spec reference:** `docs/superpowers/specs/2026-05-01-customer-dashboard-e1-design.md`

---

## Task 1: Database migration

**Files:**
- Create: `supabase/migrations/007_customer_onboarding.sql`

- [ ] **Step 1: Write the migration SQL**

Create `supabase/migrations/007_customer_onboarding.sql`:

```sql
-- 007_customer_onboarding.sql
-- E1: multi-tenant schema + future-proof columns for F1 (Stripe)

-- 1. Add owner_user_id to sites (populated by F1 after payment)
ALTER TABLE sites ADD COLUMN owner_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;
CREATE INDEX idx_sites_owner_user ON sites(owner_user_id);

-- 2. Add payment fields (used by F1)
ALTER TABLE sites ADD COLUMN published_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE sites ADD COLUMN payment_status TEXT DEFAULT 'unpaid'
  CHECK (payment_status IN ('unpaid', 'paid', 'expired'));
CREATE INDEX idx_sites_payment_grace ON sites(payment_status, published_at);

-- 3. Ensure RLS enabled
ALTER TABLE sites ENABLE ROW LEVEL SECURITY;

-- 4. SELECT policy for authenticated customers — own site only
CREATE POLICY "customers_see_own_site"
  ON sites FOR SELECT
  TO authenticated
  USING (owner_user_id = auth.uid());

-- 5. Block authenticated mutations (service_role bypasses RLS)
CREATE POLICY "no_customer_writes"
  ON sites FOR ALL
  TO authenticated
  USING (false)
  WITH CHECK (false);

-- 6. Public read for anon (used by agents-sites for /s/{slug} rendering)
CREATE POLICY "public_read_sites_by_slug"
  ON sites FOR SELECT
  TO anon
  USING (true);
```

- [ ] **Step 2: Apply migration via Supabase MCP**

Use `mcp__plugin_supabase_supabase__execute_sql` with the SQL above against project `smzmgzblbliprwbjptjs`.

- [ ] **Step 3: Verify migration applied**

Execute via Supabase MCP:

```sql
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name='sites' AND column_name IN ('owner_user_id', 'published_at', 'payment_status')
ORDER BY column_name;

SELECT policyname FROM pg_policies WHERE tablename='sites';
```

Expected: 3 columns present, 3 policies (customers_see_own_site, no_customer_writes, public_read_sites_by_slug).

- [ ] **Step 4: Backfill `published_at` for existing sites**

```sql
UPDATE sites SET published_at = COALESCE(published_at, NOW()) WHERE published_at IS NULL;
```

Expected: rows updated (or 0 if none).

- [ ] **Step 5: Commit**

```bash
git add supabase/migrations/007_customer_onboarding.sql
git commit -m "feat(E1): migration 007 - multi-tenant sites schema + payment fields"
```

---

## Task 2: Scaffold `apps/customer-dashboard/` Next.js app

**Files:**
- Create: `apps/customer-dashboard/package.json`
- Create: `apps/customer-dashboard/next.config.ts`
- Create: `apps/customer-dashboard/tsconfig.json`
- Create: `apps/customer-dashboard/tailwind.config.ts`
- Create: `apps/customer-dashboard/postcss.config.mjs`
- Create: `apps/customer-dashboard/.gitignore`
- Create: `apps/customer-dashboard/src/app/layout.tsx`
- Create: `apps/customer-dashboard/src/app/page.tsx` (placeholder)
- Create: `apps/customer-dashboard/src/app/globals.css`

- [ ] **Step 1: Create `package.json`**

```json
{
  "name": "customer-dashboard",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "@supabase/ssr": "^0.5.2",
    "@supabase/supabase-js": "^2.45.0",
    "clsx": "^2.1.1",
    "lucide-react": "^0.460.0",
    "next": "^16.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "tailwind-merge": "^2.5.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.5.0",
    "@testing-library/react": "^16.0.0",
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "jsdom": "^25.0.0",
    "postcss": "^8.4.49",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.6.0",
    "vitest": "^2.1.0"
  }
}
```

- [ ] **Step 2: Create `next.config.ts`**

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
```

- [ ] **Step 3: Create `tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{"name": "next"}],
    "paths": {"@/*": ["./src/*"]}
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 4: Create `tailwind.config.ts`**

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Playfair Display", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
};

export default config;
```

- [ ] **Step 5: Create `postcss.config.mjs`**

```javascript
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

- [ ] **Step 6: Create `.gitignore`**

```
node_modules
.next
out
*.log
.env*.local
.vercel
.turbo
```

- [ ] **Step 7: Create `src/app/globals.css`**

```css
@import "tailwindcss";

@theme {
  --font-sans: "Inter", system-ui, sans-serif;
  --font-display: "Playfair Display", Georgia, serif;
}

body {
  font-family: var(--font-sans);
  color: #1a1a1a;
  background: #fafafa;
}
```

- [ ] **Step 8: Create root `src/app/layout.tsx`**

```typescript
import "./globals.css";

export const metadata = {
  title: "Customer Dashboard",
  description: "Manage your website",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
```

- [ ] **Step 9: Create placeholder `src/app/page.tsx`**

```typescript
export default function Home() {
  return <main className="p-8"><h1 className="text-2xl font-display">Customer Dashboard</h1></main>;
}
```

- [ ] **Step 10: Install dependencies + verify build**

```bash
cd apps/customer-dashboard
npm install
npm run build
```

Expected: dependencies installed, build OK.

- [ ] **Step 11: Commit**

```bash
git add apps/customer-dashboard/
git commit -m "feat(E1): scaffold customer-dashboard Next.js app"
```

---

## Task 3: Supabase clients + UI primitives + shared components

**Files:**
- Create: `apps/customer-dashboard/src/lib/utils.ts`
- Create: `apps/customer-dashboard/src/lib/supabase/client.ts`
- Create: `apps/customer-dashboard/src/lib/supabase/server.ts`
- Create: `apps/customer-dashboard/src/components/ui/Button.tsx`
- Create: `apps/customer-dashboard/src/components/ui/Input.tsx`
- Create: `apps/customer-dashboard/src/components/ui/Label.tsx`
- Create: `apps/customer-dashboard/src/components/DashboardCard.tsx`
- Create: `apps/customer-dashboard/src/components/LogoutButton.tsx`

- [ ] **Step 1: Create `src/lib/utils.ts`**

```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 2: Create `src/lib/supabase/client.ts` (browser)**

```typescript
import { createBrowserClient } from "@supabase/ssr";

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
}
```

- [ ] **Step 3: Create `src/lib/supabase/server.ts`**

```typescript
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

export async function createClient() {
  const cookieStore = await cookies();
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options));
          } catch {
            // Server Component context — set is no-op
          }
        },
      },
    },
  );
}
```

- [ ] **Step 4: Create `src/components/ui/Button.tsx`**

```typescript
import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center px-4 py-2 rounded-md font-medium text-sm transition-colors",
        "disabled:opacity-50 disabled:pointer-events-none",
        variant === "primary" && "bg-black text-white hover:bg-gray-800",
        variant === "secondary" && "bg-gray-100 text-gray-900 hover:bg-gray-200",
        className,
      )}
      {...props}
    />
  ),
);
Button.displayName = "Button";
```

- [ ] **Step 5: Create `src/components/ui/Input.tsx`**

```typescript
import { cn } from "@/lib/utils";
import { InputHTMLAttributes, forwardRef } from "react";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "w-full px-3 py-2 border border-gray-300 rounded-md text-sm",
        "focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";
```

- [ ] **Step 6: Create `src/components/ui/Label.tsx`**

```typescript
import { cn } from "@/lib/utils";
import { LabelHTMLAttributes } from "react";

export function Label({ className, ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn("text-sm font-medium text-gray-700 block mb-1", className)}
      {...props}
    />
  );
}
```

- [ ] **Step 7: Create `src/components/DashboardCard.tsx`**

```typescript
import { cn } from "@/lib/utils";

interface DashboardCardProps {
  title: string;
  comingSoon?: boolean;
  children?: React.ReactNode;
}

export function DashboardCard({ title, comingSoon, children }: DashboardCardProps) {
  return (
    <div className={cn(
      "bg-white border border-gray-200 rounded-lg p-6",
      comingSoon && "opacity-60",
    )}>
      <h3 className="font-semibold text-lg mb-2">{title}</h3>
      {comingSoon ? (
        <span className="inline-block text-xs uppercase tracking-wider text-gray-500 bg-gray-100 px-2 py-1 rounded">
          Coming soon
        </span>
      ) : children}
    </div>
  );
}
```

- [ ] **Step 8: Create `src/components/LogoutButton.tsx`**

```typescript
"use client";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import { Button } from "./ui/Button";

export function LogoutButton() {
  const router = useRouter();
  const handleLogout = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  };
  return <Button variant="secondary" onClick={handleLogout}>Logout</Button>;
}
```

- [ ] **Step 9: Verify build still passes**

```bash
cd apps/customer-dashboard
npm run build
```

Expected: build OK.

- [ ] **Step 10: Commit**

```bash
git add apps/customer-dashboard/src/lib apps/customer-dashboard/src/components
git commit -m "feat(E1): supabase clients + UI primitives + DashboardCard + LogoutButton"
```

---

## Task 4: Login page + auth callback route

**Files:**
- Create: `apps/customer-dashboard/src/app/login/page.tsx`
- Create: `apps/customer-dashboard/src/app/api/auth/callback/route.ts`

- [ ] **Step 1: Create login page**

`apps/customer-dashboard/src/app/login/page.tsx`:

```typescript
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const supabase = createClient();
    const { error: signInError } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (signInError) {
      setError("Invalid credentials");
      return;
    }
    router.push("/");
    router.refresh();
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white border border-gray-200 rounded-lg p-8">
        <h1 className="text-3xl font-display mb-6">Sign in</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </Button>
        </form>
        <p className="text-sm text-gray-600 mt-4">
          <Link href="/forgot-password" className="underline">Forgot password?</Link>
        </p>
      </div>
    </main>
  );
}
```

- [ ] **Step 2: Create auth callback route**

`apps/customer-dashboard/src/app/api/auth/callback/route.ts`:

```typescript
import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/";

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }
  return NextResponse.redirect(`${origin}/login?error=auth_callback`);
}
```

- [ ] **Step 3: Verify build**

```bash
cd apps/customer-dashboard
npm run build
```

Expected: build OK.

- [ ] **Step 4: Commit**

```bash
git add apps/customer-dashboard/src/app/login apps/customer-dashboard/src/app/api
git commit -m "feat(E1): login page + auth callback route"
```

---

## Task 5: Forgot password + reset password pages

**Files:**
- Create: `apps/customer-dashboard/src/app/forgot-password/page.tsx`
- Create: `apps/customer-dashboard/src/app/reset-password/page.tsx`

- [ ] **Step 1: Create forgot-password page**

`apps/customer-dashboard/src/app/forgot-password/page.tsx`:

```typescript
"use client";
import { useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const supabase = createClient();
    const { error: resetError } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });
    setLoading(false);
    if (resetError) {
      setError("Could not send reset email. Try again.");
      return;
    }
    setSent(true);
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white border border-gray-200 rounded-lg p-8">
        <h1 className="text-3xl font-display mb-6">Reset your password</h1>
        {sent ? (
          <p className="text-sm text-gray-700">
            Check your inbox for a password reset link.
          </p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Sending..." : "Send reset link"}
            </Button>
          </form>
        )}
        <p className="text-sm text-gray-600 mt-4">
          <Link href="/login" className="underline">Back to login</Link>
        </p>
      </div>
    </main>
  );
}
```

- [ ] **Step 2: Create reset-password page**

`apps/customer-dashboard/src/app/reset-password/page.tsx`:

```typescript
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";

export default function ResetPasswordPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    setLoading(true);
    const supabase = createClient();
    const { error: updateErr } = await supabase.auth.updateUser({
      password,
      data: { password_changed: true },
    });
    setLoading(false);
    if (updateErr) {
      setError("Could not update password. The link may have expired.");
      return;
    }
    router.push("/login?reset=success");
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white border border-gray-200 rounded-lg p-8">
        <h1 className="text-3xl font-display mb-6">Choose a new password</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="password">New password</Label>
            <Input
              id="password"
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Updating..." : "Update password"}
          </Button>
        </form>
      </div>
    </main>
  );
}
```

- [ ] **Step 3: Verify build**

```bash
cd apps/customer-dashboard
npm run build
```

Expected: build OK.

- [ ] **Step 4: Commit**

```bash
git add apps/customer-dashboard/src/app/forgot-password apps/customer-dashboard/src/app/reset-password
git commit -m "feat(E1): forgot-password + reset-password pages"
```

---

## Task 6: Change password page (forced first login)

**Files:**
- Create: `apps/customer-dashboard/src/app/change-password/page.tsx`

- [ ] **Step 1: Create change-password page**

`apps/customer-dashboard/src/app/change-password/page.tsx`:

```typescript
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";

export default function ChangePasswordPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    setLoading(true);
    const supabase = createClient();
    const { error: updateErr } = await supabase.auth.updateUser({
      password,
      data: { password_changed: true },
    });
    setLoading(false);
    if (updateErr) {
      setError("Could not update password. Please try again.");
      return;
    }
    router.push("/");
    router.refresh();
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white border border-gray-200 rounded-lg p-8">
        <h1 className="text-3xl font-display mb-2">Set your password</h1>
        <p className="text-sm text-gray-600 mb-6">
          Please choose a new password to replace the temporary one we sent you.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="password">New password</Label>
            <Input
              id="password"
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="confirm">Confirm new password</Label>
            <Input
              id="confirm"
              type="password"
              required
              minLength={6}
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Updating..." : "Set password"}
          </Button>
        </form>
      </div>
    </main>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd apps/customer-dashboard
npm run build
```

Expected: build OK.

- [ ] **Step 3: Commit**

```bash
git add apps/customer-dashboard/src/app/change-password
git commit -m "feat(E1): change-password page (forced first login)"
```

---

## Task 7: Dashboard home page (protected)

**Files:**
- Modify: `apps/customer-dashboard/src/app/page.tsx` (replace placeholder)

- [ ] **Step 1: Replace `src/app/page.tsx`**

```typescript
import { createClient } from "@/lib/supabase/server";
import { DashboardCard } from "@/components/DashboardCard";
import { LogoutButton } from "@/components/LogoutButton";
import { redirect } from "next/navigation";

export default async function DashboardHome() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    redirect("/login");
  }

  const { data: site } = await supabase
    .from("sites")
    .select("slug, content")
    .eq("owner_user_id", user.id)
    .maybeSingle();

  const companyName = (user.user_metadata?.company_name as string | undefined) ?? "there";
  const sitesBaseUrl = "https://agents-sites.vercel.app";

  return (
    <main className="max-w-5xl mx-auto p-8">
      <header className="flex justify-between items-start mb-12">
        <div>
          <h1 className="text-4xl font-display mb-2">Welcome, {companyName}</h1>
          <p className="text-gray-600">Manage your website and explore upcoming features.</p>
        </div>
        <LogoutButton />
      </header>

      <section className="mb-12">
        <h2 className="text-2xl font-display mb-4">Your website</h2>
        {site ? (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <p className="mb-2 text-sm text-gray-600">Public URL</p>
            <a
              href={`${sitesBaseUrl}/s/${site.slug}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-lg font-medium underline"
            >
              {sitesBaseUrl}/s/{site.slug}
            </a>
          </div>
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <p className="text-sm">No website found. Please contact support.</p>
          </div>
        )}
      </section>

      <section>
        <h2 className="text-2xl font-display mb-4">Upcoming features</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <DashboardCard title="Visits & Analytics" comingSoon />
          <DashboardCard title="Custom Domain" comingSoon />
          <DashboardCard title="Automatic Blog" comingSoon />
        </div>
      </section>
    </main>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd apps/customer-dashboard
npm run build
```

Expected: build OK.

- [ ] **Step 3: Commit**

```bash
git add apps/customer-dashboard/src/app/page.tsx
git commit -m "feat(E1): protected dashboard home with site URL + coming-soon cards"
```

---

## Task 8: Middleware (auth gate + force password change)

**Files:**
- Create: `apps/customer-dashboard/middleware.ts`

- [ ] **Step 1: Create middleware**

`apps/customer-dashboard/middleware.ts`:

```typescript
import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

export async function middleware(req: NextRequest) {
  const res = NextResponse.next();
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => req.cookies.getAll(),
        setAll: (list) =>
          list.forEach(({ name, value, options }) =>
            res.cookies.set(name, value, options),
          ),
      },
    },
  );

  const { data: { user } } = await supabase.auth.getUser();
  const path = req.nextUrl.pathname;

  // Public routes (no auth required)
  const publicPaths = ["/login", "/forgot-password", "/reset-password"];
  if (
    publicPaths.some((p) => path.startsWith(p)) ||
    path.startsWith("/api/auth")
  ) {
    return res;
  }

  // Protected: must be authenticated
  if (!user) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  // Force password change on first login
  const passwordChanged = user.user_metadata?.password_changed === true;
  if (!passwordChanged && path !== "/change-password") {
    return NextResponse.redirect(new URL("/change-password", req.url));
  }

  return res;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
```

- [ ] **Step 2: Verify build (with middleware)**

```bash
cd apps/customer-dashboard
npm run build
```

Expected: build OK, "Middleware: 1" appears in build output.

- [ ] **Step 3: Commit**

```bash
git add apps/customer-dashboard/middleware.ts
git commit -m "feat(E1): middleware for auth gate + force password change"
```

---

## Task 9: Vitest config + middleware tests

**Files:**
- Create: `apps/customer-dashboard/vitest.config.ts`
- Create: `apps/customer-dashboard/__tests__/middleware.test.ts`

- [ ] **Step 1: Create vitest config**

`apps/customer-dashboard/vitest.config.ts`:

```typescript
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
  },
});
```

- [ ] **Step 2: Create middleware test**

`apps/customer-dashboard/__tests__/middleware.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@supabase/ssr", () => ({
  createServerClient: vi.fn(),
}));

import { middleware } from "../middleware";
import { createServerClient } from "@supabase/ssr";
import { NextRequest } from "next/server";

function makeReq(path: string) {
  return new NextRequest(`http://localhost:3000${path}`);
}

function mockSupabase(user: any) {
  (createServerClient as any).mockReturnValue({
    auth: {
      getUser: vi.fn().mockResolvedValue({ data: { user } }),
    },
  });
}

describe("middleware", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.NEXT_PUBLIC_SUPABASE_URL = "https://test.supabase.co";
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "anon";
  });

  it("allows /login without auth", async () => {
    mockSupabase(null);
    const res = await middleware(makeReq("/login"));
    expect(res.status).toBe(200);
  });

  it("allows /forgot-password without auth", async () => {
    mockSupabase(null);
    const res = await middleware(makeReq("/forgot-password"));
    expect(res.status).toBe(200);
  });

  it("redirects unauthenticated user to /login", async () => {
    mockSupabase(null);
    const res = await middleware(makeReq("/"));
    expect(res.status).toBe(307);
    expect(res.headers.get("location")).toContain("/login");
  });

  it("redirects user with password_changed=false to /change-password", async () => {
    mockSupabase({ id: "uid", user_metadata: { password_changed: false } });
    const res = await middleware(makeReq("/"));
    expect(res.status).toBe(307);
    expect(res.headers.get("location")).toContain("/change-password");
  });

  it("allows authenticated user with password_changed=true to access /", async () => {
    mockSupabase({ id: "uid", user_metadata: { password_changed: true } });
    const res = await middleware(makeReq("/"));
    expect(res.status).toBe(200);
  });

  it("allows /change-password access for user without password_changed flag (no redirect loop)", async () => {
    mockSupabase({ id: "uid", user_metadata: { password_changed: false } });
    const res = await middleware(makeReq("/change-password"));
    expect(res.status).toBe(200);
  });
});
```

- [ ] **Step 3: Run tests to verify they pass**

```bash
cd apps/customer-dashboard
npm test
```

Expected: 6 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add apps/customer-dashboard/vitest.config.ts apps/customer-dashboard/__tests__
git commit -m "test(E1): vitest config + middleware tests"
```

---

## Task 10: Vercel deploy + Supabase Auth URL config

**Files:** N/A (CLI + dashboard config)

- [ ] **Step 1: Link Vercel project**

```bash
cd apps/customer-dashboard
vercel link --yes
```

When prompted, choose "Create new project" with name `agents-customer-dashboard` (or accept default).

Expected: `.vercel/project.json` created.

- [ ] **Step 2: Add env vars**

Pull existing anon key from agents-dashboard:

```bash
cd ../dashboard
vercel env pull .env.production --environment production --yes
grep NEXT_PUBLIC_SUPABASE_ANON_KEY .env.production
cd ../customer-dashboard
```

Then add to customer-dashboard:

```bash
echo "https://smzmgzblbliprwbjptjs.supabase.co" | vercel env add NEXT_PUBLIC_SUPABASE_URL production
echo "<anon_key_value>" | vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
```

Verify:

```bash
vercel env ls production
```

Expected: 2 env vars listed.

- [ ] **Step 3: Deploy to production**

```bash
cd apps/customer-dashboard
vercel --prod --yes
```

Expected: deploy ready, URL printed (capture for Supabase config).

- [ ] **Step 4: Configure Supabase Auth redirect URLs**

This step requires Supabase dashboard access (no MCP tool for this). Open https://supabase.com/dashboard/project/smzmgzblbliprwbjptjs/auth/url-configuration:

1. "Site URL" → `https://agents-customer-dashboard.vercel.app`
2. "Redirect URLs" → add `https://agents-customer-dashboard.vercel.app/**`
3. Save

Mark this step done after saving in Supabase dashboard.

- [ ] **Step 5: Smoke test**

```bash
curl --ssl-no-revoke -s -o /dev/null -w "HTTP %{http_code}\n" "https://agents-customer-dashboard.vercel.app/login"
```

Expected: HTTP 200.

- [ ] **Step 6: Commit deploy artifacts**

```bash
cd ../..
git add apps/customer-dashboard/.vercel/project.json 2>/dev/null || true
git commit --allow-empty -m "chore(E1): customer-dashboard deployed to Vercel production"
```

---

## Task 11: E2E manual test

**Files:** N/A (manual verification)

- [ ] **Step 1: Create test auth.user via Supabase MCP**

Use `mcp__plugin_supabase_supabase__execute_sql`:

```sql
-- Create auth.user manually for E2E test
SELECT auth.uid();  -- check if function exists
```

The Supabase Auth admin API is preferred for creating users. Use the Supabase REST API via curl, OR via Supabase MCP if available, OR via Supabase dashboard:

Via Supabase dashboard:
1. https://supabase.com/dashboard/project/smzmgzblbliprwbjptjs/auth/users
2. "Add user" → "Create new user"
3. Email: `e2e-test@natalinoai.com`
4. Password: `TempPass1234`
5. Auto Confirm User: YES
6. After creation, edit user metadata → set:
   ```json
   {
     "company_name": "E2E Test Co",
     "password_changed": false
   }
   ```

Capture the new user's UUID.

- [ ] **Step 2: Create test site row linked to user**

Via Supabase MCP:

```sql
INSERT INTO sites (lead_id, slug, content, owner_user_id, payment_status, published_at)
VALUES (
  (SELECT id FROM leads ORDER BY created_at DESC LIMIT 1),  -- use any existing lead
  'e2e-test-site',
  '{"hero": {"headline": "E2E Test Site"}}'::jsonb,
  '<user_uuid_from_step_1>',
  'paid',
  NOW()
)
RETURNING id, slug;
```

- [ ] **Step 3: Login flow walkthrough**

Open `https://agents-customer-dashboard.vercel.app/login` in a browser:

1. Enter `e2e-test@natalinoai.com` + `TempPass1234`
2. Should redirect to `/change-password`
3. Set new password (≥6 chars), confirm, submit
4. Should redirect to `/`
5. Verify dashboard shows: "Welcome, E2E Test Co", site URL link, 3 coming-soon cards
6. Click logout → redirect to `/login`
7. Login again with new password → should go directly to `/` (no force-change redirect)

- [ ] **Step 4: Test password reset flow**

1. Logout, click "Forgot password?"
2. Enter `e2e-test@natalinoai.com` → "Check your inbox"
3. Click reset link in email → land on `/reset-password`
4. Enter new password → redirect to `/login?reset=success`
5. Login with new password → dashboard

- [ ] **Step 5: Test RLS multi-tenant isolation**

Create a SECOND test user (e.g., `e2e-test-2@natalinoai.com`) via Supabase dashboard. Login as this second user → dashboard should show "No website found" (since their `owner_user_id` is different from any site).

- [ ] **Step 6: Cleanup test data**

Via Supabase MCP:

```sql
DELETE FROM sites WHERE slug='e2e-test-site';
```

Via Supabase dashboard auth.users page: delete `e2e-test@natalinoai.com` and `e2e-test-2@natalinoai.com`.

---

## Task 12: Update BRAINSTORM_STATE + memory

**Files:**
- Modify: `BRAINSTORM_STATE.md`
- Modify: memory `project_decomposition.md`

- [ ] **Step 1: Update BRAINSTORM_STATE.md sub-projects table**

Read current `BRAINSTORM_STATE.md`. Update the row for E:

Before:
```
| E | Admin dashboards multi-tenant + Blog generator | da fare |
```

After:
```
| E1 | Customer Dashboard (auth + multi-tenant foundation) | **✅ COMPLETATO + DEPLOYATO** |
| E2 | Custom domain configuration | da fare |
| E3 | Analytics | da fare |
| E4 | Blog generator | da fare |
| E5 | Social integration | da fare |
| F1 | Stripe Payments + 48h grace + cleanup | da brainstormare (post-E1) |
| F2 | WhatsApp follow-up agent | da brainstormare (post-F1) |
| D-Phase2 | Site-ready call (secondo agente ElevenLabs) | da brainstormare (post-F1) |
```

- [ ] **Step 2: Add E1 closure section to BRAINSTORM_STATE.md**

```markdown
## Sub-progetto E1 — Customer Dashboard ✅ DEPLOYATO

**Build completato 2026-XX-XX**: nuova app customer-dashboard, Supabase Auth, RLS multi-tenant. Onboarding flow (auth.user + welcome email) **deferred a F1** perché avviene post-pagamento.

**Componenti deployati**:
- Migration `007_customer_onboarding.sql`: owner_user_id, payment_status, published_at + RLS policies
- `apps/customer-dashboard/` Next.js app live su Vercel
- 5 routes: /login, /forgot-password, /reset-password, /change-password, /
- Middleware: auth gate + force password change al primo login

**E2E validato**: manual auth.user creation (Supabase admin) → dashboard login → forced password change → dashboard render con site URL + coming-soon cards. Password reset flow OK. Multi-tenant RLS isolation verificata.

**Documenti**:
- Spec: `agents-platform/docs/superpowers/specs/2026-05-01-customer-dashboard-e1-design.md`
- Plan: `agents-platform/docs/superpowers/plans/2026-05-01-customer-dashboard-e1.md`

**Next steps coordinated**:
- F1 (Stripe) sarà il sub-progetto immediatamente successivo, completa l'onboarding flow
- F2 (WhatsApp messaging) è gated da Twilio WhatsApp Business approval (settimane)
- D-Phase2 (site-ready call) è il secondo agente ElevenLabs per vendere $349
```

- [ ] **Step 3: Update memory `project_decomposition.md`**

Replace `- **E** — Admin dashboards multi-tenant + blog generator (requirements at...)` with:

```
- **E1** — Customer Dashboard (auth + multi-tenant foundation) ← **DEPLOYATO 2026-XX-XX**
- **E2** — Custom domain configuration ← pending
- **E3** — Analytics ← pending
- **E4** — Blog generator ← pending
- **E5** — Social integration ← pending
- **F1** — Stripe Payments + 48h grace + cleanup (one-time $349) ← pending brainstorm
- **F2** — WhatsApp follow-up agent ← pending (Twilio Business API approval gated)
- **D-Phase2** — Site-ready call (secondo agente ElevenLabs) ← pending brainstorm
```

- [ ] **Step 4: Commit**

```bash
cd "c:\Users\indig\.antigravity\AGENT 2.0_TEST/agents-platform"
# BRAINSTORM_STATE.md is in parent dir (outside agents-platform repo)
echo "BRAINSTORM_STATE updated; memory persisted via Write tool"
```

---

## Self-Review Checklist (already performed)

✅ **Spec coverage**: every section of the (slimmed-down) spec maps to one or more tasks (migration → T1; scaffold → T2; clients/UI → T3; pages → T4-T7; middleware → T8; tests → T9; deploy → T10; E2E → T11; closure → T12).

✅ **Placeholder scan**: no TBDs, all code blocks complete with full implementations.

✅ **Type consistency**: `password_changed` flag consistent across middleware, change-password, reset-password. `owner_user_id` consistent across migration, dashboard query, RLS.

✅ **No "similar to Task N"**: each task has its own complete code.

✅ **Scope alignment**: Tasks 2-4 from previous plan (Builder Agent extension + welcome email) explicitly NOT in this plan — moved to F1.
