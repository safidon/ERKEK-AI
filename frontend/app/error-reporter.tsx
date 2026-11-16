"use client";

import { useEffect } from "react";

import { reportClientError } from "@/lib/report-error";

// Бүкіл сайттағы күтпеген JavaScript қателерін тыңдайды.
export function ErrorReporter() {
  useEffect(() => {
    const onError = (event: ErrorEvent) => {
      reportClientError(event.error ?? event.message, "window.onerror");
    };

    const onRejection = (event: PromiseRejectionEvent) => {
      reportClientError(event.reason, "unhandledrejection");
    };

    window.addEventListener("error", onError);
    window.addEventListener("unhandledrejection", onRejection);

    return () => {
      window.removeEventListener("error", onError);
      window.removeEventListener("unhandledrejection", onRejection);
    };
  }, []);

  return null;
}
