import type {
  AuthMeResponse,
  AuthTokens,
  ProgressSnapshotResponse,
  ProgressSummaryResponse,
  QuizAttemptHistoryItemResponse,
  QuizAttemptSubmitRequest,
  QuizAttemptSubmitResponse,
  QuizDetailResponse,
  QuizListItemResponse,
  StudySessionRequest,
  SubjectDetailResponse,
  SubjectSummaryResponse,
  UserPreferencesPatchRequest,
  UserPreferencesResponse,
  UserProfilePatchRequest,
  UserProfileResponse,
} from "@/lib/api-types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

type JsonBody = Record<string, unknown> | Array<unknown>;

function getLocalStorage(): Storage | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage;
}

function getTokens(): { accessToken: string | null; refreshToken: string | null } {
  const storage = getLocalStorage();
  if (!storage) {
    return { accessToken: null, refreshToken: null };
  }
  return {
    accessToken: storage.getItem(ACCESS_TOKEN_KEY),
    refreshToken: storage.getItem(REFRESH_TOKEN_KEY),
  };
}

function toErrorDetail(detail: unknown): string {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg?: unknown }).msg ?? "");
        }
        return "";
      })
      .filter(Boolean);
    if (messages.length > 0) {
      return messages.join(" | ");
    }
  }
  if (detail && typeof detail === "object") {
    if ("message" in detail) {
      return String((detail as { message?: unknown }).message ?? "Request failed");
    }
    try {
      return JSON.stringify(detail);
    } catch {
      return "Request failed";
    }
  }
  return "Request failed";
}

export function saveTokens(tokens: { accessToken: string; refreshToken: string }): void {
  const storage = getLocalStorage();
  if (!storage) {
    return;
  }
  storage.setItem(ACCESS_TOKEN_KEY, tokens.accessToken);
  storage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken);
}

export function clearTokens(): void {
  const storage = getLocalStorage();
  if (!storage) {
    return;
  }
  storage.removeItem(ACCESS_TOKEN_KEY);
  storage.removeItem(REFRESH_TOKEN_KEY);
}

export function hasAccessToken(): boolean {
  return Boolean(getTokens().accessToken);
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = "Request failed";
    try {
      const payload = (await response.json()) as { detail?: unknown };
      detail = toErrorDetail(payload.detail);
    } catch {
      // Keep generic detail when response body is not JSON.
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

async function refreshAccessToken(refreshToken: string): Promise<AuthTokens> {
  const response = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  return parseResponse<AuthTokens>(response);
}

type AuthRequestOptions = {
  method?: "GET" | "POST" | "PATCH";
  body?: JsonBody;
  retryOnUnauthorized?: boolean;
};

export async function authRequest<T>(
  path: string,
  options: AuthRequestOptions = {},
): Promise<T> {
  const { accessToken, refreshToken } = getTokens();
  if (!accessToken) {
    throw new ApiError(401, "Та эхлээд нэвтэрнэ үү.");
  }

  const response = await fetch(`${API_URL}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (response.status !== 401) {
    return parseResponse<T>(response);
  }

  if (options.retryOnUnauthorized === false || !refreshToken) {
    clearTokens();
    throw new ApiError(401, "Сесс дууссан байна. Дахин нэвтэрнэ үү.");
  }

  try {
    const refreshed = await refreshAccessToken(refreshToken);
    saveTokens({
      accessToken: refreshed.access_token,
      refreshToken: refreshed.refresh_token,
    });
  } catch {
    clearTokens();
    throw new ApiError(401, "Сесс дууссан байна. Дахин нэвтэрнэ үү.");
  }

  return authRequest<T>(path, { ...options, retryOnUnauthorized: false });
}

export async function login(email: string, password: string): Promise<AuthTokens> {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return parseResponse<AuthTokens>(response);
}

export async function logout(): Promise<void> {
  const { refreshToken } = getTokens();
  if (!refreshToken) {
    clearTokens();
    return;
  }
  try {
    await authRequest<void>("/auth/logout", {
      method: "POST",
      body: { refresh_token: refreshToken },
    });
  } catch {
    // If token is already invalid/revoked we still clear local tokens.
  } finally {
    clearTokens();
  }
}

export async function getMe(): Promise<AuthMeResponse> {
  return authRequest<AuthMeResponse>("/auth/me");
}

export async function getSubjects(): Promise<SubjectSummaryResponse[]> {
  return authRequest<SubjectSummaryResponse[]>("/subjects");
}

export async function getSubjectDetail(subjectId: string): Promise<SubjectDetailResponse> {
  return authRequest<SubjectDetailResponse>(`/subjects/${subjectId}`);
}

export async function getQuizzes(params?: {
  subjectId?: string;
  topicId?: string;
}): Promise<QuizListItemResponse[]> {
  const query = new URLSearchParams();
  if (params?.subjectId) {
    query.set("subject_id", params.subjectId);
  }
  if (params?.topicId) {
    query.set("topic_id", params.topicId);
  }
  const queryString = query.toString();
  return authRequest<QuizListItemResponse[]>(`/quizzes${queryString ? `?${queryString}` : ""}`);
}

export async function getQuizDetail(quizId: string): Promise<QuizDetailResponse> {
  return authRequest<QuizDetailResponse>(`/quizzes/${quizId}`);
}

export async function submitQuizAttempt(
  quizId: string,
  payload: QuizAttemptSubmitRequest,
): Promise<QuizAttemptSubmitResponse> {
  return authRequest<QuizAttemptSubmitResponse>(`/quizzes/${quizId}/attempts`, {
    method: "POST",
    body: payload,
  });
}

export async function getQuizHistory(limit = 20): Promise<QuizAttemptHistoryItemResponse[]> {
  return authRequest<QuizAttemptHistoryItemResponse[]>(`/quizzes/attempts/history?limit=${limit}`);
}

export async function getProgressSummary(days = 7): Promise<ProgressSummaryResponse> {
  return authRequest<ProgressSummaryResponse>(`/progress/summary?days=${days}`);
}

export async function getProgressSnapshots(limit = 20): Promise<ProgressSnapshotResponse[]> {
  return authRequest<ProgressSnapshotResponse[]>(`/progress/snapshots?limit=${limit}`);
}

export async function createStudySession(payload: StudySessionRequest): Promise<void> {
  await authRequest("/progress/study-sessions", {
    method: "POST",
    body: payload,
  });
}

export async function getProfile(): Promise<UserProfileResponse> {
  return authRequest<UserProfileResponse>("/users/me/profile");
}

export async function updateProfile(payload: UserProfilePatchRequest): Promise<UserProfileResponse> {
  return authRequest<UserProfileResponse>("/users/me/profile", {
    method: "PATCH",
    body: payload,
  });
}

export async function getPreferences(): Promise<UserPreferencesResponse> {
  return authRequest<UserPreferencesResponse>("/users/me/preferences");
}

export async function updatePreferences(
  payload: UserPreferencesPatchRequest,
): Promise<UserPreferencesResponse> {
  return authRequest<UserPreferencesResponse>("/users/me/preferences", {
    method: "PATCH",
    body: payload,
  });
}
