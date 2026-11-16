"use client";

// =====================================================
// ИНТЕРФЕЙС ТІЛІ (kk / ru)
// =====================================================
// Мәтіндер компонент ішінде қатар жазылады:
//   const { tr } = useLang();
//   tr("Кіру", "Войти")
// Таңдалған тіл `erkek_lang` cookie-де сақталады: оны server
// беттері (заң құжаттары) және backend (қате хабарламалары) оқиды.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useRouter } from "next/navigation";

import { LANG_COOKIE, type Lang } from "@/lib/lang";

export type { Lang } from "@/lib/lang";

type LangContextValue = {
  lang: Lang;
  setLang: (lang: Lang) => void;
  tr: (kk: string, ru: string) => string;
};

const LangContext = createContext<LangContextValue | null>(null);

function writeCookie(lang: Lang) {
  document.cookie =
    `${LANG_COOKIE}=${lang}; path=/; max-age=31536000; samesite=lax`;
}

export function LanguageProvider({
  initialLang,
  children,
}: {
  initialLang: Lang;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [lang, setLangState] = useState<Lang>(initialLang);

  // Cookie жоқ болса — қойып қоямыз (backend та сол тілді білуі үшін).
  useEffect(() => {
    if (!document.cookie.includes(`${LANG_COOKIE}=`)) {
      writeCookie(lang);
    }
  }, [lang]);

  const setLang = useCallback(
    (next: Lang) => {
      writeCookie(next);
      setLangState(next);
      document.documentElement.lang = next;
      // Server беттерін (заң құжаттары) жаңа тілмен қайта салу.
      router.refresh();
    },
    [router]
  );

  const value = useMemo<LangContextValue>(
    () => ({
      lang,
      setLang,
      tr: (kk, ru) => (lang === "ru" ? ru : kk),
    }),
    [lang, setLang]
  );

  return (
    <LangContext.Provider value={value}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang(): LangContextValue {
  const value = useContext(LangContext);

  if (!value) {
    throw new Error("useLang must be used inside LanguageProvider");
  }

  return value;
}


// =====================================================
// ТІЛ АУЫСТЫРҒЫШ
// =====================================================

export function LanguageSwitcher({
  className = "",
}: {
  className?: string;
}) {
  const { lang, setLang } = useLang();

  const options: { value: Lang; label: string; title: string }[] = [
    { value: "kk", label: "ҚАЗ", title: "Қазақша" },
    { value: "ru", label: "РУС", title: "Русский" },
  ];

  return (
    <div
      role="group"
      aria-label="Тіл / Язык"
      className={`inline-flex rounded-full border border-gold-500/20 bg-black/40 p-0.5 text-[11px] font-semibold tracking-[0.12em] ${className}`}
    >
      {options.map((option) => {
        const active = option.value === lang;

        return (
          <button
            key={option.value}
            type="button"
            title={option.title}
            aria-pressed={active}
            onClick={() => {
              if (!active) {
                setLang(option.value);
              }
            }}
            className={`rounded-full px-2.5 py-1 transition ${
              active
                ? "bg-gold-500/90 text-black"
                : "text-neutral-400 hover:text-gold-300"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
