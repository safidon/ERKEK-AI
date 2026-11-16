"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { LanguageSwitcher, useLang } from "@/lib/i18n";
import { localizePersona } from "../chat/components";

import {
  clearSession,
  ensureFreshToken,
  getValidToken,
  refreshSession,
  useSessionKeeper,
} from "@/lib/auth";

import { DeleteAccountSection } from "./delete-account";
import { TelegramLinkSection } from "./telegram-link";

type UserProfile = {
  user_id: string;

  language: string | null;
  age: number | null;
  marital_status: string | null;
  children: number | null;

  career: string | null;
  financial_status: string | null;
  main_goal: string | null;

  goals: string[];
  habits: string[];
  important_events: string[];
};

type PersonaOption = {
  id: string;
  title: string;
  description: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

// =====================================================
// SETTINGS PAGE
// =====================================================

export default function SettingsPage() {
  const router = useRouter();
  const { tr, lang } = useLang();

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [
    memoryActionLoading,
    setMemoryActionLoading,
  ] = useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  // =====================================================
  // PERSONA (ERKEK AI мінезі)
  // =====================================================

  const [persona, setPersona] =
    useState("brother");

  const [
    personaOptions,
    setPersonaOptions,
  ] = useState<PersonaOption[]>([]);

  const [
    personaSaving,
    setPersonaSaving,
  ] = useState(false);

  // =====================================================
  // BASIC PROFILE
  // =====================================================

  const [language, setLanguage] =
    useState("");

  const [age, setAge] =
    useState("");

  const [
    maritalStatus,
    setMaritalStatus,
  ] = useState("");

  const [children, setChildren] =
    useState("");

  // =====================================================
  // CAREER / FINANCE
  // =====================================================

  const [career, setCareer] =
    useState("");

  const [
    financialStatus,
    setFinancialStatus,
  ] = useState("");

  const [mainGoal, setMainGoal] =
    useState("");

  // =====================================================
  // MEMORY LISTS
  // =====================================================

  const [goals, setGoals] =
    useState<string[]>([]);

  const [habits, setHabits] =
    useState<string[]>([]);

  const [
    importantEvents,
    setImportantEvents,
  ] = useState<string[]>([]);

  // =====================================================
  // NEW ITEMS
  // =====================================================

  const [newGoal, setNewGoal] =
    useState("");

  const [newHabit, setNewHabit] =
    useState("");

  const [
    newImportantEvent,
    setNewImportantEvent,
  ] = useState("");

  // =====================================================
  // TOKEN
  // =====================================================

  function getToken() {
    return getValidToken();
  }

  // =====================================================
  // UNAUTHORIZED
  // =====================================================

  // Сервер 401 қайтарды: алдымен сессияны жаңартып көреміз,
  // болмаса ғана кіру бетіне жібереміз.
  function handleUnauthorized() {
    void refreshSession().then((result) => {
      if (result.status === "expired") {
        clearSession();
        router.replace("/login");
      }
    });
  }

  // Token мерзімі біткенде автоматты түрде шығару
  useSessionKeeper(() => router.replace("/login"));

  // =====================================================
  // APPLY PROFILE TO UI
  // =====================================================

  function applyProfile(
    profile: UserProfile
  ) {
    setLanguage(
      profile.language ?? ""
    );

    setAge(
      profile.age !== null &&
      profile.age !== undefined
        ? String(profile.age)
        : ""
    );

    setMaritalStatus(
      profile.marital_status ?? ""
    );

    setChildren(
      profile.children !== null &&
      profile.children !== undefined
        ? String(profile.children)
        : ""
    );

    setCareer(
      profile.career ?? ""
    );

    setFinancialStatus(
      profile.financial_status ?? ""
    );

    setMainGoal(
      profile.main_goal ?? ""
    );

    setGoals(
      profile.goals ?? []
    );

    setHabits(
      profile.habits ?? []
    );

    setImportantEvents(
      profile.important_events ?? []
    );
  }

  // =====================================================
  // SUCCESS MESSAGE
  // =====================================================

  function showSuccess(
    message: string
  ) {
    setSuccess(message);

    window.setTimeout(
      () => {
        setSuccess("");
      },
      2500
    );
  }

  // =====================================================
  // LOAD PROFILE
  // =====================================================

  async function loadProfile() {
    const token = getToken();

    if (!token) {
      handleUnauthorized();
      return;
    }

    // loading бастапқы мәні true, error бос —
    // effect ішінде синхронды setState қажет емес.

    try {
      const response =
        await fetch(
          `${API_URL}/profile`,
          {
            headers: {
              Authorization:
                `Bearer ${token}`,
            },
          }
        );

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            tr("Профильді жүктеу кезінде қате шықты.", "Ошибка при загрузке профиля.")
        );
      }

      applyProfile(
        data as UserProfile
      );

      const personaResponse =
        await fetch(
          `${API_URL}/profile/persona`,
          {
            headers: {
              Authorization:
                `Bearer ${token}`,
            },
          }
        );

      if (personaResponse.ok) {
        const personaData =
          await personaResponse.json();

        setPersona(
          personaData.persona
        );

        setPersonaOptions(
          personaData.options
        );
      }

    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError(
          tr("Белгісіз қате шықты.", "Произошла неизвестная ошибка.")
        );
      }

    } finally {
      setLoading(false);
    }
  }

  // =====================================================
  // AUTH CHECK + LOAD PROFILE
  // =====================================================

  useEffect(() => {
    // Access token-нің мерзімі өтсе, алдымен refresh token арқылы жаңартамыз.
    void ensureFreshToken().then((token) => {
      if (!token) {
        router.replace("/login");
        return;
      }

      void loadProfile();
    });
    // Тек mount кезінде бір рет жүктеледі.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  // =====================================================
  // SAVE PERSONA
  // =====================================================

  async function savePersona(
    nextPersona: string
  ) {
    const token = getToken();

    if (!token) {
      handleUnauthorized();
      return;
    }

    if (
      nextPersona === persona ||
      personaSaving
    ) {
      return;
    }

    const previousPersona = persona;

    setPersona(nextPersona);
    setPersonaSaving(true);
    setError("");

    try {
      const response =
        await fetch(
          `${API_URL}/profile/persona`,
          {
            method: "PATCH",
            headers: {
              "Content-Type":
                "application/json",
              Authorization:
                `Bearer ${token}`,
            },
            body: JSON.stringify({
              persona: nextPersona,
            }),
          }
        );

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      if (!response.ok) {
        throw new Error(
          tr("Мінезді сақтау кезінде қате шықты.", "Ошибка при сохранении характера.")
        );
      }

      showSuccess(
        tr("ERKEK AI мінезі сақталды.", "Характер ERKEK AI сохранён.")
      );

    } catch (error) {
      setPersona(previousPersona);

      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError(
          tr("Белгісіз қате шықты.", "Произошла неизвестная ошибка.")
        );
      }

    } finally {
      setPersonaSaving(false);
    }
  }

  // =====================================================
  // SAVE PROFILE
  // =====================================================

  async function saveProfile() {
    const token = getToken();

    if (!token) {
      handleUnauthorized();
      return;
    }

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const payload = {
        language:
          language.trim() || null,

        age:
          age.trim()
            ? Number(age)
            : null,

        marital_status:
          maritalStatus.trim() ||
          null,

        children:
          children.trim()
            ? Number(children)
            : null,

        career:
          career.trim() || null,

        financial_status:
          financialStatus.trim() ||
          null,

        main_goal:
          mainGoal.trim() || null,

        goals,
        habits,

        important_events:
          importantEvents,
      };

      const response =
        await fetch(
          `${API_URL}/profile`,
          {
            method: "PATCH",

            headers: {
              "Content-Type":
                "application/json",

              Authorization:
                `Bearer ${token}`,
            },

            body:
              JSON.stringify(
                payload
              ),
          }
        );

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            tr("Профильді сақтау кезінде қате шықты.", "Ошибка при сохранении профиля.")
        );
      }

      applyProfile(
        data as UserProfile
      );

      showSuccess(
        tr("Өзгерістер сақталды ✓", "Изменения сохранены ✓")
      );

    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError(
          tr("Белгісіз қате шықты.", "Произошла неизвестная ошибка.")
        );
      }

    } finally {
      setSaving(false);
    }
  }

  // =====================================================
  // CLEAR ONE MEMORY FIELD
  // =====================================================

  async function clearMemoryField(
    fieldName: string,
    label: string
  ) {
    const token = getToken();

    if (!token) {
      handleUnauthorized();
      return;
    }

    const confirmed =
      window.confirm(
        tr(
          `${label} бөліміндегі сақталған ақпаратты жадтан өшіреміз бе?`,
          `Удалить из памяти сохранённые сведения в разделе «${label}»?`
        )
      );

    if (!confirmed) {
      return;
    }

    setMemoryActionLoading(
      true
    );

    setError("");
    setSuccess("");

    try {
      const response =
        await fetch(
          `${API_URL}/profile/memory/${fieldName}`,
          {
            method: "DELETE",

            headers: {
              Authorization:
                `Bearer ${token}`,
            },
          }
        );

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      const data =
        await response.json();

      if (!response.ok) {
        const detail =
          typeof data.detail ===
          "string"
            ? data.detail
            : tr("Жадты тазалау кезінде қате шықты.", "Ошибка при очистке памяти.");

        throw new Error(
          detail
        );
      }

      applyProfile(
        data as UserProfile
      );

      showSuccess(
        tr(`${label} жадтан өшірілді ✓`, `«${label}» удалено из памяти ✓`)
      );

    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError(
          tr("Белгісіз қате шықты.", "Произошла неизвестная ошибка.")
        );
      }

    } finally {
      setMemoryActionLoading(
        false
      );
    }
  }

  // =====================================================
  // CLEAR ALL MEMORY
  // =====================================================

  async function clearAllMemory() {
    const token = getToken();

    if (!token) {
      handleUnauthorized();
      return;
    }

    const confirmed =
      window.confirm(
        tr("ERKEK AI сен туралы сақтаған барлық long-term memory-ді тазалаймыз ба? Аккаунт пен чаттар өшірілмейді.", "Очистить всю долгосрочную память ERKEK AI о тебе? Аккаунт и чаты не удаляются.")
      );

    if (!confirmed) {
      return;
    }

    setMemoryActionLoading(
      true
    );

    setError("");
    setSuccess("");

    try {
      const response =
        await fetch(
          `${API_URL}/profile/memory/all`,
          {
            method: "DELETE",

            headers: {
              Authorization:
                `Bearer ${token}`,
            },
          }
        );

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      const data =
        await response.json();

      if (!response.ok) {
        const detail =
          typeof data.detail ===
          "string"
            ? data.detail
            : tr("Жадты толық тазалау кезінде қате шықты.", "Ошибка при полной очистке памяти.");

        throw new Error(
          detail
        );
      }

      applyProfile(
        data as UserProfile
      );

      showSuccess(
        tr("ERKEK AI жады толық тазаланды ✓", "Память ERKEK AI полностью очищена ✓")
      );

    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError(
          tr("Белгісіз қате шықты.", "Произошла неизвестная ошибка.")
        );
      }

    } finally {
      setMemoryActionLoading(
        false
      );
    }
  }

  // =====================================================
  // ADD GOAL
  // =====================================================

  function addGoal() {
    const value =
      newGoal.trim();

    if (!value) {
      return;
    }

    if (!goals.includes(value)) {
      setGoals(
        current => [
          ...current,
          value,
        ]
      );
    }

    setNewGoal("");
  }

  // =====================================================
  // REMOVE GOAL
  // =====================================================

  function removeGoal(
    index: number
  ) {
    setGoals(
      current =>
        current.filter(
          (_, itemIndex) =>
            itemIndex !== index
        )
    );
  }

  // =====================================================
  // ADD HABIT
  // =====================================================

  function addHabit() {
    const value =
      newHabit.trim();

    if (!value) {
      return;
    }

    if (!habits.includes(value)) {
      setHabits(
        current => [
          ...current,
          value,
        ]
      );
    }

    setNewHabit("");
  }

  // =====================================================
  // REMOVE HABIT
  // =====================================================

  function removeHabit(
    index: number
  ) {
    setHabits(
      current =>
        current.filter(
          (_, itemIndex) =>
            itemIndex !== index
        )
    );
  }

  // =====================================================
  // ADD IMPORTANT EVENT
  // =====================================================

  function addImportantEvent() {
    const value =
      newImportantEvent.trim();

    if (!value) {
      return;
    }

    if (
      !importantEvents.includes(
        value
      )
    ) {
      setImportantEvents(
        current => [
          ...current,
          value,
        ]
      );
    }

    setNewImportantEvent("");
  }

  // =====================================================
  // REMOVE IMPORTANT EVENT
  // =====================================================

  function removeImportantEvent(
    index: number
  ) {
    setImportantEvents(
      current =>
        current.filter(
          (_, itemIndex) =>
            itemIndex !== index
        )
    );
  }

  // =====================================================
  // ENTER HANDLER
  // =====================================================

  function handleListEnter(
    event:
      React.KeyboardEvent<HTMLInputElement>,
    callback: () => void
  ) {
    if (
      event.nativeEvent.isComposing
    ) {
      return;
    }

    if (
      event.key === "Enter"
    ) {
      event.preventDefault();
      callback();
    }
  }

  // =====================================================
  // LOADING
  // =====================================================

  if (loading) {
    return (
      <main className="flex min-h-dvh items-center justify-center bg-black text-white">

        <div className="text-center">

          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-white font-black text-black">
            E
          </div>

          <div className="mt-4 text-sm text-neutral-500">
            {tr("Профиль жүктелуде...", "Загружаем профиль...")}
          </div>

        </div>

      </main>
    );
  }

  // =====================================================
  // UI
  // =====================================================

  return (
    <main className="min-h-dvh bg-black text-white">

      {/* HEADER */}

      <header className="sticky top-0 z-30 border-b border-neutral-900 bg-black/90 backdrop-blur">

        <div className="mx-auto flex h-16 w-full max-w-5xl items-center justify-between px-4 sm:px-6">

          <div className="flex min-w-0 items-center gap-3">

            <button
              type="button"
              onClick={() =>
                router.push("/chat")
              }
              className="
                flex
                h-10
                w-10
                shrink-0
                items-center
                justify-center
                rounded-xl
                text-xl
                text-neutral-400
                transition
                hover:bg-neutral-900
                hover:text-white
              "
              aria-label={tr("Чатқа оралу", "Назад в чат")}
            >
              ←
            </button>

            <div className="min-w-0">

              <div className="truncate font-semibold">
                {tr("Баптаулар", "Настройки")}
              </div>

              <div className="text-xs text-neutral-500">
                {tr("ERKEK AI профилі және жады", "Профиль и память ERKEK AI")}
              </div>

            </div>

          </div>

          <LanguageSwitcher className="ml-auto mr-2 shrink-0" />

          <button
            type="button"
            onClick={() =>
              router.push("/chat")
            }
            className="
              hidden
              rounded-xl
              border
              border-neutral-800
              px-4
              py-2
              text-sm
              text-neutral-300
              transition
              hover:bg-neutral-900
              hover:text-white
              sm:block
            "
          >
            {tr("Чатқа оралу", "Назад в чат")}
          </button>

        </div>

      </header>

      {/* CONTENT */}

      <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 sm:py-10">

        <div className="mb-8">

          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            {tr("Профиль және жады", "Профиль и память")}
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-neutral-500 sm:text-base">
            {tr(
              "Бұл ақпарат ERKEK AI-ға сені жақсырақ түсінуге және жауаптарды жеке жағдайыңа бейімдеуге көмектеседі.",
              "Эти сведения помогают ERKEK AI лучше понимать тебя и подстраивать ответы под твою ситуацию."
            )}
          </p>

        </div>

        {/* ERROR */}

        {error && (
          <div className="mb-6 flex items-start justify-between gap-3 rounded-xl border border-red-500/20 bg-red-500/[0.06] px-4 py-3 text-sm text-red-400">

            <span>
              {error}
            </span>

            <button
              type="button"
              onClick={() =>
                setError("")
              }
              aria-label={tr("Қатені жабу", "Закрыть ошибку")}
            >
              ×
            </button>

          </div>
        )}

        {/* SUCCESS */}

        {success && (
          <div className="mb-6 rounded-xl border border-emerald-500/20 bg-emerald-500/[0.06] px-4 py-3 text-sm text-emerald-400">
            {success}
          </div>
        )}

        <div className="space-y-6">

          {/* PERSONA */}

          {personaOptions.length > 0 && (
            <section className="rounded-2xl border border-neutral-900 bg-neutral-950 p-5 sm:p-6">

              <div className="mb-6">

                <h2 className="text-lg font-semibold">
                  {tr("ERKEK AI мінезі", "Характер ERKEK AI")}
                </h2>

                <p className="mt-1 text-sm text-neutral-500">
                  {tr(
                    "ERKEK AI саған қалай сөйлейтінін таңда. Бірден сақталады.",
                    "Выбери, как ERKEK AI будет с тобой говорить. Сохраняется сразу."
                  )}
                </p>

              </div>

              <div className="grid gap-3 sm:grid-cols-3">

                {personaOptions.map(
                  (rawOption) => {
                    const option = localizePersona(rawOption, lang);
                    const selected =
                      option.id === persona;

                    return (
                      <button
                        key={option.id}
                        type="button"
                        onClick={() =>
                          void savePersona(
                            option.id
                          )
                        }
                        disabled={
                          personaSaving
                        }
                        aria-pressed={
                          selected
                        }
                        className={
                          "rounded-xl border p-4 text-left transition disabled:cursor-wait " +
                          (selected
                            ? "border-gold-500 bg-gold-500/[0.08]"
                            : "border-neutral-800 hover:border-neutral-600")
                        }
                      >
                        <div className="font-medium">
                          {option.title}
                        </div>

                        <div className="mt-1 text-sm text-neutral-500">
                          {option.description}
                        </div>
                      </button>
                    );
                  }
                )}

              </div>

            </section>
          )}

          {/* BASIC INFO */}

          <section className="rounded-2xl border border-neutral-900 bg-neutral-950 p-5 sm:p-6">

            <div className="mb-6">

              <h2 className="text-lg font-semibold">
                {tr("Негізгі ақпарат", "Основная информация")}
              </h2>

              <p className="mt-1 text-sm text-neutral-500">
                {tr(
                  "ERKEK AI пайдаланушы туралы негізгі контекст ретінде қолданады.",
                  "ERKEK AI использует это как основной контекст о тебе."
                )}
              </p>

            </div>

            <div className="grid gap-5 sm:grid-cols-2">

              {/* LANGUAGE */}

              <div>

                <label className="mb-2 block text-sm text-neutral-400">
                  {tr("Тіл", "Язык")}
                </label>

                <select
                  value={language}
                  onChange={event =>
                    setLanguage(
                      event.target.value
                    )
                  }
                  className="
                    w-full
                    rounded-xl
                    border
                    border-neutral-800
                    bg-black
                    px-4
                    py-3
                    text-sm
                    text-white
                    outline-none
                    transition
                    focus:border-neutral-600
                  "
                >
                  <option value="">
                    {tr("Таңдалмаған", "Не выбран")}
                  </option>

                  <option value="kk">
                    Қазақша
                  </option>

                  <option value="ru">
                    Русский
                  </option>

                  <option value="en">
                    English
                  </option>
                </select>

              </div>

              {/* AGE */}

              <div>

                <label className="mb-2 block text-sm text-neutral-400">
                  {tr("Жас", "Возраст")}
                </label>

                <input
                  type="number"
                  min="1"
                  max="120"
                  value={age}
                  onChange={event =>
                    setAge(
                      event.target.value
                    )
                  }
                  placeholder={tr("Мысалы: 32", "Например: 32")}
                  className="
                    w-full
                    rounded-xl
                    border
                    border-neutral-800
                    bg-black
                    px-4
                    py-3
                    text-sm
                    text-white
                    outline-none
                    placeholder:text-neutral-700
                    focus:border-neutral-600
                  "
                />

                {!!age && (
                  <button
                    type="button"
                    disabled={
                      memoryActionLoading
                    }
                    onClick={() =>
                      clearMemoryField(
                        "age",
                        tr("Жас", "Возраст")
                      )
                    }
                    className="mt-2 text-xs text-neutral-600 transition hover:text-red-400 disabled:opacity-40"
                  >
                    {tr("Жадтан өшіру", "Удалить из памяти")}
                  </button>
                )}

              </div>

              {/* MARITAL STATUS */}

              <div>

                <label className="mb-2 block text-sm text-neutral-400">
                  {tr("Отбасылық жағдай", "Семейное положение")}
                </label>

                <input
                  value={maritalStatus}
                  onChange={event =>
                    setMaritalStatus(
                      event.target.value
                    )
                  }
                  placeholder={tr("Мысалы: үйленген", "Например: женат")}
                  className="
                    w-full
                    rounded-xl
                    border
                    border-neutral-800
                    bg-black
                    px-4
                    py-3
                    text-sm
                    text-white
                    outline-none
                    placeholder:text-neutral-700
                    focus:border-neutral-600
                  "
                />

                {!!maritalStatus && (
                  <button
                    type="button"
                    disabled={
                      memoryActionLoading
                    }
                    onClick={() =>
                      clearMemoryField(
                        "marital_status",
                        tr("Отбасылық жағдай", "Семейное положение")
                      )
                    }
                    className="mt-2 text-xs text-neutral-600 transition hover:text-red-400 disabled:opacity-40"
                  >
                    {tr("Жадтан өшіру", "Удалить из памяти")}
                  </button>
                )}

              </div>

              {/* CHILDREN */}

              <div>

                <label className="mb-2 block text-sm text-neutral-400">
                  {tr("Балалар саны", "Количество детей")}
                </label>

                <input
                  type="number"
                  min="0"
                  value={children}
                  onChange={event =>
                    setChildren(
                      event.target.value
                    )
                  }
                  placeholder={tr("Мысалы: 2", "Например: 2")}
                  className="
                    w-full
                    rounded-xl
                    border
                    border-neutral-800
                    bg-black
                    px-4
                    py-3
                    text-sm
                    text-white
                    outline-none
                    placeholder:text-neutral-700
                    focus:border-neutral-600
                  "
                />

                {children !== "" && (
                  <button
                    type="button"
                    disabled={
                      memoryActionLoading
                    }
                    onClick={() =>
                      clearMemoryField(
                        "children",
                        tr("Балалар саны", "Количество детей")
                      )
                    }
                    className="mt-2 text-xs text-neutral-600 transition hover:text-red-400 disabled:opacity-40"
                  >
                    {tr("Жадтан өшіру", "Удалить из памяти")}
                  </button>
                )}

              </div>

            </div>

          </section>

          {/* LIFE CONTEXT */}

          <section className="rounded-2xl border border-neutral-900 bg-neutral-950 p-5 sm:p-6">

            <div className="mb-6">

              <h2 className="text-lg font-semibold">
                {tr("Өмірлік контекст", "Жизненный контекст")}
              </h2>

              <p className="mt-1 text-sm text-neutral-500">
                {tr(
                  "Жұмыс, қаржы және негізгі мақсат туралы ақпарат.",
                  "Сведения о работе, финансах и главной цели."
                )}
              </p>

            </div>

            <div className="space-y-5">

              {/* CAREER */}

              <div>

                <label className="mb-2 block text-sm text-neutral-400">
                  {tr("Жұмыс / мансап", "Работа / карьера")}
                </label>

                <textarea
                  value={career}
                  onChange={event =>
                    setCareer(
                      event.target.value
                    )
                  }
                  rows={3}
                  placeholder={tr("Қазіргі жұмысың, мамандығың немесе мансаптық жағдайың...", "Твоя текущая работа, профессия или карьерная ситуация...")}
                  className="
                    w-full
                    resize-none
                    rounded-xl
                    border
                    border-neutral-800
                    bg-black
                    px-4
                    py-3
                    text-sm
                    leading-6
                    text-white
                    outline-none
                    placeholder:text-neutral-700
                    focus:border-neutral-600
                  "
                />

                {!!career && (
                  <button
                    type="button"
                    disabled={
                      memoryActionLoading
                    }
                    onClick={() =>
                      clearMemoryField(
                        "career",
                        tr("Жұмыс / мансап", "Работа / карьера")
                      )
                    }
                    className="mt-2 text-xs text-neutral-600 transition hover:text-red-400 disabled:opacity-40"
                  >
                    {tr("Жадтан өшіру", "Удалить из памяти")}
                  </button>
                )}

              </div>

              {/* FINANCIAL */}

              <div>

                <label className="mb-2 block text-sm text-neutral-400">
                  {tr("Қаржылық жағдай", "Финансовое положение")}
                </label>

                <textarea
                  value={financialStatus}
                  onChange={event =>
                    setFinancialStatus(
                      event.target.value
                    )
                  }
                  rows={3}
                  placeholder={tr("Қаржыға қатысты маңызды контекст...", "Важный контекст о финансах...")}
                  className="
                    w-full
                    resize-none
                    rounded-xl
                    border
                    border-neutral-800
                    bg-black
                    px-4
                    py-3
                    text-sm
                    leading-6
                    text-white
                    outline-none
                    placeholder:text-neutral-700
                    focus:border-neutral-600
                  "
                />

                {!!financialStatus && (
                  <button
                    type="button"
                    disabled={
                      memoryActionLoading
                    }
                    onClick={() =>
                      clearMemoryField(
                        "financial_status",
                        tr("Қаржылық жағдай", "Финансовое положение")
                      )
                    }
                    className="mt-2 text-xs text-neutral-600 transition hover:text-red-400 disabled:opacity-40"
                  >
                    {tr("Жадтан өшіру", "Удалить из памяти")}
                  </button>
                )}

              </div>

              {/* MAIN GOAL */}

              <div>

                <label className="mb-2 block text-sm text-neutral-400">
                  {tr("Негізгі мақсат", "Главная цель")}
                </label>

                <textarea
                  value={mainGoal}
                  onChange={event =>
                    setMainGoal(
                      event.target.value
                    )
                  }
                  rows={3}
                  placeholder={tr("Қазір сен үшін ең маңызды мақсат...", "Самая важная для тебя цель сейчас...")}
                  className="
                    w-full
                    resize-none
                    rounded-xl
                    border
                    border-neutral-800
                    bg-black
                    px-4
                    py-3
                    text-sm
                    leading-6
                    text-white
                    outline-none
                    placeholder:text-neutral-700
                    focus:border-neutral-600
                  "
                />

                {!!mainGoal && (
                  <button
                    type="button"
                    disabled={
                      memoryActionLoading
                    }
                    onClick={() =>
                      clearMemoryField(
                        "main_goal",
                        tr("Негізгі мақсат", "Главная цель")
                      )
                    }
                    className="mt-2 text-xs text-neutral-600 transition hover:text-red-400 disabled:opacity-40"
                  >
                    {tr("Жадтан өшіру", "Удалить из памяти")}
                  </button>
                )}

              </div>

            </div>

          </section>

          {/* GOALS */}

          <MemorySection
            title={tr("Мақсаттар", "Цели")}
            description={tr("ERKEK AI есте сақтайтын мақсаттар.", "Цели, которые запоминает ERKEK AI.")}
            fieldName="goals"
            items={goals}
            value={newGoal}
            placeholder={tr("Жаңа мақсат...", "Новая цель...")}
            onChange={setNewGoal}
            onAdd={addGoal}
            onRemove={removeGoal}
            onEnter={handleListEnter}
            onClear={clearMemoryField}
            disabled={
              memoryActionLoading
            }
          />

          {/* HABITS */}

          <MemorySection
            title={tr("Әдеттер", "Привычки")}
            description={tr("Күнделікті немесе тұрақты әдеттер.", "Ежедневные или постоянные привычки.")}
            fieldName="habits"
            items={habits}
            value={newHabit}
            placeholder={tr("Жаңа әдет...", "Новая привычка...")}
            onChange={setNewHabit}
            onAdd={addHabit}
            onRemove={removeHabit}
            onEnter={handleListEnter}
            onClear={clearMemoryField}
            disabled={
              memoryActionLoading
            }
          />

          {/* IMPORTANT EVENTS */}

          <MemorySection
            title={tr("Маңызды оқиғалар", "Важные события")}
            description={tr("AI болашақ әңгімелерде ескеруі тиіс маңызды оқиғалар.", "Важные события, которые ИИ должен учитывать в будущих разговорах.")}
            fieldName="important_events"
            items={importantEvents}
            value={newImportantEvent}
            placeholder={tr("Маңызды оқиға...", "Важное событие...")}
            onChange={
              setNewImportantEvent
            }
            onAdd={
              addImportantEvent
            }
            onRemove={
              removeImportantEvent
            }
            onEnter={
              handleListEnter
            }
            onClear={
              clearMemoryField
            }
            disabled={
              memoryActionLoading
            }
          />

          {/* MEMORY DANGER ZONE */}

          <section className="rounded-2xl border border-red-500/15 bg-red-500/[0.03] p-5 sm:p-6">

            <h2 className="text-lg font-semibold">
              {tr("Жадты басқару", "Управление памятью")}
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-neutral-500">
              {tr(
                "Бұл әрекет ERKEK AI сен туралы сақтаған long-term memory-ді тазартады. Аккаунт пен әңгімелер өшірілмейді. Тіл параметрі сақталады.",
                "Это действие очистит долгосрочную память ERKEK AI о тебе. Аккаунт и разговоры не удаляются. Настройка языка сохранится."
              )}
            </p>

            <button
              type="button"
              onClick={
                clearAllMemory
              }
              disabled={
                saving ||
                memoryActionLoading
              }
              className="
                mt-5
                rounded-xl
                border
                border-red-500/20
                bg-red-500/[0.06]
                px-4
                py-3
                text-sm
                font-medium
                text-red-400
                transition
                hover:bg-red-500/[0.12]
                hover:text-red-300
                disabled:cursor-not-allowed
                disabled:opacity-40
              "
            >
              {memoryActionLoading
                ? tr("Орындалуда...", "Выполняется...")
                : tr("Барлық жадты тазалау", "Очистить всю память")}
            </button>

          </section>

          {/* TELEGRAM */}

          <TelegramLinkSection
            onUnauthorized={
              handleUnauthorized
            }
          />

          {/* DELETE ACCOUNT */}

          <DeleteAccountSection
            onUnauthorized={
              handleUnauthorized
            }
          />

          {/* SAVE */}

          <div className="sticky bottom-0 z-20 border-t border-neutral-900 bg-black/90 py-4 backdrop-blur">

            <div className="flex items-center justify-between gap-4">

              <div className="hidden text-xs text-neutral-600 sm:block">
                {tr(
                  "Өзгерістер автоматты түрде сақталмайды.",
                  "Изменения не сохраняются автоматически."
                )}
              </div>

              <button
                type="button"
                onClick={
                  saveProfile
                }
                disabled={
                  saving ||
                  memoryActionLoading
                }
                className="
                  ml-auto
                  rounded-xl
                  bg-white
                  px-6
                  py-3
                  text-sm
                  font-medium
                  text-black
                  transition
                  hover:bg-neutral-200
                  disabled:cursor-not-allowed
                  disabled:opacity-50
                "
              >
                {saving
                  ? tr("Сақталуда...", "Сохраняем...")
                  : tr("Өзгерістерді сақтау", "Сохранить изменения")}
              </button>

            </div>

          </div>

        </div>

      </div>

    </main>
  );
}


