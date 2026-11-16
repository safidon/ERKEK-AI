import type { Metadata, Viewport } from "next";
import { Cormorant_Garamond, Manrope } from "next/font/google";
import "./globals.css";

import { LanguageProvider } from "@/lib/i18n";
import { getLang } from "@/lib/lang-server";
import { SITE_URL } from "@/lib/site";

import { ErrorReporter } from "./error-reporter";

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin", "cyrillic", "cyrillic-ext"],
});

const cormorant = Cormorant_Garamond({
  variable: "--font-cormorant",
  subsets: ["latin", "cyrillic", "cyrillic-ext"],
  weight: ["500", "600", "700"],
});

export async function generateMetadata(): Promise<Metadata> {
  const lang = await getLang();
  const ru = lang === "ru";

  const title = ru
    ? "ERKEK AI — ИИ-наставник для мужчин"
    : "ERKEK AI — ер адамдарға арналған AI ментор";

  const description = ru
    ? "Личный ИИ-наставник: работа, деньги, семья, цели и решения. Отвечает на казахском и русском. На сайте и в Telegram."
    : "Жеке AI ментор: жұмыс, ақша, отбасы, мақсат және шешімдер туралы. Қазақша және орысша жауап береді. Сайтта және Telegram-да.";

  return {
    metadataBase: new URL(SITE_URL),
    title: {
      default: title,
      template: "%s — ERKEK AI",
    },
    description,
    keywords: ru
      ? ["ИИ-наставник", "мужчины", "психология", "мотивация", "Казахстан", "ERKEK AI"]
      : ["AI ментор", "ер адам", "кеңес", "мотивация", "Қазақстан", "ERKEK AI"],
    openGraph: {
      type: "website",
      url: SITE_URL,
      siteName: "ERKEK AI",
      title,
      description,
      locale: ru ? "ru_RU" : "kk_KZ",
      alternateLocale: ru ? ["kk_KZ"] : ["ru_RU"],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
    },
    applicationName: "ERKEK AI",
    // iPhone: «Экранға қосу» кезінде толық экранда ашылады
    appleWebApp: {
      capable: true,
      title: "ERKEK AI",
      statusBarStyle: "black",
    },
  };
}

export const viewport: Viewport = {
  themeColor: "#0c0b09",
  colorScheme: "dark",
};

export default async function RootLayout({ children }: LayoutProps<"/">) {
  const lang = await getLang();

  return (
    <html
      lang={lang}
      className={`${manrope.variable} ${cormorant.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <LanguageProvider initialLang={lang}>
          <ErrorReporter />
          {children}
        </LanguageProvider>
      </body>
    </html>
  );
}
