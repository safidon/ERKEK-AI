import type { Metadata, Viewport } from "next";
import { Cormorant_Garamond, Manrope } from "next/font/google";
import "./globals.css";

import { LanguageProvider } from "@/lib/i18n";
import { getLang } from "@/lib/lang-server";

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

  return {
    title: "ERKEK AI — Digital mentor",
    description:
      lang === "ru"
        ? "ERKEK AI — цифровой наставник для мужчин на основе ИИ."
        : "ERKEK AI — ер адамдарға арналған AI-негізіндегі цифрлық ментор.",
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
        <LanguageProvider initialLang={lang}>{children}</LanguageProvider>
      </body>
    </html>
  );
}
