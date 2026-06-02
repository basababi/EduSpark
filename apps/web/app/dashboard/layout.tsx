import { DashboardSidebar } from "@/components/DashboardSidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-white lg:grid lg:grid-cols-[260px_1fr]">
      <DashboardSidebar />
      <main className="min-h-screen overflow-y-auto">
        {children}
      </main>
    </div>
  );
}