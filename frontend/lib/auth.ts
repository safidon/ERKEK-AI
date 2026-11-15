"use client";

import { useEffect } from "react";

// =====================================================
// JWT SESSION HANDLING
// =====================================================
// Access token localStorage-та сақталады. Мұнда token-нің
// мерзімі (exp) тексеріледі: мерзімі өткен token қолданылмайды,
// ал мерзімі біткен кезде пайдаланушы автоматты түрде шығады.

const TOKEN_KEY = "access_token";

// Token мерзімі бітуге 10 секунд қалғанда оны жарамсыз деп санаймыз.
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


export function saveToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}


export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
}


/**
 * Жарамды token-ді қайтарады. Token жоқ, бұзылған
 * немесе мерзімі өткен болса — session тазаланып, null қайтады.
 */
export function getValidToken(): string | null {
  const token = localStorage.getItem(TOKEN_KEY);

  if (!token) {
    return null;
  }

  const expiresAt = readExpiry(token);

  if (
    expiresAt === null ||
    expiresAt - EXPIRY_SKEW_MS <= Date.now()
  ) {
    clearSession();
    return null;
  }

  return token;
}


/**
 * Token мерзімі біткен сәтте onExpire шақырылады
 * (мысалы, /login бетіне жіберу үшін).
 */
export function useSessionExpiry(onExpire: () => void) {
  useEffect(() => {
    const token = getValidToken();

    if (!token) {
      return;
    }

    const expiresAt = readExpiry(token);

    if (expiresAt === null) {
      return;
    }

    const delay = Math.max(
      expiresAt - EXPIRY_SKEW_MS - Date.now(),
      0
    );

    // setTimeout ~24.8 күннен ұзақ кідірісті қолдамайды.
    const timer = window.setTimeout(
      () => {
        clearSession();
        onExpire();
      },
      Math.min(delay, 2_147_000_000)
    );

    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
