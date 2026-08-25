"use client";

import { create } from "zustand";

interface SessionState {
  token: string | null;
  setToken: (token: string | null) => void;
}

/** Minimal auth/session store. Persisted to localStorage on the client. */
export const useSession = create<SessionState>((set) => ({
  token: typeof window !== "undefined" ? localStorage.getItem("egpt_token") : null,
  setToken: (token) => {
    if (typeof window !== "undefined") {
      if (token) localStorage.setItem("egpt_token", token);
      else localStorage.removeItem("egpt_token");
    }
    set({ token });
  },
}));
