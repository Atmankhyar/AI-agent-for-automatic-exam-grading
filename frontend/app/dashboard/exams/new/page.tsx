"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, apiPostForm } from "@/lib/api";
import { Classroom, Exam } from "@/lib/types";
import { FileText, Plus, Trash2, Upload } from "lucide-react";

interface BaremeItem {
  type: string;
  answer_key: string;
  max_points: string;
  order: number;
}

export default function NewExamPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [manualStatement, setManualStatement] = useState("");
  const [statementFile, setStatementFile] = useState<File | null>(null);
  const [correctionFile, setCorrectionFile] = useState<File | null>(null);
  const [classes, setClasses] = useState<Classroom[]>([]);
  const [classId, setClassId] = useState("");
  const [baremeMode, setBaremeMode] = useState<"" | "auto" | "manuel">("");
  const [bareme, setBareme] = useState<BaremeItem[]>([
    { type: "qcm", answer_key: "", max_points: "1", order: 0 },
  ]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api<Classroom[]>("/classes")
      .then(setClasses)
      .catch(() => {});
  }, []);

  const addQuestion = () => {
    setBareme((b) => [
      ...b,
      { type: "qcm", answer_key: "", max_points: "1", order: b.length },
    ]);
  };

  const removeQuestion = (i: number) => {
    setBareme((b) => b.filter((_, j) => j !== i));
  };

  const updateBareme = (i: number, field: keyof BaremeItem, value: string | number) => {
    setBareme((b) => {
      const next = [...b];
      next[i] = { ...next[i], [field]: value };
      return next;
    });
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (!baremeMode) {
      setError("Choisissez comment definir le bareme en amont.");
      return;
    }
    if (!statementFile) {
      setError("L'enonce est obligatoire");
      return;
    }
    if (!correctionFile) {
      setError("Le corrige est obligatoire");
      return;
    }

    setLoading(true);
    try {
      const questions =
        baremeMode === "manuel"
          ? bareme.map((q, i) => ({
              type: q.type,
              prompt: `Question ${i + 1}`,
              answer_key: q.answer_key || null,
              max_points: parseFloat(q.max_points) || 1,
              order: i,
            }))
          : [];

      const formData = new FormData();
      formData.append("title", title || "Examen");
      formData.append("description", description);
      formData.append("manual_statement", manualStatement);
      formData.append("bareme", JSON.stringify(questions));
      formData.append("statement_file", statementFile);
      formData.append("correction_file", correctionFile);
      if (classId) {
        formData.append("class_id", classId);
      }

      const exam = await apiPostForm<Exam>("/exams/from-pdf", formData);
      router.push(`/dashboard/exams/${exam.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de la creation");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="animate-fade-in max-w-3xl">
      <h1 className="text-2xl font-bold text-ink-900 mb-2">Nouvel examen</h1>
      <p className="text-ink-500 mb-8">
        L'enonce PDF et le corrige PDF sont obligatoires pour permettre la correction automatique.
      </p>

      <form onSubmit={handleSubmit} className="space-y-8">
        {error && <div className="p-4 rounded-lg bg-red-50 text-red-700 text-sm">{error}</div>}

        <div className="bg-white rounded-xl border border-ink-200 p-6 space-y-5">
          <h2 className="font-semibold text-ink-900">Informations generales</h2>

          <div>
            <label className="block text-sm font-medium text-ink-700 mb-1.5">Titre</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-ink-200"
              placeholder="Ex: Controle de mathematiques"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ink-700 mb-1.5">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full px-4 py-3 rounded-lg border border-ink-200"
              placeholder="Instructions, duree, etc."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ink-700 mb-1.5">Classe (optionnel)</label>
            <select
              value={classId}
              onChange={(e) => setClassId(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-ink-200"
            >
              <option value="">Aucune classe</option>
              {classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-ink-700 mb-1.5">Enonce PDF (obligatoire)</label>
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => setStatementFile(e.target.files?.[0] || null)}
              className="w-full"
              required
            />
            {statementFile && (
              <p className="mt-2 text-sm text-ink-600 inline-flex items-center gap-2">
                <FileText className="w-4 h-4" />
                {statementFile.name}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-ink-700 mb-1.5">Corrige PDF (obligatoire)</label>
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => setCorrectionFile(e.target.files?.[0] || null)}
              className="w-full"
              required
            />
            {correctionFile && (
              <p className="mt-2 text-sm text-ink-600 inline-flex items-center gap-2">
                <FileText className="w-4 h-4" />
                {correctionFile.name}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-ink-700 mb-1.5">
              Saisie manuelle de l'enonce (optionnel)
            </label>
            <textarea
              value={manualStatement}
              onChange={(e) => setManualStatement(e.target.value)}
              rows={4}
              className="w-full px-4 py-3 rounded-lg border border-ink-200"
              placeholder="Copiez ici des instructions supplementaires"
            />
          </div>
    </div>

    <div className="bg-white rounded-xl border border-ink-200 p-6 space-y-6">
      <h2 className="font-semibold text-ink-900">Bareme</h2>
      <p className="text-sm text-ink-500">
        Choisissez le mode de bareme des le depart: detection automatique ou saisie manuelle.
      </p>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => setBaremeMode("auto")}
          className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium transition ${
            baremeMode === "auto"
              ? "border-brand-600 text-brand-700 bg-brand-50"
              : "border-ink-200 text-ink-700 hover:bg-ink-50"
          }`}
        >
          <Upload className="w-4 h-4" />
          Detection automatique
        </button>
        <button
          type="button"
          onClick={() => setBaremeMode("manuel")}
          className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium transition ${
            baremeMode === "manuel"
              ? "border-brand-600 text-brand-700 bg-brand-50"
              : "border-ink-200 text-ink-700 hover:bg-ink-50"
          }`}
        >
          <Plus className="w-4 h-4" />
          Saisie manuelle
        </button>
      </div>

      {baremeMode === "auto" && (
        <div className="p-4 rounded-lg border border-ink-200 bg-ink-50/60 text-sm text-ink-700">
          Le bareme sera deduit automatiquement a partir de l'enonce et du corrige. Vous pourrez le
          modifier en recreant l'examen si besoin.
        </div>
      )}

      {baremeMode === "manuel" && (
        <>
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-ink-900">Bareme manuel</h3>
            <button
              type="button"
              onClick={addQuestion}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium text-brand-600 hover:bg-brand-50 transition"
            >
              <Plus className="w-4 h-4" />
              Ajouter
            </button>
          </div>

          <p className="text-sm text-ink-500">
            Definissez vos questions et points. Si vous annulez ou supprimez tous les elements, le
            bareme automatique sera utilise.
          </p>

          {bareme.map((q, i) => (
            <div
              key={i}
              className="p-4 rounded-lg border border-ink-200 bg-ink-50/50 grid grid-cols-1 sm:grid-cols-12 gap-4 items-end"
            >
              <div className="sm:col-span-2 font-medium text-ink-700">Q{i + 1}</div>
              <div className="sm:col-span-3">
                <label className="block text-xs font-medium text-ink-500 mb-1">Type</label>
                <select
                  value={q.type}
                  onChange={(e) => updateBareme(i, "type", e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-ink-200 bg-white text-sm"
                >
                  <option value="qcm">QCM</option>
                  <option value="open">Ouverte</option>
                  <option value="code">Code</option>
                  <option value="qru">QRU</option>
                </select>
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-medium text-ink-500 mb-1">Points</label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  value={q.max_points}
                  onChange={(e) => updateBareme(i, "max_points", e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-ink-200 bg-white text-sm"
                />
              </div>
              <div className="sm:col-span-4">
                <label className="block text-xs font-medium text-ink-500 mb-1">Reponse attendue</label>
                <input
                  type="text"
                  value={q.answer_key}
                  onChange={(e) => updateBareme(i, "answer_key", e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-ink-200 bg-white text-sm"
                  placeholder="A, B, C... ou texte attendu"
                />
              </div>
              <div className="sm:col-span-1">
                {bareme.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeQuestion(i)}
                    className="p-2 rounded text-ink-400 hover:text-red-600 hover:bg-red-50 transition"
                    title="Supprimer"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </>
      )}
    </div>

        <div className="flex gap-4">
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2.5 rounded-lg bg-ink-900 text-white font-medium hover:bg-ink-800 disabled:opacity-50 transition inline-flex items-center gap-2"
          >
            <Upload className="w-4 h-4" />
            {loading ? "Creation..." : "Creer l'examen"}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="px-6 py-2.5 rounded-lg border border-ink-200 text-ink-700 font-medium hover:bg-ink-50 transition"
          >
            Annuler
          </button>
        </div>
      </form>
    </div>
  );
}
