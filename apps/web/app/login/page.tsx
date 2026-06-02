"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, login, saveTokens } from "@/lib/api-client";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("user2@example.com");
  const [password, setPassword] = useState("Passw0rd!");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await login(email, password);
      saveTokens({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
      });
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError("Нэвтрэх үед сервертэй холбогдож чадсангүй.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted px-4">
      <div className="card w-full max-w-md p-8">
        <h1 className="text-2xl font-bold mb-6 text-center">Нэвтрэх</h1>
        <form className="space-y-4" onSubmit={onSubmit}>
          <div>
            <label className="text-sm font-semibold text-slate-600">И-мэйл</label>
            <input
              className="w-full mt-1 rounded-xl border border-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/40"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="student@example.com"
              required
            />
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-600">Нууц үг</label>
            <input
              className="w-full mt-1 rounded-xl border border-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/40"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          {error && <div className="text-red-600 text-sm">{error}</div>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary text-white rounded-xl py-3 font-semibold hover:bg-primary/90 disabled:opacity-70"
          >
            {loading ? "Шалгаж байна..." : "Нэвтрэх"}
          </button>
        </form>

        <p className="text-center text-sm text-slate-500 mt-4">
          Шинэ хэрэглэгч үү?{" "}
          <a href="/signup" className="text-primary font-semibold">
            Бүртгүүлэх
          </a>
        </p>
      </div>
    </div>
  );
}
