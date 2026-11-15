"use client";

import { useRouter } from "next/navigation";

import {
  getValidToken,
} from "@/lib/auth";


export default function Home() {
  const router = useRouter();


  // =====================================================
  // START
  // =====================================================

  function handleStart() {
    const token = getValidToken();

    if (token) {
      router.push("/chat");
    } else {
      router.push("/register");
    }
  }


  // =====================================================
  // UI
  // =====================================================

  return (
    <main className="relative min-h-screen overflow-hidden bg-black text-white">

      {/* BACKGROUND */}

      <div className="pointer-events-none absolute inset-x-0 top-0 h-[1100px]">

        <div className="bg-ornament absolute inset-0" />

        <div className="absolute left-1/2 top-[-320px] h-[640px] w-[900px] -translate-x-1/2 rounded-full bg-gold-500/[0.09] blur-3xl" />

      </div>


      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <header className="sticky top-0 z-30 border-b border-gold-500/10 bg-black/70 backdrop-blur-xl">

        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-6">

          <button
            onClick={() =>
              router.push("/")
            }
            className="flex items-center gap-3"
          >
            <Logo />

            <div className="text-left">

              <div className="text-sm font-bold tracking-[0.14em]">
                ERKEK AI
              </div>

              <div className="text-[10px] uppercase tracking-[0.24em] text-gold-500/70">
                Digital mentor
              </div>

            </div>
          </button>


          <div className="flex items-center gap-2">

            <button
              onClick={() =>
                router.push("/login")
              }
              className="hidden rounded-full px-4 py-2 text-sm text-neutral-400 transition hover:text-gold-300 sm:block"
            >
              Кіру
            </button>

            <button
              onClick={handleStart}
              className="rounded-full bg-white px-5 py-2 text-sm font-semibold text-black transition"
            >
              Бастау
            </button>

          </div>

        </div>

      </header>


      {/* ================================================= */}
      {/* HERO */}
      {/* ================================================= */}

      <section className="relative z-10">

        <div className="mx-auto flex w-full max-w-6xl flex-col items-center px-4 pb-24 pt-20 text-center sm:px-6 sm:pt-28">

          <div className="mb-8 inline-flex items-center gap-2.5 rounded-full border border-gold-500/25 bg-gold-500/[0.06] px-4 py-2 text-xs font-medium text-gold-300">

            <span className="text-[9px] text-gold-500">◆</span>

            AI негізіндегі жеке digital mentor

          </div>


          <h1 className="max-w-4xl text-5xl font-semibold leading-[1.02] sm:text-7xl lg:text-[96px]">

            Өмірдегі ойларыңды

            <span className="text-gold-gradient block pb-2 italic">
              бірге талдайық.
            </span>

          </h1>


          <p className="mt-8 max-w-2xl text-base leading-8 text-neutral-400 sm:text-lg">

            ERKEK AI — жұмыс, қаржы, отбасы,
            мақсаттар және күнделікті шешімдер туралы
            сөйлесуге арналған жеке AI көмекші.

          </p>


          <div className="mt-10 flex w-full max-w-md flex-col gap-3 sm:flex-row sm:justify-center">

            <button
              onClick={handleStart}
              className="flex flex-1 items-center justify-center gap-2 rounded-full bg-white px-7 py-4 font-semibold text-black transition"
            >
              ERKEK AI-мен сөйлесу
              <span aria-hidden>→</span>
            </button>

            <button
              onClick={() =>
                router.push("/login")
              }
              className="flex items-center justify-center rounded-full border border-gold-500/25 px-7 py-4 font-medium text-neutral-200 transition hover:border-gold-500/50 hover:text-gold-200"
            >
              Кіру
            </button>

          </div>


          {/* CHAT PREVIEW */}

          <div className="relative mt-20 w-full max-w-3xl">

            <div className="absolute -inset-8 rounded-[40px] bg-gold-500/[0.06] blur-3xl" />

            <div className="relative overflow-hidden rounded-[28px] border border-gold-500/15 bg-neutral-950/90 text-left shadow-2xl">

              <div className="flex h-14 items-center gap-3 border-b border-gold-500/10 px-5">

                <Logo small />

                <div>
                  <div className="text-xs font-semibold tracking-[0.12em]">
                    ERKEK AI
                  </div>
                  <div className="flex items-center gap-1.5 text-[10px] text-neutral-500">
                    <span className="h-1.5 w-1.5 rounded-full bg-gold-400" />
                    онлайн
                  </div>
                </div>

              </div>


              <div className="space-y-6 p-5 sm:p-8">

                <div className="flex justify-end">

                  <div className="max-w-[85%] rounded-2xl rounded-br-md border border-neutral-800 bg-neutral-900 px-4 py-3 text-sm leading-6 text-neutral-100 sm:max-w-[65%]">
                    Жұмысымды ауыстырғым келеді,
                    бірақ неден бастарымды білмей жүрмін.
                  </div>

                </div>


                <div className="flex max-w-2xl gap-3">

                  <div className="mt-0.5 w-0.5 shrink-0 rounded-full bg-gradient-to-b from-gold-400 to-transparent" />

                  <div className="text-sm leading-7 text-neutral-300 sm:text-base">
                    Алдымен асықпай жағдайыңды бөліп қарайық.
                    Қазір сен үшін ең маңыздысы —
                    <span className="text-gold-300"> жаңа бағыт таңдау ма</span>,
                    табысты көбейту ме,
                    әлде тұрақты жұмыс табу ма?
                  </div>

                </div>


                <div className="flex items-center justify-between rounded-full border border-neutral-800 bg-black py-1.5 pl-5 pr-1.5">

                  <div className="text-sm text-neutral-600">
                    Не ойландырып жүр?
                  </div>

                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-black">
                    ↑
                  </div>

                </div>

              </div>

            </div>

          </div>

        </div>

      </section>


      {/* ================================================= */}
      {/* FEATURES */}
      {/* ================================================= */}

      <section className="relative z-10">

        <div className="mx-auto w-full max-w-6xl px-4 py-24 sm:px-6">

          <SectionHeading
            eyebrow="Мүмкіндіктер"
            title="Жай chatbot емес."
            text="ERKEK AI әңгіменің контекстін сақтап, әр тақырыпты бөлек жүргізуге арналған."
          />


          <div className="mt-14 grid gap-px overflow-hidden rounded-[28px] border border-gold-500/15 bg-gold-500/15 md:grid-cols-2 lg:grid-cols-3">

            <FeatureCard
              number="01"
              title="Жеке memory"
              description="Саған қатысты маңызды контекстті есте сақтап, кейінгі жауаптарды соған бейімдейді."
            />

            <FeatureCard
              number="02"
              title="Бөлек әңгімелер"
              description="Жұмыс, қаржы немесе отбасы туралы чаттар бір-бірімен араласпайды."
            />

            <FeatureCard
              number="03"
              title="Контекст сақталады"
              description="Бұрынғы әңгіменің маңызды бөліктерін summary арқылы сақтап отырады."
            />

            <FeatureCard
              number="04"
              title="Қазақша сөйлеседі"
              description="Қазақша және орысша хабарламаларды түсініп, тілге сай жауап береді."
            />

            <FeatureCard
              number="05"
              title="Жауап стилі"
              description="Сұраққа қарай қысқа, аналитикалық немесе қолдау стиліндегі жауап таңдайды."
            />

            <FeatureCard
              number="06"
              title="Қауіпсіздік"
              description="Қауіпті жағдайларды бөлек анықтап, қауіпсіз жауап логикасын қолданады."
            />

          </div>

        </div>

      </section>


      {/* ================================================= */}
      {/* HOW IT WORKS */}
      {/* ================================================= */}

      <section className="relative z-10">

        <div className="mx-auto w-full max-w-6xl px-4 py-24 sm:px-6">

          <div className="grid gap-14 lg:grid-cols-2 lg:items-center">

            <div>

              <div className="mb-4 flex items-center gap-3 text-xs font-semibold uppercase tracking-[0.28em] text-gold-500">
                <span className="h-px w-8 bg-gold-500/60" />
                Қалай жұмыс істейді
              </div>

              <h2 className="max-w-xl text-4xl font-semibold leading-tight sm:text-5xl">
                Бір әңгімеден келесі әңгімеге дейін
                <span className="text-gold-gradient italic"> контекст жоғалмайды.</span>
              </h2>

              <p className="mt-6 max-w-xl leading-8 text-neutral-400">
                Әр чаттың жеке history және summary жүйесі бар.
                Ал ұзақ мерзімді маңызды ақпарат user memory-де
                сақталады.
              </p>

            </div>


            <ol className="relative space-y-4 border-l border-gold-500/20 pl-8">

              <ProcessItem
                number="1"
                title="Жаңа чат аш"
                description="Әр тақырып үшін бөлек әңгіме баста."
              />

              <ProcessItem
                number="2"
                title="Еркін сөйлес"
                description="ERKEK AI контекст, тіл және тақырыпты талдайды."
              />

              <ProcessItem
                number="3"
                title="Әңгімені жалғастыр"
                description="Кейін қайта кіргенде бұрынғы чат тарихы сақталады."
              />

            </ol>

          </div>

        </div>

      </section>


      {/* ================================================= */}
      {/* CTA */}
      {/* ================================================= */}

      <section className="relative z-10">

        <div className="mx-auto w-full max-w-6xl px-4 py-24 sm:px-6">

          <div className="relative overflow-hidden rounded-[32px] border border-gold-500/20 bg-neutral-950 px-6 py-16 text-center sm:px-12 sm:py-20">

            <div className="bg-ornament absolute inset-0" />

            <div className="absolute left-1/2 top-[-220px] h-[420px] w-[640px] -translate-x-1/2 rounded-full bg-gold-500/[0.1] blur-3xl" />

            <div className="relative">

              <div className="mb-6 text-gold-500">◆</div>

              <h2 className="mx-auto max-w-3xl text-4xl font-semibold leading-tight sm:text-5xl">
                Кейде мәселені шешу үшін
                алдымен оны дұрыс талқылау керек.
              </h2>

              <p className="mx-auto mt-5 max-w-xl leading-7 text-neutral-400">
                ERKEK AI-мен жаңа әңгіме баста.
              </p>

              <button
                onClick={handleStart}
                className="mt-9 rounded-full bg-white px-8 py-4 font-semibold text-black transition"
              >
                Қазір бастау
              </button>

            </div>

          </div>

        </div>

      </section>


      {/* ================================================= */}
      {/* FOOTER */}
      {/* ================================================= */}

      <footer className="relative z-10">

        <div className="gold-rule mx-auto max-w-6xl opacity-40" />

        <div className="mx-auto flex w-full max-w-6xl flex-col gap-5 px-4 py-8 text-sm text-neutral-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">

          <div className="flex items-center gap-2">
            <span className="text-[9px] text-gold-500">◆</span>
            © 2026 ERKEK AI
          </div>

          <div className="flex gap-6">

            <button
              onClick={() =>
                router.push("/login")
              }
              className="transition hover:text-gold-300"
            >
              Кіру
            </button>

            <button
              onClick={() =>
                router.push("/register")
              }
              className="transition hover:text-gold-300"
            >
              Тіркелу
            </button>

          </div>

        </div>

      </footer>

    </main>
  );
}


