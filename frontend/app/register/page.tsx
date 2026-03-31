"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "../context/AuthContext";
import { api, apiPostForm } from "@/lib/api";
import { Token } from "@/lib/types";
import { FileCheck, Loader2 } from "lucide-react";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("teacher");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, role }),
        token: null,
      });

      const form = new FormData();
      form.append("username", email);
      form.append("password", password);
      const data = await apiPostForm<Token>("/auth/login", form, null);
      await login(data.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de l'inscription");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-brand-900 via-ink-800 to-ink-900 p-12 flex-col justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-500/20 flex items-center justify-center">
            <FileCheck className="w-6 h-6 text-brand-400" />
          </div>
          <span className="text-xl font-semibold text-white">ExamESICorrector</span>
        </div>
        <div>
          <h2 className="text-3xl font-bold text-white mb-4">Simplifiez la correction</h2>
          <p className="text-ink-300 text-lg max-w-md">
            Creez des examens, uploadez les copies, et obtenez des scores detailles en quelques
            minutes.
          </p>
        </div>
        <p className="text-ink-500 text-sm">© 2026 ExamESICorrector</p>
      </div>

      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-ink-50">
        <div className="w-full max-w-sm animate-fade-in">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-brand-500 flex items-center justify-center">
              <FileCheck className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-semibold text-ink-900">ExamESICorrector</span>
          </div>

          <h1 className="text-2xl font-bold text-ink-900 mb-2">Creer un compte</h1>
          <p className="text-ink-500 mb-8">Rejoignez ExamESICorrector en quelques clics</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && <div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm">{error}</div>}

            <div>
              <label className="block text-sm font-medium text-ink-700 mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 rounded-lg border border-ink-200 bg-white text-ink-900 placeholder-ink-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
                placeholder="vous@exemple.fr"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-ink-700 mb-1.5">Mot de passe</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="w-full px-4 py-3 rounded-lg border border-ink-200 bg-white text-ink-900 placeholder-ink-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
                placeholder="********"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-ink-700 mb-1.5">Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full px-4 py-3 rounded-lg border border-ink-200 bg-white text-ink-900 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
              >
                <option value="teacher">Enseignant</option>
                <option value="student">Eleve</option>
                <option value="admin">Administrateur</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 rounded-lg bg-ink-900 text-white font-medium hover:bg-ink-800 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Inscription...
                </>
              ) : (
                "S'inscrire"
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-ink-500 text-sm">
            Deja un compte ?{" "}
            <Link href="/login" className="text-brand-600 font-medium hover:text-brand-700">
              Se connecter
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
