import { Button } from "./Button";

export const TutorShowcase = () => (
  <section id="tutor" className="max-w-6xl mx-auto px-6 py-16 grid md:grid-cols-2 gap-8 items-center">
    <div className="space-y-4">
      <p className="inline-flex px-3 py-1 rounded-full bg-primary/10 text-primary font-semibold text-sm">
        AI Туслах
      </p>
      <h2 className="text-3xl font-bold">Хүссэн үедээ асуулт асуу</h2>
      <p className="text-slate-600">
        Монгол хэлээр бичсэн ямар ч асуултанд AI туслах хариулт өгнө. Хэцүү ойлголтуудыг энгийн үгээр тайлбарлаж,
        жишээ бодлого өгч, таны ойлголтыг шалгах тест үүсгэнэ.
      </p>
      <div className="flex gap-3">
        <Button variant="primary">Товч тайлбар</Button>
        <Button variant="secondary">Алхам алхмаар</Button>
        <Button variant="ghost">Тест үүсгэх</Button>
      </div>
    </div>
    <div className="card p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center font-bold text-primary">
          AI
        </div>
        <div>
          <p className="font-semibold">EduSpark AI</p>
          <p className="text-sm text-slate-500">Онлайн · Танд туслахаад бэлэн</p>
        </div>
      </div>
      <div className="space-y-3">
        <div className="self-end bg-primary text-white rounded-2xl p-3 w-fit max-w-[80%]">
          Ньютоны 2-р хуулийг тайлбарла?
        </div>
        <div className="card p-4 border border-slate-100">
          <p className="font-semibold mb-2">AI:</p>
          <p className="text-slate-700 leading-6">
            Ньютоны 2-р хууль нь хүч, масс, хурдатгалын хамаарлыг тодорхойлдог: F = ma. Хүч их байх тусам хурдатгал их,
            масс их байх тусам хурдатгал бага байна.
          </p>
        </div>
      </div>
    </div>
  </section>
);
