"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  ensureFreshToken,
  useSessionKeeper,
} from "@/lib/auth";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";


// =====================================================
// TYPES
// =====================================================

type TokenSum = {
  input: number;
  output: number;
  total: number;
  cost_usd: number | null;
};

type Stats = {
  generated_at: string;
  today: string;
  users: {
    total: number;
    new_today: number;
    new_7d: number;
    new_30d: number;
    active_today: number;
    active_7d: number;
    active_30d: number;
  };
  messages: {
    today: number;
    last_7d: number;
    last_30d: number;
  };
  tokens: {
    today: TokenSum;
    last_30d: TokenSum;
    daily_budget: number;
  };
  daily: {
    day: string;
    messages: number;
    active_users: number;
    new_users: number;
    telegram_messages?: number;
    tokens: number;
  }[];
  telegram?: {
    users: number;
    linked_to_site: number;
    messages_today: number;
    messages_7d: number;
    messages_30d: number;
  };
  feedback?: {
    last_30d: {
      likes: number;
      dislikes: number;
      satisfaction: number | null;
      by_persona: Record<string, { likes: number; dislikes: number }>;
    };
  };
  recent_users: {
    username: string;
    email: string | null;
    is_active: boolean;
    created_at: string | null;
    messages_30d: number;
    last_active: string | null;
  }[];
};


// =====================================================
// FORMAT
// =====================================================

const numberFormat = new Intl.NumberFormat("ru-RU");

function fmt(value: number) {
  return numberFormat.format(value);
}

