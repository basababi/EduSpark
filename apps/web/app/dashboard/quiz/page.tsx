"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowUpDown,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  History,
  LayoutList,
  PlayCircle,
  RotateCcw,
  Send,
  Target,
  XCircle,
} from "lucide-react";
import type {
  QuizAttemptHistoryItemResponse,
  QuizAttemptSubmitResponse,
  QuizDetailResponse,
  QuizListItemResponse,
} from "@/lib/api-types";
import { getQuizDetail, getQuizHistory, getQuizzes, submitQuizAttempt } from "@/lib/api-client";
import { handlePageApiError, requireAuthOrRedirect } from "@/lib/page-auth";
import { ApiErrorPanel } from "@/components/ui/ApiErrorPanel";
import { Skeleton } from "@/components/ui/Skeleton";
import { Toast, type ToastState } from "@/components/ui/Toast";

type SortKey = "level" | "questions" | "recent";

const SORT_OPTIONS: Array<{ key: SortKey; label: string }> = [
  { key: "level", label: "Түвшин" },
  { key: "questions", label: "Асуултын тоо" },
  { key: "recent", label: "Сүүлийн оролдлого" },
];

type AnswerResultItem = QuizAttemptSubmitResponse["answers"][number];

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`rounded-2xl border border-neutral-200 bg-white shadow-sm ${className}`}>{children}</div>;
}

function ProgressBar({ value }: { value: number }) {
  return (
    <div className="h-2.5 w-full rounded-full bg-neutral-100 overflow-hidden">
      <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  );
}

function normalizeLevel(value: string | null): number {
  const lower = (value ?? "").toLowerCase();
  if (lower.includes("adv") || lower.includes("ахис")) {
    return 3;
  }
  if (lower.includes("inter") || lower.includes("дунд")) {
    return 2;
  }
  return 1;
}

function levelLabel(value: string | null): string {
  const rank = normalizeLevel(value);
  if (rank === 3) {
    return "Ахисан";
  }
  if (rank === 2) {
    return "Дунд";
  }
  return "Анхан";
}

