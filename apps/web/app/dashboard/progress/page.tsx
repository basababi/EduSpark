"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Trophy, BookOpenCheck, Clock3, Target } from "lucide-react";
import type { ProgressSnapshotResponse, ProgressSummaryResponse } from "@/lib/api-types";
import { getProgressSnapshots, getProgressSummary } from "@/lib/api-client";
import { handlePageApiError, requireAuthOrRedirect } from "@/lib/page-auth";
import { ApiErrorPanel } from "@/components/ui/ApiErrorPanel";
import { Skeleton } from "@/components/ui/Skeleton";
import { Toast, type ToastState } from "@/components/ui/Toast";

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`rounded-2xl border border-neutral-200 bg-white shadow-sm ${className}`}>{children}</div>;
}

function ProgressBar({ value, colorClass }: { value: number; colorClass: string }) {
  return (
    <div className="h-2.5 w-full rounded-full bg-neutral-100 overflow-hidden">
      <div className={`h-full rounded-full transition-all ${colorClass}`} style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  );
}

function prettyDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("mn-MN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }).format(date);
}

export default function ProgressPage() {
  const router = useRouter();
  const [summary, setSummary] = useState<ProgressSummaryResponse | null>(null);
  const [snapshots, setSnapshots] = useState<ProgressSnapshotResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastState>(null);

  const load = useCallback(async () => {
    if (!requireAuthOrRedirect(router)) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const [summaryData, snapshotData] = await Promise.all([
        getProgressSummary(7),
        getProgressSnapshots(5),
      ]);
      setSummary(summaryData);
      setSnapshots(snapshotData);
    } catch (err) {
      const message = handlePageApiError(err, router);
      setError(message);
      setToast({ variant: "error", message });
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    void load();
  }, [load]);

  const strongest = useMemo(() => {
    if (!summary || summary.subject_progress.length === 0) {
      return null;
    }
    return [...summary.subject_progress].sort((a, b) => b.progress_percent - a.progress_percent)[0];
  }, [summary]);

  const weakest = useMemo(() => {
    if (!summary || summary.subject_progress.length === 0) {
      return null;
    }
    return [...summary.subject_progress].sort((a, b) => a.progress_percent - b.progress_percent)[0];
  }, [summary]);

  return (
    <div className="min-h-screen bg-muted px-4 py-6">
      <Toast toast={toast} onClose={() => setToast(null)} />
      <div className="mx-auto max-w-5xl space-y-4">
        <Card className="p-5 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">Ахиц</h1>
            <p className="mt-1 text-sm text-neutral-600">7 хоногийн суралцах өгөгдөл болон сэдвийн гүйцэтгэл</p>
          </div>
          <button
            onClick={() => void load()}
            className="rounded-lg border border-neutral-300 px-3 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-50"
          >
            Шинэчлэх
          </button>
        </Card>

        {loading && (
          <>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {[0, 1, 2].map((item) => (
                <Card key={item} className="p-5">
                  <Skeleton className="h-4 w-28" />
                  <Skeleton className="h-8 w-24 mt-3" />
                </Card>
              ))}
            </div>
            <Card className="p-5">
              <Skeleton className="h-5 w-48" />
              <Skeleton className="h-3 w-full mt-4" />
              <Skeleton className="h-4 w-64 mt-3" />
            </Card>
            <Card className="p-5">
              <Skeleton className="h-5 w-32" />
              {[0, 1, 2].map((item) => (
                <div key={item} className="mt-4">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-2.5 w-full mt-2" />
                </div>
              ))}
            </Card>
          </>
        )}

        {!loading && error && <ApiErrorPanel message={error} onRetry={() => void load()} />}

        {!loading && !error && summary && (
          <>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <Card className="p-5">
                <div className="flex items-center gap-3 text-neutral-500 text-sm">
                  <Clock3 size={16} />
                  <span>Сүүлийн 7 хоног</span>
                </div>
                <p className="mt-2 text-3xl font-bold text-neutral-900">{summary.weekly_hours.toFixed(1)} цаг</p>
              </Card>

              <Card className="p-5">
                <div className="flex items-center gap-3 text-neutral-500 text-sm">
                  <Trophy size={16} />
                  <span>Дундаж оноо</span>
                </div>
                <p className="mt-2 text-3xl font-bold text-neutral-900">{summary.average_quiz_score.toFixed(1)}%</p>
              </Card>

              <Card className="p-5">
                <div className="flex items-center gap-3 text-neutral-500 text-sm">
                  <BookOpenCheck size={16} />
                  <span>Дуусгасан хичээл</span>
                </div>
                <p className="mt-2 text-3xl font-bold text-neutral-900">{summary.completed_lessons}</p>
              </Card>
            </div>

            <Card className="p-5">
              <div className="flex items-center justify-between gap-3 mb-3">
                <h2 className="text-lg font-semibold text-neutral-900">Долоо хоногийн зорилго</h2>
                <span className="text-sm font-semibold text-primary">{summary.weekly_goal_percent.toFixed(1)}%</span>
              </div>
              <ProgressBar value={summary.weekly_goal_percent} colorClass="bg-primary" />
              <p className="mt-3 text-sm text-neutral-600">
                {summary.weekly_hours.toFixed(1)} / {(summary.weekly_goal_minutes / 60).toFixed(1)} цаг биелсэн байна.
              </p>
            </Card>

            <Card className="p-5">
              <h2 className="text-lg font-semibold text-neutral-900 mb-4">Сэдвийн ахиц</h2>
              <div className="space-y-4">
                {summary.subject_progress.length === 0 && (
                  <p className="text-sm text-neutral-500">Одоогоор сэдвийн ахицын өгөгдөл алга байна.</p>
                )}
                {summary.subject_progress.map((subject) => (
                  <div key={subject.subject_id}>
                    <div className="mb-2 flex items-center justify-between text-sm">
                      <div className="font-medium text-neutral-800">{subject.subject_name}</div>
                      <div className="text-neutral-600">{subject.progress_percent.toFixed(1)}%</div>
                    </div>
                    <ProgressBar value={subject.progress_percent} colorClass="bg-emerald-500" />
                    <div className="mt-1 text-xs text-neutral-500">
                      Тест: {subject.completed_quizzes} | Цаг: {(subject.study_minutes / 60).toFixed(1)}
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <Card className="p-5">
                <div className="flex items-center gap-2 text-neutral-800 font-semibold mb-2">
                  <Target size={16} />
                  Шилдэг сэдэв
                </div>
                {strongest ? (
                  <p className="text-sm text-neutral-700">
                    {strongest.subject_name} - {strongest.progress_percent.toFixed(1)}%
                  </p>
                ) : (
                  <p className="text-sm text-neutral-500">Өгөгдөл алга</p>
                )}
              </Card>

              <Card className="p-5">
                <div className="flex items-center gap-2 text-neutral-800 font-semibold mb-2">
                  <Target size={16} />
                  Анхаарах сэдэв
                </div>
                {weakest ? (
                  <p className="text-sm text-neutral-700">
                    {weakest.subject_name} - {weakest.progress_percent.toFixed(1)}%
                  </p>
                ) : (
                  <p className="text-sm text-neutral-500">Өгөгдөл алга</p>
                )}
              </Card>
            </div>

            <Card className="p-5">
              <h2 className="text-lg font-semibold text-neutral-900 mb-3">Сүүлийн snapshot-ууд</h2>
              {snapshots.length === 0 ? (
                <p className="text-sm text-neutral-500">Snapshot бүртгэл олдсонгүй.</p>
              ) : (
                <div className="space-y-2">
                  {snapshots.map((snapshot) => (
                    <div key={snapshot.id} className="rounded-lg border border-neutral-200 px-3 py-2 text-sm text-neutral-700">
                      <div className="font-medium">{prettyDate(snapshot.captured_at)}</div>
                      <div className="text-xs text-neutral-500 mt-1">{JSON.stringify(snapshot.metric)}</div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
