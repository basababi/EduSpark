"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ArrowUpRight, TrendingUp } from "lucide-react";

type WeeklyPoint = {
  day: string;
  studied: number;
  goal: number;
};

type StrengthPoint = {
  name: string;
  value: number;
};

function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-2xl border border-neutral-200 bg-white shadow-sm ${className}`}>
      {children}
    </div>
  );
}

function CardHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4 flex-wrap mb-4">
      <div>
        <h3 className="font-semibold text-neutral-900">{title}</h3>
        {subtitle && <p className="text-sm text-neutral-500 mt-1">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

export const WeeklyChart = ({
  data,
  totalHours,
  weeklyGoalHours,
  weeklyGoalPercent,
}: {
  data: WeeklyPoint[];
  totalHours: number;
  weeklyGoalHours: number;
  weeklyGoalPercent: number;
}) => (
  <Card className="p-5">
    <CardHeader
      title="7 хоногийн суралцах хугацаа"
      subtitle={`Нийт сурсан: ${totalHours.toFixed(1)} / ${weeklyGoalHours.toFixed(1)} цаг`}
      action={
        <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
          <TrendingUp size={12} />
          {weeklyGoalPercent.toFixed(1)}%
        </span>
      }
    />

    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} barGap={8}>
          <CartesianGrid vertical={false} stroke="#f1f5f9" />
          <XAxis
            dataKey="day"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#737373", fontSize: 12 }}
          />
          <YAxis hide />
          <Tooltip
            cursor={{ fill: "#fafafa" }}
            contentStyle={{
              borderRadius: 12,
              border: "1px solid #e5e5e5",
              boxShadow: "0 4px 14px rgba(0,0,0,0.06)",
            }}
          />
          <Bar dataKey="studied" fill="#171717" radius={[8, 8, 0, 0]} />
          <Bar dataKey="goal" fill="#d4d4d4" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  </Card>
);

export const Strengths = ({ items }: { items: StrengthPoint[] }) => (
  <Card className="p-5">
    <CardHeader title="Давуу талууд" subtitle="Хамгийн өндөр үзүүлэлттэй сэдвүүд" />

    <div className="space-y-4">
      {items.length === 0 ? (
        <p className="text-sm text-neutral-500">Одоогоор хангалттай өгөгдөл алга байна.</p>
      ) : (
        items.map((item) => (
          <div key={item.name}>
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="font-medium text-neutral-800">{item.name}</span>
              <span className="font-semibold text-emerald-600">{item.value.toFixed(1)}%</span>
            </div>
            <div className="h-2.5 bg-neutral-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-500 rounded-full"
                style={{ width: `${Math.min(item.value, 100)}%` }}
              />
            </div>
          </div>
        ))
      )}
    </div>
  </Card>
);

export const TrendsCard = ({ data }: { data: WeeklyPoint[] }) => (
  <Card className="p-5">
    <CardHeader
      title="Сүүлийн 7 хоногийн ахиц"
      subtitle="Өдөр тутмын суралцах тренд"
      action={
        <span className="inline-flex items-center gap-1 text-sm font-medium text-neutral-600">
          Тренд
          <ArrowUpRight size={14} />
        </span>
      }
    />

    <div className="h-60">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid vertical={false} stroke="#f1f5f9" />
          <XAxis
            dataKey="day"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#737373", fontSize: 12 }}
          />
          <YAxis hide />
          <Tooltip
            contentStyle={{
              borderRadius: 12,
              border: "1px solid #e5e5e5",
              boxShadow: "0 4px 14px rgba(0,0,0,0.06)",
            }}
          />
          <Line
            type="monotone"
            dataKey="studied"
            stroke="#171717"
            strokeWidth={3}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  </Card>
);
