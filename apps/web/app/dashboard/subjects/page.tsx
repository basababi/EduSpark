"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronDown } from "lucide-react";
import type { SubjectDetailResponse, SubjectSummaryResponse } from "@/lib/api-types";
import { getSubjectDetail, getSubjects } from "@/lib/api-client";
import { handlePageApiError, requireAuthOrRedirect } from "@/lib/page-auth";
import { ApiErrorPanel } from "@/components/ui/ApiErrorPanel";
import { Skeleton } from "@/components/ui/Skeleton";
import { Toast, type ToastState } from "@/components/ui/Toast";

type Level = "Анхан" | "Дунд" | "Ахисан";

type SubjectView = {
  id: string;
  title: string;
  description: string;
  topics: number;
  modules: number;
  lessons: number;
  progress: number;
  level: Level;
  focus: string[];
};

const LEVELS: Level[] = ["Анхан", "Дунд", "Ахисан"];

const levelStyles: Record<Level, { badge: string; border: string; accent: string }> = {
  Анхан: {
    badge: "bg-amber-50 text-amber-700 border border-amber-200",
    border: "border-amber-200",
    accent: "bg-amber-500",
  },
  Дунд: {
    badge: "bg-violet-50 text-violet-700 border border-violet-200",
    border: "border-violet-200",
    accent: "bg-violet-500",
  },
  Ахисан: {
    badge: "bg-emerald-50 text-emerald-700 border border-emerald-200",
    border: "border-emerald-200",
    accent: "bg-emerald-500",
  },
};

function mapLevel(value: string | null): Level {
  const lower = (value ?? "").toLowerCase();
  if (lower.includes("adv") || lower.includes("ахис")) {
    return "Ахисан";
  }
  if (lower.includes("inter") || lower.includes("дунд")) {
    return "Дунд";
  }
  return "Анхан";
}

function extractFocus(detail: SubjectDetailResponse | undefined): string[] {
  if (!detail) {
    return [];
  }
  const topics: string[] = [];
  for (const module of detail.modules) {
    for (const topic of module.topics) {
      topics.push(topic.title);
      if (topics.length === 3) {
        return topics;
      }
    }
  }
  return topics;
}

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`rounded-2xl border border-neutral-200 bg-white shadow-sm ${className}`}>{children}</div>;
}

function ProgressBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="h-2.5 w-full rounded-full bg-neutral-100 overflow-hidden">
      <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  );
}

