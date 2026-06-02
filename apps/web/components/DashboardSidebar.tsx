"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  Bot,
  Home,
  Settings,
  TestTube,
  TrendingUp,
  Sparkles,
} from "lucide-react";

const nav = [
  { href: "/dashboard", label: "Нүүр", icon: Home },
  { href: "/dashboard/subjects", label: "Хичээлүүд", icon: BookOpen },
  { href: "/dashboard/chat", label: "AI Туслах", icon: Bot },
  { href: "/dashboard/quiz", label: "Тест", icon: TestTube },
  { href: "/dashboard/progress", label: "Ахиц", icon: TrendingUp },
  { href: "/dashboard/settings", label: "Тохиргоо", icon: Settings },
];

export const DashboardSidebar = () => {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:block border-r border-neutral-200 bg-white">
      <div className="sticky top-0 h-screen overflow-y-auto p-4">
        <div className="rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-11 h-11 rounded-2xl bg-neutral-900 text-white flex items-center justify-center shadow-sm">
              <Sparkles size={18} />
            </div>
            <div>
              <p className="text-base font-semibold text-neutral-900">EduSpark</p>
              <p className="text-xs text-neutral-500">Learning OS</p>
            </div>
          </div>

          <nav className="space-y-1.5">
            {nav.map((item) => {
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    active
                      ? "bg-neutral-900 text-white shadow-sm"
                      : "text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900"
                  }`}
                >
                  <item.icon size={18} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="mt-6 rounded-2xl border border-violet-200 bg-violet-50 p-4">
            <p className="text-sm font-semibold text-violet-900">AI суралцах зөвлөмж</p>
            <p className="text-xs text-violet-700 mt-1 leading-5">
              Өнөөдөр хамгийн бага ахицтай сэдвээ 30 минут давтвал долоо хоногийн зорилгодоо хурдан хүрнэ.
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
};
