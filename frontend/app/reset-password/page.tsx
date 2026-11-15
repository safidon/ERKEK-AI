"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { resetPassword } from "@/lib/api";

import {
  AuthCard,
  FormError,
  FormSuccess,
  inputClassName,
  primaryButtonClassName,
} from "../auth-card";


const MIN_PASSWORD_LENGTH = 8;


export default function ResetPasswordPage() {
  return (
    <AuthCard
      eyebrow="Аккаунт"
      title="Жаңа құпиясөз"
      description="Кемінде 8 таңбадан тұратын жаңа құпиясөз ойлап тап."
    >
      {/* useSearchParams Suspense ішінде болуы керек (Next.js талабы) */}
      <Suspense fallback={<div className="h-48" />}>
        <ResetPasswordForm />
      </Suspense>
    </AuthCard>
  );
}


function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [doneMessage, setDoneMessage] = useState("");
  const [loading, setLoading] = useState(false);


  if (!token) {
    return (
      <div className="space-y-5">
        <FormError message="Сілтеме толық емес. Хаттағы сілтемені қайта аш немесе жаңасын сұра." />

        <Link
          href="/forgot-password"
          className="block text-center text-sm font-semibold text-gold-400 transition hover:text-gold-300"
        >
          Жаңа сілтеме сұрау →
        </Link>
      </div>
    );
  }


  if (doneMessage) {
    return (
      <div className="space-y-5">
        <FormSuccess message={doneMessage} />

        <Link href="/login" className={primaryButtonClassName}>
          Кіру
        </Link>
      </div>
    );
  }


  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    setError("");

    if (password.length < MIN_PASSWORD_LENGTH) {
      setError("Құпиясөз кемінде 8 таңба болуы керек.");
      return;
    }

    if (password !== confirm) {
      setError("Құпиясөздер сәйкес келмейді.");
      return;
    }

    setLoading(true);

    try {
      const result = await resetPassword(token, password);
      setDoneMessage(result.detail);
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
    <form onSubmit={handleSubmit} className="space-y-5">

      <div>
        <label htmlFor="password" className="text-sm text-neutral-400">
          Жаңа құпиясөз
        </label>

        <input
          id="password"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
          minLength={MIN_PASSWORD_LENGTH}
          maxLength={128}
          placeholder="••••••••"
          className={inputClassName}
        />
      </div>

      <div>
        <label htmlFor="confirm" className="text-sm text-neutral-400">
          Құпиясөзді қайтала
        </label>

        <input
          id="confirm"
          type="password"
          autoComplete="new-password"
          value={confirm}
          onChange={(event) => setConfirm(event.target.value)}
          required
          maxLength={128}
          placeholder="••••••••"
          className={inputClassName}
        />
      </div>

      <FormError message={error} />

      <button
        type="submit"
        disabled={loading}
        className={primaryButtonClassName}
      >
        {loading ? "Сақталуда..." : "Құпиясөзді сақтау"}
      </button>

      {error.includes("мерзімі") && (
        <Link
          href="/forgot-password"
          className="block text-center text-sm font-semibold text-gold-400 transition hover:text-gold-300"
        >
          Жаңа сілтеме сұрау →
        </Link>
      )}

    </form>
  );
}
