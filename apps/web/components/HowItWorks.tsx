const steps = [
  { title: "Сэдвээ сонгоно", desc: "Математик, физик эсвэл программчлалын хичээлүүдээс сонгоно." },
  { title: "AI-аас тайлбар авна", desc: "Асуултаа бичээд AI-аас хялбар ойлгомжтой хариулт авна." },
  { title: "Тест өгч ахиц хянана", desc: "Тест өгөөд ахицын графикаар өөрийгөө хяна." },
];

export const HowItWorks = () => (
  <section id="how" className="max-w-6xl mx-auto px-6 py-16">
    <div className="text-center mb-10 space-y-3">
      <p className="inline-flex px-3 py-1 rounded-full bg-secondary/15 text-secondary font-semibold text-sm">
        Хэрхэн ажилладаг
      </p>
      <h2 className="text-3xl font-bold">3 хялбар алхмаар эхлээрэй</h2>
      <p className="text-slate-600">Алхамуудыг дагаад суралцаж эхлээрэй.</p>
    </div>
    <div className="grid md:grid-cols-3 gap-4">
      {steps.map((step, idx) => (
        <div key={step.title} className="card p-6 border-t-4 border-primary/60">
          <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center mb-4">
            {String(idx + 1).padStart(2, "0")}
          </div>
          <h3 className="font-semibold text-lg mb-2">{step.title}</h3>
          <p className="text-slate-600 text-sm leading-6">{step.desc}</p>
        </div>
      ))}
    </div>
  </section>
);
