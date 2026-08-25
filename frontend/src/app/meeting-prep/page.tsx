"use client";

import { AnimatePresence } from "framer-motion";
import { Loader2, Sparkles, Users } from "lucide-react";
import { useState } from "react";
import { ApiError, prepareMeeting, type AgentResult } from "@/lib/api";
import { AgentResultView } from "@/components/agent-result-view";
import { AuthGate } from "@/components/auth-gate";
import { GlassCard } from "@/components/glass-card";
import { useSession } from "@/lib/store";

export default function MeetingPrepPage() {
  return (
    <AuthGate>
      <MeetingPrep />
    </AuthGate>
  );
}

function MeetingPrep() {
  const token = useSession((s) => s.token);
  const [topic, setTopic] = useState("");
  const [context, setContext] = useState("");
  const [issues, setIssues] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AgentResult | null>(null);

  const onRun = async () => {
    if (!token || topic.trim().length < 3) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const open_issues = issues
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean);
      setResult(
        await prepareMeeting(
          { topic: topic.trim(), context: context.trim(), open_issues },
          token,
        ),
      );
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Preparation failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <header>
        <h1 className="flex items-center gap-2 text-3xl font-extrabold tracking-tight">
          <Users className="h-7 w-7 text-violet" />
          Meeting <span className="text-gradient">Prep</span>
        </h1>
        <p className="mt-1 text-sm text-gray-400">
          Generate an agenda, talking points, key risks, and follow-up actions in seconds.
        </p>
      </header>

      <GlassCard hover={false}>
        <div className="flex flex-col gap-4">
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-medium text-gray-400">Meeting topic</span>
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Gen7 ECU design review kickoff"
              className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-gray-100 placeholder:text-gray-500 focus:border-cyan/40 focus:outline-none"
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-medium text-gray-400">Context (optional)</span>
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              rows={5}
              placeholder="Background, prior decisions, stakeholders, constraints…"
              className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-gray-100 placeholder:text-gray-500 focus:border-cyan/40 focus:outline-none"
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-medium text-gray-400">Open issues (one per line)</span>
            <textarea
              value={issues}
              onChange={(e) => setIssues(e.target.value)}
              rows={4}
              placeholder={"Thermal derating threshold unresolved\nSupplier B connector lead time"}
              className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-gray-100 placeholder:text-gray-500 focus:border-cyan/40 focus:outline-none"
            />
          </label>
          <button
            type="button"
            onClick={onRun}
            disabled={loading || topic.trim().length < 3}
            className="inline-flex w-fit items-center gap-2 rounded-xl bg-gradient-to-r from-cyan to-sky px-5 py-2.5 text-sm font-semibold text-black transition-transform enabled:hover:scale-[1.03] disabled:cursor-not-allowed disabled:opacity-40"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {loading ? "Preparing…" : "Prepare meeting"}
          </button>
          {error && (
            <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
              {error}
            </p>
          )}
        </div>
      </GlassCard>

      <AnimatePresence mode="wait">
        {result && <AgentResultView key="r" result={result} />}
      </AnimatePresence>
    </div>
  );
}
