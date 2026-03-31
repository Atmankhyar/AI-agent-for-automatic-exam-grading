"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Exam } from "@/lib/types";
import { FileText, Plus } from "lucide-react";

export default function ExamsPage() {
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<Exam[]>("/exams")
      .then(setExams)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-10 bg-ink-200 rounded w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-40 bg-ink-100 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-ink-900">Examens</h1>
        <Link
          href="/dashboard/exams/new"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-ink-900 text-white font-medium hover:bg-ink-800 transition"
        >
          <Plus className="w-5 h-5" />
          Nouvel examen
        </Link>
      </div>

      {exams.length === 0 ? (
        <div className="bg-white rounded-xl border border-ink-200 p-16 text-center">
          <FileText className="w-16 h-16 mx-auto mb-6 text-ink-300" />
          <h2 className="text-xl font-semibold text-ink-900 mb-2">Aucun examen</h2>
          <p className="text-ink-500 mb-6 max-w-md mx-auto">
            Créez votre premier examen pour commencer à déposer et corriger des copies.
          </p>
          <Link
            href="/dashboard/exams/new"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-ink-900 text-white font-medium hover:bg-ink-800 transition"
          >
            <Plus className="w-5 h-5" />
            Créer un examen
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {exams.map((exam) => (
            <Link
              key={exam.id}
              href={`/dashboard/exams/${exam.id}`}
              className="block bg-white rounded-xl border border-ink-200 p-6 hover:border-brand-300 hover:shadow-md transition group"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-brand-100 flex items-center justify-center shrink-0 group-hover:bg-brand-200 transition">
                  <FileText className="w-6 h-6 text-brand-600" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-ink-900 truncate">{exam.title}</h3>
                  <p className="text-sm text-ink-500 mt-1 line-clamp-2">
                    {exam.description || "Aucune description"}
                  </p>
                  <p className="text-xs text-ink-400 mt-2">
                    {exam.questions.length} question(s)
                  </p>
                  {exam.class_name && (
                    <p className="text-xs text-ink-500 mt-1">Classe: {exam.class_name}</p>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
