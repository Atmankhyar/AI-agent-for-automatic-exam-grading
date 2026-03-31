"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Score, ScoreItem } from "@/lib/types";
import { ArrowLeft, Award, CheckCircle, Loader2, RefreshCcw, XCircle } from "lucide-react";

function getCorrection(item: ScoreItem): {
  correction: string;
  reponseEtudiant: string;
  reponseAttendue: string;
} {
  const fb = item.feedback;
  if (typeof fb === "object" && fb !== null && "correction" in fb) {
    const o = fb as { correction?: string; reponse_etudiant?: string; reponse_attendue?: string };
    return {
      correction: o.correction || "",
      reponseEtudiant: o.reponse_etudiant ?? "",
      reponseAttendue: o.reponse_attendue ?? "",
    };
  }
  return {
    correction: typeof fb === "string" ? fb : "",
    reponseEtudiant: "",
    reponseAttendue: "",
  };
}

function getPlagiarism(item: ScoreItem) {
  const fb = item.feedback;
  if (typeof fb === "object" && fb !== null && "plagiarism" in fb) {
    const p = (fb as any).plagiarism;
    if (p && typeof p.ratio === "number") return p;
  }
  return null;
}

export default function ScoreDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [score, setScore] = useState<Score | null>(null);
  const [loading, setLoading] = useState(true);
  const [recomputing, setRecomputing] = useState(false);

  useEffect(() => {
    api<Score>(`/scores/${id}`)
      .then(setScore)
      .catch(() => router.push("/dashboard/scores"))
      .finally(() => setLoading(false));
  }, [id, router]);

  const recompute = async () => {
    setRecomputing(true);
    try {
      await api(`/evaluate/${id}`, { method: "POST" });
      const updated = await api<Score>(`/scores/${id}`);
      setScore(updated);
    } catch {
      // ignore
    } finally {
      setRecomputing(false);
    }
  };

  if (loading || !score) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-10 bg-ink-200 rounded w-64" />
        <div className="h-48 bg-ink-100 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="animate-fade-in max-w-2xl">
      <Link
        href="/dashboard/scores"
        className="inline-flex items-center gap-2 text-ink-600 hover:text-ink-900 mb-6 text-sm font-medium"
      >
        <ArrowLeft className="w-4 h-4" />
        Retour aux scores
      </Link>

      <div className="bg-white rounded-xl border border-ink-200 overflow-hidden">
        <div className="p-8 bg-gradient-to-br from-ink-50 to-ink-100/50">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-brand-100 flex items-center justify-center">
              <Award className="w-8 h-8 text-brand-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-ink-900">Correction de la copie</h1>
              <p className="text-ink-500 mt-1">Detail des resultats par question</p>
            </div>
          </div>
          <div className="mt-8 flex items-baseline gap-2">
            <span className="text-4xl font-bold text-ink-900">{score.total.toFixed(1)}</span>
            <span className="text-ink-500"> /20</span>
          </div>
          <div className="mt-4">
            <button
              type="button"
              onClick={recompute}
              disabled={recomputing}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-ink-200 text-sm font-medium text-ink-700 hover:bg-ink-50 disabled:opacity-50"
            >
              {recomputing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCcw className="w-4 h-4" />}
              Recalculer la note
            </button>
          </div>
        </div>

        <div className="p-6 border-t border-ink-200">
          <h2 className="font-semibold text-ink-900 mb-4">Correction par question</h2>
          <div className="space-y-6">
            {score.items.map((item, i) => {
              const { correction, reponseEtudiant, reponseAttendue } = getCorrection(item);
              const isCorrect = item.points > 0;
              const plagiarism = getPlagiarism(item);
              return (
                <div
                  key={item.id}
                  className={`p-5 rounded-xl border ${
                    isCorrect ? "border-emerald-200 bg-emerald-50/50" : "border-amber-200 bg-amber-50/30"
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-semibold text-ink-900">Question {i + 1}</span>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-medium text-brand-600">
                        {item.points.toFixed(1)} pts
                      </span>
                      {isCorrect ? (
                        <CheckCircle className="w-5 h-5 text-emerald-600" />
                      ) : (
                        <XCircle className="w-5 h-5 text-amber-600" />
                      )}
                    </div>
                  </div>
                  {plagiarism && (
                    <div className="mb-3 text-xs font-medium text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                      Reponse tres similaire detectee (ratio {Math.round(plagiarism.ratio * 100)}%). Soumission liee:{" "}
                      {plagiarism.other_submission_id || "inconnue"}.
                    </div>
                  )}
                  {correction && (
                    <p className="text-sm text-ink-700 mb-2">{correction}</p>
                  )}
                  {(reponseEtudiant || reponseAttendue) && (
                    <div className="mt-3 space-y-2 text-sm">
                      {reponseEtudiant && (
                        <div>
                          <span className="font-medium text-ink-500">Votre réponse :</span>{" "}
                          <span className="text-ink-700">{reponseEtudiant}</span>
                        </div>
                      )}
                      {reponseAttendue && (
                        <div>
                          <span className="font-medium text-ink-500">Réponse attendue :</span>{" "}
                          <span className="text-ink-700">{reponseAttendue}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
