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

  return data as {
    user_id: string;
    email: string;
    username: string;
    is_active: boolean;
    email_verification_required?: boolean;
  };
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
    // status: 403 — email әлі расталмаған (кіру бетінде «қайта жіберу» шығады).
    throw Object.assign(
      new Error(data.detail || "Кіру кезінде қате шықты."),
      { status: response.status }
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


// =====================================================
// EMAIL VERIFICATION
// =====================================================

export async function verifyEmail(token: string) {
  const response = await fetch(
    `${API_URL}/auth/verify-email`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ token }),
    }
  );

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(errorMessage(data, ""));
  }

  return data as {
    access_token: string;
    refresh_token: string;
  };
}

export async function resendVerification(email: string) {
  const response = await fetch(
    `${API_URL}/auth/resend-verification`,
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
    throw new Error(errorMessage(data, ""));
  }

  return data as { detail: string };
}
