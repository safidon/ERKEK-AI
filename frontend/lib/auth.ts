"use client";

import { useEffect, useRef } from "react";

// =====================================================
// JWT SESSION HANDLING
// =====================================================
// - access token (қысқа, ~15 мин) әр API сұранысына қосылады;
// - refresh token (ұзақ, 30 күн — қолданған сайын ұзарады) access
//   token-ді мерзімі бітпей тұрып жаңарту үшін қолданылады.
// Екеуі де localStorage-та. Бірнеше қойынды бір мезетте жаңартпауы
// үшін Web Locks API қолданылады.

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

const TOKEN_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

// Access token мерзімі бітуге осы уақыт қалғанда жаңартамыз.
const REFRESH_BEFORE_EXPIRY_MS = 2 * 60_000;

// Мерзімі бітуге 10 секунд қалған token-ді жарамсыз санаймыз.
const EXPIRY_SKEW_MS = 10_000;


function readExpiry(token: string): number | null {
  try {
    const payload = token.split(".")[1];

    if (!payload) {
      return null;
    }

    const json = atob(
      payload.replace(/-/g, "+").replace(/_/g, "/")
    );

    const exp = JSON.parse(json).exp;

    return typeof exp === "number" ? exp * 1000 : null;
  } catch {
    return null;
  }
}


function isUsable(token: string | null, marginMs: number) {
  if (!token) {
    return false;
  }

  const expiresAt = readExpiry(token);

  return expiresAt !== null && expiresAt - marginMs > Date.now();
}


export function saveTokens(
  accessToken: string,
  refreshToken?: string
) {
  localStorage.setItem(TOKEN_KEY, accessToken);

  if (refreshToken) {
    localStorage.setItem(REFRESH_KEY, refreshToken);
  }
}


/** @deprecated saveTokens қолданыңыз */
export function saveToken(token: string) {
  saveTokens(token);
}


export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}


/**
 * Жарамды access token-ді қайтарады (желіге шықпайды).
 * Мерзімі өтсе null — бірақ refresh token сақталады,
 * сессияны ensureFreshToken() арқылы жаңартуға болады.
 */
export function getValidToken(): string | null {
  const token = localStorage.getItem(TOKEN_KEY);

  return isUsable(token, EXPIRY_SKEW_MS) ? token : null;
}


/** Құрылғыда сессия бар ма (жарамды access немесе refresh token). */
export function hasStoredSession(): boolean {
  return Boolean(
    getValidToken() || localStorage.getItem(REFRESH_KEY)
  );
}


type RefreshResult =
  | { status: "ok"; token: string }
  | { status: "expired" }
  | { status: "offline" };


async function doRefresh(): Promise<RefreshResult> {
  // Басқа қойынды бізден бұрын жаңартып үлгерген болуы мүмкін.
  const current = localStorage.getItem(TOKEN_KEY);

  if (isUsable(current, REFRESH_BEFORE_EXPIRY_MS)) {
    return { status: "ok", token: current as string };
  }

  const refreshToken = localStorage.getItem(REFRESH_KEY);

  if (!refreshToken) {
    return { status: "expired" };
  }

  let response: Response;

  try {
    response = await fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  } catch {
    // Интернет жоқ — сессияны жоймаймыз, кейін қайталаймыз.
    return { status: "offline" };
  }

  if (response.status === 401 || response.status === 422) {
    // Біз жіберген уақытта басқа қойынды token-ді ауыстырған болса,
    // localStorage-та жаңасы тұр — оны қолданамыз.
    const latest = localStorage.getItem(TOKEN_KEY);

    if (
      localStorage.getItem(REFRESH_KEY) !== refreshToken &&
      isUsable(latest, EXPIRY_SKEW_MS)
    ) {
      return { status: "ok", token: latest as string };
    }

    clearSession();
    return { status: "expired" };
  }

  if (!response.ok) {
    return { status: "offline" };
  }

  const data = await response.json();

  saveTokens(data.access_token, data.refresh_token);

  return { status: "ok", token: data.access_token };
}


let inFlight: Promise<RefreshResult> | null = null;


