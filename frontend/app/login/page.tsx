"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { loginUser } from "@/lib/api";


export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);


  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const result = await loginUser(
        email,
        password
      );

      localStorage.setItem(
        "access_token",
        result.access_token
      );

      router.push("/chat");

    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError("Белгісіз қате шықты.");
      }

    } finally {
      setLoading(false);
    }
  }


  return (
    <main className="min-h-screen bg-black text-white flex items-center justify-center px-6">

      <div className="w-full max-w-md">

        <div className="mb-10">
          <h1 className="text-3xl font-semibold">
            ERKEK AI
          </h1>

          <p className="mt-2 text-neutral-400">
            Аккаунтқа кіру
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-5"
        >

          <div>
            <label className="text-sm text-neutral-400">
              Email
            </label>

            <input
              type="email"
              value={email}
              onChange={(e) =>
                setEmail(e.target.value)
              }
              required
              className="
                mt-2
                w-full
                rounded-xl
                border
                border-neutral-800
                bg-neutral-950
                px-4
                py-3
                outline-none
                focus:border-neutral-600
              "
            />
          </div>

          <div>
            <label className="text-sm text-neutral-400">
              Құпиясөз
            </label>

            <input
              type="password"
              value={password}
              onChange={(e) =>
                setPassword(e.target.value)
              }
              required
              className="
                mt-2
                w-full
                rounded-xl
                border
                border-neutral-800
                bg-neutral-950
                px-4
                py-3
                outline-none
                focus:border-neutral-600
              "
            />
          </div>

          {error && (
            <div className="text-sm text-red-400">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="
              w-full
              rounded-xl
              bg-white
              text-black
              py-3
              font-medium
              transition
              hover:bg-neutral-200
              disabled:opacity-50
            "
          >
            {loading
              ? "Кіруде..."
              : "Кіру"}
          </button>

        </form>

        <button
          onClick={() =>
            router.push("/register")
          }
          className="mt-6 text-sm text-neutral-400 hover:text-white"
        >
          Аккаунтың жоқ па? Тіркелу
        </button>

      </div>

    </main>
  );
}