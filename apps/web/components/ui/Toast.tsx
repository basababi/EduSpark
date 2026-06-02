"use client";

import { useEffect } from "react";
import type { ElementType } from "react";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";

type ToastVariant = "success" | "error" | "info";

export type ToastState = {
  variant: ToastVariant;
  message: string;
} | null;

type ToastProps = {
  toast: ToastState;
  onClose: () => void;
  durationMs?: number;
};

const TOAST_STYLES: Record<
  ToastVariant,
  {
    wrapper: string;
    icon: ElementType;
  }
> = {
  success: {
    wrapper: "border-emerald-200 bg-emerald-50 text-emerald-800",
    icon: CheckCircle2,
  },
  error: {
    wrapper: "border-red-200 bg-red-50 text-red-800",
    icon: AlertCircle,
  },
  info: {
    wrapper: "border-sky-200 bg-sky-50 text-sky-800",
    icon: Info,
  },
};

export function Toast({ toast, onClose, durationMs = 3600 }: ToastProps) {
  useEffect(() => {
    if (!toast) {
      return;
    }
    const timer = window.setTimeout(onClose, durationMs);
    return () => window.clearTimeout(timer);
  }, [toast, onClose, durationMs]);

  if (!toast) {
    return null;
  }

  const style = TOAST_STYLES[toast.variant];
  const Icon = style.icon;

  return (
    <div className="fixed right-4 top-4 z-[120] max-w-sm">
      <div
        role="status"
        aria-live="polite"
        className={`rounded-xl border px-3 py-2 shadow-lg ${style.wrapper}`}
      >
        <div className="flex items-start gap-2">
          <Icon size={18} className="shrink-0 mt-0.5" />
          <p className="text-sm font-medium leading-5 flex-1">{toast.message}</p>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-md p-1 hover:bg-black/10"
            aria-label="Toast хаах"
          >
            <X size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
