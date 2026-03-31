"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Exam, Submission } from "@/lib/types";
import { ArrowLeft, FileText, FileUp, Loader2, Play, Trash2 } from "lucide-react";
import { useAuth } from "@/app/context/AuthContext";

export default function ExamDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const id = params.id as string;
  const [exam, setExam] = useState<Exam | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [evaluatingId, setEvaluatingId] = useState<string | null>(null);
  const [deletingExam, setDeletingExam] = useState(false);

  const canEvaluate = user?.role !== "student";

  const refresh = () => {
    api<Submission[]>(`/submissions?exam_id=${id}`).then(setSubmissions);
  };

  const handleEvaluate = async (subId: string) => {
    setEvaluatingId(subId);
    try {
      await api(`/evaluate/${subId}`, { method: "POST" });
      refresh();
    } catch {
      // noop
    } finally {
      setEvaluatingId(null);
    }
  };

  const handleDeleteExam = async () => {
    if (!exam) return;
    if (!window.confirm(`Supprimer l'examen "${exam.title}" et toutes ses copies ?`)) return;

    setDeletingExam(true);
    try {
      await api(`/exams/${id}`, { method: "DELETE" });
      router.push("/dashboard/exams");
    } catch {
      // noop
    } finally {
      setDeletingExam(false);
    }
  };

  useEffect(() => {
    Promise.all([api<Exam>(`/exams/${id}`), api<Submission[]>(`/submissions?exam_id=${id}`)])
      .then(([e, s]) => {
        setExam(e);
        setSubmissions(s);
      })
      .catch(() => router.push("/dashboard/exams"))
      .finally(() => setLoading(false));
  }, [id, router]);

  if (loading || !exam) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-10 bg-ink-200 rounded w-64" />
        <div className="h-48 bg-ink-100 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <Link
        href="/dashboard/exams"
        className="inline-flex items-center gap-2 text-ink-600 hover:text-ink-900 mb-6 text-sm font-medium"
      >
        <ArrowLeft className="w-4 h-4" />
        Retour aux examens
      </Link>

      <div className="bg-white rounded-xl border border-ink-200 p-6 mb-8">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-xl bg-brand-100 flex items-center justify-center shrink-0">
              <FileText className="w-7 h-7 text-brand-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-ink-900">{exam.title}</h1>
              {exam.description && <p className="text-ink-500 mt-2">{exam.description}</p>}
              <p className="text-sm text-ink-400 mt-2">{exam.questions.length} question(s)</p>
              {exam.class_name && <p className="text-sm text-ink-500 mt-1">Classe liee: {exam.class_name}</p>}
              {!exam.class_name && exam.class_id && (
                <p className="text-sm text-ink-500 mt-1">Classe liee</p>
              )}
            </div>
          </div>
          {canEvaluate && (
            <button
              type="button"
              onClick={handleDeleteExam}
              disabled={deletingExam}
              className="inline-flex items-center gap-2 rounded-lg border border-red-200 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50"
            >
              {deletingExam ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
              Supprimer
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-xl border border-ink-200 p-6">
          <h2 className="text-base font-semibold text-ink-900 mb-3">Enonce extrait</h2>
          {exam.statement_text ? (
            <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-lg bg-ink-50 p-4 text-sm text-ink-700">
              {exam.statement_text}
            </pre>
          ) : (
            <p className="text-sm text-ink-500">Texte d'enonce non disponible.</p>
          )}
        </div>
        <div className="bg-white rounded-xl border border-ink-200 p-6">
          <h2 className="text-base font-semibold text-ink-900 mb-3">Corrige extrait</h2>
          {exam.correction_text ? (
            <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-lg bg-ink-50 p-4 text-sm text-ink-700">
              {exam.correction_text}
            </pre>
          ) : (
            <p className="text-sm text-ink-500">Texte du corrige non disponible.</p>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-ink-900">Copies</h2>
        <Link
          href={`/dashboard/upload?exam_id=${id}`}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-ink-900 text-white font-medium hover:bg-ink-800 transition text-sm"
        >
          <FileUp className="w-4 h-4" />
          Deposer une copie
        </Link>
      </div>

      <div className="bg-white rounded-xl border border-ink-200 overflow-hidden">
        {submissions.length === 0 ? (
          <div className="p-12 text-center text-ink-500">
            <FileUp className="w-12 h-12 mx-auto mb-4 text-ink-300" />
            <p>Aucune copie deposee pour cet examen</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="bg-ink-50 text-left text-sm text-ink-600">
                <th className="px-6 py-3 font-medium">N</th>
                <th className="px-6 py-3 font-medium">Eleve</th>
                <th className="px-6 py-3 font-medium">Statut</th>
                <th className="px-6 py-3 font-medium">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-100">
              {submissions.map((s, i) => (
                <tr key={s.id} className="hover:bg-ink-50/50">
                  <td className="px-6 py-4 text-sm font-medium text-ink-700">{i + 1}</td>
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
                      {s.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {s.status === "done" ? (
                      <Link
                        href={`/dashboard/scores/${s.id}`}
                        className="text-brand-600 text-sm font-medium hover:text-brand-700"
                      >
                        Voir la note &rarr;
                      </Link>
                    ) : canEvaluate && (s.status === "pending" || s.status === "error") ? (
                      <button
                        onClick={() => handleEvaluate(s.id)}
                        disabled={evaluatingId === s.id}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-50 transition"
                      >
                        {evaluatingId === s.id ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Correction...
                          </>
                        ) : (
                          <>
                            <Play className="w-4 h-4" />
                            Corriger
                          </>
                        )}
                      </button>
                    ) : (
                      <span className="text-xs text-ink-500">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
