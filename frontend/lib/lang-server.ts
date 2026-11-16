import { cookies } from "next/headers";

import { LANG_COOKIE, normalizeLang, type Lang } from "@/lib/lang";

/** Server компоненттері үшін: таңдалған интерфейс тілі. */
export async function getLang(): Promise<Lang> {
  const store = await cookies();
  return normalizeLang(store.get(LANG_COOKIE)?.value);
}
