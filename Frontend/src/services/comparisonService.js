import {
  clearStoredToken,
  getStoredToken,
} from "./authService";


const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";


function createApiError(
  message,
  status = 0,
) {
  const error = new Error(message);

  error.status = status;

  return error;
}


async function getErrorMessage(response) {
  try {
    const data = await response.json();

    if (typeof data.detail === "string") {
      return data.detail;
    }

    if (Array.isArray(data.detail)) {
      return data.detail
        .map((item) => {
          return (
            item.msg ||
            "Invalid request."
          );
        })
        .join(" ");
    }

    return "Something went wrong.";
  } catch {
    return (
      "Could not read the server response."
    );
  }
}


function getAuthorizationHeaders() {
  const token = getStoredToken();

  if (!token) {
    throw createApiError(
      "You must sign in to continue.",
      401,
    );
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}


async function authorizedRequest(
  endpoint,
  options = {},
) {
  const authorizationHeaders =
    getAuthorizationHeaders();

  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,

      headers: {
        ...authorizationHeaders,
        ...(options.headers || {}),
      },
    },
  );

  if (!response.ok) {
    if (response.status === 401) {
      clearStoredToken();
    }

    const message =
      await getErrorMessage(response);

    throw createApiError(
      message,
      response.status,
    );
  }

  return response.json();
}


export async function generateComparison(
  paperAId,
  paperBId,
) {
  const firstPaperId =
    Number(paperAId);

  const secondPaperId =
    Number(paperBId);

  if (
    !Number.isInteger(firstPaperId) ||
    !Number.isInteger(secondPaperId) ||
    firstPaperId <= 0 ||
    secondPaperId <= 0
  ) {
    throw createApiError(
      "Please select two valid research papers.",
      400,
    );
  }

  if (firstPaperId === secondPaperId) {
    throw createApiError(
      "Please select two different research papers.",
      400,
    );
  }

  return authorizedRequest(
    "/comparisons",
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        paper_a_id: firstPaperId,
        paper_b_id: secondPaperId,
      }),
    },
  );
}


export async function getComparisons() {
  return authorizedRequest(
    "/comparisons",
    {
      method: "GET",
    },
  );
}


export async function getComparison(
  comparisonId,
) {
  const numericComparisonId =
    Number(comparisonId);

  if (
    !Number.isInteger(
      numericComparisonId,
    ) ||
    numericComparisonId <= 0
  ) {
    throw createApiError(
      "Invalid comparison ID.",
      400,
    );
  }

  return authorizedRequest(
    `/comparisons/${numericComparisonId}`,
    {
      method: "GET",
    },
  );
}