// Тіл туралы ортақ мәндер (server де, client те қолданады).

export type Lang = "kk" | "ru";

export const LANG_COOKIE = "erkek_lang";

export const DEFAULT_LANG: Lang = "kk";

export function normalizeLang(value: string | undefined | null): Lang {
  return value === "ru" ? "ru" : DEFAULT_LANG;
}
