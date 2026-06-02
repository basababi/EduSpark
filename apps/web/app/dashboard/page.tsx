"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { AuthMeResponse, ProgressSummaryResponse } from "@/lib/api-types";
import { getMe, getProgressSummary } from "@/lib/api-client";
import { handlePageApiError, requireAuthOrRedirect } from "@/lib/page-auth";
import { StatCards } from "@/components/DashboardCards";
import { Strengths, TrendsCard, WeeklyChart } from "@/components/DashboardCharts";
import { ApiErrorPanel } from "@/components/ui/ApiErrorPanel";
import { Skeleton } from "@/components/ui/Skeleton";
import { Toast, type ToastState } from "@/components/ui/Toast";

const DAY_LABEL_FORMATTER = new Intl.DateTimeFormat("mn-MN", { weekday: "short" });

function formatWeekday(dateString: string): string {
  const date = new Date(`${dateString}T00:00:00`);
  if (Number.isNaN(date.getTime())) {
    return dateString;
  }
  return DAY_LABEL_FORMATTER.format(date);
}

export default function DashboardPage() {
  const router = useRouter();
  const [me, setMe] = useState<AuthMeResponse | null>(null);
  const [summary, setSummary] = useState<ProgressSummaryResponse | null>(null);
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
      const [currentUser, progress] = await Promise.all([getMe(), getProgressSummary(7)]);
      setMe(currentUser);
      setSummary(progress);
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

  const chartData = useMemo(() => {
    if (!summary) {
      return [];
    }
    const dayCount = summary.weekly_trend.length || 7;
    const dailyGoalHours = dayCount > 0 ? summary.weekly_goal_minutes / dayCount / 60 : 0;
    return summary.weekly_trend.map((point) => ({
      day: formatWeekday(point.date),
      studied: Number((point.minutes / 60).toFixed(2)),
      goal: Number(dailyGoalHours.toFixed(2)),
    }));
  }, [summary]);

  const statItems = useMemo(() => {
    if (!summary) {
      return [];
    }
    return [
      {
        key: "weekly-hours",
        icon: "time" as const,
        label: "Энэ долоо хоног",
        value: `${summary.weekly_hours.toFixed(1)} цаг`,
      },
      {
        key: "goal",
        icon: "streak" as const,
        label: "Зорилго биелэлт",
        value: `${summary.weekly_goal_percent.toFixed(1)}%`,
      },
      {
        key: "lessons",
        icon: "lessons" as const,
        label: "Дуусгасан хичээл",
        value: String(summary.completed_lessons),
      },
      {
        key: "score",
        icon: "score" as const,
        label: "Дундаж оноо",
        value: `${summary.average_quiz_score.toFixed(1)}%`,
      },
    ];
  }, [summary]);

  const strengths = useMemo(() => {
    if (!summary) {
      return [];
    }
    return [...summary.subject_progress]
      .map((subject) => ({
        name: subject.subject_name,
        value: subject.average_quiz_score ?? subject.progress_percent,
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 3);
  }, [summary]);

  return (
    <div className="min-h-screen bg-muted">
      <Toast toast={toast} onClose={() => setToast(null)} />
      <div className="max-w-5xl mx-auto px-4 py-6 space-y-4">
        <div className="card p-5 flex justify-between items-start gap-4">
          <div>
            <h1 className="text-2xl font-bold">
              {me ? `Сайн байна уу, ${me.full_name ?? me.email}!` : "Сайн байна уу!"}
            </h1>
            <p className="text-slate-600 mt-1">Өнөөдөр юу сурахаа төлөвлөхөд бэлэн үү?</p>
          </div>
          {summary && (
            <div className="text-sm text-slate-500">
              Зорилго биелэлт:{" "}
              <span className="text-primary font-semibold">{summary.weekly_goal_percent.toFixed(1)}%</span>
            </div>
          )}
        </div>

        {loading && (
          <>
            <div className="card p-5">
              <Skeleton className="h-6 w-64" />
              <Skeleton className="h-4 w-80 mt-2" />
            </div>
            <div className="grid md:grid-cols-4 gap-4">
              {[0, 1, 2, 3].map((item) => (
                <div key={item} className="card p-4">
                  <Skeleton className="h-10 w-10 rounded-xl" />
                  <Skeleton className="h-4 w-20 mt-3" />
                  <Skeleton className="h-6 w-24 mt-2" />
                </div>
              ))}
            </div>
            <div className="grid lg:grid-cols-3 gap-4">
              <div className="card p-5 lg:col-span-2">
                <Skeleton className="h-5 w-48" />
                <Skeleton className="h-64 w-full mt-4" />
              </div>
              <div className="card p-5">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-4 w-full mt-4" />
                <Skeleton className="h-4 w-full mt-3" />
                <Skeleton className="h-4 w-2/3 mt-3" />
              </div>
            </div>
          </>
        )}

        {!loading && error && (
          <ApiErrorPanel message={error} onRetry={() => void load()} />
        )}

        {!loading && !error && summary && (
          <>
            <StatCards items={statItems} />

            <div className="grid lg:grid-cols-3 gap-4">
              <div className="lg:col-span-2">
                <WeeklyChart
                  data={chartData}
                  totalHours={summary.weekly_hours}
                  weeklyGoalHours={summary.weekly_goal_minutes / 60}
                  weeklyGoalPercent={summary.weekly_goal_percent}
                />
              </div>
              <Strengths items={strengths} />
            </div>

            <div className="grid lg:grid-cols-3 gap-4">
              <div className="lg:col-span-3">
                <TrendsCard data={chartData} />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
