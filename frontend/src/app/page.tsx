"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, FileBarChart, Lightbulb, LogIn, Rocket, ShieldAlert, TrendingUp, type LucideIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { CommandBar } from "@/components/command-bar";
import { GlassCard } from "@/components/glass-card";
import { useSession } from "@/lib/store";

interface Widget {
  label: string;
  value: number;
  suffix?: string;
  trend: string;
  icon: LucideIcon;
  tone: string;
}

const INITIAL_WIDGETS: Widget[] = [
  { label: "Open Issues", value: 12, trend: "-3 this week", icon: ShieldAlert, tone: "text-magenta" },
  { label: "Risk Alerts", value: 3, trend: "2 high severity", icon: TrendingUp, tone: "text-magenta" },
  { label: "Recent Projects", value: 8, trend: "+2 active", icon: FileBarChart, tone: "text-cyan" },
  { label: "Knowledge Items", value: 1.4, suffix: "k", trend: "indexed", icon: Lightbulb, tone: "text-cyan" },
];

const SUGGESTIONS = [
  "Summarize the latest battery bench test run",
  "Find previous lessons learned on hydraulic leaks",
  "Draft a design review checklist for the Gen7 ECU",
  "Which requirements contradict the thermal spec?",
];

const FEATURES = [
  { title: "Test Report Agent", desc: "Turn raw CSV/XLSX measurements into executive summaries, anomaly maps, and exportable evidence packs.", icon: FileBarChart },
  { title: "Knowledge Hub", desc: "Grounded RAG over your documents — every answer is cited back to the source.", icon: Lightbulb },
  { title: "Failure & Design Review", desc: "Diagnose DTC/sensor failures and pressure-test designs against specs with traceable reasoning.", icon: ShieldAlert },
];

export default function DashboardPage() {
  const token = useSession((s) => s.token);
  if (!token) return <MarketingLanding />;
  return <CommandCenter />;
}

function MarketingLanding() {
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-10 py-6">
      <section className="flex flex-col items-center gap-5 text-center">
        <p className="hud-kicker">AI OPERATING SYSTEM // MANUFACTURING ENGINEERING</p>
        <motion.h1
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="display-font glitch-title max-w-3xl text-4xl font-bold tracking-tight md:text-6xl"
        >
          Engineering intelligence, <span className="text-gradient">evidence-backed</span>.
        </motion.h1>
        <p className="max-w-2xl text-base leading-relaxed text-gray-300">
          EngineerGPT reduces documentation effort, accelerates analysis, and preserves company
          knowledge with AI agents built for teams that build what matters.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/signup"
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan to-sky px-6 py-3 text-sm font-bold text-black transition-transform hover:scale-[1.03]"
          >
            <Rocket className="h-4 w-4" /> Start free
          </Link>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 border border-white/15 px-6 py-3 text-sm font-semibold text-gray-200 transition-colors hover:border-cyan/50 hover:text-white"
          >
            <LogIn className="h-4 w-4" /> Sign in
          </Link>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-gray-400">
          <span className="status-dot" aria-hidden="true" /> Free plan · No credit card required
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {FEATURES.map((f, i) => {
          const Icon = f.icon;
          return (
            <GlassCard key={f.title} delay={i * 0.05}>
              <Icon className="h-6 w-6 text-cyan" aria-hidden="true" />
              <h2 className="display-font mt-3 text-xl font-semibold">{f.title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-gray-400">{f.desc}</p>
            </GlassCard>
          );
        })}
      </section>

      <section className="flex flex-col items-center gap-4 text-center">
        <h2 className="display-font text-2xl font-semibold">
          Simple, transparent <span className="text-gradient">pricing</span>
        </h2>
        <p className="max-w-xl text-sm text-gray-400">
          Start on the Free plan, upgrade to Pro or Team as your workspace grows.
        </p>
        <Link
          href="/signup"
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan to-sky px-6 py-3 text-sm font-bold text-black transition-transform hover:scale-[1.03]"
        >
          Create your workspace <ArrowRight className="h-4 w-4" />
        </Link>
      </section>
    </div>
  );
}

