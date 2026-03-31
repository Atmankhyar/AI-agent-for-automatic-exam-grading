const RAW_SERVER_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const SERVER_URL = RAW_SERVER_URL.replace(/\/+$/, "");
const API_BASE = /\/api$/i.test(SERVER_URL) ? SERVER_URL : `${SERVER_URL}/api`;
const DEFAULT_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_API_TIMEOUT_MS || 10000);

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem("token");
  } catch {
    return null;
  }
}

function getTimeoutMs(value?: number): number {
  if (typeof value === "number" && Number.isFinite(value) && value > 0) {
    return value;
  }
  if (Number.isFinite(DEFAULT_TIMEOUT_MS) && DEFAULT_TIMEOUT_MS > 0) {
    return DEFAULT_TIMEOUT_MS;
  }
  return 10000;
}

async function fetchWithTimeout(
  url: string,
  init: RequestInit,
  timeoutMs?: number
): Promise<Response> {
  const controller = new AbortController();
  const externalSignal = init.signal;
  const onAbort = () => controller.abort();

  if (externalSignal) {
    if (externalSignal.aborted) {
      controller.abort();
    } else {
      externalSignal.addEventListener("abort", onAbort, { once: true });
    }
  }

  const ms = getTimeoutMs(timeoutMs);
  const timeout = setTimeout(() => controller.abort(), ms);

  try {
    return await fetch(url, {
      ...init,
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(
        `Requete expiree apres ${Math.round(ms / 1000)}s. Verifiez que le backend est demarre et accessible.`
      );
    }
    throw err;
  } finally {
    clearTimeout(timeout);
    if (externalSignal) {
      externalSignal.removeEventListener("abort", onAbort);
    }
  }
}

export async function api<T>(
  path: string,
  options: RequestInit & { token?: string | null; timeoutMs?: number } = {}
): Promise<T> {
  const { token: optToken, timeoutMs, ...rest } = options;
  const token = optToken ?? getToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(rest.headers as Record<string, string>),
  };
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetchWithTimeout(`${API_BASE}${path}`, {
    ...rest,
    headers: { ...headers, ...rest.headers } as HeadersInit,
  }, timeoutMs);

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail));
  }
  return res.json();
}

export async function apiUpload(
  path: string,
  file: File,
  token?: string | null,
  timeoutMs?: number
): Promise<{ file_uri: string }> {
  const t = token ?? getToken();
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetchWithTimeout(`${API_BASE}${path}`, {
    method: "POST",
    headers: t ? { Authorization: `Bearer ${t}` } : {},
    body: formData,
  }, timeoutMs);

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail));
  }
  return res.json();
}

/** POST multipart avec fichier + champs form (title, bareme, etc.) */
export async function apiPostForm<T>(
  path: string,
  formData: FormData,
  token?: string | null,
  timeoutMs?: number
): Promise<T> {
  const t = token ?? getToken();
  const res = await fetchWithTimeout(`${API_BASE}${path}`, {
    method: "POST",
    headers: t ? { Authorization: `Bearer ${t}` } : {},
    body: formData,
  }, timeoutMs);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail));
  }
  return res.json();
}
