"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  ensureFreshToken,
  saveTokens,
} from "@/lib/auth";

import { loginUser } from "@/lib/api";
import { LanguageSwitcher, useLang } from "@/lib/i18n";


export default function LoginPage() {
  const router = useRouter();
  const { tr } = useLang();

  // Кірген пайдаланушыны бірден чатқа жібереміз
  useEffect(() => {
    void ensureFreshToken().then((token) => {
      if (token) {
        router.replace("/chat");
      }
    });
  }, [router]);

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [error, setError] =
    useState("");

  const [loading, setLoading] =
    useState(false);


  // =====================================================
  // LOGIN
  // =====================================================

  async function handleSubmit(
    event: React.FormEvent
  ) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const result = await loginUser(
        email,
        password
      );

      saveTokens(
        result.access_token,
        result.refresh_token
      );

      router.push("/chat");

    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError(tr("Белгісіз қате шықты.", "Произошла неизвестная ошибка."));
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

        <div className="bg-ornament absolute inset-0" />

        <div className="absolute left-1/2 top-[-260px] h-[520px] w-[760px] -translate-x-1/2 rounded-full bg-gold-500/[0.08] blur-3xl" />

        <div className="absolute bottom-[-250px] left-[-180px] h-[500px] w-[500px] rounded-full bg-gold-500/[0.04] blur-3xl" />

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

        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white font-display text-lg font-bold text-black">
          E
        </div>

        <div className="text-left">

          <div className="text-sm font-semibold">
            ERKEK AI
          </div>

          <div className="text-[10px] uppercase tracking-[0.24em] text-gold-500/70">
            Digital mentor
          </div>

        </div>

      </button>

      <LanguageSwitcher className="absolute right-5 top-6 z-20 sm:right-7 sm:top-8" />


      {/* CONTENT */}

      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-7xl items-center justify-center px-5 py-24 sm:px-6 lg:px-8">

        <div className="grid w-full gap-14 lg:grid-cols-2 lg:items-center">


          {/* LEFT */}

          <div className="hidden lg:block">

            <div className="max-w-xl">

              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-gold-500/25 bg-gold-500/[0.06] px-4 py-2 text-xs font-medium text-gold-300">

                <span className="text-[9px] text-gold-500">◆</span>

                {tr("Қайта келгеніңе қуаныштымыз", "Рады снова тебя видеть")}

              </div>

              <h1 className="text-6xl font-semibold leading-[1.05]">

                {tr("Әңгімеңді", "Продолжи")}
                <span className="text-gold-gradient block pb-1 italic">
                  {tr("жалғастыр.", "разговор.")}
                </span>

              </h1>

              <p className="mt-6 max-w-lg text-base leading-8 text-neutral-500">

                {tr(
                  "Бұрынғы чаттарың, жеке контекст және сақталған әңгімелерің аккаунтыңа кіргеннен кейін қайта қолжетімді болады.",
                  "После входа снова будут доступны твои чаты, личный контекст и сохранённые разговоры."
                )}

              </p>

            </div>

          </div>


          {/* LOGIN CARD */}

          <div className="mx-auto w-full max-w-md">

            <div className="rounded-[28px] border border-gold-500/15 bg-neutral-950/85 p-6 shadow-2xl backdrop-blur-xl sm:p-8">

              <div className="mb-8">

                <div className="mb-3 text-xs font-semibold uppercase tracking-[0.26em] text-gold-500">
                  {tr("Аккаунт", "Аккаунт")}
                </div>

                <h2 className="text-4xl font-semibold">
                  {tr("Кіру", "Вход")}
                </h2>

                <p className="mt-2 text-sm leading-6 text-neutral-500">
                  {tr("ERKEK AI аккаунтыңа кір.", "Войди в свой аккаунт ERKEK AI.")}
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


                {/* PASSWORD */}

                <div>

                  <div className="flex items-center justify-between gap-3">

                    <label
                      htmlFor="password"
                      className="text-sm text-neutral-400"
                    >
                      {tr("Құпиясөз", "Пароль")}
                    </label>

                    <button
                      type="button"
                      onClick={() =>
                        router.push("/forgot-password")
                      }
                      className="text-xs font-medium text-gold-400 transition hover:text-gold-300"
                    >
                      {tr("Құпиясөзді ұмыттың ба?", "Забыл пароль?")}
                    </button>

                  </div>

                  <input
                    id="password"
                    type="password"
                    autoComplete="current-password"
                    value={password}
                    onChange={(event) =>
                      setPassword(
                        event.target.value
                      )
                    }
                    required
                    placeholder="••••••••"
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
                    ? tr("Кіруде...", "Входим...")
                    : tr("Кіру", "Войти")}
                </button>

              </form>


              {/* REGISTER */}

              <div className="mt-7 border-t border-white/[0.06] pt-6 text-center">

                <p className="text-sm text-neutral-600">
                  {tr("Аккаунтың жоқ па?", "Нет аккаунта?")}
                </p>

                <button
                  onClick={() =>
                    router.push("/register")
                  }
                  className="mt-2 text-sm font-semibold text-gold-400 transition hover:text-gold-300"
                >
                  {tr("Жаңа аккаунт ашу →", "Создать аккаунт →")}
                </button>

              </div>

            </div>


            {/* DISCLAIMER */}

            <p className="mt-5 text-center text-xs leading-5 text-neutral-600">
              {tr("Кіру арқылы ERKEK AI-дың", "Входя, ты продолжаешь работу в соответствии с")}{" "}
              <a href="/terms" className="text-neutral-400 underline-offset-4 hover:text-gold-300 hover:underline">
                {tr("пайдалану шарттары", "условиями использования")}
              </a>{" "}
              {tr("мен", "и")}{" "}
              <a href="/privacy" className="text-neutral-400 underline-offset-4 hover:text-gold-300 hover:underline">
                {tr("құпиялылық саясатына", "политикой конфиденциальности")}
              </a>
              {tr(" сәйкес жұмысты жалғастырасың.", " ERKEK AI.")}
            </p>

          </div>

        </div>

      </div>

    </main>
  );
}