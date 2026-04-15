"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const API_BASE =
        process.env.NEXT_PUBLIC_API_URL || "/api/v1";
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) {
        setError("Credenziali non valide");
        setLoading(false);
        return;
      }

      const data = await res.json();
      localStorage.setItem("lottery_token", data.token);
      localStorage.setItem("lottery_user", data.username);
      router.push("/");
      router.refresh();
    } catch {
      setError("Errore di connessione");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-lotto-blue to-lotto-purple flex items-center justify-center mx-auto mb-4 shadow-lg shadow-lotto-blue/30">
            <span className="text-white font-black text-2xl">L</span>
          </div>
          <h1 className="text-2xl font-black text-lotto-text">
            Lottery Lab
          </h1>
          <p className="text-sm text-lotto-muted mt-1">
            Accedi al sistema predittivo
          </p>
        </div>

        <form onSubmit={handleLogin} className="glass p-6 space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-widest text-lotto-muted mb-2">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] text-lotto-text focus:border-lotto-blue focus:outline-none transition-colors"
              placeholder="Username"
              autoComplete="username"
            />
          </div>
          <div>
            <label className="block text-xs font-bold uppercase tracking-widest text-lotto-muted mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] text-lotto-text focus:border-lotto-blue focus:outline-none transition-colors"
              placeholder="Password"
              autoComplete="current-password"
            />
          </div>

          {error && (
            <p className="text-sm text-lotto-red text-center">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg bg-gradient-to-r from-lotto-blue to-lotto-purple text-white font-bold text-sm uppercase tracking-wider hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {loading ? "Accesso..." : "Accedi"}
          </button>
        </form>
      </div>
    </div>
  );
}