function formatDate(value: string | null): string {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("mn-MN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function getScoreTone(score: number): {
  number: string;
  badge: string;
  text: string;
} {
  if (score >= 85) {
    return {
      number: "text-emerald-700",
      badge: "border-emerald-300 bg-emerald-50 text-emerald-700",
      text: "Онц",
    };
  }
  if (score >= 60) {
    return {
      number: "text-amber-700",
      badge: "border-amber-300 bg-amber-50 text-amber-700",
      text: "Сайн",
    };
  }
  return {
    number: "text-red-700",
    badge: "border-red-300 bg-red-50 text-red-700",
    text: "Сайжруулах шаардлагатай",
  };
}

export default function QuizPage() {
  const router = useRouter();
  const [quizzes, setQuizzes] = useState<QuizListItemResponse[]>([]);
  const [history, setHistory] = useState<QuizAttemptHistoryItemResponse[]>([]);
  const [activeQuiz, setActiveQuiz] = useState<QuizDetailResponse | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<QuizAttemptSubmitResponse | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  const [loading, setLoading] = useState(true);
  const [loadingQuizId, setLoadingQuizId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastState>(null);
  const [filter, setFilter] = useState("all");
  const [sortIndex, setSortIndex] = useState(0);

  const currentSort = SORT_OPTIONS[sortIndex % SORT_OPTIONS.length];

  const load = useCallback(async () => {
    if (!requireAuthOrRedirect(router)) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const [quizRows, historyRows] = await Promise.all([getQuizzes(), getQuizHistory(10)]);
      setQuizzes(quizRows);
      setHistory(historyRows);
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

  const subjectOptions = useMemo(() => {
    const values = quizzes
      .map((quiz) => quiz.subject_name)
      .filter((name): name is string => Boolean(name));
    return [...new Set(values)];
  }, [quizzes]);

  const filteredQuizzes = useMemo(() => {
    const rows = filter === "all" ? quizzes : quizzes.filter((quiz) => (quiz.subject_name ?? "") === filter);

    const sorted = [...rows].sort((a, b) => {
      if (currentSort.key === "level") {
        return normalizeLevel(b.level) - normalizeLevel(a.level);
      }
      if (currentSort.key === "questions") {
        return b.question_count - a.question_count;
      }

      const aTime = a.last_attempt_at ? new Date(a.last_attempt_at).getTime() : 0;
      const bTime = b.last_attempt_at ? new Date(b.last_attempt_at).getTime() : 0;
      return bTime - aTime;
    });

    return sorted;
  }, [quizzes, filter, currentSort.key]);

  const openQuiz = useCallback(
    async (quizId: string) => {
      setLoadingQuizId(quizId);
      setError(null);
      try {
        const detail = await getQuizDetail(quizId);
        setActiveQuiz(detail);
        setResult(null);
        setAnswers({});
        setCurrentQuestionIndex(0);
        setToast({ variant: "info", message: "Тестийн асуултууд ачааллаа." });
      } catch (err) {
        const message = handlePageApiError(err, router);
        setError(message);
        setToast({ variant: "error", message });
      } finally {
        setLoadingQuizId(null);
      }
    },
    [router],
  );

  const submit = useCallback(async () => {
    if (!activeQuiz || result) {
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        answers: activeQuiz.questions
          .filter((question) => answers[question.id])
          .map((question) => ({
            question_id: question.id,
            selected_answer: answers[question.id],
          })),
      };

      const submitResult = await submitQuizAttempt(activeQuiz.id, payload);
      setResult(submitResult);
      setCurrentQuestionIndex(0);
      setToast({ variant: "success", message: "Тест амжилттай илгээгдлээ." });
      await load();
    } catch (err) {
      const message = handlePageApiError(err, router);
      setError(message);
      setToast({ variant: "error", message });
    } finally {
      setSubmitting(false);
    }
  }, [activeQuiz, answers, result, load, router]);

  const retryQuiz = useCallback(() => {
    setResult(null);
    setAnswers({});
    setCurrentQuestionIndex(0);
    setToast({ variant: "info", message: "Тестийг дахин эхлүүллээ." });
  }, []);

  const answeredCount = activeQuiz
    ? activeQuiz.questions.filter((question) => Boolean(answers[question.id])).length
    : 0;
  const totalCount = activeQuiz?.questions.length ?? 0;
  const unansweredCount = totalCount - answeredCount;

  const answerResultMap = useMemo(() => {
    const map = new Map<string, AnswerResultItem>();
    if (result) {
      result.answers.forEach((item) => map.set(item.question_id, item));
    }
    return map;
  }, [result]);

  const questionTextMap = useMemo(() => {
    const map = new Map<string, string>();
    if (activeQuiz) {
      activeQuiz.questions.forEach((question) => {
        map.set(question.id, question.question_text);
      });
    }
    return map;
  }, [activeQuiz]);

  const questionIndexById = useMemo(() => {
    const map = new Map<string, number>();
    if (activeQuiz) {
      activeQuiz.questions.forEach((question, index) => {
        map.set(question.id, index);
      });
    }
    return map;
  }, [activeQuiz]);

  const currentQuestion = activeQuiz?.questions[currentQuestionIndex] ?? null;

  const goToQuestion = useCallback(
    (index: number) => {
      if (!activeQuiz) {
        return;
      }
      const next = Math.min(Math.max(index, 0), activeQuiz.questions.length - 1);
      setCurrentQuestionIndex(next);
    },
    [activeQuiz],
  );

  const jumpToNextUnanswered = useCallback(() => {
    if (!activeQuiz) {
      return;
    }
    const idx = activeQuiz.questions.findIndex((question) => !answers[question.id]);
    if (idx >= 0) {
      setCurrentQuestionIndex(idx);
    }
  }, [activeQuiz, answers]);

  const getChoiceClass = useCallback(
    (questionId: string, choiceKey: string): string => {
      const selected = answers[questionId];
      if (!result) {
        return selected === choiceKey
          ? "border-primary bg-primary/10 text-primary"
          : "border-neutral-200 bg-white text-neutral-700 hover:bg-neutral-50";
      }

      const answer = answerResultMap.get(questionId);
      const correct = answer?.correct_answer;
      const submitted = answer?.selected_answer ?? null;

      if (choiceKey === correct) {
        return "border-emerald-300 bg-emerald-50 text-emerald-800";
      }
      if (submitted === choiceKey && submitted !== correct) {
        return "border-red-300 bg-red-50 text-red-800";
      }
      return "border-neutral-200 bg-neutral-50 text-neutral-500";
    },
    [answers, result, answerResultMap],
  );

  const scoreTone = getScoreTone(result?.score ?? 0);

  return (
    <div className="min-h-screen bg-muted px-4 py-6">
      <Toast toast={toast} onClose={() => setToast(null)} />
      <div className="mx-auto max-w-5xl space-y-4">
        <Card className="p-5 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">Тестүүд</h1>
            <p className="mt-1 text-sm text-neutral-600">Quiz жагсаалт, дараалсан асуултын flow, үнэлгээ</p>
          </div>
          <button
            onClick={() => void load()}
            className="rounded-lg border border-neutral-300 px-3 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-50"
          >
            Шинэчлэх
          </button>
        </Card>

        {error && <ApiErrorPanel message={error} onRetry={() => void load()} />}

        <Card className="p-4">
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setFilter("all")}
              className={`rounded-full px-3 py-1.5 text-xs font-medium border ${
                filter === "all"
                  ? "bg-neutral-900 text-white border-neutral-900"
                  : "bg-white text-neutral-700 border-neutral-200"
              }`}
            >
              Бүгд
            </button>
            {subjectOptions.map((subject) => (
              <button
                key={subject}
                onClick={() => setFilter(subject)}
                className={`rounded-full px-3 py-1.5 text-xs font-medium border ${
                  filter === subject
                    ? "bg-neutral-900 text-white border-neutral-900"
                    : "bg-white text-neutral-700 border-neutral-200"
                }`}
              >
                {subject}
              </button>
            ))}

            <div className="ml-auto" />

            <button
              onClick={() => setSortIndex((prev) => prev + 1)}
              className="rounded-lg border border-neutral-200 px-3 py-2 text-xs font-medium text-neutral-700 inline-flex items-center gap-1.5"
            >
              <ArrowUpDown size={13} />
              {currentSort.label}
            </button>
          </div>
        </Card>

        {loading ? (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.2fr_0.8fr]">
            <Card className="p-5">
              <Skeleton className="h-5 w-40" />
              <div className="space-y-3 mt-4">
                {[0, 1, 2].map((item) => (
                  <div key={item} className="rounded-xl border border-neutral-200 p-4">
                    <Skeleton className="h-5 w-52" />
                    <Skeleton className="h-4 w-36 mt-2" />
                    <Skeleton className="h-3 w-full mt-3" />
                  </div>
                ))}
              </div>
            </Card>
            <Card className="p-5">
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-4 w-48 mt-2" />
              <Skeleton className="h-9 w-full mt-4" />
            </Card>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.2fr_0.8fr]">
            <div className="space-y-4">
              {filteredQuizzes.length === 0 && (
                <Card className="p-5 text-sm text-neutral-500">Сонгосон шүүлтүүрээр тест олдсонгүй.</Card>
              )}

              {filteredQuizzes.map((quiz) => (
                <Card key={quiz.id} className="p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-lg font-semibold text-neutral-900">{quiz.title}</h3>
                      <div className="mt-1 text-sm text-neutral-500">{quiz.subject_name ?? "Сэдэвгүй"}</div>
                      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-neutral-500">
                        <span className="inline-flex items-center gap-1">
                          <LayoutList size={12} /> {quiz.question_count} асуулт
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <Clock3 size={12} /> Ойролцоо {Math.max(5, quiz.question_count)} минут
                        </span>
                        <span>Түвшин: {levelLabel(quiz.level)}</span>
                      </div>
                      <div className="mt-2 text-xs text-neutral-500">
                        Сүүлийн оролдлого: {formatDate(quiz.last_attempt_at)}
                        {quiz.last_score !== null && ` | Оноо: ${quiz.last_score.toFixed(1)}%`}
                      </div>
                    </div>

                    <button
                      onClick={() => void openQuiz(quiz.id)}
                      disabled={loadingQuizId === quiz.id || quiz.question_count === 0}
                      className="rounded-lg bg-primary px-3 py-2 text-sm font-semibold text-white hover:bg-primary/90 disabled:opacity-60 inline-flex items-center gap-1.5"
                    >
                      <PlayCircle size={14} />
                      {quiz.question_count === 0
                        ? "Асуулт алга"
                        : loadingQuizId === quiz.id
                          ? "Нээж байна..."
                          : "Эхлэх"}
                    </button>
                  </div>

                  {quiz.question_count === 0 && (
                    <p className="mt-3 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-2.5 py-2">
                      Энэ тестэд асуулт ороогүй байна. Seed эсвэл admin-оос асуулт нэмэх шаардлагатай.
                    </p>
                  )}
                </Card>
              ))}
            </div>

            <div className="space-y-4">
              <Card className="p-5">
                <h2 className="text-lg font-semibold text-neutral-900">Идэвхтэй тест</h2>

                {!activeQuiz && <p className="mt-2 text-sm text-neutral-500">Зүүн талаас тест сонгоно уу.</p>}

                {activeQuiz && currentQuestion && (
                  <div className="mt-3 space-y-4">
                    <div>
                      <div className="text-sm font-semibold text-neutral-900">{activeQuiz.title}</div>
                      <div className="text-xs text-neutral-500 mt-1">
                        Хариулсан: {answeredCount}/{totalCount}
                      </div>
                      <div className="mt-2">
                        <ProgressBar value={totalCount > 0 ? (answeredCount / totalCount) * 100 : 0} />
                      </div>
                    </div>

                    <div className="rounded-xl border border-neutral-200 p-4">
                      <div className="flex items-center justify-between gap-2 mb-3">
                        <span className="text-xs font-semibold uppercase tracking-wide text-neutral-500">
                          Асуулт {currentQuestionIndex + 1} / {totalCount}
                        </span>
                        {result && (
                          <span className="text-[11px] rounded-full border border-neutral-200 bg-neutral-50 px-2 py-0.5 text-neutral-600">
                            Review mode
                          </span>
                        )}
                      </div>

                      <p className="text-sm font-medium text-neutral-900">{currentQuestion.question_text}</p>

                      <div className="mt-3 space-y-2">
                        {Object.entries(currentQuestion.choices).map(([key, text]) => {
                          const answerResult = answerResultMap.get(currentQuestion.id);
                          const isCorrectChoice = answerResult?.correct_answer === key;
                          const isWrongSelected = answerResult?.selected_answer === key && !answerResult?.is_correct;
                          return (
                            <label
                              key={`${currentQuestion.id}-${key}`}
                              className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-sm transition-colors ${getChoiceClass(
                                currentQuestion.id,
                                key,
                              )}`}
                            >
                              <input
                                type="radio"
                                name={currentQuestion.id}
                                checked={answers[currentQuestion.id] === key}
                                disabled={Boolean(result)}
                                onChange={() => setAnswers((prev) => ({ ...prev, [currentQuestion.id]: key }))}
                                className="mt-0.5"
                              />
                              <span className="flex-1">
                                {key}. {text}
                              </span>
                              {result && isCorrectChoice && <CheckCircle2 size={14} className="shrink-0 mt-0.5" />}
                              {result && isWrongSelected && <XCircle size={14} className="shrink-0 mt-0.5" />}
                            </label>
                          );
                        })}
                      </div>

                      {result && answerResultMap.get(currentQuestion.id)?.explanation && (
                        <div className="mt-3 rounded-lg border border-sky-200 bg-sky-50 p-3 text-xs text-sky-800 leading-5">
                          <span className="font-semibold">Тайлбар:</span>{" "}
                          {answerResultMap.get(currentQuestion.id)?.explanation}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => goToQuestion(currentQuestionIndex - 1)}
                        disabled={currentQuestionIndex <= 0}
                        className="flex-1 rounded-lg border border-neutral-300 px-3 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-50 disabled:opacity-50 inline-flex items-center justify-center gap-1"
                      >
                        <ChevronLeft size={14} />
                        Өмнөх
                      </button>
                      <button
                        onClick={() => goToQuestion(currentQuestionIndex + 1)}
                        disabled={currentQuestionIndex >= totalCount - 1}
                        className="flex-1 rounded-lg border border-neutral-300 px-3 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-50 disabled:opacity-50 inline-flex items-center justify-center gap-1"
                      >
                        Дараагийн
                        <ChevronRight size={14} />
                      </button>
                    </div>

                    {!result && unansweredCount > 0 && (
                      <button
                        onClick={jumpToNextUnanswered}
                        className="w-full rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-700 hover:bg-amber-100 inline-flex items-center justify-center gap-1"
                      >
                        <Target size={13} />
                        Хариулаагүй асуулт руу очих ({unansweredCount})
                      </button>
                    )}

                    {!result ? (
                      <button
                        onClick={() => void submit()}
                        disabled={submitting || answeredCount === 0}
                        className="w-full rounded-lg bg-neutral-900 px-3 py-2 text-sm font-semibold text-white hover:bg-neutral-800 disabled:opacity-50 inline-flex items-center justify-center gap-1.5"
                      >
                        <Send size={14} />
                        {submitting ? "Илгээж байна..." : "Тест илгээх"}
                      </button>
                    ) : (
                      <button
                        onClick={retryQuiz}
                        className="w-full rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm font-semibold text-neutral-700 hover:bg-neutral-50 inline-flex items-center justify-center gap-1.5"
                      >
                        <RotateCcw size={14} />
                        Дахин оролдох
                      </button>
                    )}
                  </div>
                )}
              </Card>

              {result && (
                <Card className="p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs uppercase tracking-wide text-neutral-500">Quiz result</p>
                      <p className={`text-2xl font-bold mt-1 ${scoreTone.number}`}>{result.score.toFixed(1)}%</p>
                      <p className="text-sm text-neutral-600 mt-1">
                        {result.correct_count}/{result.total_questions} зөв хариулт
                      </p>
                    </div>
                    <span className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold ${scoreTone.badge}`}>
                      {scoreTone.text}
                    </span>
                  </div>

                  <p className="text-xs text-neutral-500 mt-3">Илгээсэн: {formatDate(result.completed_at)}</p>

                  <div className="mt-4 space-y-3 max-h-72 overflow-y-auto pr-1">
                    {result.answers.map((item, idx) => {
                      const isCorrect = item.is_correct;
                      const questionIndex = questionIndexById.get(item.question_id) ?? 0;
                      return (
                        <div
                          key={item.question_id}
                          className={`rounded-xl border p-3 ${
                            isCorrect ? "border-emerald-200 bg-emerald-50/70" : "border-red-200 bg-red-50/70"
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <p className="text-xs text-neutral-500">Асуулт {idx + 1}</p>
                              <p className="text-sm font-medium text-neutral-900 mt-0.5">
                                {questionTextMap.get(item.question_id) ?? "Асуултын текст олдсонгүй"}
                              </p>
                            </div>
                            <span
                              className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-[11px] font-semibold ${
                                isCorrect
                                  ? "border border-emerald-300 text-emerald-700"
                                  : "border border-red-300 text-red-700"
                              }`}
                            >
                              {isCorrect ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                              {isCorrect ? "Зөв" : "Буруу"}
                            </span>
                          </div>

                          <div className="mt-2 text-xs text-neutral-700">
                            Таны хариулт: <span className="font-semibold">{item.selected_answer ?? "-"}</span> | Зөв:
                            <span className="font-semibold"> {item.correct_answer}</span>
                          </div>

                          {item.explanation && (
                            <div className="mt-2 rounded-lg border border-neutral-200 bg-white px-2.5 py-2 text-xs text-neutral-700 leading-5">
                              <span className="font-semibold">Тайлбар:</span> {item.explanation}
                            </div>
                          )}

                          <button
                            onClick={() => goToQuestion(questionIndex)}
                            className="mt-2 rounded-md border border-neutral-300 bg-white px-2.5 py-1 text-[11px] font-semibold text-neutral-700 hover:bg-neutral-50"
                          >
                            Энэ асуулт руу очих
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              )}

              <Card className="p-5">
                <h2 className="text-lg font-semibold text-neutral-900 inline-flex items-center gap-2">
                  <History size={16} />
                  Сүүлийн оролдлогууд
                </h2>
                <div className="mt-3 space-y-2">
                  {history.length === 0 && <p className="text-sm text-neutral-500">Оролдлогын түүх алга.</p>}
                  {history.map((item) => (
                    <div key={item.attempt_id} className="rounded-lg border border-neutral-200 px-3 py-2">
                      <div className="text-sm font-medium text-neutral-900">{item.quiz_title}</div>
                      <div className="mt-1 text-xs text-neutral-500">
                        {item.subject_name ?? "Сэдэвгүй"} | {formatDate(item.completed_at)}
                      </div>
                      <div className="mt-1 text-xs text-neutral-600">
                        {item.score !== null ? `${item.score.toFixed(1)}%` : "-"} ({item.correct_count}/{item.total_questions})
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
