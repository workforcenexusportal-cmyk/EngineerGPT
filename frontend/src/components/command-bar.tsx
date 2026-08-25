"use client";

import { motion } from "framer-motion";
import { Search, Sparkles } from "lucide-react";
import { useState } from "react";

/** The main "Ask EngineerGPT anything…" command bar. */
export function CommandBar() {
  const [value, setValue] = useState("");
  return (
    <motion.div
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="glass flex items-center gap-3 rounded-2xl px-4 py-3"
    >
      <Search className="h-5 w-5 text-cyan" />
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ask EngineerGPT anything…"
        className="flex-1 bg-transparent text-sm text-gray-100 placeholder:text-gray-500 focus:outline-none"
        aria-label="Ask EngineerGPT"
      />
      <button
        type="button"
        className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-cyan to-sky px-3 py-1.5 text-xs font-semibold text-black transition-transform hover:scale-[1.03]"
      >
        <Sparkles className="h-3.5 w-3.5" />
        Ask
      </button>
    </motion.div>
  );
}
