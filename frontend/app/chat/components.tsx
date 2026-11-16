"use client";

import { useEffect, useRef, useState } from "react";

import { getValidToken } from "@/lib/auth";
import { useLang, type Lang } from "@/lib/i18n";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";


// =====================================================
// LOGO MARK
// =====================================================

export function LogoMark({
  size = "md",
}: {
  size?: "sm" | "md" | "lg";
}) {
  const sizes = {
    sm: "h-7 w-7 rounded-lg text-sm",
    md: "h-9 w-9 rounded-xl text-base",
    lg: "h-14 w-14 rounded-2xl text-2xl",
  };

  return (
    <div
      className={`flex shrink-0 items-center justify-center bg-white font-display font-bold text-black ${sizes[size]}`}
    >
      E
    </div>
  );
}


// =====================================================
// WELCOME / STARTER PROMPTS
// =====================================================

type Topic = { icon: string; title: string; prompt: string };

const TOPICS: Record<Lang, Topic[]> = {
  kk: [
    {
      icon: "💼",
      title: "Жұмыс",
      prompt:
        "Жұмысымды ауыстырғым келеді, бірақ неден бастарымды білмеймін.",
    },
    {
      icon: "💰",
      title: "Қаржы",
      prompt:
        "Қарызым бар және ақшам айдың соңына жетпейді. Жоспар құруға көмектес.",
    },
    {
      icon: "👨‍👧",
      title: "Отбасы",
      prompt:
        "Балаларыммен жақсы қарым-қатынас орнатқым келеді, уақытым аз.",
    },
    {
      icon: "🎯",
      title: "Мақсат",
      prompt:
        "Осы жылға нақты мақсаттар қойып, оларды қадамдарға бөлгім келеді.",
    },
    {
      icon: "⚡",
      title: "Тәртіп",
      prompt:
        "Бастаған ісімді аяғына дейін жеткізе алмаймын. Қалай тәртіпке келемін?",
    },
    {
      icon: "🧭",
      title: "Ой",
      prompt:
        "Соңғы кезде бір мәселе мазалап жүр, ойымды реттеуге көмектес.",
    },
  ],
  ru: [
    {
      icon: "💼",
      title: "Работа",
      prompt:
        "Хочу сменить работу, но не знаю, с чего начать.",
    },
    {
      icon: "💰",
      title: "Деньги",
      prompt:
        "У меня есть долги, и денег не хватает до конца месяца. Помоги составить план.",
    },
    {
      icon: "👨‍👧",
      title: "Семья",
      prompt:
        "Хочу наладить отношения с детьми, но у меня мало времени.",
    },
    {
      icon: "🎯",
      title: "Цели",
      prompt:
        "Хочу поставить конкретные цели на этот год и разбить их на шаги.",
    },
    {
      icon: "⚡",
      title: "Дисциплина",
      prompt:
        "Не могу довести начатое до конца. Как стать дисциплинированнее?",
    },
    {
      icon: "🧭",
      title: "Мысли",
      prompt:
        "В последнее время меня беспокоит одна проблема, помоги разложить мысли по полочкам.",
    },
  ],
};


// Persona атаулары backend-тен қазақша келеді — тілге қарай ауыстырамыз.
const PERSONA_TEXT: Record<string, Record<Lang, { title: string; description: string }>> = {
  brother: {
    kk: {
      title: "Аға / Брат",
      description: "Жылы аға: өміріңді есте сақтайды, жеңістеріңді атайды, тура сөйлейді.",
    },
    ru: {
      title: "Брат",
      description: "Тёплый старший брат: помнит твою жизнь, отмечает победы, говорит прямо.",
    },
  },
  hardcore: {
    kk: {
      title: "Қатал / Жёсткий",
      description: "Сүзгісіз, матпен: үкім, механикасын талдау және нақты ережелер.",
    },
    ru: {
      title: "Жёсткий",
      description: "Без фильтров и с матом: вердикт, разбор механики и чёткие правила.",
    },
  },
  strategist: {
    kk: {
      title: "Стратег",
      description: "Салқын талдау: фактілер, варианттар, тәуекелдер және келесі қадам.",
    },
    ru: {
      title: "Стратег",
      description: "Холодный анализ: факты, варианты, риски и следующий шаг.",
    },
  },
};

export function localizePersona<T extends { id: string; title: string; description: string }>(
  option: T,
  lang: Lang
): T {
  const text = PERSONA_TEXT[option.id]?.[lang];
  return text ? { ...option, ...text } : option;
}


