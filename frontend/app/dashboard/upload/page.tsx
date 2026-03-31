"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { api, apiUpload } from "@/lib/api";
import { Exam, Student } from "@/lib/types";
import { CheckCircle, Loader2, Upload } from "lucide-react";
import { useAuth } from "@/app/context/AuthContext";

export default function UploadPage() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const preselectedExamId = searchParams.get("exam_id");
  const [exams, setExams] = useState<Exam[]>([]);
  const [selectedExamId, setSelectedExamId] = useState(preselectedExamId || "");
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    api<Exam[]>("/exams")
      .then(setExams)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (preselectedExamId) setSelectedExamId(preselectedExamId);
  }, [preselectedExamId]);

  const selectedExam = useMemo(
    () => exams.find((e) => e.id === selectedExamId) || null,
    [exams, selectedExamId]
  );

  useEffect(() => {
    setStudents([]);
    setSelectedStudentId("");

    if (!selectedExam?.class_id || user?.role === "student") {
      return;
    }

    api<Student[]>(`/classes/${selectedExam.class_id}/students`)
      .then(setStudents)
      .catch(() => {});
  }, [selectedExam, user?.role]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f && (f.type === "application/pdf" || f.type.startsWith("image/"))) {
      setFile(f);
    } else {
      setError("Format accepte: PDF ou image (PNG, JPG, etc.)");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedExamId || !file) {
      setError("Selectionnez un examen et un fichier");
      return;
    }

    if (user?.role !== "student" && selectedExam?.class_id && students.length > 0 && !selectedStudentId) {
      setError("Selectionnez l'eleve de cette copie");
      return;
    }

    setError("");
    setLoading(true);
    setSuccess(null);
    try {
      const { file_uri } = await apiUpload("/upload", file);
      await api("/submissions", {
        method: "POST",
        body: JSON.stringify({
          exam_id: selectedExamId,
          file_uri,
          student_id: selectedStudentId || null,
        }),
      });

      setSuccess("Copie deposee avec succes.");
      setFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors du depot");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in max-w-xl">
      <h1 className="text-2xl font-bold text-ink-900 mb-2">Deposer des copies</h1>
      <p className="text-ink-500 mb-8">
        Uploadez une copie (PDF ou image) pour un examen et associez-la a l'eleve.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && <div className="p-4 rounded-lg bg-red-50 text-red-700 text-sm">{error}</div>}
        {success && (
          <div className="p-4 rounded-lg bg-emerald-50 text-emerald-700 text-sm flex items-center gap-2">
            <CheckCircle className="w-5 h-5 shrink-0" />
            {success}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-ink-700 mb-2">Examen</label>
          <select
            value={selectedExamId}
            onChange={(e) => setSelectedExamId(e.target.value)}
            required
            className="w-full px-4 py-3 rounded-lg border border-ink-200 bg-white"
          >
            <option value="">Selectionner un examen</option>
            {exams.map((exam) => (
              <option key={exam.id} value={exam.id}>
                {exam.title}
              </option>
            ))}
          </select>
          {exams.length === 0 && (
            <p className="text-sm text-ink-500 mt-2">
              Aucun examen. <Link href="/dashboard/exams/new" className="text-brand-600 hover:underline">Creer un examen</Link>
            </p>
          )}
        </div>

        {user?.role !== "student" && selectedExam?.class_id && (
          <div>
            <label className="block text-sm font-medium text-ink-700 mb-2">Eleve</label>
            <select
              value={selectedStudentId}
              onChange={(e) => setSelectedStudentId(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-ink-200 bg-white"
            >
              <option value="">Selectionner un eleve</option>
              {students.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.full_name || s.email}
                </option>
              ))}
            </select>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-ink-700 mb-2">Fichier de la copie</label>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`
              relative border-2 border-dashed rounded-xl p-12 text-center transition
              ${dragOver ? "border-brand-500 bg-brand-50" : "border-ink-200 hover:border-ink-300"}
              ${file ? "border-brand-500 bg-brand-50/50" : ""}
            `}
          >
            <input
              type="file"
              accept=".pdf,image/*"
              onChange={(e) => {
                const f = e.target.files?.[0];
                setFile(f || null);
                setError("");
              }}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            {file ? (
              <div>
                <CheckCircle className="w-12 h-12 mx-auto mb-3 text-brand-600" />
                <p className="font-medium text-ink-900">{file.name}</p>
                <p className="text-sm text-ink-500 mt-1">{(file.size / 1024).toFixed(1)} Ko</p>
              </div>
            ) : (
              <div>
                <Upload className="w-12 h-12 mx-auto mb-3 text-ink-400" />
                <p className="font-medium text-ink-900">Glissez-deposez ou cliquez pour selectionner</p>
                <p className="text-sm text-ink-500 mt-1">PDF, PNG, JPG</p>
              </div>
            )}
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !file || !selectedExamId}
          className="w-full py-3 px-4 rounded-lg bg-ink-900 text-white font-medium hover:bg-ink-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Depot en cours...
            </>
          ) : (
            <>
              <Upload className="w-5 h-5" />
              Deposer la copie
            </>
          )}
        </button>
      </form>
    </div>
  );
}
