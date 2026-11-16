"use client";

import { useEffect, useState } from "react";

import { resendVerification } from "@/lib/api";
import { useLang } from "@/lib/i18n";

const COOLDOWN_SECONDS = 60;


/** «Хатты қайта жіберу» батырмасы (60 секунд күту аралығымен). */
export function ResendVerificationButton({
  email,
  startWithCooldown = false,
}: {
  email: string;
  startWithCooldown?: boolean;
}) {
  const { tr } = useLang();
  const [cooldown, setCooldown] = useState(startWithCooldown ? COOLDOWN_SECONDS : 0);
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");

  useEffect(() => {
    if (cooldown <= 0) {
      return;
    }

    const timer = window.setTimeout(() => setCooldown((value) => value - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [cooldown]);

  async function resend() {
    setStatus("sending");

    try {
      await resendVerification(email);
      setStatus("sent");
      setCooldown(COOLDOWN_SECONDS);
    } catch {
      setStatus("error");
    }
  }

  return (
    <div className="space-y-2 text-center">
      <button
        type="button"
        onClick={() => void resend()}
        disabled={!email || cooldown > 0 || status === "sending"}
        className="text-sm font-semibold text-gold-400 transition hover:text-gold-300 disabled:cursor-not-allowed disabled:text-neutral-600"
      >
        {cooldown > 0
          ? tr(`Хатты қайта жіберу (${cooldown} с)`, `Отправить письмо ещё раз (${cooldown} с)`)
          : tr("Хатты қайта жіберу", "Отправить письмо ещё раз")}
      </button>

      {status === "sent" && (
        <p className="text-xs text-neutral-500" role="status">
          {tr("Жаңа сілтеме жіберілді.", "Новая ссылка отправлена.")}
        </p>
      )}

      {status === "error" && (
        <p className="text-xs text-red-400" role="alert">
          {tr("Жіберу мүмкін болмады. Сәлден кейін қайталап көр.", "Не удалось отправить. Попробуй чуть позже.")}
        </p>
      )}
    </div>
  );
}


/** Тіркелгеннен кейін: «Почтаңды тексер» терезесі. */
export function CheckEmailOverlay({ email }: { email: string }) {
  const { tr } = useLang();

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="check-email-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 px-4 backdrop-blur-sm"
    >
      <div className="w-full max-w-md rounded-[28px] border border-gold-500/20 bg-neutral-950 p-7 text-center shadow-2xl sm:p-8">
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-gold-500/10 text-2xl">
          ✉️
        </div>

        <h2 id="check-email-title" className="text-3xl font-semibold">
          {tr("Почтаңды тексер", "Проверь почту")}
        </h2>

        <p className="mt-3 text-sm leading-6 text-neutral-400">
          {tr(
            "Аккаунтты белсендіру сілтемесін мына мекенжайға жібердік:",
            "Мы отправили ссылку для активации аккаунта на адрес:"
          )}
        </p>

        <p className="mt-1 break-all font-semibold text-neutral-100">{email}</p>

        <p className="mt-4 text-xs leading-5 text-neutral-500">
          {tr(
            "Хат бірнеше минут ішінде келеді. Көрмесең, «Спам» папкасын тексер.",
            "Письмо придёт в течение нескольких минут. Если не видишь его, проверь папку «Спам»."
          )}
        </p>

        <div className="mt-6 border-t border-white/[0.06] pt-5">
          <ResendVerificationButton email={email} startWithCooldown />
        </div>
      </div>
    </div>
  );
}
