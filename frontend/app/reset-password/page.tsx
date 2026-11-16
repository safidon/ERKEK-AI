"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { resetPassword } from "@/lib/api";
import { useLang } from "@/lib/i18n";

import {
  AuthCard,
  FormError,
  FormSuccess,
  inputClassName,
  primaryButtonClassName,
} from "../auth-card";


const MIN_PASSWORD_LENGTH = 8;


export default function ResetPasswordPage() {
  const { tr } = useLang();
  return (
    <AuthCard
      eyebrow={tr("Аккаунт", "Аккаунт")}
      title={tr("Жаңа құпиясөз", "Новый пароль")}
      description={tr(
        "Кемінде 8 таңбадан тұратын жаңа құпиясөз ойлап тап.",
        "Придумай новый пароль минимум из 8 символов."
      )}
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
  const { tr } = useLang();

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [doneMessage, setDoneMessage] = useState("");
  const [loading, setLoading] = useState(false);


  if (!token) {
    return (
      <div className="space-y-5">
        <FormError
          message={tr(
            "Сілтеме толық емес. Хаттағы сілтемені қайта аш немесе жаңасын сұра.",
            "Ссылка неполная. Открой ссылку из письма ещё раз или запроси новую."
          )}
        />

        <Link
          href="/forgot-password"
          className="block text-center text-sm font-semibold text-gold-400 transition hover:text-gold-300"
        >
          {tr("Жаңа сілтеме сұрау →", "Запросить новую ссылку →")}
        </Link>
      </div>
    );
  }


  if (doneMessage) {
    return (
      <div className="space-y-5">
        <FormSuccess message={doneMessage} />

        <Link href="/login" className={primaryButtonClassName}>
          {tr("Кіру", "Войти")}
        </Link>
      </div>
    );
  }


  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    setError("");

    if (password.length < MIN_PASSWORD_LENGTH) {
      setError(tr("Құпиясөз кемінде 8 таңба болуы керек.", "Пароль должен содержать минимум 8 символов."));
      return;
    }

    if (password !== confirm) {
      setError(tr("Құпиясөздер сәйкес келмейді.", "Пароли не совпадают."));
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
          : tr("Белгісіз қате шықты.", "Произошла неизвестная ошибка.")
      );
    } finally {
      setLoading(false);
    }
  }


  return (
    <form onSubmit={handleSubmit} className="space-y-5">

      <div>
        <label htmlFor="password" className="text-sm text-neutral-400">
          {tr("Жаңа құпиясөз", "Новый пароль")}
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
          {tr("Құпиясөзді қайтала", "Повтори пароль")}
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
        {loading ? tr("Сақталуда...", "Сохраняем...") : tr("Құпиясөзді сақтау", "Сохранить пароль")}
      </button>

      {(error.includes("мерзімі") || error.includes("устарела")) && (
        <Link
          href="/forgot-password"
          className="block text-center text-sm font-semibold text-gold-400 transition hover:text-gold-300"
        >
          {tr("Жаңа сілтеме сұрау →", "Запросить новую ссылку →")}
        </Link>
      )}

    </form>
  );
}
