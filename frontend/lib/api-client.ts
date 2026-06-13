import { apiBaseUrl } from "./config";

/**
 * Centralized API client used by `services/*`.
 * Falls back to throwing if NEXT_PUBLIC_API_URL is unset, so callers can
 * opt into mock data via `lib/api/*` (modular clients) when no backend is
 * available. The UPI Shield service requires a real backend.
 */

export interface ApiRequestOptions extends Omit<RequestInit, "body"> {
  body?: BodyInit | null;
  /** Skip the Authorization header (used for endpoints that don't require auth). */
  skipAuth?: boolean;
  /** Per-request timeout override (ms). */
  timeoutMs?: number;
}

export class ApiError extends Error {
  constructor(public status: number, message: string, public detail?: unknown) {
    super(message);
    this.name = "ApiError";
  }
}

function buildHeaders(opts: ApiRequestOptions): HeadersInit {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(opts.headers as Record<string, string> | undefined),
  };
  if (!opts.skipAuth) {
    const apiKey = process.env.NEXT_PUBLIC_API_KEY;
    if (apiKey) headers["Authorization"] = `Bearer ${apiKey}`;
  }
  return headers;
}

export async function apiRequest<T = unknown>(
  path: string,
  opts: ApiRequestOptions = {}
): Promise<T> {
  const base = apiBaseUrl();
  if (!base) {
    throw new ApiError(0, "API base URL is not configured");
  }
  const url = `${base.replace(/\/+$/, "")}${path}`;
  const timeout = opts.timeoutMs ?? 30_000;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeout);

  let res: Response;
  try {
    res = await fetch(url, {
      ...opts,
      headers: buildHeaders(opts),
      signal: ctrl.signal,
    });
  } finally {
    clearTimeout(timer);
  }

  if (!res.ok) {
    let detail: unknown = undefined;
    try {
      detail = await res.json();
    } catch {
      // ignore body parse errors
    }
    const message =
      (detail && typeof detail === "object" && "detail" in detail
        ? String((detail as { detail: unknown }).detail)
        : null) || `HTTP ${res.status}`;
    throw new ApiError(res.status, message, detail);
  }

  // 204 / empty body
  const text = await res.text();
  if (!text) return undefined as T;
  try {
    return JSON.parse(text) as T;
  } catch {
    return text as unknown as T;
  }
}
