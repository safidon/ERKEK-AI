"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

export default function ChatPage() {
  const router = useRouter();

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Сәлем. Қандай мәселені бірге талдаймыз?",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      router.replace("/login");
    }
  }, [router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  async function sendMessage() {
    const message = input.trim();

    if (!message || loading) {
      return;
    }

    const token = localStorage.getItem(
      "access_token"
    );

    if (!token) {
      router.replace("/login");
      return;
    }

    setError("");

    setMessages((current) => [
      ...current,
      {
        role: "user",
        content: message,
      },
    ]);

    setInput("");
    setLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            message,
          }),
        }
      );

      if (response.status === 401) {
        localStorage.removeItem(
          "access_token"
        );

        router.replace("/login");
        return;
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Сұраныс кезінде қате шықты."
        );
      }

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: data.answer,
        },
      ]);
    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError("Белгісіз қате шықты.");
      }
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    localStorage.removeItem("access_token");
    router.replace("/login");
  }

  function handleKeyDown(
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      sendMessage();
    }
  }

  return (
    <main className="flex min-h-screen flex-col bg-black text-white">

      {/* HEADER */}

      <header className="border-b border-neutral-900">
        <div className="mx-auto flex h-16 w-full max-w-4xl items-center justify-between px-5">

          <div>
            <div className="font-semibold">
              ERKEK AI
            </div>

            <div className="text-xs text-neutral-500">
              Digital mentor
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="text-sm text-neutral-400 transition hover:text-white"
          >
            Шығу
          </button>

        </div>
      </header>

      {/* CHAT */}

      <section className="flex-1 overflow-y-auto">

        <div className="mx-auto w-full max-w-4xl px-5 py-8">

          <div className="space-y-7">

            {messages.map(
              (message, index) => (
                <div
                  key={index}
                  className={
                    message.role === "user"
                      ? "flex justify-end"
                      : "flex justify-start"
                  }
                >
                  <div
                    className={
                      message.role === "user"
                        ? "max-w-[80%] rounded-2xl bg-white px-4 py-3 text-black"
                        : "max-w-[85%] text-neutral-200"
                    }
                  >
                    {message.role ===
                      "assistant" && (
                      <div className="mb-2 text-xs font-medium text-neutral-500">
                        ERKEK AI
                      </div>
                    )}

                    <div className="whitespace-pre-wrap leading-7">
                      {message.content}
                    </div>
                  </div>
                </div>
              )
            )}

            {loading && (
              <div className="flex justify-start">
                <div>
                  <div className="mb-2 text-xs text-neutral-500">
                    ERKEK AI
                  </div>

                  <div className="text-sm text-neutral-500">
                    Жауап дайындалуда...
                  </div>
                </div>
              </div>
            )}

            <div ref={bottomRef} />

          </div>

        </div>

      </section>

      {/* INPUT */}

      <footer className="border-t border-neutral-900 bg-black">

        <div className="mx-auto w-full max-w-4xl px-5 py-5">

          {error && (
            <div className="mb-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <div className="flex items-end gap-3 rounded-2xl border border-neutral-800 bg-neutral-950 p-2">

            <textarea
              value={input}
              onChange={(event) =>
                setInput(event.target.value)
              }
              onKeyDown={handleKeyDown}
              placeholder="Не ойландырып жүр?"
              rows={1}
              disabled={loading}
              className="
                max-h-40
                min-h-12
                flex-1
                resize-none
                bg-transparent
                px-3
                py-3
                text-white
                outline-none
                placeholder:text-neutral-600
              "
            />

            <button
              onClick={sendMessage}
              disabled={
                loading ||
                !input.trim()
              }
              className="
                h-11
                rounded-xl
                bg-white
                px-5
                font-medium
                text-black
                transition
                hover:bg-neutral-200
                disabled:cursor-not-allowed
                disabled:opacity-30
              "
            >
              Жіберу
            </button>

          </div>

          <div className="mt-3 text-center text-xs text-neutral-700">
            ERKEK AI қателесуі мүмкін. Маңызды шешімдерді тексер.
          </div>

        </div>

      </footer>

    </main>
  );
}