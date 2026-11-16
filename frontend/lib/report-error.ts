// Браузердегі қатені серверге жібереді (әкімшінің Telegram-ына барады).
// Бір бетте бір қате бір рет қана жіберіледі.

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

const reported = new Set<string>();
const MAX_PER_PAGE = 5;

export function reportClientError(error: unknown, context?: string) {
  if (typeof window === "undefined") {
    return;
  }

  const err = error instanceof Error ? error : null;
  const message = (
    (context ? `${context}: ` : "") +
    (err ? `${err.name}: ${err.message}` : String(error))
  ).slice(0, 1000);

  // Браузер кеңейтулері мен желі үзілуінен келетін шу.
  if (
    !message ||
    /ResizeObserver loop|Failed to fetch|NetworkError|Load failed|AbortError/i.test(message)
  ) {
    return;
  }

  if (reported.has(message) || reported.size >= MAX_PER_PAGE) {
    return;
  }

  reported.add(message);

  try {
    void fetch(`${API_URL}/client-errors`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      keepalive: true,
      body: JSON.stringify({
        message,
        stack: err?.stack?.slice(0, 4000) ?? null,
        url: window.location.href.split("?")[0].slice(0, 500),
        user_agent: navigator.userAgent.slice(0, 300),
      }),
    }).catch(() => {});
  } catch {
    // Есеп беру ешқашан бетті бұзбауы керек.
  }
}
