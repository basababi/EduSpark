import { Brain, CheckCircle2, LineChart, MessageCircle } from "lucide-react";

const items = [
  {
    icon: <Brain className="text-primary" />,
    title: "AI тайлбарлагч",
    desc: "Математик, физик, программчлалын асуултад ойлгомжтой тайлбар өгнө.",
  },
  {
    icon: <CheckCircle2 className="text-secondary" />,
    title: "Ухаалаг тест",
    desc: "Таны түвшинд тааруулан тест үүсгэж, хариултыг дүгнэнэ.",
  },
  {
    icon: <LineChart className="text-primary" />,
    title: "Ахиц хянах",
    desc: "Долоо хоногийн ахиц, зорилгын биелэлт, хүчтэй/сул талууд.",
  },
  {
    icon: <MessageCircle className="text-secondary" />,
    title: "Монгол хэл дээр",
    desc: "Бүх харилцаа, тайлбар, тестийг Монгол хэл дээр авах боломж.",
  },
];

export const Features = () => (
  <section id="features" className="max-w-6xl mx-auto px-6 py-16">
    <div className="text-center mb-10 space-y-3">
      <p className="inline-flex px-3 py-1 rounded-full bg-primary/10 text-primary font-semibold text-sm">
        Онцлогууд
      </p>
      <h2 className="text-3xl font-bold">Яагаад EduSpark AI сонгох вэ?</h2>
      <p className="text-slate-600">AI технологиор таны суралцах замыг илүү үр дүнтэй, хурдтай болгоно.</p>
    </div>
    <div className="grid md:grid-cols-4 gap-4">
      {items.map((item) => (
        <div key={item.title} className="card p-5 border border-slate-100">
          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center mb-4">
            {item.icon}
          </div>
          <h3 className="font-semibold text-lg mb-2">{item.title}</h3>
          <p className="text-slate-600 text-sm leading-6">{item.desc}</p>
        </div>
      ))}
    </div>
  </section>
);
