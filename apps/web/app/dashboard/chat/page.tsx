"use client";

import { useState, useRef, useEffect } from "react";
import { Clock, Info, ArrowRight, Send, ScanText } from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────────────

type Subject = "Программчлал" | "Физик" | "Математик";

type Suggestion = {
  id: string;
  question: string;
  subject: Subject;
  level: string;
};

// ─── Data ────────────────────────────────────────────────────────────────────

const SUGGESTIONS: Suggestion[] = [
  {
    id: "py-fn",
    question: "Python функц гэж юу вэ?",
    subject: "Программчлал",
    level: "Анхан",
  },
  {
    id: "phys-newton",
    question: "Ньютон 2-р хуулийг тайлбарла.",
    subject: "Физик",
    level: "Дунд",
  },
  {
    id: "math-var",
    question: "Хувьсагчийн төрөл ба нэгж хувиргалт.",
    subject: "Математик",
    level: "Анхан",
  },
];

// ─── Style maps ──────────────────────────────────────────────────────────────

const subjectAvatar: Record<Subject, string> = {
  Программчлал: "bg-teal-50 text-teal-800",
  Физик: "bg-amber-50 text-amber-800",
  Математик: "bg-blue-50 text-blue-800",
};

const subjectAbbr: Record<Subject, string> = {
  Программчлал: "Py",
  Физик: "Фз",
  Математик: "Мт",
};

// ─── Atoms ───────────────────────────────────────────────────────────────────

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-neutral-400">
      {children}
    </p>
  );
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function TopBar() {
  return (
    <header className="shrink-0 flex items-center justify-between px-5 h-[54px] border-b border-neutral-200 bg-white">
      <div className="flex items-center gap-2.5">
        <span className="w-2 h-2 rounded-full bg-teal-500 shrink-0" />
        <div>
          <p className="text-sm font-semibold text-neutral-900 leading-tight">
            AI Туслах
          </p>
          <p className="text-[11px] text-neutral-400 leading-tight">
            Ухаалаг суралцах туслагч
          </p>
        </div>
      </div>

      <div className="flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[11px] font-medium text-amber-700">
        <Clock size={11} />
        Backend удахгүй
      </div>
    </header>
  );
}

function DevNotice() {
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-neutral-100">
        <Info size={14} className="text-neutral-400" />
      </div>
      <div>
        <p className="mb-1 text-sm font-semibold text-neutral-900">
          Хөгжүүлэлтийн горим
        </p>
        <p className="text-sm leading-relaxed text-neutral-500">
          Чат функц backend-тэй холбогдох хүртэл идэвхгүй байна. Доорх жишээ
          асуултуудаас сонгоод интерфэйсийг туршиж болно.
        </p>
      </div>
    </div>
  );
}

function SelectedPreview({ value }: { value: string }) {
  if (!value) {
    return (
      <div className="flex items-center gap-2 rounded-2xl border-2 border-dashed border-neutral-200 bg-neutral-50 px-4 py-4 text-sm text-neutral-400">
        <ArrowRight size={14} className="opacity-50" />
        Доороос асуулт сонгоно уу
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-neutral-200 bg-white px-4 py-4 shadow-sm">
      <div className="mb-2 flex items-center gap-2">
        <ScanText size={13} className="text-neutral-400" />
        <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-neutral-400">
          Сонгосон асуулт
        </p>
      </div>
      <p className="text-sm leading-relaxed text-neutral-800">{value}</p>
    </div>
  );
}

function SuggestionButton({
  suggestion,
  isSelected,
  onSelect,
}: {
  suggestion: Suggestion;
  isSelected: boolean;
  onSelect: (q: string) => void;
}) {
  const avatarClass = subjectAvatar[suggestion.subject];
  const abbr = subjectAbbr[suggestion.subject];

  return (
    <button
      onClick={() => onSelect(suggestion.question)}
      className={`group flex w-full items-center gap-3 rounded-2xl border px-4 py-3.5 text-left transition-all duration-150 active:scale-[0.99] ${
        isSelected
          ? "border-neutral-300 bg-white shadow-sm"
          : "border-neutral-200 bg-white hover:-translate-y-[1px] hover:border-neutral-300 hover:shadow-sm"
      }`}
    >
      <div
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-xs font-semibold ${avatarClass}`}
      >
        {abbr}
      </div>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-neutral-900">
          {suggestion.question}
        </p>
        <p className="mt-0.5 text-xs text-neutral-400">
          {suggestion.subject} · {suggestion.level}
        </p>
      </div>

      <ArrowRight
        size={14}
        className={`shrink-0 transition-all duration-150 ${
          isSelected
            ? "text-neutral-500"
            : "text-neutral-300 group-hover:translate-x-0.5 group-hover:text-neutral-500"
        }`}
      />
    </button>
  );
}

function InputBar({ value }: { value: string }) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.value = value;
    }
  }, [value]);

  return (
    <div className="shrink-0 border-t border-neutral-200 bg-white px-4 py-3">
      <div className="mx-auto max-w-2xl">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            placeholder="Асуулт бичих..."
            disabled
            className="h-10 flex-1 cursor-not-allowed rounded-xl border border-neutral-200 bg-neutral-50 px-4 text-sm text-neutral-400 outline-none placeholder:text-neutral-400"
          />
          <button
            disabled
            aria-label="Илгээх"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-neutral-900 opacity-20 cursor-not-allowed"
          >
            <Send size={14} className="text-white" />
          </button>
        </div>
        <p className="mt-2 text-center text-[11px] text-neutral-400">
          Backend холбогдсоны дараа асуулт илгээх боломжтой
        </p>
      </div>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function ChatPage() {
  const [selected, setSelected] = useState("");

  return (
    <div className="flex min-h-screen flex-col bg-white">
      <TopBar />

      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-2xl space-y-5 px-4 py-6">
          <DevNotice />

          <div>
            <SectionLabel>Сонгосон асуулт</SectionLabel>
            <SelectedPreview value={selected} />
          </div>

          <div>
            <SectionLabel>Жишээ асуултууд</SectionLabel>
            <div className="space-y-2">
              {SUGGESTIONS.map((s) => (
                <SuggestionButton
                  key={s.id}
                  suggestion={s}
                  isSelected={selected === s.question}
                  onSelect={setSelected}
                />
              ))}
            </div>
          </div>
        </div>
      </main>

      <InputBar value={selected} />
    </div>
  );
}