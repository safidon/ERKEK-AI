"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  ensureFreshToken,
} from "@/lib/auth";

import { registerUser } from "@/lib/api";
import { LanguageSwitcher, useLang } from "@/lib/i18n";

import {
  finishGoogleLogin,
  GoogleButton,
  PENDING_GOOGLE_KEY,
} from "../google-button";
import { CheckEmailOverlay } from "../resend-verification";


function readPendingGoogle(): string | null {
  try {
    return sessionStorage.getItem(PENDING_GOOGLE_KEY);
  } catch {
    return null;
  }
}

const noopSubscribe = () => () => {};


export default function RegisterPage() {
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

  const [username, setUsername] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [error, setError] =
    useState("");

  const [acceptTerms, setAcceptTerms] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  // Белсендіру хаты жіберілген мекенжай.
  const [sentTo, setSentTo] =
    useState<string | null>(null);

  // Кіру бетінде Google арқылы келген жаңа пайдаланушы.
  const storedGoogle = useSyncExternalStore(
    noopSubscribe,
    readPendingGoogle,
    () => null
  );

  const [localGoogle, setLocalGoogle] =
    useState<string | null>(null);

  const pendingGoogle = localGoogle ?? storedGoogle;


  async function completeGoogle(credential: string) {
    setError("");
    setLoading(true);

    const result = await finishGoogleLogin(credential, true);

    if (result.status === "ok") {
      router.push("/chat");
      return;
    }

    setLoading(false);
    setError(
      result.status === "error" && result.message
        ? result.message
        : tr("Google арқылы кіру сәтсіз аяқталды. Қайталап көр.", "Не удалось войти через Google. Попробуй ещё раз.")
    );
  }


  function handleGoogle(credential: string) {
    if (!acceptTerms) {
      setLocalGoogle(credential);
      setError(
        tr(
          "Жалғастыру үшін алдымен төмендегі келісімге белгі қой.",
          "Чтобы продолжить, сначала отметь согласие ниже."
        )
      );
      return;
    }

    void completeGoogle(credential);
  }


  // =====================================================
  // REGISTER
  // =====================================================

  async function handleSubmit(
    event: React.FormEvent
  ) {
    event.preventDefault();

    setError("");

    if (!acceptTerms) {
      setError(
        tr(
          "Тіркелу үшін шарттар мен құпиялылық саясатына келісу керек.",
          "Для регистрации нужно принять условия и политику конфиденциальности."
        )
      );
      return;
    }

    setLoading(true);

    try {
      const created = await registerUser(
        email,
        username,
        password,
        acceptTerms
      );

      if (created.email_verification_required) {
        setSentTo(email);
      } else {
        router.push("/login");
      }

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

        <div className="absolute bottom-[-250px] right-[-180px] h-[500px] w-[500px] rounded-full bg-gold-500/[0.04] blur-3xl" />

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

                {tr("Жеке AI көмекшіңді баста", "Начни с личным ИИ-помощником")}

              </div>

              <h1 className="text-6xl font-semibold leading-[1.05]">

                {tr("Бір аккаунт.", "Один аккаунт.")}
                <span className="text-gold-gradient block pb-1 italic">
                  {tr("Барлық әңгімең.", "Все твои разговоры.")}
                </span>

              </h1>

              <p className="mt-6 max-w-lg text-base leading-8 text-neutral-500">

                {tr(
                  "Тіркелгеннен кейін жеке чаттарың, ұзақ мерзімді memory және әңгіме тарихы бір аккаунтқа байланысады.",
                  "После регистрации твои чаты, долгосрочная память и история разговоров будут привязаны к одному аккаунту."
                )}

              </p>

            </div>

          </div>


          {/* REGISTER CARD */}

          <div className="mx-auto w-full max-w-md">

            <div className="rounded-[28px] border border-gold-500/15 bg-neutral-950/85 p-6 shadow-2xl backdrop-blur-xl sm:p-8">

              <div className="mb-8">

                <div className="mb-3 text-xs font-semibold uppercase tracking-[0.26em] text-gold-500">
                  {tr("Жаңа аккаунт", "Новый аккаунт")}
                </div>

                <h2 className="text-4xl font-semibold">
                  {tr("Тіркелу", "Регистрация")}
                </h2>

                <p className="mt-2 text-sm leading-6 text-neutral-500">
                  {tr("ERKEK AI-ды пайдалануды баста.", "Начни пользоваться ERKEK AI.")}
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
                    {tr("Username", "Имя пользователя")}
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
                    {tr("Құпиясөз", "Пароль")}
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
                    placeholder={tr("Кемінде 8 таңба", "Минимум 8 символов")}
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
                    {tr("Құпиясөз кемінде 8 таңбадан тұрсын.", "Пароль должен содержать минимум 8 символов.")}
                  </p>

                </div>


                {/* CONSENT */}

                <label className="flex cursor-pointer items-start gap-3 rounded-2xl border border-white/[0.08] bg-black/40 p-4 text-sm leading-6 text-neutral-400 transition hover:border-gold-500/30">

                  <input
                    type="checkbox"
                    checked={acceptTerms}
                    onChange={(event) =>
                      setAcceptTerms(
                        event.target.checked
                      )
                    }
                    className="mt-1 h-4 w-4 shrink-0 accent-[var(--color-gold-500)]"
                  />

                  <span>
                    {tr("18 жастан асқанмын.", "Мне больше 18 лет.")}{" "}
                    {tr("", "Я ознакомился с ")}
                    <Link
                      href="/terms"
                      target="_blank"
                      className="text-gold-400 underline-offset-4 hover:underline"
                    >
                      {tr("Пайдалану шарттарымен", "Условиями использования")}
                    </Link>{" "}
                    {tr("және", "и")}{" "}
                    <Link
                      href="/privacy"
                      target="_blank"
                      className="text-gold-400 underline-offset-4 hover:underline"
                    >
                      {tr("Құпиялылық саясатымен", "Политикой конфиденциальности")}
                    </Link>
                    {tr(
                      " таныстым. Дербес деректерімді өңдеуге, оның ішінде жауап дайындау үшін OpenAI (АҚШ) қызметіне беруге келісемін.",
                      " и согласен на обработку моих персональных данных, в том числе на их передачу сервису OpenAI (США) для подготовки ответов."
                    )}
                  </span>

                </label>


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
                    ? tr("Тіркелуде...", "Регистрируем...")
                    : tr("Тіркелу", "Зарегистрироваться")}
                </button>

              </form>

              {pendingGoogle ? (
                <div className="mt-5 space-y-3 rounded-2xl border border-gold-500/25 bg-gold-500/[0.06] p-4 text-sm leading-6 text-gold-100">
                  <p>
                    {tr(
                      "Google аккаунтың дайын. Жоғарыдағы келісімге белгі қойып, жалғастыр.",
                      "Аккаунт Google готов. Отметь согласие выше и продолжай."
                    )}
                  </p>
                  <button
                    type="button"
                    disabled={!acceptTerms || loading}
                    onClick={() => void completeGoogle(pendingGoogle)}
                    className="flex w-full items-center justify-center rounded-2xl bg-white px-5 py-3 font-medium text-black transition disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {tr("Google арқылы жалғастыру", "Продолжить через Google")}
                  </button>
                </div>
              ) : (
                <div className="mt-5">
                  <GoogleButton onCredential={handleGoogle} />
                </div>
              )}


              {/* LOGIN */}

              <div className="mt-7 border-t border-white/[0.06] pt-6 text-center">

                <p className="text-sm text-neutral-600">
                  {tr("Аккаунтың бар ма?", "Уже есть аккаунт?")}
                </p>

                <button
                  onClick={() =>
                    router.push("/login")
                  }
                  className="mt-2 text-sm font-semibold text-gold-400 transition hover:text-gold-300"
                >
                  {tr("Аккаунтқа кіру →", "Войти в аккаунт →")}
                </button>

              </div>

            </div>


            {/* DISCLAIMER */}

            <p className="mt-5 text-center text-xs leading-5 text-neutral-700">
              {tr(
                "Тіркелу арқылы ERKEK AI сервисін пайдалануды бастайсың.",
                "Зарегистрировавшись, ты начинаешь пользоваться сервисом ERKEK AI."
              )}
            </p>

          </div>

        </div>

      </div>

      {sentTo && <CheckEmailOverlay email={sentTo} />}

    </main>
  );
}