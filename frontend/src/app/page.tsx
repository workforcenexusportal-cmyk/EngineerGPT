"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  FileBarChart,
  Lightbulb,
  ShieldAlert,
  TrendingUp,
} from "lucide-react";
import { CommandBar } from "@/components/command-bar";
import { GlassCard } from "@/components/glass-card";

const WIDGETS = [
  { label: "Open Issues", value: "12", trend: "-3 this week", icon: ShieldAlert, tone: "text-amber-400" },
  { label: "Risk Alerts", value: "3", trend: "2 high severity", icon: TrendingUp, tone: "text-rose-400" },
  { label: "Recent Projects", value: "8", trend: "+2 active", icon: FileBarChart, tone: "text-cyan" },
  { label: "Knowledge Items", value: "1.4k", trend: "indexed", icon: Lightbulb, tone: "text-violet" },
];

const SUGGESTIONS = [
  "Summarize the latest battery bench test run",
  "Find previous lessons learned on hydraulic leaks",
  "Draft a design review checklist for the Gen7 ECU",
  "Which requirements contradict the thermal spec?",
];

export default function DashboardPage() {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-8">
      <header className="flex flex-col gap-2">
        <motion.h1
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-3xl font-extrabold tracking-tight md:text-4xl"
        >
          AI <span className="text-gradient">Command Center</span>
        </motion.h1>
        <p className="text-sm text-gray-400">
          Your engineering operating system. Upload data, ask questions, ship faster.
        </p>
      </header>

      <CommandBar />

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {WIDGETS.map((w, i) => (
          <GlassCard key={w.label} delay={i * 0.06}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-gray-400">{w.label}</p>
                <p className="mt-1 text-2xl font-bold">{w.value}</p>
                <p className="mt-1 text-[11px] text-gray-500">{w.trend}</p>
              </div>
              <w.icon className={`h-5 w-5 ${w.tone}`} />
            </div>
          </GlassCard>
        ))}
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <GlassCard className="lg:col-span-2" delay={0.1}>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Start with the Test Report Agent</h2>
            <span className="rounded-full bg-cyan/10 px-2 py-0.5 text-[11px] text-cyan">MVP</span>
          </div>
          <p className="mt-2 text-sm text-gray-400">
            Upload CSV or XLSX measurement data and get an executive summary, engineering
            charts, anomaly detection, conclusions, and an exportable PDF.
          </p>
          <Link
            href="/test-report"
            className="mt-4 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan to-sky px-4 py-2 text-sm font-semibold text-black transition-transform hover:scale-[1.03]"
          >
            Open agent <ArrowRight className="h-4 w-4" />
          </Link>
        </GlassCard>

        <GlassCard delay={0.16}>
          <h2 className="text-lg font-semibold">Knowledge Suggestions</h2>
          <ul className="mt-3 flex flex-col gap-2">
            {SUGGESTIONS.map((s) => (
              <li
                key={s}
                className="cursor-pointer rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2 text-xs text-gray-300 transition-colors hover:border-cyan/30 hover:text-white"
              >
                {s}
              </li>
            ))}
          </ul>
        </GlassCard>
      </section>
    </div>
  );
}
