"use client";

import {
  isValidElement,
  type ReactNode,
  useEffect,
  useRef,
  useState,
} from "react";

import { useRouter } from "next/navigation";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";


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


// =====================================================
// COPY TEXT
// =====================================================

async function copyText(
  text: string
) {
  if (
    typeof navigator !== "undefined" &&
    navigator.clipboard
  ) {
    await navigator.clipboard.writeText(
      text
    );

    return;
  }

  const textarea =
    document.createElement("textarea");

  textarea.value = text;

  textarea.style.position = "fixed";
  textarea.style.opacity = "0";

  document.body.appendChild(
    textarea
  );

  textarea.focus();
  textarea.select();

  document.execCommand("copy");

  document.body.removeChild(
    textarea
  );
}


// =====================================================
// COPY BUTTON
// =====================================================

function CopyButton({
  text,
  label = "Көшіру",
  copiedLabel = "Көшірілді ✓",
  compact = false,
}: {
  text: string;
  label?: string;
  copiedLabel?: string;
  compact?: boolean;
}) {
  const [copied, setCopied] =
    useState(false);


  async function handleCopy() {
    try {
      await copyText(text);

      setCopied(true);

      window.setTimeout(
        () => {
          setCopied(false);
        },
        1800
      );

    } catch {
      setCopied(false);
    }
  }


  return (
    <button
      type="button"
      onClick={handleCopy}
      className={
        compact
          ? `
              rounded-lg
              border
              border-white/[0.08]
              bg-black/50
              px-2.5
              py-1.5
              text-[11px]
              text-neutral-400
              backdrop-blur
              transition
              hover:bg-neutral-900
              hover:text-white
            `
          : `
              inline-flex
              items-center
              rounded-lg
              px-2
              py-1
              text-xs
              text-neutral-600
              transition
              hover:bg-white/[0.04]
              hover:text-neutral-300
            `
      }
    >
      {copied
        ? copiedLabel
        : label}
    </button>
  );
}


// =====================================================
// REACT NODE -> TEXT
// =====================================================

function getNodeText(
  node: ReactNode
): string {
  if (
    typeof node === "string" ||
    typeof node === "number"
  ) {
    return String(node);
  }

  if (Array.isArray(node)) {
    return node
      .map(getNodeText)
      .join("");
  }

  if (isValidElement(node)) {
    const props =
      node.props as {
        children?: ReactNode;
      };

    return getNodeText(
      props.children
    );
  }

  return "";
}


// =====================================================
// MARKDOWN NORMALIZER
// =====================================================

function normalizeMarkdown(
  content: string
): string {
  if (!content) {
    return "";
  }

  let normalized = content
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n");

  const fenceMatches =
    normalized.match(/```/g);

  const fenceCount =
    fenceMatches?.length ?? 0;

  if (fenceCount % 2 !== 0) {
    normalized += "\n```";
  }

  return normalized;
}


// =====================================================
// MARKDOWN MESSAGE
// =====================================================

