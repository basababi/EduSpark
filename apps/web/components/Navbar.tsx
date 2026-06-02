import { Button } from "./Button";

const links = [
  { label: "Онцлогууд", href: "#features" },
  { label: "Хэрхэн ажилладаг", href: "#how" },
  { label: "Хяналт самбар", href: "#dashboard" },
  { label: "Ахиц", href: "#progress" },
];

export const Navbar = () => (
  <header className="w-full bg-white/90 backdrop-blur-md border-b border-slate-100">
    <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
      <div className="flex items-center gap-2 font-semibold text-lg">
        <span className="bg-primary text-white rounded-full p-2">AI</span>
        EduSpark AI
      </div>
      <nav className="hidden md:flex items-center gap-6 text-sm text-slate-700">
        {links.map((l) => (
          <a key={l.href} href={l.href} className="hover:text-primary">
            {l.label}
          </a>
        ))}
      </nav>
      <div className="flex items-center gap-3">
        <Button variant="ghost" href="/login">
          Нэвтрэх
        </Button>
        <Button variant="primary" href="/signup">
          Бүртгүүлэх
        </Button>
      </div>
    </div>
  </header>
);
