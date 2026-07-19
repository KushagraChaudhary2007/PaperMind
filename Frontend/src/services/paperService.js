import {
  clearStoredToken,
  getStoredToken,
} from "./authService";


const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";


function createApiError(message, status = 0) {
  const error = new Error(message);

  error.status = status;

  return error;
}


async function getFetchErrorMessage(response) {
  try {
    const responseData = await response.json();

    if (typeof responseData.detail === "string") {
      return responseData.detail;
    }

    if (Array.isArray(responseData.detail)) {
      return responseData.detail
        .map((item) => {
          return item.msg || "Invalid request.";
        })
        .join(" ");
    }

    return "Something went wrong.";
  } catch {
    return "Could not read the server response.";
  }
}


function getUploadErrorMessage(xhr) {
  try {
    const responseData = JSON.parse(
      xhr.responseText,
    );

    if (typeof responseData.detail === "string") {
      return responseData.detail;
    }

    return "The PDF could not be uploaded.";
  } catch {
    return "The PDF could not be uploaded.";
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


function handleUnauthorizedResponse(status) {
  if (status === 401) {
    clearStoredToken();
  }
}


function validatePaperId(paperId) {
  const numericPaperId = Number(paperId);

  if (
    !Number.isInteger(numericPaperId) ||
    numericPaperId <= 0
  ) {
    throw createApiError(
      "Invalid research paper ID.",
      400,
    );
  }

  return numericPaperId;
}


async function authorizedJsonRequest(
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
    handleUnauthorizedResponse(
      response.status,
    );

    const message =
      await getFetchErrorMessage(response);

    throw createApiError(
      message,
      response.status,
    );
  }

  return response.json();
}


export function uploadPaper(
  file,
  onProgress = () => {},
) {
  return new Promise((resolve, reject) => {
    let authorizationHeaders;

    try {
      authorizationHeaders =
        getAuthorizationHeaders();
    } catch (error) {
      reject(error);
      return;
    }

    const formData = new FormData();

    formData.append("file", file);

    const xhr = new XMLHttpRequest();

    xhr.open(
      "POST",
      `${API_BASE_URL}/papers/upload`,
    );

    xhr.setRequestHeader(
      "Authorization",
      authorizationHeaders.Authorization,
    );

    xhr.timeout = 120000;

    xhr.upload.addEventListener(
      "progress",
      (event) => {
        if (!event.lengthComputable) {
          return;
        }

        const percentage = Math.round(
          (event.loaded / event.total) * 100,
        );

        onProgress(percentage);
      },
    );

    xhr.addEventListener("load", () => {
      let responseData = null;

      try {
        responseData = JSON.parse(
          xhr.responseText,
        );
      } catch {
        responseData = null;
      }

      if (
        xhr.status >= 200 &&
        xhr.status < 300
      ) {
        onProgress(100);
        resolve(responseData);
        return;
      }

      handleUnauthorizedResponse(
        xhr.status,
      );

      reject(
        createApiError(
          getUploadErrorMessage(xhr),
          xhr.status,
        ),
      );
    });

    xhr.addEventListener("error", () => {
      reject(
        createApiError(
          "Could not connect to the PaperMind server.",
        ),
      );
    });

    xhr.addEventListener("timeout", () => {
      reject(
        createApiError(
          "The upload took too long. Please try again.",
        ),
      );
    });

    xhr.addEventListener("abort", () => {
      reject(
        createApiError(
          "The upload was cancelled.",
        ),
      );
    });

    xhr.send(formData);
  });
}


export async function getUserPapers() {
  return authorizedJsonRequest(
    "/papers",
    {
      method: "GET",
    },
  );
}


export async function getPaperText(paperId) {
  const numericPaperId =
    validatePaperId(paperId);

  return authorizedJsonRequest(
    `/papers/${numericPaperId}/text`,
    {
      method: "GET",
    },
  );
}


export async function getPaperSummary(paperId) {
  const numericPaperId =
    validatePaperId(paperId);

  return authorizedJsonRequest(
    `/papers/${numericPaperId}/summary`,
    {
      method: "GET",
    },
  );
}


export async function generatePaperSummary(
  paperId,
) {
  const numericPaperId =
    validatePaperId(paperId);

  return authorizedJsonRequest(
    `/papers/${numericPaperId}/summary`,
    {
      method: "POST",
    },
  );
}

const VALID_EXPLANATION_LEVELS = new Set([
  "beginner",
  "intermediate",
  "expert",
]);


function validateExplanationLevel(level) {
  const normalizedLevel = String(level)
    .trim()
    .toLowerCase();

  if (
    !VALID_EXPLANATION_LEVELS.has(
      normalizedLevel,
    )
  ) {
    throw createApiError(
      "Invalid explanation level.",
      400,
    );
  }

  return normalizedLevel;
}


export async function getPaperExplanation(
  paperId,
  level,
) {
  const numericPaperId =
    validatePaperId(paperId);

  const normalizedLevel =
    validateExplanationLevel(level);

  return authorizedJsonRequest(
    `/papers/${numericPaperId}/explanations/${normalizedLevel}`,
    {
      method: "GET",
    },
  );
}


export async function generatePaperExplanation(
  paperId,
  level,
) {
  const numericPaperId =
    validatePaperId(paperId);

  const normalizedLevel =
    validateExplanationLevel(level);

  return authorizedJsonRequest(
    `/papers/${numericPaperId}/explanations`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        level: normalizedLevel,
      }),
    },
  );
}

