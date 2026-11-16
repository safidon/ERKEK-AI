import type { MetadataRoute } from "next";

// Телефонға «қосымша» ретінде орнату үшін (PWA).
export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/",
    name: "ERKEK AI — Digital mentor",
    short_name: "ERKEK AI",
    description:
      "Ер адамдарға арналған AI-негізіндегі цифрлық ментор.",
    lang: "kk",
    start_url: "/chat",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#0c0b09",
    theme_color: "#0c0b09",
    categories: ["lifestyle", "productivity"],
    icons: [
      {
        src: "/icon-192x192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icon-512x512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icon-maskable-512x512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
