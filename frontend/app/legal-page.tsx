import Link from "next/link";

import { LEGAL_DATE } from "@/lib/legal";


// =====================================================
// ЗАҢДЫҚ БЕТТЕРДІҢ ОРТАҚ БЕЗЕНДІРУІ
// =====================================================

export function LegalPage({
  title,
  intro,
  children,
}: {
  title: string;
  intro: string;
  children: React.ReactNode;
}) {
  return (
    <main className="min-h-screen bg-black text-white">

      <header className="sticky top-0 z-30 border-b border-gold-500/10 bg-black/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 w-full max-w-3xl items-center justify-between px-4 sm:px-6">

          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white font-display text-lg font-bold text-black">
              E
            </div>
            <span className="text-sm font-bold tracking-[0.14em]">
              ERKEK AI
            </span>
          </Link>

          <nav className="flex gap-4 text-sm text-neutral-400">
            <Link href="/terms" className="transition hover:text-gold-300">
              Шарттар
            </Link>
            <Link href="/privacy" className="transition hover:text-gold-300">
              Құпиялылық
            </Link>
          </nav>

        </div>
      </header>


      <article className="mx-auto w-full max-w-3xl px-4 pb-24 pt-12 sm:px-6">

        <div className="mb-3 text-xs font-semibold uppercase tracking-[0.26em] text-gold-500">
          Құжат · {LEGAL_DATE}
        </div>

        <h1 className="text-4xl font-semibold leading-tight sm:text-5xl">
          {title}
        </h1>

        <p className="mt-5 leading-7 text-neutral-400">
          {intro}
        </p>

        <div className="gold-rule my-10 opacity-40" />

        <div className="legal-content space-y-10">
          {children}
        </div>

      </article>

    </main>
  );
}


export function Section({
  number,
  title,
  children,
}: {
  number: number;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h2 className="mb-4 flex items-baseline gap-3 text-2xl font-semibold">
        <span className="font-display text-gold-500/70">{number}.</span>
        {title}
      </h2>

      <div className="space-y-3 leading-7 text-neutral-300">
        {children}
      </div>
    </section>
  );
}


export function Bullets({ items }: { items: React.ReactNode[] }) {
  return (
    <ul className="space-y-2 pl-1">
      {items.map((item, index) => (
        <li key={index} className="flex gap-3">
          <span className="mt-2.5 h-1 w-1 shrink-0 rounded-full bg-gold-500" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}