function SubjectCard({ item }: { item: SubjectView }) {
  const style = levelStyles[item.level];

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-neutral-900">{item.title}</h3>
          <p className="mt-1 text-sm text-neutral-500">{item.description || "Тайлбар оруулаагүй"}</p>
        </div>
        <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${style.badge}`}>{item.level}</span>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2 text-center">
        <div className="rounded-lg border border-neutral-200 px-2 py-2">
          <div className="text-xs text-neutral-500">Module</div>
          <div className="font-semibold text-neutral-900">{item.modules}</div>
        </div>
        <div className="rounded-lg border border-neutral-200 px-2 py-2">
          <div className="text-xs text-neutral-500">Topic</div>
          <div className="font-semibold text-neutral-900">{item.topics}</div>
        </div>
        <div className="rounded-lg border border-neutral-200 px-2 py-2">
          <div className="text-xs text-neutral-500">Lesson</div>
          <div className="font-semibold text-neutral-900">{item.lessons}</div>
        </div>
      </div>

      <div className="mt-4">
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className="text-neutral-500">Ахиц</span>
          <span className="font-semibold text-neutral-800">{item.progress.toFixed(1)}%</span>
        </div>
        <ProgressBar value={item.progress} color={style.accent} />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {item.focus.length === 0 && (
          <span className="text-xs text-neutral-400">Одоогоор topic жагсаалт алга</span>
        )}
        {item.focus.map((topic) => (
          <span key={`${item.id}-${topic}`} className="rounded-full border border-neutral-200 bg-neutral-50 px-2.5 py-1 text-xs text-neutral-600">
            {topic}
          </span>
        ))}
      </div>
    </Card>
  );
}

function LevelSection({
  level,
  items,
}: {
  level: Level;
  items: SubjectView[];
}) {
  const [open, setOpen] = useState(true);
  const style = levelStyles[level];

  return (
    <Card className={`overflow-hidden ${style.border}`}>
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="w-full px-4 py-3 flex items-center justify-between text-left bg-white hover:bg-neutral-50"
      >
        <div className="flex items-center gap-3">
          <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${style.badge}`}>{level}</span>
          <span className="text-sm text-neutral-700">{items.length} хичээл</span>
        </div>
        <ChevronDown size={16} className={`text-neutral-500 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="border-t border-neutral-100 p-4 grid grid-cols-1 gap-4 md:grid-cols-2">
          {items.map((item) => (
            <SubjectCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </Card>
  );
}

export default function SubjectsPage() {
  const router = useRouter();
  const [subjects, setSubjects] = useState<SubjectView[]>([]);
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
      const rows = await getSubjects();
      const detailEntries = await Promise.all(
        rows.map(async (subject) => {
          try {
            const detail = await getSubjectDetail(subject.id);
            return [subject.id, detail] as const;
          } catch {
            return [subject.id, undefined] as const;
          }
        }),
      );
      const details = new Map<string, SubjectDetailResponse | undefined>(detailEntries);

      const normalized: SubjectView[] = rows.map((subject: SubjectSummaryResponse) => {
        const detail = details.get(subject.id);
        return {
          id: subject.id,
          title: subject.name,
          description: subject.description ?? "",
          topics: subject.topics_count,
          modules: subject.modules_count,
          lessons: subject.lessons_count,
          progress: subject.progress_percent,
          level: mapLevel(subject.difficulty_level),
          focus: extractFocus(detail),
        };
      });

      setSubjects(normalized);
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

  const grouped = useMemo(() => {
    return Object.fromEntries(LEVELS.map((lvl) => [lvl, subjects.filter((item) => item.level === lvl)])) as Record<Level, SubjectView[]>;
  }, [subjects]);

  const avgProgress = useMemo(() => {
    if (subjects.length === 0) {
      return 0;
    }
    return subjects.reduce((sum, item) => sum + item.progress, 0) / subjects.length;
  }, [subjects]);

  return (
    <div className="min-h-screen bg-muted px-4 py-6">
      <Toast toast={toast} onClose={() => setToast(null)} />
      <div className="mx-auto max-w-5xl space-y-4">
        <Card className="p-5 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">Хичээлүүд</h1>
            <p className="mt-1 text-sm text-neutral-600">Backend-аас татсан сэдэв, модуль, ахицын мэдээлэл</p>
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
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-8 w-20 mt-3" />
                </Card>
              ))}
            </div>
            <Card className="p-4">
              <Skeleton className="h-5 w-40" />
              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                {[0, 1, 2, 3].map((item) => (
                  <div key={item} className="rounded-xl border border-neutral-200 p-4">
                    <Skeleton className="h-5 w-36" />
                    <Skeleton className="h-4 w-3/4 mt-2" />
                    <Skeleton className="h-3 w-full mt-4" />
                  </div>
                ))}
              </div>
            </Card>
          </>
        )}

        {!loading && error && <ApiErrorPanel message={error} onRetry={() => void load()} />}

        {!loading && !error && (
          <>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <Card className="p-5">
                <div className="text-xs text-neutral-500">Нийт хичээл</div>
                <div className="mt-2 text-3xl font-bold text-neutral-900">{subjects.length}</div>
              </Card>
              <Card className="p-5">
                <div className="text-xs text-neutral-500">Нийт сэдэв</div>
                <div className="mt-2 text-3xl font-bold text-neutral-900">{subjects.reduce((sum, s) => sum + s.topics, 0)}</div>
              </Card>
              <Card className="p-5">
                <div className="text-xs text-neutral-500">Дундаж ахиц</div>
                <div className="mt-2 text-3xl font-bold text-neutral-900">{avgProgress.toFixed(1)}%</div>
              </Card>
            </div>

            <div className="space-y-3">
              {LEVELS.filter((level) => grouped[level].length > 0).length === 0 ? (
                <Card className="p-6 text-center text-sm text-neutral-500">Одоогоор харуулах хичээл алга байна.</Card>
              ) : (
                LEVELS.filter((level) => grouped[level].length > 0).map((level) => (
                  <LevelSection key={level} level={level} items={grouped[level]} />
                ))
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
