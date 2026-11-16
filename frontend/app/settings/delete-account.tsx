"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { clearSession, ensureFreshToken } from "@/lib/auth";
import { useLang } from "@/lib/i18n";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";


// =====================================================
// АККАУНТТЫ ЖОЮ
// =====================================================

export function DeleteAccountSection({
  onUnauthorized,
}: {
  onUnauthorized: () => void;
}) {
  const router = useRouter();
  const { tr } = useLang();
  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [understood, setUnderstood] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [deleted, setDeleted] = useState(false);


  function close() {
    setOpen(false);
    setPassword("");
    setUnderstood(false);
    setError("");
  }


  async function handleDelete(event: React.FormEvent) {
    event.preventDefault();

    if (!understood || !password) {
      return;
    }

    setError("");
    setLoading(true);

    try {
      const token = await ensureFreshToken();

      if (!token) {
        onUnauthorized();
        return;
      }

      const response = await fetch(
        `${API_URL}/auth/delete-account`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ password }),
        }
      );

      const data = await response.json().catch(() => ({}));

      if (response.status === 401) {
        onUnauthorized();
        return;
      }

      if (!response.ok) {
        setError(
          typeof data.detail === "string"
            ? data.detail
            : tr("Аккаунтты жою кезінде қате шықты.", "Ошибка при удалении аккаунта.")
        );
        return;
      }

      clearSession();
      setDeleted(true);

      // Хабарды оқуға уақыт беріп, басты бетке жібереміз
      // (баптаулар беті енді жұмыс істемейді).
      window.setTimeout(() => {
        router.push("/");
      }, 5000);

    } catch {
      setError(tr("Серверге қосылу мүмкін болмады. Қайталап көр.", "Не удалось подключиться к серверу. Попробуй ещё раз."));

    } finally {
      setLoading(false);
    }
  }


  if (deleted) {
    return (
      <section className="rounded-2xl border border-gold-500/25 bg-gold-500/[0.06] p-5 sm:p-6">
        <h2 className="text-lg font-semibold">
          {tr("Аккаунт жойылды", "Аккаунт удалён")}
        </h2>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-neutral-300">
          {tr(
            "Аккаунтың, әңгімелерің және барлық деректерің өшірілді. Резервтік көшірмелерден олар 14 күн ішінде өздігінен кетеді. Сау бол, брат.",
            "Твой аккаунт, разговоры и все данные удалены. Из резервных копий они исчезнут автоматически в течение 14 дней. Береги себя, брат."
          )}
        </p>

        <p className="mt-2 text-xs text-neutral-500">
          {tr("Бірнеше секундтан кейін басты бетке өтесің.", "Через несколько секунд ты перейдёшь на главную.")}
        </p>

        <Link
          href="/"
          className="mt-5 inline-flex rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black"
        >
          {tr("Басты бетке", "На главную")}
        </Link>
      </section>
    );
  }


  return (
    <section className="rounded-2xl border border-red-500/20 bg-red-500/[0.04] p-5 sm:p-6">

      <h2 className="text-lg font-semibold">
        {tr("Аккаунтты жою", "Удаление аккаунта")}
      </h2>

      <p className="mt-2 max-w-2xl text-sm leading-6 text-neutral-500">
        {tr(
          "Аккаунтың және ERKEK AI-да сақталған барлық деректерің біржола өшіріледі. Бұл әрекетті қайтару мүмкін емес.",
          "Твой аккаунт и все данные в ERKEK AI будут удалены навсегда. Это действие нельзя отменить."
        )}
      </p>


      {!open ? (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="mt-5 rounded-xl border border-red-500/25 bg-red-500/[0.06] px-4 py-3 text-sm font-medium text-red-400 transition hover:bg-red-500/[0.12] hover:text-red-300"
        >
          {tr("Аккаунтты жою…", "Удалить аккаунт…")}
        </button>
      ) : (
        <form onSubmit={handleDelete} className="mt-5 max-w-xl space-y-4">

          <div className="rounded-xl border border-red-500/20 bg-black/40 p-4 text-sm leading-6 text-neutral-300">
            <div className="mb-2 font-semibold text-red-300">
              {tr("Не өшіріледі:", "Что будет удалено:")}
            </div>
            <ul className="list-disc space-y-1 pl-5 text-neutral-400">
              <li>{tr("аккаунт (email, пайдаланушы аты, құпиясөз);", "аккаунт (email, имя пользователя, пароль);")}</li>
              <li>{tr("барлық әңгімелер мен олардың тарихы;", "все разговоры и их история;")}</li>
              <li>{tr("ERKEK AI «жадындағы» мәліметтер;", "сведения в «памяти» ERKEK AI;")}</li>
              <li>{tr("барлық құрылғылардағы кіру сессиялары.", "сессии входа на всех устройствах.")}</li>
            </ul>
          </div>

          <div>
            <label
              htmlFor="delete-password"
              className="text-sm text-neutral-400"
            >
              {tr("Растау үшін құпиясөзіңді енгіз", "Для подтверждения введи пароль")}
            </label>

            <input
              id="delete-password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-2 w-full rounded-xl border border-white/[0.08] bg-black px-4 py-3 text-white outline-none transition placeholder:text-neutral-700"
              placeholder="••••••••"
            />
          </div>

          <label className="flex cursor-pointer items-start gap-3 text-sm leading-6 text-neutral-400">
            <input
              type="checkbox"
              checked={understood}
              onChange={(event) => setUnderstood(event.target.checked)}
              className="mt-1 h-4 w-4 shrink-0 accent-red-500"
            />
            <span>
              {tr(
                "Түсіндім: аккаунт пен деректер біржола жойылады, оларды қалпына келтіру мүмкін емес.",
                "Понимаю: аккаунт и данные будут удалены навсегда, восстановить их нельзя."
              )}
            </span>
          </label>

          {error && (
            <div
              role="alert"
              className="rounded-xl border border-red-500/20 bg-red-500/[0.06] px-4 py-3 text-sm text-red-400"
            >
              {error}
            </div>
          )}

          <div className="flex flex-wrap gap-3">
            <button
              type="submit"
              disabled={!understood || !password || loading}
              className="rounded-xl bg-red-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loading ? tr("Жойылуда...", "Удаляем...") : tr("Аккаунтты біржола жою", "Удалить аккаунт навсегда")}
            </button>

            <button
              type="button"
              onClick={close}
              disabled={loading}
              className="rounded-xl border border-neutral-800 px-5 py-3 text-sm text-neutral-300 transition hover:border-neutral-700 hover:text-white"
            >
              {tr("Бас тарту", "Отмена")}
            </button>
          </div>

        </form>
      )}

    </section>
  );
}
