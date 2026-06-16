/**
 * Runtime API configuration for the Lumint frontend.
 *
 * Resolution order for the HTTP base URL:
 *   1. same-origin Next.js proxy in production browsers
 *   2. validated development-only `localStorage.lumint_api_url` override
 *   3. validated `process.env.NEXT_PUBLIC_API_URL`
 *   4. `http://localhost:8000` in development (when running `next dev` against a local FastAPI)
 *   5. `null` in production when no API is reachable
 *
 * WebSocket origin is derived by parsing the configured HTTP URL and changing
 * only the protocol. Invalid or non-http(s) URLs are rejected.
 */

const DEFAULT_DEV_API_URL = "http://localhost:8000";
const FALLBACK_API_URL = "https://lumint-api.onrender.com";

/**
 * On a deployed Vercel site, the browser should talk to a same-origin
 * Next.js API route (a transparent proxy) instead of making cross-origin
 * calls to Render. This avoids the CORS preflight and any CSP/connect-src
 * issues — see `app/api/proxy/[...path]/route.ts`.
 *
 * Set `NEXT_PUBLIC_DISABLE_PROXY=1` in the Vercel project env vars to
 * bypass the proxy and call Render directly (useful for debugging CORS).
 */
function shouldUseProxy(): boolean {
  if (typeof window === "undefined") return false;
  if (process.env.NEXT_PUBLIC_DISABLE_PROXY === "1") return false;
  return process.env.NODE_ENV === "production";
}

function isLocalHost(hostname: string): boolean {
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "0.0.0.0";
}

function normalizeHttpBaseUrl(value: string | undefined | null, allowLocalHttp: boolean): string | null {
  const trimmed = value?.trim();
  if (!trimmed) return null;
  try {
    const url = new URL(trimmed);
    if (url.protocol !== "https:" && url.protocol !== "http:") return null;
    if (url.protocol === "http:" && !(allowLocalHttp && isLocalHost(url.hostname))) return null;
    url.hash = "";
    url.search = "";
    return url.toString().replace(/\/+$/, "");
  } catch {
    return null;
  }
}

function developmentOverrideUrl(): string | null {
  if (typeof window === "undefined" || process.env.NODE_ENV === "production") return null;
  try {
    return normalizeHttpBaseUrl(window.localStorage.getItem("lumint_api_url"), true);
  } catch {
    return null;
  }
}

/**
 * The configured API base URL, or `null` if no API is reachable from this environment.
 * Use this to gate network calls: `if (apiBaseUrl()) { fetch(...) } else { useMock() }`.
 */
export function apiBaseUrl(): string | null {
  const override = developmentOverrideUrl();
  if (override) return override;

  // On deployed sites, use a same-origin proxy. This avoids leaking server
  // authentication headers into the browser and keeps CORS/connect-src simple.
  if (shouldUseProxy()) {
    return "/api/proxy";
  }

  const fromEnv = normalizeHttpBaseUrl(process.env.NEXT_PUBLIC_API_URL, true);
  if (fromEnv) {
    return fromEnv;
  }

  // If the env var is missing on a deployed site, fall back to the known
  // Render backend so the frontend still works. This is a hardcoded safety net
  // — operators can override it by setting NEXT_PUBLIC_API_URL in Vercel.
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (!isLocalHost(host)) {
      return FALLBACK_API_URL;
    }
    return DEFAULT_DEV_API_URL;
  }

  // SSR / build time: prefer the fallback so server-rendered fetches hit the
  // real backend instead of localhost.
  return FALLBACK_API_URL;
}

/**
 * Returns the WebSocket origin (protocol + host[:port]) for the configured API.
 * Derives `wss://` from `https://` and `ws://` from `http://`. Returns `null`
 * when no API is configured.
 *
 * For production, threat streaming uses the configured backend/fallback origin
 * directly because the same-origin proxy is HTTP-only. Production CSP should
 * allow `wss://lumint-api.onrender.com` unless the backend origin changes.
 */
export function wsOrigin(): string | null {
  const override = developmentOverrideUrl();
  const httpBase = override ?? normalizeHttpBaseUrl(process.env.NEXT_PUBLIC_API_URL, true) ?? FALLBACK_API_URL;
  try {
    const url = new URL(httpBase);
    if (url.protocol === "https:") {
      url.protocol = "wss:";
    } else if (url.protocol === "http:" && isLocalHost(url.hostname)) {
      url.protocol = "ws:";
    } else {
      return null;
    }
    url.pathname = "";
    url.search = "";
    url.hash = "";
    return url.toString().replace(/\/+$/, "");
  } catch {
    return null;
  }
}
