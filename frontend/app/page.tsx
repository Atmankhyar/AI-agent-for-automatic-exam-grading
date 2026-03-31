"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./context/AuthContext";

export default function Home() {
  const { token, isReady } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isReady) return;
    if (token) router.replace("/dashboard");
    else router.replace("/login");
  }, [token, isReady, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-ink-50">
      <div className="animate-pulse flex flex-col items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-brand-500/20" />
        <p className="text-ink-500 text-sm">Chargement...</p>
      </div>
    </div>
  );
}
