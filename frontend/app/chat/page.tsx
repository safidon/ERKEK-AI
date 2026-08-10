"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";


type ChatMessage = {
  id?: number;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
};


type ChatSession = {
  id: number;
  title: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
};


const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";


export default function ChatPage() {
  const router = useRouter();

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] =
    useState<number | null>(null);

  const [messages, setMessages] =
    useState<ChatMessage[]>([]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionsLoading, setSessionsLoading] =
    useState(true);

  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] =
    useState(false);

  const bottomRef = useRef<HTMLDivElement | null>(null);


  // =====================================================
  // ACTIVE SESSION
  // =====================================================

  const activeSession =
    sessions.find(
      (session) =>
        session.id === activeSessionId
    ) || null;


  // =====================================================
  // AUTH
  // =====================================================

  useEffect(() => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      router.replace("/login");
      return;
    }

    loadSessions();
  }, [router]);


  // =====================================================
  // AUTO SCROLL
  // =====================================================

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);


  // =====================================================
  // ESC CLOSE MOBILE SIDEBAR
  // =====================================================

  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setSidebarOpen(false);
      }
    }

    window.addEventListener(
      "keydown",
      handleEscape
    );

    return () => {
      window.removeEventListener(
        "keydown",
        handleEscape
      );
    };
  }, []);


  // =====================================================
  // TOKEN HELPER
  // =====================================================

  function getToken() {
    return localStorage.getItem("access_token");
  }


  // =====================================================
  // HANDLE 401
  // =====================================================

  function handleUnauthorized() {
    localStorage.removeItem("access_token");
    router.replace("/login");
  }


  // =====================================================
  // LOAD SESSIONS
  // =====================================================

  async function loadSessions() {
    const token = getToken();

    if (!token) {
      handleUnauthorized();
      return;
    }

    setSessionsLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/sessions`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Әңгімелерді жүктеу кезінде қате шықты."
        );
      }

      setSessions(data);

      if (data.length > 0) {
        const firstSessionId = data[0].id;

        setActiveSessionId(firstSessionId);

        await loadSession(
          firstSessionId,
          false
        );
      } else {
        setMessages([]);
        setActiveSessionId(null);
      }

    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError("Белгісіз қате шықты.");
      }

    } finally {
      setSessionsLoading(false);
    }
  }


  // =====================================================
  // LOAD ONE SESSION
  // =====================================================

  async function loadSession(
    sessionId: number,
    closeSidebar: boolean = true
  ) {
    const token = getToken();

    if (!token) {
      handleUnauthorized();
      return;
    }

    setError("");

    try {
      const response = await fetch(
        `${API_URL}/sessions/${sessionId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Әңгімені ашу кезінде қате шықты."
        );
      }

      setActiveSessionId(sessionId);
      setMessages(data.messages || []);

      if (closeSidebar) {
        setSidebarOpen(false);
      }

    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError("Белгісіз қате шықты.");
      }
    }
  }


  // =====================================================
  // CREATE NEW SESSION
  // =====================================================

  async function createNewChat() {
    const token = getToken();

    if (!token) {
      handleUnauthorized();
      return;
    }

    setError("");

    try {
      const response = await fetch(
        `${API_URL}/sessions`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },

          body: JSON.stringify({
            title: "Жаңа әңгіме",
          }),
        }
      );

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Жаңа чат ашу кезінде қате шықты."
        );
      }

      setSessions((current) => [
        data,
        ...current,
      ]);

      setActiveSessionId(data.id);
      setMessages([]);
      setInput("");
      setSidebarOpen(false);

    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError("Белгісіз қате шықты.");
      }
    }
  }


  // =====================================================
  // RENAME SESSION
  // =====================================================

  async function renameChat(
    sessionId: number,
    currentTitle: string
  ) {
    const token = getToken();

    if (!token) {
      handleUnauthorized();
      return;
    }

    const newTitle = window.prompt(
      "Жаңа атау:",
      currentTitle
    );

    if (newTitle === null) {
      return;
    }

    const cleanTitle = newTitle.trim();

    if (!cleanTitle) {
      return;
    }

    setError("");

    try {
      const response = await fetch(
        `${API_URL}/sessions/${sessionId}`,
        {
          method: "PATCH",

          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },

          body: JSON.stringify({
            title: cleanTitle,
          }),
        }
      );

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Әңгіме атауын өзгерту кезінде қате шықты."
        );
      }

      setSessions((current) =>
        current.map((session) =>
          session.id === sessionId
            ? {
                ...session,
                title: cleanTitle,
              }
            : session
        )
      );

    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError("Белгісіз қате шықты.");
      }
    }
  }


  // =====================================================
  // DELETE SESSION
  // =====================================================

  async function deleteChat(
    sessionId: number
  ) {
    const token = getToken();

    if (!token) {
      handleUnauthorized();
      return;
    }

    const confirmed = window.confirm(
      "Бұл әңгімені өшіргің келе ме?"
    );

    if (!confirmed) {
      return;
    }

    setError("");

    try {
      const response = await fetch(
        `${API_URL}/sessions/${sessionId}`,
        {
          method: "DELETE",

          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Әңгімені өшіру кезінде қате шықты."
        );
      }

      const remainingSessions =
        sessions.filter(
          (session) =>
            session.id !== sessionId
        );

      setSessions(
        remainingSessions
      );

      if (
        activeSessionId === sessionId
      ) {
        if (
          remainingSessions.length > 0
        ) {
          const nextId =
            remainingSessions[0].id;

          await loadSession(
            nextId,
            false
          );
        } else {
          setActiveSessionId(null);
          setMessages([]);
        }
      }

    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError("Белгісіз қате шықты.");
      }
    }
  }


  // =====================================================
  // SEND MESSAGE
  // =====================================================

  async function sendMessage() {
    const message = input.trim();

    if (
      !message ||
      loading ||
      activeSessionId === null
    ) {
      return;
    }

    const token = getToken();

    if (!token) {
      handleUnauthorized();
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
            session_id: activeSessionId,
            message,
          }),
        }
      );

      if (response.status === 401) {
        handleUnauthorized();
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

      await refreshSessionList();

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


  // =====================================================
  // REFRESH SESSION LIST
  // =====================================================

  async function refreshSessionList() {
    const token = getToken();

    if (!token) {
      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/sessions`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        return;
      }

      const data = await response.json();

      setSessions(data);

    } catch {
      // Sidebar жаңармаса да chat тоқтамауы тиіс.
    }
  }


  // =====================================================
  // LOGOUT
  // =====================================================

  function handleLogout() {
    localStorage.removeItem(
      "access_token"
    );

    router.replace("/login");
  }


  // =====================================================
  // ENTER SEND
  // =====================================================

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


  // =====================================================
  // QUICK PROMPT
  // =====================================================

  function selectQuickPrompt(
    prompt: string
  ) {
    setInput(prompt);
  }


  // =====================================================
  // SIDEBAR CONTENT
  // =====================================================

  function SidebarContent() {
    return (
      <>
        <div className="border-b border-neutral-900 p-4">

          <div className="mb-3 flex items-center justify-between lg:hidden">

            <div className="font-semibold">
              ERKEK AI
            </div>

            <button
              onClick={() =>
                setSidebarOpen(false)
              }
              className="
                flex
                h-9
                w-9
                items-center
                justify-center
                rounded-lg
                text-xl
                text-neutral-400
                transition
                hover:bg-neutral-900
                hover:text-white
              "
              aria-label="Мәзірді жабу"
            >
              ×
            </button>

          </div>

          <button
            onClick={createNewChat}
            className="
              w-full
              rounded-xl
              border
              border-neutral-800
              px-4
              py-3
              text-left
              text-sm
              transition
              hover:bg-neutral-900
            "
          >
            + Жаңа чат
          </button>

        </div>


        {/* SESSION LIST */}

        <div className="flex-1 overflow-y-auto p-2">

          {sessionsLoading && (
            <div className="space-y-2 px-2 py-3">

              {[1, 2, 3, 4].map(
                (item) => (
                  <div
                    key={item}
                    className="
                      h-11
                      animate-pulse
                      rounded-lg
                      bg-white/[0.04]
                    "
                  />
                )
              )}

            </div>
          )}


          {!sessionsLoading &&
            sessions.length === 0 && (
              <div className="px-3 py-4">

                <div className="text-sm text-neutral-500">
                  Әзірге әңгіме жоқ.
                </div>

                <div className="mt-1 text-xs leading-5 text-neutral-700">
                  Жаңа чат ашып,
                  ERKEK AI-мен сөйлесуді баста.
                </div>

              </div>
            )}


          {!sessionsLoading &&
            sessions.map(
              (session) => (
                <div
                  key={session.id}
                  className={`
                    group
                    mb-1
                    flex
                    items-center
                    rounded-lg
                    transition
                    ${
                      activeSessionId ===
                      session.id
                        ? "bg-neutral-900"
                        : "hover:bg-neutral-900/60"
                    }
                  `}
                >

                  <button
                    onClick={() =>
                      loadSession(
                        session.id
                      )
                    }
                    onDoubleClick={() =>
                      renameChat(
                        session.id,
                        session.title
                      )
                    }
                    title="Ашу үшін бас. Атын өзгерту үшін екі рет бас."
                    className="
                      min-w-0
                      flex-1
                      truncate
                      px-3
                      py-3
                      text-left
                      text-sm
                      text-neutral-300
                    "
                  >
                    {session.title}
                  </button>

                  <button
                    onClick={() =>
                      renameChat(
                        session.id,
                        session.title
                      )
                    }
                    className="
                      px-2
                      text-neutral-600
                      transition
                      hover:text-white
                      lg:hidden
                      lg:group-hover:block
                    "
                    title="Атын өзгерту"
                  >
                    ✎
                  </button>

                  <button
                    onClick={() =>
                      deleteChat(
                        session.id
                      )
                    }
                    className="
                      px-3
                      text-neutral-600
                      transition
                      hover:text-red-400
                      lg:hidden
                      lg:group-hover:block
                    "
                    title="Өшіру"
                  >
                    ×
                  </button>

                </div>
              )
            )}

        </div>


        {/* SIDEBAR FOOTER */}

        <div className="border-t border-neutral-900 p-4">

          <div className="mb-3 text-sm font-medium">
            ERKEK AI
          </div>

          <button
            onClick={handleLogout}
            className="
              text-sm
              text-neutral-500
              transition
              hover:text-white
            "
          >
            Шығу
          </button>

        </div>
      </>
    );
  }


  // =====================================================
  // UI
  // =====================================================

  return (
    <main className="flex h-dvh overflow-hidden bg-black text-white">

      {/* ================================================= */}
      {/* DESKTOP SIDEBAR */}
      {/* ================================================= */}

      <aside className="hidden w-72 shrink-0 flex-col border-r border-neutral-900 bg-neutral-950 lg:flex">
        <SidebarContent />
      </aside>


      {/* ================================================= */}
      {/* MOBILE OVERLAY */}
      {/* ================================================= */}

      {sidebarOpen && (
        <button
          type="button"
          aria-label="Мәзірді жабу"
          onClick={() =>
            setSidebarOpen(false)
          }
          className="
            fixed
            inset-0
            z-40
            bg-black/70
            backdrop-blur-sm
            lg:hidden
          "
        />
      )}


      {/* ================================================= */}
      {/* MOBILE SIDEBAR */}
      {/* ================================================= */}

      <aside
        className={`
          fixed
          inset-y-0
          left-0
          z-50
          flex
          w-[85%]
          max-w-80
          flex-col
          border-r
          border-neutral-900
          bg-neutral-950
          transition-transform
          duration-200
          ease-out
          lg:hidden
          ${
            sidebarOpen
              ? "translate-x-0"
              : "-translate-x-full"
          }
        `}
      >
        <SidebarContent />
      </aside>


      {/* ================================================= */}
      {/* MAIN CHAT */}
      {/* ================================================= */}

      <section className="flex min-w-0 flex-1 flex-col">

        {/* HEADER */}

        <header className="flex h-16 shrink-0 items-center border-b border-neutral-900 px-3 sm:px-5 lg:px-6">

          <button
            onClick={() =>
              setSidebarOpen(true)
            }
            className="
              mr-3
              flex
              h-10
              w-10
              items-center
              justify-center
              rounded-xl
              text-xl
              text-neutral-300
              transition
              hover:bg-neutral-900
              lg:hidden
            "
            aria-label="Мәзірді ашу"
          >
            ☰
          </button>

          <div className="min-w-0">

            <div className="truncate font-semibold">
              {activeSession
                ? activeSession.title
                : "ERKEK AI"}
            </div>

            <div className="text-xs text-neutral-500">
              {activeSession
                ? "ERKEK AI · Digital mentor"
                : "Digital mentor"}
            </div>

          </div>

        </header>


        {/* CHAT MESSAGES */}

        <div className="min-h-0 flex-1 overflow-y-auto">

          <div className="mx-auto w-full max-w-4xl px-3 py-6 sm:px-5 sm:py-8 lg:px-6">

            {activeSessionId === null ? (

              <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">

                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-lg font-black text-black">
                  E
                </div>

                <h1 className="mt-5 text-2xl font-semibold sm:text-3xl">
                  ERKEK AI
                </h1>

                <p className="mt-3 max-w-md text-sm leading-6 text-neutral-500 sm:text-base">
                  Жаңа әңгіме ашып,
                  ойыңдағы мәселені жаз.
                </p>

                <button
                  onClick={createNewChat}
                  className="
                    mt-7
                    rounded-xl
                    bg-white
                    px-5
                    py-3
                    font-medium
                    text-black
                    transition
                    hover:bg-neutral-200
                  "
                >
                  + Жаңа чат
                </button>

              </div>

            ) : (

              <div className="space-y-6 sm:space-y-7">


                {/* EMPTY CHAT */}

                {messages.length === 0 &&
                  !loading && (
                  <div className="flex min-h-[55vh] flex-col items-center justify-center px-4 text-center">

                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-lg font-black text-black">
                      E
                    </div>

                    <h2 className="mt-5 text-xl font-semibold sm:text-2xl">
                      Не туралы сөйлесеміз?
                    </h2>

                    <p className="mt-2 max-w-md text-sm leading-6 text-neutral-500">
                      Жұмыс, қаржы, отбасы,
                      мақсаттар немесе ойыңда жүрген
                      кез келген мәселені жаз.
                    </p>


                    {/* QUICK PROMPTS */}

                    <div className="mt-6 grid w-full max-w-xl gap-2 sm:grid-cols-2">

                      {[
                        "Жұмыс туралы кеңес керек",
                        "Қаржы жоспарымды талдайық",
                        "Мақсаттарымды реттегім келеді",
                        "Бір мәселе мазалап жүр",
                      ].map(
                        (prompt) => (
                          <button
                            key={prompt}
                            onClick={() =>
                              selectQuickPrompt(
                                prompt
                              )
                            }
                            className="
                              rounded-2xl
                              border
                              border-white/[0.07]
                              bg-white/[0.02]
                              px-4
                              py-3
                              text-left
                              text-sm
                              text-neutral-400
                              transition
                              hover:border-white/[0.14]
                              hover:bg-white/[0.04]
                              hover:text-white
                            "
                          >
                            {prompt}
                          </button>
                        )
                      )}

                    </div>

                  </div>
                )}


                {/* MESSAGES */}

                {messages.map(
                  (
                    message,
                    index
                  ) => (
                    <div
                      key={
                        message.id ??
                        index
                      }
                      className={
                        message.role ===
                        "user"
                          ? "flex justify-end"
                          : "flex justify-start"
                      }
                    >

                      <div
                        className={
                          message.role ===
                          "user"
                            ? `
                              max-w-[88%]
                              rounded-2xl
                              bg-white
                              px-4
                              py-3
                              text-black
                              sm:max-w-[80%]
                            `
                            : `
                              max-w-[95%]
                              text-neutral-200
                              sm:max-w-[85%]
                            `
                        }
                      >

                        {message.role ===
                          "assistant" && (
                          <div className="mb-2 text-xs font-medium text-neutral-500">
                            ERKEK AI
                          </div>
                        )}

                        <div className="whitespace-pre-wrap break-words text-[15px] leading-7 sm:text-base">
                          {message.content}
                        </div>

                      </div>

                    </div>
                  )
                )}


                {/* AI LOADING */}

                {loading && (
                  <div className="flex justify-start">

                    <div className="max-w-[85%]">

                      <div className="mb-2 text-xs font-medium text-neutral-500">
                        ERKEK AI
                      </div>

                      <div className="flex items-center gap-1.5">

                        <span className="h-2 w-2 animate-bounce rounded-full bg-neutral-600 [animation-delay:-0.3s]" />

                        <span className="h-2 w-2 animate-bounce rounded-full bg-neutral-600 [animation-delay:-0.15s]" />

                        <span className="h-2 w-2 animate-bounce rounded-full bg-neutral-600" />

                      </div>

                    </div>

                  </div>
                )}

                <div ref={bottomRef} />

              </div>

            )}

          </div>

        </div>


        {/* ================================================= */}
        {/* INPUT */}
        {/* ================================================= */}

        <footer className="shrink-0 border-t border-neutral-900 bg-black">

          <div className="mx-auto w-full max-w-4xl px-3 py-3 sm:px-5 sm:py-5 lg:px-6">


            {/* ERROR */}

            {error && (
              <div className="mb-3 flex items-start justify-between gap-3 rounded-xl border border-red-500/20 bg-red-500/[0.06] px-4 py-3 text-sm text-red-400">

                <span>
                  {error}
                </span>

                <button
                  onClick={() =>
                    setError("")
                  }
                  className="shrink-0 text-red-400/60 transition hover:text-red-300"
                  aria-label="Қатені жабу"
                >
                  ×
                </button>

              </div>
            )}


            {/* MESSAGE INPUT */}

            <div className="flex items-end gap-2 rounded-2xl border border-neutral-800 bg-neutral-950 p-2 transition focus-within:border-neutral-700 sm:gap-3">

              <textarea
                value={input}
                onChange={(event) =>
                  setInput(
                    event.target.value
                  )
                }
                onKeyDown={
                  handleKeyDown
                }
                placeholder={
                  activeSessionId
                    ? "Не ойландырып жүр?"
                    : "Алдымен жаңа чат аш."
                }
                rows={1}
                disabled={
                  loading ||
                  activeSessionId ===
                    null
                }
                className="
                  max-h-40
                  min-h-11
                  min-w-0
                  flex-1
                  resize-none
                  bg-transparent
                  px-2
                  py-3
                  text-sm
                  text-white
                  outline-none
                  placeholder:text-neutral-600
                  disabled:cursor-not-allowed
                  sm:min-h-12
                  sm:px-3
                  sm:text-base
                "
              />

              <button
                onClick={sendMessage}
                disabled={
                  loading ||
                  !input.trim() ||
                  activeSessionId ===
                    null
                }
                className="
                  h-11
                  shrink-0
                  rounded-xl
                  bg-white
                  px-3
                  text-sm
                  font-medium
                  text-black
                  transition
                  hover:bg-neutral-200
                  disabled:cursor-not-allowed
                  disabled:opacity-30
                  sm:px-5
                  sm:text-base
                "
              >

                <span className="hidden sm:inline">
                  Жіберу
                </span>

                <span className="sm:hidden">
                  ↑
                </span>

              </button>

            </div>


            <div className="mt-2 text-center text-[10px] text-neutral-700 sm:mt-3 sm:text-xs">
              ERKEK AI қателесуі мүмкін.
              Маңызды шешімдерді тексер.
            </div>

          </div>

        </footer>

      </section>

    </main>
  );
}