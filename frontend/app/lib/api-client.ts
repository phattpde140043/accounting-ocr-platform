const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const AUTH_MODE = process.env.NEXT_PUBLIC_AUTH_MODE ?? "demo";
const ACCESS_TOKEN_STORAGE_KEY = "accounting_ocr_access_token";
const API_TIMEOUT_MS = 5000;

const demoHeaders: Record<string, string> = {
  "X-Organization-Id": "org_demo",
  "X-User-Id": "user_admin",
  "X-Role": "admin"
};

function getAuthHeaders(): Record<string, string> {
  if (typeof window !== "undefined") {
    const accessToken = window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
    if (accessToken) {
      return { Authorization: `Bearer ${accessToken}` };
    }
  }

  return AUTH_MODE === "demo" ? demoHeaders : {};
}

export function storeAccessToken(accessToken: string): void {
  window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, accessToken);
}

export function clearAccessToken(): void {
  window.localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: getAuthHeaders(),
    cache: "no-store",
    signal: AbortSignal.timeout(API_TIMEOUT_MS)
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json"
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(API_TIMEOUT_MS)
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PATCH",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(API_TIMEOUT_MS)
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function apiPostForm<T>(
  path: string,
  formData: FormData
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: formData,
    signal: AbortSignal.timeout(API_TIMEOUT_MS)
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function apiDownload(
  path: string
): Promise<{ blob: Blob; fileName: string }> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: getAuthHeaders(),
    signal: AbortSignal.timeout(API_TIMEOUT_MS)
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  const disposition = response.headers.get("Content-Disposition") ?? "";
  const fileNameMatch = disposition.match(/filename="([^"]+)"/);
  return {
    blob: await response.blob(),
    fileName: fileNameMatch?.[1] ?? "accounting-export"
  };
}
