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