function CommandCenter() {
  const [widgets, setWidgets] = useState(INITIAL_WIDGETS);
  const [activeSuggestion, setActiveSuggestion] = useState<string | null>(null);

  useEffect(() => {
    // DYNAMIC STATE: subtle heartbeat proves the command center is live without heavy animation.
    const timer = window.setInterval(() => {
      setWidgets((current) => current.map((widget, index) => (
        index === 1 ? { ...widget, value: widget.value === 3 ? 4 : 3 } : widget
      )));
    }, 7000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-7">
      <header className="flex flex-col gap-3 border-l-2 border-cyan pl-4">
        <p className="hud-kicker">SYS.ENG // OPERATIONS NETWORK</p>
        <motion.h1
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="display-font glitch-title text-4xl font-bold tracking-tight md:text-6xl"
        >
          Command <span className="text-gradient">Center</span>
        </motion.h1>
        <p className="max-w-2xl text-sm leading-relaxed text-gray-300">
          Evidence-backed engineering intelligence for teams that build what matters.
        </p>
        <div className="flex items-center gap-2 text-[11px] text-gray-400" aria-live="polite">
          <span className="status-dot" aria-hidden="true" /> NETWORK ONLINE // MOCK AI READY
        </div>
      </header>

      <CommandBar />

      <section aria-label="Engineering telemetry" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {widgets.map((widget, index) => {
          const Icon = widget.icon;
          return (
            <GlassCard key={widget.label} delay={index * 0.05}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="hud-kicker text-[10px]">{widget.label}</p>
                  <p className="mt-2 font-mono text-3xl font-semibold text-white">
                    {widget.value}{widget.suffix}
                  </p>
                  <p className="mt-1 text-[11px] text-gray-400">{widget.trend}</p>
                </div>
                <Icon className={`h-5 w-5 ${widget.tone}`} aria-hidden="true" />
              </div>
            </GlassCard>
          );
        })}
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <GlassCard className="lg:col-span-2" delay={0.1}>
          <p className="hud-kicker">PRIMARY WORKFLOW // 01</p>
          <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
            <h2 className="display-font text-2xl font-semibold">Test Report Agent</h2>
            <span className="border border-cyan/40 px-2 py-1 text-[10px] font-semibold text-cyan">ONLINE</span>
          </div>
          <p className="mt-3 max-w-xl text-sm leading-relaxed text-gray-300">
            Transform CSV/XLSX measurements into executive summaries, anomaly maps, charts,
            conclusions, and exportable evidence packs.
          </p>
          <Link href="/test-report" className="cyber-button mt-5 inline-flex items-center gap-2 bg-cyan px-4 py-2 text-sm font-bold text-[#071014]">
            Open workflow <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </GlassCard>

        <GlassCard delay={0.15}>
          <p className="hud-kicker">QUICK QUERY // 04</p>
          <h2 className="display-font mt-2 text-2xl font-semibold">Knowledge Signals</h2>
          <ul className="mt-4 flex flex-col gap-2">
            {SUGGESTIONS.map((suggestion) => (
              <li key={suggestion}>
                <button
                  type="button"
                  onClick={() => setActiveSuggestion(suggestion)}
                  className="w-full border border-white/10 bg-white/[0.025] px-3 py-2 text-left text-xs text-gray-300 transition-colors hover:border-cyan/60 hover:text-white"
                >
                  {suggestion}
                </button>
              </li>
            ))}
          </ul>
          <p className="mt-3 min-h-4 text-[11px] text-cyan" aria-live="polite">
            {activeSuggestion ? `QUEUED: ${activeSuggestion}` : "Select a signal to queue it."}
          </p>
        </GlassCard>
      </section>
    </div>
  );
}
