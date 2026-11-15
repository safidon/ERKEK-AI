const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

export async function registerUser(
  email: string,
  username: string,
  password: string,
  acceptTerms: boolean
) {
  const response = await fetch(
    `${API_URL}/auth/register`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        username,
        password,
        accept_terms: acceptTerms,
      }),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Тіркелу кезінде қате шықты."
    );
  }

  return data;
}

export async function loginUser(
  email: string,
  password: string
) {
  const response = await fetch(
    `${API_URL}/auth/login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        password,
      }),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Кіру кезінде қате шықты."
    );
  }

  return data;
}

// =====================================================
// PASSWORD RESET
// =====================================================

function errorMessage(data: unknown, fallback: string) {
  const detail = (data as { detail?: unknown })?.detail;

  // FastAPI validation қатесі тізім түрінде келеді.
  if (typeof detail === "string") {
    return detail;
  }

  return fallback;
}

export async function requestPasswordReset(email: string) {
  const response = await fetch(
    `${API_URL}/auth/forgot-password`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email }),
    }
  );

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      errorMessage(data, "Сұранысты жіберу кезінде қате шықты.")
    );
  }

  return data as { detail: string };
}

export async function resetPassword(
  token: string,
  password: string
) {
  const response = await fetch(
    `${API_URL}/auth/reset-password`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ token, password }),
    }
  );

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      errorMessage(data, "Құпиясөзді ауыстыру кезінде қате шықты.")
    );
  }

  return data as { detail: string };
}
