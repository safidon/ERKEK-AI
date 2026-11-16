import { ImageResponse } from "next/og";

// WhatsApp, Telegram, Facebook-та сілтеме бөліскенде шығатын сурет.
// Мәтін латынша: екі тілге де ортақ және қосымша шрифт қажет етпейді.

export const alt = "ERKEK AI — Digital mentor for men";

export const size = {
  width: 1200,
  height: 630,
};

export const contentType = "image/png";

const GOLD = "#d4af5f";
const GOLD_LIGHT = "#f1d79a";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "#0c0b09",
          backgroundImage:
            "radial-gradient(circle at 50% 0%, rgba(212,175,95,0.28), rgba(12,11,9,0) 60%)",
          color: "#f5f1e8",
          fontFamily: "serif",
        }}
      >
        <div
          style={{
            width: 132,
            height: 132,
            borderRadius: 32,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: `linear-gradient(135deg, ${GOLD_LIGHT}, ${GOLD} 55%, #a8853f)`,
            color: "#0c0b09",
            fontSize: 84,
            fontWeight: 700,
          }}
        >
          E
        </div>

        <div
          style={{
            marginTop: 44,
            fontSize: 104,
            fontWeight: 700,
            letterSpacing: 10,
          }}
        >
          ERKEK AI
        </div>

        <div
          style={{
            marginTop: 10,
            fontSize: 34,
            color: GOLD,
            letterSpacing: 12,
            textTransform: "uppercase",
          }}
        >
          Digital mentor for men
        </div>

        <div
          style={{
            marginTop: 48,
            width: 120,
            height: 2,
            background: GOLD,
            opacity: 0.6,
          }}
        />

        <div
          style={{
            marginTop: 36,
            fontSize: 30,
            color: "#a39d91",
            letterSpacing: 4,
          }}
        >
          erkekai.kz
        </div>
      </div>
    ),
    size
  );
}