// =====================================================
// LOGO
// =====================================================

function Logo({ small = false }: { small?: boolean }) {
  return (
    <div
      className={`flex shrink-0 items-center justify-center rounded-xl bg-white font-display font-bold text-black ${
        small ? "h-8 w-8 text-base" : "h-9 w-9 text-lg"
      }`}
    >
      E
    </div>
  );
}


// =====================================================
// SECTION HEADING
// =====================================================

function SectionHeading({
  eyebrow,
  title,
  text,
}: {
  eyebrow: string;
  title: string;
  text: string;
}) {
  return (
    <div className="max-w-2xl">

      <div className="mb-4 flex items-center gap-3 text-xs font-semibold uppercase tracking-[0.28em] text-gold-500">
        <span className="h-px w-8 bg-gold-500/60" />
        {eyebrow}
      </div>

      <h2 className="text-4xl font-semibold sm:text-5xl">
        {title}
      </h2>

      <p className="mt-4 leading-7 text-neutral-400">
        {text}
      </p>

    </div>
  );
}


// =====================================================
// FEATURE CARD
// =====================================================

function FeatureCard({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div className="group relative min-h-56 bg-neutral-950 p-7 transition hover:bg-neutral-900">

      <div className="font-display text-3xl font-semibold text-gold-500/50 transition group-hover:text-gold-400">
        {number}
      </div>

      <div className="mt-10">

        <h3 className="text-lg font-semibold">
          {title}
        </h3>

        <p className="mt-3 text-sm leading-7 text-neutral-400">
          {description}
        </p>

      </div>

    </div>
  );
}


// =====================================================
// PROCESS ITEM
// =====================================================

function ProcessItem({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <li className="relative rounded-2xl border border-neutral-800 bg-neutral-950 p-5 transition hover:border-gold-500/30">

      <div className="absolute -left-[49px] top-5 flex h-8 w-8 items-center justify-center rounded-full border border-gold-500/40 bg-black font-display text-sm font-bold text-gold-400">
        {number}
      </div>

      <div className="font-semibold">
        {title}
      </div>

      <div className="mt-1 text-sm leading-6 text-neutral-400">
        {description}
      </div>

    </li>
  );
}
