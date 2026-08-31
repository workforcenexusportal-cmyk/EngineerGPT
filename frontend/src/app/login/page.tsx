"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { KeyRound, Loader2, LogIn } from "lucide-react";
import { useState } from "react";
import { ApiError, getContext, getMe, login } from "@/lib/api";
import { GlassCard } from "@/components/glass-card";
import { useSession } from "@/lib/store";

export default function LoginPage() {
  const router = useRouter();
  const { setSession, setContext } = useSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const session = await login(email, password);
      const me = await getMe(session.access_token);
      setSession(session.access_token, me);
      try {
        setContext(await getContext(session.access_token));
      } catch {
        /* best-effort */
      }
      router.push("/");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Sign-in failed. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-md flex-col justify-center">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <div className="mb-6 flex flex-col gap-2 text-center">
          <p className="hud-kicker">ACCESS TERMINAL</p>
          <h1 className="display-font text-3xl font-bold">
            Welcome <span className="text-gradient">back</span>
          </h1>
        </div>

        <GlassCard hover={false}>
          <div className="mb-5 flex items-center gap-3">
            <div className="rounded-xl bg-gradient-to-br from-cyan to-violet p-2">
              <KeyRound className="h-5 w-5 text-black" />
            </div>
            <div>
              <h2 className="text-lg font-bold">Sign in</h2>
              <p className="text-xs text-gray-500">Access your engineering workspace.</p>
            </div>
          </div>

          <form onSubmit={onSubmit} className="flex flex-col gap-3">
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              autoComplete="username"
              className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-gray-100 placeholder:text-gray-500 focus:border-cyan/40 focus:outline-none"
            />
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              autoComplete="current-password"
              className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-gray-100 placeholder:text-gray-500 focus:border-cyan/40 focus:outline-none"
            />

            {error && (
              <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan to-sky px-5 py-2.5 text-sm font-semibold text-black transition-transform enabled:hover:scale-[1.02] disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <LogIn className="h-4 w-4" />}
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="mt-4 text-center text-xs text-gray-500">
            No account?{" "}
            <Link href="/signup" className="text-cyan hover:underline">
              Create your workspace
            </Link>
          </p>
        </GlassCard>
      </motion.div>
    </div>
  );
}
