"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { ClassScoreItem } from "@/lib/types";
import { Award } from "lucide-react";

export default function ScoresListPage() {
  const [scores, setScores] = useState<ClassScoreItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<ClassScoreItem[]>("/me/scores")
      .then(setScores)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const grouped = scores.reduce<Record<string, { label: string; items: ClassScoreItem[] }>>((acc, item) => {
    const key = item.class_id || "__no_class__";
    const label = item.class_name || "Sans classe";
    if (!acc[key]) {
      acc[key] = { label, items: [] };
    }
    acc[key].items.push(item);
    return acc;
  }, {});

  const groups = Object.entries(grouped).sort(([, a], [, b]) => a.label.localeCompare(b.label));

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-10 bg-ink-200 rounded w-48" />
        <div className="h-64 bg-ink-100 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <h1 className="text-2xl font-bold text-ink-900 mb-2">Scores</h1>
      <p className="text-ink-500 mb-8">Notes detaillees, separees par classe</p>

      {scores.length === 0 ? (
        <div className="bg-white rounded-xl border border-ink-200 p-16 text-center text-ink-500">
          <Award className="w-16 h-16 mx-auto mb-6 text-ink-300" />
          <p className="text-lg font-medium text-ink-700">Aucun score disponible</p>
        </div>
      ) : (
        <div className="space-y-6">
          {groups.map(([groupKey, group]) => (
            <div key={groupKey} className="bg-white rounded-xl border border-ink-200 overflow-hidden">
              <div className="border-b border-ink-200 bg-ink-50 px-6 py-4">
                <h2 className="font-semibold text-ink-900">{group.label}</h2>
                <p className="text-xs text-ink-500 mt-0.5">{group.items.length} copie(s) corrigee(s)</p>
              </div>
              <table className="w-full">
                <thead>
                  <tr className="text-left text-sm text-ink-600">
                    <th className="px-6 py-3 font-medium">N</th>
                    <th className="px-6 py-3 font-medium">Examen</th>
                    <th className="px-6 py-3 font-medium">Eleve</th>
                    <th className="px-6 py-3 font-medium">Total</th>
                    <th className="px-6 py-3 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-100">
                  {group.items.map((s, i) => (
                    <tr key={s.submission_id} className="hover:bg-ink-50/50">
                      <td className="px-6 py-4 text-sm font-medium text-ink-700">{i + 1}</td>
                      <td className="px-6 py-4 text-ink-700">{s.exam_title}</td>
                      <td className="px-6 py-4 text-ink-600">{s.student_email || "-"}</td>
                      <td className="px-6 py-4 font-medium text-brand-700">{s.total.toFixed(1)} /20</td>
                      <td className="px-6 py-4">
                        <Link
                          href={`/dashboard/scores/${s.submission_id}`}
                          className="text-brand-600 text-sm font-medium hover:text-brand-700"
                        >
                          Voir le detail &rarr;
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
