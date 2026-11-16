"use client";

import { useCallback, useEffect, useState } from "react";

import { ensureFreshToken } from "@/lib/auth";
import { useLang } from "@/lib/i18n";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";


type TelegramStatus = {
  enabled: boolean;
  linked: boolean;
  bot_url: string | null;
};


// =====================================================
// TELEGRAM: сайт аккаунтын ботқа байланыстыру
// =====================================================

export function TelegramLinkSection({
  onUnauthorized,
}: {
  onUnauthorized: () => void;
}) {
  const { tr } = useLang();
  const [status, setStatus] = useState<TelegramStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [waiting, setWaiting] = useState(false);
  const [error, setError] = useState("");


  const request = useCallback(
    async (method: "GET" | "POST" | "DELETE", path: string) => {
      const token = await ensureFreshToken();

      if (!token) {
        onUnauthorized();
        return null;
      }

      const response = await fetch(`${API_URL}${path}`, {
        method,
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.status === 401) {
        onUnauthorized();
        return null;
      }

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string" ? data.detail : "error"
        );
      }

      return data;
    },
    [onUnauthorized]
  );


  const refresh = useCallback(async () => {
    try {
      const data = await request("GET", "/telegram/status");
      if (data) {
        setStatus(data);
        if (data.linked) {
          setWaiting(false);
        }
      }
    } catch {
      // Бөлім міндетті емес — қате болса көрсетпейміз.
    }
  }, [request]);


  useEffect(() => {
    let cancelled = false;

    request("GET", "/telegram/status")
      .then((data) => {
        if (!cancelled && data) {
          setStatus(data);
        }
      })
      .catch(() => {
        // Бөлім міндетті емес.
      });

    return () => {
      cancelled = true;
    };
  }, [request]);


  // Telegram-да «Start» басқанша күтеміз: бетке оралғанда тексереміз.
  useEffect(() => {
    if (!waiting) {
      return;
    }

    const onFocus = () => void refresh();
    window.addEventListener("focus", onFocus);
    const timer = window.setInterval(onFocus, 4000);

    return () => {
      window.removeEventListener("focus", onFocus);
      window.clearInterval(timer);
    };
  }, [waiting, refresh]);


  async function connect() {
    setError("");
    setBusy(true);

    // Сілтемені алдын ала ашамыз (кейбір браузерлер кейін ашылатын терезені бұғаттайды).
    const popup = window.open("", "_blank");

    try {
      const data = await request("POST", "/telegram/link");

      if (!data?.url) {
        popup?.close();
        return;
      }

      if (popup) {
        popup.location.href = data.url;
      } else {
        window.location.href = data.url;
      }

      setWaiting(true);
    } catch (err) {
      popup?.close();
      setError(
        err instanceof Error && err.message !== "error"
          ? err.message
          : tr("Сілтеме жасау кезінде қате шықты.", "Ошибка при создании ссылки.")
      );
    } finally {
      setBusy(false);
    }
  }


  async function disconnect() {
    if (
      !window.confirm(
        tr(
          "Telegram-ды аккаунттан ажыратамыз ба? Әңгімелер сақталады.",
          "Отвязать Telegram от аккаунта? Разговоры сохранятся."
        )
      )
    ) {
      return;
    }

    setError("");
    setBusy(true);

    try {
      await request("DELETE", "/telegram/link");
      await refresh();
    } catch {
      setError(tr("Ажырату кезінде қате шықты.", "Ошибка при отвязке."));
    } finally {
      setBusy(false);
    }
  }


  if (!status?.enabled) {
    return null;
  }


  return (
    <section className="rounded-2xl border border-neutral-900 bg-neutral-950 p-5 sm:p-6">

      <div className="flex flex-wrap items-start justify-between gap-4">

        <div className="max-w-xl">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <TelegramIcon />
            Telegram
          </h2>

          <p className="mt-2 text-sm leading-6 text-neutral-500">
            {status.linked
              ? tr(
                  "Telegram байланған: ботта да осы аккаунттың жады мен мінезі қолданылады.",
                  "Telegram привязан: в боте используются память и характер этого аккаунта."
                )
              : tr(
                  "ERKEK AI-мен Telegram-да да сөйлес. Байланыстырсаң, жады мен әңгімелер ортақ болады.",
                  "Общайся с ERKEK AI и в Telegram. После привязки память и разговоры станут общими."
                )}
          </p>

          {waiting && !status.linked && (
            <p className="mt-2 text-xs text-gold-400" role="status">
              {tr(
                "Telegram-да «Start» батырмасын бас — содан кейін осы бет өзі жаңарады.",
                "Нажми «Start» в Telegram — после этого страница обновится сама."
              )}
            </p>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {status.linked ? (
            <>
              {status.bot_url && (
                <a
                  href={status.bot_url}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-black"
                >
                  {tr("Ботты ашу", "Открыть бота")}
                </a>
              )}
              <button
                type="button"
                onClick={() => void disconnect()}
                disabled={busy}
                className="rounded-xl border border-neutral-800 px-4 py-2.5 text-sm text-neutral-300 transition hover:border-neutral-700 hover:text-white disabled:opacity-50"
              >
                {tr("Ажырату", "Отвязать")}
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => void connect()}
              disabled={busy}
              className="rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-black disabled:opacity-50"
            >
              {busy
                ? tr("Дайындалуда...", "Готовим...")
                : tr("Telegram-ды байланыстыру", "Привязать Telegram")}
            </button>
          )}
        </div>

      </div>

      {error && (
        <div
          role="alert"
          className="mt-4 rounded-xl border border-red-500/20 bg-red-500/[0.06] px-4 py-3 text-sm text-red-400"
        >
          {error}
        </div>
      )}

    </section>
  );
}


export function TelegramIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor" aria-hidden>
      <path d="M21.9 4.3 18.7 19.4c-.2 1-.9 1.3-1.8.8l-4.9-3.6-2.4 2.3c-.3.3-.5.5-1 .5l.3-5 9.1-8.2c.4-.4-.1-.6-.6-.2L6.2 13 1.4 11.5c-1-.3-1-1 .2-1.5L20.5 2.9c.9-.3 1.6.2 1.4 1.4Z" />
    </svg>
  );
}