export async function getPaperChatHistory(
  paperId,
) {
  const numericPaperId =
    validatePaperId(paperId);

  return authorizedJsonRequest(
    `/papers/${numericPaperId}/chat`,
    {
      method: "GET",
    },
  );
}


export async function askPaperQuestion(
  paperId,
  question,
) {
  const numericPaperId =
    validatePaperId(paperId);

  const cleanedQuestion = String(
    question,
  ).trim();

  if (cleanedQuestion.length < 2) {
    throw createApiError(
      "Please enter a valid question.",
      400,
    );
  }

  if (cleanedQuestion.length > 1000) {
    throw createApiError(
      "Your question cannot exceed 1000 characters.",
      400,
    );
  }

  return authorizedJsonRequest(
    `/papers/${numericPaperId}/chat`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        question: cleanedQuestion,
      }),
    },
  );
}

// =========================================================
// Research Roadmap API
// =========================================================

export async function getPaperRoadmap(
  paperId,
) {
  const numericPaperId =
    validatePaperId(paperId);

  return authorizedJsonRequest(
    `/papers/${numericPaperId}/roadmap`,
    {
      method: "GET",
    },
  );
}


export async function generatePaperRoadmap(
  paperId,
) {
  const numericPaperId =
    validatePaperId(paperId);

  return authorizedJsonRequest(
    `/papers/${numericPaperId}/roadmap`,
    {
      method: "POST",
    },
  );
}

// =========================================================
// Citation Generator API
// =========================================================

export async function getCitationMetadata(
  paperId,
) {
  const numericPaperId =
    validatePaperId(paperId);

  return authorizedJsonRequest(
    `/papers/${numericPaperId}/citation/metadata`,
    {
      method: "GET",
    },
  );
}


export async function generateCitationMetadata(
  paperId,
) {
  const numericPaperId =
    validatePaperId(paperId);

  return authorizedJsonRequest(
    `/papers/${numericPaperId}/citation/metadata`,
    {
      method: "POST",
    },
  );
}


export async function getFormattedCitations(
  paperId,
) {
  const numericPaperId =
    validatePaperId(paperId);

  return authorizedJsonRequest(
    `/papers/${numericPaperId}/citations`,
    {
      method: "GET",
    },
  );
}