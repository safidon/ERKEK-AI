"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import { verifyEmail } from "@/lib/api";
import { saveTokens } from "@/lib/auth";
import { useLang } from "@/lib/i18n";

import { AuthCard, FormError, primaryButtonClassName } from "../auth-card";


export default function VerifyEmailPage() {
  const { tr } = useLang();

  return (
    <AuthCard
      eyebrow={tr("Аккаунт", "Аккаунт")}
      title={tr("Email-ді растау", "Подтверждение email")}
      description={tr(
        "Сілтемені тексеріп жатырмыз.",
        "Проверяем ссылку."
      )}
    >
      {/* useSearchParams Suspense ішінде болуы керек (Next.js талабы) */}
      <Suspense fallback={<div className="h-24" />}>
        <VerifyEmailResult />
      </Suspense>
    </AuthCard>
  );
}


function VerifyEmailResult() {
  const { tr } = useLang();
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";

  const [state, setState] = useState<"checking" | "done" | "error">(
    token ? "checking" : "error"
  );
  const [message, setMessage] = useState("");

  // Token бір рет қана жарамды: React-тың қайталап шақыруынан қорғаймыз.
  const started = useRef(false);

  useEffect(() => {
    if (!token || started.current) {
      return;
    }

    started.current = true;

    verifyEmail(token)
      .then((tokens) => {
        saveTokens(tokens.access_token, tokens.refresh_token);
        setState("done");
        window.setTimeout(() => router.push("/chat"), 1500);
      })
      .catch((error: unknown) => {
        setMessage(error instanceof Error ? error.message : "");
        setState("error");
      });
  }, [token, router]);

  if (state === "checking") {
    return (
      <div className="flex items-center justify-center gap-3 py-6 text-sm text-neutral-400" role="status">
        <span className="h-2 w-2 animate-pulse rounded-full bg-gold-400" />
        {tr("Тексерілуде...", "Проверяем...")}
      </div>
    );
  }

  if (state === "done") {
    return (
      <div className="space-y-4 text-center" role="status">
        <div className="text-3xl">✅</div>
        <p className="text-sm leading-6 text-neutral-300">
          {tr(
            "Email расталды! Қазір чатқа өтесің...",
            "Email подтверждён! Сейчас откроется чат..."
          )}
        </p>
        <Link href="/chat" className={primaryButtonClassName}>
          {tr("Чатқа өту", "Перейти в чат")}
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <FormError
        message={
          message ||
          tr(
            "Сілтеме жарамсыз немесе мерзімі өткен. Растау хатын қайта сұра.",
            "Ссылка недействительна или устарела. Запроси письмо подтверждения заново."
          )
        }
      />

      <p className="text-sm leading-6 text-neutral-500">
        {tr(
          "Кіру бетінде email мен құпиясөзіңді жаз — сол жерден жаңа хат жіберуге болады.",
          "Введи email и пароль на странице входа — оттуда можно отправить новое письмо."
        )}
      </p>

      <Link href="/login" className={primaryButtonClassName}>
        {tr("Кіру бетіне өту", "Перейти ко входу")}
      </Link>
    </div>
  );
}
