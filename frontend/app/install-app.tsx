"use client";

import { useEffect, useState } from "react";


// =====================================================
// «ТЕЛЕФОНҒА ОРНАТУ» (PWA)
// =====================================================
// - Android / Chrome / Edge: браузер "beforeinstallprompt" жібереді —
//   батырма бір басумен орнатады.
// - iPhone / iPad (Safari): автоматты орнату жоқ — қысқа нұсқаулық көрсетеміз.
// - Қосымша ретінде ашылып тұрса (standalone) — ештеңе көрсетпейміз.

type InstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};


function isStandalone() {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    // iOS Safari
    (navigator as Navigator & { standalone?: boolean }).standalone === true
  );
}


function isIos() {
  const ua = navigator.userAgent;
  return (
    /iPad|iPhone|iPod/.test(ua) ||
    // iPadOS өзін Mac деп көрсетеді
    (ua.includes("Macintosh") && navigator.maxTouchPoints > 1)
  );
}


export function InstallAppButton({
  className = "",
}: {
  className?: string;
}) {
  const [promptEvent, setPromptEvent] =
    useState<InstallPromptEvent | null>(null);
  const [ios, setIos] = useState(false);
  const [installed, setInstalled] = useState(true);
  const [showIosHelp, setShowIosHelp] = useState(false);

  useEffect(() => {
    // Тек браузерде ғана анықталатын мәндер — mount кезінде бір рет.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setInstalled(isStandalone());
    setIos(isIos());

    function handlePrompt(event: Event) {
      event.preventDefault();
      setPromptEvent(event as InstallPromptEvent);
    }

    function handleInstalled() {
      setInstalled(true);
      setPromptEvent(null);
    }

    window.addEventListener("beforeinstallprompt", handlePrompt);
    window.addEventListener("appinstalled", handleInstalled);

    return () => {
      window.removeEventListener("beforeinstallprompt", handlePrompt);
      window.removeEventListener("appinstalled", handleInstalled);
    };
  }, []);


  if (installed || (!promptEvent && !ios)) {
    return null;
  }


  async function install() {
    if (promptEvent) {
      try {
        await promptEvent.prompt();
        const choice = await promptEvent.userChoice;
        if (choice.outcome === "accepted") {
          setInstalled(true);
        }
      } catch {
        // Бұл хабарлама бұрын қолданылған (мысалы, мәзірдің басқа көшірмесінде).
      }
      setPromptEvent(null);
      return;
    }

    setShowIosHelp((value) => !value);
  }


  return (
    <div className={className}>

      <button
        type="button"
        onClick={() => void install()}
        className="flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left text-sm text-neutral-300 transition hover:bg-neutral-900 hover:text-gold-300"
      >
        <span aria-hidden>📲</span>
        <span>Телефонға орнату</span>
      </button>

      {showIosHelp && (
        <div className="mt-2 rounded-xl border border-gold-500/25 bg-gold-500/[0.06] p-3 text-xs leading-5 text-neutral-300">
          <div className="mb-1 font-semibold text-gold-300">
            iPhone-ға орнату:
          </div>
          <ol className="list-decimal space-y-1 pl-4">
            <li>
              Safari-де төмендегі <strong>«Бөлісу»</strong> батырмасын бас
              (жоғары бағытталған нұсқамасы бар шаршы).
            </li>
            <li>
              Тізімнен <strong>«Экранға қосу»</strong> («На экран
              «Домой»») таңда.
            </li>
            <li>
              <strong>«Қосу»</strong> бас — ERKEK AI иконкасы негізгі
              экранда пайда болады.
            </li>
          </ol>
        </div>
      )}

    </div>
  );
}
