"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clsx } from "clsx";
import {
  Award,
  FileCheck,
  FileText,
  FileUp,
  LayoutDashboard,
  LogOut,
  Users,
} from "lucide-react";
import { useAuth } from "@/app/context/AuthContext";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { logout, user } = useAuth();

  const teacherNav = [
    { href: "/dashboard", label: "Tableau de bord", icon: LayoutDashboard },
    { href: "/dashboard/exams", label: "Examens", icon: FileText },
    { href: "/dashboard/classes", label: "Classes", icon: Users },
    { href: "/dashboard/upload", label: "Deposer des copies", icon: FileUp },
    { href: "/dashboard/scores", label: "Scores", icon: Award },
  ];

  const studentNav = [
    { href: "/dashboard", label: "Tableau de bord", icon: LayoutDashboard },
    { href: "/dashboard/exams", label: "Mes examens", icon: FileText },
    { href: "/dashboard/scores", label: "Mes notes", icon: Award },
  ];

  const nav = user?.role === "student" ? studentNav : teacherNav;

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-ink-900 text-white flex flex-col shrink-0">
        <div className="p-6 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-500/20 flex items-center justify-center">
            <FileCheck className="w-6 h-6 text-brand-400" />
          </div>
          <span className="font-semibold text-lg">ExamESICorrector</span>
        </div>

        {user && (
          <div className="px-6 pb-4 text-xs text-ink-400">
            <p className="font-medium text-ink-300">{user.full_name || user.email}</p>
            <p className="uppercase tracking-wide mt-1">{user.role}</p>
          </div>
        )}

        <nav className="flex-1 px-4 space-y-1">
          {nav.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition",
                  active
                    ? "bg-brand-500/20 text-brand-300"
                    : "text-ink-400 hover:bg-ink-800 hover:text-white"
                )}
              >
                <Icon className="w-5 h-5 shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-ink-700">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-4 py-3 rounded-lg text-ink-400 hover:bg-ink-800 hover:text-white text-sm font-medium transition"
          >
            <LogOut className="w-5 h-5" />
            Deconnexion
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        <div className="p-8">{children}</div>
      </main>
    </div>
  );
}
