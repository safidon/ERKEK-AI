"use client";

import { useState } from "react";
import Link from "next/link";

import { requestPasswordReset } from "@/lib/api";

import {
  AuthCard,
  FormError,
  FormSuccess,
  inputClassName,
  primaryButtonClassName,
} from "../auth-card";


export default function ForgotPasswordPage() {
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
          : "Белгісіз қате шықты."
      );
    } finally {
      setLoading(false);
    }
  }


  return (
    <AuthCard
      eyebrow="Аккаунт"
      title="Құпиясөзді ұмыттың ба?"
      description="Email-іңді жаз — жаңа құпиясөз қоюға арналған сілтеме жібереміз."
    >
      {sentMessage ? (
        <div className="space-y-5">

          <FormSuccess message={sentMessage} />

          <p className="text-sm leading-6 text-neutral-500">
            Хат бірнеше минут ішінде келеді. Көрмесең, «Спам»
            папкасын тексер. Сілтеме 30 минут жарамды.
          </p>

          <Link
            href="/login"
            className="block text-center text-sm font-semibold text-gold-400 transition hover:text-gold-300"
          >
            ← Кіру бетіне оралу
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
            {loading ? "Жіберілуде..." : "Сілтеме жіберу"}
          </button>

          <div className="border-t border-white/[0.06] pt-5 text-center">
            <Link
              href="/login"
              className="text-sm font-semibold text-gold-400 transition hover:text-gold-300"
            >
              ← Кіру бетіне оралу
            </Link>
          </div>

        </form>
      )}
    </AuthCard>
  );
}