// =====================================================
// MEMORY SECTION
// =====================================================

function MemorySection({
  title,
  description,
  fieldName,
  items,
  value,
  placeholder,
  onChange,
  onAdd,
  onRemove,
  onEnter,
  onClear,
  disabled,
}: {
  title: string;
  description: string;
  fieldName: string;

  items: string[];

  value: string;
  placeholder: string;

  onChange:
    (value: string) => void;

  onAdd:
    () => void;

  onRemove:
    (index: number) => void;

  onEnter:
    (
      event:
        React.KeyboardEvent<HTMLInputElement>,
      callback: () => void
    ) => void;

  onClear:
    (
      fieldName: string,
      label: string
    ) => void;

  disabled: boolean;
}) {
  const { tr } = useLang();

  return (
    <section className="rounded-2xl border border-neutral-900 bg-neutral-950 p-5 sm:p-6">

      <div className="mb-5 flex items-start justify-between gap-4">

        <div>

          <h2 className="text-lg font-semibold">
            {title}
          </h2>

          <p className="mt-1 text-sm text-neutral-500">
            {description}
          </p>

        </div>

        {items.length > 0 && (
          <button
            type="button"
            onClick={() =>
              onClear(
                fieldName,
                title
              )
            }
            disabled={
              disabled
            }
            className="
              shrink-0
              rounded-lg
              px-2
              py-1
              text-xs
              text-neutral-600
              transition
              hover:bg-red-500/[0.06]
              hover:text-red-400
              disabled:cursor-not-allowed
              disabled:opacity-40
            "
          >
            {tr("Тазалау", "Очистить")}
          </button>
        )}

      </div>

      {/* ITEMS */}

      {items.length > 0 ? (

        <div className="mb-5 space-y-2">

          {items.map(
            (
              item,
              index
            ) => (
              <div
                key={`${item}-${index}`}
                className="
                  group
                  flex
                  items-start
                  justify-between
                  gap-3
                  rounded-xl
                  border
                  border-white/[0.06]
                  bg-black
                  px-4
                  py-3
                "
              >

                <div className="min-w-0 break-words text-sm leading-6 text-neutral-300">
                  {item}
                </div>

                <button
                  type="button"
                  onClick={() =>
                    onRemove(
                      index
                    )
                  }
                  disabled={
                    disabled
                  }
                  className="
                    shrink-0
                    rounded-lg
                    px-2
                    py-1
                    text-sm
                    text-neutral-700
                    transition
                    hover:bg-red-500/[0.08]
                    hover:text-red-400
                    disabled:cursor-not-allowed
                    disabled:opacity-40
                  "
                  aria-label={tr(`${title}: элементті өшіру`, `${title}: удалить элемент`)}
                >
                  ×
                </button>

              </div>
            )
          )}

        </div>

      ) : (

        <div className="mb-5 rounded-xl border border-dashed border-neutral-800 px-4 py-5 text-center text-sm text-neutral-600">
          {tr("Әзірге ештеңе сақталмаған.", "Пока ничего не сохранено.")}
        </div>

      )}

      {/* ADD */}

      <div className="flex gap-2">

        <input
          value={value}
          onChange={event =>
            onChange(
              event.target.value
            )
          }
          onKeyDown={event =>
            onEnter(
              event,
              onAdd
            )
          }
          disabled={
            disabled
          }
          placeholder={
            placeholder
          }
          className="
            min-w-0
            flex-1
            rounded-xl
            border
            border-neutral-800
            bg-black
            px-4
            py-3
            text-sm
            text-white
            outline-none
            placeholder:text-neutral-700
            focus:border-neutral-600
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        />

        <button
          type="button"
          onClick={
            onAdd
          }
          disabled={
            disabled ||
            !value.trim()
          }
          className="
            shrink-0
            rounded-xl
            border
            border-neutral-800
            px-4
            py-3
            text-sm
            text-neutral-300
            transition
            hover:bg-neutral-900
            hover:text-white
            disabled:cursor-not-allowed
            disabled:opacity-30
          "
        >
          {tr("Қосу", "Добавить")}
        </button>

      </div>

    </section>
  );
}