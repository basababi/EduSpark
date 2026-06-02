const columns = {
  product: ["Онцлогууд", "Хэрхэн ажилладаг", "Үнэ", "Демо"],
  company: ["Бидний тухай", "Блог", "Карьер", "Холбоо барих"],
  help: ["Тусламжийн төв", "FAQ", "Нууцлалын бодлого", "Үйлчилгээний нөхцөл"],
};

export const Footer = () => (
  <footer className="bg-white border-t border-slate-100 mt-10">
    <div className="max-w-6xl mx-auto px-6 py-12 grid md:grid-cols-4 gap-8 text-sm text-slate-600">
      <div className="space-y-3">
        <div className="flex items-center gap-2 font-semibold text-lg text-slate-800">
          <span className="bg-primary text-white rounded-full p-2">AI</span>
          EduSpark AI
        </div>
        <p>Монгол хэл дээрх AI  суралцах туслах. Оюутнуудын суралцах ахицыг дэмжинэ.</p>
      </div>
      <div>
        <h4 className="font-semibold text-slate-800 mb-3">Бүтээгдэхүүн</h4>
        <div className="space-y-2">
          {columns.product.map((item) => (
            <a key={item} href="#" className="block hover:text-primary">
              {item}
            </a>
          ))}
        </div>
      </div>
      <div>
        <h4 className="font-semibold text-slate-800 mb-3">Компанӣ</h4>
        <div className="space-y-2">
          {columns.company.map((item) => (
            <a key={item} href="#" className="block hover:text-primary">
              {item}
            </a>
          ))}
        </div>
      </div>
      <div>
        <h4 className="font-semibold text-slate-800 mb-3">Тусламж</h4>
        <div className="space-y-2">
          {columns.help.map((item) => (
            <a key={item} href="#" className="block hover:text-primary">
              {item}
            </a>
          ))}
        </div>
      </div>
    </div>
    <div className="text-center text-xs text-slate-500 pb-6">© 2026 EduSpark AI. Бүх эрх хуулиар хамгаалагдсан.</div>
  </footer>
);
