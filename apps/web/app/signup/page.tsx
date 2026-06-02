export default function SignupPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-muted px-4">
      <div className="card w-full max-w-md p-8">
        <h1 className="text-2xl font-bold mb-6 text-center">Бүртгүүлэх</h1>
        <form className="space-y-4">
          <div>
            <label className="text-sm font-semibold text-slate-600">Нэр</label>
            <input
              className="w-full mt-1 rounded-xl border border-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/40"
              type="text"
              placeholder="Батаа"
            />
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-600">И-мэйл</label>
            <input
              className="w-full mt-1 rounded-xl border border-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/40"
              type="email"
              placeholder="student@example.com"
            />
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-600">Нууц үг</label>
            <input
              className="w-full mt-1 rounded-xl border border-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/40"
              type="password"
              placeholder="••••••••"
            />
          </div>
          <button
            type="submit"
            className="w-full bg-primary text-white rounded-xl py-3 font-semibold hover:bg-primary/90"
          >
            Бүртгүүлэх
          </button>
        </form>
        <p className="text-center text-sm text-slate-500 mt-4">
          Аль хэдийн бүртгэлтэй? <a href="/login" className="text-primary font-semibold">Нэвтрэх</a>
        </p>
      </div>
    </div>
  );
}
