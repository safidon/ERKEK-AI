"use client";

import { useState } from "react";
import Link from "next/link";

import { requestPasswordReset } from "@/lib/api";
import { useLang } from "@/lib/i18n";

import {
  AuthCard,
  FormError,
  FormSuccess,
  inputClassName,
  primaryButtonClassName,
} from "../auth-card";


export default function ForgotPasswordPage() {
  const { tr } = useLang();
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [sentMessage, setSentMessage] = useState("");
  const [loading, setLoading] = useState(false);


  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const result = await requestPasswordReset(email);
      setSentMessage(result.detail);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : tr("Белгісіз қате шықты.", "Произошла неизвестная ошибка.")
      );
    } finally {
      setLoading(false);
    }
  }


  return (
    <AuthCard
      eyebrow={tr("Аккаунт", "Аккаунт")}
      title={tr("Құпиясөзді ұмыттың ба?", "Забыл пароль?")}
      description={tr(
        "Email-іңді жаз — жаңа құпиясөз қоюға арналған сілтеме жібереміз.",
        "Укажи свой email — мы пришлём ссылку для нового пароля."
      )}
    >
      {sentMessage ? (
        <div className="space-y-5">

          <FormSuccess message={sentMessage} />

          <p className="text-sm leading-6 text-neutral-500">
            {tr(
              "Хат бірнеше минут ішінде келеді. Көрмесең, «Спам» папкасын тексер. Сілтеме 30 минут жарамды.",
              "Письмо придёт в течение нескольких минут. Если не видишь его, проверь папку «Спам». Ссылка действует 30 минут."
            )}
          </p>

          <Link
            href="/login"
            className="block text-center text-sm font-semibold text-gold-400 transition hover:text-gold-300"
          >
            {tr("← Кіру бетіне оралу", "← Вернуться ко входу")}
          </Link>

        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-5">

          <div>
            <label htmlFor="email" className="text-sm text-neutral-400">
              Email
            </label>

            <input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              placeholder="name@example.com"
              className={inputClassName}
            />
          </div>

          <FormError message={error} />

          <button
            type="submit"
            disabled={loading}
            className={primaryButtonClassName}
          >
            {loading ? tr("Жіберілуде...", "Отправляем...") : tr("Сілтеме жіберу", "Отправить ссылку")}
          </button>

          <div className="border-t border-white/[0.06] pt-5 text-center">
            <Link
              href="/login"
              className="text-sm font-semibold text-gold-400 transition hover:text-gold-300"
            >
              {tr("← Кіру бетіне оралу", "← Вернуться ко входу")}
            </Link>
          </div>

        </form>
      )}
    </AuthCard>
  );
}
