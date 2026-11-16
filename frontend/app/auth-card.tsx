"use client";

import Link from "next/link";

import { LanguageSwitcher } from "@/lib/i18n";


// =====================================================
// AUTH CARD
// =====================================================
// Құпиясөзді қалпына келтіру беттерінің ортақ безендіруі
// (кіру/тіркелу беттерімен бір стильде).

export function AuthCard({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <main className="relative flex min-h-screen overflow-hidden bg-black text-white">

      <div className="pointer-events-none absolute inset-0">
        <div className="bg-ornament absolute inset-0" />
        <div className="absolute left-1/2 top-[-260px] h-[520px] w-[760px] -translate-x-1/2 rounded-full bg-gold-500/[0.08] blur-3xl" />
      </div>


      <Link
        href="/"
        className="absolute left-5 top-5 z-20 flex items-center gap-3 rounded-xl px-2 py-2 transition hover:bg-white/[0.04] sm:left-7 sm:top-7"
      >
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white font-display text-lg font-bold text-black">
          E
        </div>

        <div className="text-left">
          <div className="text-sm font-semibold">
            ERKEK AI
          </div>
          <div className="text-[10px] uppercase tracking-[0.24em] text-gold-500/70">
            Digital mentor
          </div>
        </div>
      </Link>

      <LanguageSwitcher className="absolute right-5 top-6 z-20 sm:right-7 sm:top-8" />


      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-md items-center px-4 py-24">

        <div className="w-full rounded-[28px] border border-gold-500/15 bg-neutral-950/85 p-6 shadow-2xl backdrop-blur-xl sm:p-8">

          <div className="mb-7">

            <div className="mb-3 text-xs font-semibold uppercase tracking-[0.26em] text-gold-500">
              {eyebrow}
            </div>

            <h1 className="text-4xl font-semibold">
              {title}
            </h1>

            <p className="mt-2 text-sm leading-6 text-neutral-400">
              {description}
            </p>

          </div>

          {children}

        </div>

      </div>

    </main>
  );
}


export const inputClassName = `
  mt-2
  w-full
  rounded-2xl
  border
  border-white/[0.08]
  bg-black
  px-4
  py-3.5
  text-white
  outline-none
  transition
  placeholder:text-neutral-700
  focus:bg-neutral-950
`;


export const primaryButtonClassName = `
  flex
  w-full
  items-center
  justify-center
  rounded-2xl
  bg-white
  px-5
  py-3.5
  font-medium
  text-black
  transition
  disabled:cursor-not-allowed
  disabled:opacity-50
`;


export function FormError({ message }: { message: string }) {
  if (!message) {
    return null;
  }

  return (
    <div
      role="alert"
      className="rounded-xl border border-red-500/20 bg-red-500/[0.06] px-4 py-3 text-sm text-red-400"
    >
      {message}
    </div>
  );
}


export function FormSuccess({ message }: { message: string }) {
  return (
    <div
      role="status"
      className="rounded-xl border border-gold-500/25 bg-gold-500/[0.07] px-4 py-3 text-sm leading-6 text-gold-200"
    >
      {message}
    </div>
  );
}
