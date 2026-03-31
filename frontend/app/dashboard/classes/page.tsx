"use client";

import { useEffect, useMemo, useState } from "react";
import { api, apiPostForm } from "@/lib/api";
import { Classroom, Student } from "@/lib/types";
import { Loader2, Plus, Trash2, Upload, Users } from "lucide-react";

export default function ClassesPage() {
  const [classes, setClasses] = useState<Classroom[]>([]);
  const [selectedClassId, setSelectedClassId] = useState("");
  const [students, setStudents] = useState<Student[]>([]);
  const [newClassName, setNewClassName] = useState("");
  const [newClassDesc, setNewClassDesc] = useState("");
  const [studentEmail, setStudentEmail] = useState("");
  const [studentName, setStudentName] = useState("");
  const [studentPassword, setStudentPassword] = useState("eleve123");
  const [rosterFile, setRosterFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deletingClass, setDeletingClass] = useState(false);
  const [removingStudentId, setRemovingStudentId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const selectedClass = useMemo(
    () => classes.find((c) => c.id === selectedClassId) || null,
    [classes, selectedClassId]
  );

  const loadClasses = async (resetSelection = false) => {
    const data = await api<Classroom[]>("/classes");
    setClasses(data);
    const firstId = data[0]?.id || "";

    const currentExists = selectedClassId && data.some((c) => c.id === selectedClassId);
    if (resetSelection || (!selectedClassId && firstId) || (selectedClassId && !currentExists)) {
      setSelectedClassId(firstId);
    }
  };

  const loadStudents = async (classId: string) => {
    if (!classId) {
      setStudents([]);
      return;
    }
    const data = await api<Student[]>(`/classes/${classId}/students`);
    setStudents(data);
  };

  useEffect(() => {
    loadClasses()
      .catch(() => setError("Impossible de charger les classes"))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!selectedClassId) return;
    loadStudents(selectedClassId).catch(() => setError("Impossible de charger les eleves"));
  }, [selectedClassId]);

  const createClassroom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newClassName.trim()) return;
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      await api<Classroom>("/classes", {
        method: "POST",
        body: JSON.stringify({ name: newClassName.trim(), description: newClassDesc || null }),
      });
      setNewClassName("");
      setNewClassDesc("");
      await loadClasses();
      setSuccess("Classe creee avec succes");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de la creation de la classe");
    } finally {
      setSaving(false);
    }
  };

  const addStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClassId || !studentEmail.trim()) return;
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      await api(`/classes/${selectedClassId}/students`, {
        method: "POST",
        body: JSON.stringify({
          email: studentEmail.trim(),
          full_name: studentName.trim() || null,
          password: studentPassword || null,
        }),
      });
      setStudentEmail("");
      setStudentName("");
      setStudentPassword("eleve123");
      await loadStudents(selectedClassId);
      setSuccess("Eleve ajoute a la classe");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de l'ajout de l'eleve");
    } finally {
      setSaving(false);
    }
  };

  const deleteClassroom = async () => {
    if (!selectedClassId) return;
    const label = selectedClass?.name || "cette classe";
    if (!window.confirm(`Supprimer ${label} ?`)) return;

    setDeletingClass(true);
    setError("");
    setSuccess("");
    try {
      await api(`/classes/${selectedClassId}`, { method: "DELETE" });
      setStudents([]);
      await loadClasses(true);
      setSuccess("Classe supprimee");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de la suppression de la classe");
    } finally {
      setDeletingClass(false);
    }
  };

  const importRoster = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClassId || !rosterFile) return;

    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const form = new FormData();
      form.append("file", rosterFile);
      await apiPostForm(`/classes/${selectedClassId}/roster`, form);
      setRosterFile(null);
      await loadStudents(selectedClassId);
      setSuccess("Roster importe avec succes");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de l'import CSV");
    } finally {
      setSaving(false);
    }
  };

  const removeStudent = async (student: Student) => {
    if (!selectedClassId) return;
    const label = student.full_name || student.email;
    if (!window.confirm(`Supprimer ${label} de cette classe ?`)) return;

    setRemovingStudentId(student.id);
    setError("");
    setSuccess("");
    try {
      await api(`/classes/${selectedClassId}/students/${student.id}`, { method: "DELETE" });
      await loadStudents(selectedClassId);
      setSuccess("Eleve retire de la classe");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de la suppression de l'eleve");
    } finally {
      setRemovingStudentId(null);
    }
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-10 bg-ink-200 rounded w-48" />
        <div className="h-40 bg-ink-100 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="animate-fade-in space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-ink-900">Classes et eleves</h1>
        <p className="text-ink-500 mt-1">Gerez votre repertoire de classes et de comptes eleves.</p>
      </div>

      {error && <div className="p-4 rounded-lg bg-red-50 text-red-700 text-sm">{error}</div>}
      {success && <div className="p-4 rounded-lg bg-emerald-50 text-emerald-700 text-sm">{success}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-ink-200 p-6">
          <h2 className="font-semibold text-ink-900 mb-4">Creer une classe</h2>
          <form onSubmit={createClassroom} className="space-y-3">
            <input
              value={newClassName}
              onChange={(e) => setNewClassName(e.target.value)}
              placeholder="Ex: 2A Informatique"
              className="w-full px-4 py-2.5 rounded-lg border border-ink-200"
              required
            />
            <textarea
              value={newClassDesc}
              onChange={(e) => setNewClassDesc(e.target.value)}
              placeholder="Description (optionnel)"
              className="w-full px-4 py-2.5 rounded-lg border border-ink-200"
              rows={2}
            />
            <button
              type="submit"
              disabled={saving}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-ink-900 text-white text-sm font-medium disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Ajouter la classe
            </button>
          </form>

          <div className="mt-6">
            <label className="block text-sm text-ink-600 mb-2">Classe selectionnee</label>
            <select
              value={selectedClassId}
              onChange={(e) => setSelectedClassId(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg border border-ink-200"
            >
              <option value="">Selectionner</option>
              {classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <div className="flex gap-3 mt-3">
              <button
                type="button"
                onClick={deleteClassroom}
                disabled={!selectedClassId || deletingClass}
                className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-red-200 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50"
              >
                {deletingClass ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                Supprimer la classe
              </button>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-ink-200 p-6">
          <h2 className="font-semibold text-ink-900 mb-4">Ajouter un eleve</h2>
          <form onSubmit={addStudent} className="space-y-3">
            <input
              type="email"
              value={studentEmail}
              onChange={(e) => setStudentEmail(e.target.value)}
              placeholder="email@exemple.com"
              className="w-full px-4 py-2.5 rounded-lg border border-ink-200"
              required
            />
            <input
              value={studentName}
              onChange={(e) => setStudentName(e.target.value)}
              placeholder="Nom complet (optionnel)"
              className="w-full px-4 py-2.5 rounded-lg border border-ink-200"
            />
            <input
              value={studentPassword}
              onChange={(e) => setStudentPassword(e.target.value)}
              placeholder="Mot de passe initial"
              className="w-full px-4 py-2.5 rounded-lg border border-ink-200"
            />
            <button
              type="submit"
              disabled={saving || !selectedClassId}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Users className="w-4 h-4" />}
              Ajouter l'eleve
            </button>
          </form>

          <form onSubmit={importRoster} className="mt-6 space-y-3">
            <p className="text-sm text-ink-600">Import CSV (colonnes: email,full_name,password)</p>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setRosterFile(e.target.files?.[0] || null)}
              className="w-full text-sm"
            />
            <button
              type="submit"
              disabled={saving || !selectedClassId || !rosterFile}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-ink-300 text-ink-700 text-sm font-medium disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
              Importer CSV
            </button>
          </form>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-ink-200 p-6">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="font-semibold text-ink-900">
            Eleves de {selectedClass?.name || "la classe"}
          </h2>
          <span className="rounded-full bg-ink-100 px-3 py-1 text-xs font-medium text-ink-700">
            {students.length} eleve(s)
          </span>
        </div>
        {students.length === 0 ? (
          <p className="text-ink-500 text-sm">Aucun eleve pour le moment.</p>
        ) : (
          <ul className="space-y-2">
            {students.map((student) => (
              <li
                key={student.id}
                className="flex items-center justify-between gap-3 rounded-lg bg-ink-50 px-3 py-2"
              >
                <div className="min-w-0">
                  <p className="text-sm text-ink-800">{student.full_name || student.email}</p>
                  <p className="text-xs text-ink-500 truncate">{student.email}</p>
                </div>
                <button
                  type="button"
                  onClick={() => removeStudent(student)}
                  disabled={removingStudentId === student.id}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 px-2.5 py-1.5 text-xs font-medium text-red-700 hover:bg-red-50 disabled:opacity-50"
                >
                  {removingStudentId === student.id ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Trash2 className="h-3.5 w-3.5" />
                  )}
                  Retirer
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