export function ChatWelcome({
  onPick,
}: {
  onPick: (prompt: string) => void;
}) {
  const { tr, lang } = useLang();

  return (
    <div className="flex min-h-[58vh] flex-col items-center justify-center px-2 py-6 text-center">

      <LogoMark size="lg" />

      <h1 className="mt-6 text-3xl font-semibold sm:text-4xl">
        {tr("Не туралы", "О чём")}
        <span className="text-gold-gradient italic">
          {tr(" сөйлесеміз?", " поговорим?")}
        </span>
      </h1>

      <p className="mt-3 max-w-md text-sm leading-6 text-neutral-400 sm:text-base">
        {tr(
          "Тақырыпты таңда немесе ойыңды төменге еркін жаз.",
          "Выбери тему или просто напиши, что на душе."
        )}
      </p>


      <div className="mt-8 grid w-full max-w-2xl grid-cols-2 gap-2.5 sm:grid-cols-3">

        {TOPICS[lang].map((topic) => (
          <button
            key={topic.title}
            type="button"
            onClick={() => onPick(topic.prompt)}
            className="group flex flex-col items-start gap-2 rounded-2xl border border-neutral-800 bg-neutral-950 p-4 text-left transition hover:border-gold-500/40 hover:bg-neutral-900"
          >
            <span className="text-xl" aria-hidden>
              {topic.icon}
            </span>

            <span className="text-sm font-semibold text-neutral-100 transition group-hover:text-gold-300">
              {topic.title}
            </span>

            <span className="line-clamp-2 text-xs leading-5 text-neutral-500">
              {topic.prompt}
            </span>
          </button>
        ))}

      </div>

    </div>
  );
}


// =====================================================
// PERSONA SWITCHER
// =====================================================

type PersonaOption = {
  id: string;
  title: string;
  description: string;
};


export function PersonaSwitcher({
  onUnauthorized,
}: {
  onUnauthorized: () => void;
}) {
  const [persona, setPersona] =
    useState<string | null>(null);

  const [options, setOptions] =
    useState<PersonaOption[]>([]);

  const [open, setOpen] =
    useState(false);

  const [saving, setSaving] =
    useState(false);

  const rootRef =
    useRef<HTMLDivElement>(null);

  const { tr, lang } = useLang();


  useEffect(() => {
    const token = getValidToken();

    if (!token) {
      return;
    }

    fetch(`${API_URL}/profile/persona`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (response) => {
        if (response.status === 401) {
          onUnauthorized();
          return;
        }

        if (!response.ok) {
          return;
        }

        const data = await response.json();
        setPersona(data.persona);
        setOptions(data.options || []);
      })
      .catch(() => {
        // Кейіпкерді жүктеу міндетті емес — чат онсыз да жұмыс істейді.
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);


  // Сыртқа басқанда мәзірді жабу
  useEffect(() => {
    if (!open) {
      return;
    }

    function handleClick(event: MouseEvent) {
      if (
        rootRef.current &&
        !rootRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    }

    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleKey);

    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleKey);
    };
  }, [open]);


  async function choose(id: string) {
    setOpen(false);

    if (id === persona) {
      return;
    }

    const token = getValidToken();

    if (!token) {
      onUnauthorized();
      return;
    }

    const previous = persona;
    setPersona(id);
    setSaving(true);

    try {
      const response = await fetch(
        `${API_URL}/profile/persona`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ persona: id }),
        }
      );

      if (response.status === 401) {
        onUnauthorized();
        return;
      }

      if (!response.ok) {
        setPersona(previous);
      }
    } catch {
      setPersona(previous);
    } finally {
      setSaving(false);
    }
  }


  const current = options.find(
    (option) => option.id === persona
  );

  if (!current) {
    return null;
  }


  return (
    <div ref={rootRef} className="relative">

      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className="flex items-center gap-2 rounded-full border border-gold-500/25 bg-gold-500/[0.06] px-3 py-1.5 text-xs font-medium text-gold-300 transition hover:border-gold-500/50 sm:text-sm"
      >
        <span className="text-[9px] text-gold-500">◆</span>

        <span className="max-w-28 truncate sm:max-w-none">
          {localizePersona(current, lang).title}
        </span>

        <span
          className={`text-[10px] text-gold-500/70 transition ${open ? "rotate-180" : ""} ${saving ? "animate-pulse" : ""}`}
          aria-hidden
        >
          ▾
        </span>
      </button>


      {open && (
        <div
          role="listbox"
          className="absolute right-0 top-full z-40 mt-2 w-72 overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-950 p-1.5 shadow-2xl"
        >
          <div className="px-3 pb-1 pt-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-gold-500/80">
            {tr("ERKEK AI мінезі", "Характер ERKEK AI")}
          </div>

          {options.map((rawOption) => {
            const option = localizePersona(rawOption, lang);
            const selected = option.id === persona;

            return (
              <button
                key={option.id}
                type="button"
                role="option"
                aria-selected={selected}
                onClick={() => choose(option.id)}
                className={`flex w-full flex-col gap-0.5 rounded-xl px-3 py-2.5 text-left transition ${
                  selected
                    ? "bg-gold-500/[0.1]"
                    : "hover:bg-neutral-900"
                }`}
              >
                <span
                  className={`flex items-center gap-2 text-sm font-semibold ${
                    selected ? "text-gold-300" : "text-neutral-100"
                  }`}
                >
                  {option.title}
                  {selected && (
                    <span className="text-xs text-gold-400">✓</span>
                  )}
                </span>

                <span className="text-xs leading-5 text-neutral-500">
                  {option.description}
                </span>
              </button>
            );
          })}
        </div>
      )}

    </div>
  );
}


