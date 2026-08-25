"use client";

import { AnimatePresence } from "framer-motion";
import { Loader2, ShieldAlert, Sparkles } from "lucide-react";
import { useState } from "react";
import { analyzeFailure, ApiError, type AgentResult } from "@/lib/api";
import { AgentResultView } from "@/components/agent-result-view";
import { AuthGate } from "@/components/auth-gate";
import { GlassCard } from "@/components/glass-card";
import { useSession } from "@/lib/store";

export default function FailureAnalysisPage() {
  return (
    <AuthGate>
      <FailureAnalysis />
    </AuthGate>
  );
}

function parseSensorData(text: string): Record<string, number> {
  const out: Record<string, number> = {};
  for (const line of text.split(/[\n,]/)) {
    const [k, v] = line.split(/[=:]/).map((s) => s.trim());
    if (k && v !== undefined && !Number.isNaN(Number(v))) out[k] = Number(v);
  }
  return out;
}

function FailureAnalysis() {
  const token = useSession((s) => s.token);
  const [dtc, setDtc] = useState("");
  const [sensors, setSensors] = useState("");
  const [logs, setLogs] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AgentResult | null>(null);

  const onRun = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const dtc_codes = dtc
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      setResult(
        await analyzeFailure(
          { dtc_codes, sensor_data: parseSensorData(sensors), logs },
          token,
        ),
      );
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Analysis failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <header>
        <h1 className="flex items-center gap-2 text-3xl font-extrabold tracking-tight">
          <ShieldAlert className="h-7 w-7 text-amber-400" />
          Failure <span className="text-gradient">Analysis</span>
        </h1>
        <p className="mt-1 text-sm text-gray-400">
          Rank probable causes and root causes from diagnostic codes, sensor readings, and logs.
        </p>
      </header>

      <GlassCard hover={false}>
        <div className="flex flex-col gap-4">
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-medium text-gray-400">DTC codes (comma-separated)</span>
            <input
              value={dtc}
              onChange={(e) => setDtc(e.target.value)}
              placeholder="P0300, U0121, C1234"
              className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-gray-100 placeholder:text-gray-500 focus:border-cyan/40 focus:outline-none"
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-medium text-gray-400">
              Sensor data (one <code className="text-cyan">key=value</code> per line)
            </span>
            <textarea
              value={sensors}
              onChange={(e) => setSensors(e.target.value)}
              rows={4}
              placeholder={"coolant_temp=118\noil_pressure=12\nbattery_voltage=11.4"}
              className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 font-mono text-sm text-gray-100 placeholder:text-gray-500 focus:border-cyan/40 focus:outline-none"
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-medium text-gray-400">Logs / observations</span>
            <textarea
              value={logs}
              onChange={(e) => setLogs(e.target.value)}
              rows={5}
              placeholder="Intermittent stall under load; misfire counter climbing on cylinder 3…"
              className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-gray-100 placeholder:text-gray-500 focus:border-cyan/40 focus:outline-none"
            />
          </label>
          <button
            type="button"
            onClick={onRun}
            disabled={loading || (!dtc && !sensors && !logs)}
            className="inline-flex w-fit items-center gap-2 rounded-xl bg-gradient-to-r from-cyan to-sky px-5 py-2.5 text-sm font-semibold text-black transition-transform enabled:hover:scale-[1.03] disabled:cursor-not-allowed disabled:opacity-40"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {loading ? "Analyzing…" : "Analyze failure"}
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
