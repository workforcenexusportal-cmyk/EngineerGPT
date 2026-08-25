"use client";

import { create } from "zustand";

export interface AuthUser {
  sub: string;
  role: "admin" | "manager" | "engineer" | "viewer";
  org_id: string | null;
}

interface SessionState {
  token: string | null;
  user: AuthUser | null;
  setSession: (token: string, user: AuthUser) => void;
  setToken: (token: string | null) => void;
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
  setSession: (token, user) => {
    persistToken(token);
    set({ token, user });
  },
  setToken: (token) => {
    persistToken(token);
    set({ token });
  },
  logout: () => {
    persistToken(null);
    set({ token: null, user: null });
  },
}));