// =====================================================
// DAILY USAGE HINT
// =====================================================

type UsageInfo = {
  used: number;
  limit: number;
  remaining: number;
  resets_at: string;
};

// Осыдан аз қалғанда ғана ескертеміз.
const USAGE_WARN_AT = 10;


export function UsageHint({ busy }: { busy: boolean }) {
  const [usage, setUsage] =
    useState<UsageInfo | null>(null);

  const { tr, lang } = useLang();

  // Жауап аяқталған сайын (busy → false) қайта сұраймыз.
  useEffect(() => {
    if (busy) {
      return;
    }

    const token = getValidToken();

    if (!token) {
      return;
    }

    let cancelled = false;

    fetch(`${API_URL}/usage/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (!cancelled && data) {
          setUsage(data);
        }
      })
      .catch(() => {
        // Міндетті емес ақпарат — қате болса көрсетпейміз.
      });

    return () => {
      cancelled = true;
    };
  }, [busy]);


  if (!usage || usage.remaining > USAGE_WARN_AT) {
    return null;
  }

  if (usage.remaining <= 0) {
    const resetTime = new Date(usage.resets_at).toLocaleTimeString(
      lang === "ru" ? "ru-RU" : "kk-KZ",
      { hour: "2-digit", minute: "2-digit" }
    );

    return (
      <div className="mb-2 rounded-xl border border-gold-500/25 bg-gold-500/[0.07] px-4 py-2.5 text-center text-xs leading-5 text-gold-200 sm:text-sm">
        {tr(
          `Бүгінгі ${usage.limit} хабарлама лимиті бітті. Ертең ${resetTime}-та қайта жалғастырамыз.`,
          `Дневной лимит в ${usage.limit} сообщений исчерпан. Продолжим завтра в ${resetTime}.`
        )}
      </div>
    );
  }

  return (
    <div className="mb-2 text-center text-xs text-gold-500/80">
      {tr(
        `Бүгін ${usage.remaining} хабарлама қалды`,
        `Сегодня осталось сообщений: ${usage.remaining}`
      )}
    </div>
  );
}


// =====================================================
// FEEDBACK (👍 / 👎)
// =====================================================

const DISLIKE_REASONS: { id: string; kk: string; ru: string }[] = [
  { id: "not_understood", kk: "Түсінбеді", ru: "Не понял меня" },
  { id: "too_long", kk: "Тым ұзақ", ru: "Слишком длинно" },
  { id: "not_useful", kk: "Пайдасыз", ru: "Бесполезно" },
  { id: "tone", kk: "Сөйлеу мәнері", ru: "Не тот тон" },
];


export function FeedbackButtons({
  messageId,
  initialRating,
  initialReason = null,
}: {
  messageId: number;
  initialRating: number;
  initialReason?: string | null;
}) {
  const { tr, lang } = useLang();
  const [rating, setRating] = useState(initialRating);
  const [reason, setReason] = useState<string | null>(initialReason);
  const [askReason, setAskReason] = useState(false);
  const [saving, setSaving] = useState(false);

  async function send(nextRating: number, nextReason: string | null) {
    const token = getValidToken();

    if (!token) {
      return false;
    }

    try {
      const response = await fetch(`${API_URL}/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message_id: messageId,
          rating: nextRating,
          reason: nextReason,
        }),
      });

      return response.ok;
    } catch {
      return false;
    }
  }

  async function rate(value: 1 | -1) {
    if (saving) {
      return;
    }

    const previous = { rating, reason };
    // Сол батырманы қайта басса — бағаны алып тастаймыз.
    const next = rating === value ? 0 : value;

    setRating(next);
    setReason(null);
    setAskReason(next === -1);
    setSaving(true);

    const ok = await send(next, null);

    if (!ok) {
      setRating(previous.rating);
      setReason(previous.reason);
      setAskReason(false);
    }

    setSaving(false);
  }

  async function chooseReason(id: string) {
    if (saving) {
      return;
    }

    setReason(id);
    setSaving(true);

    const ok = await send(-1, id);

    if (ok) {
      setAskReason(false);
    } else {
      setReason(null);
    }

    setSaving(false);
  }

  const base =
    "inline-flex h-7 w-7 items-center justify-center rounded-lg text-sm transition disabled:cursor-not-allowed";

  const reasonLabel = DISLIKE_REASONS.find((item) => item.id === reason);

  return (
    // display: contents — батырмалар жолдың ішінде тұрады,
    // ал себептер жаңа жолға (order-last, basis-full) түседі.
    <div className="contents">
      <div className="flex items-center gap-0.5" aria-label={tr("Жауапты бағалау", "Оценить ответ")}>
        <button
          type="button"
          onClick={() => void rate(1)}
          disabled={saving}
          aria-pressed={rating === 1}
          title={tr("Жақсы жауап", "Хороший ответ")}
          aria-label={tr("Жақсы жауап", "Хороший ответ")}
          className={`${base} ${
            rating === 1
              ? "bg-gold-500/15 text-gold-300"
              : "text-neutral-600 opacity-70 hover:bg-white/[0.04] hover:text-neutral-300 hover:opacity-100"
          }`}
        >
          <ThumbIcon up filled={rating === 1} />
        </button>

        <button
          type="button"
          onClick={() => void rate(-1)}
          disabled={saving}
          aria-pressed={rating === -1}
          title={tr("Жауап ұнамады", "Ответ не понравился")}
          aria-label={tr("Жауап ұнамады", "Ответ не понравился")}
          className={`${base} ${
            rating === -1
              ? "bg-white/[0.08] text-neutral-200"
              : "text-neutral-600 opacity-70 hover:bg-white/[0.04] hover:text-neutral-300 hover:opacity-100"
          }`}
        >
          <ThumbIcon filled={rating === -1} />
        </button>

        {rating !== 0 && !askReason && (
          <span className="ml-1 text-[11px] text-neutral-600" role="status">
            {reasonLabel ? `${reasonLabel[lang]} · ` : ""}
            {tr("Рақмет!", "Спасибо!")}
          </span>
        )}
      </div>

      {rating === -1 && askReason && (
        <div className="order-last flex basis-full flex-wrap items-center gap-1.5 pt-1" role="group" aria-label={tr("Неге ұнамады?", "Что не так?")}>
          <span className="text-[11px] text-neutral-500">
            {tr("Неге ұнамады?", "Что не так?")}
          </span>

          {DISLIKE_REASONS.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => void chooseReason(item.id)}
              disabled={saving}
              aria-pressed={reason === item.id}
              className={`rounded-full border px-2.5 py-1 text-[11px] transition disabled:opacity-50 ${
                reason === item.id
                  ? "border-gold-500/50 bg-gold-500/10 text-gold-300"
                  : "border-neutral-800 text-neutral-400 hover:border-neutral-600 hover:text-neutral-200"
              }`}
            >
              {item[lang]}
            </button>
          ))}

          <button
            type="button"
            onClick={() => setAskReason(false)}
            className="px-1 text-[11px] text-neutral-600 hover:text-neutral-400"
          >
            {tr("Өткізу", "Пропустить")}
          </button>
        </div>
      )}
    </div>
  );
}