function compact(value: number) {
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1).replace(".0", "")} млн`;
  }
  if (value >= 10_000) {
    return `${Math.round(value / 1000)} мың`;
  }
  return fmt(value);
}

function shortDay(iso: string) {
  const [, month, day] = iso.split("-");
  return `${day}.${month}`;
}

function formatDateTime(iso: string | null) {
  if (!iso) {
    return "—";
  }
  return new Date(iso).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}


// =====================================================
// PAGE
// =====================================================

export default function AdminPage() {
  const router = useRouter();

  const [stats, setStats] = useState<Stats | null>(null);
  const [state, setState] = useState<
    "loading" | "ready" | "forbidden" | "error"
  >("loading");

  useSessionKeeper(() => router.replace("/login"));

  const load = useCallback(async () => {
    const token = await ensureFreshToken();

    if (!token) {
      router.replace("/login");
      return;
    }

    try {
      const response = await fetch(`${API_URL}/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });

      if (response.status === 401) {
        router.replace("/login");
        return;
      }

      if (response.status === 403) {
        setState("forbidden");
        return;
      }

      if (!response.ok) {
        setState("error");
        return;
      }

      setStats(await response.json());
      setState("ready");
    } catch {
      setState("error");
    }
  }, [router]);

  useEffect(() => {
    // Деректерді жүктеу: setState тек await fetch-тен кейін шақырылады.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);


  return (
    <main className="min-h-dvh bg-black text-white">

      <header className="sticky top-0 z-30 border-b border-neutral-900 bg-black/90 backdrop-blur">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-6">

          <div className="flex items-center gap-3">
            <Link
              href="/chat"
              className="flex h-10 w-10 items-center justify-center rounded-xl text-neutral-400 transition hover:bg-neutral-900 hover:text-white"
              aria-label="Чатқа оралу"
            >
              ←
            </Link>
            <div>
              <div className="text-sm font-semibold">Әкімші панелі</div>
              <div className="text-xs text-neutral-500">ERKEK AI статистикасы</div>
            </div>
          </div>

          {state === "ready" && (
            <button
              type="button"
              onClick={() => void load()}
              className="rounded-xl border border-neutral-800 px-3 py-2 text-xs text-neutral-300 transition hover:border-gold-500/40 hover:text-gold-300 sm:text-sm"
            >
              ↻ Жаңарту
            </button>
          )}

        </div>
      </header>


      <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6">

        {state === "loading" && (
          <div className="py-24 text-center text-sm text-neutral-500">
            Жүктелуде...
          </div>
        )}

        {state === "forbidden" && (
          <div className="mx-auto max-w-md py-24 text-center">
            <h1 className="text-3xl font-semibold">Рұқсат жоқ</h1>
            <p className="mt-3 text-sm leading-6 text-neutral-400">
              Бұл бет тек ERKEK AI әкімшісіне арналған.
            </p>
            <Link
              href="/chat"
              className="mt-6 inline-flex rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black"
            >
              Чатқа оралу
            </Link>
          </div>
        )}

        {state === "error" && (
          <div className="mx-auto max-w-md py-24 text-center text-sm text-red-400">
            Статистиканы жүктеу мүмкін болмады.{" "}
            <button
              type="button"
              onClick={() => void load()}
              className="text-gold-400 underline-offset-4 hover:underline"
            >
              Қайталау
            </button>
          </div>
        )}

        {state === "ready" && stats && <Dashboard stats={stats} />}

      </div>

    </main>
  );
}


// =====================================================
// DASHBOARD
// =====================================================

function Dashboard({ stats }: { stats: Stats }) {
  const budget = stats.tokens.daily_budget;
  const budgetUsed = budget > 0
    ? Math.min(100, Math.round((stats.tokens.today.total / budget) * 100))
    : null;

  const cost = stats.tokens.last_30d.cost_usd;

  return (
    <div className="space-y-8">

      <div>
        <h1 className="text-3xl font-semibold sm:text-4xl">Бүгін</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Жаңартылды: {formatDateTime(stats.generated_at)} · күн Астана уақытымен
        </p>
      </div>


      {/* TILES */}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">

        <StatTile
          label="Пайдаланушылар"
          value={fmt(stats.users.total)}
          detail={`+${stats.users.new_today} бүгін · +${stats.users.new_7d} 7 күнде`}
        />

        <StatTile
          label="Белсенді (жазғандар)"
          value={fmt(stats.users.active_today)}
          detail={`7 күн: ${stats.users.active_7d} · 30 күн: ${stats.users.active_30d}`}
        />

        <StatTile
          label="Хабарламалар"
          value={fmt(stats.messages.today)}
          detail={`7 күн: ${fmt(stats.messages.last_7d)} · 30 күн: ${fmt(stats.messages.last_30d)}`}
        />

        <StatTile
          label="OpenAI токендері"
          value={compact(stats.tokens.today.total)}
          detail={
            budgetUsed !== null
              ? `Күндік лимиттің ${budgetUsed}% · 30 күн: ${compact(stats.tokens.last_30d.total)}`
              : `30 күн: ${compact(stats.tokens.last_30d.total)}`
          }
          meter={budgetUsed}
        />

      </div>

      {cost !== null && (
        <p className="text-sm text-neutral-400">
          OpenAI шығыны (30 күн, шамамен):{" "}
          <span className="font-semibold text-neutral-100">${cost.toFixed(2)}</span>
        </p>
      )}


      {/* TELEGRAM */}

      {stats.telegram && (
        <TelegramPanel
          telegram={stats.telegram}
          messagesToday={stats.messages.today}
          messages7d={stats.messages.last_7d}
          messages30d={stats.messages.last_30d}
        />
      )}


      {/* FEEDBACK */}

      {stats.feedback && (
        <FeedbackPanel feedback={stats.feedback.last_30d} />
      )}


      {/* CHARTS */}

      <div className="grid gap-4 lg:grid-cols-2">

        <BarChart
          title="Күндік хабарламалар"
          subtitle="Соңғы 14 күн"
          unit="хабарлама"
          points={stats.daily.map((d) => ({ day: d.day, value: d.messages }))}
        />

        <BarChart
          title="OpenAI токендері"
          subtitle="Соңғы 14 күн, барлық сұраныстар"
          unit="токен"
          points={stats.daily.map((d) => ({ day: d.day, value: d.tokens }))}
          formatValue={compact}
        />

      </div>

      <details className="rounded-2xl border border-neutral-900 bg-neutral-950 p-4 text-sm">
        <summary className="cursor-pointer text-neutral-400 transition hover:text-gold-300">
          Күндер бойынша кесте
        </summary>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[560px] text-left">
            <thead className="text-xs uppercase tracking-wider text-neutral-500">
              <tr>
                <th className="py-2 pr-4 font-medium">Күн</th>
                <th className="py-2 pr-4 text-right font-medium">Хабарлама</th>
                <th className="py-2 pr-4 text-right font-medium">Белсенді</th>
                <th className="py-2 pr-4 text-right font-medium">Жаңа</th>
                <th className="py-2 pr-4 text-right font-medium">Telegram</th>
                <th className="py-2 text-right font-medium">Токен</th>
              </tr>
            </thead>
            <tbody className="text-neutral-300">
              {[...stats.daily].reverse().map((d) => (
                <tr key={d.day} className="border-t border-neutral-900">
                  <td className="py-2 pr-4">{shortDay(d.day)}</td>
                  <td className="py-2 pr-4 text-right tabular-nums">{fmt(d.messages)}</td>
                  <td className="py-2 pr-4 text-right tabular-nums">{fmt(d.active_users)}</td>
                  <td className="py-2 pr-4 text-right tabular-nums">{fmt(d.new_users)}</td>
                  <td className="py-2 pr-4 text-right tabular-nums">{fmt(d.telegram_messages ?? 0)}</td>
                  <td className="py-2 text-right tabular-nums">{fmt(d.tokens)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>


      {/* USERS */}

      <section className="rounded-2xl border border-neutral-900 bg-neutral-950 p-4 sm:p-6">

        <h2 className="text-xl font-semibold">Соңғы тіркелгендер</h2>
        <p className="mt-1 text-sm text-neutral-500">
          Ең соңғы {stats.recent_users.length} пайдаланушы
        </p>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="text-xs uppercase tracking-wider text-neutral-500">
              <tr>
                <th className="py-2 pr-4 font-medium">Пайдаланушы</th>
                <th className="py-2 pr-4 font-medium">Тіркелді</th>
                <th className="py-2 pr-4 text-right font-medium">Хабарлама (30 күн)</th>
                <th className="py-2 font-medium">Соңғы белсенділік</th>
              </tr>
            </thead>
            <tbody>
              {stats.recent_users.map((u) => (
                <tr key={`${u.username}:${u.email ?? ""}`} className="border-t border-neutral-900 align-top">
                  <td className="py-3 pr-4">
                    <div className="font-medium text-neutral-100">{u.username}</div>
                    <div className="text-xs text-neutral-500">{u.email ?? "Telegram"}</div>
                  </td>
                  <td className="py-3 pr-4 text-neutral-400">{formatDateTime(u.created_at)}</td>
                  <td className="py-3 pr-4 text-right tabular-nums text-neutral-200">{fmt(u.messages_30d)}</td>
                  <td className="py-3 text-neutral-400">
                    {u.last_active ? shortDay(u.last_active) : "әлі жазбаған"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </section>

    </div>
  );
}


// =====================================================
// STAT TILE
// =====================================================

function TelegramPanel({
  telegram,
  messagesToday,
  messages7d,
  messages30d,
}: {
  telegram: NonNullable<Stats["telegram"]>;
  messagesToday: number;
  messages7d: number;
  messages30d: number;
}) {
  const share = (part: number, total: number) =>
    total > 0 ? Math.round((part / total) * 100) : null;

  const share30 = share(telegram.messages_30d, messages30d);
  const telegramOnly = telegram.users - telegram.linked_to_site;

  return (
    <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">

      <StatTile
        label="Telegram хабарламалары"
        value={fmt(telegram.messages_today)}
        detail={`Бүгін сайтта: ${fmt(Math.max(messagesToday - telegram.messages_today, 0))} · 7 күн Telegram: ${fmt(telegram.messages_7d)} / сайт: ${fmt(Math.max(messages7d - telegram.messages_7d, 0))}`}
      />

      <StatTile
        label="Telegram үлесі (30 күн)"
        value={share30 === null ? "—" : `${share30}%`}
        detail={`Telegram: ${fmt(telegram.messages_30d)} · сайт: ${fmt(Math.max(messages30d - telegram.messages_30d, 0))}`}
        meter={share30}
      />

      <StatTile
        label="Telegram пайдаланушылары"
        value={fmt(telegram.users)}
        detail={`Тек Telegram: ${fmt(telegramOnly)} · сайтқа байланған: ${fmt(telegram.linked_to_site)}`}
      />

    </section>
  );
}


const PERSONA_NAMES: Record<string, string> = {
  brother: "Аға / Брат",
  hardcore: "Қатал",
  strategist: "Стратег",
};


function FeedbackPanel({
  feedback,
}: {
  feedback: NonNullable<Stats["feedback"]>["last_30d"];
}) {
  const total = feedback.likes + feedback.dislikes;
  const personas = Object.entries(feedback.by_persona).sort(
    (a, b) => (b[1].likes + b[1].dislikes) - (a[1].likes + a[1].dislikes)
  );

  return (
    <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">

      <StatTile
        label="Жауап сапасы (30 күн)"
        value={feedback.satisfaction === null ? "—" : `${feedback.satisfaction}%`}
        detail={
          total === 0
            ? "Әзірге баға жоқ"
            : `👍 ${fmt(feedback.likes)} · 👎 ${fmt(feedback.dislikes)} · барлығы ${fmt(total)}`
        }
        meter={feedback.satisfaction}
      />

      {personas.length > 0 && (
        <div className="rounded-2xl border border-neutral-900 bg-neutral-950 p-5 sm:col-span-1 lg:col-span-3">
          <div className="text-xs font-medium uppercase tracking-wider text-neutral-500">
            Мінез бойынша
          </div>

          <table className="mt-3 w-full text-left text-sm">
            <thead className="text-xs text-neutral-500">
              <tr>
                <th className="py-1.5 pr-4 font-medium">Мінез</th>
                <th className="py-1.5 pr-4 text-right font-medium">👍</th>
                <th className="py-1.5 pr-4 text-right font-medium">👎</th>
                <th className="py-1.5 text-right font-medium">Ұнағаны</th>
              </tr>
            </thead>
            <tbody className="text-neutral-300">
              {personas.map(([id, counts]) => {
                const sum = counts.likes + counts.dislikes;
                return (
                  <tr key={id} className="border-t border-neutral-900">
                    <td className="py-1.5 pr-4">{PERSONA_NAMES[id] ?? id}</td>
                    <td className="py-1.5 pr-4 text-right tabular-nums">{fmt(counts.likes)}</td>
                    <td className="py-1.5 pr-4 text-right tabular-nums">{fmt(counts.dislikes)}</td>
                    <td className="py-1.5 text-right tabular-nums">
                      {sum ? `${Math.round((counts.likes / sum) * 100)}%` : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

    </section>
  );
}


function StatTile({
  label,
  value,
  detail,
  meter = null,
}: {
  label: string;
  value: string;
  detail: string;
  meter?: number | null;
}) {
  return (
    <div className="rounded-2xl border border-neutral-900 bg-neutral-950 p-5">
      <div className="text-xs font-medium uppercase tracking-wider text-neutral-500">
        {label}
      </div>
      <div className="mt-2 font-display text-4xl font-semibold tabular-nums text-neutral-50">
        {value}
      </div>
      {meter !== null && (
        <div
          className="mt-3 h-1.5 overflow-hidden rounded-full bg-neutral-900"
          role="meter"
          aria-valuenow={meter}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={label}
        >
          <div
            className="h-full rounded-full bg-gold-500"
            style={{ width: `${Math.max(meter, 2)}%` }}
          />
        </div>
      )}
      <div className="mt-2 text-xs leading-5 text-neutral-400">{detail}</div>
    </div>
  );
}


// =====================================================
// BAR CHART (бір көрсеткіш, бір ось)
// =====================================================

function BarChart({
  title,
  subtitle,
  unit,
  points,
  formatValue = fmt,
}: {
  title: string;
  subtitle: string;
  unit: string;
  points: { day: string; value: number }[];
  formatValue?: (value: number) => string;
}) {
  const max = Math.max(...points.map((p) => p.value), 0);
  const top = niceMax(max);

  return (
    <section className="rounded-2xl border border-neutral-900 bg-neutral-950 p-4 sm:p-5">

      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="text-xs text-neutral-500">{subtitle}</p>

      <div className="mt-4 flex gap-2">

        {/* Y axis */}
        <div className="flex h-44 flex-col justify-between pb-6 text-right text-[10px] tabular-nums text-neutral-600">
          <span>{formatValue(top)}</span>
          <span>{top % 2 === 0 ? formatValue(top / 2) : ""}</span>
          <span>0</span>
        </div>

        <div className="relative flex-1">

          {/* Grid */}
          <div className="pointer-events-none absolute inset-x-0 top-0 h-[152px]">
            <div className="absolute inset-x-0 top-0 border-t border-neutral-900" />
            <div className="absolute inset-x-0 top-1/2 border-t border-neutral-900" />
            <div className="absolute inset-x-0 bottom-0 border-t border-neutral-800" />
          </div>

          {/* Bars */}
          <div className="relative flex h-[152px] items-end gap-[2px]">
            {points.map((p) => {
              const height = top > 0 ? (p.value / top) * 100 : 0;
              return (
                <div
                  key={p.day}
                  className="group relative flex h-full flex-1 items-end justify-center"
                  tabIndex={0}
                  aria-label={`${shortDay(p.day)}: ${fmt(p.value)} ${unit}`}
                >
                  <div
                    className="w-full max-w-7 rounded-t-[4px] bg-gold-500/80 transition group-hover:bg-gold-400 group-focus:bg-gold-400"
                    style={{ height: p.value > 0 ? `max(${height}%, 3px)` : "0" }}
                  />
                  <div className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-1 hidden -translate-x-1/2 whitespace-nowrap rounded-lg border border-neutral-800 bg-black px-2.5 py-1.5 text-xs shadow-xl group-hover:block group-focus:block">
                    <div className="text-neutral-400">{shortDay(p.day)}</div>
                    <div className="font-semibold tabular-nums text-neutral-100">
                      {fmt(p.value)} {unit}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* X labels: every other day */}
          <div className="mt-2 flex gap-[2px] text-[10px] tabular-nums text-neutral-600">
            {points.map((p, i) => (
              <div key={p.day} className="flex-1 text-center">
                {i % 2 === points.length % 2 ? "" : shortDay(p.day)}
              </div>
            ))}
          </div>

        </div>
      </div>

    </section>
  );
}


// Осьтің жоғарғы мәнін «әдемі» санға дөңгелектейді (1, 2, 5 × 10ⁿ).
function niceMax(value: number) {
  if (value <= 0) {
    return 1;
  }
  const exponent = Math.floor(Math.log10(value));
  const base = 10 ** exponent;
  for (const step of [1, 2, 5, 10]) {
    if (step * base >= value) {
      return step * base;
    }
  }
  return 10 * base;
}