/**
 * Access token-ді жаңартады. Бір қойындыда бір ғана сұраныс,
 * қойындылар арасында — Web Locks арқылы кезекпен.
 */
export function refreshSession(): Promise<RefreshResult> {
  if (inFlight) {
    return inFlight;
  }

  const run: () => Promise<RefreshResult> =
    typeof navigator !== "undefined" && navigator.locks
      ? async () =>
          // request() callback-тің нәтижесін қайтарады;
          // await типті Promise<Promise<…>>-тен тазартады.
          await navigator.locks.request(
            "erkek-ai-token-refresh",
            doRefresh
          )
      : doRefresh;

  inFlight = run().finally(() => {
    inFlight = null;
  });

  return inFlight;
}


/**
 * Жарамды access token қайтарады: керек болса алдымен жаңартады.
 * Сессия біткен болса null.
 */
export async function ensureFreshToken(): Promise<string | null> {
  const token = localStorage.getItem(TOKEN_KEY);

  if (isUsable(token, REFRESH_BEFORE_EXPIRY_MS)) {
    return token;
  }

  const result = await refreshSession();

  if (result.status === "ok") {
    return result.token;
  }

  if (result.status === "offline") {
    // Желі жоқ: ескі token әлі жарамды болса, соны қолданамыз.
    return getValidToken();
  }

  return null;
}


/** Осы құрылғыдағы сессияны серверде де жабады. */
export async function logout() {
  const refreshToken = localStorage.getItem(REFRESH_KEY);

  clearSession();

  if (!refreshToken) {
    return;
  }

  try {
    await fetch(`${API_URL}/auth/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      keepalive: true,
    });
  } catch {
    // Сервер қолжетімсіз болса да, құрылғыдан шықтық.
  }
}


/**
 * Сессияны тірі ұстайды:
 * - access token мерзімі бітуге ~2 минут қалғанда жаңартады;
 * - қойындыға қайта оралғанда (ноутбук ұйқыдан оянғанда) тексереді;
 * - басқа қойындыда шыққанда осы қойындыны да шығарады.
 * Сессия біржола біткенде onLoggedOut шақырылады.
 */
export function useSessionKeeper(onLoggedOut: () => void) {
  const onLoggedOutRef = useRef(onLoggedOut);

  useEffect(() => {
    onLoggedOutRef.current = onLoggedOut;
  });

  useEffect(() => {
    let timer: number | undefined;
    let stopped = false;

    async function check() {
      if (stopped) {
        return;
      }

      const token = await ensureFreshToken();

      if (stopped) {
        return;
      }

      if (!token) {
        if (!localStorage.getItem(REFRESH_KEY)) {
          onLoggedOutRef.current();
          return;
        }

        // Желі жоқ — бір минуттан кейін қайталаймыз.
        schedule(60_000);
        return;
      }

      const expiresAt = readExpiry(token) ?? Date.now();

      schedule(
        Math.max(
          expiresAt - REFRESH_BEFORE_EXPIRY_MS - Date.now(),
          5_000
        )
      );
    }

    function schedule(delay: number) {
      window.clearTimeout(timer);
      // setTimeout ~24.8 күннен ұзақ кідірісті қолдамайды.
      timer = window.setTimeout(check, Math.min(delay, 2_147_000_000));
    }

    function handleVisibility() {
      if (document.visibilityState === "visible") {
        check();
      }
    }

    function handleStorage(event: StorageEvent) {
      // Басқа қойындыда шықты.
      if (
        (event.key === REFRESH_KEY || event.key === null) &&
        !localStorage.getItem(REFRESH_KEY) &&
        !localStorage.getItem(TOKEN_KEY)
      ) {
        onLoggedOutRef.current();
      }
    }

    check();

    document.addEventListener("visibilitychange", handleVisibility);
    window.addEventListener("storage", handleStorage);

    return () => {
      stopped = true;
      window.clearTimeout(timer);
      document.removeEventListener("visibilitychange", handleVisibility);
      window.removeEventListener("storage", handleStorage);
    };
  }, []);
}