function MarkdownMessage({
  content,
}: {
  content: string;
}) {
  const normalizedContent =
    normalizeMarkdown(content);


  return (
    <div
      className="
        min-w-0
        max-w-full
        break-words
        text-[15px]
        leading-7
        text-neutral-200
        sm:text-base
      "
    >
      <ReactMarkdown
        remarkPlugins={[
          remarkGfm
        ]}
        components={{

          // =================================================
          // HEADINGS
          // =================================================

          h1: ({
            children,
          }) => (
            <h1 className="mb-4 mt-6 text-2xl font-bold tracking-tight text-white first:mt-0">
              {children}
            </h1>
          ),

          h2: ({
            children,
          }) => (
            <h2 className="mb-3 mt-5 text-xl font-semibold tracking-tight text-white first:mt-0">
              {children}
            </h2>
          ),

          h3: ({
            children,
          }) => (
            <h3 className="mb-2 mt-4 text-lg font-semibold text-white first:mt-0">
              {children}
            </h3>
          ),


          // =================================================
          // TEXT
          // =================================================

          p: ({
            children,
          }) => (
            <p className="my-3 whitespace-normal break-words leading-7 first:mt-0 last:mb-0">
              {children}
            </p>
          ),

          strong: ({
            children,
          }) => (
            <strong className="font-semibold text-white">
              {children}
            </strong>
          ),

          em: ({
            children,
          }) => (
            <em className="italic text-neutral-300">
              {children}
            </em>
          ),


          // =================================================
          // LISTS
          // =================================================

          ul: ({
            children,
          }) => (
            <ul className="my-3 list-disc space-y-1.5 pl-6">
              {children}
            </ul>
          ),

          ol: ({
            children,
          }) => (
            <ol className="my-3 list-decimal space-y-1.5 pl-6">
              {children}
            </ol>
          ),

          li: ({
            children,
          }) => (
            <li className="break-words pl-1 leading-7">
              {children}
            </li>
          ),


          // =================================================
          // QUOTE
          // =================================================

          blockquote: ({
            children,
          }) => (
            <blockquote
              className="
                my-4
                border-l-2
                border-neutral-700
                bg-white/[0.02]
                py-1
                pl-4
                pr-3
                text-neutral-400
              "
            >
              {children}
            </blockquote>
          ),


          // =================================================
          // LINKS
          // =================================================

          a: ({
            href,
            children,
          }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="
                break-all
                text-blue-400
                underline
                decoration-blue-400/40
                underline-offset-4
                transition
                hover:text-blue-300
              "
            >
              {children}
            </a>
          ),


          // =================================================
          // CODE
          // =================================================

          code: ({
            className,
            children,
            ...props
          }) => {
            const codeText =
              String(
                children
              ).replace(
                /\n$/,
                ""
              );

            const isBlock =
              Boolean(
                className
              ) ||
              codeText.includes(
                "\n"
              );


            if (isBlock) {
              return (
                <code
                  className={`
                    ${className ?? ""}
                    block
                    font-mono
                    text-[13px]
                    leading-6
                    text-neutral-200
                    sm:text-sm
                  `}
                  {...props}
                >
                  {children}
                </code>
              );
            }


            return (
              <code
                className="
                  rounded-md
                  border
                  border-white/[0.06]
                  bg-white/[0.07]
                  px-1.5
                  py-0.5
                  font-mono
                  text-[0.88em]
                  text-neutral-100
                "
                {...props}
              >
                {children}
              </code>
            );
          },


          // =================================================
          // CODE BLOCK + COPY
          // =================================================

          pre: ({
            children,
          }) => {
            const codeText =
              getNodeText(
                children
              ).replace(
                /\n$/,
                ""
              );


            return (
              <div
                className="
                  group/code
                  relative
                  my-4
                  max-w-full
                  overflow-hidden
                  rounded-xl
                  border
                  border-neutral-800
                  bg-neutral-950
                "
              >

                {/* CODE HEADER */}

                <div
                  className="
                    flex
                    h-10
                    items-center
                    justify-between
                    border-b
                    border-neutral-800
                    bg-black/30
                    px-3
                  "
                >

                  <span className="text-[11px] text-neutral-600">
                    Code
                  </span>

                  <CopyButton
                    text={
                      codeText
                    }
                    label="Copy"
                    copiedLabel="Copied ✓"
                    compact
                  />

                </div>


                {/* CODE */}

                <pre
                  className="
                    max-w-full
                    overflow-x-auto
                    whitespace-pre
                    p-4
                    font-mono
                    text-[13px]
                    leading-6
                    sm:text-sm
                  "
                >
                  {children}
                </pre>

              </div>
            );
          },


          // =================================================
          // DIVIDER
          // =================================================

          hr: () => (
            <hr className="my-6 border-neutral-800" />
          ),


          // =================================================
          // TABLE
          // =================================================

          table: ({
            children,
          }) => (
            <div
              className="
                my-4
                max-w-full
                overflow-x-auto
                rounded-xl
                border
                border-neutral-800
              "
            >
              <table className="w-full min-w-[480px] border-collapse text-sm">
                {children}
              </table>
            </div>
          ),

          thead: ({
            children,
          }) => (
            <thead className="bg-white/[0.04] text-white">
              {children}
            </thead>
          ),

          tbody: ({
            children,
          }) => (
            <tbody className="divide-y divide-neutral-900">
              {children}
            </tbody>
          ),

          tr: ({
            children,
          }) => (
            <tr>
              {children}
            </tr>
          ),

          th: ({
            children,
          }) => (
            <th
              className="
                border-r
                border-neutral-800
                px-4
                py-3
                text-left
                font-semibold
                last:border-r-0
              "
            >
              {children}
            </th>
          ),

          td: ({
            children,
          }) => (
            <td
              className="
                border-r
                border-neutral-900
                px-4
                py-3
                align-top
                last:border-r-0
              "
            >
              {children}
            </td>
          ),
        }}
      >
        {normalizedContent}
      </ReactMarkdown>
    </div>
  );
}


// =====================================================
// CHAT PAGE
// =====================================================

