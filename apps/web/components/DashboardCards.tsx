import { BookOpen, Flame, Medal, Timer } from "lucide-react";

type StatCardItem = {
  key: string;
  icon: "time" | "streak" | "lessons" | "score";
  label: string;
  value: string;
};

const ICONS = {
  time: Timer,
  streak: Flame,
  lessons: BookOpen,
  score: Medal,
} as const;

const THEMES = {
  time: { color: "text-primary", bg: "bg-primary/10" },
  streak: { color: "text-secondary", bg: "bg-secondary/15" },
  lessons: { color: "text-primary", bg: "bg-primary/10" },
  score: { color: "text-secondary", bg: "bg-secondary/15" },
} as const;

export const StatCards = ({ items }: { items: StatCardItem[] }) => {
  return (
    <div className="grid md:grid-cols-4 gap-4">
      {items.map((item) => {
        const Icon = ICONS[item.icon];
        const theme = THEMES[item.icon];

        return (
          <div key={item.key} className="card p-4 flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${theme.bg}`}>
              <Icon className={theme.color} size={20} />
            </div>
            <div>
              <p className="text-sm text-slate-500">{item.label}</p>
              <p className="text-xl font-semibold">{item.value}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};
