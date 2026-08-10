"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { registerUser } from "@/lib/api";


export default function RegisterPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
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
      await registerUser(
        email,
        username,
        password
      );

      router.push("/login");

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
            Жаңа аккаунт ашу
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
              Username
            </label>

            <input
              type="text"
              value={username}
              onChange={(e) =>
                setUsername(e.target.value)
              }
              required
              minLength={3}
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
              minLength={8}
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
              ? "Тіркелуде..."
              : "Тіркелу"}
          </button>

        </form>

        <button
          onClick={() => router.push("/login")}
          className="mt-6 text-sm text-neutral-400 hover:text-white"
        >
          Аккаунтың бар ма? Кіру
        </button>

      </div>

    </main>
  );
}