function ThumbIcon({ up = false, filled }: { up?: boolean; filled: boolean }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="15"
      height="15"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
      style={up ? undefined : { transform: "rotate(180deg)" }}
    >
      <path d="M7 10v11" />
      <path d="M15 5.9 14 10h5.8a2 2 0 0 1 1.9 2.6l-2.3 7A2 2 0 0 1 17.5 21H7V10l4.3-7.4a1.6 1.6 0 0 1 2.9 1.2Z" />
    </svg>
  );
}


// =====================================================
// ADMIN LINK (тек әкімшіге көрінеді)
// =====================================================

export function AdminLink({ onNavigate }: { onNavigate: () => void }) {
  const [isAdmin, setIsAdmin] = useState(false);
  const { tr } = useLang();

  useEffect(() => {
    const token = getValidToken();

    if (!token) {
      return;
    }

    let cancelled = false;

    fetch(`${API_URL}/admin/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (!cancelled && data?.is_admin) {
          setIsAdmin(true);
        }
      })
      .catch(() => {
        // Сілтеме көрсетілмейді — бұл міндетті емес.
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (!isAdmin) {
    return null;
  }

  return (
    <button
      type="button"
      onClick={onNavigate}
      className="flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left text-sm text-gold-400 transition hover:bg-neutral-900 hover:text-gold-300"
    >
      <span>◆</span>
      <span>{tr("Әкімші панелі", "Панель администратора")}</span>
    </button>
  );
}
