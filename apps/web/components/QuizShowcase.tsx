import { Button } from "./Button";

export const QuizShowcase = () => (
  <section id="quiz" className="max-w-6xl mx-auto px-6 py-16 grid md:grid-cols-2 gap-8 items-center">
    <div className="card p-6">
      <div className="flex justify-between text-sm text-slate-600 mb-3">
        <span>Физик · Ньютоны хууль</span>
        <span>Асуулт 3/10</span>
      </div>
      <div className="h-2 rounded-full bg-slate-100 mb-4">
        <div className="h-2 rounded-full bg-primary" style={{ width: "30%" }} />
      </div>
      <h3 className="text-lg font-semibold mb-3">Ньютоны 2-р хуулийн томъёо аль нь вэ?</h3>
      <div className="space-y-2">
        {[
          { text: "F = mv", state: "wrong" },
          { text: "F = ma", state: "correct" },
          { text: "F = m/a" },
          { text: "F = a/m" },
        ].map((opt) => (
          <div
            key={opt.text}
            className={`p-3 rounded-xl border ${
              opt.state === "correct"
                ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                : opt.state === "wrong"
                ? "border-rose-200 bg-rose-50 text-rose-700"
                : "border-slate-200 bg-white"
            }`}
          >
            {opt.text}
          </div>
        ))}
      </div>
      <div className="mt-4 p-3 rounded-xl bg-rose-50 text-rose-700 text-sm">
        Буруу хариулт. Зөв нь F = ma. Хүч нь масс ба хурдатгалын үржвэртэй тэнцүү.
      </div>
      <div className="flex gap-3 mt-4">
        <Button variant="ghost">Дахин хариулах</Button>
        <Button variant="primary">Дараагийн асуулт</Button>
      </div>
    </div>
    <div className="space-y-4">
      <p className="inline-flex px-3 py-1 rounded-full bg-secondary/15 text-secondary font-semibold text-sm">
        Тест систем
      </p>
      <h2 className="text-3xl font-bold">Мэдлэгээ шалгаж, оноогоо авна</h2>
      <p className="text-slate-600">
        AI-аар үүсгэсэн тестүүд таны түвшинд тохирсон. Алдаанаас суралцаж, ахиц дэвшлээ хянана.
      </p>
      <div className="grid grid-cols-2 gap-4">
        {[
          { label: "Дундаж оноо", value: "85%" },
          { label: "Зөв хариулт", value: "23" },
          { label: "Буруу", value: "4" },
          { label: "Сүүлийн 7 хоног", value: "+12%" },
        ].map((stat) => (
          <div key={stat.label} className="card p-4 text-center">
            <p className="text-2xl font-bold text-primary">{stat.value}</p>
            <p className="text-sm text-slate-500">{stat.label}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);
