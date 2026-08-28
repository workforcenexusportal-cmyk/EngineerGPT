"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BookOpen,
  ClipboardCheck,
  FileBarChart,
  LayoutDashboard,
  LogOut,
  ShieldAlert,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSession } from "@/lib/store";

const NAV = [
  { href: "/", label: "Command Center", icon: LayoutDashboard },
  { href: "/test-report", label: "Test Report Agent", icon: FileBarChart, ready: true },
  { href: "/knowledge", label: "Knowledge Hub", icon: BookOpen, ready: true },
  { href: "/failure-analysis", label: "Failure Analysis", icon: ShieldAlert, ready: true },
  { href: "/requirements", label: "Requirements", icon: ClipboardCheck, ready: true },
  { href: "/meeting-prep", label: "Meeting Prep", icon: Users, ready: true },
  { href: "/design-review", label: "Design Review", icon: Activity, ready: true },
];

export function Sidebar() {
  const pathname = usePathname();
  const { token, user, logout } = useSession();
  return (
    <>
      {/* FIX: provide the same navigation on narrow screens; the former desktop-only nav was unreachable. */}
      <nav aria-label="Mobile navigation" className="sticky top-0 z-30 flex gap-2 overflow-x-auto border-b border-cyan/20 bg-[#0a0a0f]/95 p-3 backdrop-blur-glass md:hidden">
        {NAV.map(({ href, label, icon: Icon }) => (
          <Link key={href} href={href} aria-current={pathname === href ? "page" : undefined} className={cn("shrink-0 border px-3 py-2 text-[11px]", pathname === href ? "border-cyan bg-cyan/10 text-cyan" : "border-white/10 text-gray-400")}>
            <Icon className="mr-1 inline h-3.5 w-3.5" aria-hidden="true" />{label}
          </Link>
        ))}
      </nav>
      <aside aria-label="Primary navigation" className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col gap-1 border-r border-cyan/20 bg-[#0a0a0f]/80 p-4 backdrop-blur-glass md:flex">
      <Link href="/" className="mb-6 flex items-center gap-2 px-2">
        {/* THEME: angular cyan identity mark. */}
        <div className="h-8 w-8 border border-cyan bg-cyan/10" aria-hidden="true" />
        <span className="display-font text-lg font-bold tracking-tight text-gradient">EngineerGPT</span>
      </Link>
      <nav className="flex flex-col gap-1">
        {NAV.map(({ href, label, icon: Icon, ready }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "group flex items-center gap-3 border-l-2 border-transparent px-3 py-2.5 text-sm transition-colors",
                active
                  ? "border-cyan bg-cyan/10 text-white"
                  : "text-gray-400 hover:bg-white/[0.04] hover:text-gray-200",
              )}
            >
              <Icon
                className={cn("h-4 w-4", active ? "text-cyan" : "text-gray-500 group-hover:text-cyan")}
              />
              <span className="flex-1">{label}</span>
              {!ready && (
                <span className="border border-white/10 px-1.5 py-0.5 text-[10px] text-gray-500">
                  soon
                </span>
              )}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto flex flex-col gap-2">
        {token && (
          <div className="flex items-center gap-2 border border-white/10 bg-white/[0.03] p-3">
            <div className="h-8 w-8 shrink-0 border border-cyan bg-cyan/10" aria-hidden="true" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium text-gray-200">
                {user?.sub ?? "Signed in"}
              </p>
              <p className="text-[10px] uppercase tracking-wide text-gray-500">
                {user?.role ?? "session"}
              </p>
            </div>
            <button
              type="button"
              onClick={logout}
              aria-label="Sign out"
              className="p-1.5 text-gray-500 transition-colors hover:bg-magenta/10 hover:text-magenta"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}
        <div className="border border-white/10 bg-white/[0.03] p-3 text-xs text-gray-400">
          AI Operating System for Manufacturing Engineers
        </div>
      </div>
      </aside>
    </>
  );
}
