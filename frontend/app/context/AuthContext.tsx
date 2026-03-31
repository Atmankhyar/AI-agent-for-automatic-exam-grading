"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Me } from "@/lib/types";

interface AuthContextType {
  token: string | null;
  user: Me | null;
  login: (token: string) => Promise<void>;
  logout: () => void;
  isReady: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function readStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem("token");
  } catch {
    return null;
  }
}

function writeStoredToken(value: string | null) {
  if (typeof window === "undefined") return;
  try {
    if (value) localStorage.setItem("token", value);
    else localStorage.removeItem("token");
  } catch {
    // Ignore storage failures and keep in-memory auth state usable.
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<Me | null>(null);
  const [isReady, setIsReady] = useState(false);

  async function loadMe(tokenValue: string) {
    try {
      const me = await api<Me>("/auth/me", { token: tokenValue });
      setUser(me);
    } catch {
      writeStoredToken(null);
      setToken(null);
      setUser(null);
    }
  }

  useEffect(() => {
    const t = readStoredToken();
    setToken(t);
    if (!t) {
      setIsReady(true);
      return;
    }

    loadMe(t).finally(() => setIsReady(true));
  }, []);

  const login = async (t: string) => {
    writeStoredToken(t);
    setToken(t);
    await loadMe(t);
  };

  const logout = () => {
    writeStoredToken(null);
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isReady }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (ctx === undefined) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
