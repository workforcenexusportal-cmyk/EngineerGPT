"use client";

import { create } from "zustand";
import type { AuthUser, SessionContext } from "@/lib/api";

interface SessionState {
  token: string | null;
  user: AuthUser | null;
  context: SessionContext | null;
  setSession: (token: string, user: AuthUser) => void;
  setToken: (token: string | null) => void;
  setContext: (context: SessionContext | null) => void;
  logout: () => void;
}

function readToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("egpt_token");
}

function persistToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem("egpt_token", token);
  else localStorage.removeItem("egpt_token");
}

/** Minimal auth/session store. Token is persisted to localStorage on the client. */
export const useSession = create<SessionState>((set) => ({
  token: readToken(),
  user: null,
  context: null,
  setSession: (token, user) => {
    persistToken(token);
    set({ token, user });
  },
  setToken: (token) => {
    persistToken(token);
    set({ token, user: null, context: null });
  },
  setContext: (context) => set({ context }),
  logout: () => {
    persistToken(null);
    set({ token: null, user: null, context: null });
  },
}));
