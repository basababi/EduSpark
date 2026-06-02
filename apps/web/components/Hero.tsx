"use client";
import { Button } from "./Button";
import { motion } from "framer-motion";

export const Hero = () => (
  <section className="max-w-6xl mx-auto px-6 py-16 grid md:grid-cols-2 gap-10 items-center">
    <div className="space-y-6">
      <p className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-semibold">
        AI-тай суралцаж эхлээрэй
      </p>
      <h1 className="text-4xl md:text-5xl font-bold leading-tight">
        Монгол хэл дээрх AI STEM суралцах туслах
      </h1>
      <p className="text-lg text-slate-600">
        Математик, физик, программчлалын хичээлийг AI ашиглан тайлбарлаж, шалгаж, ахицыг дэмжинэ.
      </p>
      <div className="flex items-center gap-3">
        <Button variant="primary" href="/signup">Туршиж эхлэх</Button>
        <Button variant="secondary" href="#demo">Демо үзэх</Button>
      </div>
      <div className="grid grid-cols-3 gap-4 text-center">
        {[
          { label: "Оюутан", value: "5,000+" },
          { label: "Хичээл", value: "500+" },
          { label: "Сэтгэл ханамж", value: "95%" },
        ].map((item) => (
          <div key={item.label} className="card p-4">
            <p className="text-2xl font-bold text-primary">{item.value}</p>
            <p className="text-sm text-slate-500">{item.label}</p>
          </div>
        ))}
      </div>
    </div>
    <motion.div
      className="card p-6 bg-gradient-to-br from-white to-slate-50"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="flex gap-3 mb-4">
        {["Математик", "Физик", "Код"].map((tab, idx) => (
          <div
            key={tab}
            className={`px-4 py-2 rounded-full text-sm font-semibold ${idx === 1 ? "bg-secondary/20 text-secondary" : "bg-primary/10 text-primary"}`}
          >
            {tab}
          </div>
        ))}
      </div>
      <div className="space-y-3 text-slate-700">
        <div className="bg-primary text-white rounded-2xl p-4 w-fit">Ньютонны 2-р хуулийг тайлбарлах уу?</div>
        <div className="card p-4 border border-slate-100">
          <p className="font-semibold mb-2">EduSpark AI</p>
          <p>
            F = ma. Хүч нь масс болон хурдатгалын үржвэртэй тэнцүү. Биеийн масс их байх тусам нэг ижил хүчний үед хурдатгал бага байна.
          </p>
        </div>
        <div className="text-sm text-slate-500">Өнөөдрийн ахиц: 75%</div>
        <div className="w-full bg-slate-100 rounded-full h-2">
          <div className="bg-primary h-2 rounded-full" style={{ width: "75%" }} />
        </div>
      </div>
    </motion.div>
  </section>
);
