"use client";

import { useRouter } from "next/navigation";


export default function Home() {
  const router = useRouter();


  // =====================================================
  // START
  // =====================================================

  function handleStart() {
    const token = localStorage.getItem(
      "access_token"
    );

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
    <main className="min-h-screen overflow-hidden bg-black text-white">

      {/* ================================================= */}
      {/* BACKGROUND */}
      {/* ================================================= */}

      <div className="pointer-events-none fixed inset-0">

        <div className="absolute left-1/2 top-[-250px] h-[500px] w-[800px] -translate-x-1/2 rounded-full bg-white/[0.035] blur-3xl" />

        <div className="absolute bottom-[-300px] right-[-200px] h-[600px] w-[600px] rounded-full bg-white/[0.025] blur-3xl" />

      </div>


      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <header className="relative z-20 border-b border-white/[0.06]">

        <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-5 sm:px-6 lg:px-8">

          {/* LOGO */}

          <button
            onClick={() =>
              router.push("/")
            }
            className="flex items-center gap-3"
          >

            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-white text-sm font-black text-black">
              E
            </div>

            <div className="text-left">

              <div className="text-sm font-semibold tracking-wide">
                ERKEK AI
              </div>

              <div className="text-[10px] uppercase tracking-[0.2em] text-neutral-600">
                Digital mentor
              </div>

            </div>

          </button>


          {/* NAV */}

          <div className="flex items-center gap-2">

            <button
              onClick={() =>
                router.push("/login")
              }
              className="
                hidden
                rounded-xl
                px-4
                py-2
                text-sm
                text-neutral-400
                transition
                hover:bg-white/[0.05]
                hover:text-white
                sm:block
              "
            >
              Кіру
            </button>

            <button
              onClick={handleStart}
              className="
                rounded-xl
                bg-white
                px-4
                py-2
                text-sm
                font-medium
                text-black
                transition
                hover:bg-neutral-200
              "
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

        <div className="mx-auto flex min-h-[760px] w-full max-w-7xl flex-col items-center justify-center px-5 py-24 text-center sm:px-6 lg:px-8">

          {/* BADGE */}

          <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-xs text-neutral-400">

            <span className="h-1.5 w-1.5 rounded-full bg-green-400" />

            AI негізіндегі жеке digital mentor

          </div>


          {/* TITLE */}

          <h1 className="max-w-5xl text-5xl font-semibold tracking-[-0.05em] sm:text-6xl lg:text-8xl">

            Өмірдегі ойларыңды

            <span className="block bg-gradient-to-b from-white to-neutral-600 bg-clip-text text-transparent">
              бірге талдайық.
            </span>

          </h1>


          {/* DESCRIPTION */}

          <p className="mt-8 max-w-2xl text-base leading-8 text-neutral-500 sm:text-lg">

            ERKEK AI — жұмыс, қаржы, отбасы,
            мақсаттар және күнделікті шешімдер туралы
            сөйлесуге арналған жеке AI көмекші.

          </p>


          {/* BUTTONS */}

          <div className="mt-10 flex w-full max-w-md flex-col gap-3 sm:flex-row sm:justify-center">

            <button
              onClick={handleStart}
              className="
                flex
                h-13
                flex-1
                items-center
                justify-center
                rounded-2xl
                bg-white
                px-6
                py-4
                font-medium
                text-black
                transition
                hover:bg-neutral-200
              "
            >
              ERKEK AI-мен сөйлесу
            </button>

            <button
              onClick={() =>
                router.push("/login")
              }
              className="
                flex
                h-13
                items-center
                justify-center
                rounded-2xl
                border
                border-white/10
                bg-white/[0.02]
                px-6
                py-4
                font-medium
                text-neutral-300
                transition
                hover:bg-white/[0.06]
                hover:text-white
              "
            >
              Кіру
            </button>

          </div>


          {/* CHAT PREVIEW */}

          <div className="relative mt-20 w-full max-w-4xl">

            <div className="absolute -inset-10 bg-white/[0.025] blur-3xl" />

            <div className="relative overflow-hidden rounded-3xl border border-white/[0.08] bg-neutral-950/80 shadow-2xl">

              {/* FAKE WINDOW HEADER */}

              <div className="flex h-14 items-center border-b border-white/[0.06] px-5">

                <div className="flex gap-2">

                  <div className="h-2.5 w-2.5 rounded-full bg-neutral-700" />
                  <div className="h-2.5 w-2.5 rounded-full bg-neutral-700" />
                  <div className="h-2.5 w-2.5 rounded-full bg-neutral-700" />

                </div>

                <div className="mx-auto pr-12 text-xs text-neutral-600">
                  ERKEK AI
                </div>

              </div>


              {/* FAKE CHAT */}

              <div className="space-y-8 p-5 text-left sm:p-8">

                <div className="flex justify-end">

                  <div className="max-w-[85%] rounded-2xl bg-white px-4 py-3 text-sm leading-6 text-black sm:max-w-[65%]">
                    Жұмысымды ауыстырғым келеді,
                    бірақ неден бастарымды білмей жүрмін.
                  </div>

                </div>


                <div className="max-w-2xl">

                  <div className="mb-2 text-xs font-medium text-neutral-600">
                    ERKEK AI
                  </div>

                  <div className="text-sm leading-7 text-neutral-300 sm:text-base">
                    Алдымен асықпай жағдайыңды бөліп қарайық.
                    Қазір сен үшін ең маңыздысы —
                    жаңа бағыт таңдау ма, табысты көбейту ме,
                    әлде тұрақты жұмыс табу ма?
                  </div>

                </div>


                <div className="rounded-2xl border border-white/[0.06] bg-black p-2">

                  <div className="flex items-center justify-between">

                    <div className="px-3 text-sm text-neutral-700">
                      Не ойландырып жүр?
                    </div>

                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-black">
                      ↑
                    </div>

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

      <section className="relative z-10 border-t border-white/[0.06]">

        <div className="mx-auto w-full max-w-7xl px-5 py-24 sm:px-6 lg:px-8">

          <div className="mb-14 max-w-2xl">

            <div className="mb-4 text-xs uppercase tracking-[0.25em] text-neutral-600">
              Мүмкіндіктер
            </div>

            <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
              Жай chatbot емес.
            </h2>

            <p className="mt-4 leading-7 text-neutral-500">
              ERKEK AI әңгіменің контекстін сақтап,
              әр тақырыпты бөлек жүргізуге арналған.
            </p>

          </div>


          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">

            {/* FEATURE 1 */}

            <FeatureCard
              number="01"
              title="Жеке memory"
              description="Саған қатысты маңызды контекстті есте сақтап, кейінгі жауаптарды соған бейімдейді."
            />

            {/* FEATURE 2 */}

            <FeatureCard
              number="02"
              title="Бөлек әңгімелер"
              description="Жұмыс, қаржы немесе отбасы туралы чаттар бір-бірімен араласпайды."
            />

            {/* FEATURE 3 */}

            <FeatureCard
              number="03"
              title="Контекст сақталады"
              description="Бұрынғы әңгіменің маңызды бөліктерін summary арқылы сақтап отырады."
            />

            {/* FEATURE 4 */}

            <FeatureCard
              number="04"
              title="Қазақша сөйлеседі"
              description="Қазақша және орысша хабарламаларды түсініп, тілге сай жауап береді."
            />

            {/* FEATURE 5 */}

            <FeatureCard
              number="05"
              title="Жауап стилі"
              description="Сұраққа қарай қысқа, аналитикалық немесе қолдау стиліндегі жауап таңдайды."
            />

            {/* FEATURE 6 */}

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

      <section className="relative z-10 border-t border-white/[0.06]">

        <div className="mx-auto w-full max-w-7xl px-5 py-24 sm:px-6 lg:px-8">

          <div className="grid gap-16 lg:grid-cols-2 lg:items-center">

            <div>

              <div className="mb-4 text-xs uppercase tracking-[0.25em] text-neutral-600">
                Қалай жұмыс істейді
              </div>

              <h2 className="max-w-xl text-3xl font-semibold tracking-tight sm:text-5xl">
                Бір әңгімеден
                келесі әңгімеге дейін
                контекст жоғалмайды.
              </h2>

              <p className="mt-6 max-w-xl leading-8 text-neutral-500">
                Әр чаттың жеке history және summary жүйесі бар.
                Ал ұзақ мерзімді маңызды ақпарат user memory-де
                сақталады.
              </p>

            </div>


            <div className="space-y-3">

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

            </div>

          </div>

        </div>

      </section>


      {/* ================================================= */}
      {/* CTA */}
      {/* ================================================= */}

      <section className="relative z-10 border-t border-white/[0.06]">

        <div className="mx-auto w-full max-w-7xl px-5 py-24 sm:px-6 lg:px-8">

          <div className="relative overflow-hidden rounded-[32px] border border-white/[0.08] bg-neutral-950 px-6 py-16 text-center sm:px-12 sm:py-20">

            <div className="absolute left-1/2 top-[-200px] h-[400px] w-[600px] -translate-x-1/2 rounded-full bg-white/[0.04] blur-3xl" />

            <div className="relative">

              <h2 className="mx-auto max-w-3xl text-3xl font-semibold tracking-tight sm:text-5xl">
                Кейде мәселені шешу үшін
                алдымен оны дұрыс талқылау керек.
              </h2>

              <p className="mx-auto mt-5 max-w-xl leading-7 text-neutral-500">
                ERKEK AI-мен жаңа әңгіме баста.
              </p>

              <button
                onClick={handleStart}
                className="
                  mt-8
                  rounded-2xl
                  bg-white
                  px-7
                  py-4
                  font-medium
                  text-black
                  transition
                  hover:bg-neutral-200
                "
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

      <footer className="relative z-10 border-t border-white/[0.06]">

        <div className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-5 py-8 text-sm text-neutral-600 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">

          <div>
            © 2026 ERKEK AI
          </div>

          <div className="flex gap-5">

            <button
              onClick={() =>
                router.push("/login")
              }
              className="transition hover:text-neutral-300"
            >
              Кіру
            </button>

            <button
              onClick={() =>
                router.push("/register")
              }
              className="transition hover:text-neutral-300"
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
    <div
      className="
        group
        min-h-60
        rounded-3xl
        border
        border-white/[0.07]
        bg-white/[0.02]
        p-6
        transition
        hover:border-white/[0.13]
        hover:bg-white/[0.035]
      "
    >

      <div className="text-xs font-medium text-neutral-700">
        {number}
      </div>

      <div className="mt-16">

        <h3 className="text-xl font-medium">
          {title}
        </h3>

        <p className="mt-3 text-sm leading-7 text-neutral-500">
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
    <div className="flex gap-5 rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5">

      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white text-sm font-semibold text-black">
        {number}
      </div>

      <div>

        <div className="font-medium">
          {title}
        </div>

        <div className="mt-1 text-sm leading-6 text-neutral-500">
          {description}
        </div>

      </div>

    </div>
  );
}