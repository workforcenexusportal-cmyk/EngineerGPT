"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { GlassCard } from "@/components/glass-card";

interface Props {
  title: string;
  description: string;
  endpoint: string;
}

/** Placeholder for modules that are scaffolded on the backend but pending UI. */
export function ModulePlaceholder({ title, description, endpoint }: Props) {
  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <header>
        <h1 className="text-3xl font-extrabold tracking-tight">{title}</h1>
        <p className="mt-1 text-sm text-gray-400">{description}</p>
      </header>
      <GlassCard hover={false}>
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center gap-3 py-10 text-center"
        >
          <div className="rounded-2xl bg-gradient-to-br from-cyan/20 to-violet/20 p-4">
            <Sparkles className="h-6 w-6 text-cyan" />
          </div>
          <p className="text-lg font-semibold">UI coming soon</p>
          <p className="max-w-md text-sm text-gray-400">
            The backend agent is live and callable. This interface is next on the roadmap.
          </p>
          <code className="rounded-lg border border-white/10 bg-black/40 px-3 py-1.5 text-xs text-cyan">
            POST {endpoint}
          </code>
        </motion.div>
      </GlassCard>
    </div>
  );
}
