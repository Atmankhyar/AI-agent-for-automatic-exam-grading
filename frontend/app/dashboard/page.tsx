"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Exam, Submission } from "@/lib/types";
import { FileText, FileUp, TrendingUp, ArrowRight } from "lucide-react";

export default function DashboardPage() {
  const [exams, setExams] = useState<Exam[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api<Exam[]>("/exams"),
      api<Submission[]>("/submissions"),
    ])
      .then(([e, s]) => {
        setExams(e);
        setSubmissions(s);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const doneCount = submissions.filter((s) => s.status === "done").length;
  const pendingCount = submissions.filter((s) => s.status === "pending" || s.status === "processing").length;

  if (loading) {
    return (
      <div className="animate-pulse space-y-8">
        <div className="h-10 bg-ink-200 rounded w-48" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 bg-ink-100 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <h1 className="text-2xl font-bold text-ink-900 mb-8">Tableau de bord</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <div className="bg-white rounded-xl border border-ink-200 p-6 shadow-sm hover:shadow-md transition">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-brand-100 flex items-center justify-center">
              <FileText className="w-6 h-6 text-brand-600" />
            </div>
            <span className="text-ink-500 font-medium">Examens</span>
          </div>
          <p className="text-3xl font-bold text-ink-900">{exams.length}</p>
          <Link
            href="/dashboard/exams"
            className="mt-4 inline-flex items-center gap-1 text-brand-600 text-sm font-medium hover:text-brand-700"
          >
            Voir les examens <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="bg-white rounded-xl border border-ink-200 p-6 shadow-sm hover:shadow-md transition">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-emerald-600" />
            </div>
            <span className="text-ink-500 font-medium">Copies corrigées</span>
          </div>
          <p className="text-3xl font-bold text-ink-900">{doneCount}</p>
        </div>

        <div className="bg-white rounded-xl border border-ink-200 p-6 shadow-sm hover:shadow-md transition">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center">
              <FileUp className="w-6 h-6 text-amber-600" />
            </div>
            <span className="text-ink-500 font-medium">En attente</span>
          </div>
          <p className="text-3xl font-bold text-ink-900">{pendingCount}</p>
          <Link
            href="/dashboard/upload"
            className="mt-4 inline-flex items-center gap-1 text-brand-600 text-sm font-medium hover:text-brand-700"
          >
            Déposer des copies <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-ink-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-ink-200">
          <h2 className="font-semibold text-ink-900">Dernières copies</h2>
          <p className="text-sm text-ink-500 mt-0.5">Copies récemment déposées ou corrigées</p>
        </div>
        <div className="overflow-x-auto">
          {submissions.length === 0 ? (
            <div className="p-12 text-center text-ink-500">
              <FileUp className="w-12 h-12 mx-auto mb-4 text-ink-300" />
              <p>Aucune copie déposée</p>
              <Link
                href="/dashboard/upload"
                className="mt-2 inline-block text-brand-600 font-medium hover:text-brand-700"
              >
                Déposer votre première copie
              </Link>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="bg-ink-50 text-left text-sm text-ink-600">
                  <th className="px-6 py-3 font-medium">N</th>
                  <th className="px-6 py-3 font-medium">Examen</th>
                  <th className="px-6 py-3 font-medium">Eleve</th>
                  <th className="px-6 py-3 font-medium">Statut</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-100">
                {submissions.slice(0, 10).map((s, i) => (
                  <tr key={s.id} className="hover:bg-ink-50/50">
                    <td className="px-6 py-4 text-sm font-medium text-ink-700">{i + 1}</td>
                    <td className="px-6 py-4 text-sm text-ink-700">{s.exam_title || "-"}</td>
                    <td className="px-6 py-4 text-sm text-ink-600">{s.student_email || "-"}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`
                          inline-flex px-2.5 py-1 rounded-full text-xs font-medium
                          ${s.status === "done" ? "bg-emerald-100 text-emerald-700" : ""}
                          ${s.status === "processing" ? "bg-amber-100 text-amber-700" : ""}
                          ${s.status === "pending" ? "bg-ink-100 text-ink-600" : ""}
                          ${s.status === "error" ? "bg-red-100 text-red-700" : ""}
                        `}
                      >
                        {s.status === "done" && "Corrigée"}
                        {s.status === "processing" && "En cours"}
                        {s.status === "pending" && "En attente"}
                        {s.status === "error" && "Erreur"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