export default function ChatPage() {
  const router =
    useRouter();

  const [
    sessions,
    setSessions,
  ] =
    useState<
      ChatSession[]
    >([]);

  const [
    activeSessionId,
    setActiveSessionId,
  ] =
    useState<
      number | null
    >(null);

  const [
    messages,
    setMessages,
  ] =
    useState<
      ChatMessage[]
    >([]);

  const [
    input,
    setInput,
  ] =
    useState("");

  const [
    loading,
    setLoading,
  ] =
    useState(false);

  const [
    regenerating,
    setRegenerating,
  ] =
    useState(false);

  const [
    sessionsLoading,
    setSessionsLoading,
  ] =
    useState(true);

  const [
    error,
    setError,
  ] =
    useState("");

  const [
    sidebarOpen,
    setSidebarOpen,
  ] =
    useState(false);

  const [
    sessionLoading,
    setSessionLoading,
  ] =
    useState(false);

  const [
    isUserNearBottom,
    setIsUserNearBottom,
  ] =
    useState(true);

  const bottomRef =
    useRef<
      HTMLDivElement | null
    >(null);

  const streamAbortControllerRef =
    useRef<AbortController | null>(
      null
    );

  const chatScrollRef =
    useRef<
      HTMLDivElement | null
    >(null);

  const textareaRef =
    useRef<
      HTMLTextAreaElement | null
    >(null);


  // =====================================================
  // ACTIVE SESSION
  // =====================================================

  const activeSession =
    sessions.find(
      (
        session
      ) =>
        session.id ===
        activeSessionId
    ) || null;


  // =====================================================
  // AUTH
  // =====================================================

  useEffect(
    () => {
      const token =
        localStorage.getItem(
          "access_token"
        );

      if (!token) {
        router.replace(
          "/login"
        );

        return;
      }

      loadSessions();

    },
    [router]
  );


  // =====================================================
  // SMART AUTO SCROLL
  // =====================================================

  useEffect(
    () => {
      if (
        !isUserNearBottom
      ) {
        return;
      }

      bottomRef.current
        ?.scrollIntoView({
          behavior:
            loading ||
            regenerating
              ? "auto"
              : "smooth",
        });

    },
    [
      messages,
      loading,
      regenerating,
      isUserNearBottom,
    ]
  );


  // =====================================================
  // TRACK SCROLL POSITION
  // =====================================================

  function handleChatScroll() {
    const container =
      chatScrollRef.current;

    if (!container) {
      return;
    }

    const distanceFromBottom =
      container.scrollHeight -
      container.scrollTop -
      container.clientHeight;

    setIsUserNearBottom(
      distanceFromBottom < 140
    );
  }


  function scrollToBottom() {
    setIsUserNearBottom(
      true
    );

    bottomRef.current
      ?.scrollIntoView({
        behavior:
          "smooth",
      });
  }


  // =====================================================
  // TEXTAREA AUTO RESIZE
  // =====================================================

  useEffect(
    () => {
      const textarea =
        textareaRef.current;

      if (!textarea) {
        return;
      }

      textarea.style.height =
        "auto";

      const maxHeight = 160;

      const nextHeight =
        Math.min(
          textarea.scrollHeight,
          maxHeight
        );

      textarea.style.height =
        `${nextHeight}px`;

      textarea.style.overflowY =
        textarea.scrollHeight >
        maxHeight
          ? "auto"
          : "hidden";
    },
    [input]
  );


  // =====================================================
  // ESC CLOSE MOBILE SIDEBAR
  // =====================================================

  useEffect(
    () => {
      function handleEscape(
        event: KeyboardEvent
      ) {
        if (
          event.key ===
          "Escape"
        ) {
          setSidebarOpen(
            false
          );
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

    },
    []
  );


  // =====================================================
  // TOKEN HELPER
  // =====================================================

  function getToken() {
    return localStorage.getItem(
      "access_token"
    );
  }


  // =====================================================
  // HANDLE 401
  // =====================================================

  function handleUnauthorized() {
    localStorage.removeItem(
      "access_token"
    );

    router.replace(
      "/login"
    );
  }


  // =====================================================
  // LOAD SESSIONS
  // =====================================================

  async function loadSessions() {
    const token =
      getToken();

    if (!token) {
      handleUnauthorized();
      return;
    }

    setSessionsLoading(
      true
    );

    setError("");

    try {
      const response =
        await fetch(
          `${API_URL}/sessions`,
          {
            headers: {
              Authorization:
                `Bearer ${token}`,
            },
          }
        );


      if (
        response.status ===
        401
      ) {
        handleUnauthorized();
        return;
      }


      const data =
        await response.json();


      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Әңгімелерді жүктеу кезінде қате шықты."
        );
      }


      setSessions(
        data
      );


      if (
        data.length > 0
      ) {
        const firstSessionId =
          data[0].id;

        setActiveSessionId(
          firstSessionId
        );

        await loadSession(
          firstSessionId,
          false
        );

      } else {
        setMessages(
          []
        );

        setActiveSessionId(
          null
        );
      }

    } catch (error) {
      if (
        error instanceof Error
      ) {
        setError(
          error.message
        );
      } else {
        setError(
          "Белгісіз қате шықты."
        );
      }

    } finally {
      setSessionsLoading(
        false
      );
    }
  }


  // =====================================================
  // LOAD ONE SESSION
  // =====================================================

  async function loadSession(
    sessionId: number,
    closeSidebar:
      boolean = true
  ) {
    const token =
      getToken();

    if (!token) {
      handleUnauthorized();
      return;
    }

    setError("");
    setSessionLoading(true);

    try {
      const response =
        await fetch(
          `${API_URL}/sessions/${sessionId}`,
          {
            headers: {
              Authorization:
                `Bearer ${token}`,
            },
          }
        );


      if (
        response.status ===
        401
      ) {
        handleUnauthorized();
        return;
      }


      const data =
        await response.json();


      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Әңгімені ашу кезінде қате шықты."
        );
      }


      setActiveSessionId(
        sessionId
      );

      setMessages(
        data.messages ||
          []
      );

      setIsUserNearBottom(
        true
      );


      if (
        closeSidebar
      ) {
        setSidebarOpen(
          false
        );
      }

    } catch (error) {
      if (
        error instanceof Error
      ) {
        setError(
          error.message
        );
      } else {
        setError(
          "Белгісіз қате шықты."
        );
      }

    } finally {
      setSessionLoading(
        false
      );
    }
  }


  // =====================================================
  // CREATE NEW SESSION
  // =====================================================

  async function createNewChat() {
    const token =
      getToken();

    if (!token) {
      handleUnauthorized();
      return;
    }

    setError("");

    try {
      const response =
        await fetch(
          `${API_URL}/sessions`,
          {
            method:
              "POST",

            headers: {
              "Content-Type":
                "application/json",

              Authorization:
                `Bearer ${token}`,
            },

            body:
              JSON.stringify({
                title:
                  "Жаңа әңгіме",
              }),
          }
        );


      if (
        response.status ===
        401
      ) {
        handleUnauthorized();
        return;
      }


      const data =
        await response.json();


      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Жаңа чат ашу кезінде қате шықты."
        );
      }


      setSessions(
        (
          current
        ) => [
          data,
          ...current,
        ]
      );

      setActiveSessionId(
        data.id
      );

      setMessages(
        []
      );

      setIsUserNearBottom(
        true
      );

      setInput("");

      setSidebarOpen(
        false
      );

    } catch (error) {
      if (
        error instanceof Error
      ) {
        setError(
          error.message
        );
      } else {
        setError(
          "Белгісіз қате шықты."
        );
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
    const token =
      getToken();

    if (!token) {
      handleUnauthorized();
      return;
    }

    const newTitle =
      window.prompt(
        "Жаңа атау:",
        currentTitle
      );


    if (
      newTitle === null
    ) {
      return;
    }


    const cleanTitle =
      newTitle.trim();


    if (!cleanTitle) {
      return;
    }


    setError("");

    try {
      const response =
        await fetch(
          `${API_URL}/sessions/${sessionId}`,
          {
            method:
              "PATCH",

            headers: {
              "Content-Type":
                "application/json",

              Authorization:
                `Bearer ${token}`,
            },

            body:
              JSON.stringify({
                title:
                  cleanTitle,
              }),
          }
        );


      if (
        response.status ===
        401
      ) {
        handleUnauthorized();
        return;
      }


      const data =
        await response.json();


      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Әңгіме атауын өзгерту кезінде қате шықты."
        );
      }


      setSessions(
        (
          current
        ) =>
          current.map(
            (
              session
            ) =>
              session.id ===
              sessionId
                ? {
                    ...session,
                    title:
                      cleanTitle,
                  }
                : session
          )
      );

    } catch (error) {
      if (
        error instanceof Error
      ) {
        setError(
          error.message
        );
      } else {
        setError(
          "Белгісіз қате шықты."
        );
      }
    }
  }


  // =====================================================
  // DELETE SESSION
  // =====================================================

  async function deleteChat(
    sessionId: number
  ) {
    const token =
      getToken();

    if (!token) {
      handleUnauthorized();
      return;
    }

    const confirmed =
      window.confirm(
        "Бұл әңгімені өшіргің келе ме?"
      );


    if (!confirmed) {
      return;
    }


    setError("");

    try {
      const response =
        await fetch(
          `${API_URL}/sessions/${sessionId}`,
          {
            method:
              "DELETE",

            headers: {
              Authorization:
                `Bearer ${token}`,
            },
          }
        );


      if (
        response.status ===
        401
      ) {
        handleUnauthorized();
        return;
      }


      const data =
        await response.json();


      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Әңгімені өшіру кезінде қате шықты."
        );
      }


      const remainingSessions =
        sessions.filter(
          (
            session
          ) =>
            session.id !==
            sessionId
        );


      setSessions(
        remainingSessions
      );


      if (
        activeSessionId ===
        sessionId
      ) {
        if (
          remainingSessions.length >
          0
        ) {
          const nextId =
            remainingSessions[0]
              .id;

          await loadSession(
            nextId,
            false
          );

        } else {
          setActiveSessionId(
            null
          );

          setMessages(
            []
          );
        }
      }

    } catch (error) {
      if (
        error instanceof Error
      ) {
        setError(
          error.message
        );
      } else {
        setError(
          "Белгісіз қате шықты."
        );
      }
    }
  }


  // =====================================================
  // STOP GENERATING
  // =====================================================

  function stopGenerating() {
    streamAbortControllerRef.current?.abort();
  }


  // =====================================================
  // SEND MESSAGE (STREAMING)
  // =====================================================

  async function sendMessage() {
    const message =
      input.trim();

    if (
      !message ||
      loading ||
      regenerating ||
      activeSessionId ===
        null
    ) {
      return;
    }

    const token =
      getToken();

    if (!token) {
      handleUnauthorized();
      return;
    }

    const sessionId =
      activeSessionId;

    setError("");
    setIsUserNearBottom(
      true
    );

    const optimisticUserMessage: ChatMessage = {
      role: "user",
      content: message,
    };

    const streamingAssistantMessage: ChatMessage = {
      role: "assistant",
      content: "",
    };

    setMessages(
      (
        current
      ) => [
        ...current,
        optimisticUserMessage,
        streamingAssistantMessage,
      ]
    );

    setInput("");
    setLoading(true);

    const controller =
      new AbortController();

    streamAbortControllerRef.current =
      controller;

    try {
      const response =
        await fetch(
          `${API_URL}/chat/stream`,
          {
            method: "POST",

            signal:
              controller.signal,

            headers: {
              "Content-Type":
                "application/json",

              Authorization:
                `Bearer ${token}`,
            },

            body:
              JSON.stringify({
                session_id:
                  sessionId,

                message,
              }),
          }
        );

      if (
        response.status ===
        401
      ) {
        handleUnauthorized();
        return;
      }

      if (!response.ok) {
        let detail =
          "Сұраныс кезінде қате шықты.";

        try {
          const data =
            await response.json();

          if (
            typeof data.detail ===
            "string"
          ) {
            detail =
              data.detail;
          }
        } catch {
          // Streaming емес error body болса да
          // generic message жеткілікті.
        }

        throw new Error(
          detail
        );
      }

      if (!response.body) {
        throw new Error(
          "Streaming response body табылмады."
        );
      }

      const reader =
        response.body.getReader();

      const decoder =
        new TextDecoder(
          "utf-8"
        );

      let assistantText =
        "";

      while (true) {
        const {
          done,
          value,
        } =
          await reader.read();

        if (done) {
          break;
        }

        const chunk =
          decoder.decode(
            value,
            {
              stream: true,
            }
          );

        if (!chunk) {
          continue;
        }

        assistantText +=
          chunk;

        setMessages(
          (
            current
          ) => {
            const next =
              [...current];

            for (
              let index =
                next.length - 1;
              index >= 0;
              index -= 1
            ) {
              if (
                next[index].role ===
                "assistant"
              ) {
                next[index] = {
                  ...next[index],
                  content:
                    assistantText,
                };

                break;
              }
            }

            return next;
          }
        );
      }

      const finalChunk =
        decoder.decode();

      if (finalChunk) {
        assistantText +=
          finalChunk;

        setMessages(
          (
            current
          ) => {
            const next =
              [...current];

            for (
              let index =
                next.length - 1;
              index >= 0;
              index -= 1
            ) {
              if (
                next[index].role ===
                "assistant"
              ) {
                next[index] = {
                  ...next[index],
                  content:
                    assistantText,
                };

                break;
              }
            }

            return next;
          }
        );
      }

      if (
        !assistantText.trim()
      ) {
        throw new Error(
          "AI жауабы бос келді."
        );
      }

      await refreshSessionList();

    } catch (error) {
      const wasAborted =
        error instanceof DOMException &&
        error.name ===
          "AbortError";

      if (wasAborted) {
        // Stop басылса, келіп үлгерген partial жауапты қалдырамыз.
        // Бірде-бір chunk келмесе, бос assistant placeholder өшеді.
        setMessages(
          (
            current
          ) => {
            const next =
              [...current];

            const last =
              next[
                next.length - 1
              ];

            if (
              last?.role ===
                "assistant" &&
              !last.content.trim()
            ) {
              next.pop();
            }

            return next;
          }
        );

      } else {
        setMessages(
          (
            current
          ) => {
            const next =
              [...current];

            if (
              next.length > 0 &&
              next[
                next.length - 1
              ].role ===
                "assistant"
            ) {
              next.pop();
            }

            if (
              next.length > 0
            ) {
              const last =
                next[
                  next.length - 1
                ];

              if (
                last.role ===
                  "user" &&
                last.content ===
                  message
              ) {
                next.pop();
              }
            }

            return next;
          }
        );

        setInput(
          message
        );

        if (
          error instanceof Error
        ) {
          setError(
            error.message
          );
        } else {
          setError(
            "Белгісіз қате шықты."
          );
        }
      }

    } finally {
      if (
        streamAbortControllerRef.current ===
        controller
      ) {
        streamAbortControllerRef.current =
          null;
      }

      setLoading(
        false
      );
    }
  }


  // =====================================================
  // REGENERATE LAST ANSWER
  // =====================================================

  async function regenerateLastAnswer() {
    if (
      loading ||
      regenerating ||
      activeSessionId === null
    ) {
      return;
    }

    const token =
      getToken();

    if (!token) {
      handleUnauthorized();
      return;
    }

    let lastAssistantIndex = -1;
    let lastUserMessage = "";

    for (
      let index = messages.length - 1;
      index >= 0;
      index -= 1
    ) {
      if (
        lastAssistantIndex === -1 &&
        messages[index].role === "assistant"
      ) {
        lastAssistantIndex = index;
        continue;
      }

      if (
        lastAssistantIndex !== -1 &&
        messages[index].role === "user"
      ) {
        lastUserMessage =
          messages[index].content;
        break;
      }
    }

    if (
      lastAssistantIndex === -1 ||
      !lastUserMessage
    ) {
      setError(
        "Қайта жауап беруге жарамды соңғы сұрақ табылмады."
      );
      return;
    }

    setError("");
    setIsUserNearBottom(
      true
    );
    setRegenerating(true);

    try {
      const response =
        await fetch(
          `${API_URL}/chat/regenerate`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",

              Authorization:
                `Bearer ${token}`,
            },

            body:
              JSON.stringify({
                session_id:
                  activeSessionId,
              }),
          }
        );

      if (
        response.status ===
        401
      ) {
        handleUnauthorized();
        return;
      }

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Жауапты қайта дайындау кезінде қате шықты."
        );
      }

      // Backend соңғы assistant жауабын DB-де
      // ауыстырғаннан кейін session-ды қайта жүктейміз.
      await loadSession(
        activeSessionId,
        false
      );

      await refreshSessionList();

    } catch (error) {
      if (
        error instanceof Error
      ) {
        setError(
          error.message
        );
      } else {
        setError(
          "Белгісіз қате шықты."
        );
      }

    } finally {
      setRegenerating(
        false
      );
    }
  }


  // =====================================================
  // REFRESH SESSION LIST
  // =====================================================

  async function refreshSessionList() {
    const token =
      getToken();

    if (!token) {
      return;
    }

    try {
      const response =
        await fetch(
          `${API_URL}/sessions`,
          {
            headers: {
              Authorization:
                `Bearer ${token}`,
            },
          }
        );


      if (!response.ok) {
        return;
      }


      const data =
        await response.json();


      setSessions(
        data
      );

    } catch {
      // Sidebar жаңармаса да
      // chat тоқтамауы тиіс.
    }
  }


  // =====================================================
  // LOGOUT
  // =====================================================

  function handleLogout() {
    localStorage.removeItem(
      "access_token"
    );

    router.replace(
      "/login"
    );
  }


  // =====================================================
  // ENTER SEND
  // =====================================================

  function handleKeyDown(
    event:
      React.KeyboardEvent<HTMLTextAreaElement>
  ) {
    if (
      event.nativeEvent.isComposing
    ) {
      return;
    }

    if (
      event.key ===
        "Enter" &&
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
    setInput(
      prompt
    );

    window.requestAnimationFrame(
      () => {
        textareaRef.current
          ?.focus();
      }
    );
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
                setSidebarOpen(
                  false
                )
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
            type="button"
            onClick={
              createNewChat
            }
            disabled={
              loading ||
              regenerating ||
              sessionLoading
            }
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
              disabled:cursor-not-allowed
              disabled:opacity-50
            "
          >
            + Жаңа чат
          </button>

        </div>


        <div className="flex-1 overflow-y-auto p-2">

          {sessionsLoading && (
            <div className="space-y-2 px-2 py-3">

              {[
                1,
                2,
                3,
                4,
              ].map(
                (
                  item
                ) => (
                  <div
                    key={
                      item
                    }
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
            sessions.length ===
              0 && (
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
              (
                session
              ) => (
                <div
                  key={
                    session.id
                  }
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
                    {
                      session.title
                    }
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


<div className="border-t border-neutral-900 p-4">

  <div className="mb-3 text-sm font-medium">
    ERKEK AI
  </div>

  <div className="space-y-1">

    <button
      type="button"
      onClick={() => {
        setSidebarOpen(false);
        router.push("/settings");
      }}
      className="
        flex
        w-full
        items-center
        gap-3
        rounded-lg
        px-2
        py-2
        text-left
        text-sm
        text-neutral-500
        transition
        hover:bg-neutral-900
        hover:text-white
      "
    >
      <span>⚙</span>
      <span>Баптаулар</span>
    </button>

    <button
      type="button"
      onClick={handleLogout}
      className="
        flex
        w-full
        items-center
        gap-3
        rounded-lg
        px-2
        py-2
        text-left
        text-sm
        text-neutral-500
        transition
        hover:bg-neutral-900
        hover:text-white
      "
    >
      <span>↪</span>
      <span>Шығу</span>
    </button>

  </div>

</div>
      </>
    );
  }


  // =====================================================
  // UI
  // =====================================================

  return (
    <main className="flex h-dvh overflow-hidden bg-black text-white">

      {/* DESKTOP SIDEBAR */}

      <aside className="hidden w-72 shrink-0 flex-col border-r border-neutral-900 bg-neutral-950 lg:flex">
        <SidebarContent />
      </aside>


      {/* MOBILE OVERLAY */}

      {sidebarOpen && (
        <button
          type="button"
          aria-label="Мәзірді жабу"
          onClick={() =>
            setSidebarOpen(
              false
            )
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


      {/* MOBILE SIDEBAR */}

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


      {/* MAIN CHAT */}

      <section className="flex min-w-0 flex-1 flex-col">

        {/* HEADER */}

        <header className="flex h-16 shrink-0 items-center border-b border-neutral-900 px-3 sm:px-5 lg:px-6">

          <button
            onClick={() =>
              setSidebarOpen(
                true
              )
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
              {
                activeSession
                  ? activeSession.title
                  : "ERKEK AI"
              }
            </div>

            <div className="text-xs text-neutral-500">
              {
                activeSession
                  ? "ERKEK AI · Digital mentor"
                  : "Digital mentor"
              }
            </div>

          </div>

        </header>


        {/* CHAT MESSAGES */}

        <div
          ref={chatScrollRef}
          onScroll={handleChatScroll}
          className="relative min-h-0 flex-1 overflow-y-auto"
        >

          {sessionLoading && (
            <div className="pointer-events-none sticky top-3 z-20 mx-auto flex w-fit items-center gap-2 rounded-full border border-white/[0.08] bg-neutral-950/90 px-3 py-1.5 text-xs text-neutral-400 shadow-lg backdrop-blur">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-neutral-500" />
              Әңгіме жүктелуде...
            </div>
          )}

          {!isUserNearBottom &&
            activeSessionId !== null && (
              <button
                type="button"
                onClick={scrollToBottom}
                className="sticky top-[calc(100%-3rem)] z-20 mx-auto mb-2 flex h-9 items-center gap-2 rounded-full border border-white/[0.08] bg-neutral-950/95 px-3 text-xs text-neutral-300 shadow-lg backdrop-blur transition hover:bg-neutral-900 hover:text-white"
                aria-label="Соңғы хабарламаға өту"
              >
                ↓ Соңғы хабарлама
              </button>
            )}

          <div className="mx-auto w-full max-w-4xl px-3 py-6 sm:px-5 sm:py-8 lg:px-6">

            {activeSessionId ===
            null ? (

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
                  onClick={
                    createNewChat
                  }
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

                {messages.length ===
                  0 &&
                  !loading && (
                  <div className="flex min-h-[55vh] flex-col items-center justify-center px-4 text-center">

                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-lg font-black text-black">
                      E
                    </div>

                    <h2 className="mt-5 text-xl font-semibold sm:text-2xl">
                      Не туралы сөйлесеміз?
                    </h2>

                    <p className="mt-2 max-w-md text-sm leading-6 text-neutral-500">
                      Жұмыс, қаржы,
                      отбасы, мақсаттар
                      немесе ойыңда жүрген
                      кез келген мәселені жаз.
                    </p>


                    <div className="mt-6 grid w-full max-w-xl gap-2 sm:grid-cols-2">

                      {[
                        "Жұмыс туралы кеңес керек",
                        "Қаржы жоспарымды талдайық",
                        "Мақсаттарымды реттегім келеді",
                        "Бір мәселе мазалап жүр",
                      ].map(
                        (
                          prompt
                        ) => (
                          <button
                            key={
                              prompt
                            }
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
                            {
                              prompt
                            }
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
                                group/message
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


                        {message.role ===
                        "assistant" ? (
                          <>
                            <MarkdownMessage
                              content={
                                message.content
                              }
                            />

                            {/* MESSAGE COPY */}

                            <div className="mt-2 flex items-center gap-1">
                              <CopyButton
                                text={
                                  message.content
                                }
                              />

                              {index ===
                                messages.length - 1 && (
                                <button
                                  type="button"
                                  onClick={
                                    regenerateLastAnswer
                                  }
                                  disabled={
                                    loading ||
                                    regenerating
                                  }
                                  className="
                                    inline-flex
                                    items-center
                                    rounded-lg
                                    px-2
                                    py-1
                                    text-xs
                                    text-neutral-600
                                    transition
                                    hover:bg-white/[0.04]
                                    hover:text-neutral-300
                                    disabled:cursor-not-allowed
                                    disabled:opacity-40
                                  "
                                >
                                  {regenerating
                                    ? "Қайта дайындалуда..."
                                    : "Қайта жауап беру"}
                                </button>
                              )}
                            </div>
                          </>
                        ) : (
                          <div className="whitespace-pre-wrap break-words text-[15px] leading-7 sm:text-base">
                            {
                              message.content
                            }
                          </div>
                        )}

                      </div>

                    </div>
                  )
                )}


                {/* AI LOADING */}

                {(
                  regenerating ||
                  (
                    loading &&
                    messages[
                      messages.length - 1
                    ]?.role ===
                      "assistant" &&
                    !messages[
                      messages.length - 1
                    ]?.content
                  )
                ) && (
                  <div className="flex justify-start">

                    <div className="max-w-[85%]">

                      <div className="mb-2 text-xs font-medium text-neutral-500">
                        ERKEK AI
                      </div>

                      <div className="flex items-center gap-2 text-sm text-neutral-500">

                        <div className="flex items-center gap-1.5">
                          <span className="h-2 w-2 animate-bounce rounded-full bg-neutral-600 [animation-delay:-0.3s]" />
                          <span className="h-2 w-2 animate-bounce rounded-full bg-neutral-600 [animation-delay:-0.15s]" />
                          <span className="h-2 w-2 animate-bounce rounded-full bg-neutral-600" />
                        </div>

                        <span>
                          {regenerating
                            ? "Жауап қайта дайындалуда..."
                            : "Жауап басталуда..."}
                        </span>

                      </div>

                    </div>

                  </div>
                )}


                <div
                  ref={
                    bottomRef
                  }
                />

              </div>

            )}

          </div>

        </div>


        {/* INPUT */}

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
                    setError(
                      ""
                    )
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
                ref={textareaRef}
                value={
                  input
                }
                onChange={(
                  event
                ) =>
                  setInput(
                    event.target
                      .value
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
                aria-label="Хабарлама"
                aria-busy={
                  loading ||
                  regenerating
                }
                disabled={
                  loading ||
                  regenerating ||
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


              {loading ? (
                <button
                  type="button"
                  onClick={
                    stopGenerating
                  }
                  aria-label="Жауапты тоқтату"
                  title="Жауапты тоқтату"
                  className="
                    flex
                    h-11
                    shrink-0
                    items-center
                    justify-center
                    gap-2
                    rounded-xl
                    bg-white
                    px-3
                    text-sm
                    font-medium
                    text-black
                    transition
                    hover:bg-neutral-200
                    sm:px-5
                    sm:text-base
                  "
                >
                  <span className="h-3 w-3 rounded-[2px] bg-black" />

                  <span className="hidden sm:inline">
                    Тоқтату
                  </span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={
                    sendMessage
                  }
                  aria-label="Хабарламаны жіберу"
                  disabled={
                    regenerating ||
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
              )}

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