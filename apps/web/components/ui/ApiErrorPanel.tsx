import { RefreshCw, TriangleAlert } from "lucide-react";

type ApiErrorPanelProps = {
  message: string;
  onRetry: () => void;
};

export function ApiErrorPanel({ message, onRetry }: ApiErrorPanelProps) {
  return (
    <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2">
          <TriangleAlert size={18} className="mt-0.5 text-red-600" />
          <p className="text-sm text-red-700">{message}</p>
        </div>
        <button
          onClick={onRetry}
          className="shrink-0 rounded-lg border border-red-300 bg-white px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-100"
        >
          <span className="inline-flex items-center gap-1">
            <RefreshCw size={12} />
            Дахин оролдох
          </span>
        </button>
      </div>
    </div>
  );
}
