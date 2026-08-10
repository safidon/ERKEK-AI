const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

export async function registerUser(
  email: string,
  username: string,
  password: string
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