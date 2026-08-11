"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

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

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

// =====================================================
// SETTINGS PAGE
// =====================================================

export default function SettingsPage() {
  const router = useRouter();

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
  // AUTH CHECK + LOAD PROFILE
  // =====================================================

  useEffect(() => {
    const token =
      localStorage.getItem(
        "access_token"
      );

    if (!token) {
      router.replace("/login");
      return;
    }

    void loadProfile();
  }, [router]);

  // =====================================================
  // TOKEN
  // =====================================================

  function getToken() {
    return localStorage.getItem(
      "access_token"
    );
  }

  // =====================================================
  // UNAUTHORIZED
  // =====================================================

  function handleUnauthorized() {
    localStorage.removeItem(
      "access_token"
    );

    router.replace("/login");
  }

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

    setLoading(true);
    setError("");

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
            "Профильді жүктеу кезінде қате шықты."
        );
      }

      applyProfile(
        data as UserProfile
      );

    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError(
          "Белгісіз қате шықты."
        );
      }

    } finally {
      setLoading(false);
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
            "Профильді сақтау кезінде қате шықты."
        );
      }

      applyProfile(
        data as UserProfile
      );

      showSuccess(
        "Өзгерістер сақталды ✓"
      );

    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError(
          "Белгісіз қате шықты."
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
        `${label} бөліміндегі сақталған ақпаратты жадтан өшіреміз бе?`
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
            : "Жадты тазалау кезінде қате шықты.";

        throw new Error(
          detail
        );
      }

      applyProfile(
        data as UserProfile
      );

      showSuccess(
        `${label} жадтан өшірілді ✓`
      );

    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError(
          "Белгісіз қате шықты."
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
        "ERKEK AI сен туралы сақтаған барлық long-term memory-ді тазалаймыз ба? Аккаунт пен чаттар өшірілмейді."
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
            : "Жадты толық тазалау кезінде қате шықты.";

        throw new Error(
          detail
        );
      }

      applyProfile(
        data as UserProfile
      );

      showSuccess(
        "ERKEK AI жады толық тазаланды ✓"
      );

    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError(
          "Белгісіз қате шықты."
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
            Профиль жүктелуде...
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
              aria-label="Чатқа оралу"
            >
              ←
            </button>

            <div className="min-w-0">

              <div className="truncate font-semibold">
                Баптаулар
              </div>

              <div className="text-xs text-neutral-500">
                ERKEK AI профилі және жады
              </div>

            </div>

          </div>

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
            Чатқа оралу
          </button>

        </div>

      </header>

      {/* CONTENT */}

      <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 sm:py-10">

        <div className="mb-8">

          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            Профиль және жады
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-neutral-500 sm:text-base">
            Бұл ақпарат ERKEK AI-ға
            сені жақсырақ түсінуге және
            жауаптарды жеке жағдайыңа
            бейімдеуге көмектеседі.
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
              aria-label="Қатені жабу"
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

          {/* BASIC INFO */}

          <section className="rounded-2xl border border-neutral-900 bg-neutral-950 p-5 sm:p-6">

            <div className="mb-6">

              <h2 className="text-lg font-semibold">
                Негізгі ақпарат
              </h2>

              <p className="mt-1 text-sm text-neutral-500">
                ERKEK AI пайдаланушы туралы
                негізгі контекст ретінде қолданады.
              </p>

            </div>

            <div className="grid gap-5 sm:grid-cols-2">

              {/* LANGUAGE */}

              <div>

                <label className="mb-2 block text-sm text-neutral-400">
                  Тіл
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
                    Таңдалмаған
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
                  Жас
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
                  placeholder="Мысалы: 32"
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
                        "Жас"
                      )
                    }
                    className="mt-2 text-xs text-neutral-600 transition hover:text-red-400 disabled:opacity-40"
                  >
                    Жадтан өшіру
                  </button>
                )}

              </div>

              {/* MARITAL STATUS */}

              <div>

                <label className="mb-2 block text-sm text-neutral-400">
                  Отбасылық жағдай
                </label>

                <input
                  value={maritalStatus}
                  onChange={event =>
                    setMaritalStatus(
                      event.target.value
                    )
                  }
                  placeholder="Мысалы: үйленген"
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
                        "Отбасылық жағдай"
                      )
                    }
                    className="mt-2 text-xs text-neutral-600 transition hover:text-red-400 disabled:opacity-40"
                  >
                    Жадтан өшіру
                  </button>
                )}

              </div>

              {/* CHILDREN */}

              <div>

                <label className="mb-2 block text-sm text-neutral-400">
                  Балалар саны
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
                  placeholder="Мысалы: 2"
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
                        "Балалар саны"
                      )
                    }
                    className="mt-2 text-xs text-neutral-600 transition hover:text-red-400 disabled:opacity-40"
                  >
                    Жадтан өшіру
                  </button>
                )}

              </div>

            </div>

          </section>

          {/* LIFE CONTEXT */}

          <section className="rounded-2xl border border-neutral-900 bg-neutral-950 p-5 sm:p-6">

            <div className="mb-6">

              <h2 className="text-lg font-semibold">
                Өмірлік контекст
              </h2>

              <p className="mt-1 text-sm text-neutral-500">
                Жұмыс, қаржы және негізгі
                мақсат туралы ақпарат.
              </p>

            </div>

            <div className="space-y-5">

              {/* CAREER */}

              <div>

                <label className="mb-2 block text-sm text-neutral-400">
                  Жұмыс / мансап
                </label>

                <textarea
                  value={career}
                  onChange={event =>
                    setCareer(
                      event.target.value
                    )
                  }
                  rows={3}
                  placeholder="Қазіргі жұмысың, мамандығың немесе мансаптық жағдайың..."
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
                        "Жұмыс / мансап"
                      )
                    }
                    className="mt-2 text-xs text-neutral-600 transition hover:text-red-400 disabled:opacity-40"
                  >
                    Жадтан өшіру
                  </button>
                )}

              </div>

              {/* FINANCIAL */}

              <div>

                <label className="mb-2 block text-sm text-neutral-400">
                  Қаржылық жағдай
                </label>

                <textarea
                  value={financialStatus}
                  onChange={event =>
                    setFinancialStatus(
                      event.target.value
                    )
                  }
                  rows={3}
                  placeholder="Қаржыға қатысты маңызды контекст..."
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
                        "Қаржылық жағдай"
                      )
                    }
                    className="mt-2 text-xs text-neutral-600 transition hover:text-red-400 disabled:opacity-40"
                  >
                    Жадтан өшіру
                  </button>
                )}

              </div>

              {/* MAIN GOAL */}

              <div>

                <label className="mb-2 block text-sm text-neutral-400">
                  Негізгі мақсат
                </label>

                <textarea
                  value={mainGoal}
                  onChange={event =>
                    setMainGoal(
                      event.target.value
                    )
                  }
                  rows={3}
                  placeholder="Қазір сен үшін ең маңызды мақсат..."
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
                        "Негізгі мақсат"
                      )
                    }
                    className="mt-2 text-xs text-neutral-600 transition hover:text-red-400 disabled:opacity-40"
                  >
                    Жадтан өшіру
                  </button>
                )}

              </div>

            </div>

          </section>

          {/* GOALS */}

          <MemorySection
            title="Мақсаттар"
            description="ERKEK AI есте сақтайтын мақсаттар."
            fieldName="goals"
            items={goals}
            value={newGoal}
            placeholder="Жаңа мақсат..."
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
            title="Әдеттер"
            description="Күнделікті немесе тұрақты әдеттер."
            fieldName="habits"
            items={habits}
            value={newHabit}
            placeholder="Жаңа әдет..."
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
            title="Маңызды оқиғалар"
            description="AI болашақ әңгімелерде ескеруі тиіс маңызды оқиғалар."
            fieldName="important_events"
            items={importantEvents}
            value={newImportantEvent}
            placeholder="Маңызды оқиға..."
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
              Жадты басқару
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-neutral-500">
              Бұл әрекет ERKEK AI сен туралы
              сақтаған long-term memory-ді
              тазартады. Аккаунт пен әңгімелер
              өшірілмейді. Тіл параметрі
              сақталады.
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
                ? "Орындалуда..."
                : "Барлық жадты тазалау"}
            </button>

          </section>

          {/* SAVE */}

          <div className="sticky bottom-0 z-20 border-t border-neutral-900 bg-black/90 py-4 backdrop-blur">

            <div className="flex items-center justify-between gap-4">

              <div className="hidden text-xs text-neutral-600 sm:block">
                Өзгерістер автоматты түрде
                сақталмайды.
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
                  ? "Сақталуда..."
                  : "Өзгерістерді сақтау"}
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
            Тазалау
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
                  aria-label={`${title}: элементті өшіру`}
                >
                  ×
                </button>

              </div>
            )
          )}

        </div>

      ) : (

        <div className="mb-5 rounded-xl border border-dashed border-neutral-800 px-4 py-5 text-center text-sm text-neutral-600">
          Әзірге ештеңе сақталмаған.
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
          Қосу
        </button>

      </div>

    </section>
  );
}