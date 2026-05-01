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
