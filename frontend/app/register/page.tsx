"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { registerUser } from "@/lib/api";


export default function RegisterPage() {
  const router = useRouter();

  const [email, setEmail] =
    useState("");

  const [username, setUsername] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [error, setError] =
    useState("");

  const [loading, setLoading] =
    useState(false);


  // =====================================================
  // REGISTER
  // =====================================================

  async function handleSubmit(
    event: React.FormEvent
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


  // =====================================================
  // UI
  // =====================================================

  return (
    <main className="relative flex min-h-screen overflow-hidden bg-black text-white">

      {/* BACKGROUND */}

      <div className="pointer-events-none absolute inset-0">

        <div className="absolute left-1/2 top-[-260px] h-[520px] w-[760px] -translate-x-1/2 rounded-full bg-white/[0.04] blur-3xl" />

        <div className="absolute bottom-[-250px] right-[-180px] h-[500px] w-[500px] rounded-full bg-white/[0.025] blur-3xl" />

      </div>


      {/* HOME BUTTON */}

      <button
        onClick={() =>
          router.push("/")
        }
        className="
          absolute
          left-5
          top-5
          z-20
          flex
          items-center
          gap-3
          rounded-xl
          px-2
          py-2
          transition
          hover:bg-white/[0.04]
          sm:left-7
          sm:top-7
        "
      >

        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-sm font-black text-black">
          E
        </div>

        <div className="text-left">

          <div className="text-sm font-semibold">
            ERKEK AI
          </div>

          <div className="text-[10px] uppercase tracking-[0.18em] text-neutral-600">
            Digital mentor
          </div>

        </div>

      </button>


      {/* CONTENT */}

      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-7xl items-center justify-center px-5 py-24 sm:px-6 lg:px-8">

        <div className="grid w-full gap-14 lg:grid-cols-2 lg:items-center">


          {/* LEFT */}

          <div className="hidden lg:block">

            <div className="max-w-xl">

              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-4 py-2 text-xs text-neutral-500">

                <span className="h-1.5 w-1.5 rounded-full bg-green-400" />

                Жеке AI көмекшіңді баста

              </div>

              <h1 className="text-5xl font-semibold leading-tight tracking-[-0.04em]">

                Бір аккаунт.
                <span className="block text-neutral-500">
                  Барлық әңгімең.
                </span>

              </h1>

              <p className="mt-6 max-w-lg text-base leading-8 text-neutral-500">

                Тіркелгеннен кейін жеке чаттарың,
                ұзақ мерзімді memory және әңгіме тарихы
                бір аккаунтқа байланысады.

              </p>

            </div>

          </div>


          {/* REGISTER CARD */}

          <div className="mx-auto w-full max-w-md">

            <div className="rounded-[28px] border border-white/[0.08] bg-neutral-950/80 p-6 shadow-2xl backdrop-blur-xl sm:p-8">

              <div className="mb-8">

                <div className="mb-3 text-xs uppercase tracking-[0.22em] text-neutral-600">
                  Жаңа аккаунт
                </div>

                <h2 className="text-3xl font-semibold tracking-tight">
                  Тіркелу
                </h2>

                <p className="mt-2 text-sm leading-6 text-neutral-500">
                  ERKEK AI-ды пайдалануды баста.
                </p>

              </div>


              <form
                onSubmit={handleSubmit}
                className="space-y-5"
              >

                {/* EMAIL */}

                <div>

                  <label
                    htmlFor="email"
                    className="text-sm text-neutral-400"
                  >
                    Email
                  </label>

                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(event) =>
                      setEmail(
                        event.target.value
                      )
                    }
                    required
                    placeholder="name@example.com"
                    className="
                      mt-2
                      w-full
                      rounded-2xl
                      border
                      border-white/[0.08]
                      bg-black
                      px-4
                      py-3.5
                      text-white
                      outline-none
                      transition
                      placeholder:text-neutral-700
                      focus:border-white/[0.2]
                      focus:bg-neutral-950
                    "
                  />

                </div>


                {/* USERNAME */}

                <div>

                  <label
                    htmlFor="username"
                    className="text-sm text-neutral-400"
                  >
                    Username
                  </label>

                  <input
                    id="username"
                    type="text"
                    autoComplete="username"
                    value={username}
                    onChange={(event) =>
                      setUsername(
                        event.target.value
                      )
                    }
                    required
                    minLength={3}
                    maxLength={30}
                    placeholder="username"
                    className="
                      mt-2
                      w-full
                      rounded-2xl
                      border
                      border-white/[0.08]
                      bg-black
                      px-4
                      py-3.5
                      text-white
                      outline-none
                      transition
                      placeholder:text-neutral-700
                      focus:border-white/[0.2]
                      focus:bg-neutral-950
                    "
                  />

                </div>


                {/* PASSWORD */}

                <div>

                  <label
                    htmlFor="password"
                    className="text-sm text-neutral-400"
                  >
                    Құпиясөз
                  </label>

                  <input
                    id="password"
                    type="password"
                    autoComplete="new-password"
                    value={password}
                    onChange={(event) =>
                      setPassword(
                        event.target.value
                      )
                    }
                    required
                    minLength={8}
                    maxLength={128}
                    placeholder="Кемінде 8 таңба"
                    className="
                      mt-2
                      w-full
                      rounded-2xl
                      border
                      border-white/[0.08]
                      bg-black
                      px-4
                      py-3.5
                      text-white
                      outline-none
                      transition
                      placeholder:text-neutral-700
                      focus:border-white/[0.2]
                      focus:bg-neutral-950
                    "
                  />

                  <p className="mt-2 text-xs leading-5 text-neutral-700">
                    Құпиясөз кемінде 8 таңбадан тұрсын.
                  </p>

                </div>


                {/* ERROR */}

                {error && (
                  <div className="rounded-xl border border-red-500/20 bg-red-500/[0.06] px-4 py-3 text-sm text-red-400">
                    {error}
                  </div>
                )}


                {/* SUBMIT */}

                <button
                  type="submit"
                  disabled={loading}
                  className="
                    flex
                    w-full
                    items-center
                    justify-center
                    rounded-2xl
                    bg-white
                    px-5
                    py-3.5
                    font-medium
                    text-black
                    transition
                    hover:bg-neutral-200
                    disabled:cursor-not-allowed
                    disabled:opacity-50
                  "
                >
                  {loading
                    ? "Тіркелуде..."
                    : "Тіркелу"}
                </button>

              </form>


              {/* LOGIN */}

              <div className="mt-7 border-t border-white/[0.06] pt-6 text-center">

                <p className="text-sm text-neutral-600">
                  Аккаунтың бар ма?
                </p>

                <button
                  onClick={() =>
                    router.push("/login")
                  }
                  className="mt-2 text-sm font-medium text-neutral-300 transition hover:text-white"
                >
                  Аккаунтқа кіру →
                </button>

              </div>

            </div>


            {/* DISCLAIMER */}

            <p className="mt-5 text-center text-xs leading-5 text-neutral-700">
              Тіркелу арқылы ERKEK AI сервисін
              пайдалануды бастайсың.
            </p>

          </div>

        </div>

      </div>

    </main>
  );
}