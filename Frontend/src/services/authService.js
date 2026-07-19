const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const TOKEN_KEY = "papermind_access_token";


async function getErrorMessage(response) {
  try {
    const data = await response.json();

    if (typeof data.detail === "string") {
      return data.detail;
    }

    if (Array.isArray(data.detail)) {
      return data.detail
        .map((error) => error.msg || "Invalid input")
        .join(" ");
    }

    return "Something went wrong. Please try again.";
  } catch {
    return "Could not connect to the PaperMind server.";
  }
}


export async function registerUser({
  fullName,
  email,
  password,
}) {
  const response = await fetch(
    `${API_BASE_URL}/auth/register`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        full_name: fullName.trim(),
        email: email.trim().toLowerCase(),
        password,
      }),
    },
  );

  if (!response.ok) {
    const message = await getErrorMessage(response);
    throw new Error(message);
  }

  return response.json();
}


export async function loginUser({
  email,
  password,
}) {
  const formData = new URLSearchParams();

  // FastAPI OAuth2 calls this field "username",
  // but we are entering the user's email.
  formData.append(
    "username",
    email.trim().toLowerCase(),
  );

  formData.append("password", password);

  const response = await fetch(
    `${API_BASE_URL}/auth/login`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/x-www-form-urlencoded",
      },

      body: formData,
    },
  );

  if (!response.ok) {
    const message = await getErrorMessage(response);
    throw new Error(message);
  }

  return response.json();
}


export function saveToken(
  accessToken,
  rememberMe = false,
) {
  clearStoredToken();

  const storage = rememberMe
    ? window.localStorage
    : window.sessionStorage;

  storage.setItem(TOKEN_KEY, accessToken);
}


export function getStoredToken() {
  return (
    window.localStorage.getItem(TOKEN_KEY) ||
    window.sessionStorage.getItem(TOKEN_KEY)
  );
}


export function clearStoredToken() {
  window.localStorage.removeItem(TOKEN_KEY);
  window.sessionStorage.removeItem(TOKEN_KEY);
}


export async function getCurrentUser() {
  const token = getStoredToken();

  if (!token) {
    throw new Error("You are not signed in.");
  }

  const response = await fetch(
    `${API_BASE_URL}/auth/me`,
    {
      method: "GET",

      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );

  if (!response.ok) {
    if (response.status === 401) {
      clearStoredToken();
    }

    const message = await getErrorMessage(response);
    throw new Error(message);
  }

  return response.json();
}