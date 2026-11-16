"use client";

import { useEffect, useRef, useState } from "react";

import { saveTokens } from "@/lib/auth";
import { useLang } from "@/lib/i18n";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

const GSI_SRC = "https://accounts.google.com/gsi/client";

// Жаңа пайдаланушы келісім белгісін қойғанша Google жауабын сақтаймыз.
export const PENDING_GOOGLE_KEY = "erkek_google_pending";

type GoogleId = {
  initialize: (options: {
    client_id: string;
    callback: (response: { credential: string }) => void;
    ux_mode?: "popup";
  }) => void;
  renderButton: (element: HTMLElement, options: Record<string, unknown>) => void;
};

declare global {
  interface Window {
    google?: { accounts: { id: GoogleId } };
  }
}


function loadScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) {
      resolve();
      return;
    }

    const existing = document.querySelector<HTMLScriptElement>(`script[src="${GSI_SRC}"]`);
    const script = existing ?? document.createElement("script");

    script.addEventListener("load", () => resolve(), { once: true });
    script.addEventListener("error", () => reject(new Error("gsi")), { once: true });

    if (!existing) {
      script.src = GSI_SRC;
      script.async = true;
      document.head.appendChild(script);
    }
  });
}


export type GoogleResult =
  | { status: "ok" }
  | { status: "consent_required"; credential: string }
  | { status: "error"; message: string };


/** Google жауабын серверге жібереді; сәтті болса token-дерді сақтайды. */
export async function finishGoogleLogin(
  credential: string,
  acceptTerms: boolean
): Promise<GoogleResult> {
  try {
    const response = await fetch(`${API_URL}/auth/google`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ credential, accept_terms: acceptTerms }),
    });

    const data = await response.json().catch(() => ({}));

    if (response.status === 428) {
      return { status: "consent_required", credential };
    }

    if (!response.ok) {
      return {
        status: "error",
        message: typeof data.detail === "string" ? data.detail : "",
      };
    }

    saveTokens(data.access_token, data.refresh_token);

    try {
      sessionStorage.removeItem(PENDING_GOOGLE_KEY);
    } catch {
      // ignore
    }

    return { status: "ok" };
  } catch {
    return { status: "error", message: "" };
  }
}


/** Google батырмасы. Сервер Google-ды қоспаса — ештеңе көрсетпейді. */
export function GoogleButton({
  onCredential,
}: {
  onCredential: (credential: string) => void;
}) {
  const { tr, lang } = useLang();
  const containerRef = useRef<HTMLDivElement>(null);
  const callbackRef = useRef(onCredential);
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    callbackRef.current = onCredential;
  }, [onCredential]);

  useEffect(() => {
    let cancelled = false;

    fetch(`${API_URL}/auth/google/config`)
      .then((response) => (response.ok ? response.json() : null))
      .then(async (config) => {
        if (cancelled || !config?.enabled || !config.client_id) {
          return;
        }

        await loadScript();

        if (cancelled || !containerRef.current || !window.google) {
          return;
        }

        window.google.accounts.id.initialize({
          client_id: config.client_id,
          callback: (response) => callbackRef.current(response.credential),
          ux_mode: "popup",
        });

        window.google.accounts.id.renderButton(containerRef.current, {
          theme: "filled_black",
          size: "large",
          shape: "pill",
          text: "continue_with",
          width: Math.min(containerRef.current.offsetWidth || 360, 400),
          locale: lang === "ru" ? "ru" : "kk",
        });

        setEnabled(true);
      })
      .catch(() => {
        // Google қолжетімсіз болса — тек email арқылы кіру қалады.
      });

    return () => {
      cancelled = true;
    };
  }, [lang]);

  return (
    <div className={enabled ? "space-y-4" : "hidden"}>
      <div className="flex items-center gap-3 text-xs text-neutral-600">
        <span className="h-px flex-1 bg-white/[0.06]" />
        {tr("немесе", "или")}
        <span className="h-px flex-1 bg-white/[0.06]" />
      </div>

      <div ref={containerRef} className="flex min-h-[44px] w-full justify-center" />
    </div>
  );
}
