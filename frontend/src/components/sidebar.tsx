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
  { href: "/failure-analysis", label: "Failure Analysis", icon: ShieldAlert },
  { href: "/requirements", label: "Requirements", icon: ClipboardCheck },
  { href: "/meeting-prep", label: "Meeting Prep", icon: Users },
  { href: "/design-review", label: "Design Review", icon: Activity },
];

export function Sidebar() {
  const pathname = usePathname();
  const { token, user, logout } = useSession();
  return (
    <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col gap-1 border-r border-white/10 bg-black/30 p-4 backdrop-blur-glass md:flex">
      <Link href="/" className="mb-6 flex items-center gap-2 px-2">
        <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-cyan to-violet" />
        <span className="text-lg font-bold tracking-tight text-gradient">EngineerGPT</span>
      </Link>
      <nav className="flex flex-col gap-1">
        {NAV.map(({ href, label, icon: Icon, ready }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors",
                active
                  ? "bg-white/[0.08] text-white"
                  : "text-gray-400 hover:bg-white/[0.04] hover:text-gray-200",
              )}
            >
              <Icon
                className={cn("h-4 w-4", active ? "text-cyan" : "text-gray-500 group-hover:text-cyan")}
              />
              <span className="flex-1">{label}</span>
              {!ready && (
                <span className="rounded-full bg-white/5 px-1.5 py-0.5 text-[10px] text-gray-500">
                  soon
                </span>
              )}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto flex flex-col gap-2">
        {token && (
          <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] p-3">
            <div className="h-8 w-8 shrink-0 rounded-full bg-gradient-to-br from-cyan to-violet" />
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
              className="rounded-lg p-1.5 text-gray-500 transition-colors hover:bg-rose-500/10 hover:text-rose-400"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3 text-xs text-gray-500">
          AI Operating System for Manufacturing Engineers
        </div>
      </div>
    </aside>
  );
}
