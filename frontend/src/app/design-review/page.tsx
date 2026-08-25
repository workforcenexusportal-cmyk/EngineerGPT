"use client";

import { AnimatePresence } from "framer-motion";
import { Activity, Loader2, Sparkles } from "lucide-react";
import { useState } from "react";
import { ApiError, reviewDesign, type AgentResult } from "@/lib/api";
import { AgentResultView } from "@/components/agent-result-view";
import { AuthGate } from "@/components/auth-gate";
import { GlassCard } from "@/components/glass-card";
import { useSession } from "@/lib/store";

export default function DesignReviewPage() {
  return (
    <AuthGate>
      <DesignReview />
    </AuthGate>
  );
}

function DesignReview() {
  const token = useSession((s) => s.token);
  const [design, setDesign] = useState("");
  const [specs, setSpecs] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AgentResult | null>(null);

  const onRun = async () => {
    if (!token || design.trim().length < 10) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(
        await reviewDesign(
          { design: design.trim(), specifications: specs.trim() },
          token,
        ),
      );
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Review failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <header>
        <h1 className="flex items-center gap-2 text-3xl font-extrabold tracking-tight">
          <Activity className="h-7 w-7 text-sky" />
          Design <span className="text-gradient">Review</span>
        </h1>
        <p className="mt-1 text-sm text-gray-400">
          Surface engineering risks, missing information, and improvements against your specs.
        </p>
      </header>

      <GlassCard hover={false}>
        <div className="flex flex-col gap-4">
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-medium text-gray-400">Design description</span>
            <textarea
              value={design}
              onChange={(e) => setDesign(e.target.value)}
              rows={8}
              placeholder="Describe the design: architecture, components, materials, interfaces, operating envelope…"
              className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-gray-100 placeholder:text-gray-500 focus:border-cyan/40 focus:outline-none"
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-medium text-gray-400">Specifications (optional)</span>
            <textarea
              value={specs}
              onChange={(e) => setSpecs(e.target.value)}
              rows={5}
              placeholder="Target requirements, standards, tolerances the design must meet…"
              className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-gray-100 placeholder:text-gray-500 focus:border-cyan/40 focus:outline-none"
            />
          </label>
          <button
            type="button"
            onClick={onRun}
            disabled={loading || design.trim().length < 10}
            className="inline-flex w-fit items-center gap-2 rounded-xl bg-gradient-to-r from-cyan to-sky px-5 py-2.5 text-sm font-semibold text-black transition-transform enabled:hover:scale-[1.03] disabled:cursor-not-allowed disabled:opacity-40"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {loading ? "Reviewing…" : "Review design"}
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
