"use client";

import { useEffect } from "react";
import Link from "next/link";

import { useLang } from "@/lib/i18n";
import { reportClientError } from "@/lib/report-error";

// Бет құлаған жағдайда көрсетілетін бет (қате әкімшіге жіберіледі).
export default function ErrorPage({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  const { tr } = useLang();

  useEffect(() => {
    reportClientError(error, "error boundary");
  }, [error]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-black px-4 text-white">
      <div className="w-full max-w-md rounded-[28px] border border-gold-500/15 bg-neutral-950 p-8 text-center">
        <div className="mb-4 text-gold-500">◆</div>

        <h1 className="text-3xl font-semibold">
          {tr("Бірдеңе дұрыс болмады", "Что-то пошло не так")}
        </h1>

        <p className="mt-3 text-sm leading-6 text-neutral-400">
          {tr(
            "Қате туралы бізге хабар кетті. Бетті қайта жүктеп көр.",
            "Мы уже получили сообщение об ошибке. Попробуй обновить страницу."
          )}
        </p>

        <div className="mt-7 flex flex-col gap-2 sm:flex-row sm:justify-center">
          <button
            type="button"
            onClick={() => retry()}
            className="rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black"
          >
            {tr("Қайталау", "Повторить")}
          </button>

          <Link
            href="/"
            className="rounded-xl border border-neutral-800 px-5 py-3 text-sm text-neutral-300 transition hover:text-white"
          >
            {tr("Басты бетке", "На главную")}
          </Link>
        </div>
      </div>
    </main>
  );
}
