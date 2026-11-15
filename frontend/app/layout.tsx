import type { Metadata } from "next";
import { Cormorant_Garamond, Manrope } from "next/font/google";
import "./globals.css";

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin", "cyrillic", "cyrillic-ext"],
});

const cormorant = Cormorant_Garamond({
  variable: "--font-cormorant",
  subsets: ["latin", "cyrillic", "cyrillic-ext"],
  weight: ["500", "600", "700"],
});

export const metadata: Metadata = {
  title: "ERKEK AI — Digital mentor",
  description:
    "ERKEK AI — ер адамдарға арналған AI-негізіндегі цифрлық ментор.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="kk"
      className={`${manrope.variable} ${cormorant.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
